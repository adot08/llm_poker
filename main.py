"""
主程序入口 - Multi-Agent LLM 德州扑克模拟器
"""

import argparse
from game_manager import GameManager
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent LLM 德州扑克模拟器")
    parser.add_argument("--players", "-p", type=int, default=4, 
                       help="玩家数量 (默认: 4)")
    parser.add_argument("--chips", "-c", type=int, default=1000,
                       help="起始筹码数量 (默认: 1000)")
    parser.add_argument("--hands", "-n", type=int, default=10,
                       help="游戏手数 (默认: 10)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="详细输出模式")
    
    args = parser.parse_args()
    
    # 验证参数
    if args.players < 2 or args.players > 6:
        print("错误: 玩家数量必须在2-6之间")
        return
    
    if args.chips < 100:
        print("错误: 起始筹码不能少于100")
        return
    
    if args.hands < 1:
        print("错误: 游戏手数必须大于0")
        return
    
    console = Console()
    
    # 显示游戏信息
    title = Panel.fit(
        "[bold blue]Multi-Agent LLM 德州扑克模拟器[/bold blue]\n"
        f"[green]玩家数量:[/green] {args.players}\n"
        f"[green]起始筹码:[/green] {args.chips}\n"
        f"[green]游戏手数:[/green] {args.hands}",
        title="游戏设置"
    )
    console.print(title)
    
    try:
        # 创建游戏管理器
        game_manager = GameManager(args.players, args.chips)
        
        # 开始游戏
        results = game_manager.play_game(args.hands)
        
        # 显示最终结果
        console.print("\n" + "="*60)
        console.print("[bold green]游戏结束！[/bold green]")
        console.print("="*60)
        
        # 显示日志路径
        log_path = game_manager.logger.get_log_path()
        console.print(f"\n[bold blue]详细日志已保存到:[/bold blue] {log_path}")
        console.print(f"[dim]包含每手牌的完整记录和LLM输入输出[/dim]")
        
        # 创建结果表格
        table = Table(title="最终筹码统计")
        table.add_column("玩家", style="cyan")
        table.add_column("LLM类型", style="magenta")
        table.add_column("最终筹码", style="green")
        table.add_column("盈亏", style="yellow")
        
        for player in game_manager.game.players:
            profit = player.chips - args.chips
            profit_text = f"+{profit}" if profit > 0 else str(profit)
            profit_style = "green" if profit > 0 else "red" if profit < 0 else "white"
            
            table.add_row(
                player.name,
                player.llm_type,
                str(player.chips),
                f"[{profit_style}]{profit_text}[/{profit_style}]"
            )
        
        console.print(table)
        
        # 显示获胜统计
        winner_stats = {}
        for result in results:
            for winner in result["winners"]:
                winner_stats[winner] = winner_stats.get(winner, 0) + 1
        
        if winner_stats:
            console.print("\n[bold]获胜统计:[/bold]")
            for player, wins in sorted(winner_stats.items(), key=lambda x: x[1], reverse=True):
                console.print(f"  {player}: {wins} 次获胜")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]游戏被用户中断[/yellow]")
    except Exception as e:
        console.print(f"\n[red]游戏运行出错: {e}[/red]")


if __name__ == "__main__":
    main() 