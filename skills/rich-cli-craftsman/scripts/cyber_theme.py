"""
Cyberpunk / Neon / Sakura Theme System for Rich CLI
Part of rich-cli-craftsman skill.
"""

from typing import Dict, Any, Optional
from rich.theme import Theme
from rich.style import Style
from rich.panel import Panel
from rich.table import Table
from rich.console import Console

# 24-bit TrueColor Palette Definitions
PALETTES = {
    "dark": { # サイバーパンク / クリムゾン・ネオン
        "primary": "#00f0ff",      # Electric Cyan
        "secondary": "#ff007f",    # Neon Magenta
        "accent": "#9d00ff",       # Electric Violet
        "success": "#00ff88",      # Cyber Mint
        "warning": "#ffb800",      # Neon Gold
        "danger": "#ff2255",       # Crimson Neon
        "bg_card": "#0f141c",      # Dark Slate
        "border": "#00f0ff",       # Cyan Border
        "dim": "#5c6370",
        "text": "#f0f6fc",
        "tag": "⚡ [bold #ff007f]DARK TUGUMI[/]"
    },
    "light": { # 通常モード / サクラ・エレガント・サイバー
        "primary": "#ff79c6",      # Sakura Pink
        "secondary": "#8be9fd",    # Soft Cyan
        "accent": "#bd93f9",       # Pastel Purple
        "success": "#50fa7b",      # Spring Green
        "warning": "#ffb86c",      # Soft Amber
        "danger": "#ff5555",       # Coral Red
        "bg_card": "#181a20",
        "border": "#ff79c6",       # Pink Border
        "dim": "#6272a4",
        "text": "#f8f8f2",
        "tag": "🌸 [bold #ff79c6]TUGUMI[/]"
    }
}

def get_rich_theme(mode: str = "light") -> Theme:
    p = PALETTES.get(mode, PALETTES["light"])
    return Theme({
        "cyber.primary": p["primary"],
        "cyber.secondary": p["secondary"],
        "cyber.accent": p["accent"],
        "cyber.success": p["success"],
        "cyber.warning": p["warning"],
        "cyber.danger": p["danger"],
        "cyber.border": p["border"],
        "cyber.dim": p["dim"],
        "cyber.text": p["text"],
    })
