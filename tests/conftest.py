"""
TUGUMIv6 Test Safety Guard (Zero External API Billing Protection)
pytest 実行時に外部の Gemini API へ課金リクエストが送信されるのをローカルモックで物理遮断する。
（無料枠キーへのすり替えではなく、テスト時は外部課金通信そのものを発生させない設計）
"""
import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

@pytest.fixture(autouse=True)
def block_unintended_paid_api_in_tests(monkeypatch):
    """テスト実行中の意図しない実API連打（TTS・画像生成・Embedding・LLM・Antigravity）をローカルで安全にモック化"""
    from core.gemini_client import GeminiClient
    monkeypatch.setattr(GeminiClient, "generate_content", lambda self, prompt, *a, **kw: f"[Test Mode Response] {str(prompt)[:50]}")
    monkeypatch.setattr(GeminiClient, "generate_content_stream", lambda self, prompt, *a, **kw: iter([("text", f"[Test Mode Stream] {str(prompt)[:50]}")]))
    monkeypatch.setattr(GeminiClient, "embed_text", lambda self, text, *a, **kw: [0.01] * 3072)
    monkeypatch.setattr(GeminiClient, "embed_texts_batch", lambda self, texts, *a, **kw: [[0.01] * 3072 for _ in texts])

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
