# -*- coding: utf-8 -*-
"""
TUGUMIv6 Capability Inspector
=============================
Unified inspection engine for SKILL ecosystem and MCP (Model Context Protocol) servers.
Provides structured data for CLI Rich visualization and Web UI REST APIs.

Master: 拓磨様
Engine: TUGUMIv6 Cognitive & Tool Architecture
"""

import os
import re
import json
import time
import datetime
from typing import Dict, Any, List, Optional

HOME = os.path.expanduser("~")
LOCAL_SKILLS_DIR = os.path.join(HOME, "TUGUMIv6", "skills")
GLOBAL_SKILLS_DIR = os.path.join(HOME, ".agents", "skills")
MCP_CONFIG_DIR = os.path.join(HOME, ".gemini", "antigravity-cli", "mcp")


def categorize_skill(name: str) -> str:
    """スキル名から直感的な専門ドメインカテゴリを分類"""
    name_lower = name.lower()
    if any(k in name_lower for k in ["robin", "penetration", "nmap", "security"]):
        return "セキュリティ・OSINT"
    elif any(k in name_lower for k in ["craftsman", "github", "test", "tdd", "regression", "root-cause", "subagent", "git", "coding", "ruff", "prompt"]):
        return "SWE & 開発工学"
    elif any(k in name_lower for k in ["brainstorming", "tree-of-thoughts", "writing-plans", "judge", "systematic-debugging", "analyse", "first-principles", "fpf"]):
        return "推論・計画・デバッグ"
    elif any(k in name_lower for k in ["binance", "crypto", "defi", "arbitrage", "income"]):
        return "副業・暗号資産"
    elif any(k in name_lower for k in ["video", "audio", "ascii", "art", "canvas", "slack-gif", "media", "music", "song", "idol", "model-producer"]):
        return "メディア・クリエイティブ"
    elif any(k in name_lower for k in ["psycholog", "counsel"]):
        return "心理分析・カウンセリング"
    elif any(k in name_lower for k in ["rokujin", "fortune", "senji"]):
        return "鑑定・六壬神課"
    elif any(k in name_lower for k in ["vita", "srw", "save"]):
        return "データ救済・バイナリ"
    elif any(k in name_lower for k in ["shizuku", "termux", "tasker", "sqlite", "context-compression", "env"]):
        return "システム・Android特権"
    elif any(k in name_lower for k in ["writer", "reporter", "wiki", "obsidian", "doc", "pdf", "docx", "pptx", "xlsx", "gossip", "horse"]):
        return "リサーチ・ナレッジ生成"
    elif any(k in name_lower for k in ["mcp", "evolution", "guard", "agent", "skill"]):
        return "自律進化・プロトコル"
    return "汎用拡張"


