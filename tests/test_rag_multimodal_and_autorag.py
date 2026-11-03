import sys
from pathlib import Path

# Add TUGUMIv6 to path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.engine_manager import EngineManager
from memory.rag_engine import HybridRAGEngine


def test_rag_image_multimodal_extraction(tmp_path):
    """画像ファイルのマルチモーダル・メタデータ抽出が安全に行われるか検証"""
    img_path = tmp_path / "sample.png"
    # Create simple dummy 1x1 png file
    import base64
    dummy_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    img_path.write_bytes(base64.b64decode(dummy_png_b64))

    rag = HybridRAGEngine()
    extracted_text, meta = rag.extract_document_content(str(img_path), str(tmp_path))

    assert "ファイル名: sample.png" in extracted_text
    assert "画像解像度: 1x1 px" in extracted_text
    assert meta["title"] == "sample.png"

def test_autorag_context_injection():
    """EngineManagerのAuto-RAGによるコンテキスト自動注入を検証"""
    em = EngineManager()
    base_inst = "あなたはつぐみです。"

    # 1. 空文字のみスキップされること
    merged_empty, rag_empty = em._inject_rag_context("   ", base_inst)
    assert merged_empty == base_inst
    assert rag_empty is None

    # 2. 検索キーワードを含む質問に対してRAG検索が実行され、確実にコンテキストが注入されること
    merged, rag_ctx = em._inject_rag_context("乃木坂46の井上和について教えて", base_inst)
    assert rag_ctx is not None
    assert "井上和" in rag_ctx


def test_rag_rrf_unique_keys_and_ranking():
    """RRFキー衝突解消により、各専門クエリで目的のドキュメントが正確に上位ヒットするか検証"""
    rag = HybridRAGEngine()
    st = rag.get_status_summary()
    assert st["total_chunks"] > 0
    assert st["total_files"] > 0

    hits_nagi = rag.search_hybrid("乃木坂46 井上和 センター", top_k=3)
    assert len(hits_nagi) > 0
    assert any("井上和" in h["title"] for h in hits_nagi)
    assert hits_nagi[0].get("content") == hits_nagi[0].get("text")


def test_rag_role_classification_and_unrestricted_retrieval():
    """原文無加工でのハイブリッド検索およびコンテキスト抽出を検証"""
    rag = HybridRAGEngine()

    task_res = rag.retrieve_for_context("UIデザインの成功例を参考にしてWebアプリの画面を作成して", top_k=3)
    assert task_res["has_hits"] is True
    assert "UI" in task_res["context_text"] or "成功例" in task_res["context_text"]


def test_antigravity_rag_tools_and_subagents():
    """Antigravity SDK 用 RAG ツール群およびサブエージェントへの配備を検証"""
    import json
    from core.subagents import get_tugumi_subagents
    from tools.antigravity_tools import get_tugumi_tools, rag_list_files, rag_search_knowledge

    list_out = rag_list_files()
    list_data = json.loads(list_out)
    assert list_data["status"] == "success"
    assert list_data["total_indexed_files"] > 0

    search_out = rag_search_knowledge("井上和", top_k=2)
    assert "井上和" in search_out

    tool_names = [getattr(t, "__name__", str(t)) for t in get_tugumi_tools()]
    assert "rag_search_knowledge" in tool_names
    assert "rag_add_knowledge" in tool_names
    assert "rag_list_files" in tool_names

    subagents = get_tugumi_subagents()
    for sa in subagents:
        if sa.name in ("researcher", "code_craftsman"):
            sa_tools = [getattr(t, "__name__", str(t)) for t in (sa.tools or [])]
            assert "rag_search_knowledge" in sa_tools
            assert "rag_list_files" in sa_tools


def test_webui_rag_endpoints_and_slash_commands():
    """Web UI の /rag スラッシュコマンド分岐・APIエンドポイント・DOMインスペクタ実装を検証"""
    from fastapi.testclient import TestClient
    from interfaces.web.web_server import app, execute_slash_command

    # 1. 管理サブコマンド (/rag status, /rag list, /rag search) は即時コマンド応答を返すこと
    cmd_status = execute_slash_command("/rag status", "normal", "test_sess")
    assert cmd_status is not None and cmd_status["is_command"] is True
    assert "ハイブリッドRAG ステータス" in cmd_status["reply"]

    cmd_list = execute_slash_command("/rag list", "normal", "test_sess")
    assert cmd_list is not None and cmd_list["is_command"] is True
    assert "ファイル一覧" in cmd_list["reply"]

    cmd_search = execute_slash_command("/rag search 井上和", "normal", "test_sess")
    assert cmd_search is not None and cmd_search["is_command"] is True
    assert "井上和" in cmd_search["reply"]

    # 2. 自然言語の質問・タスク (/rag <質問やタスク>) は None を返し、AIチャット/タスク本流へ渡すこと
    cmd_natural = execute_slash_command("/rag DARK TUGUMIの規約を踏まえてレポート構成案を作って", "normal", "test_sess")
    assert cmd_natural is None

    # 3. /api/rag/status エンドポイントと HTML テンプレートの配線検証
    client = TestClient(app)
    resp = client.get("/api/rag/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["summary"]["total_chunks"] > 0
    assert len(data["files"]) > 0

    html_path = REPO_ROOT / "interfaces" / "web" / "templates" / "index.html"
    html_text = html_path.read_text(encoding="utf-8")
    assert "rag-insp" in html_text
    assert "syncRagIndex" in html_text
    assert "listRagFiles" in html_text
    assert "askWithRagTitle" in html_text
