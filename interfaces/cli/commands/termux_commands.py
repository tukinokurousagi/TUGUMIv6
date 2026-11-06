# -*- coding: utf-8 -*-
"""
TUGUMIv6 Termux Real-Device Native Command Suite (termux_commands.py)
Termux Android CUI に特化した実用的・画期的スラッシュコマンド拡張群:
- Shell Direct Pass-through ($ cmd, ! cmd, /sh cmd)
- Latest Screenshot Auto-Vision Analysis (/ss [query], /screenshot)
- Two-way Android Clipboard Integration (/copy, /cp, /paste, /clip)
- Android App Native Opener & Share (/open <path|last>, /share <path|last>)
- Cyberpunk Smartphone Battery HUD (/battery, /power)
- TUGUMIv6 WebUI Full Background Control (/web [start|stop|status|open])
- PWA & App Icon Health Inspector (/app, /pwa)
- Arsenal & Port Instant Reverse Lookup (/find <query>)
- Termux Process & Memory Cyber Dock (/top, /ps)
- Termux Toast & Notification Dispatch (/toast <msg>, /noti <msg>)
"""

import os
import glob
import json
import shutil
import subprocess
import time
from typing import Optional, Dict, Any, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn

from interfaces.cli.cyber_theme import CYBER_PALETTES

SCREENSHOT_DIR = "/storage/emulated/0/Pictures/Screenshots"
TUGUMIDESK_ROOT = "/storage/emulated/0/TUGUMIDesk"
CATALOG_FILE = os.path.join(TUGUMIDESK_ROOT, "共有フォルダ", "00_共有フォルダ総合カタログ・早引きインデックス.md")
WEBUI_PORT = 8086
WEBUI_URL = f"http://127.0.0.1:{WEBUI_PORT}"


