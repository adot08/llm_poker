"""
LLM客户端 - 处理与LLM API的交互
"""

import openai
from typing import Dict, Any, Optional
from config import LLM_CONFIGS


class LLMClient:
    def __init__(self, llm_type: str = "qwen3"):
        """
        初始化LLM客户端
        
        Args:
            llm_type: LLM类型 ("qwen3" 或 "qwen2.5")
        """
        if llm_type not in LLM_CONFIGS:
            raise ValueError(f"不支持的LLM类型: {llm_type}")
        
        self.config = LLM_CONFIGS[llm_type]
        # 为每个客户端创建独立的配置
        import openai
        self.client = openai
        self.api_key = self.config["api_key"]
        self.api_base = self.config["url"]
        self.model = self.config["model"]
        self.model = self.config["model"]
    
    def get_action(self, game_state: str, player_hand: str, system_prompt: str) -> tuple:
        """
        从LLM获取玩家动作
        
        Args:
            game_state: 游戏状态描述
            player_hand: 玩家手牌
            system_prompt: 系统提示词
            
        Returns:
            (action, llm_input, llm_output) 元组
        """
        try:
            user_prompt = f"""
游戏状态：
{game_state}

你的手牌：{player_hand}

请根据以上信息做出决策。
"""
            
            # 构建LLM输入
            llm_input = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 50
            }
            
            # 临时设置API配置
            self.client.api_key = self.api_key
            self.client.api_base = self.api_base
            
            response = self.client.ChatCompletion.create(**llm_input)
            
            action = response.choices[0].message.content.strip()
            llm_output = action
            
            return action, llm_input, llm_output
            
        except Exception as e:
            print(f"LLM API调用失败: {e}")
            # 返回默认动作
            default_action = "fold"
            llm_input = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"游戏状态：{game_state}\n你的手牌：{player_hand}"}
                ],
                "temperature": 0.7,
                "max_tokens": 50,
                "error": str(e)
            }
            return default_action, llm_input, default_action
    
    def get_raise_amount(self, action: str, max_amount: int) -> int:
        """
        从LLM动作中解析加注金额
        
        Args:
            action: LLM返回的动作字符串
            max_amount: 最大可加注金额
            
        Returns:
            加注金额
        """
        try:
            if "raise" in action.lower():
                # 尝试提取数字
                import re
                numbers = re.findall(r'\d+', action)
                if numbers:
                    amount = int(numbers[0])
                    return min(amount, max_amount)
                else:
                    # 如果没有数字，返回最小加注
                    return max_amount // 2
            elif "all-in" in action.lower() or "allin" in action.lower():
                return max_amount
            else:
                return 0
        except:
            return 0 