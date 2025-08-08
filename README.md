# Multi-Agent LLM Texas Hold'em Simulator

[English](README.md) | [中文](README_CN.md)

A multi-agent Texas Hold'em poker simulator powered by LLMs, featuring smarter LLM interaction and precise game-state prompting.

> Language note: This project is developed in a Chinese-language environment. By default, the system prompt, CLI output, and logs are in Chinese. You can customize prompts and messages to English if desired (see Configuration below).

## Quick Preview

Sample hand log excerpt (Chinese UI by default):

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

## Features

- **Intelligent LLM decisions**: Each LLM first produces detailed reasoning and then outputs a final decision inside an `<action>...</action>` tag, improving interpretability.
- **Precise state prompting**: Carefully designed context includes each player's starting stack, a round-separated betting history, and turn-specific information for the current player.
- **Multiple LLM support**: Configure and switch between multiple LLM backends in `config.py`.
- **Complete Texas Hold'em rules**: Blinds, Preflop, Flop, Turn, River, and showdown.
- **Robust chip management**: Supports check, call, raise, all-in, and fold, with correct side-pot handling.
- **Detailed logging**: Full trace of each hand including LLM inputs/outputs and parsed actions, saved under the `logs/` directory.
- **Log viewer tool**: Use `log_viewer.py` to list sessions and inspect summaries or specific hands.

## Installation

```bash
git clone <repository-url>
cd LLMPoker
pip install -r requirements.txt
```

Requirements (from `requirements.txt`): `poker`, `openai`, `python-dotenv`, `rich`, `typing-extensions`.

## Quick Start

### Run from the command line

```bash
# Run with defaults (4 players, 1000 starting chips, 10 hands)
python main.py

# Customize number of players, starting chips, and number of hands
python main.py --players 6 --chips 2000 --hands 50
```

### CLI options (`main.py`)

- `--players, -p`: Number of players (default: 4)
- `--chips, -c`: Starting chips (default: value from `GAME_CONFIG['starting_chips']`, 1000 by default)
- `--hands, -n`: Number of hands to play (default: 10)

### View game logs (`log_viewer.py`)

```bash
# List all recorded sessions
python log_viewer.py --list

# View summary for a specific session
python log_viewer.py --session <session_id>

# View a specific hand within a session
python log_viewer.py --session <session_id> --hand <hand_number>
```

## Logging

- **Where**: Logs are written under `logs/<session_id>/` (e.g., `logs/20250101_120000/`).
- **Files**:
  - `session_summary.json`: Session-level summary, start/end times, final results.
  - `hand_<n>.json`: One file per hand with rounds, actions, showdown, and end-of-hand chip counts.
- **Action details**: Each action includes the player's name and hand, raw LLM input/output, the parsed action, and the human-readable result string printed in the console.

Minimal example of a `hand_16.json` (truncated):

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

## Configuration

All key settings live in `config.py`:

- **LLM API configs (`LLM_CONFIGS`)**: For each logical LLM type, set an OpenAI-compatible `url` (can be local or remote), `model` name, and `api_key`.
- **Game parameters (`GAME_CONFIG`)**: Small blind, big blind, starting chips, and min/max players.
- **System prompt (`PROMPT_CONFIG['system_prompt']`)**: The default system prompt is written in Chinese and instructs the model to output a single action inside `<action>...</action>`. The expected actions are:
  - `fold`
  - `check`
  - `call`
  - `raise [amount]` — where `[amount]` is the total bet after raising in the current round (e.g., if the current bet is 20 and you want to make it 80, use `raise 80`)
  - `all-in`

You can replace the system prompt with an English version if you prefer an English-only environment.

### LLM interaction details

The app sends:
- A system prompt (Chinese by default) from `PROMPT_CONFIG['system_prompt']`
- A user prompt that includes the game state, the player's hole cards, and instructions to provide reasoning followed by a final decision inside `<action>...</action>`

The client expects the final decision to be parsable from the `<action>` tag. If parsing fails or the action is illegal for the current state, a safe fallback is applied.

## Project Structure

```
LLMPoker/
├── main.py              # Entry point (CLI)
├── game_manager.py      # Game manager orchestrating the flow
├── poker_engine.py      # Poker engine: rules and state management
├── llm_client.py        # LLM client using OpenAI-compatible API
├── logger.py            # Structured logging of games and hands
├── log_viewer.py        # CLI tool to browse logs
├── config.py            # Configuration (LLMs, game settings, prompts)
└── requirements.txt     # Dependencies
```

## Notes and Tips

- **Chinese defaults**: Console text, logs, and system prompt are in Chinese by default. Adjust `PROMPT_CONFIG['system_prompt']`, and optionally translate UI strings in `main.py` and `log_viewer.py` if you need English-only output.
- **OpenAI-compatible servers**: `llm_client.py` uses the `OpenAI` Python SDK with a configurable `base_url`. Point it to your local or remote server and set the `api_key` as needed in `config.py`.
- **Side pots**: The engine supports side-pot logic; ensure your LLM understands raise semantics ("raise to" total for the current round) as described above.

## License

Specify your license here (e.g., MIT).