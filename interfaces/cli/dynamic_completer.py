# -*- coding: utf-8 -*-
"""
TUGUMIv6 Rich Dynamic Auto-Completer with Full Japanese Descriptions
- Displays clear, colorful explanation text (display_meta) for every single command.
- Solves the 'no explanation' confusion once and for all.
- Dynamically loads skill descriptions from ~/.agents/skills/*/SKILL.md
- Dynamically loads MCP server descriptions.
"""

import os
import re
import time
from typing import Dict
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

# 1. コマンド定義と分かりやすい日本語説明文 (Display Meta: 重複エイリアス完全一掃・代表純化版)
MAIN_COMMANDS: Dict[str, str] = {
    # ── 📱 Termux 実機・スマホ直結 ──
    "$": "⚡ Termuxシェル直結パススルー実行 ($ <cmd> 例: $ ls -la)",
    "/sh": "⚡ Termuxシェル直結実行 (/sh <cmd>)",
    "/ss": "📸 最新スクショ自動検出＆Gemini Vision視覚解析 (/ss [質問])",
    "/copy": "📋 直前のつぐみの回答をスマホクリップボードへ一発コピー (/copy)",
    "/paste": "📋 スマホクリップボードの内容を取得・表示・質問 (/paste)",
    "/open": "📱 Android標準アプリ(ビュワー/ブラウザ)で開く (/open <path|last>)",
    "/share": "📤 Android共有ダイアログでファイルを共有 (/share <path|last>)",
    "/battery": "🔋 スマホバッテリー残量・温度・充電状態HUD (/battery)",
    "/web": "🌐 TUGUMIv6 WebUIサーバー完全制御 (/web [start|stop|status|open])",
    "/app": "📱 PWAアプリアイコン健康診断＆更新手順 (/app)",
    "/find": "🔍 社内武器庫・コマンド・ポート・カタログ即時逆引き (/find <query>)",
    "/top": "📊 Termux実行中プロセス＆メモリ監視HUD (/top)",
    "/toast": "💬 Androidトースト通知を画面にポップアップ (/toast <msg>)",
    "/diff": "📝 Git作業ディレクトリ差分・変更一覧表示 (/diff)",

    # ── 🧠 AI推論＆思考セッション ──
    "/model": "推論モデル切替 (gemini-3.8-flash ⇄ gemini-4-argon / 3.0-pro)",
    "/thinking": "推論思考強度切替 (High ⇄ Medium ⇄ Low ⇄ Minimal)",
    "/voice": "Gemini Live 女性ボイス(12種)＆トーン(5種)設定 (/voice [name])",
    "/goal": "自律完遂ゴールモード (5層検証ゲート合格まで徹底遂行: /goal <目標>)",
    "/session": "常駐 AntigravitySession の状態検視・リセット (/session [reset])",
    "/compact": "対話コンテキストのロスレス圧縮・トークン節約 (/compact)",
    "/credits": "実測トークン＆日本円利用料金 (JPY) 詳細確認 (/credits [reset])",
    "/context": "コンテキスト消費・履歴剪定ステータス (ContextGuard)",
    "/save": "現在の会話セッションをTUGUMIDeskへ保存 (/save [タイトル])",
    "/reset": "常駐セッション記憶を初期化 (DB履歴は保持)",
    "/clear": "画面クリア＆会話DB履歴・セッション完全リフレッシュ",

    # ── 🔍 リサーチ・ナレッジ・調査 ──
    "/research": "自律ディープリサーチ (SKILL水準レポート自動生成)",
    "/rag": "社内ナレッジ・ドキュメント深層検索＆AI回答 (/rag [質問])",
    "/robin": "Dark Web OSINT 自律調査・16基オニオン検索 (/robin [query/health/list])",
    "/donut": "🍩 Donut & Stealth Browser アンチボット自動化 (/donut [scrape/clone/status])",
    "/briefing": "インテリジェント・デイリーブリーフィング即時生成・予約",
    "/memory": "多層長期記憶の確認・検索・最適化 (指示/好み/エピソード)",
    "/remember": "重要事実やルールを認知記憶へ恒久記録 (/remember)",
    "/reflect": "失敗の内省・5 Whys・Failure Guardログ表示",

    # ── 🎨 クリエイティブ・メディア ──
    "/image": "超リアル実写美女モデル・ポートレート生成・編集 (/image)",
    "/music": "楽曲自動作曲・編曲・MIDI/WAV伴奏・ボーカル生成 (/music)",
    "/dl": "動画/音声ダウンロード (YouTube/X/Bilibili/TikTok/etc.)",
    "/clone": "GitHub自動クローン＆自律エラー修復 (/clone [URL])",

    # ── 🩺 システム診断・保守・運用 ──
    "/status": "Termux＆スマホ健全性リアルタイム診断 (CPU/RAM/Battery)",
    "/doctor": "Termux環境自律整備＆修復 (プロセス回収/ゴミ掃除/Phantom)",
    "/skills": "TUGUMIv6 SKILLエコシステム一覧・検索 (/skills [word])",
    "/mcp": "MCP 2.0 連携サーバー・ツール一覧確認 (/mcp [server])",
    "/subagents": "専門サブエージェント編成目録一覧表示 (/subagents)",
    "/subagent": "専門サブエージェント直接単独実行 (/subagent <name> <指示>)",
    "/skill": "指定スキルの詳細確認・手動強制発動 (/skill <スキル名> [指示])",
    "/verify": "納品前5層検証ゲート自己診断テスト実行",
    "/heal": "自律修復・健全性回復 (全コード構文スキャン＆自動修復)",
    "/sync": "スマホ外部ストレージ (TUGUMIDesk) 双方向同期",
    "/reload": "SKILL・MCP・常駐セッションの無停止ホットリロード (/reload)",
    "/evolve": "自己進化エンジン (SOTA知見探知・10大ピラー監査・ツール合成・RAG注入)",
    "/sdk": "Antigravity SDK 10大進化ピラー・最新仕様検視・エンジン制御 (/sdk)",
    "/binance": "バイナンス実口座AI自律運用・残高・相場・売買 (/binance)",
    "/income": "完全自律不労所得パイプライン・DeFiスプレッド監視",
    "/fpf": "第一原理推論・前提鮮度監査・認識的負債排除 (FPF Core v6)",
    "/senior": "👑 シニアエンジニアクラス業務遂行規約・5大行動規範 (/senior)",
    "/dark": "表裏モード瞬時切替 (つぐみ🌸 ⇄ ダークつぐみ⚡)",
    "/help": "全機能クイックアクションパレット表示",
    "/exit": "CLIセッションを終了してTermuxに戻る",
}

