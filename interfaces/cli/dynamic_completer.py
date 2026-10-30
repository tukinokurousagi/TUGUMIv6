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

# 1. コマンド定義と分かりやすい日本語説明文 (Display Meta)
MAIN_COMMANDS: Dict[str, str] = {
    "/reset": "常駐セッション記憶を初期化 (DB履歴は保持)",
    "/clear": "画面クリア＆会話DB履歴・セッション完全リフレッシュ",
    "/new": "新規会話セッション開始 (/clear と同等)",
    "/dark": "表裏モード瞬時切替 (つぐみ🌸 ⇄ ダークつぐみ⚡)",
    "/light": "通常モード (つぐみ🌸) へ明示的に切替",
    "/senior": "シニアエンジニア業務遂行規約・5大行動規範・検証ゲート確認",
    "/swe": "シニアエンジニア業務遂行規約ショートカット (/senior と同等)",
    "/eval": "Antigravity SDK E2E自己診断・品質テスト実行",
    "/test": "E2Eテスト診断ショートカット (/eval と同等)",
    "/status": "Termux＆スマホ健全性リアルタイム診断 (CPU/RAM/Battery)",
    "/sys": "システム診断ショートカット (/status と同等)",
    "/doctor": "Termux環境自律整備＆修復 (プロセス回収/ゴミ掃除/Phantom)",
    "/reload": "SKILL・MCP・常駐セッションの無停止ホットリロード (/reload)",
    "/skills": "TUGUMIv6 SKILLエコシステム全61種一覧・検索 (/skills [word])",
    "/skill": "指定スキルの詳細確認・手動強制発動 (/skill <スキル名> [指示])",
    "/mcp": "MCP 2.0 連携サーバー・ツール一覧確認 (/mcp [server])",
    "/awm": "AWM自律学習ステータス・ワークフロー一覧・パージ (/awm [list|purge])",
    "/model": "推論モデル切替 (gemini-3.8-flash ⇄ gemini-4-argon / 3.0-pro)",
    "/session": "常駐 AntigravitySession の状態検視・リセット (/session [reset])",
    "/compact": "対話コンテキストのロスレス圧縮・トークン節約 (/compact)",
    "/credits": "実測トークン＆日本円利用料金 (JPY) 詳細確認 (/credits [reset])",
    "/cost": "トークン＆利用料金確認ショートカット (/credits と同等)",
    "/voice": "Gemini Live 女性ボイス(12種)＆トーン(5種)設定 (/voice [name])",
    "/goal": "自律完遂ゴールモード (5層検証ゲート合格まで徹底遂行: /goal <目標>)",
    "/briefing": "インテリジェント・デイリーブリーフィング即時生成・予約",
    "/music": "楽曲自動作曲・編曲・MIDI/WAV伴奏・ボーカル生成 (/music)",
    "/compose": "楽曲制作ショートカット (/music と同等)",
    "/image": "実写美女・ポートレート・画像生成・編集・合成 (/image)",
    "/img": "画像生成ショートカット (/image と同等)",
    "/photo": "超リアル実写美女モデル生成ショートカット",
    "/dl": "動画/音声ダウンロード (YouTube/X/Bilibili/TikTok/etc.)",
    "/clone": "GitHub自動クローン＆自律エラー修復 (/clone [URL])",
    "/robin": "Dark Web OSINT 自律調査・16基オニオン検索 (/robin [query/health/list])",
    "/research": "自律ディープリサーチ (SKILL水準レポート自動生成)",
    "/rag": "社内ナレッジ・ドキュメント深層検索＆AI回答 (/rag [質問])",
    "/memory": "多層長期記憶の確認・検索・最適化 (指示/好み/エピソード)",
    "/remember": "重要事実やルールを認知記憶へ恒久記録 (/remember)",
    "/reflect": "失敗の内省・5 Whys・Failure Guardログ表示",
    "/income": "完全自律不労所得パイプライン・DeFiスプレッド監視",
    "/binance": "バイナンス実口座AI自律運用・残高・相場・売買 (/binance)",
    "/verify": "納品前5層検証ゲート自己診断テスト実行",
    "/heal": "自律修復・健全性回復 (全コード構文スキャン＆自動修復)",
    "/sync": "スマホ外部ストレージ (TUGUMIDesk) 双方向同期",
    "/evolve": "自己進化エンジン (SOTA知見探知・監査・RAG注入)",
    "/context": "コンテキスト消費・履歴剪定ステータス (ContextGuard)",
    "/save": "現在の会話セッションをTUGUMIDeskへ保存 (/save [タイトル])",
    "/thinking": "推論思考強度切替 (High ⇄ Medium ⇄ Low ⇄ Minimal)",
    "/think": "思考強度切替ショートカット (/thinking と同等)",
    "/high": "思考強度を HIGH (最大推論・コード・設計) に即時切替",
    "/medium": "思考強度を MEDIUM (標準推論・日常対話) に即時切替",
    "/low": "思考強度を LOW (高速応答・短文返答) に即時切替",
    "/minimal": "思考強度を MINIMAL (超低遅延即答) に即時切替",
    "/fpf": "第一原理推論・前提鮮度監査・認識的負債排除 (FPF Core v6)",
    "/help": "全機能クイックアクションパレット表示",
    "/exit": "CLIセッションを終了してTermuxに戻る",
    "/quit": "CLIセッションを終了してTermuxに戻る",
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

    def _update_mtime_record(self):
        try:
            if os.path.exists(self._skills_dir):
                self._last_skills_mtime = os.path.getmtime(self._skills_dir)
        except Exception:
            pass

    def reload_skills(self, force: bool = False) -> bool:
        """
        ~/.agents/skills の更新日時(mtime)を検査し、変更があれば無停止で補完メタデータを再構築
        force=True の場合は無条件で即時再読込
        """
        now = time.time()
        if not force and (now - self._last_skills_check < 0.5):
            return False

        self._last_skills_check = now
        should_reload = force

        if not should_reload:
            try:
                if os.path.exists(self._skills_dir):
                    curr_mtime = os.path.getmtime(self._skills_dir)
                    if curr_mtime != self._last_skills_mtime:
                        should_reload = True
            except Exception:
                pass

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
