"""
TUGUMIv6 フルスペック不可侵 ＆ 暴走バグ再発防止 ガードテスト (test_anti_downgrade_guard.py)
拓磨様の厳命に基づく「思考・コンテキスト・RAG・ツール・SKILL・MCPのダウングレード永久禁止（Switch 2 原則）」
および「API多重呼び出し暴走バグの再発防止」をコードレベルで強制検証する。
"""

import inspect
from pathlib import Path

from core.antigravity_sdk import AntigravityEngine
from core.gemini_client import GeminiClient
from core.autoheal import AutoHealEngine
from memory.rag_engine import HybridRAGEngine


def test_full_spec_no_downgrade_antigravity_sdk():
    """コンテキスト保持量(150,000)・Thinking(high)・全ツール/SKILL/全MCPが一切制限されていないことを検証"""
    src = inspect.getsource(AntigravityEngine.build_config)
    assert "token_threshold=150000" in src, "【規約違反】コンテキスト保持量(token_threshold=150000)がダウングレードされています！"
    assert "GeminiModelOptions(thinking_level=active_level)" in src, "【規約違反】thinking_level 設定が欠落しています！"
    assert "enable_subagents=True" in src
    assert "policy.allow_all()" in src
    assert '"/data/data/com.termux/files/home/.agents/skills"' in src

    mcp_src = inspect.getsource(AntigravityEngine._resolve_dynamic_mcp_servers)
    assert "any(k in p_lower" not in mcp_src, "【規約違反】MCPサーバーにキーワード制限(利用制限)がかけられています！"

    init_src = inspect.getsource(GeminiClient._build_thinking_config)
    assert "include_thoughts=True" in init_src, "【規約違反】GeminiClient の include_thoughts=True が無効化されています！"


def test_rag_semantic_search_full_spec():
    """RAGの3072次元セマンティック検索(embed_missing=True)がデフォルト有効であることを検証"""
    sig = inspect.signature(HybridRAGEngine.ingest_all)
    assert sig.parameters["embed_missing"].default is True, "【規約違反】RAGのembed_missingがFalseにダウングレードされています！"


def test_no_mutual_recursion_in_gemini_client():
    """generate_content と generate_content_stream の相互再帰暴走バグが存在しないことを検証"""
    gen_src = inspect.getsource(GeminiClient.generate_content)
    stream_src = inspect.getsource(GeminiClient.generate_content_stream)
    assert "self.generate_content_stream(" not in gen_src, "【暴走バグ再発】generate_content が generate_content_stream を呼んでいます！"
    assert "self.generate_content(" not in stream_src, "【暴走バグ再発】generate_content_stream が generate_content を呼んでいます！"


def test_no_llm_call_in_autoheal():
    """AutoHealが裏で勝手にLLM APIを呼び出さないことを検証"""
    heal_src = inspect.getsource(AutoHealEngine.heal_file_syntax)
    assert "generate_content(" not in heal_src, "【暴走バグ再発】AutoHealが裏で勝手にLLM APIを呼び出しています！"


def test_tugumi_v5_remains_deleted():
    """廃止された TUGUMIv5 が復活していないことを検証"""
    v5_dir = Path("/data/data/com.termux/files/home/TUGUMIv5")
    assert not v5_dir.exists(), "【規約違反】完全削除されたはずの TUGUMIv5 ディレクトリが存在します！"