# 2. サブコマンド・モデル定義
MODELS_META: Dict[str, str] = {
    "gemini-3.8-flash": "⚡ 超高速・高知能 主力推論モデル (推奨・日常対話＆高速コーディング)",
    "gemini-4-argon": "🌌 Gemini 4世代フロンティア知能 (1M入出力・超難問・DeepSWEコーディング)",
    "gemini-3.0-pro": "🧠 ディープ推論モデル (深層設計・学術リサーチ)",
    "gemini-3.5-flash": "⚖️ 高速バランス推論モデル",
    "gemini-3.5-flash-lite": "🍃 超軽量・即答モデル (省トークン)",
    "flash": "gemini-3.8-flash のショートカット",
    "argon": "gemini-4-argon のショートカット",
    "pro": "gemini-3.0-pro のショートカット"
}

MCP_META: Dict[str, str] = {
    "failure_guard": "過去の失敗・禁止事項・再発防止チェック (SQLite FTS5)",
    "tugumi_v6": "TUGUMI制御・Termux実行・Shizuku+特権・メモリ・RAG",
    "research": "学術論文(arXiv/PubMed)・Wikipedia・PDF抽出・ドキュメント",
    "osint": "GitHubシークレット探索・Shodan InternetDB・crt.sh",
    "revshell": "リバースシェルTCP待受・対話的制御",
    "twitter": "X (Twitter) スクレイピング・トピック検索",
    "horse_racing": "JRA・地方競馬レースデータ・オッズ・自己学習",
    "robin": "Dark Web OSINT・16基オニオン横断検索",
    "playwright": "ヘッドレスブラウザ・Webスクレイピング・Webクローン",
    "github": "GitHubリポジトリ・PR・コミット・Issue操作",
    "gemini-api-docs-mcp": "Google Gemini 公式APIドキュメント検索",
    "metasploit": "Metasploit RPC MCP連携",
}

ROBIN_META: Dict[str, str] = {
    "threat_intel": "🔍 総合脅威インテリジェンス調査 (/robin threat_intel <query>)",
    "ransomware_malware": "🦠 ランサムウェア・マルウェア・リーク追跡 (/robin ransomware_malware <query>)",
    "personal_identity": "👤 個人情報・認証情報・ID露出調査 (/robin personal_identity <query>)",
    "corporate_espionage": "🏢 企業機密・ソースコード漏洩調査 (/robin corporate_espionage <query>)",
    "search": "⚡ 16基オニオン検索エンジンの高速横断検索 (/robin search <query>)",
    "refine": "🎯 AIによるダークウェブ検索クエリ最適化 (/robin refine <query>)",
    "scrape": "🕸️ 指定.onion URLのTor経由本文抽出 (/robin scrape <url>)",
    "health": "🩺 Torプロキシ＆AIモデル＆16基エンジンの死活監視 (/robin health)",
    "list": "📂 過去のダークウェブ調査レポート履歴一覧 (/robin list)",
    "models": "🤖 Robin MCP で利用可能なAIモデル一覧 (/robin models)",
}

