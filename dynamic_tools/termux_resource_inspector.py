#!/data/data/com.termux/files/usr/bin/python3
"""Synthesized Skill: termux_resource_inspector
Description: Auto-synthesized tool from self-evolution topic: Termux System Diagnostics
"""

import os
import shutil
import time
import subprocess
import json
try:
    import psutil
except ImportError:
    psutil = None

def get_battery_info() -> dict:
    """バッテリー状態を取得 (termux-battery-status または sysfs)"""
    try:
        res = subprocess.run(["termux-battery-status"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)
        if res.returncode == 0:
            return json.loads(res.stdout)
    except Exception:
        pass

    bat_path = "/sys/class/power_supply/battery"
    if os.path.exists(bat_path):
        info = {}
        try:
            if os.path.exists(f"{bat_path}/capacity"):
                with open(f"{bat_path}/capacity") as f:
                    info["percentage"] = int(f.read().strip())
            if os.path.exists(f"{bat_path}/status"):
                with open(f"{bat_path}/status") as f:
                    info["status"] = f.read().strip()
            if os.path.exists(f"{bat_path}/temp"):
                with open(f"{bat_path}/temp") as f:
                    info["temperature"] = round(int(f.read().strip()) / 10.0, 1)
            return info
        except Exception:
            pass
    return {"percentage": "N/A", "status": "unknown"}

def inspect_termux_resources() -> dict:
    """Termux / Android システムリソース（メモリ、ストレージ、CPU、バッテリー、稼働時間）を精密診断"""
    home_path = os.path.expanduser("~")
    total, used, free = shutil.disk_usage(home_path)

    sd_usage = None
    if os.path.exists("/storage/emulated/0"):
        try:
            s_tot, s_usd, s_fre = shutil.disk_usage("/storage/emulated/0")
            sd_usage = {
                "total_gb": round(s_tot / (1024**3), 2),
                "free_gb": round(s_fre / (1024**3), 2),
                "used_percent": round((s_usd / max(1, s_tot)) * 100, 1)
            }
        except Exception:
            pass

    mem_data = {}
    proc_count = 0
    boot_time_str = "N/A"
    if psutil:
        mem = psutil.virtual_memory()
        mem_data = {
            "total_mb": round(mem.total / (1024**2), 1),
            "available_mb": round(mem.available / (1024**2), 1),
            "used_mb": round(mem.used / (1024**2), 1),
            "percent": mem.percent
        }
        try:
            proc_count = len(psutil.pids())
            btime = psutil.boot_time()
            uptime_sec = int(time.time() - btime)
            hours, rem = divmod(uptime_sec, 3600)
            mins, secs = divmod(rem, 60)
            boot_time_str = f"{hours}h {mins}m {secs}s"
        except Exception:
            pass
    else:
        try:
            with open("/proc/meminfo") as f:
                lines = f.readlines()
                for line in lines:
                    if "MemTotal:" in line:
                        mem_data["total_mb"] = round(int(line.split()[1]) / 1024, 1)
                    elif "MemAvailable:" in line:
                        mem_data["available_mb"] = round(int(line.split()[1]) / 1024, 1)
        except Exception:
            pass

    load_avg = [0.0, 0.0, 0.0]
    try:
        load_avg = [round(x, 2) for x in os.getloadavg()]
    except Exception:
        pass

    battery = get_battery_info()

    return {
        "status": "success",
        "timestamp": time.time(),
        "system": {
            "os": os.uname().sysname if hasattr(os, 'uname') else 'Linux',
            "arch": os.uname().machine if hasattr(os, 'uname') else 'unknown',
            "cpu_count": os.cpu_count() or 1,
            "load_avg": load_avg,
            "process_count": proc_count,
            "uptime": boot_time_str
        },
        "storage_home": {
            "total_gb": round(total / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "used_percent": round((used / max(1, total)) * 100, 1)
        },
        "storage_shared": sd_usage,
        "memory": mem_data,
        "battery": battery
    }

# エイリアス（動的ツール登録名互換）
termux_resource_inspector = inspect_termux_resources

def main():
    import sys
    data = inspect_termux_resources()
    if "--json" in sys.argv:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    C_CYAN = "\033[38;5;51m"
    C_GREEN = "\033[38;5;48m"
    C_YELLOW = "\033[38;5;220m"
    C_MAGENTA = "\033[38;5;201m"
    C_WHITE = "\033[38;5;255m"
    C_MUTED = "\033[38;5;242m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    print(f"{C_CYAN}{BOLD}╔══════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{C_CYAN}{BOLD}║         📱 TUGUMIv6 Termux / Android システム精密診断レポート             ║{RESET}")
    print(f"{C_CYAN}{BOLD}╚══════════════════════════════════════════════════════════════════════════╝{RESET}")

    sys_info = data["system"]
    print(f"{C_YELLOW}{BOLD}[CPU & システム]{RESET}")
    print(f"  • アーキテクチャ: {C_WHITE}{sys_info['arch']}{RESET} (コア数: {sys_info['cpu_count']})")
    print(f"  • ロードアベレージ (1/5/15分): {C_WHITE}{sys_info['load_avg']}{RESET}")
    print(f"  • 稼働プロセス数: {C_WHITE}{sys_info['process_count']}{RESET}  |  システム稼働時間: {C_WHITE}{sys_info['uptime']}{RESET}")

    mem = data["memory"]
    print(f"\n{C_GREEN}{BOLD}[メモリ (RAM)]{RESET}")
    print(f"  • 合計: {C_WHITE}{mem.get('total_mb', 'N/A')} MB{RESET}  |  空き: {C_WHITE}{mem.get('available_mb', 'N/A')} MB{RESET}")
    pct = mem.get('percent', 0)
    bar_len = 30
    filled = int(bar_len * (pct / 100))
    bar = f"{C_GREEN}{'█' * filled}{C_MUTED}{'░' * (bar_len - filled)}{RESET}"
    print(f"  • 使用率: [{bar}] {pct}%")

    st = data["storage_home"]
    print(f"\n{C_MAGENTA}{BOLD}[内部ストレージ (Termux HOME)]{RESET}")
    print(f"  • 合計容量: {C_WHITE}{st['total_gb']} GB{RESET}  |  空き容量: {C_WHITE}{st['free_gb']} GB{RESET} ({st['used_percent']}% 使用)")

    if data.get("storage_shared"):
        sd = data["storage_shared"]
        print(f"\n{C_MAGENTA}{BOLD}[共有外部ストレージ (/sdcard)]{RESET}")
        print(f"  • 合計容量: {C_WHITE}{sd['total_gb']} GB{RESET}  |  空き容量: {C_WHITE}{sd['free_gb']} GB{RESET} ({sd['used_percent']}% 使用)")

    bat = data["battery"]
    print(f"\n{C_YELLOW}{BOLD}[バッテリー診断]{RESET}")
    pct_b = bat.get('percentage', 'N/A')
    status_b = bat.get('status', 'unknown')
    temp_b = bat.get('temperature', bat.get('temperature_c', 'N/A'))
    print(f"  • 残量: {C_WHITE}{pct_b}%{RESET}  |  状態: {C_WHITE}{status_b}{RESET}  |  温度: {C_WHITE}{temp_b}°C{RESET}")
    print(f"\n{C_MUTED}──────────────────────────────────────────────────────────────────────────{RESET}")
    print(f"{C_GREEN}✔ 全リソース診断正常完了 (Exit Code 0){RESET}")

if __name__ == '__main__':
    main()
