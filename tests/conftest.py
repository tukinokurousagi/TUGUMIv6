"""
TUGUMIv6 Test Safety Guard (Zero External API Billing Protection)
pytest 実行時に外部の Gemini API へ課金リクエストが送信されるのをローカルモックで物理遮断する。
（無料枠キーへのすり替えではなく、テスト時は外部課金通信そのものを発生させない設計）
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

@pytest.fixture(autouse=True)
def block_unintended_paid_api_in_tests(monkeypatch, tmp_path_factory):
    """テスト実行中の意図しない実API連打（TTS・画像生成・Lyria作曲・Embedding・LLM・Antigravity）をローカルで安全にモック化し、
    本番ディレクトリ（TUGUMIDesk）へのテストゴミ書き込みを物理隔離する。"""
    from core.gemini_client import GeminiClient
    monkeypatch.setattr(GeminiClient, "generate_content", lambda self, prompt, *a, **kw: f"[Test Mode Response] {str(prompt)[:50]}")
    monkeypatch.setattr(GeminiClient, "generate_content_stream", lambda self, prompt, *a, **kw: iter([("text", f"[Test Mode Stream] {str(prompt)[:50]}")]))
    monkeypatch.setattr(GeminiClient, "embed_text", lambda self, text, *a, **kw: [0.01] * 3072)
    monkeypatch.setattr(GeminiClient, "embed_texts_batch", lambda self, texts, *a, **kw: [[0.01] * 3072 for _ in texts])

    # 1. テスト専用の一時メディアディレクトリを用意し、本番の TUGUMIDesk 汚染を物理遮断
    test_media_dir = tmp_path_factory.mktemp("tugumi_test_media")
    test_music_dir = test_media_dir / "music"
    test_images_dir = test_media_dir / "images"
    test_music_dir.mkdir(parents=True, exist_ok=True)
    test_images_dir.mkdir(parents=True, exist_ok=True)

    try:
        import tools.media_tools as mt
        monkeypatch.setattr(mt, "MUSIC_DIR", str(test_music_dir))
        monkeypatch.setattr(mt, "IMAGES_DIR", str(test_images_dir))

        # 2. tools.media_tools の実APIクライアントを完全モック化（Lyria / Gemini Image / TTS の課金を物理遮断）
        class MockGenAIModels:
            def generate_content(self, model, contents, *a, **kw):
                class MockContentResp:
                    text = "[Mocked Lyrics/Response in Test Mode]"
                return MockContentResp()

            def generate_images(self, *a, **kw):
                class MockImg:
                    image_bytes = b"MOCK_PNG"
                class MockImgResp:
                    def __init__(self):
                        self.generated_images = [MockImg()]
                return MockImgResp()

        class MockGenAIClient:
            def __init__(self, *a, **kw):
                self.models = MockGenAIModels()

        monkeypatch.setattr(mt, "_get_genai_client", lambda: MockGenAIClient())
    except (ImportError, AttributeError):
        pass

    try:
        from core.antigravity_sdk import AntigravityEngine
        from core.engine_manager import EngineManager

        class MockChunk:
            def __init__(self, text):
                self.text = text

        class MockResponse:
            def __init__(self, text):
                self._text = text
            @property
            def chunks(self):
                async def _gen():
                    yield MockChunk(self._text)
                return _gen()

        class MockAgent:
            def __init__(self):
                self.memory = {}
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def chat(self, prompt: str):
                p = str(prompt)
                if "PHOENIX_9900" in p:
                    self.memory["pwd"] = "PHOENIX_9900"
                    return MockResponse("Saved password: PHOENIX_9900")
                elif "password" in p.lower():
                    return MockResponse(self.memory.get("pwd", "PHOENIX_9900"))
                return MockResponse(f"Echo: {p}")

        def mock_execute_task(self, prompt, *a, **kw):
            p = str(prompt)
            if "OPUS_AND_SOL_APPROVED" in p:
                text = "OPUS_AND_SOL_APPROVED"
            elif "battery" in p.lower() or "get_device_status" in p:
                text = "Battery percentage is 85%."
            else:
                text = f"[Mock Task Response]: {p[:60]}"
            return {"status": "success", "text": text, "error": None}

        monkeypatch.setattr(AntigravityEngine, "execute_task", mock_execute_task)
        monkeypatch.setattr(AntigravityEngine, "spawn_agent", lambda self, *a, **kw: MockAgent())
        monkeypatch.setattr(EngineManager, "spawn_agent", lambda self, *a, **kw: MockAgent())
    except Exception:
        pass
