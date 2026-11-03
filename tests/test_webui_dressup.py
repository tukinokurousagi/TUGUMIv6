"""
TUGUMIv6 WebUI AI美女モデル顔立ち固定・着せ替え機能 (Dressup) 結合テスト
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from interfaces.web.web_server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_dressup_references_endpoint(client):
    """リファレンス画像（専属モデル一覧・金型モデル・最新スクショ）取得エンドポイントの検証"""
    import os

    import tools.media_tools as mt

    # テスト環境の IMAGES_DIR に models ディレクトリとダミーモデルを作成
    models_dir = os.path.join(mt.IMAGES_DIR, "models")
    os.makedirs(models_dir, exist_ok=True)
    with open(os.path.join(models_dir, "model_01_pure_seiso.png"), "wb") as f:
        f.write(b"MOCK_MODEL_1")
    with open(os.path.join(models_dir, "model_02_elegance_01.png"), "wb") as f:
        f.write(b"MOCK_MODEL_2")

    resp = client.get("/api/image/dressup/references")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "exclusive_models" in data
    assert isinstance(data["exclusive_models"], list)
    assert len(data["exclusive_models"]) >= 2
    assert "latest_screenshot" in data
    assert "gold_model" in data
    assert "recent_models" in data
    assert "recent_screenshots" in data
    print("References endpoint response:", data)


def test_dressup_post_endpoint(client):
    """POST /api/image/dressup エンドポイントの検証（モック）"""
    mock_res = {
        "success": True,
        "file_path": "/storage/emulated/0/TUGUMIDesk/Images/Takuma_Dressup_Test.png",
        "filename": "Takuma_Dressup_Test.png",
        "model": "gemini-3.1-flash-image",
        "outfit": "夏用セーラー制服",
        "background": "夕暮れの教室",
        "dimensions": "1024x1024",
        "message": "👗 顔立ち固定・着せ替え画像を生成しました"
    }

    with patch("tools.media_tools.GeminiImageStudio.face_lock_dressup", return_value=mock_res):
        payload = {
            "image_paths": ["/storage/emulated/0/TUGUMIDesk/Images/ref_model_closeup.png"],
            "outfit": "夏用セーラー制服",
            "background": "夕暮れの教室",
            "mood_or_pose": "照れ笑い",
            "auto_crop_black_bars": True
        }
        resp = client.post("/api/image/dressup", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "preview_url" in data
        assert data["preview_url"] == "/api/media/file/image/Takuma_Dressup_Test.png"


def test_studio_execute_dressup_mode(client):
    """POST /api/image/studio/execute (mode='dressup') の検証（モック）"""
    mock_res = {
        "success": True,
        "file_path": "/storage/emulated/0/TUGUMIDesk/Images/Takuma_Studio_Dressup.png",
        "filename": "Takuma_Studio_Dressup.png",
        "model": "gemini-3.1-flash-image",
        "outfit": "藍色朝顔柄の白地浴衣",
        "background": "夕暮れの夏祭り",
        "dimensions": "1024x1024",
        "message": "👗 顔立ち固定・着せ替え画像を生成しました"
    }

    with patch("tools.media_tools.GeminiImageStudio.face_lock_dressup", return_value=mock_res):
        payload = {
            "mode": "dressup",
            "image_paths": ["/storage/emulated/0/TUGUMIDesk/Images/ref_model_closeup.png"],
            "outfit": "藍色朝顔柄の白地浴衣",
            "background": "夕暮れの夏祭り",
            "mood_or_pose": "微笑み",
            "auto_crop_black_bars": True
        }
        resp = client.post("/api/image/studio/execute", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["preview_url"] == "/api/media/file/image/Takuma_Studio_Dressup.png"


def test_media_file_screenshot_fallback(client):
    """Screenshots ディレクトリに存在するファイルに対する画像取得エンドポイントのフォールバック検証"""
    resp = client.get("/api/image/dressup/references")
    assert resp.status_code == 200
    data = resp.json()
    if data.get("latest_screenshot"):
        ss_name = data["latest_screenshot"]["name"]
        file_resp = client.get(f"/api/media/file/image/{ss_name}")
        assert file_resp.status_code == 200
        assert file_resp.headers["content-type"] in ("image/png", "image/jpeg")


def test_image_upload_endpoint(client, tmp_path):
    """POST /api/image/upload 画像アップロードAPIの正常系検証"""
    import io
    dummy_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    file_payload = {"file": ("test_model.png", io.BytesIO(dummy_png), "image/png")}

    resp = client.post("/api/image/upload", files=file_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "filename" in data
    assert "file_path" in data
    assert "preview_url" in data
    assert data["size_bytes"] == len(dummy_png)
    assert data["preview_url"].startswith("/api/media/file/image/")


def test_media_delete_endpoint(client):
    """POST /api/media/delete メディアギャラリー削除APIの検証"""
    import io
    dummy_data = b"MOCK_MEDIA_DATA"
    upload_resp = client.post("/api/image/upload", files={"file": ("to_delete.png", io.BytesIO(dummy_data), "image/png")})
    assert upload_resp.status_code == 200
    uploaded_name = upload_resp.json()["filename"]

    # 1. 正常削除
    del_resp = client.post("/api/media/delete", json={"filename": uploaded_name, "folder": "uploads", "file_type": "image"})
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # 2. 既に削除されたファイルの再削除（404）
    del_resp2 = client.post("/api/media/delete", json={"filename": uploaded_name, "folder": "uploads", "file_type": "image"})
    assert del_resp2.status_code == 404


def test_expand_pattern_endpoint(client):
    """POST /api/image/dressup/expand_pattern マルチパターン生成APIの検証（モック）"""
    import os

    import tools.media_tools as mt

    models_dir = os.path.join(mt.IMAGES_DIR, "models")
    os.makedirs(models_dir, exist_ok=True)
    base_file = os.path.join(models_dir, "model_02_elegance_01.png")
    with open(base_file, "wb") as f:
        f.write(b"MOCK_MODEL_2_BASE")

    mock_res = {
        "success": True,
        "file_path": "/storage/emulated/0/TUGUMIDesk/Images/model_02_elegance_02_closeup_smile.png",
        "filename": "model_02_elegance_02_closeup_smile.png",
        "model": "gemini-3.1-flash-image",
        "pattern_type": "closeup_smile",
        "model_prefix": "model_02_elegance"
    }
    with patch("tools.media_tools.GeminiImageStudio.generate_model_pattern", return_value=mock_res):
        resp = client.post(
            "/api/image/dressup/expand_pattern",
            json={
                "image_paths": [base_file],
                "pattern_type": "closeup_smile",
                "model_prefix": "model_02_elegance"
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["pattern_type"] == "closeup_smile"
        assert "preview_url" in data

