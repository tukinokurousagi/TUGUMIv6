#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#   TUGUMIv6 WebUI Launcher (Cyber HUD WebUI)
#   Port: 8086
#   Dedicated to Master Takuma
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="python3"
WEB_SCRIPT="$SCRIPT_DIR/interfaces/web/web_server.py"
PID_FILE="$SCRIPT_DIR/data/webui.pid"
LOG_FILE="$SCRIPT_DIR/logs/webui.log"
PORT=8086
URL="http://127.0.0.1:$PORT"

if [ ! -f "$WEB_SCRIPT" ]; then
    echo -e "\033[91m[ERROR] WebUIスクリプト ($WEB_SCRIPT) が見つかりません。\033[0m" >&2
    exit 1
fi

cd "$SCRIPT_DIR"
mkdir -p "$SCRIPT_DIR/data" "$SCRIPT_DIR/logs"
export PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}"

# Termux wake lock (スリープ防止)
if command -v termux-wake-lock > /dev/null 2>&1; then
    termux-wake-lock 2>/dev/null || true
fi

# ブラウザ起動関数（Termux環境向け多重フォールバック）
open_browser() {
    local target_url="$1"
    if command -v termux-open-url > /dev/null 2>&1; then
        termux-open-url "$target_url" > /dev/null 2>&1 || true
    elif command -v am > /dev/null 2>&1; then
        am start --user 0 -a android.intent.action.VIEW -d "$target_url" > /dev/null 2>&1 || true
    elif command -v termux-open > /dev/null 2>&1; then
        termux-open "$target_url" > /dev/null 2>&1 || true
    elif command -v xdg-open > /dev/null 2>&1; then
        xdg-open "$target_url" > /dev/null 2>&1 || true
    fi
}

# アクセス情報＆QRコード表示関数（サブ端末・タブレット向け）
print_access_banner() {
    echo -e "\033[38;2;0;240;255m╔═════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[38;2;0;240;255m║   TUGUMIv6 WebUI (Cyber HUD) — Port: $PORT                     ║\033[0m"
    echo -e "\033[38;2;0;240;255m╚═════════════════════════════════════════════════════════════╝\033[0m"
    echo -e "ローカルアクセス: \033[38;2;255;42;133m\033[1m$URL/\033[0m"

    # サブ端末・タブレット向けWi-Fi IP取得＆QRコード描画
    "$PYTHON_BIN" -c '
import socket, subprocess, sys
def get_ip():
    try:
        res = subprocess.run(["rish", "-c", "ip -4 addr show wlan0"], capture_output=True, text=True, timeout=1)
        for line in res.stdout.splitlines():
            line = line.strip()
            if line.startswith("inet "):
                return line.split()[1].split("/")[0]
    except Exception:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if not ip.startswith("127."):
            return ip
    except Exception:
        pass
    return None

lan_ip = get_ip()
port = sys.argv[1] if len(sys.argv) > 1 else "8086"
if lan_ip:
    tab_url = f"http://{lan_ip}:{port}/"
    print(f"\033[38;5;82m📱 タブレット/サブ端末接続用URL:\033[0m \033[1m\033[38;5;226m{tab_url}\033[0m")
    try:
        import qrcode
        qr = qrcode.QRCode(box_size=1, border=1)
        qr.add_data(tab_url)
        print("\033[38;5;51m[カメラでスキャンして一発接続]\033[0m")
        qr.print_ascii(invert=True)
    except Exception:
        pass
' "$PORT" 2>/dev/null || true
}

print_access_banner

