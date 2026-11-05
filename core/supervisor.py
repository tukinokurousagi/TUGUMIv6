# -*- coding: utf-8 -*-
"""
TUGUMIv6 Supervisor & Process Manager
- Lifecycle manager for background daemon, WebUI, and passive income workers
- Health checks, PID management, and automatic crash recovery
- TaskStateMachine: RUNNING -> PAUSED -> RESUMING の遷移管理、旧ストリーム/ワーカー/キューの完全破棄、LoopGuardリセット
- guarded_call: ツール実行・記憶アクセスの未捕獲例外によるプロセス突然死の防止（エラーを推論エンジンへ返して自律リカバリ）
"""

import os
import sys
import time
import json
import signal
import subprocess
import threading
import traceback
from enum import Enum
from typing import Dict, Any, Optional, Callable, List

class TaskState(str, Enum):
    """タスク実行ステートマシンの状態"""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    RESUMING = "RESUMING"
    CANCELLED = "CANCELLED"


# 許可される遷移（それ以外も例外にはせず強制遷移する: 状態不整合で再開が止まる事故を避けるため）
_ALLOWED_TRANSITIONS: Dict[TaskState, set] = {
    TaskState.IDLE: {TaskState.RUNNING, TaskState.CANCELLED},
    TaskState.RUNNING: {TaskState.PAUSED, TaskState.IDLE, TaskState.CANCELLED, TaskState.RESUMING},
    TaskState.PAUSED: {TaskState.RESUMING, TaskState.CANCELLED, TaskState.RUNNING},
    TaskState.RESUMING: {TaskState.RUNNING, TaskState.CANCELLED, TaskState.IDLE},
    TaskState.CANCELLED: {TaskState.IDLE, TaskState.RUNNING, TaskState.RESUMING},
}


class StreamContext:
    """1本のストリーミング出力（CLI/SSE）に対応する世代付きコンテキスト。

    中断時は close() で旧ストリームを明示的に失効させ、再開時は新しい StreamContext へ再バインドする。
    旧ストリームは is_current() が False になるため、後始末で新ターンを cancel してはならない。
    """
    def __init__(self, owner: "TaskStateMachine", stream_id: int, generation: int, label: str = ""):
        self._owner = owner
        self.stream_id = stream_id
        self.generation = generation
        self.label = label
        self.closed = threading.Event()

    def close(self) -> None:
        self.closed.set()

    def is_current(self) -> bool:
        return (not self.closed.is_set()) and self._owner.generation == self.generation

    def release(self) -> None:
        self._owner._release_stream(self)


class TaskStateMachine:
    """タスクの一時中断→追加プロンプト→再開を安全に管理するステートマシン (スレッドセーフ)

    RUNNING -> PAUSED -> RESUMING -> RUNNING / いつでも CANCELLED
    遷移ごとに「旧ターンの残骸（ストリーム・ワーカー・Queue・LoopGuard履歴）」を確実に破棄する。
    """
    def __init__(self):
        self._lock = threading.RLock()
        self.state: TaskState = TaskState.IDLE
        self.generation: int = 0
        self._next_stream_id: int = 0
        self._streams: Dict[int, StreamContext] = {}
        self._flush_hooks: List[Callable[[], None]] = []
        self.history: List[Dict[str, Any]] = []

    # -------- 内部 --------
    def _transition(self, new_state: TaskState, reason: str = "") -> None:
        old = self.state
        self.history.append({"t": time.time(), "from": old.value, "to": new_state.value, "reason": reason})
        if len(self.history) > 200:
            del self.history[:100]
        self.state = new_state

    def _release_stream(self, ctx: StreamContext) -> None:
        with self._lock:
            self._streams.pop(ctx.stream_id, None)

    def _close_all_streams(self) -> int:
        n = 0
        for ctx in list(self._streams.values()):
            ctx.close()
            n += 1
        self._streams.clear()
        return n

    def _reset_loop_guard(self) -> None:
        try:
            from core.loop_guard import default_loop_guard
            default_loop_guard.mark_resumed()
        except Exception:
            pass

    def _run_flush_hooks(self) -> None:
        for hook in list(self._flush_hooks):
            try:
                hook()
            except Exception:
                pass

    # -------- 公開API --------
    def register_flush_hook(self, hook: Callable[[], None]) -> None:
        """中断/再開時に呼ばれるキュー・ワーカー破棄フックを登録（重複登録は無視）"""
        with self._lock:
            if hook not in self._flush_hooks:
                self._flush_hooks.append(hook)

    def begin_turn(self, steering: bool = False, label: str = "") -> StreamContext:
        """新ターン開始。旧ストリームを全て失効させ、新ストリームコンテキストを返す。
        steering=True（ESC一時停止からの追加プロンプト再開）なら RESUMING 経由で RUNNING に遷移し LoopGuard をリセットする。"""
        with self._lock:
            # 直前がユーザーによる一時停止/中断/再開処理中だった場合のみ「意図的な再開」とみなす
            # （タイムアウト自動リカバリ等の通常の再試行では LoopGuard を緩めない）
            interrupted = self.state in (TaskState.PAUSED, TaskState.CANCELLED, TaskState.RESUMING)
            self._close_all_streams()
            self.generation += 1
            if steering and interrupted:
                self._transition(TaskState.RESUMING, "begin_turn(steering)")
                self._reset_loop_guard()
                self._run_flush_hooks()
            self._transition(TaskState.RUNNING, "begin_turn")
            self._next_stream_id += 1
            ctx = StreamContext(self, self._next_stream_id, self.generation, label)
            self._streams[ctx.stream_id] = ctx
            return ctx

    def end_turn(self, ctx: Optional[StreamContext] = None) -> None:
        """ターン正常終了。自分が最新世代の場合のみ IDLE へ戻す（旧ストリームの後始末が新ターンを壊さない）"""
        with self._lock:
            if ctx is not None:
                self._release_stream(ctx)
                if ctx.generation != self.generation:
                    return
            if self.state in (TaskState.RUNNING, TaskState.RESUMING):
                self._transition(TaskState.IDLE, "end_turn")

    def pause(self) -> None:
        with self._lock:
            self._transition(TaskState.PAUSED, "pause")

    def resume(self, steering: bool = False) -> None:
        """一時停止解除（そのまま続行）。steering の場合は begin_turn(steering=True) 側でリセットされる"""
        with self._lock:
            self._transition(TaskState.RESUMING, "resume")
            if not steering:
                self._transition(TaskState.RUNNING, "resume_continue")

    def cancel(self, reason: str = "cancel") -> None:
        """中断: 全ストリーム失効 + ワーカー/Queueフラッシュフック + LoopGuardリセット"""
        with self._lock:
            self._close_all_streams()
            self._transition(TaskState.CANCELLED, reason)
            self._reset_loop_guard()
            self._run_flush_hooks()

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {"state": self.state.value, "generation": self.generation, "active_streams": len(self._streams)}


