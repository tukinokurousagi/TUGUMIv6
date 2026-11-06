# -*- coding: utf-8 -*-
"""
TUGUMIv6 Thinking Viewer & Streaming Renderer
- Controls thinking stream and summary display
- Rich Markdown & Syntax Highlight Streaming
- Antigravity CLI Standard Thinking Transparency
Dedicated to Master Takuma.
"""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown


class ThinkingViewer:
    """思考プロセスの可視化・ストリーミング実行制御クラス（Antigravity CLI / Claude Code 標準仕様）
    - モデル内部の推論（Thinking / Test-Time Compute）を隠さず可視化（Thinking Transparency）
    - リアルタイムストリーミング出力と完了時アコーディオンパネル描画を完全両立
    - サクサクモード（ストリーミング抑制）時でも思考サマリーパネルを美しく提示
    """
    def __init__(
        self,
        console: Console,
        mode: str = "light",
        show_thinking: bool = True,
        stream_thinking: bool = True
    ):
        self.console = console
        self.mode = mode
        self.show_thinking = show_thinking      # 思考ログ全体の可視化（デフォルトTrue）
        self.stream_thinking = stream_thinking  # リアルタイムストリーム印字（デフォルトTrue）
        self._is_thinking = False
        self._streamed_any = False

    def _write_output(self, text: str):
        """端末への直接印字（stream_thinking が有効な場合）"""
        if not self.show_thinking or not self.stream_thinking:
            return
        self._streamed_any = True
        sys.stdout.write(text)
        sys.stdout.flush()

    def start_thinking_stream(self):
        """思考プロセスのリアルタイムストリーミング出力"""
        if not self.show_thinking or not self.stream_thinking or self._is_thinking:
            return
        self._is_thinking = True
        self._streamed_any = False
        if self.mode == "dark":
            sys.stdout.write("\n\033[38;2;255;0;85m┌─ 🧠 Deep Thinking (TTC: HIGH) · (ESCで一時停止) ──\033[0m\n\033[38;5;244m")
        else:
            sys.stdout.write("\n\033[38;2;189;147;249m┌─ 🧠 Deep Thinking (TTC: HIGH) · (ESCで一時停止) ──\033[0m\n\033[38;5;244m")
        sys.stdout.flush()

    def stream_thought_chunk(self, chunk: str):
        """思考プロセスの断片処理"""
        if not self.show_thinking or not self.stream_thinking or not chunk:
            return
        if not self._is_thinking:
            self.start_thinking_stream()
        self._write_output(chunk)

    def end_thinking_stream(self):
        """思考プロセスのストリーミング終了"""
        if not self._is_thinking:
            return
        self._is_thinking = False
        if self._streamed_any:
            if self.mode == "dark":
                sys.stdout.write("\033[0m\n\033[38;2;255;0;85m└─ ⏱ [推論完了]\033[0m\n\n")
            else:
                sys.stdout.write("\033[0m\n\033[38;2;189;147;249m└─ ⏱ [推論完了]\033[0m\n\n")
        else:
            sys.stdout.write("\033[0m\n")
        sys.stdout.flush()

    def render_response_header(self, speaker_name: str, speaker_style: str, model_name: str = "3.8-Flash"):
        """回答ストリーミング開始時のスタイリッシュなヘッダーディバイダーを描画"""
        m_short = model_name.replace("gemini-", "").replace("google/", "")
        clean_speaker = speaker_name.replace("🌸", "").replace("⚡", "").strip()
        if self.mode == "dark":
            tag = f"[bold #ff0055]●[/bold #ff0055] [bold white]{clean_speaker}[/bold white] [dim cyan]({m_short})[/dim cyan]"
        else:
            tag = f"[bold #ff79c6]●[/bold #ff79c6] [bold white]{clean_speaker}[/bold white] [dim]({m_short})[/dim]"
        self.console.print(f"\n{tag}")

    def render_thinking_summary(self, thought_text: str, duration: float = 0.0):
        """完了した思考ログの描画（Claude Code / Antigravity風スマートバッジ & 思考アコーディオンパネル）"""
        if not thought_text.strip():
            return

        lines = [line.strip() for line in thought_text.strip().splitlines() if line.strip()]
        steps_count = len(lines)
        total_chars = len(thought_text)

        # 思考ログ表示が明示的に無効化されている場合、または既にリアルタイムストリーミング済みの場合は1行の洗練バッジを表示
        if getattr(self, "_streamed_any", False) or not self.show_thinking:
            badge_color = "#ff0055" if self.mode == "dark" else "#bd93f9"
            self.console.print(f"  [dim {badge_color}]✢[/dim {badge_color}] [dim]Thought for {duration:.1f}s ({steps_count} steps, {total_chars:,} chars)[/dim]")
            return

        # ストリーミング非表示（サクサクモード）時は、思考プロセスの詳細サマリーパネルを展開描画！
        max_preview_lines = 5
        if len(lines) > max_preview_lines:
            preview_lines = lines[:max_preview_lines] + [f"... (他 {len(lines) - max_preview_lines} 行 / 計 {total_chars:,} 字)"]
        else:
            preview_lines = lines

        if self.mode == "dark":
            preview = "\n".join([f"[#ff0055]❯[/#ff0055] [dim]{line}[/dim]" for line in preview_lines])
            title = f"[dim #ff0055]🧠 Thought for {duration:.1f}s ({steps_count} steps)[/dim #ff0055]"
            border = "#ff0055"
        else:
            preview = "\n".join([f"[cyber.dim]›[/cyber.dim] {line}" for line in preview_lines])
            title = f"[dim #bd93f9]🧠 Thought for {duration:.1f}s ({steps_count} steps)[/dim #bd93f9]"
            border = "#6272a4"

        panel = Panel(
            preview,
            title=title,
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