def get_latest_screenshot() -> Optional[str]:
    """最新のスクリーンショットファイルの絶対パスを取得"""
    if not os.path.isdir(SCREENSHOT_DIR):
        return None
    patterns = [os.path.join(SCREENSHOT_DIR, ext) for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp")]
    files = []
    for pat in patterns:
        files.extend(glob.glob(pat))
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def execute_shell_passthrough(cmd_str: str, console: Console, mode: str = "light") -> int:
    """Termuxシェル直結実行 ($ cmd, ! cmd, /sh cmd)"""
    p = CYBER_PALETTES.get(mode, CYBER_PALETTES["light"])
    clean_cmd = cmd_str.strip()
    if clean_cmd.startswith("$") or clean_cmd.startswith("!"):
        clean_cmd = clean_cmd[1:].strip()
    elif clean_cmd.startswith("/sh") or clean_cmd.startswith("/bash"):
        clean_cmd = clean_cmd.split(maxsplit=1)[1] if len(clean_cmd.split()) > 1 else ""

    if not clean_cmd:
        console.print(f"[bold yellow]⚠️ 実行するシェルコマンドを入力してください (例: $ ls -la, ! git status)[/bold yellow]\n")
        return 1

    console.print(f"\n[dim]⚡ Termux Shell Exec:[/] [bold {p['primary']}]{clean_cmd}[/bold {p['primary']}]")
    start_t = time.time()
    try:
        res = subprocess.run(
            clean_cmd,
            shell=True,
            text=True,
            capture_output=True,
            timeout=120
        )
        elapsed = time.time() - start_t
        code_color = "green" if res.returncode == 0 else "red"
        
        output_body = []
        if res.stdout:
            output_body.append(res.stdout.rstrip())
        if res.stderr:
            output_body.append(f"[bold red]{res.stderr.rstrip()}[/bold red]")
        if not output_body:
            output_body.append("[dim](出力なし)[/dim]")

        content = "\n".join(output_body)
        console.print(Panel(
            content,
            title=f"[bold {p['primary']}]◈ Termux Shell Output ◈[/bold {p['primary']}] [dim]({elapsed:.2f}s | Exit: [{code_color}]{res.returncode}[/{code_color}])[/dim]",
            border_style=p["border"],
            expand=False
        ))
        console.print()
        return res.returncode
    except subprocess.TimeoutExpired:
        console.print(f"[bold red]❌ コマンド実行がタイムアウトしました (120秒超過)[/bold red]\n")
        return 124
    except Exception as e:
        console.print(f"[bold red]❌ シェル実行エラー: {e}[/bold red]\n")
        return 1


def handle_latest_screenshot_analysis(
    query: str,
    engine: Any,
    console: Console,
    mode: str = "light"
) -> bool:
    """最新スクリーンショットの自動検出＆Gemini Vision推論 (/ss [質問], /screenshot)"""
    p = CYBER_PALETTES.get(mode, CYBER_PALETTES["light"])
    latest_img = get_latest_screenshot()
    if not latest_img:
        console.print(f"[bold yellow]⚠️ スクリーンショットフォルダ ({SCREENSHOT_DIR}) に画像が見つかりません。[/bold yellow]\n")
        return False

    file_name = os.path.basename(latest_img)
    file_size_kb = os.path.getsize(latest_img) / 1024
    user_prompt = query.strip() if query.strip() else "この画面の内容を詳細に認識・解説し、エラーや重要情報があれば原因と具体的な解決手順を教えてください。"

    console.print(Panel(
        f"[bold cyan]• 対象画像:[/] [bold white]{file_name}[/bold white] ({file_size_kb:.1f} KB)\n"
        f"[bold cyan]• 保存パス:[/] [dim]{latest_img}[/dim]\n"
        f"[bold cyan]• 解析プロンプト:[/] [yellow]{user_prompt}[/yellow]\n"
        f"[bold green]👁️ Gemini Vision マルチモーダル推論を実行中...[/bold green]",
        title=f"[bold {p['primary']}]◈ 最新スクショ自動ビジョン解析 (/ss) ◈[/bold {p['primary']}]",
        border_style=p["border"]
    ))

    try:
        from PIL import Image
        img = Image.open(latest_img)

        # EngineManager の Vision 推論を実行
        prompt_parts = [
            "【マスター拓磨様の端末最新スクリーンショット視覚解析】\n"
            f"指示: {user_prompt}\n\n"
            "以下の手順で構造化して回答してください:\n"
            "1. 【画面の概要と現在開いているアプリ・UI】\n"
            "2. 【検出された重要テキスト・ログ・エラー情報】\n"
            "3. 【分析・原因特定（エラーや疑問点がある場合）】\n"
            "4. 【マスター拓磨様への具体的かつ最短のアクション・解決策】",
            img
        ]

        console.print(f"\n[bold {p['secondary']}]つぐみ（ビジョン推論モード）が回答を生成中...🌸[/bold {p['secondary']}]\n")
        
        # エンジン経由で推論
        if hasattr(engine, "generate_content"):
            resp = engine.generate_content(prompt_parts)
            text_out = resp.text if hasattr(resp, "text") else str(resp)
        else:
            # フォールバック: genai direct client
            client = engine.client if hasattr(engine, "client") else None
            if client:
                res = client.models.generate_content(
                    model=getattr(engine, "current_model", "gemini-3.8-flash"),
                    contents=prompt_parts
                )
                text_out = res.text
            else:
                text_out = "推論クライアントを取得できませんでした。"

        from rich.markdown import Markdown
        console.print(Panel(
            Markdown(text_out),
            title=f"[bold {p['primary']}]◈ ビジョン解析結果: {file_name} ◈[/bold {p['primary']}]",
            border_style=p["border"]
        ))
        console.print()
        return True
    except Exception as e:
        console.print(f"[bold red]❌ ビジョン解析エラー: {e}[/bold red]\n")
        return False


def handle_clipboard_copy(text: str, console: Console, mode: str = "light") -> bool:
    """Androidクリップボードへのテキストコピー (/copy, /cp)"""
    p = CYBER_PALETTES.get(mode, CYBER_PALETTES["light"])
    if not text or not text.strip():
        console.print(f"[bold yellow]⚠️ クリップボードにコピーする対象のテキストがありません。[/bold yellow]\n")
        return False

    clean_text = text.strip()
    try:
        proc = subprocess.Popen(["termux-clipboard-set"], stdin=subprocess.PIPE, text=True)
        proc.communicate(input=clean_text, timeout=5)
        # トースト表示 (可能なら)
        subprocess.run(["termux-toast", "✔ つぐみの回答をクリップボードにコピーしました🌸"], capture_output=True, timeout=2)
        
        preview = clean_text[:120] + ("..." if len(clean_text) > 120 else "")
        console.print(Panel(
            f"[bold green]✔ つぐみの回答テキスト ({len(clean_text):,} 文字) を端末クリップボードにコピーしました！[/bold green]\n\n"
            f"[dim]内容プレビュー:\n{preview}[/dim]\n\n"
            f"[cyan]💡 他のアプリ（ブラウザ、メモ、LINE等）でそのまま貼り付けできます。[/cyan]",
            title=f"[bold {p['primary']}]◈ Android Clipboard Copied (/copy) ◈[/bold {p['primary']}]",
            border_style="green"
        ))
        console.print()
        return True
    except Exception as e:
        console.print(f"[bold red]❌ クリップボードコピー失敗: {e}[/bold red]\n")
        return False


def handle_clipboard_paste(console: Console, mode: str = "light") -> Optional[str]:
    """Androidクリップボードからのテキスト取得 (/paste, /clip)"""
    p = CYBER_PALETTES.get(mode, CYBER_PALETTES["light"])
    try:
        res = subprocess.run(["termux-clipboard-get"], capture_output=True, text=True, timeout=5)
        clip_content = res.stdout.strip()
        if not clip_content:
            console.print(f"[bold yellow]ℹ️ クリップボードは現在空です。[/bold yellow]\n")
            return None

        preview = clip_content[:200] + ("..." if len(clip_content) > 200 else "")
        console.print(Panel(
            f"[bold cyan]• クリップボード取得文字数:[/] {len(clip_content):,} 文字\n\n"
            f"[bold white]{preview}[/bold white]\n\n"
            f"[dim]※ この内容をプロンプトとして質問・解析する場合は、そのまま Enter または追加指示を入力してください。[/dim]",
            title=f"[bold {p['primary']}]◈ Android Clipboard Content (/paste) ◈[/bold {p['primary']}]",
            border_style=p["border"]
        ))
        console.print()
        return clip_content
    except Exception as e:
        console.print(f"[bold red]❌ クリップボード取得エラー: {e}[/bold red]\n")
        return None


def handle_native_open(target: str, last_file: Optional[str], console: Console, mode: str = "light") -> bool:
    """Androidのネイティブアプリ（ビュワー・ブラウザ・エディタ）で開く (/open)"""
    p = CYBER_PALETTES.get(mode, CYBER_PALETTES["light"])
    target_path = target.strip()
    if not target_path or target_path == "last":
        if last_file and os.path.exists(last_file):
            target_path = last_file
        else:
            # 最新のスクショまたは直近成果物
            latest_ss = get_latest_screenshot()
            if latest_ss:
                target_path = latest_ss
            else:
                console.print(f"[bold yellow]⚠️ 開く対象のファイルパスが指定されておらず、直前のファイルもありません。[/bold yellow]\n")
                return False

    target_path = os.path.expanduser(target_path)
    if not os.path.exists(target_path) and not target_path.startswith(("http://", "https://")):
        console.print(f"[bold red]❌ 指定されたファイルが見つかりません: {target_path}[/bold red]\n")
        return False

    try:
        subprocess.run(["termux-open", target_path], capture_output=True, timeout=5)
        console.print(f"[bold green]✔ Android ネイティブアプリで開きました: [white]{target_path}[/white][/bold green]\n")
        return True
    except Exception as e:
        console.print(f"[bold red]❌ termux-open 起動エラー: {e}[/bold red]\n")
        return False


def handle_native_share(target: str, last_file: Optional[str], console: Console, mode: str = "light") -> bool:
    """Androidの共有ダイアログでファイルを共有 (/share)"""
    p = CYBER_PALETTES.get(mode, CYBER_PALETTES["light"])
    target_path = target.strip()
    if not target_path or target_path == "last":
        if last_file and os.path.exists(last_file):
            target_path = last_file
        else:
            latest_ss = get_latest_screenshot()
            if latest_ss:
                target_path = latest_ss
            else:
                console.print(f"[bold yellow]⚠️ 共有するファイルが指定されていません。[/bold yellow]\n")
                return False

    target_path = os.path.expanduser(target_path)
    if not os.path.exists(target_path):
        console.print(f"[bold red]❌ 共有対象ファイルが見つかりません: {target_path}[/bold red]\n")
        return False

    try:
        subprocess.run(["termux-share", target_path], capture_output=True, timeout=5)
        console.print(f"[bold green]✔ Android 共有ダイアログを展開しました: [white]{target_path}[/white][/bold green]\n")
        return True
    except Exception as e:
        console.print(f"[bold red]❌ termux-share 実行エラー: {e}[/bold red]\n")
        return False


def show_cyber_battery_hud(console: Console, mode: str = "light") -> None:
    """スマホバッテリー＆ハードウェア診断HUD (/battery, /power)"""
    p = CYBER_PALETTES.get(mode, CYBER_PALETTES["light"])
    try:
        res = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=5)
        if res.returncode != 0:
            console.print(f"[bold yellow]⚠️ termux-battery-status の出力を取得できませんでした。[/bold yellow]\n")
            return
        data = json.loads(res.stdout)
    except Exception as e:
        console.print(f"[bold red]❌ バッテリー情報取得エラー: {e}[/bold red]\n")
        return

    pct = data.get("percentage", 0)
    temp = data.get("temperature", 0.0)
    health = data.get("health", "UNKNOWN")
    status = data.get("status", "UNKNOWN")
    plugged = data.get("plugged", "UNPLUGGED")
    voltage = data.get("voltage", 0) / 1000.0
    current_ma = abs(data.get("current", 0)) / 1000.0

    # カラーバーの生成
    bar_len = 24
    filled_len = int(bar_len * (pct / 100.0))
    bar_color = "green" if pct > 40 else ("yellow" if pct > 20 else "red")
    bar_str = f"[{bar_color}]{'█' * filled_len}{'░' * (bar_len - filled_len)}[/{bar_color}]"

    # 温度警告
    temp_color = "green" if temp < 40.0 else ("yellow" if temp < 43.0 else "bold red")
    temp_icon = "❄️" if temp < 38.0 else ("🌡️" if temp < 43.0 else "🔥")

    plug_str = "[bold green]⚡ 充電中[/bold green]" if plugged != "UNPLUGGED" else "[dim]放電中[/dim]"

    content = (
        f"[bold cyan]残量ステータス:[/]  {bar_str}  [bold {bar_color}]{pct}%[/bold {bar_color}] ({plug_str})\n"
        f"[bold cyan]バッテリー温度:[/]  {temp_icon} [{temp_color}]{temp:.1f} ℃[/{temp_color}]  [dim](正常範囲: 25〜42℃)[/dim]\n"
        f"[bold cyan]セル健康状態:[/]    [bold green]{health}[/bold green] | [cyan]電圧:[/] {voltage:.2f} V | [cyan]電流:[/] {current_ma:.0f} mA\n"
        f"[bold cyan]接続タイプ:[/]      {plugged} ({status})\n"
    )
    if temp >= 42.0:
        content += f"\n[bold red]⚠️ 警告: 端末温度が高温です。高負荷処理時は冷却を推奨します。[/bold red]"

    console.print(Panel(
        content,
        title=f"[bold {p['primary']}]◈ Termux Smartphone Power & Battery HUD (/battery) ◈[/bold {p['primary']}]",
        border_style=p["border"]
    ))
    console.print()


