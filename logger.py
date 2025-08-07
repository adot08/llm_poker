"""
日志记录模块 - 记录游戏详细信息和LLM输入输出
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path


class GameLogger:
    def __init__(self, log_dir: str = "logs"):
        """
        初始化游戏日志记录器
        
        Args:
            log_dir: 日志目录
        """
        self.log_dir = Path(log_dir)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.log_dir / self.session_id
        
        # 创建日志目录
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建会话信息文件
        self.session_info = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "hands": []
        }
        
        print(f"📁 日志目录: {self.session_dir}")
    
    def log_hand_start(self, hand_num: int, game_config: Dict[str, Any]):
        """记录一手牌开始"""
        hand_info = {
            "hand_num": hand_num,
            "start_time": datetime.now().isoformat(),
            "game_config": game_config,
            "rounds": []
        }
        
        self.session_info["hands"].append(hand_info)
        self.current_hand = hand_info
        
        print(f"📝 开始记录第 {hand_num} 手牌")
    
    def log_round_start(self, round_name: str, game_state: str, community_cards: List[str]):
        """记录一轮开始"""
        round_info = {
            "round_name": round_name,
            "start_time": datetime.now().isoformat(),
            "game_state": game_state,
            "community_cards": community_cards,
            "actions": []
        }
        
        self.current_hand["rounds"].append(round_info)
        self.current_round = round_info
    
    def log_player_action(self, player_name: str, player_hand: List[str], 
                         llm_input: Dict[str, Any], llm_output: str, 
                         parsed_action: str, action_result: Dict[str, Any]):
        """记录玩家动作"""
        action_info = {
            "player_name": player_name,
            "player_hand": player_hand,
            "timestamp": datetime.now().isoformat(),
            "llm_input": llm_input,
            "llm_output": llm_output,
            "parsed_action": parsed_action,
            "action_result": action_result
        }
        
        self.current_round["actions"].append(action_info)
        
        # 打印旁观者视角的信息
        print(f"👤 {player_name} 手牌: {' '.join(player_hand)}")
        print(f"🤖 {player_name} 原始输出: {llm_output}")
        print(f"✅ {player_name} 解析动作: {parsed_action}")
    
    def log_showdown(self, players_info: List[Dict[str, Any]], winners: List[str], pot: int):
        """记录摊牌"""
        showdown_info = {
            "timestamp": datetime.now().isoformat(),
            "players_info": players_info,
            "winners": winners,
            "pot": pot
        }
        
        self.current_hand["showdown"] = showdown_info
    
    def log_hand_end(self, final_state: Dict[str, Any]):
        """记录一手牌结束"""
        self.current_hand["end_time"] = datetime.now().isoformat()
        self.current_hand["final_state"] = final_state
        
        # 保存当前手牌的详细日志
        hand_file = self.session_dir / f"hand_{self.current_hand['hand_num']}.json"
        with open(hand_file, 'w', encoding='utf-8') as f:
            json.dump(self.current_hand, f, ensure_ascii=False, indent=2)
        
        print(f"💾 第 {self.current_hand['hand_num']} 手牌日志已保存: {hand_file}")
    
    def log_session_end(self, final_results: Dict[str, Any]):
        """记录会话结束"""
        self.session_info["end_time"] = datetime.now().isoformat()
        self.session_info["final_results"] = final_results
        
        # 保存会话总结
        session_file = self.session_dir / "session_summary.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(self.session_info, f, ensure_ascii=False, indent=2)
        
        print(f"💾 会话总结已保存: {session_file}")
    
    def get_log_path(self) -> str:
        """获取日志目录路径"""
        return str(self.session_dir) 