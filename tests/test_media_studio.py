"""
TUGUMIv6 メディア制作・作曲・画像処理統合テスト (test_media_studio.py)
"""

import os
import sys
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.media_tools import MusicCompositionEngine, ImageStudioEngine, PureMidiWriter
from tools.antigravity_tools import get_tugumi_tools
from interfaces.web.web_server import app
from fastapi.testclient import TestClient


class TestMediaStudio:

    def test_01_pure_midi_writer(self, tmp_path):
        """純粋Python MIDIライターの生成検証"""
        writer = PureMidiWriter(bpm=120)
        t_idx = writer.add_track("Lead", instrument=0)
        writer.add_note(t_idx, "C4", 0.0, 1.0)
        writer.add_note(t_idx, "E4", 1.0, 1.0)
        writer.add_note(t_idx, "G4", 2.0, 1.0)
        
        mid_file = str(tmp_path / "test_notes.mid")
        writer.write_to_file(mid_file)
        
        assert os.path.exists(mid_file)
        assert os.path.getsize(mid_file) > 20
        with open(mid_file, "rb") as f:
            header = f.read(4)
            assert header == b"MThd"

    def test_02_music_composition_cyberpunk(self):
        """Cyberpunk スタイルでの自動作曲・WAV/MP3合成"""
        res = MusicCompositionEngine.compose(genre="cyberpunk", bars=2, title="test_unit_cyberpunk", use_lyria=False, with_vocal=False)
        assert res["success"] is True
        assert res["genre"] == "cyberpunk"
        assert res["bpm"] == 128
        assert os.path.exists(res["midi_path"])
        if res.get("wav_path"):
            assert os.path.exists(res["wav_path"])
            assert os.path.getsize(res["wav_path"]) > 1000

    def test_03_music_composition_all_genres(self):
        """全ジャンルプリセットの作曲動作確認"""
        genres = ["lofi", "chiptune", "japanese", "ambient"]
        for g in genres:
            res = MusicCompositionEngine.compose(genre=g, bars=1, title=f"test_unit_{g}", use_lyria=False, with_vocal=False)
            assert res["success"] is True
            assert os.path.exists(res["midi_path"])

    def test_04_image_editing_and_filters(self, tmp_path):
        """Pillow による画像編集・フィルター検証"""
        test_img = Image.new("RGB", (120, 120), color=(10, 20, 30))
        img_path = str(tmp_path / "test_orig.png")
        test_img.save(img_path)

        # 1. フィルター
        res_filt = ImageStudioEngine.edit(img_path, action="filter", params={"type": "cyberpunk"}, output_filename="test_filt.png")
        assert res_filt["success"] is True
        assert os.path.exists(res_filt["file_path"])

        # 2. リサイズ
        res_resize = ImageStudioEngine.edit(img_path, action="resize", params={"width": 64, "height": 64}, output_filename="test_resize.png")
        assert res_resize["success"] is True
        assert res_resize["dimensions"] == "64x64"

    def test_05_image_composition(self, tmp_path):
        """画像合成（左右並列）の検証"""
        img1 = Image.new("RGBA", (80, 80), color=(255, 0, 0, 255))
        img2 = Image.new("RGBA", (80, 80), color=(0, 255, 0, 255))
        p1 = str(tmp_path / "img1.png")
        p2 = str(tmp_path / "img2.png")
        img1.save(p1)
        img2.save(p2)

        res_comp = ImageStudioEngine.compose([p1, p2], mode="side_by_side", output_filename="test_comp_unit.png")
        assert res_comp["success"] is True
        assert res_comp["dimensions"] == "160x80"
        assert os.path.exists(res_comp["file_path"])

    def test_06_image_to_ascii(self, tmp_path):
        """TrueColor ASCIIアート変換検証"""
        img = Image.new("RGB", (40, 20), color=(0, 240, 255))
        p = str(tmp_path / "ascii_test.png")
        img.save(p)

        art = ImageStudioEngine.to_ascii(p, target_width=20)
        assert len(art) > 0
        assert "\033[38;2;" in art  # ANSI TrueColor code exists

    def test_07_antigravity_tools_registration(self):
        """get_tugumi_tools に新設ツールが登録されているか"""
        tools = get_tugumi_tools()
        tool_names = [getattr(t, "__name__", "") for t in tools]
        assert "generate_image" in tool_names
        assert "edit_image" in tool_names
        assert "compose_images" in tool_names
        assert "convert_image_to_ascii" in tool_names
        assert "compose_music" in tool_names

    def test_08_web_api_endpoints(self):
        """FastAPI TestClient を使った Web API 疎通テスト"""
        client = TestClient(app)
        
        # 1. 楽曲作曲API
        r_music = client.post("/api/music/compose", json={"genre": "ambient", "bars": 1, "title": "test_web_ambient", "use_lyria": False, "with_vocal": False})
        assert r_music.status_code == 200
        assert r_music.json()["success"] is True

        # 2. メディアファイル一覧API
        r_list = client.get("/api/media/files")
        assert r_list.status_code == 200
        data = r_list.json()
        assert data["success"] is True
        assert data["count"] > 0

    def test_09_gemini_music_studio_compose_full_song(self):
        """GeminiMusicStudio による作詞・Lyriaフルボイス楽曲生成パイプライン検証"""
        from tools.media_tools import GeminiMusicStudio
        res = GeminiMusicStudio.compose_full_song(
            theme="サイバーパンクの夜明け、拓磨様と共に",
            genre="cyberpunk",
            bars=1,
            title="test_unit_vocal_pipeline",
            use_lyria=True
        )
        assert res["success"] is True
        assert len(res["lyrics"]) > 0
        assert os.path.exists(res["mp3_path"])
        if res.get("wav_path"):
            assert os.path.exists(res["wav_path"])

    def test_10_gemini_image_studio_prompt_fusion(self, tmp_path):
        """GeminiImageStudio による画像プロンプト融合・一枚合成検証"""
        from tools.media_tools import GeminiImageStudio
        img1 = Image.new("RGB", (64, 64), color=(255, 0, 100))
        img2 = Image.new("RGB", (64, 64), color=(0, 100, 255))
        p1 = str(tmp_path / "f1.png")
        p2 = str(tmp_path / "f2.png")
        img1.save(p1)
        img2.save(p2)

        res = GeminiImageStudio.compose([p1, p2], prompt="2つの画像を美しく融合", output_filename="test_fuse.png")
        assert res["success"] is True
        assert os.path.exists(res["file_path"])

    def test_11_web_api_image_endpoints(self, tmp_path):
        """FastAPI TestClient を使った新設画像APIエンドポイント疎通テスト"""
        client = TestClient(app)
        img = Image.new("RGB", (64, 64), color=(100, 200, 150))
        p = str(tmp_path / "web_test.png")
        img.save(p)

        # 編集API
        r_edit = client.post("/api/image/edit", json={"image_path": p, "action": "filter", "params": {"type": "cyberpunk"}})
        assert r_edit.status_code == 200
        assert r_edit.json()["success"] is True
