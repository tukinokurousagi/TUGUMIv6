"""
Termux Terminal Width & Environment Guard
Part of rich-cli-craftsman skill.
"""

import os
import sys
import shutil
import unicodedata

def get_terminal_width(default: int = 80, min_width: int = 50, max_width: int = 120) -> int:
    """Termuxの画面幅を取得し、極端な狭さや広がりをクランプして返す"""
    try:
        cols = shutil.get_terminal_size(fallback=(default, 24)).columns
        return max(min_width, min(cols, max_width))
    except Exception:
        return default

def get_char_width(char: str) -> int:
    """East Asian Widthを考慮した1文字のターミナル表示幅 (1 or 2)"""
    w = unicodedata.east_asian_width(char)
    if w in ('F', 'W'):
        return 2
    return 1

def get_string_display_width(s: str) -> int:
    """全角半角・絵文字を考慮した文字列の実際の表示幅"""
    return sum(get_char_width(c) for c in s)

def is_interactive() -> bool:
    """パイプやリダイレクトではなく、対話的端末（TTY）かどうかを判定"""
    return sys.stdout.isatty() and sys.stdin.isatty()

def restore_cursor():
    """終了時にカーソルを確実に再表示する (ANSI escape)"""
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()