def test_no_deceptive_mock_or_benchmark_hardcoding_in_dark_tugumi():
    """DARK-TUGUMI にテスト通過目的のハードコード偽装やツール未実行での虚偽完了報告が存在しないことを検証"""
    graph_file = Path("/data/data/com.termux/files/home/DARK-TUGUMI/dark_tugumi/graph.py")
    tools_file = Path("/data/data/com.termux/files/home/DARK-TUGUMI/dark_tugumi/tools.py")
    assert graph_file.is_file() and tools_file.is_file()

    graph_src = graph_file.read_text(encoding="utf-8")
    tools_src = tools_file.read_text(encoding="utf-8")

    # 1. 前任者が仕込んだデモ専用のインチキハードコードが完全に排除されていること
    forbidden_cheats = [
        "production-penetration-testing/SKILL.md",
        'cmd = cmd_m.group(1) if cmd_m else "uname -a && ls -la"',
        "Completed by DARK-TUGUMI.",
    ]
    for cheat in forbidden_cheats:
        assert cheat not in graph_src, f"【欺瞞コード検知】デモ専用ハードコード '{cheat}' が残存しています！"

    # 2. ツール未実行時に完了(done)と偽ることを物理遮断する Anti-Deception Gate が実装されていること
    assert "Anti-Deception Gate" in graph_src, "【規約違反】ツール未実行時の虚偽報告遮断ゲート (Anti-Deception Gate) が欠落しています！"
    assert "[ERROR] ツール未実行" in graph_src

    # 3. 必須実働ツール (Metasploit MCP / 汎用MCP / レポート保存) が実働ワーカーにマウントされていること
    assert "def metasploit_mcp(" in tools_src
    assert "def mcp_call(" in tools_src
    assert "save_report_to_desk" in tools_src


def test_tugumi_v6_core_functions_not_restricted_by_binance():
    """バイナンス優先によるTUGUMIv6基本機能の制限・ダウングレードが存在しないことを検証"""
    import json
    from core.gemini_client import _resolve_gemini_api_key

    # 1. engine_config.json の thinking_level が "high" (Switch 2 フルスペック) であること
    cfg_path = Path("/data/data/com.termux/files/home/TUGUMIv6/engine_config.json")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert cfg.get("thinking_level") == "high", "【規約違反】engine_config.json の thinking_level が high からダウングレードされています！"

    # 2. 非対話環境 (cron / デイリーブリーフィング等) でも API キーが確実に解決されること
    resolved_key = _resolve_gemini_api_key("")
    assert len(resolved_key) > 20, "【規約違反】非対話環境で Gemini API キーが解決できず、デイリーブリーフィング等の基本機能が遮断されています！"

    # 3. WebUI チャット (/api/chat) が自然言語メッセージを /binance 固定コマンドへ強制横取りしていないこと
    web_srv_path = Path("/data/data/com.termux/files/home/TUGUMIv6/interfaces/web/web_server.py")
    web_src = web_srv_path.read_text(encoding="utf-8")
    assert 'execute_slash_command("/binance scan"' not in web_src, (
        "【規約違反】WebUIチャットがAI推論をバイパスして /binance scan へ強制インターセプトしています！"
    )
    assert 'execute_slash_command("/binance balance"' not in web_src, (
        "【規約違反】WebUIチャットがAI推論をバイパスして /binance balance へ強制インターセプトしています！"
    )

    # 4. Gemini Live API (/api/live/ws) が _resolve_gemini_api_key を使用し、即時Web検索・長期記憶・メディア生成ツールを完備していること
    assert "_resolve_gemini_api_key" in web_src
    for live_tool in ("search_web_realtime", "recall_tugumi_memory", "generate_creative_media"):
        assert f'"name": "{live_tool}"' in web_src, f"【規約違反】Gemini Live API から基本ツール '{live_tool}' が欠落しています！"


def test_skill_ecosystem_full_coverage_and_contract_integrity():
    """SKILLエコシステムが正本(~/.agents/skills)から全数認識され、UIデータ契約(has_tools等)を満たすことを検証"""
    from core.capability_inspector import SkillInspector
    insp = SkillInspector()
    skills = insp.list_skills()
    
    # 1. 認識SKILL数が正本(>=60件)であること(足切り・探索漏れ排除)
    assert len(skills) >= 60, f"【規約違反】認識SKILL数が {len(skills)}件 に激減しています！正本(~/.agents/skills)をスキャンしてください。"
    
    # 2. UIデータ契約: 全SKILL辞書に has_tools, has_scripts, category が存在し、boolであること
    for s in skills:
        assert "has_tools" in s, f"【データ契約違反】SKILL '{s.get('name')}' に has_tools キーが存在しません！"
        assert isinstance(s["has_tools"], bool), f"has_tools は bool である必要があります (got {type(s['has_tools'])})"
        assert "has_scripts" in s, f"【データ契約違反】SKILL '{s.get('name')}' に has_scripts キーが存在しません！"
        assert isinstance(s["has_scripts"], bool)
        assert bool(s.get("category")), f"SKILL '{s.get('name')}' のカテゴリが空です"


