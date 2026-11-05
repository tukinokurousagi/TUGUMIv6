# -*- coding: utf-8 -*-
"""
TUGUMIv6 Context Compressor & Observation Masking
- Prompt Caching Optimization (Separation of Static Prefix & Dynamic Turns)
- Observation Masking (Truncate & Hash huge outputs > 300 lines)
- Context Token Budget Defense
- Pinned Context: SOUL.md 由来のコアプロンプト/system ロールは圧縮・剪定・マスクの対象外（ペルソナ漂流防止）
"""

import hashlib
import os
from typing import List, Dict, Any, Optional

PINNED_MARKER = "[PINNED:SOUL]"
_SOUL_PATH_CANDIDATES = (
    os.path.join(os.path.dirname(__file__), "SOUL.md"),
    os.path.expanduser("~/.gemini/config/SOUL.md"),
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "SOUL.md"),
)

class ContextCompressor:
    """Context Token Preservation & Masking Manager"""
    def __init__(self, max_output_lines: int = 150, max_token_estimate: int = 30000, soul_path: Optional[str] = None):
        self.max_output_lines = max_output_lines
        self.max_token_estimate = max_token_estimate
        self._soul_path = soul_path
        self._soul_cache: str = ""
        self._soul_mtime: float = -1.0
        self._fingerprints: List[str] = []

    # ==================== Pinned Context (SOUL.md) ====================
    def _resolve_soul_path(self) -> Optional[str]:
        for cand in ([self._soul_path] if self._soul_path else list(_SOUL_PATH_CANDIDATES)):
            if cand and os.path.isfile(cand):
                return cand
        return None

    def get_pinned_context(self) -> str:
        """SOUL.md 全文（圧縮対象外のコアプロンプト）を返す。更新時刻でキャッシュ無効化し常に最新を保証"""
        path = self._resolve_soul_path()
        if not path:
            return self._soul_cache
        try:
            mtime = os.path.getmtime(path)
            if mtime != self._soul_mtime:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    self._soul_cache = f.read()
                self._soul_mtime = mtime
                # 本文中の意味のある行頭〜80文字を指紋として採取し、ピン止め対象の判別に使う
                lines = [ln.strip() for ln in self._soul_cache.splitlines() if len(ln.strip()) >= 20 and not ln.strip().startswith("#")]
                self._fingerprints = [ln[:80] for ln in lines[:6]]
        except OSError:
            pass
        return self._soul_cache

    def is_pinned_text(self, text: str) -> bool:
        """テキストが SOUL.md 由来のコアプロンプトか判定（圧縮・マスク禁止対象）"""
        if not text:
            return False
        if PINNED_MARKER in text:
            return True
        self.get_pinned_context()
        return any(fp and fp in text for fp in self._fingerprints)

    def is_pinned_message(self, message: Dict[str, Any]) -> bool:
        """system ロール・pinned フラグ付き・SOUL.md 由来メッセージは Pinned Context として保護する"""
        if not isinstance(message, dict):
            return False
        if message.get("pinned") or message.get("role") == "system":
            return True
        content = message.get("content")
        return isinstance(content, str) and self.is_pinned_text(content)

    def protect_system_prompt(self, system_prompt: str) -> str:
        """システムプロンプトに SOUL.md コアが欠落している場合のみ先頭に復元注入し、ペルソナ・ガードレール脱落を防ぐ"""
        soul = self.get_pinned_context()
        if not soul or self.is_pinned_text(system_prompt or ""):
            return system_prompt
        return f"{PINNED_MARKER}\n{soul}\n\n{system_prompt or ''}"

    def mask_observation(self, tool_output: str, tool_name: str = "") -> str:
        """巨大なツール出力・CLI結果を安全に圧縮・マスクし、トークン爆発を防ぐ"""
        if not tool_output:
            return tool_output
        # SOUL.md 由来のコアプロンプトは一切切り詰めない
        if self.is_pinned_text(tool_output):
            return tool_output

        lines = tool_output.splitlines()
        if len(lines) <= self.max_output_lines:
            return tool_output

        head_lines = lines[:40]
        tail_lines = lines[-40:]
        omitted_count = len(lines) - 80
        out_hash = hashlib.sha256(tool_output.encode("utf-8", errors="replace")).hexdigest()[:12]

        masked_output = (
            "\n".join(head_lines)
            + f"\n\n... [Observation Masked: {omitted_count} lines truncated by TUGUMIv6 ContextGuard (SHA256:{out_hash})] ...\n\n"
            + "\n".join(tail_lines)
        )
        return masked_output

    def estimate_tokens(self, text: str) -> int:
        """簡易トークン数推定 (1 token ≈ 3〜4 chars for Japanese/Code)"""
        return max(1, len(text) // 3)

    def prune_history(self, messages: List[Dict[str, Any]], max_turns: int = 20) -> List[Dict[str, Any]]:
        """対話履歴のスマート剪定（直近Nターンを維持）。

        Pinned Context（system ロール / pinned フラグ / SOUL.md 由来）はスライディングウィンドウから完全に分離し、
        元の位置関係を保ったまま必ず全件保持する（max_turns は非Pinnedメッセージにのみ適用）。
        """
        pinned_idx = {i for i, m in enumerate(messages) if self.is_pinned_message(m)}
        if pinned_idx:
            rest = [m for i, m in enumerate(messages) if i not in pinned_idx]
            kept = self._prune_plain(rest, max_turns)
            kept_ids = {id(m) for m in kept}
            return [m for i, m in enumerate(messages) if i in pinned_idx or id(m) in kept_ids]
        return self._prune_plain(messages, max_turns)

    @staticmethod
    def _prune_plain(messages: List[Dict[str, Any]], max_turns: int) -> List[Dict[str, Any]]:
        if len(messages) <= max_turns:
            return list(messages)
        if max_turns <= 0:
            return []
        if max_turns <= 2:
            return list(messages[-max_turns:])

        # 最初のターン（初期コンテキスト）と直近のターンを温存
        pinned = messages[:2]
        recent = messages[-(max_turns - 2):]
        return pinned + recent
