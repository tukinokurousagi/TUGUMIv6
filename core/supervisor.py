# -*- coding: utf-8 -*-
"""
TUGUMIv6 Supervisor & Process Manager
- Lifecycle manager for background daemon, WebUI, and passive income workers
- Health checks, PID management, and automatic crash recovery
"""

import os
import sys
import time
import json
import signal
import subprocess
import threading
from typing import Dict, Any, Optional

class Supervisor:
    """Daemon & Process Supervisor for TUGUMIv6"""
    def __init__(self, base_dir: str = "/data/data/com.termux/files/home/TUGUMIv6"):
        self.base_dir = base_dir
        self.pid_dir = os.path.join(self.base_dir, "logs")
        os.makedirs(self.pid_dir, exist_ok=True)
        self.pid_file = os.path.join(self.pid_dir, "supervisor.pid")
        self.heartbeat_file = os.path.join(self.pid_dir, "heartbeats.json")
        self.lock = threading.RLock()

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
