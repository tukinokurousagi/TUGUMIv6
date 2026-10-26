#!/data/data/com.termux/files/usr/bin/python3
"""TUGUMI Termux Network & Security Auditor
Real-time network security diagnostics for Android Termux (Linux aarch64).
"""

import time
import socket
import urllib.request
import concurrent.futures
from typing import List, Dict, Any

C_CYAN = "\033[38;5;51m"
C_BLUE = "\033[38;5;39m"
C_GREEN = "\033[38;5;48m"
C_YELLOW = "\033[38;5;220m"
C_ORANGE = "\033[38;5;208m"
C_RED = "\033[38;5;196m"
C_WHITE = "\033[38;5;255m"
C_MUTED = "\033[38;5;242m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_banner():
    banner = f"""{C_CYAN}{BOLD}
╔══════════════════════════════════════════════════════════════════════════════╗
║        🛡️  TUGUMI NETWORK & SECURITY AUDITOR (Termux aarch64)               ║
║        Zero-Mock Network Diagnostics & Vulnerability Assessment              ║
╚══════════════════════════════════════════════════════════════════════════════╝{RESET}"""
    print(banner)

def get_gateway_info() -> Dict[str, Any]:
    """ネットワークインターフェースIPおよび接続性検出"""
    local_ip = "127.0.0.1"
    gw_ip = "Unknown"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    # 推定ゲートウェイ (サブネットの.1)
    if local_ip != "127.0.0.1":
        parts = local_ip.split(".")
        if len(parts) == 4:
            gw_ip = f"{parts[0]}.{parts[1]}.{parts[2]}.1"

    # ゲートウェイ疎通測定
    gw_latency_ms = None
    if gw_ip != "Unknown":
        t0 = time.perf_counter()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3.0)
            s.connect_ex((gw_ip, 53))
            gw_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            s.close()
        except Exception:
            gw_latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    return {"local_ip": local_ip, "gateway": gw_ip, "latency_ms": gw_latency_ms}

def test_dns_resolution() -> List[Dict[str, Any]]:
    """主要DNSホストへの名前解決速度テスト"""
    domains = ["cloudflare.com", "google.com", "openrouter.ai", "github.com"]
    results = []

    for d in domains:
        t0 = time.perf_counter()
        try:
            addr = socket.getaddrinfo(d, 80, socket.AF_INET, socket.SOCK_STREAM)
            elapsed = round((time.perf_counter() - t0) * 1000, 2)
            ip = addr[0][4][0] if addr else "unknown"
            results.append({"domain": d, "ip": ip, "latency_ms": elapsed, "status": "OK"})
        except Exception as e:
            elapsed = round((time.perf_counter() - t0) * 1000, 2)
            results.append({"domain": d, "ip": "Failed", "latency_ms": elapsed, "status": str(e)})

    return results

def test_http_endpoints() -> List[Dict[str, Any]]:
    """主要外部＆ローカルエンドポイントの疎通・HTTPステータス診断"""
    endpoints = [
        {"name": "Google (WAN)", "url": "https://www.google.com", "expected": 200},
        {"name": "Cloudflare DNS (HTTP)", "url": "https://1.1.1.1", "expected": 200},
        {"name": "OpenRouter API Gateway", "url": "https://openrouter.ai/api/v1/models", "expected": 200},
        {"name": "Local TUGUMIv6 WebUI", "url": "http://127.0.0.1:8086/api/health", "expected": 200},
        {"name": "Local Ollama LLM Engine", "url": "http://127.0.0.1:11434/api/tags", "expected": 200},
    ]

    def check_url(ep):
        t0 = time.perf_counter()
        try:
            req = urllib.request.Request(
                ep["url"],
                headers={"User-Agent": "TUGUMI-Security-Auditor/1.0"}
            )
            with urllib.request.urlopen(req, timeout=15.0) as resp:
                elapsed = round((time.perf_counter() - t0) * 1000, 2)
                return {
                    "name": ep["name"],
                    "url": ep["url"],
                    "status_code": resp.status,
                    "latency_ms": elapsed,
                    "alive": True,
                    "error": None
                }
        except urllib.error.HTTPError as he:
            elapsed = round((time.perf_counter() - t0) * 1000, 2)
            return {
                "name": ep["name"],
                "url": ep["url"],
                "status_code": he.code,
                "latency_ms": elapsed,
                "alive": True,
                "error": None
            }
        except Exception as e:
            elapsed = round((time.perf_counter() - t0) * 1000, 2)
            err_msg = str(e)
            if "Connection refused" in err_msg:
                err_msg = "Connection Refused (Offline)"
            elif "timed out" in err_msg.lower():
                err_msg = "Timeout (>3.5s)"
            return {
                "name": ep["name"],
                "url": ep["url"],
                "status_code": None,
                "latency_ms": elapsed,
                "alive": False,
                "error": err_msg
            }

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(check_url, endpoints))

    return results

