# -*- coding: utf-8 -*-
"""
TUGUMIv6 Loop Guard
- Detects repetitive identical tool calls / loops
- Prevents infinite spinning and runaway API calls
"""

import functools
import json
import threading
from typing import List, Tuple, Callable

class LoopGuard:
    """Loop Detection & Flailing Prevention Guard with Thread-Safety and Decorator"""
    def __init__(self, threshold: int = 3):
        self.threshold = threshold
        self.call_history: List[str] = []
        self.lock = threading.RLock()

    def record_call(self, tool_name: str, args_repr: str) -> bool:
        """呼び出しを記録し、同一引数でのループまたは往復ループが閾値を超えたらTrue（ループ検知）を返す"""
        with self.lock:
            signature = f"{tool_name}:{args_repr}"
            self.call_history.append(signature)

            # 1. 直近N回の連続一致チェック (A -> A -> A)
            if len(self.call_history) >= self.threshold:
                recent = self.call_history[-self.threshold:]
                if len(set(recent)) == 1:
                    return True  # 連続ループ検知

            # 2. 2サイクル往復ループチェック (A -> B -> A -> B -> A -> B)
            cycle_window = self.threshold * 2
            if len(self.call_history) >= cycle_window:
                recent_cycle = self.call_history[-cycle_window:]
                evens = set(recent_cycle[0::2])
                odds = set(recent_cycle[1::2])
                if len(evens) == 1 and len(odds) == 1 and evens != odds:
                    return True  # 往復ループ検知

            return False

    def check_call(self, tool_name: str, args_repr: str) -> Tuple[bool, str]:
        """呼び出しをチェック＆記録し、ループ検知時にはエラーメッセージを生成"""
        is_loop = self.record_call(tool_name, args_repr)
        if is_loop:
            msg = (
                f"[LoopGuard Error] Tool '{tool_name}' was called {self.threshold} times with identical or cycling arguments: {args_repr}. "
                f"Execution blocked to prevent runaway flailing loop and token waste. "
                f"Please inspect intermediate results or switch to an alternative strategy."
            )
            return True, msg
        return False, ""

    def guard(self, func: Callable) -> Callable:
        """ツール関数を自動でLoopGuard保護するデコレータ"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                args_repr = json.dumps({"args": [str(a) for a in args], "kwargs": {k: str(v) for k, v in kwargs.items()}}, sort_keys=True)
            except Exception:
                args_repr = f"args={args},kwargs={kwargs}"
            
            is_loop, error_msg = self.check_call(func.__name__, args_repr)
            if is_loop:
                return json.dumps({"error": error_msg, "loop_blocked": True}, ensure_ascii=False)
            return func(*args, **kwargs)
        return wrapper

    def get_history(self) -> List[str]:
        with self.lock:
            return list(self.call_history)

    def reset(self) -> None:
        with self.lock:
            self.call_history.clear()

# Global LoopGuard instance
default_loop_guard = LoopGuard(threshold=3)