def guarded_call(component: str, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Dict[str, Any]:
    """ツール実行・記憶アクセスなどを包括的に保護して呼び出す。

    例外は絶対に上位へ漏らさずプロセスを落とさない。失敗時は構造化エラーを返し、
    推論エンジンがその内容を読んで自律リカバリ（代替手段への切替）できるようにする。
    KeyboardInterrupt / SystemExit / CancelledError(BaseException) はユーザー中断として再送出する。
    """
    try:
        return {"ok": True, "result": func(*args, **kwargs), "component": component}
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        return {
            "ok": False,
            "component": component,
            "error": f"{type(e).__name__}: {e}",
            "traceback": traceback.format_exc()[-1500:],
            "hint": "このエラー内容を踏まえ、引数・パス・状態を確認して別手段または修正パラメータで再試行してください。",
        }


# グローバル・ステートマシン（CLI / Web / EngineManager が共有）
default_task_state = TaskStateMachine()


class Supervisor:
    """Daemon & Process Supervisor for TUGUMIv6"""
    def __init__(self, base_dir: str = "/data/data/com.termux/files/home/TUGUMIv6"):
        self.base_dir = base_dir
        self.pid_dir = os.path.join(self.base_dir, "logs")
        os.makedirs(self.pid_dir, exist_ok=True)
        self.pid_file = os.path.join(self.pid_dir, "supervisor.pid")
        self.heartbeat_file = os.path.join(self.pid_dir, "heartbeats.json")
        self.lock = threading.RLock()

    def guarded_call(self, component: str, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """未捕獲例外によるプロセス突然死を防ぎ、失敗をハートビートに記録した上で構造化エラーを返す"""
        res = guarded_call(component, func, *args, **kwargs)
        if not res.get("ok"):
            try:
                self.record_heartbeat(component, {"status": "error", "error": res.get("error", "")[:300]})
            except Exception:
                pass
        return res

    def save_pid(self) -> None:
        with open(self.pid_file, "w") as f:
            f.write(str(os.getpid()))

    def save_process_pid(self, name: str, pid: int) -> None:
        path = os.path.join(self.pid_dir, f"{name}.pid")
        with open(path, "w") as f:
            f.write(str(pid))

    def get_status(self) -> Dict[str, Any]:
        running = False
        pid = None
        if os.path.exists(self.pid_file):
            try:
                with open(self.pid_file) as f:
                    pid = int(f.read().strip())
                # Check process
                os.kill(pid, 0)
                running = True
            except (OSError, ValueError):
                running = False

        return {
            "running": running,
            "pid": pid if running else None,
            "base_dir": self.base_dir
        }

    # ==================== ハートビート・ヘルスチェック ====================
    def record_heartbeat(self, component: str = "main", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """コンポーネント（CLI、WebUI、Worker等）の生存ハートビートをアトミックに記録"""
        with self.lock:
            heartbeats = {}
            if os.path.exists(self.heartbeat_file):
                try:
                    with open(self.heartbeat_file, "r", encoding="utf-8") as f:
                        heartbeats = json.load(f)
                except Exception:
                    heartbeats = {}

            entry = {
                "timestamp": time.time(),
                "time_iso": time.strftime("%Y-%m-%d %H:%M:%S"),
                "pid": os.getpid(),
                "metadata": metadata or {}
            }
            heartbeats[component] = entry

            try:
                tmp_file = f"{self.heartbeat_file}.tmp"
                with open(tmp_file, "w", encoding="utf-8") as f:
                    json.dump(heartbeats, f, indent=2, ensure_ascii=False)
                os.replace(tmp_file, self.heartbeat_file)
            except Exception:
                pass

            return entry

    def check_heartbeat(self, component: str = "main", max_staleness_sec: float = 60.0) -> Dict[str, Any]:
        """特定コンポーネントのハートビート鮮度をチェック"""
        if not os.path.exists(self.heartbeat_file):
            return {"alive": False, "status": "no_heartbeat_file", "component": component}

        try:
            with open(self.heartbeat_file, "r", encoding="utf-8") as f:
                heartbeats = json.load(f)
        except Exception as e:
            return {"alive": False, "status": f"read_error: {e}", "component": component}

        if component not in heartbeats:
            return {"alive": False, "status": "not_registered", "component": component}

        hb = heartbeats[component]
        age = time.time() - hb.get("timestamp", 0)
        alive = age <= max_staleness_sec
        return {
            "alive": alive,
            "age_seconds": round(age, 2),
            "max_staleness": max_staleness_sec,
            "component": component,
            "last_seen": hb.get("time_iso", ""),
            "pid": hb.get("pid")
        }

    def get_all_heartbeats(self) -> Dict[str, Any]:
        """全コンポーネントのハートビート一覧を取得"""
        if not os.path.exists(self.heartbeat_file):
            return {}
        try:
            with open(self.heartbeat_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    # ==================== プロセス監視＆制御 ====================
    def monitor_process(self, pid: int) -> Dict[str, Any]:
        """指定PIDのプロセス生存およびリソース状態を監視"""
        try:
            os.kill(pid, 0)
            alive = True
        except (OSError, ValueError):
            alive = False

        info: Dict[str, Any] = {"pid": pid, "alive": alive}
        if alive:
            # Linux / Termux procファイルシステムから情報取得試行
            proc_stat = f"/proc/{pid}/status"
            if os.path.exists(proc_stat):
                try:
                    with open(proc_stat, "r") as f:
                        for line in f:
                            if line.startswith("VmRSS:"):
                                info["rss_memory"] = line.split(":", 1)[1].strip()
                            elif line.startswith("Name:"):
                                info["name"] = line.split(":", 1)[1].strip()
                except Exception:
                    pass
        return info

    def list_tracked_processes(self) -> Dict[str, Any]:
        """logsディレクトリ内の全PIDファイルをスキャンして状態確認"""
        results = {}
        for f in os.listdir(self.pid_dir):
            if f.endswith(".pid"):
                name = f[:-4]
                path = os.path.join(self.pid_dir, f)
                try:
                    with open(path) as pf:
                        pid = int(pf.read().strip())
                    results[name] = self.monitor_process(pid)
                except Exception as e:
                    results[name] = {"error": str(e), "alive": False}
        return results

    def kill_process(self, pid: int, sig: int = signal.SIGTERM) -> bool:
        """指定プロセスを安全に終了"""
        try:
            os.kill(pid, sig)
            return True
        except Exception:
            return False

    def health_check_system(self) -> Dict[str, Any]:
        """総合ヘルスチェック（Supervisor、全ハートビート、全プロセス、システム稼働）"""
        return {
            "supervisor": self.get_status(),
            "heartbeats": self.get_all_heartbeats(),
            "processes": self.list_tracked_processes(),
            "timestamp": time.time()
        }

    def start_webui_background(self, port: int = 8086) -> Dict[str, Any]:
        """WebUIサーバーを安全にバックグラウンド起動"""
        web_script = os.path.join(self.base_dir, "interfaces", "web", "web_server.py")
        log_file = os.path.join(self.pid_dir, "webui.log")
        with open(log_file, "a") as out:
            proc = subprocess.Popen(
                [sys.executable, web_script, "--port", str(port)],
                stdout=out,
                stderr=out,
                cwd=self.base_dir,
                start_new_session=True
            )
        self.save_process_pid("webui", proc.pid)
        return {"status": "started", "pid": proc.pid, "port": port, "log": log_file}
