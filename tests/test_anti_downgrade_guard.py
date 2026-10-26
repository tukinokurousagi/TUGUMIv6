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

