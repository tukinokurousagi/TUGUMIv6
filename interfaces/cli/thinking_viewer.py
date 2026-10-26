# -*- coding: utf-8 -*-
"""
TUGUMIv6 Thinking Viewer & Streaming Renderer
- Controls thinking stream and summary display
- Rich Markdown & Syntax Highlight Streaming
Dedicated to Master Takuma.
"""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown


class ThinkingViewer:
    """思考プロセスのサクサク・スマート実行制御クラス（Claude Code / Antigravity CLI 標準仕様）
    - 思考生ログの端末垂れ流しを停止し、サクサク・スマートな進行を実現
    - モデル内部の推論（Thinking / Test-Time Compute）は最高精度で100%維持
    - 画面を汚さず、ツール実行インスペクタ（⚡ [EXEC_TOOL]）と回答のみをスマートに提示
    """
    def __init__(self, console: Console, mode: str = "light", show_thinking: bool = False):
        self.console = console
        self.mode = mode
        self.show_thinking = show_thinking  # デフォルトはサクサク・スマートモード（非表示）
        self._is_thinking = False
        self._streamed_any = False

    def _write_output(self, text: str):
        """端末への直接印字（show_thinking が有効な場合のみ）"""
        if not self.show_thinking:
            return
        self._streamed_any = True
        sys.stdout.write(text)
        sys.stdout.flush()

    def start_thinking_stream(self):
        """思考プロセスのリアルタイムストリーミング出力（show_thinking が有効な場合のみ）"""
        if not self.show_thinking or self._is_thinking:
            return
        self._is_thinking = True
        self._streamed_any = False
        if self.mode == "dark":
            sys.stdout.write("\n\033[1;35m🧠 [ダークつぐみ深層推論]\033[0m \033[2m(リアルタイム思考中 / Ctrl+Cで中断可能)\033[0m\n\033[2;36m")
        else:
            sys.stdout.write("\n\033[1;34m🧠 [つぐみ思考推論]\033[0m \033[2m(リアルタイム思考中 / Ctrl+Cで中断可能)\033[0m\n\033[2;37m")
        sys.stdout.flush()

    def stream_thought_chunk(self, chunk: str):
        """思考プロセスの断片処理（サクサクモード時は画面印字を完全抑止）"""
        if not self.show_thinking or not chunk:
            return
        if not self._is_thinking:
            self.start_thinking_stream()
        self._write_output(chunk)

    def end_thinking_stream(self):
        """思考プロセスのストリーミング終了"""
        if not self.show_thinking or not self._is_thinking:
            return
        self._is_thinking = False
        if self._streamed_any:
            sys.stdout.write("\033[0m\033[2;34m⏱ [思考プロセス完了]\033[0m\n\n")
        else:
            sys.stdout.write("\033[0m\n")
        sys.stdout.flush()

    def render_response_header(self, speaker_name: str, speaker_style: str, model_name: str = "3.8-Flash"):
        """回答ストリーミング開始時のスタイリッシュなヘッダーディバイダーを描画"""
        import shutil
        term_size_cols = shutil.get_terminal_size((80, 24)).columns
        term_width = min(term_size_cols, self.console.width or 80)
        target_w = max(34, min(term_width - 2, 76))
        
        # モデル名短縮
        m_short = model_name.replace("gemini-", "").replace("google/", "")
        if self.mode == "dark":
            tag = f"[bold #ff0055]🤖 {speaker_name}[/bold #ff0055] [dim cyan]─── [{m_short}][/dim cyan]"
            prefix_len = 12 + len(m_short)
            divider = f"\n{tag} " + "─" * max(0, target_w - prefix_len)
        else:
            tag = f"[bold #ff79c6]🤖 {speaker_name}[/bold #ff79c6] [dim]─── [{m_short}][/dim]"
            prefix_len = 10 + len(m_short)
            divider = f"\n{tag} " + "─" * max(0, target_w - prefix_len)
        self.console.print(divider + "\n")

    def render_thinking_summary(self, thought_text: str, duration: float = 0.0):
        """完了した思考ログの描画（Claude Code風スマートバッジ & 折りたたみプレビュー）"""
        if not thought_text.strip():
            return

        lines = [line.strip() for line in thought_text.strip().splitlines() if line.strip()]
        steps_count = len(lines)

        # サクサクモード時は、画面を汚さない1行のスマートカプセル（Pill）バッジとして静かに表示
        if not self.show_thinking:
            if self.mode == "dark":
                badge = f"  [dim #ff0055]🧠 深層推論完了:[/] [dim cyan]⏱ {duration:.2f}s[/] [dim]({steps_count} steps)[/dim]"
            else:
                badge = f"  [dim #bd93f9]🧠 深層推論完了:[/] [dim]⏱ {duration:.2f}s ({steps_count} steps)[/dim]"
            self.console.print(badge)
            return

        if getattr(self, "_streamed_any", False):
            return

        if len(lines) > 4:
            preview_lines = lines[:3] + [f"... (他 {len(lines) - 3} 行の思考ログ)"]
        else:
            preview_lines = lines

        if self.mode == "dark":
            preview = "\n".join([f"[#ff0055]❯[/#ff0055] [dim]{line}[/dim]" for line in preview_lines])
            title = "[bold #ff0055]☠ 深層推論ログ (TTC思考推論)[/bold #ff0055]"
            subtitle = f"[dim cyan]⏱ 思考時間: {duration:.2f}秒 │ {steps_count} steps[/dim cyan]"
            border = "#ff0055"
        else:
            preview = "\n".join([f"[cyber.dim]›[/cyber.dim] {line}" for line in preview_lines])
            title = "[bold #bd93f9]🧠 つぐみ思考プロセス[/bold #bd93f9]"
            subtitle = f"[cyber.dim]⏱ 思考時間: {duration:.2f}秒 │ {steps_count} steps[/cyber.dim]"
            border = "#6272a4"
        
        panel = Panel(
            preview,
            title=title,
            subtitle=subtitle,
            border_style=border,
            padding=(0, 1),
        )
        self.console.print(panel)

    def render_markdown_response(self, response_text: str, speaker_name: str, speaker_style: str, model_name: str = "3.8-Flash"):
        """回答テキストをリッチなMarkdown・シンタックスハイライト付きで描画"""
        self.render_response_header(speaker_name, speaker_style, model_name)
        try:
            md = Markdown(response_text, code_theme="monokai")
            self.console.print(md)
        except Exception:
            self.console.print(response_text)
        self.console.print()
