# -*- coding: utf-8 -*-
"""
TUGUMIv6 Status Dock Component
- Compact Cyberpunk HUD Bar above prompt
- Displays Mode, Model, Tokens, Memory, and Platform Info
Dedicated to Master Takuma.
"""

import os
import glob
import shutil
from typing import Dict, Any
from rich.console import Console
from rich.markup import escape
from interfaces.cli.cyber_theme import get_display_width

class StatusDock:
    """プロンプト直前に表示されるコンパクトなサイバーステータスドック"""
    def __init__(self, console: Console):
        self.console = console

    def get_system_stats(self) -> Dict[str, Any]:
        """Termux環境のリアルタイム実機メモリ・ストレージ・プロセス統計を取得 (Zero-Mock)"""
        ram_pct = 45
        ram_stat = "45%"
        try:
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
            mem_total = 0
            mem_avail = 0
            for line in lines:
                if line.startswith("MemTotal:"):
                    mem_total = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_avail = int(line.split()[1])
            if mem_total > 0:
                ram_pct = int(((mem_total - mem_avail) / mem_total) * 100)
                ram_stat = f"{ram_pct}%"
        except Exception:
            ram_stat = "N/A"

        # ディスク使用率
        disk_pct = 50
        try:
            total, used, free = shutil.disk_usage(os.path.expanduser("~"))
            disk_pct = int(used / total * 100)
        except Exception:
            pass

        # 実行中プロセス数
        proc_cnt = 0
        try:
            proc_cnt = len(glob.glob("/proc/[0-9]*"))
        except Exception:
            pass

        return {
            "ram": ram_stat,
            "ram_pct": ram_pct,
            "disk_pct": disk_pct,
            "proc_cnt": proc_cnt
        }

    def render_dock(
        self,
        mode: str,
        token_count: int,
        cost_jpy: float = 0.0,
        rag_active: bool = True,
        thinking_level: str = "high",
        model_name: str = "gemini-3.8-flash"
    ):
        """ステータスドックをレンダリング (Termuxスマホ画面幅自動追従・Zero-Overflow HUD)"""
        stats = self.get_system_stats()
        jpy_display = f"¥{cost_jpy:.4f}" if cost_jpy < 0.1 else (f"¥{cost_jpy:.3f}" if cost_jpy < 1.0 else f"¥{cost_jpy:.2f}")

        ram_int = int(stats['ram'].replace("%", "")) if "%" in stats['ram'] and stats['ram'].replace("%", "").isdigit() else 45
        filled = max(0, min(6, int(round(6 * ram_int / 100.0))))

        # 実際の端末幅（Termuxスマホ画面幅）を精密取得
        term_size_cols = shutil.get_terminal_size((80, 24)).columns
        term_width = min(term_size_cols, self.console.width or 80)
        target_w = max(34, min(term_width - 2, 76))
        th_lvl = (thinking_level or "high").upper()

        # モデル短縮フォーマット (動的反映)
        m_lower = (model_name or "gemini-3.8-flash").lower()
        if "argon" in m_lower or "gemini-4" in m_lower:
            m_label = "[bold #ff007f]4-Argon[/bold #ff007f]" if mode == "dark" else "[bold #d63384]4-Argon[/bold #d63384]"
            m_short = "4-Argon"
        elif "3.8" in m_lower or ("flash" in m_lower and "lite" not in m_lower and "3.5" not in m_lower):
            m_label = "[bold #00f0ff]3.8-Flash[/bold #00f0ff]" if mode == "dark" else "[bold cyan]3.8-Flash[/bold cyan]"
            m_short = "3.8-Flash"
        elif "pro" in m_lower:
            m_label = "[bold #ffb703]3.0-Pro[/bold #ffb703]" if mode == "dark" else "[bold #d97706]3.0-Pro[/bold #d97706]"
            m_short = "3.0-Pro"
        elif "lite" in m_lower or "3.5" in m_lower:
            m_label = "[bold #98c379]3.5-Lite[/bold #98c379]" if mode == "dark" else "[bold green]3.5-Lite[/bold green]"
            m_short = "3.5-Lite"
        else:
            m_short = m_lower.replace("gemini-", "").replace("google/", "")[:10]
            m_label = f"[bold white]{m_short}[/bold white]"

        # テーマ設定
        if mode == "dark":
            mode_badge = "☠ BLACK_ICE"
            mode_color = "#ff0055"
            dock_border = "#ff0055"
            ram_bar = "[#ff0055]" + "█" * filled + "[#5c6370]" + "░" * (6 - filled) + "[/]"
            th_color = "#00f0ff" if th_lvl == "HIGH" else ("#e5c07b" if th_lvl == "MEDIUM" else "#98c379")
            top_char, bottom_char = "┌", "└"
            top_corner, bottom_corner = "┐", "┘"
        else:
            mode_badge = "🌸 つぐみ"
            mode_color = "#ff79c6"
            dock_border = "#ff79c6"
            ram_bar = "[#8be9fd]" + "█" * filled + "[#5c6370]" + "░" * (6 - filled) + "[/]"
            th_color = "#00f0ff" if th_lvl == "HIGH" else ("#e5c07b" if th_lvl == "MEDIUM" else "#98c379")
            top_char, bottom_char = "╭", "╰"
            top_corner, bottom_corner = "╮", "╯"

        badge_len = 5 + get_display_width(mode_badge)
        dash_count = max(0, target_w - badge_len)
        top_line = f"[{dock_border}]{top_char}─{escape('[')} [bold {mode_color}]{mode_badge}[/] [{dock_border}]{escape(']')}" + "─" * dash_count + f"{top_corner}[/]"
        bottom_line = f"[{dock_border}]{bottom_char}" + "─" * max(0, target_w) + f"{bottom_corner}[/]"

        # スマホ狭画面（幅 < 54文字）の超スマート自動適応
        if term_width < 54:
            row_compact = (
                f"  [bold #00f0ff]🧠[/] {m_label} │ "
                f"[bold magenta]💾[/] {stats['ram']} │ "
                f"[bold yellow]⚡[/] {jpy_display} │ "
                f"[dim]T:[/] {token_count:,}"
            )
            self.console.print(top_line)
            self.console.print(row_compact)
            self.console.print(bottom_line)
            return

        # 標準・広幅画面
        rag_str = "[green]3072d[/green]" if rag_active else "[dim]OFF[/dim]"
        disk_bar = f"[#00f0ff]{stats['disk_pct']}%[/]" if stats['disk_pct'] < 85 else f"[#ff0055]{stats['disk_pct']}%[/]"

        row1 = (
            f"  [bold #00f0ff]CORE:[/] {m_label} [bold {th_color}]🧠{th_lvl}[/] │ "
            f"[bold #ff0055]RAM:[/] {ram_bar} [bold white]{stats['ram']}[/] │ "
            f"[bold #00ff88]RAG:[/] {rag_str}"
        )
        row2 = (
            f"  [bold #ffb800]TOKENS:[/] {token_count:,} │ "
            f"[bold magenta]COST:[/] [bold magenta]{jpy_display}[/] │ "
            f"[dim]DISK:[/] {disk_bar} │ "
            f"[dim]PIDS:[/] [cyan]{stats['proc_cnt']}[/]"
        )

        self.console.print(top_line)
        self.console.print(row1)
        self.console.print(row2)
        self.console.print(bottom_line)

