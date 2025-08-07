# Multi-Agent LLM 德州扑克模拟器

一个基于LLM的多智能体德州扑克游戏模拟器，支持纯文本状态维护和多种LLM模型。

## 功能特点

- 🎮 **纯文本状态维护**: 所有游戏状态都以纯文本形式维护和展示
- 🤖 **多LLM支持**: 支持多个LLM模型作为玩家
- 🎯 **完整德州扑克规则**: 包含preflop、flop、turn、river四个轮次
- 💰 **筹码管理**: 完整的筹码下注、跟注、加注、全下机制
- 📊 **详细统计**: 游戏结果和玩家表现统计
- 🎨 **美观界面**: 使用Rich库提供彩色终端界面
- 📝 **详细日志**: 完整的游戏记录和LLM输入输出日志
- 👁️ **旁观者视角**: 显示所有玩家的手牌和决策过程

## 支持的LLM模型

- **Qwen3**: `http://10.10.4.83:9998/v1` - `qwen3-instruct`
- **Qwen2.5**: `http://10.10.2.71:8007/v1` - `Qwen/Qwen2.5-72B-Instruct-Raw`

## 安装

1. 克隆项目：
```bash
git clone <repository-url>
cd LLMPoker
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
# 使用默认设置运行游戏 (4个玩家，1000筹码，10手牌)
python main.py

# 自定义玩家数量和筹码
python main.py --players 6 --chips 2000 --hands 20

# 详细输出模式
python main.py --verbose
```

### 命令行参数

- `--players, -p`: 玩家数量 (2-6，默认: 4)
- `--chips, -c`: 起始筹码数量 (默认: 1000)
- `--hands, -n`: 游戏手数 (默认: 10)
- `--verbose, -v`: 详细输出模式

### 示例

```bash
# 6个玩家，每人2000筹码，玩30手牌
python main.py -p 6 -c 2000 -n 30

# 2个玩家快速游戏
python main.py -p 2 -c 500 -n 5
```

### 日志查看
```bash
# 列出所有游戏会话
python log_viewer.py --list

# 查看特定会话
python log_viewer.py --session 20250807_104812

# 查看特定手牌
python log_viewer.py --session 20250807_104812 --hand 2

# 查看LLM详细信息
python log_viewer.py --session 20250807_104812 --hand 2 --llm-details

# 查看特定玩家的LLM详情
python log_viewer.py --session 20250807_104812 --hand 2 --llm-details --player Player_3
```

## 游戏规则

### 基本规则
- 德州扑克标准规则
- 小盲注: 10筹码，大盲注: 20筹码
- 支持的动作: check(过牌), call(跟注), raise(加注), fold(弃牌), all-in(全下)

### 游戏流程
1. **Preflop**: 发手牌，收取盲注，进行第一轮下注
2. **Flop**: 发3张公共牌，进行第二轮下注
3. **Turn**: 发第4张公共牌，进行第三轮下注
4. **River**: 发第5张公共牌，进行最后一轮下注
5. **Showdown**: 摊牌，确定获胜者，分配底池

### LLM决策
每个LLM玩家会根据以下信息做出决策：
- 自己的手牌
- 公共牌
- 当前筹码数量
- 其他玩家的下注情况
- 游戏轮次

## 项目结构

```
LLMPoker/
├── main.py              # 主程序入口
├── game_manager.py      # 游戏管理器
├── poker_game.py        # 扑克游戏引擎
├── llm_client.py        # LLM客户端
├── logger.py            # 日志记录模块
├── log_viewer.py        # 日志查看工具
├── config.py            # 配置文件
├── requirements.txt     # 依赖包
├── test_*.py           # 测试脚本
└── README.md           # 项目说明
```

## 配置

可以在 `config.py` 中修改以下配置：

- LLM API端点和模型
- 游戏参数（盲注、起始筹码等）
- LLM提示词模板

## 技术栈

- **poker**: 德州扑克规则引擎
- **openai**: LLM API客户端
- **rich**: 终端美化库
- **typing**: 类型提示

## 注意事项

1. 确保LLM API服务可用
2. 网络连接稳定，避免API调用失败
3. 游戏过程中可以按Ctrl+C中断

## 故障排除

### LLM API连接失败
- 检查网络连接
- 验证API端点地址
- 确认LLM服务正在运行

### 游戏卡住
- 检查是否有玩家进入无限循环
- 验证下注逻辑是否正确
- 查看详细输出模式获取更多信息

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 许可证

MIT License 