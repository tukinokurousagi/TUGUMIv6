#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#   TUGUMIv6 CLI Core Launcher
#   Google Gemini 3.8 Flash & Antigravity Core
#   Dedicated to Master Takuma
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="python3"

MAIN_SCRIPT="$SCRIPT_DIR/interfaces/cli/main.py"

if [ ! -f "$MAIN_SCRIPT" ]; then
    echo -e "\033[91m[ERROR] メインスクリプト ($MAIN_SCRIPT) が見つかりません。\033[0m"
    exit 1
fi

export PYTHONWARNINGS="ignore"

# GOOGLE_API_KEY と GEMINI_API_KEY の重複警告を完全抑止
if [ -n "$GOOGLE_API_KEY" ] && [ -n "$GEMINI_API_KEY" ]; then
    unset GEMINI_API_KEY
fi

cd "$SCRIPT_DIR"
exec "$PYTHON_BIN" "$MAIN_SCRIPT" "$@"
