# Multi-Agent LLM 德州扑克模拟器

语言: [English](README.md) | [中文](README_CN.md)

一个基于LLM的多智能体德州扑克游戏模拟器，现在拥有更智能的LLM交互和更精确的游戏状态提示。

## 👀 快速预览

示例手牌日志片段（默认中文界面）：

```text
📝 开始记录第 16 手牌
庄家(D): Player-2
Player-1: 手牌 [A♦ T♥]
Player-2: 手牌 [A♥ J♦]

--- PREFLOP 轮 ---
公共牌: []
Player-1 加注到 50
Player-2 跟注 30

--- FLOP 轮 ---
公共牌: [9♠ 5♠ 2♣]
Player-1 加注到 60
Player-2 跟注 60

--- TURN 轮 ---
公共牌: [9♠ 5♠ 2♣ 4♦]
Player-1 过牌
Player-2 加注到 220
Player-1 弃牌

--- 摊牌 ---
Player-2 是唯一幸存者, 赢得底池 440

--- 手牌结束 筹码情况 ---
Player-1: 850
Player-2: 1150
```

## 🚀 主要功能

-   **🧠 智能LLM决策**: LLM会先输出详细的思考过程，然后使用`<action>`标签给出最终决策，极大提升了行为的可解释性。
-   **🎯 精确的状态提示**: 为LLM精心设计了上下文提示，包含每手牌的初始筹码、带轮次分隔的完整下注历史，以及为当前玩家定制的回合信息。
-   **🤖 多LLM支持**: 可通过`config.py`轻松配置和切换多种LLM模型作为玩家。
-   **完整的德州扑克规则**: 实现了完整的德州扑克游戏逻辑，包括盲注、Preflop、Flop、Turn、River以及最终摊牌。
-   **💰 健壮的筹码管理**: 支持check, call, raise, all-in, fold等所有标准动作，并能正确处理边池逻辑。
-   **📝 详细的日志系统**: 每一手牌的完整进程，包括LLM的思考过程和最终决策，都会被记录下来，方便复盘和分析。
-   **👁️ 日志查看工具**: 提供了`log_viewer.py`，可以方便地查看和筛选历史游戏记录。

## 🛠️ 安装

1.  克隆项目:
    ```bash
    git clone <repository-url>
    cd LLMPoker
    ```

2.  安装依赖:
    ```bash
    pip install -r requirements.txt
    ```

## 🎮 使用方法

### 命令行运行

```bash
# 使用默认设置运行游戏 (4个玩家, 1000起始筹码, 运行10手牌)
python main.py

# 自定义玩家数量、起始筹码和游戏手数
python main.py --players 6 --chips 2000 --hands 50
```

### 命令行参数

-   `--players, -p`: 玩家数量 (默认: 4)
-   `--chips, -c`: 起始筹码 (默认: 1000)
-   `--hands, -n`: 游戏手数 (默认: 10)

### 查看游戏日志（`log_viewer.py`）

```bash
# 列出所有已记录的游戏会话
python log_viewer.py --list

# 查看指定会话的摘要
python log_viewer.py --session <session_id>

# 查看指定会话的特定手牌详情
python log_viewer.py --session <session_id> --hand <hand_number>
```

## 📝 日志说明

- **存储位置**: `logs/<session_id>/`（如 `logs/20250101_120000/`）。
- **文件结构**:
  - `session_summary.json`: 会话级汇总（开始/结束时间、最终筹码、胜利统计）。
  - `hand_<n>.json`: 每手牌一个文件，包含轮次、动作、摊牌与手牌结束时筹码。
- **动作详情**: 每个动作都记录玩家名与手牌、LLM输入/输出、解析后的标准动作、以及控制台可读的动作结果字符串。

`hand_16.json` 最小示例（截断）：

```json
{
  "hand_num": 16,
  "rounds": [
    {
      "round_name": "turn",
      "community_cards": ["9♠", "5♠", "2♣", "4♦"],
      "actions": [
        {
          "player_name": "Player-2",
          "llm_input": {"model": "...", "messages": ["..."]},
          "llm_output": "...",
          "parsed_action": {"action": "raise", "amount": 220},
          "action_result": "Player-2 加注到 220"
        }
      ]
    }
  ],
  "showdown": {
    "results": [
      {
        "pot_amount": 440,
        "eligible_players": ["Player-1", "Player-2"],
        "winners": ["Player-2"],
        "hand_name": "未摊牌",
        "hand_cards": []
      }
    ]
  }
}
```

## ⚙️ 配置

所有关键配置都在 `config.py` 中进行：

-   **LLM API配置 (`LLM_CONFIGS`)**: 配置 OpenAI 兼容的 `url`、`model`、`api_key`。
-   **游戏参数 (`GAME_CONFIG`)**: 小盲注、大盲注、起始筹码、最小/最大玩家数。
-   **系统提示词 (`PROMPT_CONFIG['system_prompt']`)**: 默认中文系统提示词，要求最终决策必须放在 `<action>...</action>` 中。支持：
    - `fold`
    - `check`
    - `call`
    - `raise [金额]`（表示当前轮次的总下注，例如当前为20，加注到80写作 `raise 80`）
    - `all-in`

你也可以将系统提示词替换为英文版本，从而获得纯英文环境。

## 🏗️ 项目结构

```
LLMPoker/
├── main.py              # 主程序入口
├── game_manager.py      # 游戏管理器，负责整体游戏流程控制
├── poker_engine.py      # 核心扑克游戏引擎，处理规则和状态
├── llm_client.py        # LLM客户端，负责与大语言模型API交互
├── logger.py            # 日志记录模块
├── log_viewer.py        # 日志查看工具
├── config.py            # 配置文件
└── requirements.txt     # 项目依赖
```

## 备注与提示

- **中文默认**: 控制台文本、日志、系统提示词默认均为中文。可在 `config.py` 中修改 `PROMPT_CONFIG['system_prompt']`，并在 `main.py`、`log_viewer.py` 中按需翻译界面文案。
- **OpenAI 兼容服务**: `llm_client.py` 使用 `OpenAI` Python SDK，支持自定义 `base_url` 指向本地或远程服务器，并在 `config.py` 设置 `api_key`。
- **边池**: 引擎支持边池逻辑；请确保 LLM 明白“加注到”的语义（本轮总下注）。