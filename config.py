"""
配置文件 - LLM API端点和模型设置
"""

# LLM API配置
LLM_CONFIGS = {
    "qwen3": {
        "url": "http://10.10.4.83:9998/v1",
        "model": "qwen3-instruct",
        "api_key": "dummy"  # 如果不需要API key可以设为dummy
    },
    "qwen2.5": {
        "url": "http://10.10.2.71:8007/v1", 
        "model": "Qwen/Qwen2.5-72B-Instruct-Raw",
        "api_key": "dummy"
    }
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
    "system_prompt": """你是一个德州扑克玩家。你需要根据当前游戏状态做出决策。

游戏规则：
- 德州扑克有4轮：preflop, flop, turn, river
- 每轮你可以：check(过牌), call(跟注), raise(加注), fold(弃牌), all-in(全下)
- 你的目标是赢得底池中的筹码

请根据游戏状态信息做出决策，只回复一个动作：
- check
- call  
- raise [金额]
- fold
- all-in"""
} 