def handle_webui_control(subcmd: str, console: Console, mode: str = "light") -> None:
    """TUGUMIv6 WebUI サーバー完全制御 (/web [start|stop|restart|status|open])"""
    p = CYBER_PALETTES.get(mode, CYBER_PALETTES["light"])
    sub = subcmd.strip().lower() if subcmd.strip() else "status"

    web_script = os.path.expanduser("~/TUGUMIv6/interfaces/web/web_server.py")
    pid_file = os.path.expanduser("~/TUGUMIv6/data/webui.pid")

    def is_running() -> Tuple[bool, Optional[int]]:
        try:
            res = subprocess.run(["curl", "-s", "-m", "1", f"{WEBUI_URL}/api/health"], capture_output=True, text=True)
            if '"status":' in res.stdout:
                if os.path.exists(pid_file):
                    try:
                        with open(pid_file, "r") as f:
                            return True, int(f.read().strip())
                    except Exception:
                        pass
                return True, None
        except Exception:
            pass
        return False, None

    running, pid = is_running()

    if sub in ("status", "info"):
        state_str = f"[bold green]🟢 稼働中 (Online)[/bold green]" if running else f"[bold yellow]🟡 停止中 (Offline)[/bold yellow]"
        pid_str = f"PID: {pid}" if pid else ("(外部起動またはPID未記録)" if running else "")
        console.print(Panel(
            f"[bold cyan]• WebUI 稼働状態:[/] {state_str} {pid_str}\n"
            f"[bold cyan]• ローカルURL:[/] [bold #00f0ff]{WEBUI_URL}/[/bold #00f0ff]\n"
            f"[bold cyan]• リッスンポート:[/] {WEBUI_PORT}\n"
            f"[bold cyan]• PWA アプリアイコン:[/] [green]つぐみちゃんアプリアイコン配備済[/green]\n\n"
            f"[dim]操作コマンド:\n"
            f"  • `/web start`   : バックグラウンドでサーバーを起動\n"
            f"  • `/web stop`    : サーバーを停止してポート解放\n"
            f"  • `/web open`    : ブラウザで WebUI を開く\n"
            f"  • `/web restart` : サーバーを再起動[/dim]",
            title=f"[bold {p['primary']}]◈ TUGUMIv6 WebUI Controller (/web) ◈[/bold {p['primary']}]",
            border_style=p["border"]
        ))
        console.print()

    elif sub in ("start", "run", "launch"):
        if running:
            console.print(f"[bold green]🟢 WebUI サーバーは既に稼働中です！[/bold green] ({WEBUI_URL}/)")
            subprocess.run(["termux-open-url", f"{WEBUI_URL}/"], capture_output=True)
            console.print(f"[cyan]🌐 ブラウザで開きました。[/cyan]\n")
            return

        console.print(f"[bold cyan]🚀 WebUI サーバーをバックグラウンド起動中 (Port: {WEBUI_PORT})...[/bold cyan]")
        log_file = os.path.expanduser("~/TUGUMIv6/logs/webui.log")
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        os.makedirs(os.path.dirname(pid_file), exist_ok=True)

        cmd = f"nohup python3 {web_script} > {log_file} 2>&1 & echo $!"
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        new_pid = proc.stdout.strip()
        if new_pid:
            with open(pid_file, "w") as f:
                f.write(new_pid)

        # 起動待機 (最大5秒ポーリング)
        success = False
        for _ in range(10):
            time.sleep(0.5)
            r, _ = is_running()
            if r:
                success = True
                break

        if success:
            console.print(Panel(
                f"[bold green]✔ TUGUMIv6 WebUI サーバーが正常に起動いたしました！[/bold green]\n\n"
                f"[bold cyan]• URL:[/] [bold #00f0ff]{WEBUI_URL}/[/bold #00f0ff]\n"
                f"[bold cyan]• PID:[/] {new_pid}\n"
                f"[bold cyan]• ログ:[/] `{log_file}`\n\n"
                f"[green]🌐 ブラウザで画面を自動展開します...[/green]",
                title=f"[bold {p['primary']}]◈ WebUI 起動完了 ◈[/bold {p['primary']}]",
                border_style="green"
            ))
            subprocess.run(["termux-open-url", f"{WEBUI_URL}/"], capture_output=True)
        else:
            console.print(f"[bold red]❌ サーバー起動の確認がタイムアウトしました。ログを確認してください: `{log_file}`[/bold red]")
        console.print()

    elif sub in ("stop", "kill", "down"):
        if not running:
            console.print(f"[bold yellow]ℹ️ WebUI サーバーは既に停止しています。[/bold yellow]\n")
            return

        console.print(f"[yellow]🛑 WebUI サーバーを停止中...[/yellow]")
        try:
            subprocess.run(["curl", "-s", "-m", "2", "-X", "POST", f"{WEBUI_URL}/api/system/shutdown"], capture_output=True)
        except Exception:
            pass
        time.sleep(0.5)
        subprocess.run(["pkill", "-f", "interfaces/web/web_server.py"], capture_output=True)
        if os.path.exists(pid_file):
            try:
                os.remove(pid_file)
            except Exception:
                pass
        console.print(f"[bold green]✔ WebUI サーバーを停止し、ポート {WEBUI_PORT} を解放いたしました、拓磨様🌸[/bold green]\n")

    elif sub in ("restart", "reboot"):
        handle_webui_control("stop", console, mode)
        time.sleep(1)
        handle_webui_control("start", console, mode)

    elif sub in ("open", "browse"):
        if not running:
            console.print(f"[bold yellow]⚠️ サーバーが停止しているため、先に起動します...[/bold yellow]")
            handle_webui_control("start", console, mode)
        else:
            subprocess.run(["termux-open-url", f"{WEBUI_URL}/"], capture_output=True)
            console.print(f"[bold green]✔ ブラウザで {WEBUI_URL}/ を開きました！[/bold green]\n")