DONUT_META: Dict[str, str] = {
    "scrape": "🛡️ アンチボット完全回避スクレイピング (/donut scrape <URL>)",
    "clone": "🌐 動的SPA完全HTMLクローン保存 (/donut clone <URL>)",
    "status": "🩺 Donut Local API & Termux Stealth 診断 (/donut status)",
    "list": "📁 登録プロファイル一覧 (/donut list)",
    "config": "⚙️ 接続設定の確認・更新 (/donut config)",
}

DOCTOR_META: Dict[str, str] = {
    "fix": "発見された問題を全件自動修復・掃除",
    "inspect": "Termux環境の深層診断レポート表示",
}

BRIEFING_META: Dict[str, str] = {
    "generate": "最新ニュース・技術・相場のブリーフィング即時生成",
    "view": "直近のブリーフィングレポートを閲覧",
    "list": "過去のブリーフィング履歴一覧",
}

BINANCE_META: Dict[str, str] = {
    "status": "💎 実口座総資産・LOT_SIZE売却可否・損益精密診断 (/binance status)",
    "scan": "⚡ 全主要JPYペアのクオンツAlphaランキングスキャン (/binance scan)",
    "patrol": "🛡️ 4層防護パトロール即時実行＆速報レポート生成 (/binance patrol)",
    "backtest": "📈 実ヒストリカルKline戦略バックテスト検証 (/binance backtest)",
    "dust": "🧹 端数資産をBNB(手数料25％割引燃料)へ一括変換 (/binance dust)",
    "buy": "🟢 指定銘柄の成行買い (/binance buy SUI 120)",
    "sell": "🔴 指定銘柄のLOT_SIZE最適化成行売り (/binance sell PEPE)",
    "cron": "⏰ 定期自律パトロール管理 (/binance cron status|start|stop)",
}

SDK_META: Dict[str, str] = {
    "status": "🚀 Antigravity SDK 10大進化ピラー・常駐セッション・Hooks v2 ライブ診断 (/sdk status)",
    "spec": "🔬 google-antigravity SDK 全クラス・26フィールド・Hooks v2 ライブ検視 (/sdk spec)",
    "gap": "📊 10大進化ピラー AST Gap分析＆実機設定検証 (/sdk gap)",
    "verify": "✅ AntigravityEngine.build_config() 実機検証ゲート実行 (/sdk verify)",
    "tools": "🛠️ ネイティブ登録ツール＆動的合成ツール一覧 (/sdk tools)",
    "engine": "⚡ プライマリ推論エンジン切替 (/sdk engine antigravity|gemini)",
    "reset": "🔄 常駐 AntigravitySession クリーンリセット (/sdk reset)",
}

EVOLVE_META: Dict[str, str] = {
    "status": "📊 10大進化ピラー＆システム衛生即時監査 (API消費ゼロ: /evolve status)",
    "check": "✅ Antigravity SDK 10大進化ピラー実機検証ゲート (/evolve check)",
    "gap": "🔍 AST Evolution Gap 分析レポート表示 (/evolve gap)",
    "spec": "🔬 google-antigravity SDK 最新仕様ライブ検視 (/evolve spec)",
    "tools": "🛠️ 自己進化で動的合成されたツール一覧・詳細 (/evolve tools)",
    "audit": "🩺 6大ドメイン・システムアーキテクチャ深層監査 (/evolve audit)",
    "fast": "⚡ 高速自己進化サイクル実行 (SOTA探知＋合成＋高速検証: /evolve fast [topic])",
    "run": "🚀 フル5フェーズ自己進化サイクル実行 (/evolve run [topic])",
}

WEB_META: Dict[str, str] = {
    "start": "WebUIサーバーをバックグラウンド起動＆ブラウザ自動展開",
    "stop": "WebUIサーバーを停止してポート8086を解放",
    "status": "WebUIサーバーの稼働状態・PID・URLを確認",
    "open": "ブラウザで WebUI (http://127.0.0.1:8086/) を開く",
    "restart": "WebUIサーバーを再起動",
}


