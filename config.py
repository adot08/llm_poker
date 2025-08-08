"""
配置文件 - LLM API端点、游戏设置和提示词
"""


# LLM API配置
LLM_CONFIGS = {
    "model_1": {
        "url": "http://your_url:9998/v1",
        "model": "your_model",
        "api_key": "dummy"  # 如果不需要API key可以设为dummy
    },
    "model_2": {
        "url": "http://your_url:8007/v1", 
        "model": "your_model",
        "api_key": "dummy"
    },
    "model_3": {
        "url": "http://your_url:8001/v1",
        "model": "deepseek-r1-0528-awq",
        "api_key": "dummy"
    },
}

# 游戏配置
GAME_CONFIG = {
    "small_blind": 10,
    "big_blind": 20,
    "starting_chips": 1000,
    "max_players": 6,
    "min_players": 2
}

# LLM提示词配置
PROMPT_CONFIG = {
    "system_prompt": """你是一个专业的德州扑克AI玩家。你的任务是根据当前牌局信息，做出最优的决策。

你的决策必须严格遵循以下格式之一：
- `fold`：如果你认为应该弃牌。
- `check`：如果你可以在不投入更多筹码的情况下继续游戏。
- `call`：如果你决定跟注。
- `raise [金额]`：如果你决定加注。**[金额]必须是你加注后，在当前轮次的总下注额**。例如，当前下注是20，你想加注到80，你应该回复 `raise 80`。
- `all-in`：如果你决定全下所有筹码。

请在<action>...</action>标签中只回复一个动作指令，不要包含任何解释或额外文字。"""
}