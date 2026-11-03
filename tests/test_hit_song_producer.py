import os
import sys

sys.path.insert(0, "/data/data/com.termux/files/home/TUGUMIv6")

from tools.media_tools import HitSongProducerEngine
from fastapi.testclient import TestClient
from interfaces.web.web_server import app

client = TestClient(app)

def test_hit_song_producer_presets():
    """6大ジャンルプリセットの構造完全性テスト"""
    presets = HitSongProducerEngine.GENRE_PRESETS
    assert "emotional_rock" in presets
    assert "neo_citypop" in presets
    assert "future_bass" in presets
    assert "orchestral_ballad" in presets
    assert "lofi_bedroom" in presets
    assert "cyberpunk" in presets

    for _p_id, info in presets.items():
        assert "bpm" in info and isinstance(info["bpm"], int)
        assert "key" in info
        assert "chords" in info
        assert "style_prompt" in info
        assert "vocal_default" in info

def test_hit_song_producer_logic():
    """ユーザープロンプトからの楽曲プロデュース・モーラ調律作詞・仕様書生成テスト"""
    concept = "雨の深夜の首都高を走り抜ける切ない失恋アニソン風ロック"
    res = HitSongProducerEngine.produce_hit_song(
        concept_prompt=concept,
        genre_preset="emotional_rock",
        title="Test_Highway_Rain",
        synthesize_audio=False # 高速テストのため音声合成はスキップ
    )

    assert res["success"] is True
    assert "title" in res and res["title"] == "Test_Highway_Rain"
    assert "lyrics" in res and len(res["lyrics"]) > 20
    assert "bpm" in res and 60 <= res["bpm"] <= 220
    assert "key" in res
    assert "chord_progression" in res
    assert "sonic_prompt" in res
    assert "sheet_path" in res and os.path.exists(res["sheet_path"])

    # 仕様書の中身確認
    with open(res["sheet_path"], "r", encoding="utf-8") as f:
        content = f.read()
        assert "【オリコン1位級プロデュース仕様書】" in content
        assert "Test_Highway_Rain" in content
        assert "モーラ調律" in content

    # クリーンアップ
    try:
        os.remove(res["sheet_path"])
        desk_path = os.path.join("/storage/emulated/0/TUGUMIDesk/音楽・作曲", os.path.basename(res["sheet_path"]))
        if os.path.exists(desk_path):
            os.remove(desk_path)
    except Exception:
        pass

def test_api_music_produce_endpoint():
    """FastAPI POST /api/music/produce エンドポイントのE2Eテスト"""
    response = client.post("/api/music/produce", json={
        "prompt": "星空を見上げながら未来を誓う壮大なバラード",
        "genre_preset": "orchestral_ballad",
        "title": "Test_Starry_Sky",
        "synthesize_audio": False
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["title"] == "Test_Starry_Sky"
    assert "bpm" in data and 50 <= data["bpm"] <= 180
    assert "lyrics" in data and len(data["lyrics"]) > 20
    assert "sonic_prompt" in data

    # クリーンアップ
    if data.get("sheet_path") and os.path.exists(data["sheet_path"]):
        try:
            os.remove(data["sheet_path"])
        except Exception:
            pass
