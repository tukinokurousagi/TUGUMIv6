# -*- coding: utf-8 -*-
"""
TUGUMIv6 Context Compressor & Observation Masking
- Prompt Caching Optimization (Separation of Static Prefix & Dynamic Turns)
- Observation Masking (Truncate & Hash huge outputs > 300 lines)
- Context Token Budget Defense
"""

import hashlib
from typing import List, Dict, Any

class ContextCompressor:
    """Context Token Preservation & Masking Manager"""
    def __init__(self, max_output_lines: int = 150, max_token_estimate: int = 30000):
        self.max_output_lines = max_output_lines
        self.max_token_estimate = max_token_estimate

    def mask_observation(self, tool_output: str, tool_name: str = "") -> str:
        """巨大なツール出力・CLI結果を安全に圧縮・マスクし、トークン爆発を防ぐ"""
        if not tool_output:
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
        """対話履歴のスマート剪定（直近Nターンを維持しつつ、システムプロンプトを最優先防衛）"""
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
