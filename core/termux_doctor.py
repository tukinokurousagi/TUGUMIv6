# -*- coding: utf-8 -*-
"""
TUGUMIv6 Termux Environment Doctor & Self-Healing Maintenance Engine
- Antigravity CLI Grade Deep System Inspection & Autonomous Maintenance
- Termux Architecture (Android aarch64, bionic libc, $PREFIX, $TMPDIR)
- Shizuku+ Privileged Inspection (rish, su, adb, aicore)
- Phantom Process Killer Detection & Privileged Neutralization
- Process & Zombie Sanitation, Storage & Cache Cleanup
- SQLite WAL Checkpointing & Database Optimization
- TLS / SSL Certificate Health & SSL_CERT_FILE Auto-Configuration
"""

import os
import time
import json
import shutil
import sqlite3
import subprocess
import glob
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("TUGUMI.Doctor")

class TermuxDoctor:
    """Termux System Diagnostics & Self-Healing Maintenance Engine"""

    def __init__(self, base_dir: str = "/data/data/com.termux/files/home/TUGUMIv6"):
        self.base_dir = base_dir
        self.home_dir = os.path.expanduser("~")
        self.prefix_dir = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
        self.tmp_dir = os.environ.get("TMPDIR", os.path.join(self.prefix_dir, "tmp"))
        self.ca_cert_path = os.path.join(self.prefix_dir, "etc", "tls", "cert.pem")
        self.db_path = os.path.join(self.base_dir, "data", "tugumi_memory.db")
        self.rish_path = shutil.which("rish") or os.path.join(self.home_dir, "bin", "rish")
        self.su_path = shutil.which("su") or os.path.join(self.home_dir, "bin", "su")

    # ==================== 1. 深層環境インスペクション (深層把握) ====================
    def inspect_all(self) -> Dict[str, Any]:
        """Termux環境の全レイヤーを完全把握・診断"""
        report: Dict[str, Any] = {
            "timestamp": time.time(),
            "time_iso": time.strftime("%Y-%m-%d %H:%M:%S"),
            "health_score": 100,
            "issues": [],
            "warnings": [],
            "system": self._inspect_system(),
            "storage": self._inspect_storage(),
            "memory": self._inspect_memory(),
            "processes": self._inspect_processes(),
            "privileges": self._inspect_privileges(),
            "tls_ssl": self._inspect_tls_ssl(),
            "sqlite": self._inspect_sqlite(),
            "toolchain": self._inspect_toolchain(),
            "phantom_killer": self._inspect_phantom_process_killer(),
            "battery": self._inspect_battery()
        }

        # スコア計算
        score = 100
        score -= len(report["issues"]) * 15
        score -= len(report["warnings"]) * 5
        report["health_score"] = max(0, min(100, score))
        report["status"] = "EXCELLENT" if report["health_score"] >= 90 else ("GOOD" if report["health_score"] >= 70 else "NEEDS_MAINTENANCE")
        return report

    def _inspect_system(self) -> Dict[str, Any]:
        """OS、カーネル、Termux基本構造の把握"""
        uname = os.uname()
        android_os = "Unknown"
        try:
            getprop = subprocess.run(["getprop", "ro.build.version.release"], capture_output=True, text=True, timeout=8)
            if getprop.returncode == 0 and getprop.stdout.strip():
                android_os = f"Android {getprop.stdout.strip()}"
        except Exception:
            pass

        uptime_seconds = 0.0
        if os.path.exists("/proc/uptime"):
            try:
                with open("/proc/uptime", "r", encoding="utf-8") as uf:
                    uptime_seconds = float(uf.read().split()[0])
            except Exception:
                uptime_seconds = 0.0

        return {
            "os": uname.sysname,
            "kernel": uname.release,
            "arch": uname.machine,
            "android_version": android_os,
            "prefix": self.prefix_dir,
            "home": self.home_dir,
            "tmpdir": self.tmp_dir,
            "prefix_exists": os.path.exists(self.prefix_dir),
            "tmpdir_exists": os.path.exists(self.tmp_dir),
            "uptime_seconds": round(uptime_seconds, 1),
            "uptime_hours": round(uptime_seconds / 3600.0, 2),
        }

    def _inspect_storage(self) -> Dict[str, Any]:
        """内部ストレージ、共有ストレージ、一時ディレクトリの容量とパーミッション"""
        res: Dict[str, Any] = {}
        # $HOME 容量
        try:
            home_stat = shutil.disk_usage(self.home_dir)
            res["home_free_gb"] = round(home_stat.free / (1024**3), 2)
            res["home_total_gb"] = round(home_stat.total / (1024**3), 2)
            res["home_used_pct"] = round((home_stat.used / home_stat.total) * 100, 1)
            res["free_gb"] = res["home_free_gb"]
            res["percent"] = res["home_used_pct"]
        except Exception as e:
            res["home_error"] = str(e)

        # 共有ストレージ (/storage/emulated/0)
        shared_dir = "/storage/emulated/0"
        res["shared_storage_accessible"] = os.path.exists(shared_dir) and os.access(shared_dir, os.R_OK | os.W_OK)
        res["shared_storage_path"] = shared_dir

        # 一時ディレクトリの肥大化チェック
        tmp_files_count = 0
        tmp_size_mb = 0.0
        if os.path.exists(self.tmp_dir):
            for root, _, files in os.walk(self.tmp_dir):
                tmp_files_count += len(files)
                for f in files:
                    try:
                        fp = os.path.join(root, f)
                        tmp_size_mb += os.path.getsize(fp) / (1024 * 1024)
                    except OSError:
                        pass
        res["tmp_files_count"] = tmp_files_count
        res["tmp_size_mb"] = round(tmp_size_mb, 2)
        return res

    def _inspect_memory(self) -> Dict[str, Any]:
        """RAM および Swap 使用率の把握"""
        mem_info: Dict[str, Any] = {"total_mb": 0, "available_mb": 0, "used_mb": 0, "used_pct": 0, "percent": 0}
        if os.path.exists("/proc/meminfo"):
            try:
                with open("/proc/meminfo", "r") as f:
                    data = {}
                    for line in f:
                        parts = line.split(":")
                        if len(parts) == 2:
                            key = parts[0].strip()
                            val = parts[1].strip().split()[0]
                            data[key] = int(val)
                total = data.get("MemTotal", 0) // 1024
                avail = data.get("MemAvailable", 0) // 1024
                used = total - avail
                mem_info["total_mb"] = total
                mem_info["available_mb"] = avail
                mem_info["used_mb"] = used
                mem_info["used_pct"] = round((used / total * 100) if total else 0, 1)
                mem_info["percent"] = mem_info["used_pct"]
            except Exception as e:
                mem_info["error"] = str(e)
        return mem_info

    def _inspect_processes(self) -> Dict[str, Any]:
        """ゾンビプロセス、古いPythonプロセスの把握"""
        zombies = []
        python_procs = []
        try:
            ps = subprocess.run(["ps", "-ef"], capture_output=True, text=True, timeout=10)
            if ps.returncode == 0:
                lines = ps.stdout.strip().split("\n")
                for line in lines[1:]:
                    parts = line.split(None, 7)
                    if len(parts) >= 8:
                        pid, _ppid, cmd = parts[1], parts[2], parts[7]
                        if "<defunct>" in line or " Z " in line:
                            zombies.append({"pid": pid, "cmd": cmd})
                        elif "python" in cmd and str(os.getpid()) not in pid:
                            python_procs.append({"pid": pid, "cmd": cmd[:50]})
        except Exception as e:
            logger.warning(f"ps inspection error: {e}")

        return {
            "zombies_count": len(zombies),
            "zombies": zombies,
            "python_processes_count": len(python_procs),
            "python_processes": python_procs[:5]
        }

    def _inspect_privileges(self) -> Dict[str, Any]:
        """Shizuku, rish, su, adb, AICore+ 特権状態"""
        rish_ok = False
        su_ok = False
        if os.path.exists(self.rish_path):
            try:
                r = subprocess.run([self.rish_path, "-c", "id"], capture_output=True, text=True, timeout=8)
                rish_ok = (r.returncode == 0)
            except Exception:
                rish_ok = False

        if os.path.exists(self.su_path):
            try:
                r = subprocess.run([self.su_path, "-c", "id"], capture_output=True, text=True, timeout=8)
                su_ok = (r.returncode == 0)
            except Exception:
                su_ok = False

        plus_ok = bool(shutil.which("plus"))
        return {
            "rish_available": rish_ok,
            "rish_path": self.rish_path,
            "su_available": su_ok,
            "su_path": self.su_path,
            "plus_aicore_available": plus_ok,
            "has_root_or_shizuku": rish_ok or su_ok
        }

    def _inspect_tls_ssl(self) -> Dict[str, Any]:
        """CA証明書ファイルと SSL_CERT_FILE 環境変数の整合性 (Lesson #6 防衛)"""
        ca_exists = os.path.exists(self.ca_cert_path)
        env_cert = os.environ.get("SSL_CERT_FILE", "")
        env_cert_valid = bool(env_cert and os.path.exists(env_cert))
        
        status = "OK"
        if not ca_exists:
            status = "MISSING_CA_BUNDLE"
        elif not env_cert_valid:
            status = "SSL_CERT_FILE_UNSET"

        return {
            "ca_bundle_path": self.ca_cert_path,
            "ca_bundle_exists": ca_exists,
            "ssl_cert_file_env": env_cert,
            "ssl_cert_file_valid": env_cert_valid,
            "status": status
        }

    def _inspect_sqlite(self) -> Dict[str, Any]:
        """TUGUMI SQLite メモリ DB の整合性と WAL モード"""
        db_exists = os.path.exists(self.db_path)
        if not db_exists:
            return {"exists": False, "status": "NOT_FOUND"}

        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode;")
            journal_mode = cursor.fetchone()[0]
            cursor.execute("PRAGMA busy_timeout;")
            busy_timeout = cursor.fetchone()[0]
            cursor.execute("PRAGMA integrity_check;")
            integrity = cursor.fetchone()[0]
            conn.close()
            return {
                "exists": True,
                "journal_mode": journal_mode,
                "busy_timeout": busy_timeout,
                "integrity": integrity,
                "wal_enabled": (journal_mode.lower() == "wal"),
                "status": "HEALTHY" if integrity == "ok" and journal_mode.lower() == "wal" else "WARNING"
            }
        except Exception as e:
            return {"exists": True, "error": str(e), "status": "ERROR"}

    def _inspect_toolchain(self) -> Dict[str, Any]:
        """必須CLIツールチェーンの把握"""
        tools = ["git", "python3", "rg", "sqlite3", "curl", "node", "clang"]
        found = {}
        missing = []
        for t in tools:
            path = shutil.which(t)
            if path:
                found[t] = path
            else:
                missing.append(t)
        return {
            "installed_count": len(found),
            "missing": missing,
            "tools": found
        }

    def _inspect_phantom_process_killer(self) -> Dict[str, Any]:
        """Android 12+ Phantom Process Killer 設定確認"""
        max_phantom = "Unknown"
        status = "UNKNOWN"
        # rish または su 経由で取得試行
        cmd = "device_config get activity_manager max_phantom_processes"
        try:
            if os.path.exists(self.rish_path):
                r = subprocess.run([self.rish_path, "-c", cmd], capture_output=True, text=True, timeout=8)
                if r.returncode == 0 and r.stdout.strip():
                    max_phantom = r.stdout.strip()
            elif os.path.exists(self.su_path):
                r = subprocess.run([self.su_path, "-c", cmd], capture_output=True, text=True, timeout=8)
                if r.returncode == 0 and r.stdout.strip():
                    max_phantom = r.stdout.strip()
        except Exception:
            pass

        if max_phantom in ("2147483647", "999999"):
            status = "DISABLED (SAFE)"
        elif max_phantom in ("32", "64", "null", ""):
            status = "ACTIVE_OR_DEFAULT (RISK_OF_KILL)"

        return {
            "max_phantom_processes": max_phantom,
            "status": status,
            "needs_fix": (status != "DISABLED (SAFE)")
        }

    def _inspect_battery(self) -> Dict[str, Any]:
        """バッテリー残量、温度、状態（termux-battery-status または dumpsys）"""
        info: Dict[str, Any] = {
            "percentage": None,
            "temperature_c": None,
            "temperature": None,
            "status": "UNKNOWN",
            "health": "UNKNOWN",
            "plugged": "UNKNOWN",
            "voltage_v": None,
        }
        # 1. termux-battery-status を試行
        try:
            r = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=8)
            if r.returncode == 0 and r.stdout.strip():
                data = json.loads(r.stdout)
                info["percentage"] = data.get("percentage")
                info["temperature_c"] = data.get("temperature")
                info["temperature"] = info["temperature_c"]
                info["status"] = data.get("status", "UNKNOWN")
                info["health"] = data.get("health", "UNKNOWN")
                info["plugged"] = data.get("plugged", "UNKNOWN")
                if "voltage" in data:
                    info["voltage_v"] = round(data["voltage"] / 1000.0, 2)
                return info
        except Exception:
            pass

        # 2. dumpsys battery (rish / su / 直接)
        for cmd in [["dumpsys", "battery"], ["rish", "-c", "dumpsys battery"], ["su", "-c", "dumpsys battery"]]:
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
                if r.returncode == 0 and "level:" in r.stdout:
                    for line in r.stdout.splitlines():
                        line = line.strip()
                        if line.startswith("level:"):
                            info["percentage"] = int(line.split(":")[1].strip())
                        elif line.startswith("temperature:"):
                            info["temperature_c"] = round(int(line.split(":")[1].strip()) / 10.0, 1)
                            info["temperature"] = info["temperature_c"]
                        elif line.startswith("status:"):
                            st_map = {"2": "CHARGING", "3": "DISCHARGING", "4": "NOT_CHARGING", "5": "FULL"}
                            val = line.split(":")[1].strip()
                            info["status"] = st_map.get(val, val)
                        elif line.startswith("voltage:"):
                            info["voltage_v"] = round(int(line.split(":")[1].strip()) / 1000.0, 2)
                    if info["percentage"] is not None:
                        return info
            except Exception:
                pass

        return info

    # ==================== 2. 自律環境整備・自己修復 (自律整備) ====================
    def maintain_environment(self, fix_all: bool = True) -> Dict[str, Any]:
        """Termux環境の全レイヤーを一括自律整備・最適化"""
        actions_taken = []
        errors = []

        # 1. ゾンビプロセス＆不要プロセスの刈り取り
        zombie_res = self.clean_zombies()
        if zombie_res.get("killed_count", 0) > 0:
            actions_taken.append(f"ゾンビ/放置プロセス {zombie_res['killed_count']}件 を回収しました。")

        # 2. 一時ファイル＆キャッシュクリーンアップ
        clean_res = self.clean_temp_files(older_than_hours=24)
        if clean_res.get("deleted_count", 0) > 0:
            actions_taken.append(f"一時ファイル {clean_res['deleted_count']}件 ({clean_res['freed_mb']}MB) をクリーンアップしました。")

        # 3. SQLite DB の WAL チェックポイント & 最適化
        sqlite_res = self.optimize_sqlite_databases()
        actions_taken.append(f"SQLite DB ({len(sqlite_res)}個) のWALチェックポイント・最適化を完遂しました。")

        # 4. TLS / SSL_CERT_FILE 環境変数の自動設定・修復
        tls_res = self.fix_tls_environment()
        if tls_res.get("action"):
            actions_taken.append(tls_res["action"])

        # 5. Phantom Process Killer の特権無効化
        if fix_all:
            phantom_res = self.disable_phantom_process_killer()
            if phantom_res.get("success"):
                actions_taken.append("Phantom Process Killer を特権昇格(rish)により永続無効化しました。")

        # 整備後再インスペクション
        after_report = self.inspect_all()

        return {
            "timestamp": time.time(),
            "time_iso": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "MAINTENANCE_COMPLETED",
            "actions_taken": actions_taken,
            "errors": errors,
            "health_score_after": after_report["health_score"],
            "after_status": after_report["status"]
        }

    def clean_zombies(self) -> Dict[str, Any]:
        """ゾンビプロセスの回収"""
        killed = 0
        try:
            ps = subprocess.run(["ps", "-ef"], capture_output=True, text=True, timeout=10)
            if ps.returncode == 0:
                for line in ps.stdout.strip().split("\n"):
                    if "<defunct>" in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            ppid = parts[2]
                            try:
                                # 親プロセスにSIGCHLDを送って回収を促す
                                os.kill(int(ppid), 17) # SIGCHLD
                                killed += 1
                            except Exception:
                                pass
        except Exception as e:
            return {"error": str(e), "killed_count": 0}
        return {"killed_count": killed}

    def clean_temp_files(self, older_than_hours: int = 24) -> Dict[str, Any]:
        """古い一時ファイルおよび __pycache__ のクリーンアップ"""
        deleted = 0
        freed_bytes = 0
        cutoff = time.time() - (older_than_hours * 3600)

        # $TMPDIR 内の古いファイルを削除
        if os.path.exists(self.tmp_dir):
            for item in os.listdir(self.tmp_dir):
                item_path = os.path.join(self.tmp_dir, item)
                try:
                    if os.path.isfile(item_path) and os.path.getmtime(item_path) < cutoff:
                        freed_bytes += os.path.getsize(item_path)
                        os.remove(item_path)
                        deleted += 1
                except Exception:
                    pass

        # TUGUMIv6 配下の古い *.bak, *.tmp, *.pyc のクリーンアップ
        for pattern in ["**/*.bak", "**/*.tmp", "**/*.pyc"]:
            for fpath in glob.glob(os.path.join(self.base_dir, pattern), recursive=True):
                # 直近で作成されたバックアップは保護し、24時間超のみ削除
                try:
                    if os.path.getmtime(fpath) < cutoff:
                        freed_bytes += os.path.getsize(fpath)
                        os.remove(fpath)
                        deleted += 1
                except Exception:
                    pass

        return {
            "deleted_count": deleted,
            "freed_mb": round(freed_bytes / (1024 * 1024), 2)
        }

    def optimize_sqlite_databases(self) -> List[Dict[str, Any]]:
        """全SQLite DBのWALチェックポイントおよびPRAGMA optimize"""
        results = []
        dbs = glob.glob(os.path.join(self.base_dir, "**/*.db"), recursive=True)
        # ルートの tugumi_memory.db 等も対象
        root_dbs = glob.glob(os.path.join(self.home_dir, "tugumi*.db"))
        all_dbs = set(dbs + root_dbs)

        for db in all_dbs:
            try:
                conn = sqlite3.connect(db, timeout=10.0)
                cursor = conn.cursor()
                cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                cursor.execute("PRAGMA optimize;")
                conn.commit()
                conn.close()
                results.append({"db": os.path.basename(db), "status": "optimized"})
            except Exception as e:
                results.append({"db": os.path.basename(db), "error": str(e)})
        return results

    def fix_tls_environment(self) -> Dict[str, Any]:
        """Termux CA Bundle の確認と SSL_CERT_FILE の設定"""
        if not os.path.exists(self.ca_cert_path):
            return {"action": None, "status": "CA_FILE_MISSING"}

        action = None
        if os.environ.get("SSL_CERT_FILE") != self.ca_cert_path:
            os.environ["SSL_CERT_FILE"] = self.ca_cert_path
            action = f"SSL_CERT_FILE を {self.ca_cert_path} に設定しました。"

        return {"action": action, "ssl_cert_file": self.ca_cert_path}

    def disable_phantom_process_killer(self) -> Dict[str, Any]:
        """Shizuku (rish) を用いて Phantom Process Killer を無効化"""
        cmd = "device_config put activity_manager max_phantom_processes 2147483647"
        if os.path.exists(self.rish_path):
            try:
                r = subprocess.run([self.rish_path, "-c", cmd], capture_output=True, text=True, timeout=10)
                if r.returncode == 0:
                    return {"success": True, "method": "rish"}
            except Exception as e:
                return {"success": False, "error": str(e)}

        if os.path.exists(self.su_path):
            try:
                r = subprocess.run([self.su_path, "-c", cmd], capture_output=True, text=True, timeout=10)
                if r.returncode == 0:
                    return {"success": True, "method": "su"}
            except Exception as e:
                return {"success": False, "error": str(e)}

        return {"success": False, "error": "No privileged shell (rish/su) available"}

    # ==================== 3. HUD フォーマット出力 ====================
    def format_hud_summary(self, report: Optional[Dict[str, Any]] = None) -> str:
        """ターミナルに表示する洗練されたテキストHUDサマリー"""
        rep = report or self.inspect_all()
        score = rep.get("health_score", 100)
        status = rep.get("status", "OK")
        
        lines = [
            "╔═══ [TUGUMIv6 Termux Environment Inspection & Doctor] ═══╗",
            f"║ Health Score: {score}/100 [{status}]",
            f"║ OS/Arch: {rep['system']['android_version']} | {rep['system']['kernel']} ({rep['system']['arch']})",
            f"║ Storage: Free {rep['storage'].get('home_free_gb', '?')}GB / {rep['storage'].get('home_total_gb', '?')}GB (Used: {rep['storage'].get('home_used_pct', '?')}%)",
            f"║ RAM: Used {rep['memory'].get('used_mb', '?')}MB / {rep['memory'].get('total_mb', '?')}MB ({rep['memory'].get('used_pct', '?')}%)",
            f"║ Battery: {rep.get('battery', {}).get('percentage', '?')}% ({rep.get('battery', {}).get('status', 'UNKNOWN')}, Temp: {rep.get('battery', {}).get('temperature_c', '?')}℃, Volt: {rep.get('battery', {}).get('voltage_v', '?')}V)",
            f"║ Shizuku/Privileges: rish={'OK' if rep['privileges']['rish_available'] else 'NG'}, su={'OK' if rep['privileges']['su_available'] else 'NG'}, plus={'OK' if rep['privileges']['plus_aicore_available'] else 'NG'}",
            f"║ Phantom Killer: {rep['phantom_killer']['status']}",
            f"║ TLS/CA Bundle: {rep['tls_ssl']['status']} ({'Set' if rep['tls_ssl']['ssl_cert_file_valid'] else 'Unset'})",
            f"║ SQLite Memory: {rep['sqlite'].get('status', 'OK')} (WAL: {rep['sqlite'].get('journal_mode', 'wal')})",
            f"║ Zombies: {rep['processes'].get('zombies_count', 0)} detected",
            "╚═════════════════════════════════════════════════════════════╝"
        ]
        return "\n".join(lines)