def handle_app_inspector(console: Console, mode: str = "light") -> None:
    """PWA & アプリアイコン健康診断 (/app, /pwa)"""
    p = CYBER_PALETTES.get(mode, CYBER_PALETTES["light"])
    static_dir = os.path.expanduser("~/TUGUMIv6/interfaces/web/static")
    icon_192 = os.path.join(static_dir, "icon-192.png")
    icon_512 = os.path.join(static_dir, "icon-512.png")
    manifest = os.path.join(static_dir, "manifest.json")

    has_192 = os.path.exists(icon_192)
    has_512 = os.path.exists(icon_512)
    has_man = os.path.exists(manifest)

    status_192 = f"[bold green]✔ 配備済 ({os.path.getsize(icon_192)/1024:.1f} KB)[/bold green]" if has_192 else "[bold red]✖ 未配置[/bold red]"
    status_512 = f"[bold green]✔ 配備済 ({os.path.getsize(icon_512)/1024:.1f} KB)[/bold green]" if has_512 else "[bold red]✖ 未配置[/bold red]"

    content = (
        f"[bold white]TUGUMIv6 PWA / WebAPK アプリアイコン診断:[/bold white]\n\n"
        f"[bold cyan]• 標準アイコン (192x192):[/] {status_192}\n"
        f"[bold cyan]• 高解像度アイコン (512x512):[/] {status_512}\n"
        f"[bold cyan]• Webマニフェスト:[/] {'[bold green]✔ 正常[/bold green]' if has_man else '[bold red]✖ 異常[/bold red]'}\n\n"
        f"[bold yellow]📱 ホーム画面アイコンの即時更新手順:[/bold yellow]\n"
        f"  1. スマホの「設定 ➔ アプリ ➔ TUGUMIv6」またはアプリアイコン長押しから **アンインストール**\n"
        f"  2. `/web open` でブラウザを開く\n"
        f"  3. ブラウザの右上「︙」メニューから **「アプリをインストール」** を押す\n"
        f"  ➔ 一瞬で可愛いつぐみのアイコンに切り替わります🌸"
    )

    console.print(Panel(
        content,
        title=f"[bold {p['primary']}]◈ PWA & App Icon Inspector (/app) ◈[/bold {p['primary']}]",
        border_style=p["border"]
    ))
    console.print()


