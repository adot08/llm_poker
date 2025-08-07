"""
简化游戏测试 - 只使用一个LLM类型
"""

from poker_game import PokerGame, Player
from llm_client import LLMClient
from config import PROMPT_CONFIG
import time

def simple_game():
    print("开始简化游戏测试...")
    
    # 创建游戏
    game = PokerGame(num_players=2, starting_chips=500)
    
    # 只使用一个LLM客户端
    llm_client = LLMClient("qwen3")
    
    # 重置游戏
    game.reset_round()
    game.deal_cards()
    
    # 收取盲注
    sb_pos = (game.dealer_pos + 1) % game.num_players
    sb_player = game.players[sb_pos]
    sb_amount = min(game.small_blind, sb_player.chips)
    sb_player.chips -= sb_amount
    sb_player.current_bet = sb_amount
    game.pot += sb_amount
    
    bb_pos = (game.dealer_pos + 2) % game.num_players
    bb_player = game.players[bb_pos]
    bb_amount = min(game.big_blind, bb_player.chips)
    bb_player.chips -= bb_amount
    bb_player.current_bet = bb_amount
    game.pot += bb_amount
    
    game.current_bet = bb_amount
    game.current_player = (bb_pos + 1) % game.num_players
    
    print(f"收取盲注: {sb_player.name} 小盲 {sb_amount}, {bb_player.name} 大盲 {bb_amount}")
    
    # 获取第一个玩家的动作
    current_player = game.players[game.current_player]
    game_state = game.get_game_state_text()
    player_hand = game.get_player_hand_text(current_player)
    
    current_bet_to_call = game.current_bet - current_player.current_bet
    game_state += f"\n当前玩家: {current_player.name}"
    game_state += f"\n需要跟注: {current_bet_to_call} 筹码"
    game_state += f"\n你的筹码: {current_player.chips}"
    
    print(f"\n游戏状态:")
    print(game_state)
    print(f"\n玩家手牌: {player_hand}")
    
    # 获取LLM决策
    print(f"\n正在获取 {current_player.name} 的决策...")
    action = llm_client.get_action(game_state, player_hand, PROMPT_CONFIG["system_prompt"])
    print(f"{current_player.name} 的动作: {action}")
    
    # 执行动作
    action_lower = action.lower()
    if "fold" in action_lower:
        current_player.is_active = False
        print(f"{current_player.name} 弃牌")
    elif "call" in action_lower:
        call_amount = min(current_bet_to_call, current_player.chips)
        current_player.chips -= call_amount
        current_player.current_bet += call_amount
        game.pot += call_amount
        print(f"{current_player.name} 跟注 {call_amount}")
    elif "raise" in action_lower:
        raise_amount = llm_client.get_raise_amount(action, current_player.chips)
        if raise_amount == 0:
            raise_amount = current_player.chips // 2
        current_player.chips -= raise_amount
        current_player.current_bet += raise_amount
        game.pot += raise_amount
        game.current_bet = current_player.current_bet
        print(f"{current_player.name} 加注到 {raise_amount}")
    
    # 摊牌
    winners = game.get_winner()
    print(f"\n--- 摊牌 ---")
    print(f"底池: {game.pot} 筹码")
    
    for player in game.players:
        if player.is_active:
            hand_text = game.get_player_hand_text(player)
            print(f"{player.name}: {hand_text}")
    
    if winners:
        winner_names = [w.name for w in winners]
        print(f"获胜者: {', '.join(winner_names)}")
        game.distribute_pot(winners)
        
        for winner in winners:
            print(f"{winner.name} 获得筹码，当前筹码: {winner.chips}")
    
    print("\n游戏结束！")

if __name__ == "__main__":
    simple_game() 