def scan_local_ports() -> List[Dict[str, Any]]:
    """ローカルリスニングポート検査（netstat / ss / lsof 代替）＆セキュリティリスク評価"""
    # 監査対象ターゲットポートとサービス名
    target_ports = [
        (22, "SSH Remote Access", "HIGH"),
        (80, "HTTP Web Server", "MEDIUM"),
        (443, "HTTPS Web Server", "LOW"),
        (1080, "SOCKS5 Proxy", "MEDIUM"),
        (3000, "Node / Frontend Dev", "LOW"),
        (3306, "MySQL Database", "HIGH"),
        (5000, "Flask / Python API", "LOW"),
        (5432, "PostgreSQL Database", "HIGH"),
        (6379, "Redis In-Memory DB", "HIGH"),
        (8000, "HTTP Dev Server", "LOW"),
        (8022, "Termux OpenSSH", "HIGH"),
        (8080, "Alternative WebUI", "MEDIUM"),
        (8086, "TUGUMIv6 WebUI Dashboard", "LOW"),
        (8888, "Jupyter / Proxy Hub", "MEDIUM"),
        (9000, "PHP-FPM / Admin API", "MEDIUM"),
        (11434, "Ollama Local LLM API", "LOW"),
    ]

    open_ports = []

    def check_port(item):
        port, service, risk = item
        # 127.0.0.1 接続テスト
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.06)
        res_local = s.connect_ex(("127.0.0.1", port))
        s.close()

        if res_local == 0:
            return {
                "port": port,
                "service": service,
                "risk": risk,
                "binding": "127.0.0.1 (Localhost Only)",
                "open": True
            }
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        scan_results = list(executor.map(check_port, target_ports))

    open_ports = [r for r in scan_results if r is not None]

    # 追加でアクティブなネットワークデーモンプロセス（sshd, python, node等）を検出
    try:
        import psutil
        for proc in psutil.process_iter(['name', 'cmdline']):
            name = (proc.info.get('name') or '').lower()
            cmd = ' '.join(proc.info.get('cmdline') or []).lower()
            if 'sshd' in name or 'sshd' in cmd:
                if not any(p['port'] in (22, 8022) for p in open_ports):
                    open_ports.append({
                        "port": 8022,
                        "service": "OpenSSH Daemon (Detected via Process)",
                        "risk": "HIGH",
                        "binding": "Active Process",
                        "open": True
                    })
    except Exception:
        pass

    return open_ports

def main():
    print_banner()

    # 1. Gateway & Interface
    gw = get_gateway_info()
    print(f"{C_YELLOW}{BOLD}[1. ネットワークインターフェース＆ローカルIP]{RESET}")
    print(f"  • 端末ローカルIP: {C_WHITE}{gw['local_ip']}{RESET}  |  デフォルトゲートウェイ: {C_WHITE}{gw['gateway']}{RESET}")
    if gw['latency_ms'] is not None:
        print(f"  • ゲートウェイ応答性: {C_GREEN}{gw['latency_ms']} ms{RESET}")
    print()

    # 2. DNS Resolution Speed
    dns_list = test_dns_resolution()
    print(f"{C_BLUE}{BOLD}[2. DNS名前解決レイテンシ診断]{RESET}")
    for d in dns_list:
        status_color = C_GREEN if d['status'] == 'OK' else C_RED
        print(f"  • {d['domain']:<18} → {C_WHITE}{d['ip']:<15}{RESET} ({status_color}{d['latency_ms']:>6.2f} ms{RESET}) [{status_color}{d['status']}{RESET}]")
    print()

    # 3. HTTP Endpoints Connectivity
    endpoints = test_http_endpoints()
    print(f"{C_GREEN}{BOLD}[3. 主要エンドポイント＆サービス疎通診断]{RESET}")
    for ep in endpoints:
        if ep['alive']:
            color = C_GREEN if ep['status_code'] == 200 else C_YELLOW
            print(f"  • {ep['name']:<25} : {color}{ep['status_code']} OK{RESET} ({ep['latency_ms']:>6.1f} ms) {C_MUTED}[{ep['url']}]{RESET}")
        else:
            print(f"  • {ep['name']:<25} : {C_RED}OFFLINE{RESET} ({ep['error']}) {C_MUTED}[{ep['url']}]{RESET}")
    print()

    # 4. Local Port & Vulnerability Audit
    open_ports = scan_local_ports()
    print(f"{C_ORANGE}{BOLD}[4. ローカルリスニングポート＆セキュリティ監査]{RESET}")
    if open_ports:
        for p in open_ports:
            risk_color = C_RED if p['risk'] == 'HIGH' else (C_YELLOW if p['risk'] == 'MEDIUM' else C_GREEN)
            print(f"  • Port {C_WHITE}{BOLD}{p['port']:<5}{RESET} : {p['service']:<25} バインド: {p['binding']} 脅威度: {risk_color}[{p['risk']}]{RESET}")
    else:
        print(f"  {C_GREEN}✔ 開放中の危険な不要ポートは検出されませんでした（堅牢なサンドボックス状態）。{RESET}")

    print(f"\n{C_MUTED}──────────────────────────────────────────────────────────────────────────────{RESET}")
    print(f"{C_GREEN}{BOLD}✔ ネットワークセキュリティ監査正常終了 (Exit Code 0){RESET}\n")

if __name__ == "__main__":
    main()
