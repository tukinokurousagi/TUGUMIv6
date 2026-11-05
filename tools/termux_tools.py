# -*- coding: utf-8 -*-
"""
TUGUMIv6 Termux & Shizuku+ Privileged Tools
- Maximizes Shizuku+ (rish, su, adb, plus command suite)
- Privileged Shell Command Execution
- Android UI Automation (touch, swipe, text, dump via AICore+)
- Non-blocking Process Management
"""

import subprocess
import shutil
import os
import shlex
from typing import Dict, Any, Optional

class TermuxTools:
    """Termux, Shizuku+ & Android Super-Privilege Manager"""
    def __init__(self):
        self.rish_path = shutil.which("rish") or "/data/data/com.termux/files/home/bin/rish"
        self.su_path = shutil.which("su") or "/data/data/com.termux/files/home/bin/su"
        self.adb_path = shutil.which("adb") or "/data/data/com.termux/files/usr/bin/adb"
        self.plus_path = shutil.which("plus") or "/data/data/com.termux/files/home/bin/plus"

    def run_termux_command(self, cmd: str, timeout: float = 300.0, cwd: Optional[str] = None) -> Dict[str, Any]:
        """標準Termuxコマンド実行（非ブロッキングselectパイプ監視により、デーモン起動やESC強制中断でも0.01秒で即座に復帰）"""
        import select
        import signal
        import time
        try:
            from interfaces.cli.task_interrupter import TaskInterrupter
        except ImportError:
            TaskInterrupter = None

        proc = None
        out_chunks: list[bytes] = []
        err_chunks: list[bytes] = []
        try:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                start_new_session=True
            )
            if TaskInterrupter:
                TaskInterrupter.register_process(proc)

            out_fd = proc.stdout.fileno() if proc.stdout else -1
            err_fd = proc.stderr.fileno() if proc.stderr else -1
            open_fds = []
            for fd in (out_fd, err_fd):
                if fd >= 0:
                    try:
                        os.set_blocking(fd, False)
                    except Exception:
                        pass
                    open_fds.append(fd)

            active_elapsed = 0.0
            last_loop_t = time.time()
            exited_at: Optional[float] = None

            while open_fds:
                now = time.time()
                dt = max(0.0, now - last_loop_t)
                last_loop_t = now

                # 1. ESCキャンセル/軌道修正された瞬間（最大0.03秒以内）にパイプEOFを待たず即時脱出！
                if TaskInterrupter and TaskInterrupter.was_terminated(proc):
                    break

                # 2. 一時停止中（SIGSTOP中）はタイムアウトタイマーを進めない
                is_paused = bool(TaskInterrupter and getattr(TaskInterrupter, "_is_currently_paused", False))
                if not is_paused:
                    active_elapsed += dt
                    if active_elapsed >= timeout:
                        try:
                            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                        except Exception:
                            try:
                                proc.kill()
                            except Exception:
                                pass
                        return {
                            "exit_code": -1,
                            "stdout": b"".join(out_chunks).decode("utf-8", errors="replace"),
                            "stderr": f"Command timed out ({timeout}s)"
                        }

                try:
                    rlist, _, _ = select.select(open_fds, [], [], 0.03)
                except Exception:
                    break

                for fd in rlist:
                    try:
                        data = os.read(fd, 65536)
                        if not data:
                            open_fds.remove(fd)
                        elif fd == out_fd:
                            out_chunks.append(data)
                        else:
                            err_chunks.append(data)
                    except BlockingIOError:
                        pass
                    except OSError:
                        if fd in open_fds:
                            open_fds.remove(fd)

                # 3. 親シェル終了後、バックグラウンド子プロセス(nohup/&等)がFDを握っていても0.08秒無出力なら即完了！
                if proc.poll() is not None:
                    if exited_at is None:
                        exited_at = time.time()
                    elif not rlist and (time.time() - exited_at) >= 0.08:
                        break

            stdout_str = b"".join(out_chunks).decode("utf-8", errors="replace")
            stderr_str = b"".join(err_chunks).decode("utf-8", errors="replace")

            if TaskInterrupter and TaskInterrupter.was_terminated(proc):
                return {
                    "exit_code": -15,
                    "stdout": stdout_str,
                    "stderr": (stderr_str + "\n[Interrupted by Master Takuma via ESC]").strip()
                }

            if proc.poll() is None:
                try:
                    proc.wait(timeout=0.2)
                except Exception:
                    pass

            return {
                "exit_code": proc.returncode if proc.returncode is not None else 0,
                "stdout": stdout_str,
                "stderr": stderr_str
            }
        except Exception as e:
            if proc:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
            stdout_str = b"".join(out_chunks).decode("utf-8", errors="replace")
            if TaskInterrupter and proc and TaskInterrupter.was_terminated(proc):
                return {"exit_code": -15, "stdout": stdout_str, "stderr": "[Interrupted by Master Takuma via ESC]"}
            return {"exit_code": -1, "stdout": stdout_str, "stderr": str(e)}
        finally:
            if TaskInterrupter and proc:
                TaskInterrupter.unregister_process(proc)

    def run_privileged_command(self, cmd: str, method: str = "auto", timeout: float = 180.0) -> Dict[str, Any]:
        """Shizuku+ / su / rish / adb 特権コマンド実行"""
        # auto: rish -> su -> adb の順でフォールバック
        methods = ["rish", "su", "adb"] if method == "auto" else [method]
        
        last_res = {
            "exit_code": -1,
            "stdout": "",
            "stderr": "No privileged binaries found or all methods failed",
            "method_used": "failed"
        }
        for m in methods:
            quoted_cmd = shlex.quote(cmd)
            if m == "rish" and os.path.exists(self.rish_path):
                full_cmd = f"{self.rish_path} -c {quoted_cmd}"
                res = self.run_termux_command(full_cmd, timeout=timeout)
                res["method_used"] = "rish"
                if res["exit_code"] == 0:
                    return res
                last_res = res
            elif m == "su" and os.path.exists(self.su_path):
                full_cmd = f"{self.su_path} -c {quoted_cmd}"
                res = self.run_termux_command(full_cmd, timeout=timeout)
                res["method_used"] = "su"
                if res["exit_code"] == 0:
                    return res
                last_res = res
            elif m == "adb" and os.path.exists(self.adb_path):
                full_cmd = f"{self.adb_path} shell {quoted_cmd}"
                res = self.run_termux_command(full_cmd, timeout=timeout)
                res["method_used"] = "adb"
                if res["exit_code"] == 0:
                    return res
                last_res = res

        return last_res

    def android_ui_action(self, action_type: str, *args) -> Dict[str, Any]:
        """AICore+ / Shizuku による画面操作 (touch, swipe, text, keyevent)"""
        if os.path.exists(self.plus_path):
            args_str = " ".join([str(a) for a in args])
            cmd = f"{self.plus_path} aicore {action_type} {args_str}"
            return self.run_termux_command(cmd)
        
        # フォールバック (input コマンド via rish/su)
        if action_type == "touch" and len(args) >= 2:
            return self.run_privileged_command(f"input tap {args[0]} {args[1]}")
        elif action_type == "swipe" and len(args) >= 4:
            duration = args[4] if len(args) > 4 else 300
            return self.run_privileged_command(f"input swipe {args[0]} {args[1]} {args[2]} {args[3]} {duration}")
        elif action_type == "text" and len(args) >= 1:
            safe_text = str(args[0]).replace(" ", "%s")
            return self.run_privileged_command(f"input text {safe_text}")
        elif action_type == "key" and len(args) >= 1:
            return self.run_privileged_command(f"input keyevent {args[0]}")

        return {"exit_code": -1, "stdout": "", "stderr": f"Unsupported action: {action_type}"}

    def vision_ui_step(self, instruction: str) -> Dict[str, Any]:
        """Gemini Vision によるAndroid画面の視覚認識・自律操作（1ステップ）"""
        try:
            from tools.vision_ui_agent import VisionUIAgent
            agent = VisionUIAgent()
            return agent.step(instruction)
        except Exception as e:
            return {"error": f"Vision UI 操作エラー: {e}", "action": "wait", "is_goal_reached": False}

    def vision_ui_inspect(self, focus_query: str = "") -> Dict[str, Any]:
        """Gemini Vision による現在のAndroid画面の詳細視覚インスペクト"""
        try:
            from tools.vision_ui_agent import VisionUIAgent
            agent = VisionUIAgent()
            return agent.inspect_screen(focus_query)
        except Exception as e:
            return {"error": f"Vision UI 観察エラー: {e}"}

    def vision_ui_switch_keyboard(self) -> Dict[str, Any]:
        """日本語テンキー（Gboard）の左下隅 [108, 2125] の「あa1」キーをタップ（拓磨様直伝）"""
        try:
            from tools.vision_ui_agent import VisionUIAgent
            agent = VisionUIAgent()
            agent.execute_action({"action": "switch_keyboard_mode"})
            return {"status": "success", "message": "文字種切替キー [108, 2125] をタップしました"}
        except Exception as e:
            return {"error": f"キーボード切替失敗: {e}"}

    def inspect_environment(self) -> Dict[str, Any]:
        """Termux環境の全レイヤー深層診断（Antigravity CLI水準）"""
        from core.termux_doctor import TermuxDoctor
        doctor = TermuxDoctor()
        return doctor.inspect_all()

    def maintain_environment(self, fix_all: bool = True) -> Dict[str, Any]:
        """Termux環境の自律整備・自己修復（ゾンビ刈り取り、一時ファイル掃除、DB最適化、TLS設定、Phantom Killer無効化）"""
        from core.termux_doctor import TermuxDoctor
        doctor = TermuxDoctor()
        return doctor.maintain_environment(fix_all=fix_all)

    def get_hud_status(self) -> str:
        """Termux環境の美麗HUDテキストサマリー"""
        from core.termux_doctor import TermuxDoctor
        doctor = TermuxDoctor()
        return doctor.format_hud_summary()
