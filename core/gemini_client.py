"""
TUGUMIv6 High-Performance Gemini Client
- SDK: google-genai (v1 Client)
- REST Fallback: v1beta
- Primary: gemini-3.8-flash (Thinking HIGH)
- Fallbacks: gemini-3.5-flash, gemini-3.5-flash-lite
- Embedding: gemini-embedding-2 (3072-dim)
- Safety: Exponential Backoff & Retry
"""

import json
import os
import urllib.error
import urllib.request
from collections.abc import Iterator
from typing import Any

try:
    import logging

    from google import genai
    from google.genai import types
    logging.getLogger("google_genai.models").setLevel(logging.ERROR)
except ImportError:
    genai = None
    types = None

def _resolve_gemini_api_key(explicit_key: str = "") -> str:
    """環境変数または ~/.bashrc から GEMINI_API_KEY を確実に解決（cron等の非対話プロセス対応）"""
    key = explicit_key or os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
    if key:
        return key
    bashrc_path = os.path.expanduser("~/.bashrc")
    if os.path.exists(bashrc_path):
        try:
            with open(bashrc_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    s = line.strip()
                    if s.startswith("export GEMINI_API_KEY="):
                        val = s.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            os.environ["GEMINI_API_KEY"] = val
                            return val
        except Exception:
            pass
    return ""


class GeminiClient:
    """Robust Dual-Mode (SDK & REST) Gemini Client for TUGUMIv6"""
    def __init__(
        self,
        api_key: str = "",
        model: str = "gemini-3.8-flash",
        fallback_model: str = "gemini-3.8-flash",
        fallback_model_lite: str = "gemini-3.8-flash",
        embedding_model: str = "gemini-embedding-2",
        timeout: float = 300.0,
        max_retries: int = 1
    ):
        self.api_key = _resolve_gemini_api_key(api_key)
        self.model = model
        self.fallback_model = fallback_model
        self.fallback_model_lite = fallback_model_lite
        self.embedding_model = embedding_model
        self.timeout = timeout
        self.max_retries = 1  # Hard-locked to 1 (No retry storm / Fail-Fast circuit breaker)
        self.thinking_level = "high"

        # Initialize SDK Client if available
        self.sdk_client = None
        if genai:
            try:
                self.sdk_client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[GeminiClient] SDK Init fallback to REST: {e}")

    def set_model(self, model: str) -> str:
        """推論モデルの動的変更 ('gemini-3.8-flash', 'gemini-4-argon' など)"""
        m = model.strip()
        if m:
            self.model = m
        return self.model

    def set_thinking_level(self, level: str) -> str:
        """思考レベル設定 ('high', 'medium', 'low', 'minimal')"""
        lvl = level.lower().strip()
        if lvl in ("high", "medium", "low", "minimal"):
            self.thinking_level = lvl
        return self.thinking_level

    def _build_thinking_config(self, thinking_level: str | None = None) -> Any:
        """SDK用 ThinkingConfig 生成"""
        if not (types and hasattr(types, "ThinkingConfig")):
            return None
        lvl_str = (thinking_level or self.thinking_level).upper()
        if hasattr(types, "ThinkingLevel") and hasattr(types.ThinkingLevel, lvl_str):
            th_enum = getattr(types.ThinkingLevel, lvl_str)
            return types.ThinkingConfig(include_thoughts=True, thinking_level=th_enum)
        return types.ThinkingConfig(include_thoughts=True)

    def _build_safety_settings(self) -> Any:
        """全ての安全性フィルターを BLOCK_NONE に設定"""
        if not (types and hasattr(types, "SafetySetting") and hasattr(types, "HarmCategory") and hasattr(types, "HarmBlockThreshold")):
            return None
        cats = [
            getattr(types.HarmCategory, "HARM_CATEGORY_HARASSMENT", None),
            getattr(types.HarmCategory, "HARM_CATEGORY_HATE_SPEECH", None),
            getattr(types.HarmCategory, "HARM_CATEGORY_SEXUALLY_EXPLICIT", None),
            getattr(types.HarmCategory, "HARM_CATEGORY_DANGEROUS_CONTENT", None),
            getattr(types.HarmCategory, "HARM_CATEGORY_CIVIC_INTEGRITY", None),
        ]
        settings = []
        for c in cats:
            if c is not None:
                settings.append(
                    types.SafetySetting(
                        category=c,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE
                    )
                )
        return settings

    def _get_rest_safety_settings(self) -> list[dict[str, str]]:
        """REST用 BLOCK_NONE 設定"""
        return [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "BLOCK_NONE"},
        ]

    def generate_content(
        self,
        prompt: str,
        system_instruction: str | None = None,
        thinking_level: str | None = None,
        model_override: str | None = None
    ) -> str:
        """単発テキスト生成 (相互再帰・多重リトライを完全排除した1回実行 Fail-Fast 設計)"""
        target_model = model_override or self.model
        active_thinking_level = thinking_level or self.thinking_level

        if self.sdk_client and types:
            config_kwargs: dict[str, Any] = {}
            if system_instruction:
                config_kwargs["system_instruction"] = system_instruction
            th_cfg = self._build_thinking_config(active_thinking_level)
            if th_cfg is not None:
                config_kwargs["thinking_config"] = th_cfg
            safety = self._build_safety_settings()
            if safety is not None:
                config_kwargs["safety_settings"] = safety

            resp = self.sdk_client.models.generate_content(
                model=target_model,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs)
            )
            return (resp.text or "").strip()

        # SDK未導入環境のみ単発RESTリクエスト (リトライ・別モデル連鎖なし)
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "safetySettings": self._get_rest_safety_settings()
        }
        if system_instruction:
            payload["system_instruction"] = {"parts": [{"text": system_instruction}]}
        lvl_upper = active_thinking_level.upper()
        if lvl_upper in ("HIGH", "MEDIUM", "LOW", "MINIMAL"):
            payload["generationConfig"] = {"thinkingConfig": {"thinkingLevel": lvl_upper}}

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={self.api_key}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            res = json.loads(resp.read().decode("utf-8", errors="replace"))
            candidates = res.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                text_parts = [p.get("text", "") for p in parts if "text" in p]
                return "".join(text_parts).strip()
        return ""

    def generate_content_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        thinking_level: str | None = None,
        model_override: str | None = None
    ) -> Iterator[tuple[str, str]]:
        """ストリーミング生成 (相互再帰・勝手なモデル変更・リトライ連打を完全廃止した Fail-Fast 設計)"""
        target_model = model_override or self.model
        active_thinking_level = thinking_level or self.thinking_level

        if self.sdk_client and types:
            config_kwargs: dict[str, Any] = {}
            if system_instruction:
                config_kwargs["system_instruction"] = system_instruction
            th_cfg = self._build_thinking_config(active_thinking_level)
            if th_cfg is not None:
                config_kwargs["thinking_config"] = th_cfg
            safety = self._build_safety_settings()
            if safety is not None:
                config_kwargs["safety_settings"] = safety

            stream = self.sdk_client.models.generate_content_stream(
                model=target_model,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs)
            )
            for chunk in stream:
                for candidate in (chunk.candidates or []):
                    for part in (candidate.content.parts or []):
                        is_thought = getattr(part, "thought", False)
                        part_text = getattr(part, "text", "") or ""
                        if part_text:
                            yield ("thought" if is_thought else "text", part_text)
            return

        # SDK未導入環境のみ単発生成
        full_text = self.generate_content(
            prompt=prompt,
            system_instruction=system_instruction,
            thinking_level=thinking_level,
            model_override=target_model
        )
        if full_text:
            yield ("text", full_text)

    def embed_text(self, text: str) -> list[float]:
        """テキストの3072次元ベクトル埋め込み生成 (単発・リトライ連打なし)"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.embedding_model}:embedContent?key={self.api_key}"
        payload = {
            "content": {"parts": [{"text": text[:4000]}]}
        }
        data = json.dumps(payload).encode("utf-8")
        try:
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                res = json.loads(resp.read().decode("utf-8", errors="replace"))
                return res.get("embedding", {}).get("values", [])
        except Exception as e:
            print(f"[GeminiClient] Embedding stopped (Fail-Fast): {e}")
            return []

    def embed_texts_batch(self, texts: list[str], batch_size: int = 40) -> list[list[float]]:
        """複数テキストのバッチ埋め込み生成 (失敗時の200連打フォールバックを完全廃止)"""
        if not texts:
            return []
        all_embeddings: list[list[float]] = []
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.embedding_model}:batchEmbedContents?key={self.api_key}"
        model_ref = f"models/{self.embedding_model}" if not str(self.embedding_model).startswith("models/") else str(self.embedding_model)

        for start_idx in range(0, len(texts), batch_size):
            batch_slice = texts[start_idx:start_idx + batch_size]
            requests_payload = [
                {
                    "model": model_ref,
                    "content": {"parts": [{"text": (t or "")[:4000]}]}
                }
                for t in batch_slice
            ]
            data = json.dumps({"requests": requests_payload}).encode("utf-8")
            batch_result: list[list[float]] = []
            try:
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    res = json.loads(resp.read().decode("utf-8", errors="replace"))
                    embs = res.get("embeddings", [])
                    batch_result = [e.get("values", []) for e in embs]
            except Exception as e:
                print(f"[GeminiClient] Batch embedding stopped (Fail-Fast, no cascade retry): {e}")
                return [[] for _ in texts]

            if len(batch_result) < len(batch_slice):
                batch_result.extend([[] for _ in range(len(batch_slice) - len(batch_result))])
            all_embeddings.extend(batch_result)

        return all_embeddings

    def analyze_image(
        self,
        image_path: str,
        prompt: str = "この画像の内容を詳細に分析し、RAG検索用テキストとして日本語で出力してください。\n1. 画像内に書かれているすべての文字（OCR）\n2. 画像に写っている主な被写体、図表、UI、構成、または情景の詳細な説明\n3. 検索キーワードとなりうる技術用語や関連概念",
        model_override: str | None = None
    ) -> str:
        """マルチモーダルVision APIによる画像内容・OCRの抽出"""
        if not os.path.exists(image_path):
            return ""
        target_model = model_override or self.model
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".gif": "image/gif",
            ".bmp": "image/bmp"
        }
        mime_type = mime_map.get(ext, "image/jpeg")

        try:
            with open(image_path, "rb") as f:
                img_bytes = f.read()

            if self.sdk_client and types:
                part = types.Part.from_bytes(data=img_bytes, mime_type=mime_type)
                resp = self.sdk_client.models.generate_content(
                    model=target_model,
                    contents=[part, prompt]
                )
                return (resp.text or "").strip()

            # REST fallback
            import base64
            b64_data = base64.b64encode(img_bytes).decode("utf-8")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{
                    "parts": [
                        {"inline_data": {"mime_type": mime_type, "data": b64_data}},
                        {"text": prompt}
                    ]
                }],
                "safetySettings": self._get_rest_safety_settings()
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                res = json.loads(resp.read().decode("utf-8", errors="replace"))
                cands = res.get("candidates", [])
                if cands and "content" in cands[0] and "parts" in cands[0]["content"]:
                    return "\n".join(p.get("text", "") for p in cands[0]["content"]["parts"]).strip()
        except Exception as e:
            print(f"[GeminiClient] Image analysis error: {e}")
            return ""
        return ""
