# main.py

import argparse
from game_manager import GameManager
from config import GAME_CONFIG
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import sys
try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

def main():
    parser = argparse.ArgumentParser(description="Multi-Agent LLM 德州扑克模拟器")
    parser.add_argument("--players", "-p", type=int, default=4, help=f"玩家数量 (默认: 4)")
    parser.add_argument("--chips", "-c", type=int, default=GAME_CONFIG['starting_chips'], help=f"起始筹码 (默认: {GAME_CONFIG['starting_chips']})")
    parser.add_argument("--hands", "-n", type=int, default=10, help="游戏手数 (默认: 10)")
    
    args = parser.parse_args()
    
    if not (GAME_CONFIG['min_players'] <= args.players <= GAME_CONFIG['max_players']):
        print(f"错误: 玩家数量必须在 {GAME_CONFIG['min_players']}-{GAME_CONFIG['max_players']} 之间")
        return
    
    console = Console()
    
    title = Panel.fit(
        "[bold blue]Multi-Agent LLM 德州扑克模拟器[/bold blue]\n"
        f"[green]玩家数量:[/green] {args.players}\n"
        f"[green]起始筹码:[/green] {args.chips}\n"
        f"[green]游戏手数:[/green] {args.hands}",
        title="游戏设置"
    )
    console.print(title)
    
    try:
        game_manager = GameManager(args.players, args.chips)
        results = game_manager.play_game(args.hands)
        
        console.print("\n" + "="*60)
        console.print("[bold green]游戏结束！[/bold green]")
        console.print("="*60)
        
        log_path = game_manager.logger.get_log_path()
        console.print(f"\n[bold blue]详细日志已保存到:[/bold blue] [u]{log_path}[/u]")
        
        table = Table(title="最终结果统计")
        table.add_column("玩家", style="cyan")
        table.add_column("LLM类型", style="magenta")
        table.add_column("最终筹码", style="green")
        table.add_column("总盈亏", style="yellow")
        table.add_column("获胜手数", style="blue")

        final_chips = results['final_chips']
        winner_stats = results['winner_stats']
        
        # 获取初始玩家列表和他们的LLM类型
        player_llm_map = {p.name: p.llm_type for p in game_manager.game.players}
        
        # 按最终筹码排序
        sorted_players = sorted(final_chips.items(), key=lambda item: item[1], reverse=True)

        for player_name, chips in sorted_players:
            profit = chips - args.chips
            profit_text = f"+{profit}" if profit > 0 else str(profit)
            profit_style = "green" if profit > 0 else "red" if profit < 0 else "white"
            
            table.add_row(
                player_name,
                player_llm_map.get(player_name, "N/A"),
                str(chips),
                f"[{profit_style}]{profit_text}[/{profit_style}]",
                str(winner_stats.get(player_name, 0))
            )
        
        console.print(table)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]游戏被用户中断[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]游戏运行出错: {e}[/bold red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()