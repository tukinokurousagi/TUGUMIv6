# -*- coding: utf-8 -*-
"""
TUGUMIv6 Status Dock Component (SOTA 2026 Edition)
- Connected Modern AI Agent Status Bar directly integrated with prompt
- Displays Mode, Model, Thinking Intensity, Tokens, Cost, Memory, and RAG
- Zero-Overflow & East Asian Width Protection
Dedicated to Master Takuma.
"""

import os
import glob
import shutil
from typing import Dict, Any
from rich.console import Console
from rich.cells import cell_len
from rich.text import Text

class StatusDock:
    """プロンプト直前に表示される洗練されたモダンAIエージェント・ステータスバー"""
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
        """プロンプトと一体化する最新SOTA AIエージェント・コネクテッドドック"""
        stats = self.get_system_stats()
        jpy_display = f"¥{cost_jpy:.4f}" if cost_jpy < 0.1 else (f"¥{cost_jpy:.3f}" if cost_jpy < 1.0 else f"¥{cost_jpy:.2f}")

        term_size_cols = shutil.get_terminal_size((80, 24)).columns
        term_width = min(term_size_cols, self.console.width or 80)
        th_lvl = (thinking_level or "high").upper()

        m_lower = (model_name or "gemini-3.8-flash").lower()
        if "argon" in m_lower or "gemini-4" in m_lower:
            m_short = "4-Argon"
        elif "3.8" in m_lower or ("flash" in m_lower and "lite" not in m_lower and "3.5" not in m_lower):
            m_short = "3.8-Flash"
        elif "pro" in m_lower:
            m_short = "3.0-Pro"
        elif "lite" in m_lower or "3.5" in m_lower:
            m_short = "3.5-Lite"
        else:
            m_short = m_lower.replace("gemini-", "").replace("google/", "")[:9]

        is_dark = (mode == "dark")
        border_col = "#ff0055" if is_dark else "#ff79c6"
        primary = "#ff0055" if is_dark else "#ff79c6"
        top_char = "┌" if is_dark else "╭"
        top_r = "┐" if is_dark else "╮"
        agent_tag = "☠ BLACK_ICE v6" if is_dark else "🌸 つぐみ v6"

        tok_k = f"{token_count/1000:.1f}k" if token_count >= 1000 else str(token_count)

        # 優先度別バッジ群
        b_agent = Text.from_markup(f" [bold {primary}]{agent_tag}[/] ")
        b_model = Text.from_markup(f" [bold cyan]{m_short}[/] [dim #00f0ff]🧠{th_lvl}[/] ")
        b_cost = Text.from_markup(f" [bold yellow]{jpy_display}[/] [dim]({tok_k})[/dim] ")
        b_ram = Text.from_markup(f" [bold magenta]💾 {stats['ram']}[/] ")
        b_rag = Text.from_markup(" [bold green]3072d RAG[/] ") if rag_active else Text.from_markup(" [dim]RAG:OFF[/] ")

        # 端末幅に合わせてバッジを動的選定（折り返し絶対防止）
        dock = Text()
        dock.append(top_char + "─[", style=border_col)
        dock.append_text(b_agent)
        dock.append("]─[", style=border_col)
        dock.append_text(b_model)
        dock.append("]", style=border_col)

        candidates = [b_cost, b_ram, b_rag]
        for c in candidates:
            temp = Text()
            temp.append("─[", style=border_col)
            temp.append_text(c)
            temp.append("]", style=border_col)
            if cell_len(dock.plain) + cell_len(temp.plain) + 4 < term_width:
                dock.append_text(temp)

        cur_len = cell_len(dock.plain)
        dash = max(1, term_width - 1 - cur_len)
        dock.append("─" * dash + top_r, style=border_col)

        self.console.print(dock)