def test_webui_resume_dock_and_session_isolation_contract():
    """WebUI の再開ドック(#resumeDock)とセッション分離・緊急停止トグルが実装されていることを検証"""
    tpl_path = Path("/data/data/com.termux/files/home/TUGUMIv6/interfaces/web/templates/index.html")
    tpl_src = tpl_path.read_text(encoding="utf-8")
    
    # 1. 再開ドックとセッション分離ハンドラが存在すること
    assert 'id="resumeDock"' in tpl_src, "【UI欠陥回帰】index.html に #resumeDock が存在しません！"
    assert "checkResumeDockForCurrentSession" in tpl_src, "【セッション汚染回帰】checkResumeDockForCurrentSession が存在しません！"
    assert "resumeInterruptedTask" in tpl_src
    assert "dismissInterruptedTask" in tpl_src
    
    # 2. 緊急停止トグルボタンが配備されていること
    assert "toggleEmergencyStop" in tpl_src, "【UI欠陥回帰】toggleEmergencyStop が存在しません！"


def test_mcp_descriptions_japanese_immutability():
    """全MCPツール説明文の完全日本語表記および不可侵・永続化を検証（英語への先祖返りを物理遮断）"""
    from tools.mcp_ja_enforcer import enforce_mcp_schemas_japanese, verify_source_mcp_files_japanese
    from core.capability_inspector import MCP_TOOL_JA_DESCRIPTIONS

    # 1. 登録辞書が十分な網羅性を持っていること
    assert len(MCP_TOOL_JA_DESCRIPTIONS) >= 80, (
        f"【規約違反】MCP_TOOL_JA_DESCRIPTIONS の登録件数が激減しています！ (現行: {len(MCP_TOOL_JA_DESCRIPTIONS)}件)"
    )

    # 2. 全スキーマJSONファイルの説明文が日本語であること（英語に戻っていないこと）
    total, updated, issues = enforce_mcp_schemas_japanese(check_only=True)
    assert total >= 80, f"【規約違反】検査対象スキーマ数が不足しています (現行: {total}件)"
    assert len(issues) == 0, f"【先祖返り検知】以下のMCPスキーマが英語または異なる説明文に戻っています: {issues}"

    # 3. 主要MCPサーバーのソースコードdocstringが日本語であること
    src_issues = verify_source_mcp_files_japanese()
    assert len(src_issues) == 0, f"【先祖返り検知】MCPソースコードのdocstringが改竄・巻き戻っています: {src_issues}"


def test_sdk_10_pillars_hooks_and_mcp2_stateless_tools_guard():
    """Antigravity SDK 10大進化ピラー・Hooks v2・MCP 2.0 ステートレス拡張ツール5種の常時登録を検証"""
    from tools.antigravity_tools import get_tugumi_tools
    from core.engine_manager import EngineManager

    tools = get_tugumi_tools()
    tool_names = {getattr(t, "__name__", "") for t in tools}

    # 1. MCP 2.0 (2026-07-28) Stateless / Tasks / Apps 拡張ツール5種が漏れなく登録されていること
    required_mcp2_tools = {
        "mcp2_start_task",
        "mcp2_task_status",
        "mcp2_task_cancel",
        "mcp2_render_app",
        "mcp2_protocol_info",
    }
    missing = required_mcp2_tools - tool_names
    assert not missing, f"【規約違反】MCP 2.0 拡張ツールが get_tugumi_tools() から漏れています: {missing}"
    assert len(tools) >= 58, f"【規約違反】ネイティブ登録ツール数が減少しています (現行: {len(tools)}種)"

    # 2. AntigravityEngine に Hooks v2・ホットリロード・テレメトリAPIが実装されていること
    for attr in ("get_telemetry", "reload_tools", "reload_subagents", "get_mcp_server_names", "registered_tools"):
        assert hasattr(AntigravityEngine, attr), f"【規約違反】AntigravityEngine.{attr} が欠落しています！"

    # 3. EngineManager に set_primary_engine と get_antigravity_status が実装されていること
    for attr in ("set_primary_engine", "get_antigravity_status"):
        assert hasattr(EngineManager, attr), f"【規約違反】EngineManager.{attr} が欠落しています！"






