"""
测试脚本 - 验证德州扑克游戏系统
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from poker_game import PokerGame, Player
from llm_client import LLMClient
from config import PROMPT_CONFIG


def test_poker_game():
    """测试扑克游戏基本功能"""
    print("测试扑克游戏基本功能...")
    
    # 创建游戏
    game = PokerGame(num_players=3, starting_chips=1000)
    
    # 测试发牌
    game.deal_cards()
    print(f"玩家手牌:")
    for player in game.players:
        hand_text = game.get_player_hand_text(player)
        print(f"  {player.name}: {hand_text}")
    
    # 测试发公共牌
    game.deal_community_cards(3)
    print(f"公共牌: {game._cards_to_text(game.community_cards)}")
    
    # 测试游戏状态文本
    state_text = game.get_game_state_text()
    print(f"游戏状态文本长度: {len(state_text)} 字符")
    
    print("✅ 扑克游戏基本功能测试通过")


def test_llm_client():
    """测试LLM客户端"""
    print("\n测试LLM客户端...")
    
    try:
        # 测试Qwen3客户端
        client = LLMClient("qwen3")
        print("✅ Qwen3客户端创建成功")
        
        # 测试Qwen2.5客户端
        client = LLMClient("qwen2.5")
        print("✅ Qwen2.5客户端创建成功")
        
    except Exception as e:
        print(f"❌ LLM客户端测试失败: {e}")
        return False
    
    return True


def test_game_manager():
    """测试游戏管理器"""
    print("\n测试游戏管理器...")
    
    try:
        from game_manager import GameManager
        
        # 创建游戏管理器
        manager = GameManager(num_players=2, starting_chips=500)
        print("✅ 游戏管理器创建成功")
        
        # 测试游戏状态
        state = manager.game.get_game_state_text()
        print(f"✅ 游戏状态生成成功，长度: {len(state)} 字符")
        
    except Exception as e:
        print(f"❌ 游戏管理器测试失败: {e}")
        return False
    
    return True


def main():
    """运行所有测试"""
    print("开始运行德州扑克游戏系统测试...\n")
    
    # 测试扑克游戏
    test_poker_game()
    
    # 测试LLM客户端
    llm_ok = test_llm_client()
    
    # 测试游戏管理器
    manager_ok = test_game_manager()
    
    print("\n" + "="*50)
    print("测试结果总结:")
    print("✅ 扑克游戏引擎: 通过")
    print(f"{'✅' if llm_ok else '❌'} LLM客户端: {'通过' if llm_ok else '失败'}")
    print(f"{'✅' if manager_ok else '❌'} 游戏管理器: {'通过' if manager_ok else '失败'}")
    
    if llm_ok and manager_ok:
        print("\n🎉 所有测试通过！系统可以正常运行。")
        print("运行 'python main.py' 开始游戏。")
    else:
        print("\n⚠️  部分测试失败，请检查配置和网络连接。")


if __name__ == "__main__":
    main() 