def load_skills_with_descriptions() -> Dict[str, str]:
    """Reads ~/.agents/skills/*/SKILL.md to extract clean 1-line Japanese descriptions."""
    skills_dir = os.path.expanduser("~/.agents/skills")
    if not os.path.exists(skills_dir):
        return {}

    skills_meta: Dict[str, str] = {}
    try:
        for entry in sorted(os.listdir(skills_dir)):
            skill_path = os.path.join(skills_dir, entry)
            if not os.path.isdir(skill_path) or entry.startswith("."):
                continue

            md_path = os.path.join(skill_path, "SKILL.md")
            desc = ""
            if os.path.exists(md_path):
                try:
                    with open(md_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = [f.readline() for _ in range(25)]
                        content = "".join(lines)
                        # description: ... を探す
                        m = re.search(r'description:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE)
                        if m:
                            desc = m.group(1).strip()
                except Exception:
                    pass

            if not desc:
                # 既知スキルのデフォルト説明
                default_descs = {
                    "taste-skill": "デザイン美学・余白・配色・コードのエレガンス向上",
                    "music-composer-pro": "AI楽曲制作・作曲・編曲・BGM生成",
                    "hit-song-producer-pro": "オリコン・チャート1位級 AI楽曲プロデュース",
                    "systematic-debugging": "第一原理デバッグ・根本原因究明・修正",
                    "test-driven-development": "TDD・5層検証ゲート・カバレッジ保証",
                    "first-principles-engine": "第一原理思考・思い込み排除・前提鮮度監査",
                    "master-writer-pro": "プロフェッショナル執筆・ジャーナリズム・論文作成",
                    "super-judge": "最高峰LLM-as-a-Judge・批判的評価・合意形成",
                    "tree-of-thoughts": "深層論理推論・思考の木・5 Whys分析",
                    "writing-plans": "実行計画策定・タスク分解・WBS管理",
                    "video-downloader": "YouTube/X/TikTok 動画・音声保存",
                    "rich-cli-craftsman": "サイバーパンク/ネオン美学・リッチCLI/TUI開発",
                    "ui-ux-pro-max": "美麗デザイン＆Zero-Mock動くWebUI構築",
                    "ai-model-producer-pro": "商用AI美女モデル・リアルポートレート生成",
                }
                desc = default_descs.get(entry, "TUGUMI 特注専門スキル")

            # 短く分かりやすくカット
            if len(desc) > 38:
                desc = desc[:36] + ".."
            skills_meta[entry] = desc
    except Exception:
        pass

    return skills_meta


class TugumiRichCompleter(Completer):
    """Rich Completer that provides intuitive completions with full Japanese explanations."""

    def __init__(self):
        self._skills_dir = os.path.expanduser("~/.agents/skills")
        self._last_skills_check = 0.0
        self._last_skills_mtime = 0.0
        self.skills_meta = load_skills_with_descriptions()
        self._update_mtime_record()

    def _compute_skills_signature(self) -> float:
        """~/.agents/skills 直下の増減および各サブディレクトリ内の SKILL.md 更新を両方高速検知"""
        if not os.path.exists(self._skills_dir):
            return 0.0
        try:
            max_mtime = os.path.getmtime(self._skills_dir)
            count = 0
            for entry in os.listdir(self._skills_dir):
                if entry.startswith("."):
                    continue
                s_dir = os.path.join(self._skills_dir, entry)
                if os.path.isdir(s_dir):
                    count += 1
                    md_path = os.path.join(s_dir, "SKILL.md")
                    if os.path.exists(md_path):
                        m = os.path.getmtime(md_path)
                        if m > max_mtime:
                            max_mtime = m
            return round(max_mtime + (count * 1e-6), 6)
        except Exception:
            return 0.0

    def _update_mtime_record(self):
        self._last_skills_mtime = self._compute_skills_signature()

    def reload_skills(self, force: bool = False) -> bool:
        """
        ~/.agents/skills および各 SKILL.md の更新日時(mtime)を検査し、
        変更があれば無停止で補完メタデータを再構築 (force=True は無条件で即時再読込)
        """
        now = time.time()
        if not force and (now - self._last_skills_check < 0.5):
            return False

        self._last_skills_check = now
        should_reload = force

        if not should_reload:
            curr_sig = self._compute_skills_signature()
            if curr_sig != self._last_skills_mtime:
                should_reload = True

        if should_reload:
            self.skills_meta = load_skills_with_descriptions()
            self._update_mtime_record()
            return True

        return False

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor
        stripped = text.lstrip()

        # 1. まだコマンド入力中（例: "/" や "/s" など）
        if " " not in stripped:
            word = stripped.lower()
            for cmd, meta in MAIN_COMMANDS.items():
                if cmd.lower().startswith(word):
                    yield Completion(
                        text=cmd,
                        start_position=-len(stripped),
                        display=cmd,
                        display_meta=meta
                    )
            return

        # 2. コマンド入力後のサブ引数補完
        parts = stripped.split(maxsplit=1)
        base_cmd = parts[0].lower()
        sub_word = parts[1].lower() if len(parts) > 1 else ""

        # A. /skill または /skills
        if base_cmd in ("/skill", "/skills"):
            self.reload_skills(force=False)
            for s_name, s_meta in self.skills_meta.items():
                if s_name.lower().startswith(sub_word):
                    yield Completion(
                        text=s_name,
                        start_position=-len(sub_word),
                        display=s_name,
                        display_meta=s_meta
                    )

        # A-2. /subagent
        elif base_cmd == "/subagent":
            subagents_cand = {
                "researcher": "専門リサーチ・RAG知識探索・Web調査サブエージェント",
                "sysops": "システム運用・端末診断・特権実行サブエージェント",
                "code_craftsman": "自律コーディング・精密デバッグサブエージェント"
            }
            for sa_name, sa_meta in subagents_cand.items():
                if sa_name.lower().startswith(sub_word):
                    yield Completion(
                        text=sa_name,
                        start_position=-len(sub_word),
                        display=sa_name,
                        display_meta=sa_meta
                    )

        # B. /mcp
        elif base_cmd == "/mcp":
            for m_name, m_meta in MCP_META.items():
                if m_name.lower().startswith(sub_word):
                    yield Completion(
                        text=m_name,
                        start_position=-len(sub_word),
                        display=m_name,
                        display_meta=m_meta
                    )

        # B2. /robin
        elif base_cmd == "/robin":
            for r_name, r_meta in ROBIN_META.items():
                if r_name.lower().startswith(sub_word):
                    yield Completion(
                        text=r_name,
                        start_position=-len(sub_word),
                        display=r_name,
                        display_meta=r_meta
                    )

        # B3. /donut
        elif base_cmd in ("/donut", "/stealth"):
            for d_name, d_meta in DONUT_META.items():
                if d_name.lower().startswith(sub_word):
                    yield Completion(
                        text=d_name,
                        start_position=-len(sub_word),
                        display=d_name,
                        display_meta=d_meta
                    )

        # B4. /web
        elif base_cmd == "/web":
            for w_name, w_meta in WEB_META.items():
                if w_name.lower().startswith(sub_word):
                    yield Completion(
                        text=w_name,
                        start_position=-len(sub_word),
                        display=w_name,
                        display_meta=w_meta
                    )

        # C. /model
        elif base_cmd == "/model":
            for mod_name, mod_meta in MODELS_META.items():
                if mod_name.lower().startswith(sub_word):
                    yield Completion(
                        text=mod_name,
                        start_position=-len(sub_word),
                        display=mod_name,
                        display_meta=mod_meta
                    )

        # D. /doctor
        elif base_cmd == "/doctor":
            for d_name, d_meta in DOCTOR_META.items():
                if d_name.lower().startswith(sub_word):
                    yield Completion(
                        text=d_name,
                        start_position=-len(sub_word),
                        display=d_name,
                        display_meta=d_meta
                    )

        # E. /briefing
        elif base_cmd == "/briefing":
            for b_name, b_meta in BRIEFING_META.items():
                if b_name.lower().startswith(sub_word):
                    yield Completion(
                        text=b_name,
                        start_position=-len(sub_word),
                        display=b_name,
                        display_meta=b_meta
                    )

        # F. /binance または /crypto
        elif base_cmd in ("/binance", "/crypto"):
            for bn_name, bn_meta in BINANCE_META.items():
                if bn_name.lower().startswith(sub_word):
                    yield Completion(
                        text=bn_name,
                        start_position=-len(sub_word),
                        display=bn_name,
                        display_meta=bn_meta
                    )

        # G. /sdk または /antigravity
        elif base_cmd in ("/sdk", "/antigravity"):
            for sk_name, sk_meta in SDK_META.items():
                if sk_name.lower().startswith(sub_word):
                    yield Completion(
                        text=sk_name,
                        start_position=-len(sub_word),
                        display=sk_name,
                        display_meta=sk_meta
                    )

        # H. /evolve
        elif base_cmd == "/evolve":
            for ev_name, ev_meta in EVOLVE_META.items():
                if ev_name.lower().startswith(sub_word):
                    yield Completion(
                        text=ev_name,
                        start_position=-len(sub_word),
                        display=ev_name,
                        display_meta=ev_meta
                    )
