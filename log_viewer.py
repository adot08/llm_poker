"""
日志查看工具 - 方便查看和分析游戏日志
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint


class LogViewer:
    def __init__(self, log_dir: str):
        self.log_dir = Path(log_dir)
        self.console = Console()
        
    def list_sessions(self):
        """列出所有会话"""
        if not self.log_dir.exists():
            print(f"日志目录不存在: {self.log_dir}")
            return
        
        sessions = [d for d in self.log_dir.iterdir() if d.is_dir()]
        if not sessions:
            print("没有找到任何会话日志")
            return
        
        table = Table(title="游戏会话列表")
        table.add_column("会话ID", style="cyan")
        table.add_column("开始时间", style="green")
        table.add_column("手牌数量", style="yellow")
        table.add_column("玩家数量", style="magenta")
        
        for session in sorted(sessions, reverse=True):
            summary_file = session / "session_summary.json"
            if summary_file.exists():
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                
                table.add_row(
                    session.name,
                    summary.get("start_time", "未知")[:19],
                    str(summary.get("final_results", {}).get("total_hands", 0)),
                    str(len(summary.get("final_results", {}).get("final_chips", {})))
                )
        
        self.console.print(table)
    
    def view_session(self, session_id: str):
        """查看特定会话"""
        session_dir = self.log_dir / session_id
        if not session_dir.exists():
            print(f"会话不存在: {session_id}")
            return
        
        summary_file = session_dir / "session_summary.json"
        if not summary_file.exists():
            print(f"会话总结文件不存在: {summary_file}")
            return
        
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary = json.load(f)
        
        # 显示会话概览
        self.console.print(Panel.fit(
            f"[bold blue]会话概览[/bold blue]\n"
            f"[green]会话ID:[/green] {summary['session_id']}\n"
            f"[green]开始时间:[/green] {summary['start_time']}\n"
            f"[green]结束时间:[/green] {summary.get('end_time', '进行中')}\n"
            f"[green]总手数:[/green] {summary.get('final_results', {}).get('total_hands', 0)}",
            title="会话信息"
        ))
        
        # 显示最终结果
        final_results = summary.get("final_results", {})
        if final_results:
            table = Table(title="最终筹码统计")
            table.add_column("玩家", style="cyan")
            table.add_column("最终筹码", style="green")
            table.add_column("盈亏", style="yellow")
            
            final_chips = final_results.get("final_chips", {})
            winner_stats = final_results.get("winner_stats", {})
            
            for player, chips in final_chips.items():
                # 计算盈亏（假设起始筹码为1000）
                starting_chips = 1000
                profit = chips - starting_chips
                profit_text = f"+{profit}" if profit > 0 else str(profit)
                profit_style = "green" if profit > 0 else "red" if profit < 0 else "white"
                
                wins = winner_stats.get(player, 0)
                table.add_row(
                    f"{player} (胜{wins}次)",
                    str(chips),
                    f"[{profit_style}]{profit_text}[/{profit_style}]"
                )
            
            self.console.print(table)
    
    def view_hand(self, session_id: str, hand_num: int):
        """查看特定手牌"""
        session_dir = self.log_dir / session_id
        hand_file = session_dir / f"hand_{hand_num}.json"
        
        if not hand_file.exists():
            print(f"手牌文件不存在: {hand_file}")
            return
        
        with open(hand_file, 'r', encoding='utf-8') as f:
            hand_data = json.load(f)
        
        # 显示手牌概览
        self.console.print(Panel.fit(
            f"[bold blue]第 {hand_num} 手牌[/bold blue]\n"
            f"[green]开始时间:[/green] {hand_data['start_time']}\n"
            f"[green]结束时间:[/green] {hand_data.get('end_time', '进行中')}\n"
            f"[green]获胜者:[/green] {', '.join(hand_data.get('final_state', {}).get('winners', []))}",
            title="手牌信息"
        ))
        
        # 显示每轮动作
        for round_data in hand_data.get("rounds", []):
            self.console.print(f"\n[bold yellow]--- {round_data['round_name'].upper()} 轮 ---[/bold yellow]")
            
            for action in round_data.get("actions", []):
                player = action["player_name"]
                hand = " ".join(action["player_hand"])
                llm_output = action["llm_output"]
                parsed_action = action["parsed_action"]
                result = action["action_result"]["message"]
                
                self.console.print(f"👤 {player} 手牌: {hand}")
                self.console.print(f"🤖 原始输出: {llm_output}")
                self.console.print(f"✅ 解析动作: {parsed_action}")
                self.console.print(f"📝 执行结果: {result}")
                self.console.print("")
        
        # 显示摊牌
        showdown = hand_data.get("showdown", {})
        if showdown:
            self.console.print("[bold red]--- 摊牌 ---[/bold red]")
            for player_info in showdown.get("players_info", []):
                self.console.print(f"👤 {player_info['name']}: {player_info['hand']}")
            
            winners = showdown.get("winners", [])
            if winners:
                self.console.print(f"🏆 获胜者: {', '.join(winners)}")
    
    def view_llm_details(self, session_id: str, hand_num: int, player_name: str = None):
        """查看LLM详细信息"""
        session_dir = self.log_dir / session_id
        hand_file = session_dir / f"hand_{hand_num}.json"
        
        if not hand_file.exists():
            print(f"手牌文件不存在: {hand_file}")
            return
        
        with open(hand_file, 'r', encoding='utf-8') as f:
            hand_data = json.load(f)
        
        self.console.print(f"[bold blue]第 {hand_num} 手牌 LLM 详细信息[/bold blue]\n")
        
        for round_data in hand_data.get("rounds", []):
            for action in round_data.get("actions", []):
                if player_name and action["player_name"] != player_name:
                    continue
                
                player = action["player_name"]
                self.console.print(f"[bold cyan]{player}[/bold cyan]")
                
                # 显示LLM输入
                llm_input = action["llm_input"]
                self.console.print(f"[green]模型:[/green] {llm_input['model']}")
                self.console.print(f"[green]温度:[/green] {llm_input['temperature']}")
                self.console.print(f"[green]最大token:[/green] {llm_input['max_tokens']}")
                
                # 显示消息
                for i, message in enumerate(llm_input["messages"]):
                    role = message["role"]
                    content = message["content"]
                    self.console.print(f"[yellow]{role}:[/yellow] {content[:200]}...")
                
                # 显示输出
                self.console.print(f"[green]LLM输出:[/green] {action['llm_output']}")
                self.console.print(f"[green]解析动作:[/green] {action['parsed_action']}")
                self.console.print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="游戏日志查看工具")
    parser.add_argument("--log-dir", "-d", default="logs", help="日志目录")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有会话")
    parser.add_argument("--session", "-s", help="查看特定会话")
    parser.add_argument("--hand", "-n", type=int, help="查看特定手牌")
    parser.add_argument("--player", "-p", help="查看特定玩家的LLM详情")
    parser.add_argument("--llm-details", action="store_true", help="显示LLM详细信息")
    
    args = parser.parse_args()
    
    viewer = LogViewer(args.log_dir)
    
    if args.list:
        viewer.list_sessions()
    elif args.session:
        if args.hand:
            if args.llm_details:
                viewer.view_llm_details(args.session, args.hand, args.player)
            else:
                viewer.view_hand(args.session, args.hand)
        else:
            viewer.view_session(args.session)
    else:
        viewer.list_sessions()


if __name__ == "__main__":
    main() 