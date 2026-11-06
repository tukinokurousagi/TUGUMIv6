# -*- coding: utf-8 -*-
"""
TUGUMIv6 Modern Live Tool Inspector (SOTA 2026 Edition)
- High-density Compact Cyber Card UI (Zero-Slop, Mobile-Optimized)
- In-place Status Pill, Execution Latency, and Truncated Payload Previews
- TrueColor Semantic Status Highlighting
Dedicated to Master Takuma.
"""

import time
from typing import Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.markup import escape

class ToolInspector:
    """ツール呼び出しを現代的CLI水準（Claude Code / Charm.sh風）でコンパクトに可視化するインスペクタ"""
    def __init__(self, console: Console, mode: str = "light"):
        self.console = console
        self.mode = mode
        self._start_times: Dict[str, float] = {}

    def display_tool_start(self, tool_name: str, args: Optional[Dict[str, Any]] = None):
        """ツール実行開始をスマートな1行パルス表示（サブエージェント委譲時は専用バッジ）"""
        self._start_times[tool_name] = time.time()

        # サブエージェント委譲の特別リッチ表示
        if "subagent" in tool_name.lower():
            target_sa = ""
            sub_prompt = ""
            if args:
                target_sa = args.get("subagent_name") or args.get("TypeName") or ""
                sub_prompt = args.get("task_prompt") or args.get("Prompt") or ""
                if not target_sa and "Subagents" in args and isinstance(args["Subagents"], list) and args["Subagents"]:
                    first_sa = args["Subagents"][0]
                    target_sa = first_sa.get("TypeName") or first_sa.get("name") or ""
                    sub_prompt = first_sa.get("Prompt") or ""

            clean_p = sub_prompt.replace("\n", " ").strip()
            if len(clean_p) > 50:
                clean_p = clean_p[:47] + "..."

            tag = "[bold #bd93f9]🤖 [SUBAGENT_DISPATCH][/bold #bd93f9]"
            sa_badge = f"[bold white on #6272a4] {target_sa or 'worker'} [/bold white on #6272a4]"
            self.console.print(f"  {tag} {sa_badge} [dim cyan]指示: {escape(clean_p)}[/dim cyan]")
            return

        # 主要引数のコンパクト要約
        arg_summary = ""
        if args:
            items = []
            for k, v in list(args.items())[:3]:
                val = str(v).replace("\n", " ")
                if len(val) > 30:
                    val = val[:27] + "..."
                items.append(f"[dim]{k}=[/dim][white]{escape(val)}[/white]")
            if items:
                arg_summary = f" [dim]({', '.join(items)})[/dim]"

        if self.mode == "dark":
            tag = "[bold #ff0055]┌ ⚡[/bold #ff0055]"
            name_style = "bold #00f0ff"
        else:
            tag = "[bold #00f0ff]┌ ⚡[/bold #00f0ff]"
            name_style = "bold yellow"

        self.console.print(f"  {tag} [{name_style}]{tool_name}[/{name_style}]{arg_summary}")

    def display_tool_result(self, tool_name: str, success: bool, summary: str, details: Optional[str] = None):
        """ツール完了結果をスマホ最適化された洗練ツリー（Modern Agent Tree）で表示"""
        start_t = self._start_times.pop(tool_name, None)
        duration_str = f" [dim]⏱ {time.time() - start_t:.2f}s[/dim]" if start_t else ""

        clean_summary = summary.replace("\n", " ").strip()
        if len(clean_summary) > 75:
            clean_summary = clean_summary[:72] + "..."

        if self.mode == "dark":
            status_badge = "[bold #00ff88]✔ OK[/bold #00ff88]" if success else "[bold #ff0033]✖ ERR[/bold #ff0033]"
            prefix = "[dim #ff0055]└─[/dim #ff0055]"
        else:
            status_badge = "[bold #50fa7b]✔ OK[/bold #50fa7b]" if success else "[bold #ff5555]✖ ERR[/bold #ff5555]"
            prefix = "[dim #00f0ff]└─[/dim #00f0ff]"

        # 1行スマートツリーカード
        line = f"  {prefix} {status_badge} [{tool_name}]{duration_str} [dim white]› {escape(clean_summary)}[/dim white]"
        self.console.print(line)

        # 詳細がある場合のみ控えめに1行追加
        if details and not success:
            clean_details = details.replace("\n", " ").strip()
            if len(clean_details) > 80:
                clean_details = clean_details[:77] + "..."
            self.console.print(f"    [dim red]└─ ErrorDetail: {escape(clean_details)}[/dim red]")

    def display_diff(self, file_path: str, diff_text: str):
        """ファイル編集のGit差分プレビュー"""
        from rich.syntax import Syntax
        syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=True)
        panel = Panel(
            syntax,
            title=f"[bold cyan]Surgical Diff: {file_path}[/bold cyan]",
            border_style="cyan",
            padding=(0, 1)
        )
        self.console.print(panel)
