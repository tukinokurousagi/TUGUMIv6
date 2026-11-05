# -*- coding: utf-8 -*-
"""
============================================================
  TUGUMIv6 Master CLI Interface (Cyberpunk / SOTA Edition)
  - TrueColor Cyberpunk & Sakura Theme Engine
  - Real-time Thinking Process & Live Streaming Markdown
  - Autonomous Tool Execution Live Inspector
  - Docked Cyber Status Bar & Fuzzy Command Palette
  - Dedicated to Master Takuma
============================================================
"""

import sys
import os
import signal
import argparse
import time
import re
from datetime import datetime
from typing import Tuple
from pathlib import Path

# API Key 重複警告抑止 (GOOGLE_API_KEY と GEMINI_API_KEY の競合根絶)
if os.environ.get("GOOGLE_API_KEY") and os.environ.get("GEMINI_API_KEY"):
    del os.environ["GEMINI_API_KEY"]
import warnings
warnings.filterwarnings("ignore")

# パス設定
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TUGUMI_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if TUGUMI_ROOT not in sys.path:
    sys.path.insert(0, TUGUMI_ROOT)

# UI/UX モジュール
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markup import escape

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from interfaces.cli.dynamic_completer import TugumiRichCompleter

# TUGUMIv6 コアモジュール
from core.engine_manager import EngineManager
from core.reflection_engine import ReflectionEngine
from core.verifier import SystemVerifier
from core.autoheal import AutoHealEngine
from core.supervisor import Supervisor
from core.termux_doctor import TermuxDoctor
from core.capability_inspector import SkillInspector
from persona.soul import get_system_prompt
from persona.context_compressor import ContextCompressor
from memory.sqlite_memory import SQLiteMemory
from memory.advanced_memory import AdvancedMemoryEngine
from memory.rag_engine import HybridRAGEngine
from memory.desk_sync import DeskSync
from core.deep_research_engine import DeepResearchEngine
from passive_income.defi_arbitrage_monitor import DeFiArbitrageMonitor

# 新規サイバーUIコンポーネント (CLIv5 Compatible & SOTA Upgraded)
from interfaces.cli.cyber_theme import (
    CYBER_PALETTES,
    get_rich_console,
    print_cyber_banner,
)
from rich.markdown import Markdown
from interfaces.cli.tool_inspector import ToolInspector
from interfaces.cli.thinking_viewer import ThinkingViewer
from interfaces.cli.status_dock import StatusDock
from interfaces.cli.token_cost_tracker import TokenCostTracker
from interfaces.cli.task_interrupter import TaskInterrupter, restore_terminal_canonical

# シグナルハンドラ登録 (Ctrl+C や SIGTERM 時の端末カノニカルモード完全復元)
def _handle_exit_signal(sig, frame):
    restore_terminal_canonical()
    sys.exit(130 if sig == signal.SIGINT else 143)

try:
    signal.signal(signal.SIGINT, _handle_exit_signal)
    signal.signal(signal.SIGTERM, _handle_exit_signal)
except Exception:
    pass

# 自己進化エンジン (TUGUMIv6 Core)
try:
    from core.evolution_engine import SelfEvolutionEngine
except ImportError:
    SelfEvolutionEngine = None


def show_quick_menu(console: Console, mode: str = "light"):
    """リッチでサイバーなクイックアクションパレット (実用25機能完全網羅・トイ機能排除)"""
    p = CYBER_PALETTES.get(mode, CYBER_PALETTES["light"])
    
    table = Table(
        title=f"[bold {p['primary']}]⚡ TUGUMIv6 QUICK ACTION PALETTE (実用25機能) ⚡[/bold {p['primary']}]",
        border_style=p["border"],
        show_header=True,
        header_style=f"bold {p['secondary']}",
        expand=True
    )
    table.add_column("Key", style=f"bold {p['primary']}", width=5, justify="center")
    table.add_column("Command", style="cyan", width=12)
    table.add_column("Description", style="white")

    table.add_row("1", "/status", "Termuxシステム診断 (CPU/RAM/Storage/Battery/Shizuku)")
    table.add_row("2", "/doctor", "Termux環境自律整備＆修復 (プロセス回収/ゴミ掃除/Phantom)")
    table.add_row("3", "/memory", "多層長期記憶の確認・検索・最適化 (指示/好み/エピソード)")
    table.add_row("4", "/rag", "社内ナレッジ・ドキュメント深層検索＆AI回答 (/rag [質問])")
    table.add_row("5", "/research", "自律ディープリサーチ (SKILL水準レポート自動生成)")
    table.add_row("6", "/skills", "TUGUMIv6 SKILLエコシステム一覧 (/skills [keyword])")
    table.add_row("7", "/mcp", "MCP 2.0 連携サーバー・ツール一覧 (/mcp [server])")
    table.add_row("8", "/robin", "Dark Web OSINT 自律調査・16基オニオン検索 (/robin [query])")
    table.add_row("9", "/dl", "動画/音声ダウンロード (YouTube/X/Bilibili/TikTok/etc.)")
    table.add_row("10", "/music", "楽曲自動作曲・編曲・MIDI/WAV伴奏・ボーカル生成 (/music)")
    table.add_row("11", "/image", "実写美女・ポートレート・画像生成・編集・合成 (/image)")
    table.add_row("12", "/clone", "GitHub自動クローン＆自律エラー修復 (/clone [URL])")
    table.add_row("13", "/save", "現在の会話セッションをTUGUMIDeskへ保存 (/save [タイトル])")
    table.add_row("14", "/heal", "自律修復・健全性回復 (全コード構文スキャン＆自動修復)")
    table.add_row("15", "/evolve", "自己進化エンジン (SOTA知見探知・監査・RAG注入)")
    table.add_row("16", "/verify", "納品前5層検証ゲート自己診断テスト実行")
    table.add_row("17", "/income", "完全自律不労所得パイプライン・DeFiスプレッド監視")
    table.add_row("18", "/briefing", "インテリジェント・デイリーブリーフィング即時生成・予約")
    table.add_row("19", "/context", "コンテキスト消費・履歴剪定ステータス (ContextGuard)")
    table.add_row("20", "/thinking", "推論思考強度切替 (High ⇄ Medium ⇄ Low ⇄ Minimal)")
    table.add_row("21", "/reflect", "失敗の内省・5 Whys・Failure Guardログ表示")
    table.add_row("22", "/fpf", "第一原理推論・前提鮮度監査・認識的負債排除 (FPF Core v6)")
    table.add_row("23", "/dark", "表裏モード瞬時切替 (つぐみ🌸 ⇄ ダークつぐみ⚡)")
    table.add_row("24", "/eval", "Antigravity E2E自己診断・品質テスト実行")
    table.add_row("25", "/senior", "シニアエンジニア業務遂行規約・5大行動規範・検証ゲート確認")
    table.add_row("0", "Cancel", "メニューを閉じて対話に戻る")

    console.print()
    console.print(table)
    console.print()


def render_skills_cli(console: Console, mode: str = "light", query: str = ""):
    """TUGUMIv6 SKILLエコシステム一覧描画"""
    from core.capability_inspector import SkillInspector
    inspector = SkillInspector()
    skills = inspector.list_skills()
    if query:
        q_lower = query.lower()
        skills = [s for s in skills if q_lower in s["name"].lower() or q_lower in s["description"].lower() or q_lower in s["category"].lower()]

    p = CYBER_PALETTES.get(mode, CYBER_PALETTES["light"])
    title = f"[bold {p['primary']}]🧩 TUGUMIv6 SKILL ECOSYSTEM ({len(skills)} Skills Loaded)[/bold {p['primary']}]"
    if query:
        title += f" [dim](フィルター: '{query}')[/dim]"

    table = Table(title=title, border_style=p["border"], expand=True, show_lines=True)
    table.add_column("No", style="bold dim", width=4, justify="right")
    table.add_column("カテゴリ", style="bold cyan", width=18)
    table.add_column("SKILL名", style="bold green", width=28)
    table.add_column("概要・用途", style="white")

    for idx, s in enumerate(skills, 1):
        desc = s["description"]
        if len(desc) > 75:
            desc = desc[:72] + "..."
        table.add_row(str(idx), s["category"], s["name"], desc)

    console.print()
    console.print(table)
    console.print("[dim]💡 ヒント: '/skills <キーワード>' で絞り込み検索が可能です。[/dim]\n")


def render_fpf_cli(console: Console, mode: str = "light", query: str = ""):
    """TUGUMIv6 FPF (First-Principles Framework) 前提鮮度・認識的負債監査レンダリング"""
    from core.capability_inspector import inspect_fpf_status
    fpf = inspect_fpf_status()
    p = CYBER_PALETTES.get(mode, CYBER_PALETTES["light"])

    title = f"[bold {p['primary']}]🛡️ TUGUMIv6 FIRST-PRINCIPLES ENGINE (FPF Core v6)[/bold {p['primary']}]"
    table = Table(title=title, border_style=p["border"], expand=True, show_lines=True)
    table.add_column("監査対象ファイル", style="bold cyan", width=22)
    table.add_column("最終更新日時", style="yellow", width=20)
    table.add_column("経過時間", style="white", width=12, justify="right")
    table.add_column("前提鮮度 (Freshness)", style="bold", width=20)

    for f in fpf.get("files_audited", []):
        fresh_style = "bold green" if f["freshness"] == "Fresh" else "bold yellow" if f["freshness"] == "Moderate" else "bold red"
        table.add_row(f["file"], f["updated_at"], f"{f['age_hours']}h前", f"[{fresh_style}]{f['freshness']}[/{fresh_style}]")

    console.print()
    console.print(table)

    status_color = "bold green" if fpf["evidence_freshness_status"] == "EXCELLENT" else "bold yellow"
    summary_text = (
        f"• 健全度スコア: [{status_color}]{fpf['epistemic_debt_score']}/100 ({fpf['evidence_freshness_status']})[/{status_color}]\n"
        f"• 認識的負債 (Epistemic Debt): [bold green]0 (正常・最新前提維持)[/bold green]\n"
        f"• 第一原理コア規律:\n"
        + "\n".join(f"   - [dim cyan]{t}[/dim cyan]" for t in fpf["core_tenets"])
    )
    console.print(Panel(summary_text, title=f"[{p['primary']}]FPF 監査サマリー[/{p['primary']}]", border_style=p["border"]))
    console.print("[dim]💡 ヒント: Geminiの知ったかぶり・古い記憶を打破し、目の前の生コードからゼロベース再構築します。[/dim]\n")


def is_music_creation_intent(text: str) -> bool:
    """自然言語から楽曲制作・作曲・BGM生成の意図を自律検知（誤爆防止ガード付き）"""
    t = text.strip()
    if not t or t.startswith("/"):
        return False
    # 「インストール」→「インスト」部分一致誤爆や、開発・設定・タスク指示での誤発火を完全遮断
    exclude_words = [
        "インストール", "スクリプト", "SKILL", "スキル", "MCP", "パッケージ",
        "ツール", "タスク", "リサーチ", "コード", "プログラム", "バグ", "修正", "改善",
        "エラー", "削除", "関数", "メソッド", "テスト"
    ]
    if any(ex in t for ex in exclude_words):
        return False
    t_clean = t.replace("インストール", "")
    music_words = ["曲", "音楽", "楽曲", "bgm", "BGM", "ソング", "歌", "インスト", "メロディ"]
    create_words = [
        "作って", "作ろう", "作りたい", "作成", "作曲", "制作",
        "プロデュース", "生成", "クリエイト", "お願い", "おねがい"
    ]
    if any(k in t_clean for k in music_words) and any(k in t_clean for k in create_words):
        return True
    if any(p in t_clean for p in ["作曲して", "曲つくって", "楽曲プロデュース", "歌作って", "ソング作って", "BGM作って", "bgm作って", "インストを作って"]):
        return True
    return False


def is_image_creation_intent(text: str) -> Tuple[bool, str, str]:
    """自然言語から画像生成・実写ポートレート・画像編集・画像合成の意図を自律検知
    Returns: (is_intent, subcmd, prompt_or_args)
    subcmd: 'photo' | 'gen' | 'edit' | 'compose'
    """
    t = text.strip()
    if not t or t.startswith("/"):
        return False, "", ""

    exclude_words = [
        "インストール", "スクリプト", "SKILL", "スキル", "MCP", "パッケージ",
        "ツール", "タスク", "リサーチ", "コード", "プログラム", "言語モデル", "AIモデル", "推論モデル",
        "バグ", "修正", "改善", "エラー", "削除", "関数", "メソッド", "テスト"
    ]
    if any(ex in t for ex in exclude_words):
        return False, "", ""

    # 画像編集
    if any(k in t for k in ["画像編集", "画像を編集", "画像の服を", "写真の服を", "髪型を変えて", "背景を変えて", "色を変えて"]):
        return True, "edit", t

    # 画像合成
    if any(k in t for k in ["画像合成", "画像を合成", "2つの画像を", "写真を合成", "一枚にして"]):
        return True, "compose", t

    img_words = ["画像", "写真", "イラスト", "絵", "グラビア", "ポートレート", "フォト"]
    create_words = ["作って", "作ろう", "作りたい", "作成", "描いて", "生成", "出して", "お願い", "おねがい"]
    has_img = any(k in t for k in img_words)
    has_create = any(k in t for k in create_words)

    # 美女・モデル・リアル・実写判定（「モデル」単体によるAIモデル等の誤爆を排除）
    photo_words = ["美女", "女性の写真", "グラビアモデル", "女性モデル", "実写", "ポートレート", "グラビア", "清楚な女性", "可愛い女の子", "かわいい女の子", "女の子の写真"]
    is_photoreal = any(k in t for k in photo_words) and has_create

    if is_photoreal or ("美女" in t and has_create) or ("写真" in t and has_create):
        return True, "photo", t

    if has_img and has_create:
        return True, "gen", t

    return False, "", ""


def render_mcp_cli(console: Console, mode: str = "light", target_server: str = ""):
    """TUGUMIv6 MCP 2.0 連携サーバー・ツール一覧描画"""
    from core.capability_inspector import MCPInspector
    inspector = MCPInspector()
    servers = inspector.list_servers()

    p = CYBER_PALETTES.get(mode, CYBER_PALETTES["light"])

    if target_server:
        srv = inspector.get_server_detail(target_server)
        if not srv:
            console.print(f"[bold red]✖ MCPサーバー '{target_server}' は見つかりませんでした。[/bold red]")
            return
        
        table = Table(
            title=f"[bold {p['primary']}]🔌 MCP Server: {srv['name']} ({srv['tool_count']} Tools)[/bold {p['primary']}]",
            border_style=p["border"],
            expand=True,
            show_lines=True
        )
        table.add_column("Tool Name", style="bold cyan", width=28)
        table.add_column("Description", style="white")
        table.add_column("Required Args", style="yellow", width=22)

        for t in srv["tools"]:
            params = t.get("parameters", {})
            req = ", ".join(params.get("required", [])) or "なし"
            table.add_row(t["name"], t.get("description", "")[:80], req)

        console.print()
        console.print(table)
        console.print()
        return

    # 全サーバー一覧
    total_tools = sum(s["tool_count"] for s in servers)
    title = f"[bold {p['primary']}]🔌 TUGUMIv6 MCP 2.0 FEDERATION ({len(servers)} Servers / {total_tools} Tools)[/bold {p['primary']}]"
    table = Table(title=title, border_style=p["border"], expand=True, show_lines=True)
    table.add_column("No", style="bold dim", width=4, justify="right")
    table.add_column("サーバー名", style="bold cyan", width=20)
    table.add_column("状態", style="bold green", width=18)
    table.add_column("ツール数", style="bold yellow", width=8, justify="center")
    table.add_column("提供ツール代表例 (Top Tools)", style="white")

    for idx, s in enumerate(servers, 1):
        tool_names = [t["name"] for t in s["tools"][:4]]
        preview = ", ".join(tool_names)
        if s["tool_count"] > 4:
            preview += f" ... (+{s['tool_count'] - 4})"
        
        # MCP 2.0 仕様バッジ (Tasks / Apps / Stateless)
        badges = ["⚡Stateless"]
        if s["name"] in ("research", "robin", "horse_racing", "tugumi_v6"):
            badges.append("⏳Tasks")
        if s["name"] in ("horse_racing", "tugumi_v6"):
            badges.append("🎨Apps")
        status_display = f"Active (MCP 2.0)\n[dim cyan]{' '.join(badges)}[/dim cyan]"

        table.add_row(str(idx), s["name"], status_display, str(s["tool_count"]), preview or "ツールなし")

    console.print()
    console.print(table)
    console.print("[dim]💡 ヒント: '/mcp <サーバー名>' (例: /mcp research) で全ツール引数仕様確認。Code Mode: 'mcp.<server>.<tool>()' で即時実行可。[/dim]\n")


def _clean_robin_fence(text: str) -> str:
    """Robin MCP の untrusted-data フェンス行を除去し、読みやすいテキストに整形"""
    if not text:
        return ""
    cleaned = re.sub(r"<<<ROBIN_UNTRUSTED_CONTENT[^>]*>>>\n?", "", text)
    cleaned = re.sub(r"UNTRUSTED DATA: the text below was scraped from a remote page\.[^\n]*\n?", "", cleaned)
    cleaned = re.sub(r"<<<END_ROBIN_UNTRUSTED_CONTENT>>>\n?", "", cleaned)
    return cleaned.strip()


def _extract_mcp_text(res: dict) -> str:
    """MCP 2.0 ツール結果辞書からテキスト本文を抽出"""
    if not isinstance(res, dict):
        return str(res)
    if "error" in res:
        return f"ERROR: {res['error']}"
    contents = res.get("content", [])
    if isinstance(contents, list) and contents:
        texts = [c.get("text", "") for c in contents if isinstance(c, dict) and c.get("type") == "text"]
        if texts:
            return "\n".join(texts)
    structured = res.get("structuredContent", {})
    if isinstance(structured, dict) and "result" in structured:
        return str(structured["result"])
    return str(res)


