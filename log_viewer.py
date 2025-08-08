# log_viewer.py
# (只需微调 showdown 部分，其余保持原样)

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
        if not self.log_dir.exists(): rprint(f"[red]日志目录不存在: {self.log_dir}[/red]"); return
        sessions = sorted([d for d in self.log_dir.iterdir() if d.is_dir()], reverse=True)
        if not sessions: rprint("[yellow]没有找到任何会话日志[/yellow]"); return
        
        table = Table(title="游戏会话列表")
        table.add_column("会话ID", style="cyan"); table.add_column("开始时间", style="green")
        table.add_column("手牌数量", style="yellow"); table.add_column("玩家数量", style="magenta")
        
        for session in sessions:
            summary_file = session / "session_summary.json"
            if summary_file.exists():
                with open(summary_file, 'r', encoding='utf-8') as f: summary = json.load(f)
                hands_played = len(summary.get("hands", []))
                player_count = len(summary.get("final_results", {}).get("final_chips", {}))
                table.add_row(session.name, summary.get("start_time", "未知")[:19], str(hands_played), str(player_count))
        self.console.print(table)
    
    def view_session(self, session_id: str):
        session_dir = self.log_dir / session_id
        if not session_dir.exists(): rprint(f"[red]会话不存在: {session_id}[/red]"); return
        summary_file = session_dir / "session_summary.json"
        if not summary_file.exists(): rprint(f"[red]会话总结文件不存在: {summary_file}[/red]"); return
        
        with open(summary_file, 'r', encoding='utf-8') as f: summary = json.load(f)
        
        final_results = summary.get("final_results", {})
        if final_results:
            table = Table(title="最终筹码统计")
            table.add_column("玩家", style="cyan"); table.add_column("最终筹码", style="green"); table.add_column("获胜次数", style="blue")
            
            final_chips = final_results.get("final_chips", {})
            winner_stats = final_results.get("winner_stats", {})
            for player, chips in sorted(final_chips.items(), key=lambda x: x[1], reverse=True):
                table.add_row(player, str(chips), str(winner_stats.get(player, 0)))
            self.console.print(table)
        else:
            rprint("[yellow]会话未完成，无最终结果。[/yellow]")
    
    def view_hand(self, session_id: str, hand_num: int):
        hand_file = self.log_dir / session_id / f"hand_{hand_num}.json"
        if not hand_file.exists(): rprint(f"[red]手牌文件不存在: {hand_file}[/red]"); return
        with open(hand_file, 'r', encoding='utf-8') as f: hand_data = json.load(f)
        
        self.console.print(Panel.fit(f"[bold blue]第 {hand_num} 手牌[/bold blue]"))
        
        for round_data in hand_data.get("rounds", []):
            self.console.print(f"\n[bold yellow]--- {round_data['round_name'].upper()} 轮 (公共牌: {' '.join(round_data['community_cards'])}) ---[/bold yellow]")
            for action in round_data.get("actions", []):
                p = action["player_name"]; h = " ".join(action["player_hand"])
                o = action["llm_output"]; pa = action["parsed_action"]
                r = action["action_result"]
                self.console.print(f"👤 [cyan]{p}[/cyan] (手牌: {h}): {r} (LLM: {o})")
        
        showdown = hand_data.get("showdown", {})
        if showdown and "results" in showdown:
            self.console.print("\n[bold red]--- 摊牌 ---[/bold red]")
            for result in showdown["results"]:
                winners = ', '.join(result['winners'])
                hand_name = result['hand_name']; hand_cards = ' '.join(result['hand_cards'])
                self.console.print(f"🏆 底池 {result['pot_amount']} 由 [bold green]{winners}[/bold green] 赢得")
                self.console.print(f"   牌型: {hand_name} - {hand_cards}")
        else:
            self.console.print("\n[bold red]--- 无需摊牌 ---[/bold red]")

def main():
    parser = argparse.ArgumentParser(description="游戏日志查看工具")
    parser.add_argument("--log-dir", "-d", default="logs", help="日志目录")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有会话")
    parser.add_argument("--session", "-s", help="查看特定会话的总结或手牌")
    parser.add_argument("--hand", "-n", type=int, help="查看特定手牌的详情")
    args = parser.parse_args()
    
    viewer = LogViewer(args.log_dir)
    if args.session and args.hand:
        viewer.view_hand(args.session, args.hand)
    elif args.session:
        viewer.view_session(args.session)
    else:
        viewer.list_sessions()

if __name__ == "__main__":
    main()