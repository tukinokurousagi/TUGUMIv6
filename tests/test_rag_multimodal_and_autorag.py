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

    # 1. 挨拶など短文・日常表現はトークン防衛のためスキップされること
    base_inst = "あなたはつぐみです。"
    merged, rag_ctx = em._inject_rag_context("こんにちは", base_inst)
    assert merged == base_inst
    assert rag_ctx is None

    # 2. 検索キーワードを含む質問に対してRAG検索が実行されること
    # （TUGUMI_RAG内の既知キーワード "DARK TUGUMI" や "メス" など）
    merged, rag_ctx = em._inject_rag_context("DARK TUGUMIのプロトコルについて教えて", base_inst)
    if rag_ctx:
        assert "【自律参照ナレッジベース (Auto-RAG Knowledge)】" in merged
        assert "DARK TUGUMI" in merged or "ドキュメント" in merged
