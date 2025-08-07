"""
游戏管理器 - 整合LLM客户端和扑克游戏引擎
"""

from typing import List, Dict, Optional, Any
from llm_client import LLMClient
from poker_game import PokerGame, Player, Action
from config import PROMPT_CONFIG
from logger import GameLogger
import time


class GameManager:
    def __init__(self, num_players: int = 4, starting_chips: int = 1000):
        self.game = PokerGame(num_players, starting_chips)
        self.llm_clients = {}
        self.system_prompt = PROMPT_CONFIG["system_prompt"]
        
        # 初始化日志记录器
        self.logger = GameLogger()
        
        # 初始化LLM客户端
        self.llm_clients = {}
        for llm_type in ["qwen3", "qwen2.5"]:
            try:
                self.llm_clients[llm_type] = LLMClient(llm_type)
                print(f"✅ 初始化 {llm_type} 客户端成功")
            except Exception as e:
                print(f"❌ 初始化 {llm_type} 客户端失败: {e}")
    
    def play_hand(self, hand_num: int) -> Dict:
        """玩一手牌"""
        print("\n" + "="*50)
        print("开始新的一手牌")
        print("="*50)
        
        # 记录手牌开始
        game_config = {
            "num_players": self.game.num_players,
            "starting_chips": self.game.starting_chips,
            "small_blind": self.game.small_blind,
            "big_blind": self.game.big_blind
        }
        self.logger.log_hand_start(hand_num, game_config)
        
        # 重置游戏状态
        self.game.reset_round()
        
        # 发手牌
        self.game.deal_cards()
        
        # 收取盲注
        self._collect_blinds()
        
        # 玩各个轮次
        rounds = ["preflop", "flop", "turn", "river"]
        for round_name in rounds:
            if not self._play_round(round_name):
                break
        
        # 摊牌和分配底池
        winners = self.game.get_winner()
        self._showdown(winners)
        
        # 记录手牌结束
        final_state = {
            "winners": [w.name for w in winners],
            "pot": self.game.pot,
            "final_state": self.game.get_game_state_text(),
            "player_chips": {p.name: p.chips for p in self.game.players}
        }
        self.logger.log_hand_end(final_state)
        
        return final_state
    
    def _collect_blinds(self):
        """收取盲注"""
        # 小盲注
        sb_pos = (self.game.dealer_pos + 1) % self.game.num_players
        sb_player = self.game.players[sb_pos]
        sb_amount = min(self.game.small_blind, sb_player.chips)
        sb_player.chips -= sb_amount
        sb_player.current_bet = sb_amount
        self.game.pot += sb_amount
        
        # 大盲注
        bb_pos = (self.game.dealer_pos + 2) % self.game.num_players
        bb_player = self.game.players[bb_pos]
        bb_amount = min(self.game.big_blind, bb_player.chips)
        bb_player.chips -= bb_amount
        bb_player.current_bet = bb_amount
        self.game.pot += bb_amount
        
        self.game.current_bet = bb_amount
        
        # 设置位置信息
        self.game.small_blind_pos = sb_pos
        self.game.big_blind_pos = bb_pos
        
        # preflop从大盲位置的下一个玩家开始（UTG位置）
        self.game.current_player = (bb_pos + 1) % self.game.num_players
        
        print(f"收取盲注: {sb_player.name} 小盲 {sb_amount}, {bb_player.name} 大盲 {bb_amount}")
        print(f"位置: 庄家={self.game.players[self.game.dealer_pos].name}, "
              f"小盲={sb_player.name}, 大盲={bb_player.name}")
    
    def _play_round(self, round_name: str) -> bool:
        """玩一个轮次"""
        print(f"\n--- {round_name.upper()} 轮 ---")
        
        # 如果是flop轮，发公共牌
        if round_name == "flop":
            self.game.deal_community_cards(3)
            print(f"发公共牌: {' '.join([str(card) for card in self.game.community_cards])}")
        elif round_name in ["turn", "river"]:
            self.game.deal_community_cards(1)
            print(f"发公共牌: {' '.join([str(card) for card in self.game.community_cards])}")
        
        # 记录轮次开始
        game_state = self.game.get_game_state_text()
        community_cards = [str(card) for card in self.game.community_cards]
        self.logger.log_round_start(round_name, game_state, community_cards)
        
        # 重置下注（除了preflop轮）
        if round_name != "preflop":
            self.game.current_bet = 0
            for player in self.game.players:
                player.current_bet = 0
            print("重置下注")
        
        # 设置起始玩家
        if round_name == "preflop":
            # preflop从大盲位置的下一个玩家开始
            self.game.current_player = (self.game.big_blind_pos + 1) % self.game.num_players
        else:
            # 其他轮次从小盲位置开始
            self.game.current_player = self.game.small_blind_pos
        
        # 找到第一个活跃玩家
        while not self.game.players[self.game.current_player].is_active:
            self.game.current_player = (self.game.current_player + 1) % self.game.num_players
        
        print(f"起始玩家: {self.game.players[self.game.current_player].name}")
        
        # 进行下注轮次
        round_complete = False
        start_player = self.game.current_player
        last_raiser = None  # 记录最后一个加注的玩家
        round_started = False  # 标记轮次是否已经开始
        
        # 在preflop轮中，标记大盲注还没有行动过
        if round_name == "preflop":
            self.big_blind_acted = False
            # 如果大盲注是起始玩家，说明没有其他玩家行动，大盲注已经行动过了
            if self.game.current_player == self.game.big_blind_pos:
                self.big_blind_acted = True
        
        while not round_complete:
            current_player = self.game.players[self.game.current_player]
            
            if not current_player.is_active or current_player.is_all_in:
                self.game.current_player = (self.game.current_player + 1) % self.game.num_players
                # 如果回到起始玩家，轮次结束
                if self.game.current_player == start_player:
                    round_complete = True
                continue
            
            # 获取LLM决策
            action, llm_input, llm_output = self._get_player_action(current_player)
            
            # 执行动作
            action_result = self._execute_action(current_player, action)
            
            # 记录玩家动作
            player_hand = [str(card) for card in current_player.hand]
            self.logger.log_player_action(
                current_player.name, 
                player_hand, 
                llm_input, 
                llm_output, 
                action, 
                action_result
            )
            
            if not action_result:
                break
            
            # 标记轮次已经开始
            round_started = True
            
            # 检查是否有加注
            if action_result["action_type"] in ["raise", "all-in"]:
                last_raiser = current_player
                # 重置起始玩家为加注玩家的下一个
                start_player = (self.game.current_player + 1) % self.game.num_players
                # 找到下一个活跃玩家作为新的起始玩家
                while not self.game.players[start_player].is_active:
                    start_player = (start_player + 1) % self.game.num_players
                # 如果起始玩家就是当前玩家，说明只有两个玩家，但轮次还没有结束
                # 需要让另一个玩家有机会回应加注
                if start_player == self.game.current_player:
                    # 继续轮次，让另一个玩家有机会回应
                    print(f"加注后继续轮次，等待玩家回应")
            
            # 移动到下一个玩家
            self.game.current_player = (self.game.current_player + 1) % self.game.num_players
            
            # 检查是否只剩一个玩家
            active_players = [p for p in self.game.players if p.is_active]
            if len(active_players) <= 1:
                return False
            
            # 检查轮次是否完成（回到起始玩家且所有下注相等）
            if self.game.current_player == start_player and round_started:
                if self.game.is_round_complete():
                    # 在preflop轮中，如果大盲注还没有行动过，需要给大盲注一次机会
                    if round_name == "preflop" and not self.big_blind_acted:
                        # 标记大盲注已经行动过
                        self.big_blind_acted = True
                        print(f"大盲注还有一次行动机会")
                        round_complete = False
                    else:
                        round_complete = True
                        print(f"轮次完成，所有玩家下注均衡")
                else:
                    # 如果下注不均衡，继续轮次
                    print(f"下注不均衡，继续轮次等待玩家回应")
        
        return True
    
    def _get_player_action(self, player: Player) -> tuple:
        """获取玩家动作"""
        # 构建游戏状态描述
        game_state = self.game.get_game_state_text()
        player_hand = self.game.get_player_hand_text(player)
        
        # 添加当前玩家特定信息
        current_bet_to_call = self.game.current_bet - player.current_bet
        
        # 确定当前玩家的位置
        player_pos = ""
        for i, p in enumerate(self.game.players):
            if p == player:
                if i == self.game.dealer_pos:
                    player_pos = "(庄家)"
                elif i == self.game.small_blind_pos:
                    player_pos = "(小盲)"
                elif i == self.game.big_blind_pos:
                    player_pos = "(大盲)"
                else:
                    player_pos = "(其他)"
                break
        
        game_state += f"\n当前玩家: {player.name}{player_pos}"
        game_state += f"\n需要跟注: {current_bet_to_call} 筹码"
        game_state += f"\n你的筹码: {player.chips}"
        
        # 获取LLM决策
        llm_client = self.llm_clients[player.llm_type]
        action, llm_input, llm_output = llm_client.get_action(game_state, player_hand, self.system_prompt)
        
        print(f"{player.name} 的动作: {action}")
        return action, llm_input, llm_output
    
    def _execute_action(self, player: Player, action: str) -> Dict[str, Any]:
        """执行玩家动作"""
        action_lower = action.lower()
        current_bet_to_call = self.game.current_bet - player.current_bet
        
        action_result = {
            "action_type": "unknown",
            "amount": 0,
            "success": True,
            "message": ""
        }
        
        if "fold" in action_lower:
            player.is_active = False
            action_result["action_type"] = "fold"
            action_result["message"] = f"{player.name} 弃牌"
            print(f"{player.name} 弃牌")
            
        elif "check" in action_lower:
            if current_bet_to_call > 0:
                action_result["message"] = f"{player.name} 不能过牌，需要跟注 {current_bet_to_call}"
                print(f"{player.name} 不能过牌，需要跟注 {current_bet_to_call}")
                # 强制跟注
                call_amount = min(current_bet_to_call, player.chips)
                player.chips -= call_amount
                player.current_bet += call_amount
                self.game.pot += call_amount
                action_result["action_type"] = "call"
                action_result["amount"] = call_amount
                action_result["message"] = f"{player.name} 跟注 {call_amount}"
                print(f"{player.name} 跟注 {call_amount}")
            else:
                action_result["action_type"] = "check"
                action_result["message"] = f"{player.name} 过牌"
                print(f"{player.name} 过牌")
                
        elif "call" in action_lower:
            call_amount = min(current_bet_to_call, player.chips)
            player.chips -= call_amount
            player.current_bet += call_amount
            self.game.pot += call_amount
            action_result["action_type"] = "call"
            action_result["amount"] = call_amount
            action_result["message"] = f"{player.name} 跟注 {call_amount}"
            print(f"{player.name} 跟注 {call_amount}")
            
        elif "raise" in action_lower or "all-in" in action_lower or "allin" in action_lower:
            llm_client = self.llm_clients[player.llm_type]
            max_raise = player.chips
            
            if "all-in" in action_lower or "allin" in action_lower:
                raise_amount = max_raise
                action_result["action_type"] = "all-in"
            else:
                raise_amount = llm_client.get_raise_amount(action, max_raise)
                if raise_amount == 0:
                    raise_amount = max_raise // 2  # 默认加注一半筹码
                action_result["action_type"] = "raise"
            
            # 计算实际需要投入的筹码（增量）
            current_bet_to_call = self.game.current_bet - player.current_bet
            
            # 如果LLM返回的是总下注金额，需要转换为增量
            if raise_amount > current_bet_to_call:
                # LLM返回的是总下注金额
                total_bet_needed = raise_amount
            else:
                # LLM返回的是增量
                total_bet_needed = self.game.current_bet + raise_amount
            
            # 确保加注金额合理
            min_raise = self.game.current_bet + self.game.big_blind
            total_bet_needed = max(total_bet_needed, min_raise)
            total_bet_needed = min(total_bet_needed, player.current_bet + max_raise)
            
            # 计算实际投入的筹码
            actual_bet_amount = total_bet_needed - player.current_bet
            
            player.chips -= actual_bet_amount
            player.current_bet = total_bet_needed
            self.game.pot += actual_bet_amount
            self.game.current_bet = total_bet_needed
            action_result["amount"] = actual_bet_amount
            
            if raise_amount == max_raise:
                player.is_all_in = True
                action_result["message"] = f"{player.name} 全下 {raise_amount}"
                print(f"{player.name} 全下 {raise_amount}")
            else:
                action_result["message"] = f"{player.name} 加注到 {raise_amount}"
                print(f"{player.name} 加注到 {raise_amount}")
        
        # 检查玩家是否全下
        if player.chips == 0:
            player.is_all_in = True
        
        return action_result
    
    def _showdown(self, winners: List[Player]):
        """摊牌和分配底池"""
        print(f"\n--- 摊牌 ---")
        print(f"底池: {self.game.pot} 筹码")
        
        # 收集玩家信息用于日志
        players_info = []
        for player in self.game.players:
            if player.is_active:
                hand_text = self.game.get_player_hand_text(player)
                print(f"{player.name}: {hand_text}")
                players_info.append({
                    "name": player.name,
                    "hand": hand_text,
                    "chips": player.chips,
                    "is_active": player.is_active
                })
        
        if winners:
            winner_names = [w.name for w in winners]
            print(f"获胜者: {', '.join(winner_names)}")
            self.game.distribute_pot(winners)
            
            for winner in winners:
                print(f"{winner.name} 获得筹码，当前筹码: {winner.chips}")
        else:
            print("没有获胜者")
            winner_names = []
        
        # 记录摊牌信息
        self.logger.log_showdown(players_info, winner_names, self.game.pot)
    
    def play_game(self, num_hands: int = 10):
        """玩多手牌"""
        print(f"开始 {num_hands} 手牌的德州扑克游戏")
        print(f"玩家数量: {self.game.num_players}")
        print(f"起始筹码: {self.game.starting_chips}")
        
        results = []
        for hand_num in range(1, num_hands + 1):
            print(f"\n第 {hand_num} 手牌")
            result = self.play_hand(hand_num)
            results.append(result)
            
            # 显示玩家筹码状态
            print("\n玩家筹码状态:")
            for player in self.game.players:
                print(f"  {player.name}: {player.chips} 筹码")
            
            # 检查是否有玩家出局
            active_players = [p for p in self.game.players if p.chips > 0]
            if len(active_players) <= 1:
                print(f"\n游戏结束！只剩 {len(active_players)} 个玩家有筹码")
                break
            
            time.sleep(1)  # 短暂暂停
        
        # 记录会话结束
        final_results = {
            "total_hands": len(results),
            "final_chips": {p.name: p.chips for p in self.game.players},
            "winner_stats": self._calculate_winner_stats(results)
        }
        self.logger.log_session_end(final_results)
        
        return results
    
    def _calculate_winner_stats(self, results: List[Dict]) -> Dict[str, int]:
        """计算获胜统计"""
        winner_stats = {}
        for result in results:
            for winner in result["winners"]:
                winner_stats[winner] = winner_stats.get(winner, 0) + 1
        return winner_stats 