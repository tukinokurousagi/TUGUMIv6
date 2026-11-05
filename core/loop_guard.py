# -*- coding: utf-8 -*-
"""
TUGUMIv6 Loop Guard
- Detects repetitive identical tool calls / loops
- Prevents infinite spinning and runaway API calls
"""

import difflib
import functools
import hashlib
import inspect
import json
import re
import threading
from typing import List, Tuple, Callable

# 引数内の「呼び出しごとに揺れる可変要素」を正規化するための正規表現群
_VOLATILE_PATTERNS: List[Tuple["re.Pattern[str]", str]] = [
    # ISO8601 / 日時 (2026-11-05T22:35:37Z, 2026-11-05 22:35:37.123+09:00, 20261105_223537)
    (re.compile(r"\d{4}-\d{2}-\d{2}[T _]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?"), "<TS>"),
    (re.compile(r"\b\d{8}[_-]?\d{6}\b"), "<TS>"),
    # 時刻のみ (22:35:37)
    (re.compile(r"\b\d{1,2}:\d{2}:\d{2}(?:\.\d+)?\b"), "<TIME>"),
    # UUID
    (re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"), "<UUID>"),
    # エポック秒/ミリ秒/PID等の10桁以上の長大数値
    (re.compile(r"\b\d{10,}\b"), "<NUM>"),
    # 8桁以上の16進ハッシュ / セッションID風トークン (sess_ab12cd34, tmp1a2b3c4d)
    (re.compile(r"\b(?:sess|tmp|task|run|job)[_-]?[0-9a-zA-Z]{6,}\b"), "<ID>"),
    (re.compile(r"\b[0-9a-f]{12,}\b"), "<HEX>"),
    # 空白の揺れ
    (re.compile(r"\s+"), " "),
]

# 曖昧一致を行う最小引数長（短い引数同士の誤爆: "1" vs "2" 等を防ぐ）
_FUZZY_MIN_LEN = 24
_FUZZY_RATIO = 0.94


def normalize_args_repr(args_repr: str) -> str:
    """タイムスタンプ・UUID・長大数値・ランダムIDなど可変要素を正規化した引数表現を返す"""
    text = str(args_repr)
    for pattern, repl in _VOLATILE_PATTERNS:
        text = pattern.sub(repl, text)
    return text.strip()


def _digest(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()[:16]

class LoopGuard:
    """Loop Detection & Flailing Prevention Guard with Thread-Safety and Decorator

    - 正規化ハッシュ判定: タイムスタンプ/UUID/長大数値等の可変要素を除去した上で同一性を判定
    - 類似度判定: 同一ツールの長い引数が ≥94% 類似なら「実質同一」とみなす
    - 周期ループ判定: 周期1〜3のアクション系列（A→A→A / A→B→A→B… / A→B→C→A→B→C…）を検知
    - reset()/mark_resumed(): ユーザーによる意図的な一時中断→追加プロンプト再開時にカウントをクリア
    """
    def __init__(self, threshold: int = 3):
        self.threshold = threshold
        self.call_history: List[str] = []
        # call_history と同期した (tool_name, 正規化引数, 正規化ハッシュ) の系列
        self._records: List[Tuple[str, str, str]] = []
        self.lock = threading.RLock()
        self._max_history = max(64, threshold * 12)

    @staticmethod
    def _same_action(a: Tuple[str, str, str], b: Tuple[str, str, str]) -> bool:
        """2つのアクションが実質同一か（正規化ハッシュ一致 or 長い引数の高類似度）"""
        if a[0] != b[0]:
            return False
        if a[2] == b[2]:
            return True
        if len(a[1]) >= _FUZZY_MIN_LEN and len(b[1]) >= _FUZZY_MIN_LEN:
            if abs(len(a[1]) - len(b[1])) > max(len(a[1]), len(b[1])) * 0.1:
                return False
            return difflib.SequenceMatcher(None, a[1], b[1], autojunk=False).ratio() >= _FUZZY_RATIO
        return False

    def record_call(self, tool_name: str, args_repr: str) -> bool:
        """呼び出しを記録し、同一(または実質同一)引数でのループ・周期ループが閾値を超えたらTrue（ループ検知）を返す"""
        with self.lock:
            norm = normalize_args_repr(args_repr)
            rec = (tool_name, norm, _digest(f"{tool_name}:{norm}"))
            self.call_history.append(f"{tool_name}:{args_repr}")
            self._records.append(rec)
            if len(self._records) > self._max_history:
                drop = len(self._records) - self._max_history
                del self._records[:drop]
                del self.call_history[:drop]

            n = len(self._records)

            # 1. 直近N回の連続一致チェック (A -> A -> A)。可変要素は正規化済み、長引数は類似度判定
            if n >= self.threshold:
                recent = self._records[-self.threshold:]
                if all(self._same_action(recent[0], r) for r in recent[1:]):
                    return True

            # 2. 周期ループチェック（周期2: A->B->A->B->A->B / 周期3: A->B->C->A->B->C->A->B->C）
            for period in (2, 3):
                window = self.threshold * period
                if n < window:
                    continue
                recent_cycle = self._records[-window:]
                lanes = [recent_cycle[i::period] for i in range(period)]
                if not all(all(self._same_action(lane[0], r) for r in lane[1:]) for lane in lanes):
                    continue
                # 全レーンが同一アクションの場合は周期ではなく（1）の領域なので除外
                heads = [lane[0] for lane in lanes]
                distinct = any(not self._same_action(heads[0], h) for h in heads[1:])
                if distinct:
                    return True

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
        """ツール関数を自動でLoopGuard保護するデコレータ（同期/非同期関数の両対応）"""
        def _build_args_repr(args, kwargs) -> str:
            try:
                return json.dumps({"args": [str(a) for a in args], "kwargs": {k: str(v) for k, v in kwargs.items()}}, sort_keys=True)
            except Exception:
                return f"args={args},kwargs={kwargs}"

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                is_loop, error_msg = self.check_call(func.__name__, _build_args_repr(args, kwargs))
                if is_loop:
                    return json.dumps({"error": error_msg, "loop_blocked": True}, ensure_ascii=False)
                return await func(*args, **kwargs)
            return async_wrapper

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            is_loop, error_msg = self.check_call(func.__name__, _build_args_repr(args, kwargs))
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
            self._records.clear()

    def mark_resumed(self) -> None:
        """ユーザーによる意図的な一時中断→追加プロンプト再開時に呼び、再開直後のリトライを無限ループと誤認しないよう履歴をクリアする"""
        self.reset()

# Global LoopGuard instance
default_loop_guard = LoopGuard(threshold=3)
