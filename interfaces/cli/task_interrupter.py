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

import atexit
import os
import select
import signal
import sys
import threading
from typing import Any, Optional, Set, Tuple
from rich.console import Console
from rich.panel import Panel

# termios / tty は Linux / Termux 環境でインポート可能
try:
    import termios
    import tty
    TERMIOS_AVAILABLE = True
except ImportError:
    TERMIOS_AVAILABLE = False


_SAVED_STDIN_ATTRS = None
if TERMIOS_AVAILABLE and sys.stdin.isatty():
    try:
        _SAVED_STDIN_ATTRS = termios.tcgetattr(sys.stdin.fileno())
    except Exception:
        pass


def restore_terminal_canonical():
    """ターミナルを標準のカノニカル・エコーモードに100%確実に復元する自己修復関数"""
    if TERMIOS_AVAILABLE and sys.stdin.isatty() and _SAVED_STDIN_ATTRS:
        try:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, _SAVED_STDIN_ATTRS)
        except Exception:
            pass


atexit.register(restore_terminal_canonical)


class TaskInterrupter:
    """タスク実行中のESCキー検知とリアルタイム一時停止・プロンプト追加マネージャ
    - 誤検知完全排除: スマホIMEやANSIエスケープシーケンスを完全ドレインし、純粋な単独ESCのみを捕捉
    - 端末保護: 入力バッファの完全フラッシュと標準モード復元によりキーボード破壊を根絶
    - 安全一時停止: 勝手なサブプロセス皆殺しを廃止し、キャンセル確定時のみ中断
    """
    _global_active_processes: Set[Any] = set()
    _terminated_pids: Set[int] = set()
    _is_currently_paused: bool = False
    _active_instance = None

    def __init__(self, console: Console):
        self.console = console
        self._old_settings = None
        self._is_active = False
        self._esc_pressed_event = threading.Event()
        self._stop_monitor_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        self._cooldown_until: float = 0.0
        self.last_pause_duration: float = 0.0

    @classmethod
    def register_process(cls, proc: Any):
        """実行中サブプロセスを登録"""
        if proc:
            cls._global_active_processes.add(proc)

    @classmethod
    def unregister_process(cls, proc: Any):
        """完了したサブプロセスを解除"""
        cls._global_active_processes.discard(proc)
        if proc and hasattr(proc, "pid") and proc.pid:
            cls._terminated_pids.discard(proc.pid)

    @classmethod
    def was_terminated(cls, proc: Any) -> bool:
        """ESCキャンセルまたは軌道修正により強制中断されたプロセスか判定"""
        if proc and hasattr(proc, "pid") and proc.pid:
            return proc.pid in cls._terminated_pids
        return False

    @classmethod
    def pause_all_active_processes(cls):
        """一時停止中（TASK PAUSED）は実行中サブプロセスグループ全体にSIGSTOPを送って物理凍結"""
        cls._is_currently_paused = True
        if not hasattr(signal, "SIGSTOP"):
            return
        for proc in list(cls._global_active_processes):
            try:
                if hasattr(proc, "poll") and proc.poll() is None and proc.pid:
                    try:
                        pgid = os.getpgid(proc.pid)
                        os.killpg(pgid, signal.SIGSTOP)
                    except Exception:
                        proc.send_signal(signal.SIGSTOP)
            except Exception:
                pass

    @classmethod
    def resume_all_active_processes(cls):
        """続行（そのままEnter）選択時にサブプロセスグループ全体へSIGCONTを送って物理再開"""
        cls._is_currently_paused = False
        if not hasattr(signal, "SIGCONT"):
            return
        for proc in list(cls._global_active_processes):
            try:
                if hasattr(proc, "poll") and proc.poll() is None and proc.pid:
                    try:
                        pgid = os.getpgid(proc.pid)
                        os.killpg(pgid, signal.SIGCONT)
                    except Exception:
                        proc.send_signal(signal.SIGCONT)
            except Exception:
                pass

    @classmethod
    def terminate_all_active_processes(cls):
        """登録中の全サブプロセス（および子孫プロセス群）を即座に完全終了しパイプを即時解放"""
        cls._is_currently_paused = False
        for proc in list(cls._global_active_processes):
            try:
                if hasattr(proc, "pid") and proc.pid:
                    cls._terminated_pids.add(proc.pid)
                if hasattr(proc, "poll") and proc.poll() is None:
                    # 1. SIGSTOP凍結中だった場合に備えてSIGCONTで起こす
                    if hasattr(signal, "SIGCONT") and proc.pid:
                        try:
                            os.killpg(os.getpgid(proc.pid), signal.SIGCONT)
                        except Exception:
                            pass
                    # 2. プロセスグループごとSIGTERM -> SIGKILLで子孫プロセス(node/openclaw/proot等)まで即時殲滅
                    if proc.pid:
                        try:
                            pgid = os.getpgid(proc.pid)
                            os.killpg(pgid, signal.SIGTERM)
                        except Exception:
                            try:
                                proc.terminate()
                            except Exception:
                                pass
                        try:
                            pgid = os.getpgid(proc.pid)
                            os.killpg(pgid, signal.SIGKILL)
                        except Exception:
                            try:
                                proc.kill()
                            except Exception:
                                pass
                    else:
                        proc.kill()
                # 3. パイプ(stdout/stderr/stdin)を閉じて communicate() のブロックを即時解除
                for stream_name in ("stdout", "stderr", "stdin"):
                    st = getattr(proc, stream_name, None)
                    if st:
                        try:
                            st.close()
                        except Exception:
                            pass
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
        """バックグラウンドで純粋な単独ESCキー入力を常時監視"""
        fd = sys.stdin.fileno()
        while not self._stop_monitor_event.is_set():
            try:
                if not sys.stdin.isatty():
                    break
                rlist, _, _ = select.select([fd], [], [], 0.05)
                if rlist and not self._stop_monitor_event.is_set():
                    raw = os.read(fd, 1)
                    if raw == b'\x1b':  # ESC (ASCII 27)
                        # 後続バイト（矢印キーやIME等のマルチバイトシーケンス \x1b[...]）の有無を確認
                        r2, _, _ = select.select([fd], [], [], 0.04)
                        if r2:
                            # エスケープシーケンスの残りを全て吸い出して読み捨て（誤作動防止）
                            os.read(fd, 1024)
                            continue
                        # 純粋な単独ESCキー押下確定！
                        self._esc_pressed_event.set()
                        # ここで勝手にプロセスを殺さない（一時停止ダイアログで続行を選べるようにする）
                        break
            except Exception:
                break

    def activate(self) -> bool:
        """ターミナルを非ブロッキングcbreakモードに設定し、監視スレッドを始動"""
        if not TERMIOS_AVAILABLE or not sys.stdin.isatty():
            self._is_active = False
            return False

        try:
            self._old_settings = termios.tcgetattr(sys.stdin.fileno())
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
        """監視スレッドを停止し、ターミナル設定を元のカノニカルモードに100%安全復元"""
        self._stop_monitor_event.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=0.3)
        self._monitor_thread = None

        if self._is_active and TERMIOS_AVAILABLE and sys.stdin.isatty():
            restore_terminal_canonical()
        self._is_active = False

    def check_esc_pressed(self) -> bool:
        """非ブロッキングでESCキーが押されたか判定（再開直後の暴発防止クールダウンガード付）"""
        import time
        if time.time() < self._cooldown_until:
            self._esc_pressed_event.clear()
            return False
        return self._esc_pressed_event.is_set()

    def handle_pause(self, current_text: str = "", mode: str = "dark") -> Tuple[str, Optional[str]]:
        """
        ESCが押された際の一時停止ダイアログ。
        実行中サブプロセスをSIGSTOPで物理凍結し、ターミナル設定を標準カノニカルモードに安全復元してから入力を受け付ける。
        """
        import time
        pause_start_t = time.time()
        self.last_pause_duration = 0.0

        # 0. 実行中サブプロセスを一時停止（SIGSTOP）して裏での勝手な進行を防止
        self.pause_all_active_processes()

        # 1. 監視スレッドを停止し、端末を標準モードに完全復元
        self.deactivate()

        # 2. stdin入力バッファのゴミ（残存ESCシーケンス等）を完全クリア
        if TERMIOS_AVAILABLE and sys.stdin.isatty():
            try:
                termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
            except Exception:
                pass

        self.console.print()
        from interfaces.cli.cyber_theme import CYBER_PALETTES
        palette = CYBER_PALETTES.get(mode, CYBER_PALETTES["dark"])
        accent_color = palette.get("primary", "cyan")

        pause_panel = Panel(
            "[bold yellow]⏸ 【TASK PAUSED】タスクを一時停止いたしました。[/bold yellow]\n\n"
            "マスター拓磨様、追加の指示や修正プロンプトを入力してください。\n"
            "[dim]• [white]そのまま Enter[/white] : 一時停止を解除してタスクを安全に続行\n"
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
            self.last_pause_duration = max(0.0, time.time() - pause_start_t)
            self.console.print("\n[yellow]拓磨様、タスクの中断を指示されました。[/yellow]\n")
            self.terminate_all_active_processes()
            self._cooldown_until = time.time() + 1.0
            return "cancel", None

        self.last_pause_duration = max(0.0, time.time() - pause_start_t)

        if not user_addition:
            self.console.print("[bold green]▶ 拓磨様、一時停止を解除しタスクを続行いたします。[/bold green]\n")
            # 凍結していたサブプロセスへSIGCONTを送って物理再開
            self.resume_all_active_processes()
            # 続行時のみ監視を再開（0.8秒のクールダウンを設けて再開直後の再発火・キー余韻ループを物理遮断）
            self._cooldown_until = time.time() + 0.8
            self._esc_pressed_event.clear()
            self.activate()
            return "continue", None
        elif user_addition.lower() in ("/cancel", "cancel", "exit"):
            self.console.print("[bold red]✖ 拓磨様、タスクを中断いたしました。メインメニューへ戻ります。[/bold red]\n")
            self.terminate_all_active_processes()
            self._cooldown_until = time.time() + 1.0
            return "cancel", None
        else:
            self.console.print(
                f"[bold {accent_color}]⚡ 追加指示を受信いたしました：[/bold {accent_color}]"
                f"[bold white]「{user_addition}」[/bold white]\n"
                f"[dim]指示をリアルタイムにコンテキストへ注入し、タスクを再開・適応生成いたします...[/dim]\n"
            )
            # 再生成へ向かうため実行中サブプロセスグループを即座に終了
            self.terminate_all_active_processes()
            self._cooldown_until = time.time() + 1.0
            return "resume", user_addition
