# llm_client.py

from openai import OpenAI
import re
from typing import Dict, Any, List
from config import LLM_CONFIGS

class LLMClient:
    def __init__(self, llm_type: str):
        if llm_type not in LLM_CONFIGS:
            raise ValueError(f"不支持的LLM类型: {llm_type}")
        
        self.config = LLM_CONFIGS[llm_type]
        self.model = self.config["model"]
        
        try:
            self.client = OpenAI(
                api_key=self.config["api_key"],
                base_url=self.config["url"]
            )
        except Exception as e:
            raise ConnectionError(f"无法初始化 {llm_type} 的OpenAI客户端: {e}")

    def get_action(self, game_state: str, player_hand: str, system_prompt: str) -> tuple:
        user_prompt = (
            f"游戏状态:\n{game_state}\n\n"
            f"你的手牌: {player_hand}\n\n"
            "请先对当前局势进行详细分析，说明你的思考过程，然后将最终决策放在 <action>...</action> 标签中。\n"
            "例如: <action>raise 100</action> 或 <action>fold</action>.\n\n"
            "你的分析和决策:"
        )
        
        llm_input = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
        }
        
        try:
            response = self.client.chat.completions.create(**llm_input)
            # TODO: 看一下gptoss的输出，应该是在think部分的。这部分的output要加进来
            raw_action = response.choices[0].message.content.strip()
            parsed_action = self._parse_action(raw_action)
            try:
                reasoning_content = response.choices[0].message.reasoning_content
            except AttributeError:
                reasoning_content = None
            if reasoning_content:
                raw_action = f"{reasoning_content}\n{raw_action}"
            return parsed_action, llm_input, raw_action
            
        except Exception as e:
            print(f"LLM API调用失败 for {self.config['model']}: {e}")
            default_action = {'action': 'fold'}
            llm_input["error"] = str(e)
            return default_action, llm_input, "API_ERROR"

    def _parse_action(self, text: str) -> Dict[str, Any]:
        """将LLM的文本输出解析为标准动作字典.
        
        优先从 <action>...</action> 标签中提取动作.
        """
        action_text = text
        
        # 尝试从<action>标签中提取内容
        action_match = re.search(r'<action>(.*?)</action>', text, re.IGNORECASE | re.DOTALL)
        if action_match:
            action_text = action_match.group(1).strip()
        
        text_lower = action_text.lower()
        
        if "all-in" in text_lower or "allin" in text_lower:
            return {'action': 'all-in'}
        
        if "raise" in text_lower:
            numbers = re.findall(r'\d+', action_text) # Search in the extracted part
            if numbers:
                return {'action': 'raise', 'amount': int(numbers[0])}
            else: # 如果LLM只说raise但没给金额，这是个问题，安全起见我们当作弃牌
                return {'action': 'fold'}

        if "call" in text_lower:
            return {'action': 'call'}
        
        if "check" in text_lower:
            return {'action': 'check'}

        if "fold" in text_lower:
            return {'action': 'fold'}
        
        # 如果无法解析，默认弃牌
        return {'action': 'fold'}