class SkillInspector:
    """TUGUMIv6 SKILLエコシステムの深層調査エンジン"""

    def __init__(self, local_dir: str = LOCAL_SKILLS_DIR, global_dir: Optional[str] = GLOBAL_SKILLS_DIR):
        self.local_dir = local_dir
        self.global_dir = global_dir

    def _get_search_dirs(self) -> List[str]:
        """正本 (~/.agents/skills) を最優先し、ローカルをフォールバックとして取得"""
        dirs = []
        if self.global_dir and os.path.exists(self.global_dir):
            dirs.append(self.global_dir)
        if self.local_dir and os.path.exists(self.local_dir) and self.local_dir not in dirs:
            dirs.append(self.local_dir)
        return dirs

    def list_skills(self) -> List[Dict[str, Any]]:
        """配備されている全SKILLの一覧とメタデータを構造化取得"""
        skills = []
        seen = set()

        # 正本 (~/.agents/skills) を最優先スキャン（規約第5章 5.3 厳選61-63種正本準拠）
        search_dirs = self._get_search_dirs()

        for s_dir in search_dirs:
            if not os.path.exists(s_dir):
                continue
            for entry in sorted(os.listdir(s_dir)):
                if entry.startswith(".") or entry in seen:
                    continue
                full_path = os.path.join(s_dir, entry)
                skill_md_path = os.path.join(full_path, "SKILL.md")

                if os.path.isdir(full_path) and os.path.exists(skill_md_path):
                    seen.add(entry)
                    meta = self._parse_skill_md(skill_md_path, entry)
                    scripts_dir = os.path.join(full_path, "scripts")
                    has_scripts = os.path.exists(scripts_dir) and len(os.listdir(scripts_dir)) > 0
                    tools_dir = os.path.join(full_path, "tools")
                    has_tools = (os.path.exists(tools_dir) and len(os.listdir(tools_dir)) > 0) or ("tool" in meta.get("description", "").lower())
                    
                    skills.append({
                        "name": entry,
                        "title": meta.get("name", entry),
                        "description": meta.get("description", "説明なし"),
                        "category": categorize_skill(entry),
                        "path": full_path,
                        "is_symlink": os.path.islink(full_path),
                        "has_scripts": has_scripts,
                        "has_tools": has_tools,
                        "status": "Active"
                    })

        return sorted(skills, key=lambda x: (x["category"], x["name"]))

    def get_skill_detail(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """特定SKILLのMarkdown全文、スクリプト一覧等の詳細を取得"""
        search_dirs = self._get_search_dirs()
        for s_dir in search_dirs:
            full_path = os.path.join(s_dir, skill_name)
            skill_md = os.path.join(full_path, "SKILL.md")
            if os.path.exists(skill_md):
                try:
                    with open(skill_md, "r", encoding="utf-8", errors="ignore") as f:
                        raw_content = f.read()
                    
                    scripts = []
                    scripts_dir = os.path.join(full_path, "scripts")
                    if os.path.exists(scripts_dir):
                        scripts = [f for f in os.listdir(scripts_dir) if not f.startswith(".")]

                    meta = self._parse_skill_md(skill_md, skill_name)
                    return {
                        "name": skill_name,
                        "description": meta.get("description", ""),
                        "category": categorize_skill(skill_name),
                        "path": full_path,
                        "content": raw_content,
                        "scripts": scripts,
                        "status": "Active"
                    }
                except Exception as e:
                    return {"name": skill_name, "error": str(e)}
        return None

    def _parse_skill_md(self, filepath: str, fallback_name: str) -> Dict[str, str]:
        """SKILL.md の YAML フロントマターから name / description を抽出"""
        res = {"name": fallback_name, "description": ""}
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(4096)
            
            # YAML Frontmatter (---\n ... \n---)
            m = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
            if m:
                fm = m.group(1)
                for line in fm.splitlines():
                    if line.startswith("name:"):
                        res["name"] = line.replace("name:", "").strip().strip("'\"")
                    elif line.startswith("description:"):
                        res["description"] = line.replace("description:", "").strip().strip("'\"")
            
            # フロントマターがない場合のフォールバック（# タイトル、または最初の段落）
            if not res["description"]:
                lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#") and not l.startswith("---")]
                if lines:
                    res["description"] = lines[0][:150]
        except Exception:
            pass
        return res


MCP_TOOL_JA_DESCRIPTIONS = {
    # tugumi_v6
    "tugumi_exec": "Termux Linux環境（Android aarch64）上でBashシェルコマンドを実行します。",
    "tugumi_privileged_exec": "Android Termux環境にてShizuku/rish、su、またはフォールバックを用いて特権・昇格コマンドを実行します。",
    "tugumi_device_telemetry": "Android実機のバッテリー残量・温度・メモリ使用状況・システム稼働時間などのテレメトリ情報を取得します。",
    "tugumi_memory_recall": "エビングハウス忘却曲線スコアリングに対応したTUGUMIv6の4層永続記憶（作業・エピソード・意味・手続き）を検索・想起します。",
    "tugumi_memory_store": "重要な知見、失敗教訓、拓磨様の好み・方針、または実行手順をTUGUMIv6の4層永続記憶へ安全に保存・定着させます。",
    "tugumi_rag_query": "ローカルドキュメント、リファレンス実装、技術ナレッジを対象に、TUGUMIv6のハイブリッドRAG知識ベースを検索します。",
    "tugumi_music_compose": "Billboard/オリコン1位級 AI楽曲プロデュース・作詞・音響合成 (hit-song-producer-pro SKILL準拠)",
    "tugumi_check_health": "Termux Linux環境およびTUGUMIv6システム全体の包括的な診断・ヘルスチェックを実行します。",

    # failure_guard
    "check_failure_risk": "危険な操作や不慣れな作業を実行する前に、過去の失敗教訓・アンチパターン・禁止事項をSQLite FTS5から事前検索します。",
    "record_failure_lesson": "新しく発見された失敗・アンチパターン・技術的教訓をSQLite FTS5失敗記憶データベースへ永続記録します。",
    "list_recent_failures": "最近記録された失敗教訓・アンチパターンの一覧を取得します。",

    # twitter
    "get_user_tweets": "指定したX（旧Twitter）ユーザーの最新ツイート一覧を取得します。",
    "search_x_topics": "X（旧Twitter）上の特定の話題、キーワード、事件・トレンドに関する言説や世論をWeb検索経由で収集・調査します。",

    # osint
    "github_search_code": "GitHub公開リポジトリから機密情報（APIキー、トークン、認証情報）やコードパターンを高速検索します。",
    "shodan_internetdb_lookup": "Shodan InternetDB APIを用いて、対象IPアドレスの開放ポート、稼働サービス、既知脆弱性（CVE）を照会します。",
    "crt_sh_subdomain_enum": "crt.sh のSSL/TLS証明書透明性ログを解析し、対象ドメインに紐づくサブドメイン一覧を網羅列挙します。",

    # revshell
    "revshell_start_listener": "リバースシェル接続を受信するためのローカルTCPリスナーを起動します。",
    "revshell_check_status": "ターゲットからリバースシェル接続が確立されているか確認し、保留中のシェル出力を読み取ります。",
    "revshell_send_command": "接続中のリバースシェルに対してBashコマンドを送信し、即時出力を自動的に読み取ります。",

    # horse_racing
    "race_resolve": "自然言語のレース指定（開催日、競馬場名、レース番号）を一意に検証・確定された正規レース情報に変換・特定します。",
    "race_card": "指定されたレースIDの確定出馬表（馬番、馬名、性齢、斤量、騎手、調教師）を取得します。",
    "validate": "レース同一性、出走頭数の完全性、馬番と馬名の対応整合性、および買い目チケットの妥当性を厳格に検証します。",
    "horse_history": "指定された馬ID（horse_id）の過去レース戦績、走破時計、着順、通過順位などの履歴データを取得します。",
    "market": "指定レースの最新リアルタイムオッズ情報（単勝・複勝・馬連・ワイド等）を取得します。",
    "race_context": "指定レースの馬場状態（芝・ダート、良・稍重・重・不良）、天候、トラックバイアスおよび展開傾向を取得します。",
    "race_dossier": "出走馬一覧、リアルタイムオッズ、馬場バイアスを含む総合ドシエ（全情報）を一括即時収集します。",
    "report_save": "生成された競馬予測MarkdownレポートをAndroid/TUGUMIDeskストレージへ安全に永続保存します。",
    "race_results": "レース確定後の公式確定着順、確定タイム、払戻金（単勝・複勝・馬連・三連単等）を取得します。",
    "race_learn": "確定着順と事前予測を比較検証し、特徴量重みの自己調整および回顧知見の自己学習アップデートを実行します。",

    # robin
    "robin_search": "Torネットワーク経由で16基のオニオン検索エンジンを横断し、単一クエリでダークウェブを一括探索します。",
    "robin_refine": "ユーザーの質問や調査目的を、ダークウェブ検索に適した5単語以内の推敲された検索クエリに変換・洗練します。",
    "robin_filter": "直前の検索結果から、調査トピックやクエリの目的に真に合致する結果のみを精緻に判定・絞り込みます。",
    "robin_scrape": "Torネットワーク経由で指定されたオニオンWebページを安全に読み込み、テキストデータを抽出して返します。",
    "robin_investigate": "推敲・探索・絞込・スクレイピング・要約・保存を一気通貫で全自動実行します。",
    "robin_save_investigation": "Robinの検索・スクレイピング結果から作成した脅威インテリジェンス調査レポートを永続保存します。",
    "robin_list_models": "Robinが調査や推論に利用可能なモデル一覧を取得します。",
    "robin_health": "Torネットワークの接続状態、オニオン検索エンジンの稼働状況およびモデルヘルスを診断します。",
    "robin_list_investigations": "保存されている過去の脅威インテリジェンス調査レポート一覧を新しい順に取得します。",

    # playwright
    "playwright_scrape": "Puppeteer（ヘッドレスChromium）を用いてWebページをスクレイピングします。SPAやJavaScript動的描画サイトの本文抽出に最適です。",
    "puppeteer_clone_page": "Puppeteer（ヘッドレスChromium）を用いてWebページを完全にクローン保存します。",

    # metasploit
    "list_exploits": "利用可能なMetasploitエクスプロイトモジュール一覧を取得・検索します。",
    "list_payloads": "利用可能なMetasploitペイロード一覧を取得・検索します。",
    "generate_payload": "指定した設定でMetasploitペイロードバイナリ/シェルコードを生成します。",
    "run_exploit": "指定ターゲットに対してMetasploitエクスプロイトモジュールを実行します。",
    "run_post_module": "確立されたセッション上でポストエクスプロイトモジュールを実行します。",
    "run_auxiliary_module": "Metasploitオーグジュアリモジュール（スキャナー、DoS、Fuzzer等）を実行します。",
    "list_active_sessions": "現在確立されているアクティブなMetasploitセッション一覧を取得します。",
    "send_session_command": "アクティブなセッションに対してコマンドを送信・実行します。",
    "list_listeners": "現在稼働中のハンドラー・リスナージョブ一覧を取得します。",
    "start_listener": "リバースシェル待受用ハンドラー（multi/handler）を起動します。",
    "stop_job": "稼働中のMetasploitジョブを停止します。",
    "terminate_session": "指定したMetasploitセッションを切断・終了します。",

    # gemini-api-docs-mcp
    "gemini_search_docs": "Google Gemini APIおよびGenAI SDKの公式最新ドキュメントを検索します。",
    "gemini_get_doc": "ドキュメントID（chunk_id）を指定して公式ドキュメントページの全文を取得します。",

    # github
    "add_comment_to_pending_review": "作成中の保留中プルリクエストレビューにレビューコメントを追加します。",
    "add_issue_comment": "指定したGitHub Issueまたはコメントに対して返信コメントやリアクションを追加します。",
    "add_reply_to_pull_request_comment": "既存のプルリクエストコメントに対してインライン返信やリアクションを追加します。",
    "assign_copilot_to_issue": "GitHubリポジトリの特定のIssueにGitHub Copilotを割り当てます。",
    "create_branch": "GitHubリポジトリに新しいブランチを作成します。",
    "create_or_update_file": "GitHubリポジトリ内の単一ファイルを作成または更新（コミット）します。",
    "create_pull_request": "GitHubリポジトリに新しいプルリクエスト（PR）を作成します。",
    "create_repository": "アカウントまたは指定組織に新しいGitHubリポジトリを作成します。",
    "delete_file": "GitHubリポジトリから指定ファイルを削除（コミット）します。",
    "fork_repository": "GitHubリポジトリを自身のアカウントまたは組織へフォークします。",
    "get_commit": "GitHubリポジトリの特定のコミット詳細情報を取得します。",
    "get_file_contents": "GitHubリポジトリ内のファイルまたはディレクトリの内容を取得します。",
    "get_label": "GitHubリポジトリに登録されている特定のラベル情報を取得します。",
    "get_latest_release": "GitHubリポジトリの最新リリース情報を取得します。",
    "get_me": "現在認証されているGitHubユーザーのアカウント詳細情報を取得します。",
    "get_release_by_tag": "指定されたタグ名に対応するGitHubリリース情報を取得します。",
    "get_tag": "GitHubリポジトリ内の特定のGitタグ詳細情報を取得します。",
    "get_team_members": "GitHub組織内の特定チームに所属するメンバー一覧を取得します。",
    "get_teams": "認証ユーザーが所属しているGitHub組織内のチーム一覧を取得します。",
    "issue_read": "GitHubリポジトリの特定のIssueの詳細情報を取得します。",
    "issue_write": "GitHubリポジトリに新しいIssueを作成、または既存Issueを更新します。",
    "list_branches": "GitHubリポジトリのブランチ一覧を取得します。",
    "list_commits": "GitHubリポジトリの指定ブランチのコミット履歴一覧を取得します。",
    "list_issue_fields": "リポジトリまたは組織で定義されているIssueフィールド一覧を取得します。",
    "list_issue_types": "サポートされているIssueタイプ一覧を取得します。",
    "list_issues": "GitHubリポジトリのIssue一覧を取得します。",
    "list_pull_requests": "GitHubリポジトリのプルリクエスト一覧を取得します。",
    "list_releases": "GitHubリポジトリのリリース一覧を取得します。",
    "list_repository_collaborators": "GitHubリポジトリのコラボレーター（共同開発者）一覧を取得します。",
    "list_tags": "GitHubリポジトリのGitタグ一覧を取得します。",
    "merge_pull_request": "GitHubリポジトリのプルリクエストをマージします。",
    "pull_request_read": "特定のプルリクエストの詳細情報を取得します。",
    "pull_request_review_write": "プルリクエストのレビューを作成・提出・削除します。",
    "push_files": "複数のファイルを単一のコミットとしてGitHubリポジトリへプッシュします。",
    "request_copilot_review": "プルリクエストに対してGitHub Copilotコードレビューをリクエストします。",
    "search_code": "GitHubコード検索構文を用いて全GitHubリポジトリを対象にコードを高速検索します。",
    "search_commits": "GitHubコミット検索構文を用いてリポジトリ横断でコミットを検索します。",
    "search_issues": "GitHub Issue検索構文を用いてリポジトリ横断でIssueを検索します。",
    "search_pull_requests": "GitHub検索構文を用いてリポジトリ横断でプルリクエストを検索します。",
    "search_repositories": "リポジトリ名、説明文、トピック等からGitHubリポジトリを横断検索します。",
    "search_users": "ユーザー名、本名、プロフィール情報からGitHubユーザーを検索します。",
    "sub_issue_write": "GitHubリポジトリの親IssueにサブIssueを追加します。",
    "update_pull_request": "既存のプルリクエストのタイトル、本文、状態等を更新します。",
    "update_pull_request_branch": "プルリクエストのブランチをベースブランチの最新変更で更新します。"
}


class MCPInspector:
    """TUGUMIv6 MCP (Model Context Protocol) サーバー・ツール深層調査エンジン"""

    def __init__(self, mcp_dir: str = MCP_CONFIG_DIR):
        self.mcp_dir = mcp_dir

    def list_servers(self) -> List[Dict[str, Any]]:
        """登録・連携されている全MCPサーバーと各ツールの概要を取得"""
        servers = []
        if not os.path.exists(self.mcp_dir):
            return servers

        for entry in sorted(os.listdir(self.mcp_dir)):
            server_dir = os.path.join(self.mcp_dir, entry)
            if not os.path.isdir(server_dir) or entry.startswith("."):
                continue

            tools = []
            instructions = ""

            for fname in sorted(os.listdir(server_dir)):
                fpath = os.path.join(server_dir, fname)
                if fname.endswith(".json"):
                    tool_name = fname[:-5]
                    tool_info = self._parse_tool_schema(fpath, tool_name)
                    tools.append(tool_info)
                elif fname.lower() == "instructions.md":
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            instructions = f.read(500).strip()
                    except Exception:
                        pass

            servers.append({
                "name": entry,
                "server_name": entry,
                "status": "Active (MCP 2.0)",
                "tool_count": len(tools),
                "tools": tools,
                "instructions_preview": instructions[:120] if instructions else "なし",
                "path": server_dir
            })

        return servers

    def get_server_detail(self, server_name: str) -> Optional[Dict[str, Any]]:
        """特定MCPサーバーの全ツールJSONスキーマ詳細を取得 (オンデマンドライブ取得フォールバック対応)"""
        server_dir = os.path.join(self.mcp_dir, server_name)
        if not os.path.exists(server_dir) or not os.path.isdir(server_dir):
            try:
                from tools.tugumi_mcp import mcp as live_mcp
                live_tools = live_mcp.list_tools(server_name)
                if live_tools:
                    formatted_tools = []
                    for t in live_tools:
                        t_name = t.get("name", "")
                        t_desc = MCP_TOOL_JA_DESCRIPTIONS.get(t_name, t.get("description", "説明なし")).split("\n")[0]
                        schema = t.get("inputSchema", t.get("parameters", {}))
                        formatted_tools.append({
                            "name": t_name,
                            "description": t_desc,
                            "parameters": schema,
                            "schema_raw": t
                        })
                    return {
                        "name": server_name,
                        "server_name": server_name,
                        "status": "On-Demand (MCP 2.0 Ephemeral)",
                        "tool_count": len(formatted_tools),
                        "instructions": "On-Demand Ephemeral MCP Server",
                        "tools": formatted_tools,
                        "path": "~/.gemini/config/mcp_config.json"
                    }
            except Exception:
                pass
            return None

        tools = []
        instructions = ""
        instructions_path = os.path.join(server_dir, "instructions.md")
        if os.path.exists(instructions_path):
            try:
                with open(instructions_path, "r", encoding="utf-8", errors="ignore") as f:
                    instructions = f.read()
            except Exception:
                pass

        for fname in sorted(os.listdir(server_dir)):
            if fname.endswith(".json"):
                fpath = os.path.join(server_dir, fname)
                tool_name = fname[:-5]
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        schema = json.load(f)
                    desc = schema.get("description", "")
                    if not desc or desc == "説明なし" or tool_name in MCP_TOOL_JA_DESCRIPTIONS:
                        desc = MCP_TOOL_JA_DESCRIPTIONS.get(tool_name, desc or "説明なし")
                    tools.append({
                        "name": tool_name,
                        "description": desc,
                        "parameters": schema.get("parameters", {}),
                        "schema_raw": schema
                    })
                except Exception as e:
                    tools.append({"name": tool_name, "error": str(e)})

        return {
            "name": server_name,
            "server_name": server_name,
            "status": "Active (MCP 2.0)",
            "tool_count": len(tools),
            "instructions": instructions,
            "tools": tools,
            "path": server_dir
        }

    def _parse_tool_schema(self, filepath: str, fallback_name: str) -> Dict[str, Any]:
        """JSONスキーマからツール名、説明、必須引数を抽出"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            params = data.get("parameters", {})
            properties = params.get("properties", {})
            required = params.get("required", [])
            args_summary = ", ".join(f"{k}*" if k in required else k for k in properties.keys())

            desc = data.get("description", "")
            if not desc or desc == "説明なし" or fallback_name in MCP_TOOL_JA_DESCRIPTIONS:
                desc = MCP_TOOL_JA_DESCRIPTIONS.get(fallback_name, desc or "説明なし")

            return {
                "name": fallback_name,
                "description": desc.split("\n")[0][:120],
                "args_summary": args_summary or "引数なし",
                "required_args": required
            }
        except Exception as e:
            return {"name": fallback_name, "description": f"Schema load error: {e}", "args_summary": "-"}


def inspect_fpf_status() -> Dict[str, Any]:
    """FPF (First-Principles Framework) 前提鮮度・認識的負債監査"""
    skill_path = os.path.join(GLOBAL_SKILLS_DIR, "first-principles-engine", "SKILL.md")
    skill_active = os.path.exists(skill_path)

    core_files = [
        os.path.join(HOME, "TUGUMIv6", "engine_config.json"),
        os.path.join(HOME, "TUGUMIv6", "persona", "soul.py"),
        os.path.join(HOME, "TUGUMIv6", "core", "engine_manager.py"),
        os.path.join(HOME, ".agents", "TSUGUMI_MEMORY.md"),
    ]
    file_audits = []
    now = time.time()
    for fp in core_files:
        if os.path.exists(fp):
            mtime = os.path.getmtime(fp)
            dt = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            age_hours = (now - mtime) / 3600
            freshness = "Fresh" if age_hours < 48 else "Moderate" if age_hours < 168 else "Decayed"
            file_audits.append({
                "file": os.path.basename(fp),
                "path": fp,
                "updated_at": dt,
                "freshness": freshness,
                "age_hours": round(age_hours, 1)
            })

    decayed_count = sum(1 for f in file_audits if f["freshness"] == "Decayed")
    debt_score = max(0, 100 - (decayed_count * 20))

    return {
        "engine_active": skill_active,
        "engine_name": "first-principles-engine (FPF Core v6)",
        "evidence_freshness_status": "EXCELLENT" if debt_score >= 80 else "WARNING",
        "epistemic_debt_score": debt_score,
        "files_audited": file_audits,
        "core_tenets": [
            "Evidence is perishable (証拠は生鮮食品である)",
            "Anti-Cutoff Bias (オフカット知識・一般論の疑念化)",
            "Context Drift Guard (変更差分からの前提崩壊自動検知)",
            "First-Principles Reset (物理的事実・入出力からゼロベース再構築)"
        ]
    }

