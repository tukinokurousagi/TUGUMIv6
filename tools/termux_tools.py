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
        """標準Termuxコマンド実行（ESC割り込み追跡対応）"""
        try:
            from interfaces.cli.task_interrupter import TaskInterrupter
        except ImportError:
            TaskInterrupter = None

        proc = None
        try:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd
            )
            if TaskInterrupter:
                TaskInterrupter.register_process(proc)

            stdout, stderr = proc.communicate(timeout=timeout)
            return {
                "exit_code": proc.returncode,
                "stdout": stdout,
                "stderr": stderr
            }
        except subprocess.TimeoutExpired:
            if proc:
                proc.kill()
                stdout, stderr = proc.communicate()
            return {"exit_code": -1, "stdout": "", "stderr": f"Command timed out ({timeout}s)"}
        except Exception as e:
            if proc:
                try:
                    proc.kill()
                except Exception:
                    pass
            return {"exit_code": -1, "stdout": "", "stderr": str(e)}
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
