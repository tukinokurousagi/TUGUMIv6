# -*- coding: utf-8 -*-
"""
============================================================
  TUGUMIv6 Token & Real-Time Cost Tracker Component
  - Accurate Token Tracking (Prompt, Completion, Thinking, Total)
  - Gemini 3.8 Flash Official Pricing Engine
  - Real-Time JPY (Japanese Yen) Currency Conversion
  - Rich HUD & Task Completion Cost Panel
  - Dedicated to Master Takuma
============================================================
"""

from typing import Dict, Any, Optional
from rich.console import Console
from rich.cells import cell_len
from rich.text import Text

# Gemini 3.8 Flash 公式料金体系 (USD / 100万トークン)
# Context <= 128k:
# Input: $0.075 / 1M ($0.000075 / 1k)
# Output (including Thinking): $0.30 / 1M ($0.00030 / 1k)
# Context > 128k:
# Input: $0.15 / 1M, Output: $0.60 / 1M
GEMINI_38_FLASH_INPUT_PER_1M = 0.075
GEMINI_38_FLASH_OUTPUT_PER_1M = 0.300
DEFAULT_USD_JPY_RATE = 155.0  # 1 USD = 155.0 JPY (設定可能)

# マルチモデル対応 料金テーブル (USD / 100万トークン)
MODEL_PRICING_TABLE: Dict[str, Dict[str, Any]] = {
    "gemini-3.8-flash": {
        "label": "Gemini 3.8 Flash",
        "input_per_1m": 0.075,
        "output_per_1m": 0.300,
    },
    "gemini-4-argon": {
        "label": "Gemini 4 Argon",
        "input_per_1m": 1.250,
        "output_per_1m": 5.000,
    },
    "gemini-3.0-pro": {
        "label": "Gemini 3.0 Pro",
        "input_per_1m": 1.250,
        "output_per_1m": 5.000,
    },
    "gemini-3.1-pro-preview": {
        "label": "Gemini 3.1 Pro",
        "input_per_1m": 1.250,
        "output_per_1m": 5.000,
    },
    "gemini-3.5-flash": {
        "label": "Gemini 3.5 Flash",
        "input_per_1m": 0.075,
        "output_per_1m": 0.300,
    },
    "gemini-3.5-flash-lite": {
        "label": "Gemini 3.5 Flash-Lite",
        "input_per_1m": 0.0375,
        "output_per_1m": 0.150,
    },
}


