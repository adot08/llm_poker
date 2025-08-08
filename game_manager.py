# game_manager.py

from typing import List, Dict, Tuple
from llm_client import LLMClient
from poker_engine import PokerGame, Player
from config import PROMPT_CONFIG, GAME_CONFIG, LLM_CONFIGS
from logger import GameLogger
import time
import itertools

class GameManager:
    def __init__(self, num_players: int, starting_chips: int):
        llm_types = list(LLM_CONFIGS.keys())
        llm_types_iter = itertools.cycle(llm_types)
        player_configs = [
            {"name": f"Player-{i+1}", "llm_type": next(llm_types_iter)}
            for i in range(num_players)
        ]
        
        self.game = PokerGame(
            players_with_llm=player_configs,
            starting_chips=starting_chips,
            small_blind=GAME_CONFIG['small_blind'],
            big_blind=GAME_CONFIG['big_blind']
        )
        self.llm_clients = {
            llm_type: LLMClient(llm_type) for llm_type in llm_types
        }
        self.system_prompt = PROMPT_CONFIG["system_prompt"]
        self.logger = GameLogger()
        self.winner_stats = {p.name: 0 for p in self.game.players}
        self.action_history = []

    def play_game(self, num_hands: int):
        for hand_num in range(1, num_hands + 1):
            if len([p for p in self.game.players if p.chips > 0]) < 2:
                print("\n游戏结束，只剩一位玩家！")
                break
            
            print("\n" + "="*60)
            print(f"手牌 #{hand_num}")
            print("="*60)
            self._play_hand(hand_num)
            time.sleep(3)

        final_chips = {p.name: p.chips for p in self.game.players}
        self.logger.log_session_end(final_chips, self.winner_stats)
        return self.get_final_results()

    def _play_hand(self, hand_num: int):
        self.action_history.clear()
        game_config = {
            "num_players": self.game.num_players,
            "starting_chips": [p.initial_chips for p in self.game.players if p.name in self.winner_stats],
            "small_blind": self.game.small_blind,
            "big_blind": self.game.big_blind
        }
        self.logger.log_hand_start(hand_num, game_config)
        
        if not self.game.start_new_hand(): return

        print(f"庄家(D): {self.game.get_player(self.game.dealer_pos).name}")
        for p in self.game.players:
            if p.chips > 0: print(f"{p.name}: 手牌 [{' '.join(map(str, p.hand))}]")

        rounds = ["preflop", "flop", "turn", "river"]
        for round_name in rounds:
            if len([p for p in self.game.players if p.is_active]) < 2: break
            
            self.action_history.append(f"\n--- {round_name.upper()} 轮 ---")
            print(f"\n--- {round_name.upper()} 轮 ---")
            if round_name != 'preflop': self.game.deal_community(3 if round_name == 'flop' else 1)
            
            print(f"公共牌: [{' '.join(map(str, self.game.community_cards))}]")
            self.logger.log_round_start(round_name, [str(c) for c in self.game.community_cards])
            
            self._run_betting_round(round_name)
        
        self.game.collect_bets_and_manage_pots()
        self._showdown()
        
        print("\n--- 手牌结束 筹码情况 ---")
        for p in self.game.players:
            print(f"{p.name}: {p.chips}")
        
        final_chips = {p.name: p.chips for p in self.game.players}
        self.logger.log_hand_end(final_chips)

    def _run_betting_round(self, round_name: str):
        self.game.start_betting_round(round_name)
        if self.game.action_player_idx == -1: return

        if round_name == 'preflop':
            sb_player = self.game.get_player(self.game.small_blind_pos)
            bb_player = self.game.get_player(self.game.big_blind_pos)
            self.action_history.append(f"{sb_player.name}(SB) 下小盲 {self.game.small_blind}")
            self.action_history.append(f"{bb_player.name}(BB) 下大盲 {self.game.big_blind}")

        num_active_players = len([p for p in self.game.players if p.is_active])
        acted_players = set()
        
        while True:
            player = self.game.get_player(self.game.action_player_idx)
            
            # 轮次结束条件
            all_acted = len(acted_players) >= num_active_players
            all_bets_matched = all(p.bet_in_round == self.game.current_bet for p in self.game.players if p.is_active and not p.is_all_in)
            action_on_raiser = player == self.game.last_raiser

            if (action_on_raiser or all_acted) and all_bets_matched and self.game.current_bet > 0:
                break
            if all_acted and self.game.current_bet == 0: # 所有人都过牌
                break

            acted_players.add(player)
            
            action_dict, llm_input, llm_output = self._get_player_action(player)
            
            action_msg = self.game.handle_action(player, action_dict['action'], action_dict.get('amount', 0))
            print(action_msg)
            self.action_history.append(action_msg)
            
            self.logger.log_player_action(player.name, player.hand, llm_input, llm_output, action_dict, action_msg)
            
            if len([p for p in self.game.players if p.is_active]) < 2: break

            self.game.action_player_idx = self.game.get_next_active_player_idx(self.game.action_player_idx)
            if self.game.action_player_idx == -1: break

    def _get_player_action(self, player: Player) -> tuple:
        valid_actions = self._get_valid_actions(player)
        game_state_text = self._get_game_state_text(player)
        
        llm_client = self.llm_clients[player.llm_type]
        parsed_action, llm_input, raw_output = llm_client.get_action(
            game_state_text, f"[{' '.join(map(str, player.hand))}]", self.system_prompt
        )
        
        # 验证LLM动作
        action_name = parsed_action['action']
        if action_name not in valid_actions:
            # 如果LLM意图是check但不能check，强制call或fold
            if action_name == 'check' and valid_actions.get('call', 0) > 0:
                parsed_action = {'action': 'call'}
            else: # 其他非法动作，强制fold
                parsed_action = {'action': 'fold'}
        
        if action_name == 'raise':
            amount = parsed_action.get('amount', 0)
            min_r, max_r = valid_actions['raise']['min'], valid_actions['raise']['max']
            # 修正加注额到合法范围
            parsed_action['amount'] = max(min_r, min(amount, max_r))
            
        return parsed_action, llm_input, raw_output

    def _get_valid_actions(self, player: Player) -> Dict:
        actions = {}
        to_call = self.game.current_bet - player.bet_in_round
        
        if to_call == 0:
            actions['check'] = True
        else:
            actions['call'] = min(to_call, player.chips)
        
        actions['fold'] = True
        actions['all-in'] = True

        min_raise_total = self.game.current_bet + self.game.min_raise_amount
        max_raise_total = player.chips + player.bet_in_round
        if max_raise_total >= min_raise_total:
            actions['raise'] = {'min': min_raise_total, 'max': max_raise_total}
        
        return actions

    def _get_game_state_text(self, current_player: Player) -> str:
        state = []
        state.append(f"底池总额: {sum(p.bet_in_hand for p in self.game.players)}")
        state.append(f"公共牌: [{' '.join(map(str, self.game.community_cards))}]")
        
        state.append("\n--- 玩家信息 ---")
        for i, p in enumerate(self.game.players):
            pos_info = ""
            if i == self.game.dealer_pos: pos_info += "(D)"
            if hasattr(self.game, 'small_blind_pos') and i == self.game.small_blind_pos: pos_info += "(SB)"
            if hasattr(self.game, 'big_blind_pos') and i == self.game.big_blind_pos: pos_info += "(BB)"

            if p.is_active:
                player_status = f"初始:{p.chips_at_start_of_hand}, 已下注:{p.bet_in_hand}, 剩余:{p.chips}"
            else:
                player_status = "已弃牌"

            line = f"- {p.name}{pos_info}: {player_status}"
            if p == current_player: line += " (你)"
            state.append(line)
        
        if self.action_history:
            state.append("\n--- 本手牌下注历史 ---")
            state.extend(self.action_history)

        state.append("\n--- 你的回合 ---")
        to_call = self.game.current_bet - current_player.bet_in_round
        clipped_to_call = min(to_call, current_player.chips)
        state.append(f"本手牌初始筹码: {current_player.chips_at_start_of_hand}")
        state.append(f"已下注筹码: {current_player.bet_in_hand}")
        state.append(f"剩余筹码: {current_player.chips}")
        state.append(f"需要跟注: {clipped_to_call}")
        
        return "\n".join(state)
        
    def _showdown(self):
        print("\n--- 摊牌 ---")
        active_players = [p for p in self.game.players if p.is_active]
        if len(active_players) == 1:
            winner = active_players[0]
            total_pot = sum(pot['amount'] for pot in self.game.pots)
            winner.chips += total_pot
            print(f"{winner.name} 是唯一幸存者, 赢得底池 {total_pot}")
            self.winner_stats[winner.name] += 1
            
            # 修正pot结构以包含eligible_players
            pot_details = {
                'amount': total_pot,
                'eligible_players': active_players 
            }
            self.logger.log_showdown([{'pot': pot_details, 'winners': [winner], 'hand_details': ('未摊牌', [])}])
            return
        
        winner_results = self.game.determine_winners()
        self.logger.log_showdown(winner_results)

        for res in winner_results:
            pot_amt = res['pot']['amount']
            winners = res['winners']
            details = res['hand_details']
            print(f"底池 {pot_amt} 由 {', '.join([w.name for w in winners])} 赢得")
            print(f"  牌型: {details[0]} - {' '.join(map(str, details[1]))}")
            for w in winners: self.winner_stats[w.name] += 1
        
        self.game.distribute_winnings(winner_results)

    def get_final_results(self):
        return {
            "final_chips": {p.name: p.chips for p in self.game.players},
            "winner_stats": self.winner_stats
        }