# -------------------------------------------------------------
# 既に稼働中の場合:
# ブラウザを開き、フォアグラウンド監視モードにアタッチ。
# [Ctrl+C] や exit でサーバーを停止しポート8086を即座に解放する。
# -------------------------------------------------------------
if curl -s -m 2 "$URL/api/health" 2>/dev/null | grep -q '"status":'; then
    echo -e "  \033[38;5;82m🟢 TUGUMIv6 WebUI サーバーは既に正常稼働中です！\033[0m"
    echo -e "  \033[38;5;208m🌐 ブラウザで $URL/ を開きます...\033[0m"
    open_browser "$URL/"
    echo ""
    echo -e "  \033[38;5;196m\033[1m🛑 [Ctrl+C] を押すとサーバーを停止しポート8086を解放します。\033[0m"
    echo -e "\033[38;5;244m─────────────────────────────────────────────────────────────\033[0m"

    stop_attached() {
        echo ""
        echo -e "\033[38;5;196m🛑 停止シグナルを受信しました。WebUIサーバーを停止しポート8086を解放します...\033[0m"
        # API経由で優雅に停止
        curl -s -m 2 -X POST "$URL/api/system/shutdown" > /dev/null 2>&1 || true
        sleep 0.5
        # PIDファイルがあればチェックしてkill
        if [ -f "$PID_FILE" ]; then
            RUNNING_PID=$(cat "$PID_FILE" 2>/dev/null || true)
            if [ -n "$RUNNING_PID" ] && kill -0 "$RUNNING_PID" 2>/dev/null; then
                kill "$RUNNING_PID" 2>/dev/null || true
            fi
            rm -f "$PID_FILE"
        fi
        # ポート8086が残っていれば確実に終了
        pkill -f "interfaces/web/web_server.py" 2>/dev/null || true
        echo -e "\033[38;5;82m✅ TUGUMIv6 WebUI サーバーを停止し、ポート8086を解放しました。\033[0m"
        exit 0
    }
    trap stop_attached INT TERM HUP

    # サーバー稼働状態を監視
    while true; do
        if ! curl -s -m 1 "$URL/api/health" 2>/dev/null | grep -q '"status":'; then
            echo ""
            echo -e "\033[38;5;244mℹ️ サーバーの停止を検知しました。ポート8086は解放されています。\033[0m"
            exit 0
        fi
        sleep 1
    done
fi

# -------------------------------------------------------------
# 新規起動: フォアグラウンド実行
# [Ctrl+C] や 端末終了時にトラップで確実にサーバー停止・ポート解放
# -------------------------------------------------------------

# 起動監視＆自動ブラウザオープン (超高速/api/healthエンドポイントをバックグラウンドポーリング・最大30秒)
(
    for i in $(seq 1 60); do
        sleep 0.5
        if curl -s -m 2 "$URL/api/health" 2>/dev/null | grep -q '"status":'; then
            echo ""
            echo -e "  \033[38;5;82m🌐 WebUIの正常起動を確認！ブラウザで $URL/ を開きます...\033[0m"
            open_browser "$URL/"
            break
        fi
    done
) &
BROWSER_PID=$!

SERVER_CHILD_PID=""

cleanup_server() {
    if [ -n "$BROWSER_PID" ] && kill -0 "$BROWSER_PID" 2>/dev/null; then
        kill "$BROWSER_PID" 2>/dev/null || true
    fi
    if [ -n "$SERVER_CHILD_PID" ] && kill -0 "$SERVER_CHILD_PID" 2>/dev/null; then
        echo ""
        echo -e "\033[38;5;196m🛑 WebUI サーバープロセスを停止中 (PID: $SERVER_CHILD_PID)...\033[0m"
        kill "$SERVER_CHILD_PID" 2>/dev/null || true
        sleep 0.3
        if kill -0 "$SERVER_CHILD_PID" 2>/dev/null; then
            kill -9 "$SERVER_CHILD_PID" 2>/dev/null || true
        fi
    fi
    rm -f "$PID_FILE" 2>/dev/null || true
    echo -e "\033[38;5;82m✅ TUGUMIv6 WebUI サーバーを停止し、ポート8086を解放しました。\033[0m"
}
trap cleanup_server EXIT INT TERM HUP

echo -e "  \033[38;5;196m\033[1m🛑 [Ctrl+C] を押すとサーバーをいつでも瞬時に停止しポートを解放できます。\033[0m"
echo ""

# Pythonサーバーを子プロセスとして実行し、waitで待機
"$PYTHON_BIN" "$WEB_SCRIPT" "$@" &
SERVER_CHILD_PID=$!
echo "$SERVER_CHILD_PID" > "$PID_FILE"

wait "$SERVER_CHILD_PID" || true
