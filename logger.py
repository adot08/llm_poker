# logger.py
# (无需改动，使用你提供的原始文件即可)

import json
import os
import time
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

class GameLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.log_dir / self.session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.session_info = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "hands": []
        }
        print(f"📁 日志目录: {self.session_dir}")
    
    def log_hand_start(self, hand_num: int, game_config: Dict[str, Any]):
        hand_info = {
            "hand_num": hand_num,
            "start_time": datetime.now().isoformat(),
            "game_config": game_config,
            "rounds": []
        }
        self.session_info["hands"].append(hand_info)
        self.current_hand_info = hand_info
        print(f"📝 开始记录第 {hand_num} 手牌")
    
    def log_round_start(self, round_name: str, community_cards: List[str]):
        round_info = {
            "round_name": round_name,
            "start_time": datetime.now().isoformat(),
            "community_cards": community_cards,
            "actions": []
        }
        self.current_hand_info["rounds"].append(round_info)
        self.current_round_info = round_info
    
    def log_player_action(self, player_name: str, player_hand: List[str], 
                         llm_input: Dict[str, Any], llm_output: str, 
                         parsed_action: Dict[str, Any], action_result: str):
        action_info = {
            "player_name": player_name,
            "player_hand": [str(c) for c in player_hand],
            "timestamp": datetime.now().isoformat(),
            "llm_input": llm_input,
            "llm_output": llm_output,
            "parsed_action": parsed_action,
            "action_result": action_result
        }
        self.current_round_info["actions"].append(action_info)
    
    def log_showdown(self, winner_results: List[Dict]):
        showdown_info = {
            "timestamp": datetime.now().isoformat(),
            "results": []
        }
        for res in winner_results:
            showdown_info["results"].append({
                'pot_amount': res['pot']['amount'],
                'eligible_players': [p.name for p in res['pot']['eligible_players']],
                'winners': [w.name for w in res['winners']],
                'hand_name': res['hand_details'][0],
                'hand_cards': [str(c) for c in res['hand_details'][1]]
            })
        self.current_hand_info["showdown"] = showdown_info
    
    def log_hand_end(self, final_chips: Dict[str, int]):
        self.current_hand_info["end_time"] = datetime.now().isoformat()
        self.current_hand_info["final_chips"] = final_chips
        hand_file = self.session_dir / f"hand_{self.current_hand_info['hand_num']}.json"
        with open(hand_file, 'w', encoding='utf-8') as f:
            json.dump(self.current_hand_info, f, ensure_ascii=False, indent=2)
        print(f"💾 第 {self.current_hand_info['hand_num']} 手牌日志已保存: {hand_file}")
    
    def log_session_end(self, final_chips: Dict[str, int], winner_stats: Dict[str, int]):
        self.session_info["end_time"] = datetime.now().isoformat()
        self.session_info["final_results"] = {
            "final_chips": final_chips,
            "winner_stats": winner_stats
        }
        session_file = self.session_dir / "session_summary.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(self.session_info, f, ensure_ascii=False, indent=2)
        print(f"💾 会话总结已保存: {session_file}")

    def get_log_path(self) -> str:
        return str(self.session_dir)