def handle_instant_find(query: str, console: Console, mode: str = "light") -> None:
    """社内武器庫・スクリプト・ポート・カタログ即時逆引き (/find <query>)"""
    p = CYBER_PALETTES.get(mode, CYBER_PALETTES["light"])
    q = query.strip()
    if not q:
        console.print(f"[bold yellow]⚠️ 検索キーワードを入力してください (例: /find binance, /find port, /find 救済)[/bold yellow]\n")
        return

    console.print(f"\n[cyan]🔍 共有カタログ・社内武器庫を高速検索中:[/] [bold white]{q}[/bold white]...")
    results = []

    # 1. カタログファイル内を検索
    if os.path.exists(CATALOG_FILE):
        try:
            with open(CATALOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    if q.lower() in line.lower():
                        results.append(f"[dim]カタログ L{line_num}:[/dim] {line.strip()}")
        except Exception:
            pass

    # 2. ~/bin/ のスクリプト名を検索
    bin_dir = os.path.expanduser("~/bin")
    if os.path.isdir(bin_dir):
        for fname in os.listdir(bin_dir):
            if q.lower() in fname.lower():
                full_path = os.path.join(bin_dir, fname)
                results.append(f"[bold green]~/bin/{fname}[/bold green] [dim]({full_path})[/dim]")

    if not results:
        console.print(f"[bold yellow]ℹ️ '{q}' に一致するツールやカタログ項目は見つかりませんでした。[/bold yellow]\n")
        return

    # 最大15件表示
    display_rows = results[:15]
    content = "\n".join(f"• {r}" for r in display_rows)
    if len(results) > 15:
        content += f"\n\n[dim]※ 他 {len(results) - 15} 件の一致項目があります。[/dim]"

    console.print(Panel(
        content,
        title=f"[bold {p['primary']}]◈ 社内武器庫・カタログ即時逆引き (/find: {q}) ◈[/bold {p['primary']}]",
        border_style=p["border"]
    ))
    console.print()


def show_top_processes(console: Console, mode: str = "light") -> None:
    """Termux内プロセス＆メモリ使用状況HUD (/top, /ps)"""
    p = CYBER_PALETTES.get(mode, CYBER_PALETTES["light"])
    try:
        res = subprocess.run(
            ["ps", "-ef"],
            capture_output=True,
            text=True,
            timeout=5
        )
        lines = res.stdout.splitlines()
    except Exception as e:
        console.print(f"[bold red]❌ プロセス一覧取得エラー: {e}[/bold red]\n")
        return

    # Termux環境の主要プロセスを抽出 (python, node, bun, ollama, bash等)
    proc_table = Table(
        title=f"[bold {p['primary']}]◈ Termux Active Processes HUD (/top) ◈[/bold {p['primary']}]",
        border_style=p["border"],
        show_header=True,
        header_style=f"bold {p['secondary']}",
        expand=True
    )
    proc_table.add_column("PID", style="cyan", width=8, justify="right")
    proc_table.add_column("User", style="dim", width=10)
    proc_table.add_column("Time", style="yellow", width=8)
    proc_table.add_column("Command", style="white")

    count = 0
    for line in lines[1:]:
        parts = line.split(maxsplit=7)
        if len(parts) >= 8:
            uid, pid, ppid, c, stime, tty, time_str, cmd = parts
            # 興味のあるプロセスに絞り込み
            if any(k in cmd.lower() for k in ("python", "node", "bun", "ollama", "shizuku", "sshd", "tmux", "web_server")):
                short_cmd = cmd[:50] + ("..." if len(cmd) > 50 else "")
                proc_table.add_row(pid, uid, time_str, short_cmd)
                count += 1
                if count >= 12:
                    break

    if count == 0:
        for line in lines[1:10]:
            parts = line.split(maxsplit=7)
            if len(parts) >= 8:
                proc_table.add_row(parts[1], parts[0], parts[6], parts[7][:50])

    console.print(proc_table)
    console.print(f"[dim]※ 不要なプロセス停止は `/sh kill <PID>` または `/doctor` で自動クリーンアップできます。[/dim]\n")