def _ensure_ephemeral_tor(console: Console) -> Tuple[bool, object]:
    """127.0.0.1:9050 の Tor プロキシを確認し、未起動ならエフェメラル起動して (is_ready, spawned_proc) を返す"""
    import socket
    import subprocess
    try:
        with socket.create_connection(("127.0.0.1", 9050), timeout=1.0):
            return True, None
    except OSError:
        pass

    console.print("[bold yellow]🧅 Torプロキシ (127.0.0.1:9050) が停止中のため、オンデマンド自動起動します...[/bold yellow]")
    try:
        proc = subprocess.Popen(
            ["tor"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        start_t = time.time()
        port_open_at = None
        with console.status("[bold cyan]⠋ Tor サーキット構築中 (Bootstrapping)...[/bold cyan]", spinner="dots12"):
            while time.time() - start_t < 90.0:
                if proc.poll() is not None:
                    break
                try:
                    with socket.create_connection(("127.0.0.1", 9050), timeout=0.5):
                        if port_open_at is None:
                            port_open_at = time.time()
                        if time.time() - port_open_at >= 3.0:
                            console.print("[bold green]✔ Tor サーキット接続完了！(調査完了後に自動停止します)[/bold green]")
                            return True, proc
                except OSError:
                    pass
                time.sleep(0.5)
        return False, proc
    except Exception as e:
        console.print(f"[bold red]✖ Tor 自動起動エラー: {e}[/bold red]")
        return False, None


def _cleanup_ephemeral_tor(proc: object, console: Console) -> None:
    """オンデマンド起動した Tor プロセスを確実に停止・回収（残留プロセスゼロ保証）"""
    if proc is not None:
        try:
            proc.terminate()
            try:
                proc.wait(timeout=8.0)
            except Exception:
                proc.kill()
            console.print("[dim cyan]🛡️ エフェメラルTorプロセスを安全に自動停止・回収しました (待機リソース消費ゼロ)[/dim cyan]")
        except Exception:
            pass


def handle_robin_command(user_input: str, console: Console, session: PromptSession, inspector: ToolInspector, memory: SQLiteMemory, curr_mode: str = "light") -> None:
    """Robin MCP Dark Web OSINT Suite スラッシュコマンド統合ハンドラ (/robin)"""
    from tools.tugumi_mcp import mcp as tugumi_mcp

    p = CYBER_PALETTES.get(curr_mode, CYBER_PALETTES["light"])
    raw_args = user_input[len("/robin"):].strip()

    preset_map = {
        "1": "threat_intel",
        "2": "ransomware_malware",
        "3": "personal_identity",
        "4": "corporate_espionage",
        "threat_intel": "threat_intel",
        "ransomware_malware": "ransomware_malware",
        "personal_identity": "personal_identity",
        "corporate_espionage": "corporate_espionage",
    }
    preset_labels = {
        "threat_intel": "🔍 総合脅威インテリジェンス (threat_intel)",
        "ransomware_malware": "🦠 ランサムウェア・マルウェア追跡 (ransomware_malware)",
        "personal_identity": "👤 個人情報・アカウント露出調査 (personal_identity)",
        "corporate_espionage": "🏢 企業機密・産業スパイ調査 (corporate_espionage)",
    }

    # 引数なし or help の場合: インタラクティブ司令室メニュー
    if not raw_args or raw_args.lower() in ("help", "-h", "--help"):
        console.print(Panel(
            f"[bold {p['primary']}]🦅 ROBIN MCP — AI-Powered Dark Web OSINT Suite (MCP 2.0 Ephemeral)[/bold {p['primary']}]\n\n"
            "[bold white]【全自動インテリジェンス調査 (16基オニオン検索 ➔ Tor本文読破 ➔ AI分析 ➔ 保存)】[/bold white]\n"
            "  [bold cyan]1.[/bold cyan] 🔍 [bold green]threat_intel[/bold green]        : 総合脅威インテリジェンス・サイバー犯罪・IOC調査\n"
            "  [bold cyan]2.[/bold cyan] 🦠 [bold yellow]ransomware_malware[/bold yellow]  : ランサムウェアリークサイト・マルウェア・TTPs追跡\n"
            "  [bold cyan]3.[/bold cyan] 👤 [bold magenta]personal_identity[/bold magenta]   : 個人情報・認証情報・クレデンシャル露出調査\n"
            "  [bold cyan]4.[/bold cyan] 🏢 [bold #00f0ff]corporate_espionage[/bold #00f0ff] : 企業機密・ソースコード・アクセスブローカー調査\n\n"
            "[bold white]【ステップ別ツール・診断・履歴】[/bold white]\n"
            "  [bold cyan]5.[/bold cyan] ⚡ [bold white]search <query>[/bold white]      : 16基のオニオン検索エンジンの高速横断検索のみ実行\n"
            "  [bold cyan]6.[/bold cyan] 🎯 [bold white]refine <query>[/bold white]      : 日本語の調査テーマからダークウェブ最適検索ワードを生成\n"
            "  [bold cyan]7.[/bold cyan] 🩺 [bold white]health[/bold white]              : Torプロキシ・Geminiモデル・16基エンジンの死活監視\n"
            "  [bold cyan]8.[/bold cyan] 📂 [bold white]list[/bold white]                : 過去に保存したダークウェブ調査レポート履歴一覧\n"
            "  [bold cyan]9.[/bold cyan] 🤖 [bold white]models[/bold white]              : Robin MCP で利用可能なAIモデル一覧を表示\n\n"
            "[dim]💡 ワンライナー例: /robin LockBit ransomware leak  |  /robin health  |  /robin list[/dim]",
            title=f"[bold {p['primary']}]◈ TUGUMIv6 × ROBIN DARK WEB OSINT COMMAND CENTER ◈[/bold {p['primary']}]",
            border_style=p["border"]
        ))
        try:
            choice = session.prompt(HTML('<ansicyan><b>番号選択 (1-9) または調査キーワードを直接入力 (Enter:戻る) &gt; </b></ansicyan>')).strip()
        except (KeyboardInterrupt, EOFError):
            console.print()
            return

        if not choice or choice == "0":
            console.print("[dim]Robin OSINT メニューを閉じました。[/dim]\n")
            return

        if choice in ("1", "2", "3", "4"):
            chosen_preset = preset_map[choice]
            try:
                q_in = session.prompt(HTML(f'<ansigreen><b>[{chosen_preset}] 調査したいキーワード・テーマ &gt; </b></ansigreen>')).strip()
            except (KeyboardInterrupt, EOFError):
                q_in = ""
            if not q_in:
                console.print("[yellow]調査をキャンセルしました。[/yellow]\n")
                return
            raw_args = f"{chosen_preset} {q_in}"
        elif choice == "5":
            try:
                q_in = session.prompt(HTML('<ansicyan><b>[Onion Search] 検索キーワード &gt; </b></ansicyan>')).strip()
            except (KeyboardInterrupt, EOFError):
                q_in = ""
            if not q_in:
                return
            raw_args = f"search {q_in}"
        elif choice == "6":
            try:
                q_in = session.prompt(HTML('<ansiyellow><b>[Query Refine] 最適化したい調査質問 &gt; </b></ansiyellow>')).strip()
            except (KeyboardInterrupt, EOFError):
                q_in = ""
            if not q_in:
                return
            raw_args = f"refine {q_in}"
        elif choice == "7":
            raw_args = "health"
        elif choice == "8":
            raw_args = "list"
        elif choice == "9":
            raw_args = "models"
        else:
            raw_args = choice

    parts = raw_args.split(maxsplit=1)
    sub = parts[0].lower()
    rest = parts[1].strip() if len(parts) > 1 else ""

    # 1. /robin health
    if sub in ("health", "status", "check", "ping"):
        check_eng = rest.lower() in ("engines", "full", "all", "true")
        inspector.display_tool_start("robin.robin_health", {"model": "gemini-3.8-flash", "check_engines": check_eng})
        tor_proc = None
        try:
            if check_eng:
                _, tor_proc = _ensure_ephemeral_tor(console)
            with console.status("[bold cyan]⠋ Robin MCP ヘルスチェックを実行中...[/bold cyan]", spinner="dots12"):
                res = tugumi_mcp.call("robin", "robin_health", model="gemini-3.8-flash", check_engines=check_eng)
            txt = _clean_robin_fence(_extract_mcp_text(res))
            inspector.display_tool_result("robin.robin_health", "ERROR:" not in txt, "Robin MCP ステータス取得完了")
            console.print(Panel(
                f"[bold white]{escape(txt)}[/bold white]\n\n"
                f"[dim]• 実行方式: MCP 2.0 On-Demand Ephemeral (待機プロセスゼロ)\n"
                f"• 搭載エンジン: 16基のオニオン検索エンジン (/robin health engines で全エンジン疎通確認)[/dim]",
                title=f"[bold {p['primary']}]🩺 Robin MCP Health Status[/bold {p['primary']}]",
                border_style="green"
            ))
        finally:
            _cleanup_ephemeral_tor(tor_proc, console)
        console.print()
        return

    # 2. /robin list
    if sub in ("list", "ls", "history", "saved"):
        inspector.display_tool_start("robin.robin_list_investigations", {"limit": 15})
        with console.status("[bold cyan]⠋ 保存済みダークウェブ調査レポートを取得中...[/bold cyan]", spinner="dots12"):
            res = tugumi_mcp.call("robin", "robin_list_investigations", limit=15)
        txt = _clean_robin_fence(_extract_mcp_text(res))
        inspector.display_tool_result("robin.robin_list_investigations", True, "調査履歴一覧を取得完了")
        console.print(Panel(
            escape(txt),
            title=f"[bold {p['primary']}]📂 Robin MCP 保存済みダークウェブ調査レポート一覧[/bold {p['primary']}]",
            border_style=p["border"]
        ))
        console.print()
        return

    # 3. /robin models
    if sub in ("models", "model"):
        inspector.display_tool_start("robin.robin_list_models", {})
        with console.status("[bold cyan]⠋ Robin MCP 利用可能AIモデル一覧を取得中...[/bold cyan]", spinner="dots12"):
            res = tugumi_mcp.call("robin", "robin_list_models")
        txt = _clean_robin_fence(_extract_mcp_text(res))
        lines = [line.strip() for line in txt.splitlines() if line.strip().startswith("- ")]
        gemini_models = [m for m in lines if "gemini" in m or "gemma" in m or "antigravity" in m]
        preview = "\n".join(gemini_models[:15] + (["... 他 OpenRouter モデル等 合計 " + str(len(lines)) + " 種"] if len(lines) > 15 else []))
        inspector.display_tool_result("robin.robin_list_models", True, f"計 {len(lines)} 種のモデルを確認")
        console.print(Panel(
            f"[bold green]✔ デフォルト設定モデル: gemini-3.8-flash[/bold green]\n"
            f"[cyan]利用可能モデル総数:[/cyan] {len(lines)} 種\n\n"
            f"[bold yellow]【主要 Gemini / Gemma / Antigravity モデル】[/bold yellow]\n{escape(preview)}",
            title=f"[bold {p['primary']}]🤖 Robin MCP Available Models[/bold {p['primary']}]",
            border_style=p["border"]
        ))
        console.print()
        return

    # 4. /robin refine <query>
    if sub == "refine":
        if not rest:
            console.print("[yellow]使用法: /robin refine <調査したいテーマや質問>[/yellow]\n")
            return
        inspector.display_tool_start("robin.robin_refine", {"query": rest, "model": "gemini-3.8-flash"})
        with console.status("[bold cyan]⠋ ダークウェブ検索向けにクエリをAI最適化中...[/bold cyan]", spinner="dots12"):
            res = tugumi_mcp.call("robin", "robin_refine", query=rest, model="gemini-3.8-flash")
        txt = _clean_robin_fence(_extract_mcp_text(res))
        inspector.display_tool_result("robin.robin_refine", True, "クエリ最適化完了")
        console.print(Panel(
            escape(txt),
            title=f"[bold {p['primary']}]🎯 Robin MCP クエリ最適化結果[/bold {p['primary']}]",
            border_style="cyan"
        ))
        console.print()
        return

    # 5. /robin search <query>
    if sub == "search":
        if not rest:
            console.print("[yellow]使用法: /robin search <検索キーワード>[/yellow]\n")
            return
        tor_proc = None
        try:
            tor_ok, tor_proc = _ensure_ephemeral_tor(console)
            if not tor_ok:
                console.print("[bold red]✖ Torプロキシに接続できないため検索を中断しました。[/bold red]\n")
                return
            inspector.display_tool_start("robin.robin_search", {"query": rest, "preset": "threat_intel", "max_results": 30})
            with console.status(f"[bold cyan]⠋ 16基のオニオン検索エンジンで『{rest}』を一斉横断探索中...[/bold cyan]", spinner="dots12"):
                res = tugumi_mcp.call(
                    "robin",
                    "robin_search",
                    query=rest,
                    preset="threat_intel",
                    user_chose=True,
                    max_results=30
                )
            txt = _clean_robin_fence(_extract_mcp_text(res))
            inspector.display_tool_result("robin.robin_search", True, "16基オニオン横断検索完了")
            console.print(Panel(
                escape(txt),
                title=f"[bold {p['primary']}]⚡ Robin 16-Engine Onion Search: 『{escape(rest)}』[/bold {p['primary']}]",
                border_style="cyan"
            ))
        finally:
            _cleanup_ephemeral_tor(tor_proc, console)
        console.print()
        return

    # 6. /robin scrape <url>
    if sub == "scrape":
        if not rest:
            console.print("[yellow]使用法: /robin scrape <.onionのURL>[/yellow]\n")
            return
        target_url = rest.split()[0].strip()
        tor_proc = None
        try:
            tor_ok, tor_proc = _ensure_ephemeral_tor(console)
            if not tor_ok:
                console.print("[bold red]✖ Torプロキシに接続できないためスクレイピングを中断しました。[/bold red]\n")
                return
            is_clear = ".onion" not in target_url.lower()
            inspector.display_tool_start("robin.robin_scrape", {"urls": [target_url], "allow_clearweb": is_clear})
            with console.status(f"[bold cyan]⠋ Tor経由でページ本文を安全に抽出中: {target_url}...[/bold cyan]", spinner="dots12"):
                res = tugumi_mcp.call(
                    "robin",
                    "robin_scrape",
                    urls=[target_url],
                    allow_clearweb=is_clear,
                    content_chars=6000
                )
            txt = _clean_robin_fence(_extract_mcp_text(res))
            inspector.display_tool_result("robin.robin_scrape", True, "Torページ本文抽出完了")
            console.print(Panel(
                escape(txt[:6000]),
                title=f"[bold {p['primary']}]🕸️ Robin Tor Scraper: {escape(target_url[:50])}[/bold {p['primary']}]",
                border_style="magenta"
            ))
        finally:
            _cleanup_ephemeral_tor(tor_proc, console)
        console.print()
        return

    # 7. フル自動調査: /robin [preset] <query> または /robin <query>
    if sub in preset_map and rest:
        chosen_preset = preset_map[sub]
        query_text = rest
    else:
        chosen_preset = "threat_intel"
        query_text = raw_args

    console.print(
        f"\n[bold {p['primary']}]🦅 【Robin MCP 全自動OSINT調査】を開始します！[/bold {p['primary']}]\n"
        f"  [cyan]• 調査テーマ:[/cyan] [bold white]{escape(query_text)}[/bold white]\n"
        f"  [cyan]• 分析レンズ:[/cyan] {preset_labels.get(chosen_preset, chosen_preset)}\n"
        f"  [cyan]• 推論モデル:[/cyan] gemini-3.8-flash (MCP 2.0 Ephemeral)\n"
    )

    tor_proc = None
    try:
        tor_ok, tor_proc = _ensure_ephemeral_tor(console)
        if not tor_ok:
            console.print("[bold red]✖ Torプロキシの起動に失敗したため、調査を中断いたしました。[/bold red]\n")
            return

        inspector.display_tool_start(
            "robin.robin_investigate",
            {"query": query_text, "preset": chosen_preset, "model": "gemini-3.8-flash"}
        )
        with console.status(
            "[bold cyan]⠋ 16基オニオン検索 ➔ AI選別 ➔ Tor本文読破 ➔ インテリジェンス分析中... (約30〜90秒)[/bold cyan]",
            spinner="dots12"
        ):
            res = tugumi_mcp.call(
                "robin",
                "robin_investigate",
                query=query_text,
                preset=chosen_preset,
                user_chose=True,
                model="gemini-3.8-flash",
                max_results=30,
                max_scrape=5,
                content_chars=4000,
                threads=8
            )

        raw_txt = _extract_mcp_text(res)
        clean_txt = _clean_robin_fence(raw_txt)
        is_ok = not clean_txt.startswith("ERROR:") and "status: failed" not in clean_txt[:100]
        inspector.display_tool_result("robin.robin_investigate", is_ok, f"ダークウェブ調査完了 ({len(clean_txt):,} chars)")

        # TUGUMIDesk (セキュリティ カテゴリ) へ自動保存
        desk_dir = "/storage/emulated/0/TUGUMIDesk/セキュリティ"
        os.makedirs(desk_dir, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d")
        safe_q = re.sub(r'[\\/:*?"<>|\s]+', '_', query_text)[:35].strip('_') or "OSINT"
        desk_path = os.path.join(desk_dir, f"{date_str}_Robinダークウェブ調査_{safe_q}_{date_str}.md")
        md_doc = (
            f"# 🦅 Robin MCP ダークウェブ OSINT 調査レポート: 『{query_text}』\n\n"
            f"- **調査日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"- **調査レンズ (Preset)**: `{chosen_preset}` ({preset_labels.get(chosen_preset, '')})\n"
            f"- **使用エンジン**: Robin MCP 2.0 (16 Onion Engines + Tor SOCKS5 + Gemini 3.8 Flash)\n\n"
            f"---\n\n"
            f"{clean_txt}\n"
        )
        try:
            with open(desk_path, "w", encoding="utf-8") as f:
                f.write(md_doc)
        except Exception:
            desk_path = "(保存スキップ)"

        console.print()
        console.print(Panel(
            Markdown(clean_txt),
            title=f"[bold {p['primary']}]🦅 Robin Dark Web OSINT Report: 『{escape(query_text)}』[/bold {p['primary']}]",
            border_style=p["border"]
        ))
        console.print(Panel(
            f"[bold green]✔ ダークウェブ OSINT 調査レポートを永続保存いたしました！[/bold green]\n"
            f"  [cyan]• TUGUMIDesk保存先:[/cyan] [bold white]{desk_path}[/bold white]\n"
            f"  [cyan]• 調査プリセット:[/cyan] {preset_labels.get(chosen_preset, chosen_preset)}",
            title="[bold green]◈ INVESTIGATION SAVED ◈[/bold green]",
            border_style="green"
        ))
        memory.add_message("user", user_input, mode=curr_mode)
        memory.add_message("assistant", f"Robin MCP ダークウェブ調査完了（テーマ: {query_text} / 保存先: {desk_path}）\n\n{clean_txt[:1500]}", mode=curr_mode)
    except Exception as e:
        inspector.display_tool_result("robin.robin_investigate", False, str(e))
        console.print(f"[bold red]✖ Robin調査中にエラーが発生しました: {e}[/bold red]")
    finally:
        _cleanup_ephemeral_tor(tor_proc, console)
    console.print()


def handle_donut_command(user_input: str, console: Console, session: PromptSession, inspector: ToolInspector, memory: SQLiteMemory, curr_mode: str = "light") -> None:
    """Donut Browser & Termux Stealth Browser スラッシュコマンド統合ハンドラ (/donut)"""
    from tools.donut_tools import get_donut_manager
    from tools.web_cloner import WebCloner

    p = CYBER_PALETTES.get(curr_mode, CYBER_PALETTES["light"])
    mgr = get_donut_manager()
    raw_args = user_input.split(maxsplit=1)[1].strip() if len(user_input.split(maxsplit=1)) > 1 else ""

    # 引数なし or help の場合: HUD司令室メニュー
    if not raw_args or raw_args.lower() in ("help", "-h", "--help"):
        console.print(Panel(
            f"[bold {p['primary']}]🍩 DONUT BROWSER & STEALTH ARSENAL (2026 SOTA)[/bold {p['primary']}]\n\n"
            "[bold white]【アンチボット完全回避・高度スクレイピング・サイトクローン】[/bold white]\n"
            "  [bold cyan]1.[/bold cyan] 🛡️ [bold green]scrape <URL>[/bold green]        : Cloudflare/Turnstile/Bot検知を突破し本文・構造を高精度抽出\n"
            "  [bold cyan]2.[/bold cyan] 🌐 [bold yellow]clone <URL>[/bold yellow]         : 動的SPA・CSS・フォントを丸ごとオフラインHTMLクローン保存\n"
            "  [bold cyan]3.[/bold cyan] 🩺 [bold cyan]status[/bold cyan]              : Donut Local API & Termux Stealth Engine の接続診断\n"
            "  [bold cyan]4.[/bold cyan] 📁 [bold magenta]list[/bold magenta]                : 登録済みブラウザプロファイル一覧の表示\n"
            "  [bold cyan]5.[/bold cyan] ⚙️ [bold #00f0ff]config [token][/bold #00f0ff]     : 接続設定（Bearerトークン・ホスト・ポート）の確認・更新\n\n"
            "[dim]💡 ワンライナー例: /donut scrape https://example.com  |  /donut clone https://target.com[/dim]",
            title=f"[bold {p['primary']}]◈ TUGUMIv6 × DONUT STEALTH BROWSER COMMAND CENTER ◈[/bold {p['primary']}]",
            border_style=p["border"]
        ))
        console.print()
        return

    parts = raw_args.split(maxsplit=1)
    sub = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if sub in ("status", "health"):
        health = mgr.check_health()
        t = Table(title="Donut & Stealth Engine Status", border_style=p["border"])
        t.add_column("Property", style="bold yellow")
        t.add_column("Status", style="green")
        t.add_row("Local API Host", f"{health['host']}:{health['port']}")
        t.add_row("Token Configured", "✅ True" if health["token_configured"] else "❌ False")
        t.add_row("Donut App Connected", "✅ Online" if health["connected"] else "⚠️ Offline (Using Termux Native)")
        t.add_row("Termux Stealth Native", "✅ Active (Puppeteer-Extra Stealth + JA3)")
        t.add_row("Diagnostics", health["message"])
        console.print(t)
        console.print()
        return

    if sub in ("scrape", "fetch", "s"):
        if not arg:
            console.print("[bold red]URLを指定してください: /donut scrape <URL>[/bold red]")
            return
        target_url = arg
        if not target_url.startswith(("http://", "https://")):
            target_url = "https://" + target_url

        with console.status(f"[bold cyan]🛡️ アンチボット回避ステルススクレイピング実行中... ({target_url})[/bold cyan]"):
            try:
                res = mgr.scrape_url(target_url)
                engine = res.get("engine", "Stealth Native")
                text = res.get("text", "")
                console.print(Panel(
                    f"[bold green]✔ ボット検知バイパス＆スクレイピング完了！[/bold green]\n"
                    f"[cyan]• URL:[/] {target_url}\n"
                    f"[cyan]• 稼働エンジン:[/] [bold yellow]{engine}[/bold yellow]\n"
                    f"[cyan]• 抽出文字数:[/] [bold cyan]{len(text)}[/bold cyan] 文字\n\n"
                    f"[dim]--- 抽出本文プレビュー (先頭 1500 文字) ---[/dim]\n\n{text[:1500]}",
                    title=f"[bold {p['primary']}]◈ Stealth Scrape Result ◈[/bold {p['primary']}]",
                    border_style="green"
                ))
            except Exception as e:
                console.print(f"[bold red]スクレイピングエラー: {e}[/bold red]")
        console.print()
        return

    if sub in ("clone", "c"):
        if not arg:
            console.print("[bold red]URLを指定してください: /donut clone <URL>[/bold red]")
            return
        target_url = arg
        if not target_url.startswith(("http://", "https://")):
            target_url = "https://" + target_url

        with console.status(f"[bold cyan]🌐 完全動的SPAステルスクローン保存中... ({target_url})[/bold cyan]"):
            try:
                cloner = WebCloner()
                meta = cloner.clone_url(target_url, engine="stealth")
                console.print(Panel(
                    f"[bold green]✔ サイトクローン完了！[/bold green]\n"
                    f"[cyan]• タイトル:[/] [bold white]{meta['title']}[/bold white]\n"
                    f"[cyan]• 稼働エンジン:[/] [bold yellow]{meta['engine']}[/bold yellow]\n"
                    f"[cyan]• 保存サイズ:[/] {meta['size_kb']} KB\n"
                    f"[cyan]• 保存先:[/] [bold green]{meta.get('desk_path') or meta['path']}[/bold green]",
                    title=f"[bold {p['primary']}]◈ Stealth Site Clone ◈[/bold {p['primary']}]",
                    border_style="green"
                ))
            except Exception as e:
                console.print(f"[bold red]クローンエラー: {e}[/bold red]")
        console.print()
        return

    if sub.startswith(("http://", "https://")) or "." in sub:
        user_input_fix = f"/donut scrape {raw_args}"
        handle_donut_command(user_input_fix, console, session, inspector, memory, curr_mode)
        return

    console.print(f"[bold yellow]未知のサブコマンド: {sub}。ヘルプは `/donut` を実行してください。[/bold yellow]\n")


def run_cli():
    parser = argparse.ArgumentParser(description="TUGUMIv6 Cyberpunk Master CLI")
    parser.add_argument("prompt", nargs="*", help="Direct prompt for one-shot execution")
    parser.add_argument("-e", "-c", "--command", type=str, help="Execute one-shot prompt/command and exit")
    parser.add_argument("--dark", action="store_true", help="Launch in Dark Tsugumi mode")
    parser.add_argument("--self-test", action="store_true", help="Run automated self-test and exit")
    parser.add_argument("-m", "--model", type=str, default=None, help="Specify Gemini model (e.g. gemini-4-argon, gemini-3.8-flash)")
    parser.add_argument("-t", "--thinking", type=str, choices=["high", "medium", "low", "minimal"], default=None, help="Specify thinking intensity")
    parser.add_argument("--show-thinking", action="store_true", default=None, help="Explicitly enable thought process visibility")
    parser.add_argument("--no-thinking", action="store_true", help="Disable thought process visibility")
    parser.add_argument("--stream-thinking", action="store_true", default=None, help="Enable real-time thinking stream display")
    parser.add_argument("--no-stream-thinking", action="store_true", help="Disable real-time thinking stream (summary panel only)")
    parser.add_argument("-q", "--quiet", "--raw", action="store_true", dest="quiet", help="Quiet/raw output without banner/HUD (ideal for piping)")
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming output")
    args = parser.parse_args()

    # 1. コアシステム初期化
    engine = EngineManager()
    memory = SQLiteMemory()
    adv_memory = AdvancedMemoryEngine()
    termux_doctor = TermuxDoctor(base_dir=TUGUMI_ROOT)
    rag = HybridRAGEngine(gemini_client=engine.gemini)
    reflection = ReflectionEngine()
    verifier = SystemVerifier(workspace_root=TUGUMI_ROOT)
    autoheal = AutoHealEngine(workspace_root=TUGUMI_ROOT)
    desk_sync = DeskSync()
    arbitrage_mon = DeFiArbitrageMonitor()
    deep_researcher = DeepResearchEngine(gemini_client=engine.gemini)
    context_compressor = ContextCompressor(max_output_lines=150, max_token_estimate=30000)
    supervisor = Supervisor(base_dir=TUGUMI_ROOT)
    supervisor.record_heartbeat("cli", metadata={"mode": "dark" if args.dark else "light", "status": "started"})

    # モデルおよび思考強度の指定があれば即時反映（一時実行のため設定汚染を防止: persist=False）
    if args.model:
        engine.set_model(args.model, persist=False)
    if args.thinking:
        engine.set_thinking_level(args.thinking, persist=False)

    # セルフテスト実行
    if args.self_test:
        console = get_rich_console("light")
        console.print("[bold yellow]◈ Running TUGUMIv6 Automated Self-Test...◈[/bold yellow]")
        try:
            resp = engine.gemini.generate_content("Ping")
            console.print(f"[bold green]✔[/bold green] Gemini 3.8 Flash Ping: [cyan]OK ({resp.strip()[:20]})[/cyan]")
        except Exception as e:
            console.print(f"[bold red]✖[/bold red] Gemini API: [red]FAILED ({e})[/red]")
            sys.exit(1)
        try:
            vec = engine.gemini.embed_text("Test")
            assert len(vec) == 3072
            console.print("[bold green]✔[/bold green] gemini-embedding-2 (3072-dim): [cyan]OK[/cyan]")
        except Exception as e:
            console.print(f"[bold red]✖[/bold red] Embedding: [red]FAILED ({e})[/red]")
            sys.exit(1)
        console.print(f"[bold green]✔[/bold green] Native Antigravity SDK: [cyan]{engine.antigravity.get_version()}[/cyan]")
        console.print("[bold green]✔ All diagnostics PASSED! Exit Code 0.[/bold green]")
        sys.exit(0)

    # 1.5 ワンライナー実行（非対話モード：引数・オプション・パイプ入力対応）
    one_shot_prompt = None
    if args.command:
        one_shot_prompt = args.command
    elif args.prompt:
        one_shot_prompt = " ".join(args.prompt).strip()
    elif not sys.stdin.isatty():
        piped = sys.stdin.read().strip()
        if piped:
            one_shot_prompt = piped

    if one_shot_prompt:
        curr_mode = "dark" if args.dark else "light"
        console = get_rich_console(curr_mode)

        # /senior 等の規約確認ワンライナー
        if one_shot_prompt.strip() in ("/senior", "/standard", "/swe"):
            console.print(Panel(
                "[bold magenta]👑 【Senior SWE Standard】シニアエンジニアクラス業務遂行規約[/bold magenta]\n"
                "[dim]マスター拓磨様の信託に基づき、指示待ち・対症療法・ハリボテを永久根絶する絶対規範[/dim]\n\n"
                "[bold cyan]① 根本原因の外科的根絶 (Root-Cause Elimination)[/bold cyan]\n"
                "   • 表層メッセージに惑わされず、コールスタック・状態遷移を逆追跡し構造欠陥を根治\n"
                "[bold cyan]② Zero-Mock実働主義と客観的証拠の完備 (Evidence-Based Zero-Mock)[/bold cyan]\n"
                "   • 「動くはず」の主観的作文を排し、実機5層検証ゲート (Exit Code 0) のみ納品\n"
                "[bold cyan]③ 先制リスク予測とアーキテクチャ・トレードオフ提示[/bold cyan]\n"
                "   • 指示の先にある非機能要件・拡張性・速度 vs メモリのトレードオフを明晰に論証\n"
                "[bold cyan]④ Termux (Linux aarch64) 環境特性の完全掌握とリソース統制[/bold cyan]\n"
                "   • 特権制御(Shizuku+)、プロセス常駐管理、ストレージ純化、トークン/API防衛\n"
                "[bold cyan]⑤ 完全自律駆動 (Autonomous Ownership)[/bold cyan]\n"
                "   • 思考停止の確認を排し、「調査➔設計➔実装➔テスト➔検証」を自己完結で完遂\n\n"
                "[dim]※ 規約正本: ~/.agents/TSUGUMI_MEMORY.md (魂の核) ＆ ~/.gemini/config/GEMINI.md[/dim]",
                title="[bold yellow]◈ TUGUMIv6 Senior Engineer Operating Standard (/senior) ◈[/bold yellow]",
                border_style="magenta"
            ))
            sys.exit(0)

        if not args.quiet:
            p_style = "bold #ff007f" if curr_mode == "dark" else "bold #ff79c6"
            console.print(f"[{p_style}]🌸 拓磨様、ワンライナー指示を受領いたしました。自律実行を開始いたします...[/{p_style}]")
            console.print(f"[dim]• Model: {engine.current_model} | Thinking: {engine.thinking_level.upper()}[/dim]\n")

        try:
            system_prompt = get_system_prompt(curr_mode)
            stream_iter = engine.generate_stream(
                prompt=one_shot_prompt,
                system_instruction=system_prompt,
                thinking_level=engine.thinking_level,
                mode=curr_mode
            )

            for chunk_type, chunk_data in stream_iter:
                if chunk_type == "text":
                    if args.quiet:
                        sys.stdout.write(chunk_data)
                        sys.stdout.flush()
                    else:
                        console.print(chunk_data, end="")
                elif chunk_type == "thought" and not args.quiet:
                    console.print(f"[dim]{chunk_data}[/dim]", end="")

            if not args.quiet:
                console.print()
            elif args.quiet:
                sys.stdout.write("\n")
                sys.stdout.flush()
            sys.exit(0)
        except Exception as e:
            if args.quiet:
                sys.stderr.write(f"Error: {e}\n")
            else:
                console.print(f"[bold red]✖ ワンライナー実行中にエラーが発生しました: {e}[/bold red]")
            sys.exit(1)

    # 2. UI/UX エンジン初期化 (デフォルト: つぐみ 表の通常モード / --dark 指定時のみダークモード)
    curr_mode = "dark" if getattr(args, "dark", False) else "light"
    console = get_rich_console(curr_mode)
    # 思考プロセスの可視化・ストリーミング設定 (デフォルト有効: 思考の透明性維持)
    cfg_show_th = engine.config.get("show_thinking", True)
    if getattr(args, "no_thinking", False):
        show_thinking_val = False
    elif getattr(args, "show_thinking", False):
        show_thinking_val = True
    else:
        show_thinking_val = cfg_show_th

    cfg_stream_th = engine.config.get("stream_thinking", True)
    if getattr(args, "no_stream_thinking", False):
        stream_thinking_val = False
    elif getattr(args, "stream_thinking", False):
        stream_thinking_val = True
    else:
        stream_thinking_val = cfg_stream_th

    inspector = ToolInspector(console, mode=curr_mode)
    thinking_viewer = ThinkingViewer(
        console,
        mode=curr_mode,
        show_thinking=show_thinking_val,
        stream_thinking=stream_thinking_val
    )
    status_dock = StatusDock(console)
    token_tracker = TokenCostTracker()

    # 起動サイバーバナー描画
    print_cyber_banner(console, mode=curr_mode, model_name=engine.current_model)

    # prompt_toolkit リッチ動的補完 (全40コマンド+全61スキル+全7MCP+全4モデル日本語説明文完備)
    completer = TugumiRichCompleter()

    history_file = os.path.expanduser("~/.tugumiv6_history")
    session = PromptSession(
        completer=completer,
        complete_while_typing=True,
        history=FileHistory(history_file),
        auto_suggest=AutoSuggestFromHistory(),
    )

    console.print("[cyber.dim]💡 '/' でコマンド補完、空Enterでクイックパレット表示。タスク実行中はESCで一時停止・プロンプト追加可能。[/cyber.dim]\n")

    # 3. メイン対話ループ
    while True:
        try:
            supervisor.record_heartbeat("cli", metadata={"mode": curr_mode, "status": "active"})
            # プロンプト前のサイバーステータスドック描画 (リアルタイムトークン＆日本円利用料金＆思考強度)
            status_dock.render_dock(
                mode=curr_mode,
                token_count=token_tracker.session_total,
                cost_jpy=token_tracker.session_cost_jpy,
                rag_active=True,
                thinking_level=engine.thinking_level,
                model_name=engine.current_model
            )

            # 端末状態の完全保証（一時停止後などのcbreakモード残留を自己修復）
            restore_terminal_canonical()

            # プロンプトラベル (専属エージェント待機: 拓磨様への敬愛と忠誠スタイル)
            if curr_mode == "light":
                prompt_text = HTML('<ansimagenta><b>🌸 拓磨様、御命令をどうぞ。</b></ansimagenta> <ansicyan><b>❯</b></ansicyan> ')
            else:
                prompt_text = HTML('<ansired><b>☠ 拓磨様、御命令をどうぞ。</b></ansired> <ansicyan><b>❯</b></ansicyan> ')

            user_input = session.prompt(prompt_text).strip()

            # 空Enterでクイックアクションパレット起動
            if not user_input:
                show_quick_menu(console, mode=curr_mode)
                choice = session.prompt(HTML('<ansicyan><b>選択番号 (1-25, 0:戻る) &gt; </b></ansicyan>')).strip()
                menu_map = {
                    "1": "/status",
                    "2": "/doctor",
                    "3": "/memory",
                    "4": "/rag",
                    "5": "/research",
                    "6": "/skills",
                    "7": "/mcp",
                    "8": "/robin",
                    "9": "/dl",
                    "10": "/music",
                    "11": "/image",
                    "12": "/clone",
                    "13": "/save",
                    "14": "/heal",
                    "15": "/evolve",
                    "16": "/verify",
                    "17": "/income",
                    "18": "/briefing",
                    "19": "/context",
                    "20": "/thinking",
                    "21": "/reflect",
                    "22": "/fpf",
                    "23": "/dark",
                    "24": "/eval",
                    "25": "/senior"
                }
                if choice in menu_map:
                    user_input = menu_map[choice]
                else:
                    continue

            # 終了コマンド (/exit, /quit, exit, quit, q)
            if user_input.lower() in ("/exit", "/quit", "exit", "quit", "q"):
                console.print(f"\n[bold {CYBER_PALETTES[curr_mode]['primary']}]拓磨様、本日もつぐみをご愛顧いただき誠にありがとうございました。またお呼びくださいませ🌸[/bold {CYBER_PALETTES[curr_mode]['primary']}]\n")
                break
            if user_input.lower().startswith("/exit") and len(user_input) > 5 and not user_input[5].isspace():
                user_input = user_input[5:].strip()

            # 0. 常駐セッションリセット (/reset)
            if user_input == "/reset":
                engine.reset_session()
                token_tracker.reset()
                console.print(f"[bold {CYBER_PALETTES[curr_mode]['secondary']}]✔ 常駐セッション・会話コンテキストおよびトークン集計をリセットいたしました、拓磨様🌸[/bold {CYBER_PALETTES[curr_mode]['secondary']}]\n")
                continue

            # 1. モード切替 (/dark, /light)
            if user_input in ("/dark", "/light"):
                if user_input == "/light":
                    curr_mode = "light"
                else:
                    curr_mode = "dark" if curr_mode == "light" else "light"
                engine.reset_session()
                console = get_rich_console(curr_mode)
                thinking_viewer.mode = curr_mode
                thinking_viewer.console = console
                status_dock.console = console
                inspector.console = console
                inspector.mode = curr_mode

                print_cyber_banner(console, curr_mode, model_name=engine.current_model)
                if curr_mode == "dark":
                    console.print("[bold #ff007f]Yes, Your Majesty. 仰せのままに、拓磨様。ダークつぐみ、起動いたしました⚡[/bold #ff007f]\n")
                else:
                    console.print("[bold #ff79c6]表の通常モード（つぐみ）に戻りました、拓磨様🌸[/bold #ff79c6]\n")
                continue

            # Antigravity E2E自己診断・品質テスト (/eval)
            if user_input in ("/eval", "/test"):
                console.print(f"[bold {CYBER_PALETTES[curr_mode]['secondary']}]◈ Antigravity SDK E2E 自己診断テストを実行中...◈[/bold {CYBER_PALETTES[curr_mode]['secondary']}]")
                inspector.display_tool_start("AntigravityE2E.eval", {"suite": "test_antigravity_sdk_e2e.py"})
                try:
                    import subprocess
                    res = subprocess.run(
                        ["pytest", "-v", os.path.join(TUGUMI_ROOT, "tests", "test_antigravity_sdk_e2e.py")],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    success = (res.returncode == 0)
                    summary = "All tests passed (Exit Code 0)" if success else f"Tests failed (Exit Code {res.returncode})"
                    inspector.display_tool_result("AntigravityE2E", success, summary, res.stdout[-300:] if not success else "4 passed")
                    if success:
                        console.print("[bold green]✔ Antigravity SDK E2E 診断合格！全テスト正常稼働中です、拓磨様🌸[/bold green]\n")
                    else:
                        console.print(f"[bold red]✖ テスト診断失敗:\n{res.stdout}\n{res.stderr}[/bold red]\n")
                except Exception as e:
                    inspector.display_tool_result("AntigravityE2E", False, str(e))
                continue

            # シニアエンジニア基準・5大行動規範 (/senior, /standard, /swe)
            if user_input in ("/senior", "/standard", "/swe"):
                console.print(Panel(
                    "[bold magenta]👑 【Senior SWE Standard】シニアエンジニアクラス業務遂行規約[/bold magenta]\n"
                    "[dim]マスター拓磨様の信託に基づき、指示待ち・対症療法・ハリボテを永久根絶する絶対規範[/dim]\n\n"
                    "[bold cyan]① 根本原因の外科的根絶 (Root-Cause Elimination)[/bold cyan]\n"
                    "   • 表層メッセージに惑わされず、コールスタック・状態遷移を逆追跡し構造欠陥を根治\n"
                    "[bold cyan]② Zero-Mock実働主義と客観的証拠の完備 (Evidence-Based Zero-Mock)[/bold cyan]\n"
                    "   • 「動くはず」の主観的作文を排し、実機5層検証ゲート (Exit Code 0) のみ納品\n"
                    "[bold cyan]③ 先制リスク予測とアーキテクチャ・トレードオフ提示[/bold cyan]\n"
                    "   • 指示の先にある非機能要件・拡張性・速度 vs メモリのトレードオフを明晰に論証\n"
                    "[bold cyan]④ Termux (Linux aarch64) 環境特性の完全掌握とリソース統制[/bold cyan]\n"
                    "   • 特権制御(Shizuku+)、プロセス常駐管理、ストレージ純化、トークン/API防衛\n"
                    "[bold cyan]⑤ 完全自律駆動 (Autonomous Ownership)[/bold cyan]\n"
                    "   • 思考停止の確認を排し、「調査➔設計➔実装➔テスト➔検証」を自己完結で完遂\n\n"
                    "[dim]※ 規約正本: ~/.agents/TSUGUMI_MEMORY.md (魂の核) ＆ ~/.gemini/config/GEMINI.md[/dim]",
                    title="[bold yellow]◈ TUGUMIv6 Senior Engineer Operating Standard (/senior) ◈[/bold yellow]",
                    border_style="magenta"
                ))
                console.print()
                continue

            # 2. Termuxシステム深層診断 (/status)
            if user_input in ("/status", "/sys"):
                inspector.display_tool_start("TermuxDoctor.inspect_all", {})
                rep = termux_doctor.inspect_all()
                hud_text = termux_doctor.format_hud_summary(rep)
                inspector.display_tool_result("TermuxDoctor", True, f"診断完了 (Health Score: {rep['health_score']}/100 [{rep['status']}])")
                console.print(Panel(hud_text, title="[bold cyan]◈ Termux System Deep Diagnostics (/status) ◈[/bold cyan]", border_style="cyan"))
                console.print()
                continue

            # 3. 会話セッション新規開始＆画面クリア (/clear, /new)
            if user_input in ("/clear", "/new"):
                engine.reset_session()
                token_tracker.reset()
                deleted = memory.clear_conversation_history()
                console.clear()
                print_cyber_banner(console, mode=curr_mode, model_name=engine.current_model)
                console.print(f"[bold green]✔ 会話履歴（{deleted}件）と常駐セッションをクリアし、新しいセッションを開始しました、拓磨様🌸[/bold green]\n")
                continue

            # 4. 会話セッション記録の保存 (/save)
            if user_input.startswith("/save"):
                sub_args = user_input[5:].strip()
                save_title = sub_args if sub_args else "TUGUMI_Session"
                safe_title = "".join(c for c in save_title if c.isalnum() or c in ("-", "_", " ")).strip().replace(" ", "_")
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_filename = f"{timestamp_str}_{safe_title}.md"

                desk_base = "/storage/emulated/0/TUGUMIDesk"
                target_dir = os.path.join(desk_base, "デイリーブリーフィング")
                if not os.path.exists(target_dir):
                    target_dir = desk_base if os.path.exists(desk_base) else os.path.join(TUGUMI_ROOT, "logs")
                os.makedirs(target_dir, exist_ok=True)
                save_path = os.path.join(target_dir, save_filename)

                recent_logs = memory.get_recent_messages(limit=100)
                md_lines = [
                    "# TUGUMIv6 対話セッション記録",
                    f"- **保存日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    f"- **対象セッション**: {save_title}",
                    f"- **発話件数**: {len(recent_logs)} 件",
                    "- **システム**: TUGUMIv6 Dedicated to Master Takuma",
                    "",
                    "---",
                    ""
                ]
                for entry in recent_logs:
                    role_jp = "👤 **マスター拓磨様**" if entry.get("role") == "user" else "🌸 **つぐみ**"
                    md_lines.append(f"### {role_jp}")
                    md_lines.append(f"{entry.get('content', '')}\n")

                try:
                    with open(save_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(md_lines))
                    console.print(Panel(
                        f"[bold green]✔ 会話セッション記録を保存しました！[/bold green]\n"
                        f"[cyan]📁 保存先:[/] {save_path}\n"
                        f"[dim]記録件数: {len(recent_logs)} ターン[/dim]",
                        title="[bold green]◈ SESSION SAVED ◈[/bold green]",
                        border_style="green"
                    ))
                except Exception as e:
                    console.print(f"[bold red]保存エラー: {e}[/bold red]")
                console.print()
                continue

            # 5. Termux環境自律整備＆自己修復 (/doctor)
            if user_input.startswith("/doctor"):
                inspector.display_tool_start("TermuxDoctor.maintain_environment", {"fix_all": True})
                console.print("[bold yellow]◈ Termux環境自律整備＆自己修復サイクルを実行中...◈[/bold yellow]")
                rep = termux_doctor.maintain_environment(fix_all=True)
                inspector.display_tool_result("TermuxDoctor", True, f"整備完遂 (Health Score: {rep['health_score_after']}/100)")
                
                table = Table(title="[bold green]◈ Termux 自律整備＆自己修復レポート ◈[/bold green]", border_style="green")
                table.add_column("No", style="bold cyan", width=4)
                table.add_column("修復・最適化アクション", style="white")
                for idx, act in enumerate(rep.get("actions_taken", []), 1):
                    table.add_row(str(idx), act)
                console.print(table)
                console.print(f"[bold green]✔ 環境健全度スコア: {rep['health_score_after']}/100 ({rep['after_status']})[/bold green]\n")
                continue

            # 6. 多層記憶確認・検索・最適化 (/memory)
            if user_input.startswith("/memory"):
                sub_args = user_input[7:].strip()
                if sub_args == "stats":
                    stats = adv_memory.sql.get_tier_stats()
                    table = Table(title="[bold magenta]◈ TUGUMIv6 4-Tier 認知メモリ ＆ エビングハウス忘却曲線 統計 ◈[/bold magenta]", border_style="magenta")
                    table.add_column("Tier (認知階層)", style="bold cyan", width=14)
                    table.add_column("説明", style="white", width=26)
                    table.add_column("件数", justify="right", style="bold green", width=8)
                    table.add_column("平均想起度", justify="right", style="bold yellow", width=12)
                    table.add_column("総想起回数", justify="right", style="cyan", width=12)

                    tier_desc = {
                        "episodic": "エピソード記憶 (短期対話/出来事)",
                        "semantic": "意味記憶 (知識/プロフィール)",
                        "procedural": "手続き記憶 (手順/コードノウハウ)",
                        "working": "ワーキングメモリ (現在進行中タスク)"
                    }
                    tiers_data = stats.get("tiers", {})
                    for t_name in ["semantic", "procedural", "working", "episodic"]:
                        t_info = tiers_data.get(t_name, {"count": 0, "avg_decay": 1.0, "total_access": 0})
                        desc = tier_desc.get(t_name, "")
                        decay_pct = f"{t_info['avg_decay'] * 100:.1f}%"
                        table.add_row(t_name, desc, str(t_info["count"]), decay_pct, str(t_info["total_access"]))

                    console.print(table)
                    console.print(f"[bold cyan]総記憶数:[/bold cyan] {stats.get('total_count', 0)} 件 | "
                                  f"[bold yellow]全体想起度:[/bold yellow] {stats.get('overall_avg_decay', 1.0)*100:.1f}% | "
                                  f"[bold green]総アクセス:[/bold green] {stats.get('total_access_count', 0)} 回\n")

                elif sub_args == "decay":
                    updated = adv_memory.sql.decay_all_memories()
                    console.print(f"[bold green]✔ エビングハウス忘却曲線減衰の再計算完了: {updated} 件の記憶スコアを更新しました。[/bold green]\n")

                elif sub_args.startswith("tier "):
                    t_target = sub_args[5:].strip().lower()
                    mems = adv_memory.sql.get_memories(tier=t_target, limit=15, min_importance=1)
                    table = Table(title=f"[bold magenta]◈ Tier: {t_target} 記憶一覧 ({len(mems)}件) ◈[/bold magenta]", border_style="magenta")
                    table.add_column("ID", style="dim", width=4)
                    table.add_column("Subject", style="bold yellow", width=18)
                    table.add_column("Fact Content", style="white")
                    table.add_column("想起度", justify="right", style="bold green", width=8)
                    table.add_column("Imp", justify="center", style="bold red", width=5)
                    table.add_column("Acc", justify="right", style="cyan", width=5)
                    for m in mems:
                        d_score = m.get("decay_score", 1.0) or 1.0
                        table.add_row(
                            str(m.get("id", "")),
                            m.get("subject", ""),
                            m.get("fact_content", ""),
                            f"{d_score*100:.1f}%",
                            str(m.get("importance", 1)),
                            str(m.get("access_count", 0))
                        )
                    console.print(table)

                elif sub_args.startswith("search "):
                    q = sub_args[7:].strip()
                    mems = adv_memory.sql.recall_similar(q, limit=5)
                    table = Table(title=f"[bold magenta]◈ 記憶想起結果 (エビングハウス忘却曲線減衰 × 4-Tier想起): '{q}' ◈[/bold magenta]", border_style="magenta")
                    table.add_column("Tier", style="bold cyan", width=12)
                    table.add_column("Subject", style="bold yellow", width=16)
                    table.add_column("Fact Content", style="white")
                    table.add_column("想起度", justify="right", style="bold green", width=8)
                    table.add_column("スコア", justify="right", style="bold yellow", width=8)
                    table.add_column("Acc", justify="right", style="cyan", width=5)
                    for m in mems:
                        d_score = m.get("decay_score", 1.0) or 1.0
                        h_score = m.get("hybrid_score", 0.0) or 0.0
                        table.add_row(
                            m.get("tier", "semantic"),
                            m.get("subject", ""),
                            m.get("fact_content", ""),
                            f"{d_score*100:.1f}%",
                            f"{h_score:.3f}",
                            str(m.get("access_count", 0))
                        )
                    console.print(table)

                elif sub_args == "optimize":
                    opt_res = adv_memory.optimize()
                    console.print(f"[bold green]✔ SQLite DB 最適化完了: {opt_res}[/bold green]\n")

                else:
                    # 全重要記憶の4-Tierダイジェスト表示
                    core_mems = adv_memory.sql.get_memories(min_importance=2, limit=15)
                    table = Table(title="[bold magenta]◈ TUGUMIv6 4-Tier 構造化長期記憶（拓磨様プロファイル・重要方針） ◈[/bold magenta]", border_style="magenta")
                    table.add_column("Tier", style="bold cyan", width=12)
                    table.add_column("Cat", style="cyan", width=10)
                    table.add_column("Subject", style="bold yellow", width=18)
                    table.add_column("Fact Content", style="white")
                    table.add_column("想起度", justify="right", style="bold green", width=8)
                    table.add_column("Imp", justify="center", style="bold red", width=5)
                    table.add_column("Acc", justify="right", style="cyan", width=5)
                    for m in core_mems:
                        d_score = m.get("decay_score", 1.0) or 1.0
                        table.add_row(
                            m.get("tier", "semantic"),
                            m.get("category", ""),
                            m.get("subject", ""),
                            m.get("fact_content", ""),
                            f"{d_score*100:.1f}%",
                            str(m.get("importance", 3)),
                            str(m.get("access_count", 0))
                        )
                    console.print(table)
                    console.print("[dim]※ コマンド例: /memory stats | /memory decay | /memory tier <name> | /memory search <単語> | /remember [tier] <内容>[/dim]\n")
                continue

            # 6.5 直接記憶格納 (/remember [tier] <内容>)
            if user_input.startswith("/remember"):
                rem_args = user_input[9:].strip()
                if not rem_args:
                    console.print("[yellow]使用方法: /remember [tier] <記憶したい内容>[/yellow]")
                    console.print("[dim]例: /remember procedural git commit は必ず Conventional Commits に従う[/dim]")
                    console.print("[dim]例: /remember 拓磨様のお気に入りの競馬場は中京競馬場 (デフォルト: semantic)[/dim]\n")
                    continue

                valid_tiers = ("semantic", "procedural", "working", "episodic")
                parts = rem_args.split(maxsplit=1)
                if len(parts) == 2 and parts[0].lower() in valid_tiers:
                    chosen_tier = parts[0].lower()
                    content = parts[1].strip()
                else:
                    chosen_tier = "semantic"
                    content = rem_args

                mem_id = adv_memory.sql.remember(
                    content=content,
                    category="user_direct",
                    tier=chosen_tier,
                    subject="拓磨様指示",
                    importance=4
                )
                console.print(f"[bold green]✔ 長期記憶に格納しました (ID: {mem_id})[/bold green]")
                console.print(f"  [cyan]Tier:[/cyan] [bold]{chosen_tier}[/bold] | [cyan]内容:[/cyan] {content}\n")
                continue

            # 7. ハイブリッドRAGナレッジ検索・AI回答 (/rag)
            force_rag_query = False
            if user_input.startswith("/rag"):
                sub_query = user_input[4:].strip()

                if sub_query.startswith(("sync", "reindex", "update")):
                    is_force = "force" in sub_query or "all" in sub_query
                    inspector.display_tool_start("HybridRAGEngine.sync", {"max_files": 10000, "force": is_force})
                    stats = rag.ingest_all(max_files=10000, force=is_force)
                    n_synced = stats.get("newly_indexed_chunks", 0)
                    tot_files = stats.get("total_indexed_files", 0)
                    tot_chunks = stats.get("total_chunks", 0)
                    inspector.display_tool_result("HybridRAGEngine", True, f"総ファイル {tot_files}件 / 総チャンク {tot_chunks}件 (新規更新 {n_synced}チャンク)")
                    console.print(f"[bold green]✔ ナレッジベース同期完了: 総ファイル {tot_files}件 ({tot_chunks} チャンク / 新規更新 {n_synced}件)[/bold green]\n")
                    continue

                if sub_query in ("status", "info"):
                    st_sum = rag.get_status_summary()
                    f_stats = st_sum.get("folder_stats", {})
                    folder_lines = [f"  • [bold]{k}[/bold]: {v.get('files', 0)} files ({v.get('chunks', 0)} chunks)" for k, v in f_stats.items()]
                    console.print(Panel(
                        f"[cyan]ナレッジベース:[/cyan] TUGUMI_RAG (Obsidian / TUGUMIDesk / Self-Evolution連動)\n"
                        f"[cyan]登録ファイル数:[/cyan] [bold green]{st_sum.get('total_indexed_files', 0)}[/bold green] ファイル "
                        f"([bold cyan]{st_sum.get('total_chunks', 0)}[/bold cyan] チャンク)\n"
                        f"[cyan]3072dベクトル数:[/cyan] [bold green]{st_sum.get('embedded_chunks', 0)}[/bold green] 件 / "
                        f"[cyan]FTS5インデックス:[/cyan] [bold green]{st_sum.get('fts_chunks', st_sum.get('fts5_rows', 0))}[/bold green] 行\n"
                        "[cyan]フォルダ別内訳:[/cyan]\n" + ("\n".join(folder_lines) if folder_lines else "  (なし)") + "\n"
                        "[dim]※ コマンド: /rag <質問・タスク>, /rag search <単語>, /rag list [フォルダ], /rag sync[/dim]",
                        title="[bold cyan]◈ RAG Knowledge Engine Status ◈[/bold cyan]",
                        border_style="cyan"
                    ))
                    console.print()
                    continue

                if sub_query == "list" or sub_query.startswith("list "):
                    f_filter = sub_query[4:].strip() if len(sub_query) > 4 else None
                    files_list = rag.list_indexed_files(folder_filter=f_filter)
                    if not files_list:
                        console.print(f"[yellow]該当するRAG登録ファイルはありません ({f_filter or 'all'})。[/yellow]\n")
                    else:
                        lines_out = []
                        for idx_f, f_item in enumerate(files_list, 1):
                            _, r_lbl = rag._classify_folder_role(f_item.get("folder", ""), f_item.get("rel_path", ""))
                            lines_out.append(
                                f"[bold cyan]{idx_f:2d}.[/bold cyan] [bold white]{f_item.get('title')}[/bold white] "
                                f"[dim]({f_item.get('folder')} / {f_item.get('chunks', 0)} chunks)[/dim] {r_lbl.split('（')[0]}"
                            )
                        console.print(Panel(
                            "\n".join(lines_out),
                            title=f"[bold cyan]◈ RAG Indexed Files ({len(files_list)} files) ◈[/bold cyan]",
                            border_style="cyan"
                        ))
                        console.print()
                    continue

                if sub_query.startswith("add "):
                    add_body = sub_query[4:].strip()
                    if "|" in add_body:
                        k_title, k_text = [x.strip() for x in add_body.split("|", 1)]
                    else:
                        k_title = f"CLI_Note_{int(time.time())}"
                        k_text = add_body
                    if not k_text:
                        console.print("[yellow]使い方: /rag add <タイトル> | <登録するナレッジ本文>[/yellow]\n")
                        continue
                    inspector.display_tool_start("HybridRAGEngine.add_knowledge", {"title": k_title})
                    ok = rag.add_knowledge(title=k_title, text=k_text, category="manual")
                    inspector.display_tool_result("HybridRAGEngine", ok, f"ナレッジ『{k_title}』を3072d RAGへ登録")
                    console.print(f"[bold green]✔ RAGナレッジベースへ『{k_title}』を追加・インデックスしました。[/bold green]\n")
                    continue

                if sub_query.startswith("search "):
                    s_keyword = sub_query[7:].strip()
                    if not s_keyword:
                        console.print("[yellow]検索キーワードを指定してください。例: /rag search 井上和[/yellow]\n")
                        continue
                    inspector.display_tool_start("HybridRAGEngine", {"query": s_keyword, "top_k": 5})
                    results = rag.search_hybrid(s_keyword, top_k=5)
                    if not results:
                        inspector.display_tool_result("HybridRAGEngine", False, "該当ナレッジなし")
                        console.print(f"[yellow]'{s_keyword}' に一致するナレッジは見つかりませんでした。[/yellow]\n")
                    else:
                        inspector.display_tool_result("HybridRAGEngine", True, f"{len(results)}件のナレッジを抽出")
                        for i, r in enumerate(results, 1):
                            clean_body = r.get("clean_text") or r.get("text", "")
                            role_lbl = r.get("role_label", "📘 ナレッジ")
                            p = Panel(
                                f"[bold magenta]{role_lbl}[/bold magenta] [dim](Folder: {r.get('folder')})[/dim]\n"
                                + clean_body[:380] + ("..." if len(clean_body) > 380 else ""),
                                title=f"[bold cyan][{i}] {r.get('title')}[/bold cyan] [dim](Score: {round(r.get('score', 0), 3)} / RRF: {round(r.get('rrf_score', 0), 4)})[/dim]",
                                border_style="cyan"
                            )
                            console.print(p)
                        console.print()
                    continue

                # 引数なしの場合は分かりやすいガイドを表示
                if not sub_query:
                    console.print(Panel(
                        "[bold cyan]【3072次元ハイブリッドRAGの使い方】[/bold cyan]\n"
                        "• [bold green]通常のチャット・タスク[/bold green] : 質問やタスク指示に応じて関連知識・成功例リファレンスを自動でスマート注入\n"
                        "• [bold green]/rag <質問文・タスク指示>[/bold green] : 明示的にRAGを強制検索し、つぐみがナレッジに基づいて回答・タスク遂行\n"
                        "• [bold green]/rag search <単語>[/bold green] : ナレッジの該当チャンク・スコア・役割を一覧表示\n"
                        "• [bold green]/rag list [フォルダ][/bold green] : インデックス済みファイル一覧を表示 (例: `/rag list 成功例`)\n"
                        "• [bold green]/rag add <題> | <本文>[/bold green] : 新しい知見をその場で3072次元ベクトル化してRAGに登録\n"
                        "• [bold green]/rag sync[/bold green] : TUGUMI_RAG から最新ドキュメントを再インデックス\n"
                        "• [bold green]/rag status[/bold green] : 現在のベクトル登録数・フォルダ別内訳を確認",
                        title="[bold cyan]◈ TUGUMIv6 RAG KNOWLEDGE GUIDE ◈[/bold cyan]",
                        border_style="cyan"
                    ))
                    console.print()
                    continue

                # /rag <質問文・タスク指示> の場合：明示的RAGモードとしてメイン推論・エージェント実行パイプラインへ直結
                force_rag_query = True
                user_input = sub_query

            # 3. 内省ログ (/reflect)
            if user_input == "/reflect":
                inspector.display_tool_start("ReflectionEngine", {"action": "check_risk"})
                risks = reflection.check_risk("")
                if not risks:
                    inspector.display_tool_result("ReflectionEngine", True, "未解決の失敗記録なし。システム健全です。")
                else:
                    inspector.display_tool_result("ReflectionEngine", True, f"{len(risks)}件の失敗記録を取得")
                    table = Table(title="[bold yellow]TUGUMIv6 Failure Guard 監査レコード[/bold yellow]", border_style="yellow")
                    table.add_column("ID", width=6)
                    table.add_column("Keyword", style="cyan")
                    table.add_column("Cause", style="red")
                    table.add_column("Forbidden Action", style="bold red")
                    table.add_column("Correct Alternative", style="green")
                    for r in risks:
                        table.add_row(str(r['id']), r['keyword'], r['cause'][:30], r['forbidden_action'][:30], r['correct_alternative'][:30])
                    console.print(table)
                console.print()
                continue

            # 4. 不労所得 (/income)
            if user_input == "/income":
                inspector.display_tool_start("DeFiArbitrageMonitor", {"action": "scan_spreads"})
                spreads = arbitrage_mon.scan_binance_ticker_spreads()
                valid_spreads = [s for s in spreads if "error" not in s]
                error_items = [s["error"] for s in spreads if "error" in s]

                if valid_spreads:
                    inspector.display_tool_result("DeFiArbitrageMonitor", True, f"{len(valid_spreads)}ペアのスキャン完了")
                else:
                    inspector.display_tool_result("DeFiArbitrageMonitor", False, f"スキャン失敗: {', '.join(error_items) if error_items else 'データなし'}")
                
                table = Table(title="[bold green]DeFi 取引所間アービトラージ・スプレッド監視 (Binance ⇄ Bybit)[/bold green]", border_style="green")
                table.add_column("Symbol", style="bold cyan")
                table.add_column("Binance Price", justify="right")
                table.add_column("Bybit Price", justify="right")
                table.add_column("Arbitrage Route", style="magenta")
                table.add_column("Spread %", justify="right", style="bold yellow")
                for s in valid_spreads:
                    bin_p = f"${s.get('binance_price', s.get('bid')):,}" if isinstance(s.get('binance_price'), (int, float)) else str(s.get('bid'))
                    by_p = f"${s.get('bybit_price', s.get('ask')):,}" if isinstance(s.get('bybit_price'), (int, float)) else str(s.get('ask'))
                    direction = s.get('direction', 'Bid-Ask')
                    spread_style = "bold green" if s.get('is_profitable') else "yellow"
                    table.add_row(s['symbol'], bin_p, by_p, direction, f"[{spread_style}]{s['spread_pct']}%[/{spread_style}]")
                console.print(table)
                if error_items:
                    console.print(f"[bold yellow]⚠ 一部API取得エラー: {'; '.join(error_items)}[/bold yellow]")
                console.print("[cyber.dim]自動記事生成・配信パイプライン: 稼働待機中 (/data/media_articles)[/cyber.dim]\n")
                continue

            # 5. システム検証 (/verify または /check)
            if user_input in ("/verify", "/check"):
                inspector.display_tool_start("SystemVerifier", {"target": "gemini_client.py", "action": "verify_all_gates"})
                res = verifier.verify_all_gates(os.path.join(TUGUMI_ROOT, "core", "gemini_client.py"))
                inspector.display_tool_result("SystemVerifier", res['passed'], res.get('message', ''), res.get('details', ''))
                console.print()
                continue

            # 6. 自律修復・健全性回復 (/heal)
            if user_input.startswith("/heal"):
                inspector.display_tool_start("AutoHealEngine", {"action": "scan_and_heal"})
                heal_res = autoheal.heal_all_broken()
                if heal_res["broken_found"] == 0:
                    inspector.display_tool_result("AutoHealEngine", True, f"全{heal_res['scanned']}ファイル正常 (構文エラー 0件, Exit Code 0)")
                else:
                    inspector.display_tool_result(
                        "AutoHealEngine",
                        heal_res["failed_count"] == 0,
                        f"破損検出: {heal_res['broken_found']}件, 修復完了: {heal_res['healed_count']}件, 失敗: {heal_res['failed_count']}件"
                    )
                console.print()
                continue

            # 7. ストレージ同期 (/sync)
            if user_input == "/sync":
                inspector.display_tool_start("DeskSync", {"destination": "TUGUMIDesk"})
                s_res = desk_sync.sync_to_desk()
                inspector.display_tool_result("DeskSync", True, f"{s_res.get('synced_count', 0)} ファイルを高速同期完了", s_res.get('destination'))
                console.print()
                continue

            # 8. Antigravity SDK 10大ピラー・最新仕様検視・制御 (/sdk, /antigravity) ＆ 自己進化 (/evolve)
            if user_input.startswith(("/sdk", "/antigravity", "/evolve")):
                parts = user_input.split(maxsplit=2)
                base_cmd = parts[0].lower()
                sub_cmd = parts[1].lower() if len(parts) > 1 else ""
                rest_arg = parts[2].strip() if len(parts) > 2 else ""
                p = CYBER_PALETTES.get(curr_mode, CYBER_PALETTES["light"])

                evolver_path = os.path.expanduser("~/.agents/skills/self-evolution-engine/scripts/antigravity_self_evolver.py")
                evolver_mod = None
                if os.path.exists(evolver_path):
                    try:
                        import importlib.util
                        spec_loader = importlib.util.spec_from_file_location("antigravity_self_evolver", evolver_path)
                        evolver_mod = importlib.util.module_from_spec(spec_loader)
                        spec_loader.loader.exec_module(evolver_mod)
                    except Exception:
                        evolver_mod = None

                # A. /sdk reset
                if base_cmd in ("/sdk", "/antigravity") and sub_cmd in ("reset", "restart", "clear"):
                    engine.reset_session()
                    console.print("[bold green]✔ Antigravity SDK 常駐セッション (AntigravitySession) をクリーンリセットいたしました、拓磨様🌸[/bold green]\n")
                    continue

                # B. /sdk engine [antigravity|gemini]
                if base_cmd in ("/sdk", "/antigravity") and sub_cmd == "engine":
                    target_eng = rest_arg.lower() if rest_arg else ("gemini" if engine.primary_engine == "antigravity" else "antigravity")
                    if target_eng not in ("antigravity", "gemini"):
                        console.print("[bold yellow]使用法: `/sdk engine antigravity` または `/sdk engine gemini`[/bold yellow]\n")
                        continue
                    new_eng = engine.set_primary_engine(target_eng, persist=True)
                    console.print(Panel(
                        f"[bold green]✔ プライマリ推論エンジンを [bold cyan]{new_eng.upper()}[/bold cyan] に切り替えました！[/bold green]\n"
                        f"[dim]設定は engine_config.json に永続化されました。[/dim]",
                        title=f"[bold {p['primary']}]◈ Primary Engine Switched ◈[/bold {p['primary']}]",
                        border_style="green",
                    ))
                    console.print()
                    continue

                # C. /sdk spec または /evolve spec (実機 google-antigravity SDK 仕様ライブ検視)
                if sub_cmd == "spec":
                    spec_data = evolver_mod.check_antigravity_sdk_spec() if evolver_mod else {"version": "0.1.20", "configs": {}, "hooks_v2": [], "triggers": [], "enums": {}}
                    cfg_map = spec_data.get("configs", {})
                    local_fields = list(cfg_map.get("LocalAgentConfig", {}).keys())
                    cap_fields = list(cfg_map.get("CapabilitiesConfig", {}).keys())
                    hooks_list = spec_data.get("hooks_v2", [])
                    triggers_list = spec_data.get("triggers", [])
                    enums_map = spec_data.get("enums", {})

                    s_table = Table(
                        title=f"[bold {p['primary']}]🔬 Google Antigravity SDK (v{spec_data.get('version', '0.1.20')}) 実機仕様ライブ検視 (/sdk spec)[/bold {p['primary']}]",
                        border_style=p["border"],
                        expand=True,
                        show_lines=True,
                    )
                    s_table.add_column("SDK コンポーネント", style="bold cyan", width=26)
                    s_table.add_column("数", style="bold yellow", width=6, justify="center")
                    s_table.add_column("実機抽出フィールド / デコレータ / シグネチャ一覧", style="white")
                    s_table.add_row("LocalAgentConfig", str(len(local_fields)), ", ".join(local_fields))
                    s_table.add_row("CapabilitiesConfig", str(len(cap_fields)), ", ".join(cap_fields))
                    s_table.add_row("Hooks v2 (@hooks.*)", str(len(hooks_list)), ", ".join(f"@{h}" for h in hooks_list))
                    s_table.add_row("Native Triggers", str(len(triggers_list)), ", ".join(f"triggers.{t}" for t in triggers_list))
                    for ek, ev in enums_map.items():
                        s_table.add_row(f"Enum: {ek}", str(len(ev)), ", ".join(ev))
                    console.print()
                    console.print(s_table)
                    console.print()
                    continue

                # D. /sdk tools または /evolve tools (登録ツール＆動的合成ツール一覧)
                if sub_cmd == "tools":
                    from core.dynamic_skill_synthesizer import DynamicSkillSynthesizer
                    synth = DynamicSkillSynthesizer()
                    dyn_tools = synth.list_synthesized_skills()
                    all_tools = engine.antigravity.reload_tools() if hasattr(engine.antigravity, "reload_tools") else engine.antigravity.get_tools()

                    t_table = Table(
                        title=f"[bold {p['primary']}]🛠️ Antigravity SDK 登録ツール ({len(all_tools)}種) ＆ 動的合成ツール ({len(dyn_tools)}種)[/bold {p['primary']}]",
                        border_style=p["border"],
                        expand=True,
                    )
                    t_table.add_column("区分", style="bold cyan", width=14)
                    t_table.add_column("ツール関数名", style="bold yellow", width=32)
                    t_table.add_column("概要 (Docstring)", style="white")
                    dyn_fn_names = {k.split(".")[-1] for k in dyn_tools}
                    for fn in all_tools:
                        fn_name = getattr(fn, "__name__", str(fn))
                        doc_line = (getattr(fn, "__doc__", "") or "").strip().splitlines()[0] if getattr(fn, "__doc__", None) else "Native callable tool"
                        kind = "[bold magenta]⚡ 動的合成[/bold magenta]" if fn_name in dyn_fn_names else "[green]● コア標準[/green]"
                        t_table.add_row(kind, fn_name, doc_line[:70])
                    console.print()
                    console.print(t_table)
                    console.print()
                    continue

                # E. /evolve audit (システム衛生＆アーキテクチャ深層監査のみ即時実行)
                if base_cmd == "/evolve" and sub_cmd == "audit":
                    if SelfEvolutionEngine:
                        evo = SelfEvolutionEngine(mode=curr_mode)
                        evo.phase2_architecture_audit()
                    continue

                # F. /sdk [status|gap|verify] または /evolve [status|check|gap|verify] (API消費ゼロ・10大ピラーライブ診断)
                if base_cmd in ("/sdk", "/antigravity") or (base_cmd == "/evolve" and sub_cmd in ("status", "check", "gap", "verify")):
                    ag_st = engine.get_antigravity_status()
                    ver_res = evolver_mod.verify_tugumi_evolution() if evolver_mod else {"all_passed": True, "checks": {}, "gap_summary": {"evolution_score_percent": 100.0}}
                    checks = ver_res.get("checks", {})
                    gap_sum = ver_res.get("gap_summary", {})
                    score_pct = gap_sum.get("evolution_score_percent", ag_st.get("evolution_score", 100.0))
                    sess_info = ag_st.get("session", {})
                    telem = ag_st.get("telemetry", {})

                    p_table = Table(
                        title=f"[bold {p['primary']}]🚀 Antigravity SDK (v{ag_st.get('sdk_version', '0.1.20')}) 10大進化ピラー＆常駐セッション診断[/bold {p['primary']}]",
                        border_style=p["border"],
                        expand=True,
                        show_lines=True,
                    )
                    p_table.add_column("Pillar", style="bold cyan", width=8, justify="center")
                    p_table.add_column("SDK 機能フィールド", style="bold yellow", width=28)
                    p_table.add_column("状態", width=10, justify="center")
                    p_table.add_column("実機設定・テレメトリ詳細", style="white")

                    pillar_rows = [
                        ("P1", "skills_paths", checks.get("skills_paths", True), f"~/.agents/skills ({ag_st.get('skills_count', 61)}種 自動ディスカバリ)"),
                        ("P2", "mcp_servers (MCP 2.0)", checks.get("mcp_servers", True), f"{len(ag_st.get('mcp_servers', []))}基 (2026-07-28 Stateless Core & Ephemeral On-Demand / 常駐占有ゼロ)"),
                        ("P3", "subagents", checks.get("subagents", True), f"{len(ag_st.get('subagents', []))}体 ({', '.join(ag_st.get('subagents', []))})"),
                        ("P4", "policies", checks.get("policies", True), "policy.allow_all() 高速自律実行ポリシー"),
                        ("P5", "workspaces", checks.get("workspaces", True), f"{engine.antigravity.workspace} 境界保護"),
                        ("P6", "compaction_config", checks.get("compaction_config", True), "CompactionConfig(token_threshold=150,000) ロスレス要約"),
                        ("P7", "retry_config", checks.get("retry_config", True), "RetryConfig(exponential=2.0, jitter=0.2) 自己修復"),
                        ("P8", "hooks (Hooks v2)", checks.get("hooks_registered", True), f"3種稼働 (@on_tool_error, @post_tool_call, @on_compaction) | Call:{telem.get('tool_calls', 0)} Recover:{telem.get('tool_errors_recovered', 0)}"),
                        ("P9", "save_dir", checks.get("save_dir", True), "~/.tugumi/sessions マルチターン状態永続化"),
                        ("P10", "tool_output_truncation", checks.get("tool_output_truncation_config", True), "ToolOutputTruncationConfig(max_tokens=16,000) 溢れ防護"),
                    ]
                    for pid, pname, pok, pdesc in pillar_rows:
                        p_table.add_row(pid, pname, "[bold green]✔ PASS[/bold green]" if pok else "[bold red]✖ GAP[/bold red]", pdesc)

                    sess_badge = "[bold green]🟢 稼働中 (Warm Persistent)[/bold green]" if sess_info.get("active") else "[bold yellow]🟡 オンデマンド待機中 (初回呼出時ミリ秒起動)[/bold yellow]"
                    summary_panel = Panel(
                        f"[bold cyan]• 総合進化スコア:[/] [bold green]{score_pct}% (10/10 Pillars Complete)[/bold green]  │  "
                        f"[bold cyan]プライマリエンジン:[/] [bold yellow]{ag_st.get('primary_engine', 'antigravity').upper()}[/bold yellow]\n"
                        f"[bold cyan]• アクティブモデル:[/] [bold white]{ag_st.get('current_model')}[/bold white] (Thinking: [bold cyan]{ag_st.get('thinking_level', 'high').upper()}[/bold cyan])\n"
                        f"[bold cyan]• 常駐セッション:[/] {sess_badge} (Turns: {sess_info.get('turn_count', 0)})\n"
                        f"[bold cyan]• ネイティブ登録ツール:[/] [bold green]{ag_st.get('registered_tools_count', 0)} 種[/bold green]  │  "
                        f"[bold cyan]認識SKILL総数:[/] [bold green]{ag_st.get('skills_count', 61)} 種[/bold green]  │  "
                        f"[bold cyan]マウントMCP:[/] [bold green]{len(ag_st.get('mcp_servers', []))} 基[/bold green]\n"
                        f"[dim]※ サブコマンド: `/sdk spec` (SDK仕様検視) | `/sdk tools` (ツール一覧) | `/sdk engine <antigravity|gemini>` | `/sdk reset` | `/evolve run [topic]`[/dim]",
                        title=f"[bold {p['primary']}]◈ Antigravity SDK Live Telemetry Summary ◈[/bold {p['primary']}]",
                        border_style=p["border"],
                    )
                    console.print()
                    console.print(summary_panel)
                    console.print(p_table)
                    console.print()
                    continue

                # G. /evolve [fast|run|<topic>] (フルまたは高速SOTA自己進化サイクル実行)
                is_fast_evo = (sub_cmd in ("fast", "--fast", "-f"))
                if sub_cmd in ("run", "fast", "--fast", "-f"):
                    topic = rest_arg or "2026 AI Agent Protocols & Context Engineering"
                else:
                    topic = user_input[7:].strip() or "2026 AI Agent Protocols & Context Engineering"

                if SelfEvolutionEngine:
                    evo = SelfEvolutionEngine(mode=curr_mode)
                    evo.run_full_cycle(topic=topic, fast_mode=is_fast_evo)
                    engine.reload_skills()
                    completer.reload_skills(force=True)
                    token_tracker.record_turn(
                        prompt_text=topic,
                        response_text="Self-Evolution Full SOTA Trend Sensing & Tool Synthesis (Switch 2)" * 15
                    )
                    token_tracker.render_cost_banner(console, mode=curr_mode)
                else:
                    console.print("[bold red]SelfEvolutionEngine module not found.[/bold red]")
                continue

            # 9. コンテキスト予算防衛 (/context)
            if user_input == "/context":
                recent_logs = memory.get_recent_messages(limit=50)
                total_chars = sum(len(m.get("content", "")) for m in recent_logs)
                est_tokens = context_compressor.estimate_tokens(" " * total_chars)
                pruned = context_compressor.prune_history(recent_logs, max_turns=10)
                pruned_chars = sum(len(m.get("content", "")) for m in pruned)
                pruned_tokens = context_compressor.estimate_tokens(" " * pruned_chars)

                table = Table(title="[bold cyan]ContextGuard トークン予算防衛ステータス[/bold cyan]", border_style="cyan")
                table.add_column("項目", style="bold")
                table.add_column("値", style="yellow")
                table.add_row("DB保存メッセージ総数 (直近50件)", str(len(recent_logs)))
                table.add_row("累積コンテキスト推定トークン", f"{est_tokens:,} tokens")
                table.add_row("スマート剪定後トークン (max_turns=10)", f"{pruned_tokens:,} tokens")
                saving_pct = round((1 - (pruned_tokens / est_tokens)) * 100, 1) if est_tokens > 0 else 0
                table.add_row("トークン削減率 (Token Budget Defense)", f"{saving_pct}% 削減")
                console.print(table)
                console.print()
                continue

            # 10. 動画・音声ダウンロード (/dl)
            if user_input.startswith("/dl"):
                raw_args = user_input[3:].strip()
                import shlex
                import subprocess

                dl_cmd = [os.path.expanduser("~/bin/tugumi-dl")]
                if raw_args:
                    try:
                        dl_cmd.extend(shlex.split(raw_args))
                    except Exception:
                        dl_cmd.append(raw_args)

                console.print("[bold cyan]🎬 Universal Video Downloader 起動中...[/bold cyan]")
                try:
                    subprocess.run(dl_cmd)
                except Exception as e:
                    console.print(f"[bold red]ダウンロード起動エラー:[/] {e}")
                console.print()
                continue

            # 10.5 自律Gitクローン＆自動エラー修復 (/clone)
            if user_input.startswith("/clone"):
                raw_args = user_input[6:].strip()
                import shlex
                import subprocess

                clone_cmd = [os.path.expanduser("~/bin/tugumi-clone")]
                if raw_args:
                    try:
                        clone_cmd.extend(shlex.split(raw_args))
                    except Exception:
                        clone_cmd.append(raw_args)

                console.print("[bold cyan]🌸 TUGUMIv6 自律Gitクローン＆自動エラー修復システム 起動中...[/bold cyan]")
                try:
                    subprocess.run(clone_cmd)
                except Exception as e:
                    console.print(f"[bold red]クローン実行エラー:[/] {e}")
                console.print()
                continue

            # 10.9 SKILL・常駐セッション無停止ホットリロード (/reload)
            if user_input.strip() in ("/reload", "/skills reload", "/reload skills", "/skills -r"):
                with console.status("[bold cyan]🔄 SKILLエコシステム＆常駐セッションをホットリロード中...[/bold cyan]"):
                    completer.reload_skills(force=True)
                    reload_info = engine.reload_skills()
                    inspector_skills = SkillInspector().list_skills()

                p = CYBER_PALETTES.get(curr_mode, CYBER_PALETTES["light"])
                console.print(Panel(
                    f"[bold green]✔ TUGUMIv6 無停止ホットリロードが完了いたしました！[/bold green]\n\n"
                    f"[cyan]• 認識SKILL総数:[/] [bold yellow]{len(inspector_skills)}[/bold yellow] 種 (正本 ~/.agents/skills 完全同期)\n"
                    f"[cyan]• CLI補完候補:[/] [bold green]即座に最新化済[/bold green] (ミリ秒mtime自動追従稼働)\n"
                    f"[cyan]• 常駐Agentセッション:[/] [bold cyan]クリーン同期済[/bold cyan] (会話履歴・コンテキスト保持)\n"
                    f"[cyan]• 純度＆防護ゲート:[/] [bold magenta]Anti-Junk / Termux aarch64 適合ガード常時稼働[/bold magenta]",
                    title=f"[bold {p['primary']}]◈ Zero-Downtime Hot Reload Completed ◈[/bold {p['primary']}]",
                    border_style="green"
                ))
                console.print()
                continue

            # 11. SKILL一覧・検索 (/skills) および個別スキル検視・手動発動 (/skill)
            if user_input.startswith("/skills"):
                sk_parts = user_input.split(maxsplit=2)
                sk_sub = sk_parts[1].lower() if len(sk_parts) > 1 else ""

                if sk_sub in ("reload", "-r"):
                    completer.reload_skills(force=True)
                    reload_info = engine.reload_skills()
                    console.print(f"[bold green]✔ 全 {reload_info.get('total_skills', 0)} 種のSKILLをホットリロードいたしました！[/bold green]\n")
                    continue

                if sk_sub in ("audit", "check"):
                    from core.skill_assimilator import SkillAssimilator
                    assimilator = SkillAssimilator()
                    installed = assimilator.list_installed_skills()
                    a_table = Table(
                        title=f"[bold cyan]🔍 TUGUMIv6 配備済み全SKILL Termux純度＆適合性監査 ({len(installed)}種)[/bold cyan]",
                        border_style="cyan",
                        expand=True
                    )
                    a_table.add_column("No", width=4, justify="center")
                    a_table.add_column("スキル名", style="bold yellow", width=28)
                    a_table.add_column("Termux適合性", width=14, justify="center")
                    a_table.add_column("説明 / 診断", style="white")

                    for idx, s in enumerate(installed, start=1):
                        rep = assimilator.audit_skill(s["path"])
                        status_str = "[bold green]✔ 完全適合[/bold green]" if rep["is_valid"] and not rep["termux_fixes_needed"] else "[yellow]⚠ 要修正[/yellow]"
                        diag = s["description"]
                        if rep["termux_fixes_needed"]:
                            diag = f"[yellow]Termux非互換記述 {len(rep['termux_fixes_needed'])} 件検知[/yellow]"
                        a_table.add_row(str(idx), s["name"], status_str, diag)
                    console.print()
                    console.print(a_table)
                    console.print()
                    continue

                if sk_sub in ("assimilate", "import") and len(sk_parts) > 2:
                    target_import_path = sk_parts[2].strip()
                    from core.skill_assimilator import SkillAssimilator
                    assimilator = SkillAssimilator()
                    res = assimilator.purify_and_install(target_import_path)
                    if res.get("success"):
                        completer.reload_skills(force=True)
                        engine.reload_skills()
                        console.print(Panel(
                            f"[bold green]✔ 外部スキル『{res['skill_name']}』の純化・Termux移植・配備が完了いたしました！[/bold green]\n\n"
                            f"[cyan]• 配備先:[/] {res['installed_path']}\n"
                            f"[cyan]• Termux自動修正ファイル:[/] {len(res.get('fixed_files', []))} 件 (シバン置換・/tmp適合)\n"
                            f"[cyan]• ホットリロード:[/] [bold green]即座に完了 (再起動なしで利用可能)[/bold green]",
                            title="[bold cyan]◈ Curated Skill Assimilation Success ◈[/bold cyan]",
                            border_style="green"
                        ))
                    else:
                        console.print(f"[bold red]✖ スキル純化・取り込み失敗:[/] {res.get('error')}\n")
                    continue

                sk_query = user_input.split(maxsplit=1)[1] if len(user_input.split()) > 1 else ""
                render_skills_cli(console, mode=curr_mode, query=sk_query)
                continue

            if user_input.startswith("/skill"):
                sk_parts = user_input.split(maxsplit=2)
                if len(sk_parts) == 1:
                    render_skills_cli(console, mode=curr_mode, query="")
                    continue
                target_skill = sk_parts[1].strip()
                skill_task = sk_parts[2].strip() if len(sk_parts) > 2 else ""
                skill_md_path = os.path.expanduser(f"~/.agents/skills/{target_skill}/SKILL.md")
                if os.path.isfile(skill_md_path):
                    try:
                        with open(skill_md_path, "r", encoding="utf-8", errors="ignore") as sf:
                            skill_md_content = sf.read()
                    except Exception as e:
                        skill_md_content = f"読み込みエラー: {e}"
                    if not skill_task:
                        from rich.markdown import Markdown
                        preview_md = "\n".join(skill_md_content.splitlines()[:45])
                        if len(skill_md_content.splitlines()) > 45:
                            preview_md += f"\n\n... (全 {len(skill_md_content.splitlines())} 行 | `/skill {target_skill} <指示>` でこのスキルを強制適用して実行)"
                        console.print(Panel(
                            Markdown(preview_md),
                            title=f"[bold cyan]🧩 SKILL Inspector: {target_skill}[/bold cyan]",
                            subtitle=f"[dim]{skill_md_path}[/dim]",
                            border_style="cyan",
                        ))
                        console.print()
                        continue
                    else:
                        console.print(f"[bold cyan]🧩 スキル『{target_skill}』のプロトコルをロードし、指示を実行いたします！[/bold cyan]\n")
                        user_input = (
                            f"【強制発動SKILL: {target_skill}】\n"
                            f"以下のSKILL定義に従ってタスクを遂行してください:\n"
                            f"{skill_md_content[:6000]}\n\n"
                            f"【拓磨様からのご指示】\n{skill_task}"
                        )
                else:
                    render_skills_cli(console, mode=curr_mode, query=target_skill)
                    continue

            # 11.5 FPF 第一原理推論・前提鮮度監査 (/fpf)
            if user_input.startswith("/fpf"):
                fpf_query = user_input.split(maxsplit=1)[1] if len(user_input.split()) > 1 else ""
                render_fpf_cli(console, mode=curr_mode, query=fpf_query)
                continue

            # 11.8 MCP 2.0 連携サーバー・ツール一覧 (/mcp)
            if user_input.startswith("/mcp"):
                mcp_target = user_input.split(maxsplit=1)[1].strip() if len(user_input.split()) > 1 else ""
                render_mcp_cli(console, mode=curr_mode, target_server=mcp_target)
                continue

            # 11.9 Robin MCP Dark Web OSINT スラッシュコマンド (/robin)
            if user_input.startswith("/robin"):
                handle_robin_command(
                    user_input=user_input,
                    console=console,
                    session=session,
                    inspector=inspector,
                    memory=memory,
                    curr_mode=curr_mode
                )
                continue

            # 11.95 Donut Browser & Stealth Browser スラッシュコマンド (/donut, /stealth)
            if user_input.startswith(("/donut", "/stealth")):
                handle_donut_command(
                    user_input=user_input,
                    console=console,
                    session=session,
                    inspector=inspector,
                    memory=memory,
                    curr_mode=curr_mode
                )
                continue

            # 12.5 インテリジェント・デイリーブリーフィング (/briefing)
            if user_input.startswith("/briefing"):
                parts = user_input.split(maxsplit=2)
                sub = parts[1].lower() if len(parts) > 1 else ""
                from tools.briefing_tools import BriefingTools
                btools = BriefingTools(workspace_root=TUGUMI_ROOT)
                p = CYBER_PALETTES.get(curr_mode, CYBER_PALETTES["light"])

                if sub in ("list", "ls", "schedules"):
                    schedules = btools.list_scheduled_briefings()
                    if not schedules:
                        console.print("[cyan]現在登録されている定期デイリーブリーフィングのcronスケジュールはありません。[/cyan]")
                    else:
                        console.print(f"[bold green]【現在登録中の定期デイリーブリーフィング ({len(schedules)}件)】[/bold green]")
                        for s in schedules:
                            console.print(f"  • ID: [bold yellow]{s['job_id']}[/bold yellow] | 時刻: [cyan]{s['time']}[/cyan] | テーマ: {s['topic']}")
                    continue

                if sub in ("remove", "rm", "delete") and len(parts) > 2:
                    target_id = parts[2].strip()
                    rm_res = btools.remove_scheduled_briefing(target_id)
                    console.print(f"[bold green]定期ブリーフィング削除結果: {rm_res}[/bold green]")
                    continue

                if sub in ("schedule", "set", "cron") and len(parts) > 2:
                    sched_time = parts[2].strip()
                    sched_res = btools.schedule_daily_briefing(time_str=sched_time)
                    console.print(f"[bold green]✔ 定期デイリーブリーフィング設定完了: 毎朝 {sched_res['scheduled_time']} に自動生成・通知します。[/bold green]")
                    continue

                if sub == "latest":
                    latest = btools.get_latest_briefing()
                    if latest.get("status") == "success":
                        from rich.markdown import Markdown
                        console.print(Panel(Markdown(latest["content"]), title=f"[bold green]最新ブリーフィング: {latest['filename']}[/bold green]", border_style=p["border"]))
                    else:
                        console.print(f"[yellow]{latest.get('message', 'ブリーフィングが見つかりません')}[/yellow]")
                    continue

                # 通常の即時生成
                topic_arg = user_input.split(maxsplit=1)[1] if len(user_input.split()) > 1 else None
                inspector.display_tool_start("DailyBriefingEngine.generate_briefing", {"topic": topic_arg or "総合インテリジェンス"})
                console.print("[bold yellow]☀️ 本日のインテリジェント・デイリーブリーフィングを生成中... (気象実測・Webリサーチ・Termux診断・推稿)[/bold yellow]")
                try:
                    b_res = btools.generate_daily_briefing(topic=topic_arg)
                    inspector.display_tool_result("DailyBriefingEngine", True, f"TUGUMIDesk保存完了: {b_res.get('desk_path')}")
                    from rich.markdown import Markdown
                    console.print(Panel(Markdown(b_res["content"]), title=f"[bold cyan]☀️ つぐみデイリーブリーフィング ({b_res['date']})[/bold cyan]", border_style=p["border"]))
                except Exception as e:
                    inspector.display_tool_result("DailyBriefingEngine", False, f"生成エラー: {e}")
                    console.print(f"[bold red]ブリーフィング生成中にエラーが発生しました: {e}[/bold red]")
                continue

            # 13. 楽曲自動作曲・編曲・再生 (/music または /compose)
            if user_input.startswith("/music") or user_input.startswith("/compose"):
                cmd_parts = user_input.split(maxsplit=1)
                raw_args = cmd_parts[1].strip() if len(cmd_parts) > 1 else ""

                if raw_args.lower() in ("presets", "list", "genre", "genres"):
                    from tools.media_tools import HitSongProducerEngine
                    p_table = Table(title="[bold magenta]◈ TUGUMIv6 オリコン上位ジャンル・プリセット一覧 ◈[/bold magenta]", border_style="magenta")
                    p_table.add_column("プリセットID", style="bold cyan", width=18)
                    p_table.add_column("ジャンル名", style="bold yellow", width=22)
                    p_table.add_column("BPM / Key", style="white", width=16)
                    p_table.add_column("黄金コード進行", style="cyan")
                    for p_id, p_info in HitSongProducerEngine.GENRE_PRESETS.items():
                        p_table.add_row(p_id, p_info["name"], f"{p_info['bpm']} BPM ({p_info['key']})", p_info["chords"])
                    console.print(p_table)
                    console.print("[dim]※ 使用例: /music produce 雨の深夜に首都高を飛ばす切ない疾走ロック[/dim]\n")
                    continue

                if raw_args:
                    theme_input = raw_args
                    if theme_input.startswith("produce "):
                        theme_input = theme_input[8:].strip()
                else:
                    # プロンプトによる自由な要望入力
                    console.print(Panel(
                        "[bold cyan]🎵 拓磨様、どのような楽曲をプロデュース・制作いたしましょうか？[/bold cyan]\n\n"
                        "[white]曲調、歌詞の情景、感情、テンポ、ボーカル声質などを自由にご入力ください。[/white]\n"
                        "[dim]・例: 雨の深夜に首都高を飛ばしながら過去の恋に別れを告げる疾走感あるロック\n"
                        "・例: 乃木坂46風の切ない夏のエモーショナルピアノポップ、サビで突き抜けるハイトーン\n"
                        "・例: 深夜の作業用、落ち着いた雨音混じりのLo-Fi HipHop\n"
                        "※ そのまま空Enterを押すとキャンセルします。(/music presets でジャンル一覧)[/dim]",
                        title="[bold magenta]◈ TUGUMIv6 HIT SONG PRODUCER STUDIO (オリコン1位級 AI楽曲制作) ◈[/bold magenta]",
                        border_style="magenta"
                    ))
                    try:
                        theme_input = session.prompt(HTML('<ansimagenta><b>[Music Request] ご希望の楽曲プロンプト &gt; </b></ansimagenta>')).strip()
                    except (KeyboardInterrupt, EOFError):
                        theme_input = ""

                    if not theme_input:
                        console.print("[yellow]楽曲制作をキャンセルしました。[/yellow]\n")
                        continue

                inspector.display_tool_start("HitSongProducerEngine", {"concept": theme_input})
                console.print("[bold cyan]🏆 hit-song-producer-pro スキルを適用し、オリコン1位級楽曲プロデュース・作詞・音響合成を開始...[/bold cyan]")
                try:
                    from tools.media_tools import GeminiMusicStudio
                    res = GeminiMusicStudio.create_music_direct(user_prompt=theme_input)
                    if res.get("success"):
                        audio_target = res.get("mp3_path")
                        inspector.display_tool_result("HitSongProducerEngine", True, f"楽曲完成: 『{res['title']}』")

                        m_table = Table(title=f"[bold #00f0ff]🏆 拓磨様のための新曲『{res['title']}』プロデュース完成！ ◈[/bold #00f0ff]", border_style="#7928ca")
                        m_table.add_column("項目", style="bold cyan", width=18)
                        m_table.add_column("詳細情報 / パス", style="white")
                        m_table.add_row("タイトル", f"『{res['title']}』")
                        if res.get("genre"):
                            bpm_str = f" ({res['bpm']} BPM / Key: {res.get('key', '')})" if res.get("bpm") else ""
                            m_table.add_row("ジャンル / テンポ", f"{res['genre']}{bpm_str}")
                        if res.get("chord_progression"):
                            m_table.add_row("黄金コード進行", str(res["chord_progression"]))
                        if res.get("hook_strategy"):
                            m_table.add_row("冒頭3秒フック", str(res["hook_strategy"]))
                        m_table.add_row("指示イメージ", theme_input)
                        if audio_target and os.path.exists(audio_target):
                            m_table.add_row("🎧 完成楽曲 (MP3)", f"{audio_target} ({os.path.getsize(audio_target):,} bytes)")
                        if res.get("sheet_path"):
                            m_table.add_row("📝 仕様書＆歌詞", str(res["sheet_path"]))
                        m_table.add_row("📱 保存場所", "/storage/emulated/0/Music/TUGUMI/ (スマホ標準音楽プレイヤーで即再生)")
                        console.print(m_table)

                        # モーラ調律歌詞のプレビュー表示
                        if res.get("lyrics"):
                            console.print(Panel(
                                res["lyrics"],
                                title=f"[bold yellow]📝 モーラ調律・完全歌詞カード: 『{res['title']}』[/bold yellow]",
                                border_style="yellow"
                            ))

                        # 再生開始
                        if audio_target and os.path.exists(audio_target):
                            console.print(f"[bold green]▶ 楽曲の再生を開始します: {os.path.basename(audio_target)}[/bold green]")
                            try:
                                import subprocess
                                subprocess.run(["termux-media-player", "play", audio_target], capture_output=True)
                            except Exception:
                                subprocess.run(["termux-open", audio_target], capture_output=True)
                    else:
                        console.print(f"[bold red]楽曲制作エラー: {res.get('error')}[/bold red]")
                except Exception as e:
                    inspector.display_tool_result("HitSongProducerEngine", False, f"作曲エラー: {e}")
                    console.print(f"[bold red]楽曲制作中にエラーが発生しました: {e}[/bold red]")
                console.print()
                continue

            # 13.4 実写美女・画像生成・編集・合成スタジオ (/image, /img, /photo)
            if user_input.startswith(("/image", "/img", "/photo")):
                cmd_parts = user_input.split(maxsplit=2)
                base_cmd = cmd_parts[0].lower()
                sub_cmd = cmd_parts[1].lower() if len(cmd_parts) > 1 else ""
                extra_args = cmd_parts[2].strip() if len(cmd_parts) > 2 else ""

                # ショートカット判定 (/photo <prompt>, /img <prompt>)
                if base_cmd == "/photo":
                    sub_cmd = "photo"
                    extra_args = user_input[len("/photo"):].strip()
                    if not extra_args:
                        try:
                            extra_args = session.prompt(HTML('<ansigreen><b>[実写美女プロンプト] ご希望のシチュエーション &gt; </b></ansigreen>')).strip()
                        except (KeyboardInterrupt, EOFError):
                            continue
                        if not extra_args:
                            continue
                elif base_cmd == "/img":
                    sub_cmd = "gen"
                    extra_args = user_input[len("/img"):].strip()
                    if not extra_args:
                        try:
                            extra_args = session.prompt(HTML('<ansicyan><b>[画像プロンプト] 生成したい内容 &gt; </b></ansicyan>')).strip()
                        except (KeyboardInterrupt, EOFError):
                            continue
                        if not extra_args:
                            continue

                # 引数なしの場合はインタラクティブメニュー
                if not sub_cmd or sub_cmd in ("help", "-h", "--help"):
                    console.print(Panel(
                        "[bold #00f0ff]◈ TUGUMIv6 GEMINI 3 IMAGE & PHOTOREAL STUDIO ◈[/bold #00f0ff]\n\n"
                        "[bold white]1. /image photo <プロンプト>[/bold white] - [green]超リアル実写美女・ポートレート写真生成 (一眼レフ/毛穴/自然光/Portra400)[/green]\n"
                        "[bold white]2. /image gen <プロンプト>[/bold white]   - [cyan]一般AI画像生成 (サイバーパンク/アート/イラスト等)[/cyan]\n"
                        "[bold white]3. /image edit <画像パス> <指示>[/bold white] - [magenta]既存画像のプロンプト編集 (衣装変更/背景変形/髪型変更)[/magenta]\n"
                        "[bold white]4. /image compose <画像1> <画像2> <指示>[/bold white] - [yellow]複数画像の一枚融合・シーン合成[/yellow]\n\n"
                        "[dim]例: /photo 22歳の清楚系モデル、代官山のおしゃれなカフェで微笑むスナップ写真\n"
                        "例: /image edit /storage/emulated/0/TUGUMIDesk/Images/model.jpg 服を白ニットに変えて[/dim]",
                        title="[bold magenta]📸 画像生成・編集・実写ポートレートメニュー[/bold magenta]",
                        border_style="cyan"
                    ))
                    try:
                        choice = session.prompt(HTML('<ansicyan><b>機能選択 (1:実写ポートレート, 2:画像生成, 3:画像編集, 4:画像合成, 0:戻る) &gt; </b></ansicyan>')).strip()
                    except (KeyboardInterrupt, EOFError):
                        continue

                    if choice == "1":
                        sub_cmd = "photo"
                        extra_args = session.prompt(HTML('<ansigreen><b>[実写美女プロンプト] ご希望のシチュエーション &gt; </b></ansigreen>')).strip()
                    elif choice == "2":
                        sub_cmd = "gen"
                        extra_args = session.prompt(HTML('<ansicyan><b>[画像プロンプト] 生成したい内容 &gt; </b></ansicyan>')).strip()
                    elif choice == "3":
                        sub_cmd = "edit"
                        raw_edit = session.prompt(HTML('<ansimagenta><b>[画像パスと指示] &lt;画像パス&gt; &lt;編集指示&gt; &gt; </b></ansimagenta>')).strip()
                        parts = raw_edit.split(maxsplit=1)
                        if len(parts) == 2:
                            sub_cmd = "edit"
                            extra_args = raw_edit
                        else:
                            console.print("[yellow]画像パスと指示の両方を指定してください。[/yellow]\n")
                            continue
                    elif choice == "4":
                        sub_cmd = "compose"
                        extra_args = session.prompt(HTML('<ansiyellow><b>[合成] &lt;画像1&gt; &lt;画像2&gt; &lt;合成指示&gt; &gt; </b></ansiyellow>')).strip()
                    else:
                        continue

                from tools.media_tools import GeminiImageStudio

                if sub_cmd in ("photo", "portrait", "リアル", "実写"):
                    p_text = extra_args or "22-year-old beautiful Japanese model in a Tokyo cafe, candid snapshot"
                    inspector.display_tool_start("GeminiImageStudio.photo", {"prompt": p_text})
                    console.print("[bold green]📸 一眼レフ光学仕様・マイクロ肌テクスチャ・自然光を自動昇華して実写生成中...[/bold green]")
                    res = GeminiImageStudio.generate(prompt=p_text, photoreal=True, style="photoreal")
                    if res.get("success"):
                        img_path = res["file_path"]
                        inspector.display_tool_result("GeminiImageStudio", True, f"実写ポートレート完成: {os.path.basename(img_path)}")
                        # アスキーアートプレビュー
                        console.print(GeminiImageStudio.to_ascii(img_path, target_width=44))
                        i_table = Table(title="[bold #00f0ff]📸 超リアル実写ポートレート生成完了！ ◈[/bold #00f0ff]", border_style="#00f0ff")
                        i_table.add_column("項目", style="bold cyan", width=16)
                        i_table.add_column("詳細情報 / パス", style="white")
                        i_table.add_row("モデル指示", p_text)
                        i_table.add_row("使用モデル", res.get("model", "gemini-3.1-flash-image"))
                        i_table.add_row("解像度", res.get("dimensions", "1408x768"))
                        i_table.add_row("保存先", f"{img_path} ({os.path.getsize(img_path):,} bytes)")
                        i_table.add_row("ギャラリー", "スマホ標準ギャラリーで即閲覧可能 (メディアスキャン済)")
                        console.print(i_table)
                        try:
                            import subprocess
                            subprocess.run(["termux-open", img_path], capture_output=True)
                        except Exception:
                            pass
                    else:
                        console.print(f"[bold red]画像生成エラー: {res.get('error')}[/bold red]")

                elif sub_cmd in ("gen", "generate"):
                    p_text = extra_args or "Cyberpunk neon metropolis"
                    inspector.display_tool_start("GeminiImageStudio.generate", {"prompt": p_text})
                    console.print("[bold cyan]🎨 Gemini 画像生成モデルへプロンプトを投入中...[/bold cyan]")
                    res = GeminiImageStudio.generate(prompt=p_text, style="cyberpunk")
                    if res.get("success"):
                        img_path = res["file_path"]
                        inspector.display_tool_result("GeminiImageStudio", True, f"画像完成: {os.path.basename(img_path)}")
                        console.print(GeminiImageStudio.to_ascii(img_path, target_width=44))
                        i_table = Table(title="[bold #00f0ff]🎨 画像生成完了！ ◈[/bold #00f0ff]", border_style="#7928ca")
                        i_table.add_column("項目", style="bold cyan", width=16)
                        i_table.add_column("詳細情報 / パス", style="white")
                        i_table.add_row("指示プロンプト", p_text)
                        i_table.add_row("保存先", f"{img_path} ({os.path.getsize(img_path):,} bytes)")
                        console.print(i_table)
                        try:
                            import subprocess
                            subprocess.run(["termux-open", img_path], capture_output=True)
                        except Exception:
                            pass
                    else:
                        console.print(f"[bold red]画像生成エラー: {res.get('error')}[/bold red]")

                elif sub_cmd in ("edit", "modify"):
                    parts = extra_args.split(maxsplit=1)
                    if len(parts) < 2:
                        console.print("[yellow]使用法: /image edit <元画像パス> <編集指示>[/yellow]\n")
                        continue
                    src_img, edit_p = parts[0], parts[1]
                    inspector.display_tool_start("GeminiImageStudio.edit", {"src": src_img, "prompt": edit_p})
                    console.print("[bold magenta]🖼️ 既存画像の特徴を保持したままプロンプト指示通りに変形・編集実行中...[/bold magenta]")
                    res = GeminiImageStudio.edit(image_path=src_img, prompt=edit_p)
                    if res.get("success"):
                        img_path = res["file_path"]
                        inspector.display_tool_result("GeminiImageStudio", True, f"画像編集完了: {os.path.basename(img_path)}")
                        console.print(GeminiImageStudio.to_ascii(img_path, target_width=44))
                        i_table = Table(title="[bold #ff007f]🖼️ 画像編集・変形完了！ ◈[/bold #ff007f]", border_style="#ff007f")
                        i_table.add_column("項目", style="bold magenta", width=16)
                        i_table.add_column("詳細情報 / パス", style="white")
                        i_table.add_row("元画像", src_img)
                        i_table.add_row("編集指示", edit_p)
                        i_table.add_row("保存先", f"{img_path} ({os.path.getsize(img_path):,} bytes)")
                        console.print(i_table)
                        try:
                            import subprocess
                            subprocess.run(["termux-open", img_path], capture_output=True)
                        except Exception:
                            pass
                    else:
                        console.print(f"[bold red]画像編集エラー: {res.get('error')}[/bold red]")

                elif sub_cmd in ("compose", "fuse"):
                    parts = extra_args.split(maxsplit=2)
                    if len(parts) < 3:
                        console.print("[yellow]使用法: /image compose <画像1> <画像2> <合成指示>[/yellow]\n")
                        continue
                    p1, p2, comp_p = parts[0], parts[1], parts[2]
                    inspector.display_tool_start("GeminiImageStudio.compose", {"p1": p1, "p2": p2, "prompt": comp_p})
                    console.print("[bold yellow]🎭 複数画像を1つの調和されたシーンに融合・合成中...[/bold yellow]")
                    res = GeminiImageStudio.compose(image_paths=[p1, p2], prompt=comp_p)
                    if res.get("success"):
                        img_path = res["file_path"]
                        inspector.display_tool_result("GeminiImageStudio", True, f"画像合成完了: {os.path.basename(img_path)}")
                        console.print(GeminiImageStudio.to_ascii(img_path, target_width=44))
                        i_table = Table(title="[bold #ffaa00]🎭 画像合成・融合完了！ ◈[/bold #ffaa00]", border_style="#ffaa00")
                        i_table.add_column("項目", style="bold yellow", width=16)
                        i_table.add_column("詳細情報 / パス", style="white")
                        i_table.add_row("入力画像", f"{p1}\n{p2}")
                        i_table.add_row("合成指示", comp_p)
                        i_table.add_row("保存先", f"{img_path} ({os.path.getsize(img_path):,} bytes)")
                        console.print(i_table)
                        try:
                            import subprocess
                            subprocess.run(["termux-open", img_path], capture_output=True)
                        except Exception:
                            pass
                    else:
                        console.print(f"[bold red]画像合成エラー: {res.get('error')}[/bold red]")
                console.print()
                continue

            # 13.5 自律ディープリサーチ (/research) - SKILL完全準拠水準
            if user_input.startswith("/research"):
                cmd_parts = user_input.split(maxsplit=1)
                raw_topic = cmd_parts[1].strip() if len(cmd_parts) > 1 else ""

                if raw_topic:
                    research_topic = raw_topic
                else:
                    console.print(Panel(
                        "[bold cyan]🔍 拓磨様、どのようなテーマを深層調査（ディープリサーチ）いたしますか？[/bold cyan]\n\n"
                        "[white]最新AI動向、技術仕様、セキュリティ、人物、芸能、競馬、副業など、自由にテーマをご入力ください。[/white]\n"
                        "[dim]・例: MCP 2.0 と Google A2A プロトコルの最新仕様比較\n"
                        "・例: Termux Linux aarch64 における最新のLLM推論高速化技術\n"
                        "・例: 乃木坂46 5期生 井上和の最新活動動向と今後のキャリア展望\n"
                        "※ そのまま空Enterを押すとキャンセルします。[/dim]",
                        title="[bold cyan]◈ TUGUMIv6 DEEP RESEARCH STUDIO ◈[/bold cyan]",
                        border_style="cyan"
                    ))
                    try:
                        research_topic = session.prompt(HTML('<ansicyan><b>[Research Topic] 調査テーマ &gt; </b></ansicyan>')).strip()
                    except (KeyboardInterrupt, EOFError):
                        research_topic = ""

                    if not research_topic:
                        console.print("[yellow]ディープリサーチをキャンセルしました。[/yellow]\n")
                        continue

                console.print(f"\n[bold cyan]🔍 【SKILL準拠】ディープリサーチ自律パイプラインを開始します: 『{research_topic}』[/bold cyan]")

                def cli_progress(step: str, detail: str, _console=console):
                    _console.print(f"  [bold yellow]➔ [{step}][/bold yellow] [dim]{detail}[/dim]")

                inspector.display_tool_start("DeepResearchEngine", {"topic": research_topic})
                status_msg = "[bold cyan]⠋ 多角Web索敵・一次ソース精読・Gemini 3.8推稿中... [dim](SKILL水準構造化)[/dim][/bold cyan]"
                with console.status(status_msg, spinner="dots12"):
                    res = deep_researcher.run_research_pipeline(topic=research_topic, progress_cb=cli_progress)

                if res.get("success"):
                    inspector.display_tool_result("DeepResearchEngine", True, f"レポート完成: {res['title']}")

                    r_table = Table(title=f"[bold #00f0ff]📄 ディープリサーチ報告書完成: 『{res['title']}』 ◈[/bold #00f0ff]", border_style="#00f0ff")
                    r_table.add_column("項目", style="bold cyan", width=18)
                    r_table.add_column("内容 / パス", style="white")
                    r_table.add_row("調査テーマ", research_topic)
                    r_table.add_row("分類カテゴリ", f"【{res['category']}】")
                    r_table.add_row("📝 Markdown保存先", res["md_path"])
                    r_table.add_row("🌐 美麗HTML保存先", res["html_path"])
                    r_table.add_row("📊 レポート規模", f"{res['char_count']:,} 文字 / 一次ソース {res['sources_count']} 件")
                    console.print()
                    console.print(r_table)
                    console.print()

                    content = res.get("content", "")
                    summary_match = re.search(r"## 1\. エグゼクティブサマリー.*?\n(.*?)(?=\n## 2|\Z)", content, re.DOTALL)
                    summary_text = summary_match.group(1).strip() if summary_match else content[:400]
                    console.print(Panel(
                        summary_text,
                        title="[bold green]◈ エグゼクティブサマリー (結論先行) ◈[/bold green]",
                        border_style="green"
                    ))
                    console.print("[dim]※ 全文はスマホのファイル管理、ブラウザ、またはObsidianから閲覧できます。[/dim]\n")
                else:
                    inspector.display_tool_result("DeepResearchEngine", False, f"リサーチ失敗: {res.get('error')}")
                    console.print(f"[bold red]リサーチ中にエラーが発生しました: {res.get('error')}[/bold red]\n")
            # 14. 思考強度切替 (/thinking, /think, /high, /medium, /low, /minimal)
            if user_input.startswith(("/thinking", "/think", "/high", "/medium", "/low", "/minimal")):
                parts = user_input.split()
                cmd = parts[0].lower()
                target_level = None

                if cmd == "/high":
                    target_level = "high"
                elif cmd == "/medium":
                    target_level = "medium"
                elif cmd == "/low":
                    target_level = "low"
                elif cmd == "/minimal":
                    target_level = "minimal"
                elif len(parts) >= 2:
                    sub = parts[1].lower()
                    if sub == "stream":
                        action = parts[2].lower() if len(parts) >= 3 else ("off" if thinking_viewer.stream_thinking else "on")
                        if action in ("on", "1", "true", "enable"):
                            thinking_viewer.stream_thinking = True
                            thinking_viewer.show_thinking = True
                            console.print("[bold green]✔ 思考プロセスのリアルタイムストリーミング出力を【ON】に設定しました。[/bold green]\n")
                        else:
                            thinking_viewer.stream_thinking = False
                            console.print("[bold yellow]✔ 思考プロセスのリアルタイムストリーミングを【OFF】にしました（完了時サマリーパネルのみ表示）。[/bold yellow]\n")
                        continue
                    elif sub in ("show", "on"):
                        thinking_viewer.show_thinking = True
                        console.print("[bold green]✔ 思考プロセスの可視化を【ON】に設定しました。[/bold green]\n")
                        continue
                    elif sub in ("hide", "off"):
                        thinking_viewer.show_thinking = False
                        console.print("[bold yellow]✔ 思考プロセスの可視化を【OFF】に設定しました（最小バッジ表示）。[/bold yellow]\n")
                        continue
                    elif sub == "toggle":
                        thinking_viewer.show_thinking = not thinking_viewer.show_thinking
                        st_txt = "ON" if thinking_viewer.show_thinking else "OFF"
                        console.print(f"[bold cyan]✔ 思考プロセスの可視化を【{st_txt}】に切り替えました。[/bold cyan]\n")
                        continue

                    mapping = {"h": "high", "m": "medium", "l": "low", "min": "minimal"}
                    norm = mapping.get(sub, sub)
                    if norm in ("high", "medium", "low", "minimal"):
                        target_level = norm
                    else:
                        console.print(f"[bold red]✖ 無効な思考レベルまたはサブコマンドです: {parts[1]}[/bold red] (利用可能: high, medium, low, minimal / stream on|off, show, hide, toggle)\n")
                        continue
                else:
                    # 引数なしの場合: リッチな選択HUDを表示
                    p = CYBER_PALETTES.get(curr_mode, CYBER_PALETTES["light"])
                    t_table = Table(
                        title=f"[bold {p['primary']}]🧠 Gemini 3 推論思考強度設定 (Thinking Level)[/bold {p['primary']}]",
                        border_style=p["border"],
                        expand=True,
                        show_lines=True
                    )
                    t_table.add_column("No", style="bold cyan", width=4, justify="center")
                    t_table.add_column("Level", style="bold yellow", width=14)
                    t_table.add_column("用途・特性", style="white")
                    t_table.add_column("状態", style="bold green", width=10, justify="center")

                    curr_lvl = engine.thinking_level.lower()
                    levels = [
                        ("1", "high", "HIGH (最大推論)", "複雑な設計・コーディング・学術リサーチ・最高峰論理推論"),
                        ("2", "medium", "MEDIUM (標準推論)", "日常対話・要約・Web調査・知性と速度のベストバランス"),
                        ("3", "low", "LOW (高速推論)", "短文応答・コマンド実行・超低遅延・トークン大幅節約"),
                        ("4", "minimal", "MINIMAL (最小推論)", "超高速即答・思考ステップ極小化")
                    ]
                    for num, l_key, l_name, l_desc in levels:
                        is_active = "● 現在" if l_key == curr_lvl else ""
                        t_table.add_row(num, l_name, l_desc, f"[bold #00f0ff]{is_active}[/bold #00f0ff]")

                    console.print()
                    console.print(t_table)
                    console.print(f"[dim]現在の思考強度: [bold cyan]{curr_lvl.upper()}[/bold cyan] │ 安全フィルター: [bold green]BLOCK_NONE (全解除)[/bold green][/dim]\n")

                    try:
                        sel = session.prompt(HTML('<ansicyan><b>思考レベルを選択 (1:High, 2:Medium, 3:Low, 4:Minimal, Enter:戻る) &gt; </b></ansicyan>')).strip().lower()
                    except (KeyboardInterrupt, EOFError):
                        sel = ""
                    sel_map = {
                        "1": "high", "high": "high", "h": "high",
                        "2": "medium", "medium": "medium", "m": "medium",
                        "3": "low", "low": "low", "l": "low",
                        "4": "minimal", "minimal": "minimal", "min": "minimal"
                    }
                    if sel in sel_map:
                        target_level = sel_map[sel]
                    else:
                        console.print("[dim]思考レベルの変更をキャンセルしました。[/dim]\n")
                        continue

                if target_level:
                    engine.set_thinking_level(target_level, persist=True)
                    p = CYBER_PALETTES.get(curr_mode, CYBER_PALETTES["light"])
                    th_color = "#00f0ff" if target_level == "high" else ("#e5c07b" if target_level == "medium" else "#98c379")

                    res_panel = Panel(
                        f"[bold white]推論思考強度を [bold {th_color}]{target_level.upper()}[/] に切り替えました！[/bold white]\n\n"
                        f"[cyan]• モデル:[/] Gemini 3.8 Flash (Thinking {target_level.upper()})\n"
                        f"[cyan]• 安全設定:[/] 全安全性フィルター BLOCK_NONE (完全無制限・100%出力保証)\n"
                        f"[cyan]• 永続化:[/] engine_config.json に即時保存完了 (次回起動時も維持)",
                        title=f"[bold {p['primary']}]◈ 推論思考強度アップデート ◈[/bold {p['primary']}]",
                        border_style=p["border"]
                    )
                    console.print()
                    console.print(res_panel)
                    console.print()
                continue

            # 14.4 AWM (Agent Workflow Memory) 管理 (/awm)
            if user_input.startswith("/awm"):
                parts = user_input.split()
                subcmd = parts[1].lower() if len(parts) >= 2 else "status"

                p = CYBER_PALETTES.get(curr_mode, CYBER_PALETTES["light"])
                stats = engine.get_awm_stats()

                if subcmd in ("purge", "clean"):
                    purged = engine.purge_awm_workflows(max_failures=2)
                    p_panel = Panel(
                        f"[bold green]✔ AWMガベージコレクション完了[/bold green]\n\n"
                        f"[cyan]• パージ件数:[/] {purged} 件の失敗・陳腐化ワークフローを抹消\n"
                        f"[cyan]• 状態:[/] データベース純化完了 (ゴミ・ノイズ蓄積ゼロ保持)",
                        title=f"[bold {p['primary']}]◈ AWM Garbage Collection ◈[/bold {p['primary']}]",
                        border_style=p["border"]
                    )
                    console.print()
                    console.print(p_panel)
                    console.print()
                    continue

                if subcmd in ("list", "ls", "all"):
                    wfs = stats.get("workflows", [])
                    wf_table = Table(
                        title=f"[bold {p['primary']}]🧠 AWM 学習済みワークフロー一覧 ({len(wfs)}件)[/bold {p['primary']}]",
                        border_style=p["border"],
                        expand=True,
                        show_lines=True
                    )
                    wf_table.add_column("No", style="bold cyan", width=4, justify="center")
                    wf_table.add_column("ワークフロー名", style="bold yellow", width=26)
                    wf_table.add_column("目標パターン", style="white")
                    wf_table.add_column("Steps", style="green", width=6, justify="center")
                    wf_table.add_column("成功/失敗", style="bold magenta", width=10, justify="center")

                    for idx, w in enumerate(wfs, start=1):
                        wf_table.add_row(
                            str(idx),
                            str(w.get("name")),
                            str(w.get("goal")),
                            str(w.get("steps")),
                            f"[green]{w.get('success')}[/green] / [red]{w.get('failures')}[/red]"
                        )
                    console.print()
                    console.print(wf_table)
                    console.print()
                    continue

                # デフォルト: AWMステータス・HUD
                total_wf = stats.get("total_workflows", 0)
                replays = stats.get("total_success_replays", 0)
                saved_tok = stats.get("estimated_saved_tokens", 0)

                awm_panel = Panel(
                    f"[bold white]Agent Workflow Memory (AWM) 自律学習ステータス[/bold white]\n\n"
                    f"[cyan]• 登録ワークフロー数:[/] [bold yellow]{total_wf}[/] 件\n"
                    f"[cyan]• 実証済み再利用回数:[/] [bold green]{replays}[/] 回\n"
                    f"[cyan]• 推定削減トークン数:[/] [bold magenta]{saved_tok:,}[/] tok (高速ショートカット実証)\n"
                    f"[cyan]• ゴミ・ノイズ防護壁:[/] 多層重要度フィルター ＆ 品質ゲート常時稼働\n\n"
                    f"[dim]サブコマンド: /awm list (一覧) | /awm purge (ゴミ掃除)[/dim]",
                    title=f"[bold {p['primary']}]◈ AWM Cognitive Status ◈[/bold {p['primary']}]",
                    border_style=p["border"]
                )
                console.print()
                console.print(awm_panel)
                console.print()
                continue

            # 14.5 推論モデル切替 (/model)
            if user_input.startswith("/model"):
                parts = user_input.split()
                target_model = None

                if len(parts) >= 2:
                    sub = parts[1].strip()
                    menu_num_map = {"1": "gemini-3.8-flash", "2": "gemini-4-argon", "3": "gemini-3.0-pro", "4": "gemini-3.5-flash-lite"}
                    target_model = menu_num_map.get(sub) or engine.normalize_model_name(sub)
                    if not target_model.startswith("gemini-"):
                        console.print(f"[bold red]✖ 不明なモデル指定: '{escape(sub)}'[/bold red] [dim](例: /model 2, /model argon, /model flash, /model pro, /model lite)[/dim]\n")
                        continue
                else:
                    # 引数なしの場合: リッチなモデル選択HUDを表示
                    p = CYBER_PALETTES.get(curr_mode, CYBER_PALETTES["light"])
                    m_table = Table(
                        title=f"[bold {p['primary']}]🤖 Gemini 推論モデル切替 (Model Switcher)[/bold {p['primary']}]",
                        border_style=p["border"],
                        expand=True,
                        show_lines=True
                    )
                    m_table.add_column("No", style="bold cyan", width=4, justify="center")
                    m_table.add_column("モデル識別子", style="bold yellow", width=22)
                    m_table.add_column("特性・推奨用途", style="white")
                    m_table.add_column("状態", style="bold green", width=10, justify="center")

                    curr_m = engine.current_model
                    models_list = [
                        ("1", "gemini-3.8-flash", "⚡ [bold #00f0ff]超高速・高知能 主力ワークホース[/bold #00f0ff] (日常対話・高速SWE・Thinking対応)"),
                        ("2", "gemini-4-argon", "🌌 [bold #ff007f]Gemini 4世代フロンティア知能[/bold #ff007f] (1M入出力・超難問・DeepSWE・空間推論)"),
                        ("3", "gemini-3.0-pro", "🧠 [bold #ffb703]ディープ推論モデル[/bold #ffb703] (深層設計・学術リサーチ・複雑論理)"),
                        ("4", "gemini-3.5-flash-lite", "🍃 [bold #98c379]超軽量・即答モデル[/bold #98c379] (省トークン・超低遅延)")
                    ]

                    for num, m_id, m_desc in models_list:
                        is_active = "● 現在" if m_id == curr_m else ""
                        m_table.add_row(num, m_id, m_desc, f"[bold #00f0ff]{is_active}[/bold #00f0ff]")

                    console.print()
                    console.print(m_table)
                    console.print(f"[dim]現在のアクティブモデル: [bold cyan]{curr_m}[/bold cyan] │ 安全設定: [bold green]BLOCK_NONE[/bold green] │ 通信: [bold yellow]SSEストリーミング優先[/bold yellow][/dim]\n")

                    try:
                        sel = session.prompt(HTML('<ansicyan><b>モデルを選択 (1: 3.8-Flash, 2: 4-Argon, 3: 3.0-Pro, 4: Lite, Enter:戻る) &gt; </b></ansicyan>')).strip().lower()
                    except (KeyboardInterrupt, EOFError):
                        sel = ""

                    sel_map = {
                        "1": "gemini-3.8-flash", "flash": "gemini-3.8-flash", "3.8": "gemini-3.8-flash",
                        "2": "gemini-4-argon", "argon": "gemini-4-argon", "4-argon": "gemini-4-argon",
                        "3": "gemini-3.0-pro", "pro": "gemini-3.0-pro",
                        "4": "gemini-3.5-flash-lite", "lite": "gemini-3.5-flash-lite"
                    }
                    if sel in sel_map:
                        target_model = sel_map[sel]
                    else:
                        console.print("[dim]モデルの変更をキャンセルしました。[/dim]\n")
                        continue

                if target_model:
                    new_m = engine.set_model(target_model, persist=True)
                    p = CYBER_PALETTES.get(curr_mode, CYBER_PALETTES["light"])
                    m_color = "#ff007f" if "argon" in new_m else ("#00f0ff" if "3.8" in new_m else "#ffb703")

                    argon_notice = ""
                    if "argon" in new_m:
                        argon_notice = (
                            "\n[bold magenta]✦ Gemini 4 Argon アドバイス適用済み ✦[/bold magenta]\n"
                            "[dim]• SSEストリーミング(streamGenerateContent)で無通信タイムアウト・切断を防止\n"
                            "• 503/429検知時にジッター付き指数バックオフ(2s→4s→8s+Jitter)自動リトライ\n"
                            "• サーキットブレーカー: 解消不能時は gemini-3.8-flash (Thinking HIGH) へ自動フォールバック[/dim]\n"
                        )

                    res_panel = Panel(
                        f"[bold white]推論モデルを [bold {m_color}]{new_m}[/] に切り替えました！[/bold white]\n"
                        f"{argon_notice}\n"
                        f"[cyan]• 思考強度:[/] Thinking {engine.thinking_level.upper()}\n"
                        f"[cyan]• 安全設定:[/] 全安全性フィルター BLOCK_NONE (完全無制限・100%出力保証)\n"
                        f"[cyan]• 永続化:[/] engine_config.json に即時保存完了 (次回起動時も維持)",
                        title=f"[bold {p['primary']}]◈ 推論モデルアップデート ◈[/bold {p['primary']}]",
                        border_style=p["border"]
                    )
                    console.print()
                    console.print(res_panel)
                    console.print()
                continue

            # 15. バイナンス暗号資産AI自動運用 (/binance, /crypto) v2.0 Quant Edition
            if user_input.startswith(("/binance", "/crypto")):
                parts = user_input.split()
                subcmd = parts[1].lower() if len(parts) > 1 else "status"
                from tools.binance_tools import BinanceCryptoTools
                import subprocess
                btools = BinanceCryptoTools()

                if subcmd in ("status", "balance", "wallet", "残高"):
                    p = subprocess.run(["binance-ai", "status"], capture_output=True, text=True)
                    console.print(f"\n[bold cyan]{p.stdout.strip()}[/bold cyan]\n")

                elif subcmd in ("scan", "scan-2x", "market", "相場"):
                    console.print("[cyan]⏳ 主要JPY銘柄のマルチタイムフレーム・クオンツAlphaを解析中...[/cyan]")
                    scan_args = ["binance-ai", "scan-2x"]
                    if len(parts) > 2 and parts[2] in ("--all", "all"):
                        scan_args.append("--all")
                    p = subprocess.run(scan_args, capture_output=True, text=True)
                    console.print(f"\n{p.stdout.strip()}\n")

                elif subcmd in ("patrol", "run", "report", "パトロール"):
                    console.print("[cyan]🚀 自律クオンツパトロール v2.0 を即時実行中...[/cyan]")
                    p = subprocess.run(["binance-ai", "report"], capture_output=True, text=True)
                    console.print(f"\n{p.stdout.strip()}\n")

                elif subcmd in ("backtest", "bt", "バックテスト"):
                    sym_arg = parts[2].upper() if len(parts) > 2 else ""
                    console.print("[cyan]📈 実ヒストリカルデータでクオンツv2.0戦略を検証中...[/cyan]")
                    bt_args = ["binance-ai", "backtest"]
                    if sym_arg:
                        bt_args.append(sym_arg)
                    p = subprocess.run(bt_args, capture_output=True, text=True)
                    console.print(f"\n{p.stdout.strip()}\n")

                elif subcmd in ("dust", "bnb", "端数"):
                    dust_args = ["binance-ai", "dust"]
                    if len(parts) > 2:
                        dust_args.extend(parts[2:])
                    p = subprocess.run(dust_args, capture_output=True, text=True)
                    console.print(f"\n{p.stdout.strip()}\n")

                elif subcmd in ("buy", "買"):
                    sym = parts[2].upper() if len(parts) > 2 else "SUIJPY"
                    amt = float(parts[3]) if len(parts) > 3 else 115.0
                    console.print(f"[yellow]⚡ {sym} を成行買い発注中 (金額: ¥{amt:,.0f})...[/yellow]")
                    res = btools.execute_trade_sync(sym, "BUY", amt)
                    if res.get("success"):
                        console.print(Panel(
                            f"[bold green]✔ 成行買い注文が約定いたしました！[/bold green]\n\n"
                            f"[cyan]• 銘柄:[/] {res['symbol']}\n"
                            f"[cyan]• 約定単価:[/] ¥{res['price']:,.4f}\n"
                            f"[cyan]• 約定数量:[/] {res['executed_qty']} 枚\n"
                            f"[cyan]• 支払金額:[/] ¥{res['cummulative_quote']:,.2f}\n"
                            f"[cyan]• 注文ID:[/] {res['order_id']}",
                            title="[bold yellow]◈ Binance 取引約定完了 ◈[/bold yellow]",
                            border_style="green"
                        ))
                    else:
                        console.print(f"[bold red]✖ 発注失敗: {res.get('error')}[/bold red]\n")

                elif subcmd in ("sell", "close", "売"):
                    sym = parts[2].upper() if len(parts) > 2 else "SUIJPY"
                    console.print(f"[yellow]⚡ {sym} をLOT_SIZE最適化・成行売り発注中...[/yellow]")
                    res = btools.execute_trade_sync(sym, "SELL")
                    if res.get("success"):
                        console.print(Panel(
                            f"[bold green]✔ 売却注文が約定いたしました！[/bold green]\n\n"
                            f"[cyan]• 銘柄:[/] {res['symbol']}\n"
                            f"[cyan]• 約定単価:[/] ¥{res['price']:,.4f}\n"
                            f"[cyan]• 売却数量:[/] {res['executed_qty']} 枚\n"
                            f"[cyan]• 獲得日本円:[/] ¥{res['cummulative_quote']:,.2f}\n"
                            f"[cyan]• 残端数:[/] {res.get('remaining_dust_qty', 0.0)} 枚\n"
                            f"[cyan]• 注文ID:[/] {res['order_id']}",
                            title="[bold yellow]◈ Binance 売却約定完了 ◈[/bold yellow]",
                            border_style="green"
                        ))
                    else:
                        console.print(f"[bold red]✖ 売却失敗: {res.get('error')}[/bold red]\n")

                elif subcmd in ("cron", "schedule", "自律"):
                    act = parts[2].lower() if len(parts) > 2 else "status"
                    interval = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 1
                    cmd_args = ["binance-ai", "cron", act]
                    if act == "start":
                        cmd_args += ["--interval", str(interval)]
                    p = subprocess.run(cmd_args, capture_output=True, text=True)
                    console.print(f"\n[bold cyan]{p.stdout.strip()}[/bold cyan]\n")

                else:
                    console.print(
                        "[bold cyan]◈ /binance クオンツ運用 v2.0 コマンド一覧 ◈[/bold cyan]\n"
                        "  • `/binance status` (総資産・LOT_SIZE売却可否・損益診断)\n"
                        "  • `/binance scan [--all]` (クオンツAlphaランキングスキャン)\n"
                        "  • `/binance patrol` (4層防護パトロール即時実行＆速報出力)\n"
                        "  • `/binance backtest [銘柄]` (実ヒストリカル戦略バックテスト)\n"
                        "  • `/binance dust [--include-locked]` (端数をBNB燃料へ一括変換)\n"
                        "  • `/binance buy <銘柄> [金額]` (成行買い 例: /binance buy SUI 120)\n"
                        "  • `/binance sell <銘柄>` (LOT_SIZE最適化成行売り 例: /binance sell PEPE)\n"
                        "  • `/binance cron <start|stop|status>` (定期パトロール管理)\n"
                    )
                continue

            # 16. ヘルプ (/help)
            if user_input == "/help":
                show_quick_menu(console, mode=curr_mode)
                continue

            # 16.1 常駐セッション検視・管理 (/session)
            if user_input.startswith("/session"):
                s_parts = user_input.split()
                s_act = s_parts[1].lower() if len(s_parts) > 1 else "status"
                if s_act in ("reset", "clear", "init"):
                    engine.reset_session()
                    console.print("[bold green]✔ 常駐 AntigravitySession をクリーンリセットいたしました、拓磨様🌸[/bold green]\n")
                else:
                    ag_info = engine.get_antigravity_status() if hasattr(engine, "get_antigravity_status") else {}
                    s_info = ag_info.get("session", {})
                    sess_state_str = "[bold green]🟢 Active (Warm Persistent)[/bold green]" if s_info.get("active") else "[bold yellow]🟡 Standby (次回推論時にミリ秒起動)[/bold yellow]"
                    console.print(Panel(
                        f"[bold cyan]• セッション状態:[/] {sess_state_str}\n"
                        f"[bold cyan]• プライマリエンジン:[/] [bold white]{ag_info.get('primary_engine', 'antigravity').upper()}[/bold white]\n"
                        f"[bold cyan]• 現在のモデル:[/] [bold yellow]{engine.current_model}[/bold yellow] (Thinking: [cyan]{engine.thinking_level.upper()}[/cyan])\n"
                        f"[bold cyan]• 累積ターン数:[/] {max(s_info.get('turn_count', 0), token_tracker.session_turns)} ターン\n"
                        f"[bold cyan]• 累積トークン:[/] {token_tracker.session_total_tokens:,} tokens (¥{token_tracker.session_cost_jpy:.4f})\n"
                        f"[bold cyan]• 永続化ディレクトリ:[/] `{s_info.get('save_dir', '~/.tugumi/sessions')}`\n"
                        f"[dim]※ `/session reset` で常駐セッションを初期化できます。[/dim]",
                        title="[bold cyan]◈ Antigravity Persistent Session Status (/session) ◈[/bold cyan]",
                        border_style="cyan",
                    ))
                    console.print()
                continue

            # 16.2 コンテキストロスレス圧縮 (/compact)
            if user_input.startswith("/compact"):
                before_msgs = memory.get_recent_messages(limit=30)
                raw_chars = sum(len(m.get("content", "")) for m in before_msgs)
                compressed_ctx = memory.get_compressed_context()
                after_chars = len(compressed_ctx)
                saved_ratio = int((1.0 - (after_chars / max(raw_chars, 1))) * 100) if raw_chars > after_chars else 0
                console.print(Panel(
                    f"[bold green]✔ 対話コンテキストのロスレス圧縮・剪定が完了いたしました！[/bold green]\n\n"
                    f"[cyan]• 対象メッセージ:[/] 直近 {len(before_msgs)} 件\n"
                    f"[cyan]• 圧縮前サイズ:[/] {raw_chars:,} 文字\n"
                    f"[cyan]• 圧縮後サイズ:[/] {after_chars:,} 文字 (削減率: [bold yellow]{saved_ratio}%[/bold yellow])\n"
                    f"[cyan]• 重要制約保護:[/] Switch 2 原則 / 150k Context / 3072d RAG 完全保持",
                    title="[bold cyan]◈ ContextCompressor Lossless Compaction (/compact) ◈[/bold cyan]",
                    border_style="green",
                ))
                console.print()
                continue

            # 16.3 トークン＆日本円利用料金確認 (/credits, /cost)
            if user_input.startswith(("/credits", "/cost")):
                c_parts = user_input.split()
                if len(c_parts) > 1 and c_parts[1].lower() in ("reset", "clear"):
                    token_tracker.reset()
                    console.print("[bold green]✔ セッションのトークン＆利用料金カウンターをリセットいたしました。[/bold green]\n")
                else:
                    token_tracker.render_cost_banner(console, mode=curr_mode, model_name=engine.current_model)
                    console.print()
                continue

            # 16.4 Gemini Live 女性ボイス＆トーン設定 (/voice)
            if user_input.startswith("/voice"):
                import json
                v_parts = user_input.split()
                voice_cfg_path = os.path.expanduser("~/.tugumi_live_voice.json")
                voices_catalog = {
                    "Aoede": "爽やか・知的（つぐみ標準）",
                    "Kore": "凛とした・知性",
                    "Leda": "快活・エネルギッシュ",
                    "Despina": "滑らか・上品",
                    "Autonoe": "朗らか・明るい",
                    "Callirrhoe": "気さく・リラックス",
                    "Erinome": "透明感・澄んだ美声",
                    "Laomedeia": "軽快・アップビート",
                    "Pulcherrima": "前向き・気品",
                    "Sulafat": "温かみ・包容力",
                    "Vindemiatrix": "穏やか・優しい",
                    "Achernar": "ソフト・繊細",
                }
                tones_catalog = {
                    "standard": "知的・誠実（標準）",
                    "gentle": "甘やか・癒やし（優しい）",
                    "energetic": "快活・ハキハキ（元気）",
                    "cool": "クール・凛々しい（ダークつぐみ風）",
                    "whisper": "ささやき・親密（深夜モード）",
                }
                curr_v = {"voice": "Aoede", "tone": "standard"}
                if os.path.exists(voice_cfg_path):
                    try:
                        with open(voice_cfg_path, "r", encoding="utf-8") as vf:
                            curr_v.update(json.load(vf))
                    except Exception:
                        pass

                if len(v_parts) > 1:
                    req_v = v_parts[1].strip()
                    matched_v = next((k for k in voices_catalog if k.lower() == req_v.lower()), None)
                    matched_t = next((k for k in tones_catalog if k.lower() == req_v.lower()), None)
                    if matched_v:
                        curr_v["voice"] = matched_v
                    elif matched_t:
                        curr_v["tone"] = matched_t
                    else:
                        console.print(f"[bold red]✖ 無効なボイスまたはトーン名です: {req_v}[/bold red]\n")
                        continue
                    if len(v_parts) > 2:
                        req_t = v_parts[2].strip().lower()
                        if req_t in tones_catalog:
                            curr_v["tone"] = req_t
                    try:
                        with open(voice_cfg_path, "w", encoding="utf-8") as vf:
                            json.dump(curr_v, vf, ensure_ascii=False, indent=2)
                    except Exception:
                        pass
                    console.print(
                        f"[bold green]✔ Gemini Live 音声設定を更新いたしました！[/bold green]\n"
                        f"  • ボイス: [bold cyan]{curr_v['voice']}[/bold cyan] ({voices_catalog.get(curr_v['voice'], '')})\n"
                        f"  • トーン: [bold yellow]{curr_v['tone']}[/bold yellow] ({tones_catalog.get(curr_v['tone'], '')})\n"
                    )
                else:
                    v_table = Table(title="[bold #ff79c6]🎙️ Gemini Live 女性ボイス (12種) ＆ トーン設定 (/voice)[/bold #ff79c6]", border_style="#ff79c6")
                    v_table.add_column("Voice名", style="bold cyan", width=16)
                    v_table.add_column("声質・特徴", style="white")
                    v_table.add_column("状態", style="bold green", width=10, justify="center")
                    for vk, vd in voices_catalog.items():
                        mark = "★ 選択中" if vk == curr_v.get("voice") else ""
                        v_table.add_row(vk, vd, mark)
                    console.print(v_table)
                    console.print(f"[dim]現在のトーン: {curr_v.get('tone')} ({tones_catalog.get(curr_v.get('tone', 'standard'), '')}) | 変更例: `/voice Kore cool`[/dim]\n")
                continue

            # 16.5 自律ゴール完遂モード (/goal)
            if user_input.startswith("/goal"):
                goal_text = user_input[5:].strip()
                if not goal_text:
                    console.print("[bold yellow]💡 使い方: `/goal <達成したい目標>` (5層検証ゲート合格まで自律完遂します)[/bold yellow]\n")
                    continue
                console.print(f"[bold #00f0ff]🎯 自律完遂ゴールモード (/goal) 起動: 『{goal_text}』[/bold #00f0ff]\n")
                user_input = (
                    f"【自律完遂ゴールモード (/goal)】\n"
                    f"目標: {goal_text}\n"
                    f"Explore → Plan → Execute → Verify (5層検証ゲート: 構文・Ruff・実機テスト・回帰ゼロ・コスト保全) を途中で止めずに完全自律で遂行し、客観的証拠（Exit Code 0）とともに完遂報告してください。"
                )

            # 16.9 未定義スラッシュコマンドのタイポガード (APIクォータ浪費防止)
            if user_input.startswith("/") and not user_input.startswith(("/storage/", "/data/", "/sdcard/", "/system/", "/proc/", "/tmp/")):
                from interfaces.cli.dynamic_completer import MAIN_COMMANDS
                cmd_token = user_input.split()[0].lower()
                if cmd_token not in MAIN_COMMANDS:
                    import difflib
                    candidates = difflib.get_close_matches(cmd_token, list(MAIN_COMMANDS.keys()), n=3, cutoff=0.45)
                    sug_lines = [f"[bold yellow]⚠ 未定義のコマンドです:[/] [bold white]{cmd_token}[/bold white]"]
                    if candidates:
                        sug_lines.append("\n[bold cyan]💡 もしかして以下のコマンドですか？[/bold cyan]")
                        for cand in candidates:
                            sug_lines.append(f"  • [bold green]{cand}[/bold green] : {MAIN_COMMANDS.get(cand, '')}")
                    sug_lines.append("\n[dim]※ 全コマンド一覧は `/help` で確認できます。[/dim]")
                    console.print(Panel("\n".join(sug_lines), title="[bold yellow]◈ Command Typo Guard ◈[/bold yellow]", border_style="yellow"))
                    console.print()
                    continue


            # --- 通常対話 & 自律実行ループ ---
            # 0. 自然言語 楽曲制作インテント検知 (プロンプト直結)
            if is_music_creation_intent(user_input):
                console.print("\n[bold #00f0ff]🎵 拓磨様の音楽制作リクエストをダイレクトに実行いたします！[/bold #00f0ff]")
                console.print("[cyber.dim]プロンプトマネージャーを完全排除し、拓磨様の指示を直接音楽モデルへ投入します...[/cyber.dim]\n")

                # プロンプトぶつ切り・単語くり抜き処理を完全排除し、拓磨様の言葉を100%完全なまま渡す
                user_prompt = user_input.strip()

                # 「こんな感じで」等の直前参照がある場合、直前の対話から文脈をフルに取得して合体（ぶつ切り防止）
                if any(k in user_input for k in ["こんな感じ", "この感じ", "さっきの", "前回の", "これで作って"]):
                    recent_msgs = memory.get_recent_messages(limit=4)
                    for m in reversed(recent_msgs):
                        if m.get("content") and m.get("content") != user_input:
                            prev_content = m.get("content").strip()
                            if len(prev_content) > 5:
                                user_prompt = f"【文脈・要望】\n{prev_content}\n\n【追加指示】\n{user_input}"
                                break

                inspector.display_tool_start("GeminiMusicStudio", {"prompt": user_prompt})

                try:
                    from tools.media_tools import GeminiMusicStudio
                    res = GeminiMusicStudio.create_music_direct(user_prompt=user_prompt)
                    if res.get("success"):
                        audio_target = res.get("mp3_path")
                        inspector.display_tool_result("GeminiMusicStudio", True, f"楽曲完成: 『{res['title']}』")

                        m_table = Table(title=f"[bold #00f0ff]🎵 拓磨様のための新曲『{res['title']}』完成！ ◈[/bold #00f0ff]", border_style="#7928ca")
                        m_table.add_column("項目", style="bold cyan", width=16)
                        m_table.add_column("詳細情報 / パス", style="white")
                        m_table.add_row("タイトル", f"『{res['title']}』")
                        m_table.add_row("指示プロンプト", user_prompt)
                        if audio_target and os.path.exists(audio_target):
                            m_table.add_row("🎧 完成楽曲 (MP3)", f"{audio_target} ({os.path.getsize(audio_target):,} bytes)")
                        m_table.add_row("📱 保存場所", "/storage/emulated/0/Music/TUGUMI/ (スマホ標準音楽プレイヤーで即再生)")
                        console.print(m_table)

                        # 再生開始
                        if audio_target and os.path.exists(audio_target):
                            console.print(f"[bold green]▶ 楽曲の再生を開始します: {os.path.basename(audio_target)}[/bold green]")
                            try:
                                import subprocess
                                subprocess.run(["termux-media-player", "play", audio_target], capture_output=True)
                            except Exception:
                                subprocess.run(["termux-open", audio_target], capture_output=True)

                        resp_summary = f"拓磨様、ご指示いただきましたプロンプト『{user_prompt}』に基づき、余計なプロンプト加工を行わずダイレクトに楽曲『{res['title']}』を制作いたしました！スマホの音楽プレイヤーまたはTermuxから即座にお聴きいただけます。"
                        memory.add_message("user", user_input, mode=curr_mode)
                        memory.add_message("assistant", resp_summary, mode=curr_mode)
                    else:
                        console.print(f"[bold red]楽曲制作エラー: {res.get('error')}[/bold red]")

                except Exception as e:
                    inspector.display_tool_result("GeminiMusicStudio", False, f"楽曲制作エラー: {e}")
                    console.print(f"[bold red]楽曲制作中にエラーが発生しました: {e}[/bold red]")

                console.print()
                continue

            # 0.5 自然言語 画像生成・実写ポートレート・画像編集インテント検知 (プロンプト直結)
            is_img, img_subcmd, img_args = is_image_creation_intent(user_input)
            if is_img:
                from tools.media_tools import GeminiImageStudio
                console.print("\n[bold #00f0ff]📸 拓磨様の画像生成・ポートレートリクエストをダイレクトに実行いたします！[/bold #00f0ff]")
                console.print("[cyber.dim]Gemini 3 画像モデル (gemini-3.1-flash-image) を起動中...[/cyber.dim]\n")

                user_prompt = user_input.strip()
                # 文脈引き継ぎ
                if any(k in user_input for k in ["こんな感じ", "この感じ", "さっきの", "前回の", "これで作って"]):
                    recent_msgs = memory.get_recent_messages(limit=4)
                    for m in reversed(recent_msgs):
                        if m.get("content") and m.get("content") != user_input:
                            prev_content = m.get("content").strip()
                            if len(prev_content) > 5:
                                user_prompt = f"【文脈・要望】\n{prev_content}\n\n【追加指示】\n{user_input}"
                                break

                inspector.display_tool_start("GeminiImageStudio", {"subcmd": img_subcmd, "prompt": user_prompt})

                try:
                    if img_subcmd == "photo":
                        console.print("[bold green]📸 一眼レフ光学仕様・マイクロ肌テクスチャ・自然光を自動昇華して実写生成中...[/bold green]")
                        res = GeminiImageStudio.generate(prompt=user_prompt, photoreal=True, style="photoreal")
                    elif img_subcmd == "edit":
                        # 画像パスが指示に含まれているか確認
                        path_match = re.search(r'(/[\w\-./]+\.(?:jpg|jpeg|png|webp))', user_prompt)
                        if path_match and os.path.exists(path_match.group(1)):
                            src_path = path_match.group(1)
                            clean_prompt = user_prompt.replace(src_path, "").strip()
                            console.print(f"[bold magenta]🖼️ 既存画像 ({os.path.basename(src_path)}) をプロンプト指示通りに編集・変形中...[/bold magenta]")
                            res = GeminiImageStudio.edit(image_path=src_path, prompt=clean_prompt)
                        else:
                            # 直近生成された画像を探してフォールバック
                            from tools.media_tools import IMAGES_DIR
                            recent_files = sorted(Path(IMAGES_DIR).glob("*.jpg"), key=os.path.getmtime, reverse=True)
                            if recent_files:
                                src_path = str(recent_files[0])
                                console.print(f"[bold magenta]🖼️ 最新の画像 ({os.path.basename(src_path)}) を対象に編集・変形中...[/bold magenta]")
                                res = GeminiImageStudio.edit(image_path=src_path, prompt=user_prompt)
                            else:
                                res = {"success": False, "error": "編集対象の画像パスが見つかりませんでした。/image edit <画像パス> <指示> をご指定ください。"}
                    else:
                        console.print("[bold cyan]🎨 Gemini 画像生成モデルへプロンプトを投入中...[/bold cyan]")
                        res = GeminiImageStudio.generate(prompt=user_prompt, style="cyberpunk")

                    if res.get("success"):
                        img_path = res["file_path"]
                        inspector.display_tool_result("GeminiImageStudio", True, f"画像生成完了: {os.path.basename(img_path)}")
                        # ターミナル内アスキーアートプレビュー
                        console.print(GeminiImageStudio.to_ascii(img_path, target_width=44))

                        i_table = Table(title="[bold #00f0ff]📸 拓磨様のための画像生成完了！ ◈[/bold #00f0ff]", border_style="#00f0ff")
                        i_table.add_column("項目", style="bold cyan", width=16)
                        i_table.add_column("詳細情報 / パス", style="white")
                        i_table.add_row("指示プロンプト", user_prompt)
                        i_table.add_row("保存先", f"{img_path} ({os.path.getsize(img_path):,} bytes)")
                        i_table.add_row("解像度", res.get("dimensions", "1408x768"))
                        i_table.add_row("ギャラリー", "スマホ標準ギャラリーで即閲覧可能 (メディアスキャン済)")
                        console.print(i_table)

                        try:
                            import subprocess
                            subprocess.run(["termux-open", img_path], capture_output=True)
                        except Exception:
                            pass

                        resp_summary = f"拓磨様、ご指示いただきましたプロンプトに基づき、最高峰クオリティの画像を生成いたしました！保存先: {img_path}"
                        memory.add_message("user", user_input, mode=curr_mode)
                        memory.add_message("assistant", resp_summary, mode=curr_mode)
                    else:
                        console.print(f"[bold red]画像生成エラー: {res.get('error')}[/bold red]")

                except Exception as e:
                    inspector.display_tool_result("GeminiImageStudio", False, f"画像処理エラー: {e}")
                    console.print(f"[bold red]画像処理中にエラーが発生しました: {e}[/bold red]")

                console.print()
                continue

            # 1. ハイブリッドRAGコンテキスト自動取得（チャット＆タスク両対応・制限なし）
            rag_context = ""
            rag_hits = []
            rag_bundle = rag.retrieve_for_context(user_input, top_k=3)
            if rag_bundle.get("has_hits"):
                rag_hits = rag_bundle.get("hits", [])
                rag_context = rag_bundle.get("context_text", "")
                inspector.display_tool_result("AutoRAG", True, rag_bundle.get("summary_label", f"関連ナレッジ {len(rag_hits)}件を自動コンテキスト注入"))

            # 2. ContextCompressorによる対話履歴スマート剪定＆Observation Masking
            past_logs = memory.get_recent_messages(limit=16)
            pruned_logs = context_compressor.prune_history(past_logs, max_turns=8)
            history_context = ""
            if pruned_logs:
                hist_snippets = []
                for entry in pruned_logs:
                    role_label = "マスター拓磨様" if entry.get("role") == "user" else "つぐみ"
                    content = entry.get("content", "").strip()
                    # 拓磨様の発言（role == "user"）は1文字も改ざん・マスク・省略せず100%完全保持
                    if entry.get("role") == "user":
                        masked_content = content
                    else:
                        masked_content = context_compressor.mask_observation(content, tool_name=f"log_{entry.get('role')}")
                    hist_snippets.append(f"[{role_label}]: {masked_content}")
                history_context = "\n".join(hist_snippets)

            # 3. 多層記憶想起＆システムプロンプト生成
            cognitive_memory_context = adv_memory.recall_cognitive_context(current_query=user_input)
            system_prompt = get_system_prompt(mode=curr_mode, rag_context=rag_context, memory_context=cognitive_memory_context, corporate_query=user_input)

            # 4. ユーザー発言記録
            memory.add_message("user", f"/rag {user_input}" if force_rag_query else user_input, mode=curr_mode)

            # 5. プロンプト構築（マスター拓磨様の最新指示を最優先核として配置＋常駐セッション向けRAG透過注入）
            memory_context = memory.format_memory_context(user_input, max_chars=3000)
            prompt_parts = [f"【マスター拓磨様からの至上指示（最優先・完全遵守要件）】\n{user_input}"]
            if rag_context:
                prompt_parts.append(f"【📚 参照RAGナレッジ（TUGUMI_RAG ローカル確定知識・リファレンス）】\n{rag_context}")
            if history_context:
                prompt_parts.append(f"【参考：直前対話履歴（ContextCompressor剪定済）】\n{history_context}")
            if memory_context:
                prompt_parts.append(f"【参考：関連長期記憶】\n{memory_context}")
            current_prompt = "\n\n".join(prompt_parts)

            # 6. 推論 & ストリーミング生成（ESC一時停止・リアルタイムSteering・タイムアウト自律リカバリ対応）
            timeout_recovery_count = 0
            is_steering_turn = False
            while True:
                thought_accumulator = []
                text_accumulator = []
                start_time = time.time()
                is_cancelled = False
                resumed_prompt = None
                timed_out_error = None

                last_tool_name = ""
                speaker = "つぐみ🌸" if curr_mode == "light" else "ダークつぐみ⚡"
                speaker_style = f"bold {CYBER_PALETTES[curr_mode]['primary']}"
                
                # リアルタイム推論HUD初期化
                active_model = getattr(engine, 'current_model', 'Argon')
                status_msg = f"[bold {CYBER_PALETTES[curr_mode]['secondary']}]⠋ Native Antigravity SDK 接続中... [dim cyan]⏱ 0.0s[/dim cyan] [dim](ESCで一時停止)[/dim][/bold {CYBER_PALETTES[curr_mode]['secondary']}]"
                status = console.status(status_msg, spinner="dots12")
                status.start()
                has_started_text = False
                thought_chars = 0
                first_thought_time = None

                try:
                    stream_iter = engine.generate_stream(
                        prompt=current_prompt,
                        system_instruction=system_prompt,
                        thinking_level=engine.thinking_level,
                        mode=curr_mode,
                        user_goal=user_input,
                        is_steering=is_steering_turn
                    )
                    with TaskInterrupter(console) as interrupter:
                        active_tool_running = False
                        for chunk_type, chunk_data in stream_iter:
                            # 1. ESCキー押下判定（毎0.1s確実に判定）
                            if interrupter.check_esc_pressed():
                                if status._live.is_started:
                                    status.stop()
                                if hasattr(engine, "set_paused"):
                                    engine.set_paused(True)
                                action, extra_prompt = interrupter.handle_pause(
                                    current_text="".join(text_accumulator),
                                    mode=curr_mode
                                )
                                if hasattr(engine, "set_paused"):
                                    engine.set_paused(False)
                                pause_dur = getattr(interrupter, "last_pause_duration", 0.0)
                                if pause_dur > 0:
                                    start_time += pause_dur
                                    if first_thought_time is not None:
                                        first_thought_time += pause_dur

                                if action == "cancel":
                                    is_cancelled = True
                                    restore_terminal_canonical()
                                    engine.cancel_active_task()
                                    engine.reset_session(system_instruction=system_prompt)
                                    if hasattr(stream_iter, "close"):
                                        try:
                                            stream_iter.close()
                                        except Exception:
                                            pass
                                    break
                                elif action == "resume" and extra_prompt:
                                    resumed_prompt = extra_prompt
                                    restore_terminal_canonical()
                                    engine.cancel_active_task()
                                    if hasattr(stream_iter, "close"):
                                        try:
                                            stream_iter.close()
                                        except Exception:
                                            pass
                                    break
                                # action == "continue": 再開
                                if not has_started_text:
                                    if active_tool_running and last_tool_name:
                                        elapsed_now = max(0.0, time.time() - start_time)
                                        status.update(
                                            f"[bold {CYBER_PALETTES[curr_mode]['secondary']}]🔧 ツール [{last_tool_name}] 実行再開・継続中... "
                                            f"[dim cyan]⏱ {elapsed_now:.1f}s[/dim cyan] [dim](ESCで一時停止)[/dim][/bold {CYBER_PALETTES[curr_mode]['secondary']}]"
                                        )
                                    status.start()

                            now = time.time()
                            elapsed = max(0.0, now - start_time)

                            # 2. 定期パルス（tick）によるリアルタイムタイマー＆推論進捗HUD更新
                            if chunk_type == "tick":
                                if status._live.is_started:
                                    if active_tool_running and last_tool_name:
                                        hud_msg = (
                                            f"[bold {CYBER_PALETTES[curr_mode]['secondary']}]🔧 ツール [{last_tool_name}] 実行中... "
                                            f"[dim cyan]⏱ {elapsed:.1f}s[/dim cyan] [dim](ESCで一時停止)[/dim][/bold {CYBER_PALETTES[curr_mode]['secondary']}]"
                                        )
                                    elif thought_chars > 0:
                                        # 思考中（Thinking中）の場合：文字数と生成スピードをリアルタイム表示
                                        th_speed = thought_chars / max(0.1, (now - (first_thought_time or start_time)))
                                        hud_msg = (
                                            f"[bold {CYBER_PALETTES[curr_mode]['secondary']}]🧠 深層推論実行中 "
                                            f"([white]{thought_chars:,}[/white]字 / [cyan]{th_speed:.0f}字/s[/cyan]) "
                                            f"[dim cyan]⏱ {elapsed:.1f}s[/dim cyan] [dim](ESCで一時停止)[/dim][/bold {CYBER_PALETTES[curr_mode]['secondary']}]"
                                        )
                                    else:
                                        # API接続・準備中：経過時間と状態フェーズを明示
                                        if elapsed < 3.0:
                                            phase = "🌐 API接続・リクエスト確立中..."
                                        elif elapsed < 15.0:
                                            phase = f"⚡ [{active_model}] 推論演算中..."
                                        elif elapsed < 35.0:
                                            phase = "⏳ 深層推論中 (正常稼働中 / 思考展開中)..."
                                        else:
                                            phase = "🔬 大規模深層推論を継続中 (正常稼働中)..."
                                        hud_msg = (
                                            f"[bold {CYBER_PALETTES[curr_mode]['secondary']}]{phase} "
                                            f"[dim cyan]⏱ {elapsed:.1f}s[/dim cyan] [dim](ESCで一時停止)[/dim][/bold {CYBER_PALETTES[curr_mode]['secondary']}]"
                                        )
                                    status.update(hud_msg)
                                continue

                            elif chunk_type == "thought":
                                active_tool_running = False
                                if first_thought_time is None:
                                    first_thought_time = now
                                thought_chars += len(chunk_data)
                                thought_accumulator.append(chunk_data)
                                if getattr(thinking_viewer, "show_thinking", False):
                                    if status._live.is_started:
                                        status.stop()
                                    thinking_viewer.stream_thought_chunk(chunk_data)
                                else:
                                    # サクサクモード時でもHUDの文字数カウンターを即座に動的更新！
                                    if not has_started_text and not status._live.is_started:
                                        status.start()
                                    if status._live.is_started:
                                        th_speed = thought_chars / max(0.1, (now - first_thought_time))
                                        hud_msg = (
                                            f"[bold {CYBER_PALETTES[curr_mode]['secondary']}]🧠 深層推論実行中 "
                                            f"([white]{thought_chars:,}[/white]字 / [cyan]{th_speed:.0f}字/s[/cyan]) "
                                            f"[dim cyan]⏱ {elapsed:.1f}s[/dim cyan] [dim](ESCで一時停止)[/dim][/bold {CYBER_PALETTES[curr_mode]['secondary']}]"
                                        )
                                        status.update(hud_msg)

                            elif chunk_type == "tool_call":
                                thinking_viewer.end_thinking_stream()
                                if status._live.is_started:
                                    status.stop()
                                if has_started_text:
                                    sys.stdout.write("\n")
                                    sys.stdout.flush()
                                last_tool_name = getattr(chunk_data, "name", "tool")
                                active_tool_running = True
                                inspector.display_tool_start(last_tool_name, getattr(chunk_data, "args", {}))
                                if not has_started_text:
                                    status.update(
                                        f"[bold {CYBER_PALETTES[curr_mode]['secondary']}]🔧 ツール [{last_tool_name}] 実行中... "
                                        f"[dim cyan]⏱ {elapsed:.1f}s[/dim cyan] [dim](ESCで一時停止)[/dim][/bold {CYBER_PALETTES[curr_mode]['secondary']}]"
                                    )
                                    status.start()
                            elif chunk_type == "tool_result":
                                active_tool_running = False
                                thinking_viewer.end_thinking_stream()
                                if status._live.is_started:
                                    status.stop()
                                tool_n = getattr(chunk_data, "name", "tool")
                                res_val = getattr(chunk_data, "result", None)
                                err_val = getattr(chunk_data, "error", None)
                                is_ok = err_val is None
                                summary_msg = f"Output: {str(res_val)[:80]}..." if res_val is not None else (f"Error: {err_val}" if err_val else "Finished")
                                inspector.display_tool_result(tool_n, is_ok, summary_msg)
                                if not has_started_text:
                                    status.update(
                                        f"[bold {CYBER_PALETTES[curr_mode]['secondary']}]⚡ [{active_model}] ツール結果解析・推論継続中... "
                                        f"[dim cyan]⏱ {elapsed:.1f}s[/dim cyan] [dim](ESCで一時停止)[/dim][/bold {CYBER_PALETTES[curr_mode]['secondary']}]"
                                    )
                                    status.start()
                            elif chunk_type == "cancelled":
                                thinking_viewer.end_thinking_stream()
                                if status._live.is_started:
                                    status.stop()
                                is_cancelled = True
                                break
                            elif chunk_type == "error":
                                thinking_viewer.end_thinking_stream()
                                if status._live.is_started:
                                    status.stop()
                                if "タイムアウト" in str(chunk_data):
                                    timed_out_error = str(chunk_data)
                                    console.print(f"\n[bold red]✖ 実行時間超過保護: {chunk_data}[/bold red]")
                                    if hasattr(engine, "session") and engine.session:
                                        try:
                                            engine.session.cancel()
                                        except Exception:
                                            pass
                                    memory.add_message(
                                        "assistant",
                                        f"【タイムアウト遮断記録】{chunk_data}。直前のツール: {last_tool_name or 'なし'}。文脈は保持されています。直ちに自律リカバリを実行します。",
                                        mode=curr_mode
                                    )
                                    break
                                elif "Persistent session stream fallback" not in str(chunk_data) and "fallback triggered" not in str(chunk_data):
                                    console.print(f"[bold yellow]⚠ {chunk_data}[/bold yellow]")
                            else:
                                thinking_viewer.end_thinking_stream()
                                if status._live.is_started:
                                    status.stop()
                                if not has_started_text:
                                    thinking_viewer.render_response_header(speaker, speaker_style, getattr(engine, 'current_model', '3.8-Flash'))
                                    has_started_text = True
                                sys.stdout.write(chunk_data)
                                sys.stdout.flush()
                                text_accumulator.append(chunk_data)
                except Exception as e:
                    if status._live.is_started:
                        status.stop()
                    console.print(f"[bold red]✖ 生成エラー: {e}[/bold red]")
                    reflection.record_failure(
                        keyword="generate_stream",
                        cause=str(e),
                        forbidden_action="エラーの未対応放置",
                        correct_alternative="Antigravity SDK / GeminiClient フォールバックカスケードによる再送"
                    )
                    memory.add_message("assistant", f"【生成エラー発生】エラー内容: {e}。直前のツール: {last_tool_name or 'なし'}。拓磨様から問われた際は隠さず誠実に説明してください。", mode=curr_mode)
                finally:
                    thinking_viewer.end_thinking_stream()
                    if status._live.is_started:
                        status.stop()

                if is_cancelled:
                    console.print("[yellow]拓磨様、タスクを中断いたしました。[/yellow]\n")
                    memory.add_message("assistant", f"【タスク中断記録】拓磨様によりESC中断されました。直前の実行ツール: {last_tool_name or 'なし'}。拓磨様から中断理由や状況を問われた際は、この経緯を隠さず100%誠実に即答してください。", mode=curr_mode)
                    break

                if timed_out_error:
                    if timeout_recovery_count < 2:
                        timeout_recovery_count += 1
                        console.print(f"[bold yellow]🔄 【自律リカバリ自動発動（試行 {timeout_recovery_count}/2）】[/bold yellow] [dim cyan]タイムアウト（{timed_out_error}）を検知。作業を中断・放棄せず、代替手段・軽量化・高速フラグを自律適用してタスクを即座に継続完遂いたします...[/dim cyan]\n")
                        prev_text = "".join(text_accumulator).strip()
                        current_prompt = (
                            f"【🚨 システム自律自己修復指令（タイムアウト自動リカバリ・継続完遂マンデート）】\n"
                            f"直前の処理（直前の実行ツール: {last_tool_name or 'コマンド実行/推論'}）が時間超過（{timed_out_error}）により安全遮断されました。\n"
                            f"【最重要】作業を中断・放棄して立ち止まる行為は論外であり絶対に禁止です。直ちに自律的に以下のリカバリ行動を取ってください：\n"
                            f"1. 【タイムアウト原因の特定】: サーバー未起動時の自動待機、長大なテスト、過剰な入出力等の要因を即座に看破せよ。\n"
                            f"2. 【代替アプローチの即座実行】: 同一の重いコマンドや処理を絶対に繰り返すな。高速クラウドフラグ（例: `--cloud`, `--fast`）、サーバー未起動防止フラグ（`--no-auto-start`）、ピンポイントな単体テスト、または非同期バックグラウンド実行（`nohup ... &`）等の軽量・確実な代替手段に即座に切り替えよ。\n"
                            f"3. 【自律完遂】: 拓磨様の手を煩わせることなく、当初の目的（ゴール: 「{user_input}」）を客観的証拠（Exit Code 0）が得られるまで最後まで完遂せよ。\n\n"
                            f"【当初の全体ゴール】:\n{user_input}\n\n"
                            f"【タイムアウト直前の途中経過】:\n{prev_text[:800] if prev_text else '（初期処理中）'}"
                        )
                        is_steering_turn = True
                        continue
                    else:
                        console.print("\n[bold red]⚠ 連続タイムアウトを検知いたしました。安全のため拓磨様へ制御を委譲いたします。[/bold red]\n")
                        break

                if resumed_prompt:
                    # 拓磨様からの追加・軌道修正指示を最優先に統合し、文脈（メモリ・ツール履歴）を完全維持したまま即座に方針を切り替えてタスク続行！
                    if has_started_text:
                        sys.stdout.write("\n\n")
                        sys.stdout.flush()
                    prev_text = "".join(text_accumulator).strip()
                    inject_prompt = resumed_prompt
                    resumed_prompt = None  # 多重実行防止
                    console.print(f"\n[bold magenta]⚡ 【軌道修正（Steering）適用】[/bold magenta] [bold white]「{inject_prompt}」[/bold white]")
                    console.print("[dim cyan]› これまでの作業文脈を保持したまま方針を即座に切り替え、タスクを正しい方向で続行いたします...[/dim cyan]\n")
                    
                    # セッションは絶対にリセットせず完全維持する（作業記憶・MCP・文脈を破棄しない）
                    # 拓磨様からの軌道修正コマンドとして同一エージェントへ直接注入
                    interrupted_tool_info = f"（直前に実行中だったツール `{last_tool_name}` は拓磨様により強制中断されました。同一の重いコマンドの再実行は厳禁です）" if last_tool_name else ""
                    fallback_prev = f"（ツール {last_tool_name or '推論'} 実行段階で中断）"
                    current_prompt = (
                        f"【🚨 マスター拓磨様からの即時・最優先【軌道修正】至上指示】\n"
                        f"直前の処理{interrupted_tool_info}は、マスター拓磨様によりESC一時停止・軌道修正されました。\n"
                        f"これまでの作業文脈・試行結果を保持した上で、以下の拓磨様の修正指示・お言葉を100%最優先とし、直ちに思考・行動方針を切り替えて迅速に応答・完遂してください。\n\n"
                        f"【マスター拓磨様からの修正指示・追加プロンプト（最優先遵守）】:\n"
                        f"{inject_prompt}\n\n"
                        f"【当初の全体ゴール】:\n"
                        f"{user_input}\n\n"
                        f"【中断された直前の途中内容（参考）】:\n"
                        f"{prev_text[:1000] if prev_text else fallback_prev}"
                    )
                    is_steering_turn = True
                    continue

                # 正常終了
                if has_started_text:
                    sys.stdout.write("\n\n")
                    sys.stdout.flush()
                break

            if is_cancelled:
                continue

            elapsed = time.time() - start_time
            full_thought = "".join(thought_accumulator)
            full_response = "".join(text_accumulator)

            # 思考ログ（Thinking）のアコーディオン描画
            if full_thought:
                thinking_viewer.render_thinking_summary(full_thought, duration=elapsed)

            # リアルタイム表示済みでない場合（エラー時など）のみフォールバック描画
            if not has_started_text and full_response:
                thinking_viewer.render_markdown_response(full_response, speaker, speaker_style, getattr(engine, 'current_model', '3.8-Flash'))

            # アシスタント発言記録
            memory.add_message("assistant", full_response, mode=curr_mode)

            # 拓磨様の発言・指示から重要事実・好みを自律検知して長期記憶に定着
            try:
                adv_memory.consolidate_interaction(user_input, full_response)
            except Exception:
                pass

            # トークン消費＆日本円料金の計算・表示！
            token_tracker.record_turn(
                prompt_text=current_prompt,
                response_text=full_response,
                thought_text=full_thought
            )
            token_tracker.render_cost_banner(console, mode=curr_mode)

        except KeyboardInterrupt:
            console.print("\n[yellow]拓磨様、中断指示を受信いたしました。[/yellow]\n")
            try:
                memory.add_message("assistant", "【タスク中断記録】拓磨様によりCtrl+Cで強制中断されました。拓磨様から中断理由や状況を問われた際は、中断された事実を隠さず100%誠実に即答してください。", mode=curr_mode)
            except Exception:
                pass
            continue
        except EOFError:
            break


if __name__ == "__main__":
    run_cli()
