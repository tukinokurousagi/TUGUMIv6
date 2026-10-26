# -*- coding: utf-8 -*-
"""
============================================================
  TUGUMIv6 Task Interrupter & Live Steering Component
  - Non-blocking ESC key detection during task execution
  - Real-time task pause and resume
  - Interactive steering prompt injection from Master Takuma
  - Safe terminal tty/termios management for Termux / Linux
  - Dedicated to Master Takuma
============================================================
"""

import sys
import select
import threading
import signal
from typing import Optional, Tuple, Set, Any
from rich.console import Console
from rich.panel import Panel

# termios / tty は Linux / Termux 環境でインポート可能
try:
    import termios
    import tty
    TERMIOS_AVAILABLE = True
except ImportError:
    TERMIOS_AVAILABLE = False


class TaskInterrupter:
    """タスク実行中のESCキー検知とリアルタイム一時停止・プロンプト追加マネージャ
    - バックグラウンドスレッド監視により、ツール実行・通信中もESCを確実に即時捕捉
    - 実行中のサブプロセスがあれば即時シグナル中断してブロックを完全回避
    """
    _global_active_processes: Set[Any] = set()
    _active_instance = None

    def __init__(self, console: Console):
        self.console = console
        self._old_settings = None
        self._is_active = False
        self._esc_pressed_event = threading.Event()
        self._stop_monitor_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None

    @classmethod
    def register_process(cls, proc: Any):
        """実行中サブプロセスを登録（ESC押下時に即時停止するため）"""
        if proc:
            cls._global_active_processes.add(proc)

    @classmethod
    def unregister_process(cls, proc: Any):
        """完了したサブプロセスを解除"""
        cls._global_active_processes.discard(proc)

    @classmethod
    def terminate_all_active_processes(cls):
        """登録中の全サブプロセスを即座に安全中断"""
        for proc in list(cls._global_active_processes):
            try:
                if hasattr(proc, "poll") and proc.poll() is None:
                    proc.send_signal(signal.SIGINT)
                    # 応答がなければ即時KILL
                    threading.Timer(0.3, lambda p=proc: p.kill() if p.poll() is None else None).start()
            except Exception:
                pass
        cls._global_active_processes.clear()

    def __enter__(self):
        TaskInterrupter._active_instance = self
        self.activate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deactivate()
        TaskInterrupter._active_instance = None

    def _monitor_loop(self):
        """バックグラウンドでESCキー入力を常時ポーリング監視"""
        while not self._stop_monitor_event.is_set():
            try:
                if not sys.stdin.isatty():
                    break
                rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
                if rlist:
                    ch = sys.stdin.read(1)
                    if ch == '\x1b':  # ESC (ASCII 27)
                        # 矢印キー等のエスケープシーケンス (\x1b[...) かどうか短時間で判定
                        r2, _, _ = select.select([sys.stdin], [], [], 0.05)
                        if r2:
                            sys.stdin.read(2)  # 矢印キー等を読み捨て
                            continue
                        # ESCキー確定！
                        self._esc_pressed_event.set()
                        # ツール実行中であればサブプロセスを即時中断してフリーズ解除！
                        self.terminate_all_active_processes()
                        break
            except Exception:
                break

    def activate(self) -> bool:
        """ターミナルを非ブロッキングcbreakモードに設定し、監視スレッドを始動"""
        if not TERMIOS_AVAILABLE or not sys.stdin.isatty():
            self._is_active = False
            return False

        try:
            self._old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
            self._is_active = True
            self._esc_pressed_event.clear()
            self._stop_monitor_event.clear()

            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()
            return True
        except Exception:
            self._is_active = False
            return False

    def deactivate(self) -> None:
        """監視スレッドを停止し、ターミナル設定を元のカノニカルモードに安全復元"""
        self._stop_monitor_event.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=0.2)
        self._monitor_thread = None

        if self._is_active and self._old_settings and TERMIOS_AVAILABLE:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSANOW, self._old_settings)
            except Exception:
                pass
        self._is_active = False

    def check_esc_pressed(self) -> bool:
        """非ブロッキングでESCキーが押されたか判定"""
        return self._esc_pressed_event.is_set()

    def handle_pause(self, current_text: str = "", mode: str = "dark") -> Tuple[str, Optional[str]]:
        """
        ESCが押された際の一時停止ダイアログ。
        ターミナル設定を一時復元して拓磨様からの追加プロンプトを受け付ける。

        Returns:
            action:
                'resume': 追加プロンプトを注入して再開
                'continue': 追加プロンプトなしでそのまま続行
                'cancel': タスクを中断してメインREPLに戻る
            additional_prompt: 拓磨様から入力された追加指示テキスト
        """
        # 一時停止のためターミナルを標準モードに復元
        self.deactivate()

        self.console.print()
        from interfaces.cli.cyber_theme import CYBER_PALETTES
        palette = CYBER_PALETTES.get(mode, CYBER_PALETTES["dark"])
        accent_color = palette.get("primary", "cyan")

        pause_panel = Panel(
            "[bold yellow]⏸ 【TASK PAUSED】タスクを一時停止いたしました。[/bold yellow]\n\n"
            "マスター拓磨様、追加の指示や修正プロンプトを入力してください。\n"
            "[dim]• [white]そのまま Enter[/white] : 一時停止を解除してタスクを続行\n"
            "• [white]テキスト入力[/white]   : リアルタイムに指示を注入して方向修正（Steering）\n"
            "• [white]/cancel[/white]      : タスクを安全に中断してメインメニューに戻る[/dim]",
            title="[bold yellow]◈ ESC Interrupt System Activated ◈[/bold yellow]",
            border_style="yellow",
            padding=(0, 1)
        )
        self.console.print(pause_panel)

        try:
            prompt_symbol = "🌸" if mode == "light" else "⚡"
            user_addition = input(f"追加プロンプト {prompt_symbol} > ").strip()
        except (KeyboardInterrupt, EOFError):
            self.console.print("\n[yellow]拓磨様、タスクの中断を指示されました。[/yellow]\n")
            return "cancel", None
        finally:
            # 入力完了後、タスク監視用に再度 cbreak モードを有効化
            self.activate()

        if not user_addition:
            self.console.print("[bold green]▶ 拓磨様、一時停止を解除しタスクを続行いたします。[/bold green]\n")
            return "continue", None
        elif user_addition.lower() in ("/cancel", "cancel", "exit"):
            self.console.print("[bold red]✖ 拓磨様、タスクを中断いたしました。メインメニューへ戻ります。[/bold red]\n")
            return "cancel", None
        else:
            self.console.print(
                f"[bold {accent_color}]⚡ 追加指示を受信いたしました：[/bold {accent_color}]"
                f"[bold white]「{user_addition}」[/bold white]\n"
                f"[dim]指示をリアルタイムにコンテキストへ注入し、タスクを再開・適応生成いたします...[/dim]\n"
            )
            return "resume", user_addition