class TokenCostTracker:
    """マルチモデル対応の高精度トークン＆日本円コスト追跡クラス"""
    def __init__(
        self,
        usd_jpy_rate: float = DEFAULT_USD_JPY_RATE,
        input_rate_per_1m: float = GEMINI_38_FLASH_INPUT_PER_1M,
        output_rate_per_1m: float = GEMINI_38_FLASH_OUTPUT_PER_1M,
        model_name: str = "gemini-3.8-flash",
    ):
        self.usd_jpy_rate = usd_jpy_rate
        self.model_name = model_name or "gemini-3.8-flash"
        self.model_label = "Gemini 3.8 Flash"
        self._custom_rates = (
            input_rate_per_1m != GEMINI_38_FLASH_INPUT_PER_1M
            or output_rate_per_1m != GEMINI_38_FLASH_OUTPUT_PER_1M
        )
        self.input_rate_per_1m = input_rate_per_1m
        self.output_rate_per_1m = output_rate_per_1m
        if not self._custom_rates:
            self.set_model(self.model_name)

        # セッション累計
        self.session_prompt_tokens: int = 0
        self.session_completion_tokens: int = 0
        self.session_thinking_tokens: int = 0
        self.session_total_tokens: int = 0
        self.session_turns: int = 0
        self._accumulated_cost_usd: float = 0.0
        self._last_turn_cost_usd: float = 0.0

        # 最新ターン
        self.last_prompt_tokens: int = 0
        self.last_completion_tokens: int = 0
        self.last_thinking_tokens: int = 0
        self.last_turn_tokens: int = 0

    def set_model(self, model_name: str) -> None:
        """現在の推論モデルに合わせて料金レートと表示ラベルを動的更新"""
        if not model_name:
            return
        norm = model_name.strip().lower().replace("models/", "").replace("google/", "")
        self.model_name = norm
        info = MODEL_PRICING_TABLE.get(norm)
        if not info:
            if "argon" in norm or "gemini-4" in norm:
                info = MODEL_PRICING_TABLE["gemini-4-argon"]
            elif "pro" in norm:
                info = MODEL_PRICING_TABLE["gemini-3.0-pro"]
            elif "lite" in norm:
                info = MODEL_PRICING_TABLE["gemini-3.5-flash-lite"]
            elif "3.5" in norm:
                info = MODEL_PRICING_TABLE["gemini-3.5-flash"]
            else:
                info = MODEL_PRICING_TABLE["gemini-3.8-flash"]
        self.model_label = info["label"]
        if not self._custom_rates:
            self.input_rate_per_1m = info["input_per_1m"]
            self.output_rate_per_1m = info["output_per_1m"]

    def reset(self) -> None:
        """セッション累計および直近ターンのトークン・コストを完全にゼロクリア"""
        self.session_prompt_tokens = 0
        self.session_completion_tokens = 0
        self.session_thinking_tokens = 0
        self.session_total_tokens = 0
        self.session_turns = 0
        self._accumulated_cost_usd = 0.0
        self._last_turn_cost_usd = 0.0
        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0
        self.last_thinking_tokens = 0
        self.last_turn_tokens = 0

    @property
    def session_total(self) -> int:
        return self.session_total_tokens

    @property
    def session_cost_usd(self) -> float:
        input_cost = (self.session_prompt_tokens / 1_000_000.0) * self.input_rate_per_1m
        output_cost = (self.session_completion_tokens / 1_000_000.0) * self.output_rate_per_1m
        return input_cost + output_cost

    @property
    def session_cost_jpy(self) -> float:
        return self.session_cost_usd * self.usd_jpy_rate

    @property
    def last_cost_usd(self) -> float:
        input_cost = (self.last_prompt_tokens / 1_000_000.0) * self.input_rate_per_1m
        output_cost = (self.last_completion_tokens / 1_000_000.0) * self.output_rate_per_1m
        return input_cost + output_cost

    @property
    def last_cost_jpy(self) -> float:
        return self.last_cost_usd * self.usd_jpy_rate

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        高精度なトークン数推定
        - 英語・数字・記号: ~4文字で1トークン
        - 日本語・マルチバイト（ひらがな・カタカナ・漢字）: ~1.2文字で1トークン
        """
        if not text:
            return 0
        ascii_chars = sum(1 for c in text if ord(c) < 128)
        non_ascii_chars = len(text) - ascii_chars
        est = int(ascii_chars / 4.0 + non_ascii_chars / 1.2)
        return max(est, 1)

    def record_turn(
        self,
        prompt_text: str = "",
        response_text: str = "",
        thought_text: str = "",
        usage_metadata: Optional[Any] = None,
        model_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        ターンのトークン消費を記録し、料金を算出。
        Gemini APIの usage_metadata があれば最優先で採用、なければ高精度推計。
        """
        if model_name:
            self.set_model(model_name)
        prompt_tokens = 0
        completion_tokens = 0
        thinking_tokens = 0

        if usage_metadata:
            # usage_metadata オブジェクトまたは dict から抽出
            if hasattr(usage_metadata, "prompt_token_count") and usage_metadata.prompt_token_count:
                prompt_tokens = int(usage_metadata.prompt_token_count)
            elif isinstance(usage_metadata, dict) and "prompt_token_count" in usage_metadata:
                prompt_tokens = int(usage_metadata["prompt_token_count"])

            if hasattr(usage_metadata, "candidates_token_count") and usage_metadata.candidates_token_count:
                completion_tokens = int(usage_metadata.candidates_token_count)
            elif isinstance(usage_metadata, dict) and "candidates_token_count" in usage_metadata:
                completion_tokens = int(usage_metadata["candidates_token_count"])

            if hasattr(usage_metadata, "thoughts_token_count") and usage_metadata.thoughts_token_count:
                thinking_tokens = int(usage_metadata.thoughts_token_count)
            elif isinstance(usage_metadata, dict) and "thoughts_token_count" in usage_metadata:
                thinking_tokens = int(usage_metadata["thoughts_token_count"])

        # フォールバック推計
        if prompt_tokens == 0:
            prompt_tokens = self.estimate_tokens(prompt_text)
        if completion_tokens == 0:
            thought_t = self.estimate_tokens(thought_text)
            resp_t = self.estimate_tokens(response_text)
            thinking_tokens = thought_t
            completion_tokens = thought_t + resp_t

        turn_total = prompt_tokens + completion_tokens

        # ターン記録
        self.last_prompt_tokens = prompt_tokens
        self.last_completion_tokens = completion_tokens
        self.last_thinking_tokens = thinking_tokens
        self.last_turn_tokens = turn_total

        # セッション累計加算
        self.session_prompt_tokens += prompt_tokens
        self.session_completion_tokens += completion_tokens
        self.session_thinking_tokens += thinking_tokens
        self.session_total_tokens += turn_total
        self.session_turns += 1

        return {
            "model_name": self.model_name,
            "model_label": self.model_label,
            "turn_prompt_tokens": prompt_tokens,
            "turn_completion_tokens": completion_tokens,
            "turn_thinking_tokens": thinking_tokens,
            "turn_total_tokens": turn_total,
            "turn_cost_usd": self.last_cost_usd,
            "turn_cost_jpy": self.last_cost_jpy,
            "session_total_tokens": self.session_total_tokens,
            "session_cost_usd": self.session_cost_usd,
            "session_cost_jpy": self.session_cost_jpy,
        }

    def render_cost_banner(
        self,
        console: Console,
        mode: str = "dark",
        model_name: Optional[str] = None,
    ) -> None:
        """タスク・ターン終了時に、消費トークンと日本円料金を現代のSOTAエージェント水準で美しく1行テレメトリ表示"""
        if model_name:
            self.set_model(model_name)
        cost_jpy = self.last_cost_jpy
        sess_jpy = self.session_cost_jpy

        # 日本円のフォーマット（極小額の場合は小数点4桁、通常は3〜2桁）
        jpy_str = f"¥{cost_jpy:.4f}" if cost_jpy < 0.1 else (f"¥{cost_jpy:.3f}" if cost_jpy < 1.0 else f"¥{cost_jpy:.2f}")
        sess_jpy_str = f"¥{sess_jpy:.4f}" if sess_jpy < 0.1 else (f"¥{sess_jpy:.3f}" if sess_jpy < 1.0 else f"¥{sess_jpy:.2f}")

        term_width = getattr(console, "width", 80) or 80
        is_dark = (mode == "dark")
        accent = "#00f0ff" if is_dark else "#bd93f9"
        primary = "#ff0055" if is_dark else "#ff79c6"

        th_info = f" · th: {self.last_thinking_tokens:,}" if self.last_thinking_tokens else ""

        # フル詳細1行テレメトリ
        t = Text()
        t.append("  ✢ ", style=f"bold {accent}")
        t.append("Turn: ", style="bold cyan")
        t.append(f"{self.last_turn_tokens:,}", style="bold white")
        t.append(" tok ", style="dim")
        t.append(f"({self.last_prompt_tokens:,} in · {self.last_completion_tokens:,} out{th_info}) ", style="dim")
        t.append("· ", style="dim")
        t.append(jpy_str, style="bold magenta")
        t.append(" │ ", style=f"dim {primary}")
        t.append("Session: ", style="bold cyan")
        t.append(f"{self.session_total_tokens:,}", style="bold white")
        t.append(" tok · ", style="dim")
        t.append(sess_jpy_str, style="bold green")
        t.append(f" ({self.session_turns} turns @ {self.model_label})", style="dim")

        # 画面幅オーバー時はスマート短縮
        if cell_len(t.plain) + 4 > term_width:
            t = Text()
            t.append("  ✢ ", style=f"bold {accent}")
            t.append("Turn: ", style="bold cyan")
            t.append(f"{self.last_turn_tokens:,} tok", style="bold white")
            t.append(f" ({jpy_str})", style="bold magenta")
            t.append(" │ ", style=f"dim {primary}")
            t.append("Sess: ", style="bold cyan")
            t.append(f"{self.session_total_tokens:,} tok", style="bold white")
            t.append(f" ({sess_jpy_str})", style="bold green")
            t.append(f" [{self.session_turns}t]", style="dim")

        console.print()
        console.print(t)
        console.print()
