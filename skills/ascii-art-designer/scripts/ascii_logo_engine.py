#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASCII Art & Logo Designer Engine for Termux
===========================================
High-performance, TrueColor (24-bit RGB) gradient rendering, FIGlet/Art font synthesis,
smartphone-responsive auto-resizing, Cyber HUD frame decoration, image-to-ANSI conversion,
and multi-format exporter (ANSI, Bash, Python, HTML, Markdown).

Designed for Termux (Android) & Modern CUI Environments.
"""

import os
import re
import sys
import shutil
import math
from typing import List, Tuple, Dict, Optional, Union

try:
    import pyfiglet
except ImportError:
    pyfiglet = None

try:
    import art
except ImportError:
    art = None

try:
    from PIL import Image
except ImportError:
    Image = None


# ==============================================================================
# 1. Color & TrueColor Gradient Engine
# ==============================================================================

class RGBColor:
    """Represents an RGB color with utility methods for hex conversion and blending."""
    def __init__(self, r: int, g: int, b: int):
        self.r = max(0, min(255, int(r)))
        self.g = max(0, min(255, int(g)))
        self.b = max(0, min(255, int(b)))

    @classmethod
    def from_hex(cls, hex_str: str) -> "RGBColor":
        hex_str = hex_str.lstrip("#").strip()
        if len(hex_str) == 3:
            hex_str = "".join([c * 2 for c in hex_str])
        if len(hex_str) != 6:
            return cls(255, 255, 255)
        try:
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            return cls(r, g, b)
        except ValueError:
            return cls(255, 255, 255)

    def to_hex(self) -> str:
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"

    def to_ansi_fg(self) -> str:
        return f"\033[38;2;{self.r};{self.g};{self.b}m"

    def to_ansi_bg(self) -> str:
        return f"\033[48;2;{self.r};{self.g};{self.b}m"

    def to_css_rgb(self) -> str:
        return f"rgb({self.r},{self.g},{self.b})"

    @staticmethod
    def lerp(c1: "RGBColor", c2: "RGBColor", t: float) -> "RGBColor":
        """Linear interpolation between two colors with clamp [0, 1]."""
        t = max(0.0, min(1.0, float(t)))
        r = int(round(c1.r + (c2.r - c1.r) * t))
        g = int(round(c1.g + (c2.g - c1.g) * t))
        b = int(round(c1.b + (c2.b - c1.b) * t))
        return RGBColor(r, g, b)


# Predefined Color Palettes for Professional Termux & Cyber Aesthetics
PRESET_PALETTES: Dict[str, List[str]] = {
    # Cyber & Red Themes (TUGUMI Signature)
    "red_cyber": ["#FF0033", "#FF3366", "#FF6600", "#FFAA00"],
    "crimson_flame": ["#8B0000", "#FF0000", "#FF4500", "#FFA500"],
    "blood_moon": ["#4A0000", "#990000", "#E60000", "#FF4D4D"],
    
    # Neon & Synthwave Themes
    "cyberpunk": ["#00F0FF", "#7000FF", "#FF007F", "#FFE600"],
    "neon_synth": ["#9900FF", "#CC00FF", "#FF00AA", "#00FFFF"],
    "tokyo_night": ["#4158D0", "#C850C0", "#FFCC70"],
    "miami_vice": ["#F107A3", "#7B2CBF", "#00F5D4"],
    
    # Matrix & Hacker Themes
    "matrix": ["#003311", "#009933", "#00FF66", "#99FF99"],
    "emerald_hacker": ["#0B6623", "#2E8B57", "#00FF7F", "#7FFFD4"],
    "terminal_amber": ["#663300", "#CC6600", "#FF9900", "#FFCC66"],
    
    # Futuristic & Tech Themes
    "ice_glacier": ["#001F3F", "#0074D9", "#7FDBFF", "#E0FFFF"],
    "deep_ocean": ["#03045E", "#0077B6", "#00B4D8", "#90E0EF"],
    "electric_violet": ["#240046", "#7B2CBF", "#9D4EDD", "#E0AAFF"],
    "gold_luxury": ["#5E4B1F", "#B8860B", "#FFD700", "#FFF8DC"],
    "pure_silver": ["#2B2B2B", "#666666", "#AAAAAA", "#FFFFFF"],
    "monochrome": ["#444444", "#888888", "#CCCCCC", "#FFFFFF"],
    "rainbow": ["#FF0000", "#FF7F00", "#FFFF00", "#00FF00", "#0000FF", "#4B0082", "#9400D3"],
}


class GradientEngine:
    """Computes smooth TrueColor gradients across text lines in multiple directions."""

    @staticmethod
    def multi_lerp(palette: List[RGBColor], t: float) -> RGBColor:
        """Interpolates across a multi-stop color palette with t in [0, 1]."""
        t = max(0.0, min(1.0, float(t)))
        if not palette:
            return RGBColor(255, 255, 255)
        if len(palette) == 1:
            return palette[0]

        segments = len(palette) - 1
        scaled_t = t * segments
        idx = int(math.floor(scaled_t))
        if idx >= segments:
            return palette[-1]
        local_t = scaled_t - idx
        return RGBColor.lerp(palette[idx], palette[idx + 1], local_t)

    @classmethod
    def apply_gradient(
        cls,
        text_lines: List[str],
        palette_input: Union[str, List[str], List[RGBColor]] = "red_cyber",
        direction: str = "horizontal",
        bold: bool = True,
    ) -> List[str]:
        """
        Applies a TrueColor gradient to a list of text lines.
        
        Directions:
        - 'horizontal': Left-to-right gradient across each line.
        - 'vertical': Top-to-bottom gradient across lines.
        - 'diagonal': Top-left to bottom-right diagonal gradient.
        - 'center_out': Radiates from center to edges.
        """
        # Resolve palette
        if isinstance(palette_input, str):
            if palette_input.lower() in PRESET_PALETTES:
                raw_colors = PRESET_PALETTES[palette_input.lower()]
            elif ":" in palette_input or "," in palette_input:
                raw_colors = re.split(r"[:,]", palette_input)
            else:
                raw_colors = PRESET_PALETTES["red_cyber"]
            palette = [RGBColor.from_hex(c) for c in raw_colors]
        elif isinstance(palette_input, list):
            palette = [
                c if isinstance(c, RGBColor) else RGBColor.from_hex(str(c))
                for c in palette_input
            ]
        else:
            palette = [RGBColor.from_hex(c) for c in PRESET_PALETTES["red_cyber"]]

        if not palette:
            palette = [RGBColor(255, 255, 255)]

        total_lines = len(text_lines)
        if total_lines == 0:
            return []

        # Find maximum line length
        max_len = max((len(cls.strip_ansi(line)) for line in text_lines), default=1)
        if max_len == 0:
            max_len = 1

        styled_lines = []
        bold_code = "\033[1m" if bold else ""
        reset_code = "\033[0m"

        for line_idx, line in enumerate(text_lines):
            raw_line = cls.strip_ansi(line)
            line_len = len(raw_line)
            if line_len == 0:
                styled_lines.append("")
                continue

            colored_chars = []
            char_pos = 0

            for ch in raw_line:
                if ch == " ":
                    colored_chars.append(" ")
                    char_pos += 1
                    continue

                # Calculate t parameter based on direction
                if direction == "vertical":
                    t = line_idx / max(1, total_lines - 1)
                elif direction == "diagonal":
                    t = (char_pos / max(1, max_len - 1) + line_idx / max(1, total_lines - 1)) / 2.0
                elif direction == "center_out":
                    center_x = max_len / 2.0
                    center_y = total_lines / 2.0
                    dx = (char_pos - center_x) / max(1.0, center_x)
                    dy = (line_idx - center_y) / max(1.0, center_y)
                    dist = math.sqrt(dx * dx + dy * dy)
                    t = min(1.0, dist / 1.414)
                else:  # 'horizontal' (default)
                    t = char_pos / max(1, max_len - 1)

                col = cls.multi_lerp(palette, t)
                colored_chars.append(f"{col.to_ansi_fg()}{bold_code}{ch}")
                char_pos += 1

            styled_lines.append("".join(colored_chars) + reset_code)

        return styled_lines

    @staticmethod
    def strip_ansi(text: str) -> str:
        """Removes all ANSI escape sequences to compute visual width."""
        ansi_regex = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_regex.sub("", text)


# ==============================================================================
# 2. Font Catalog & Responsive Fitting Engine
# ==============================================================================

# Recommended Fonts Categorized by Visual Style and Screen Footprint
FONT_CATALOG = {
    # Compact & Smartphone-Friendly (Fits in 35-48 chars width)
    "compact": [
        "mini", "smslant", "small", "term", "digital", "bubble", "lean",
        "script", "pebbles", "smscript", "smshadow", "smascii9"
    ],
    # Cyber & Modern Tech (Crisp, High-Tech, HUD Compatible)
    "cyber": [
        "slant", "cybermedium", "speed", "standard", "doom", "isometric1",
        "3d_diagonal", "starwars", "larry3d", "ogre", "colossal"
    ],
    # Heavy & Block / 3D (Bold impact for wide screens)
    "heavy": [
        "block", "banner3-D", "big", "isometric2", "alligator", "thick",
        "epic", "gothic", "graffiti", "rectangles"
    ],
    # Minimal & Clean
    "minimal": [
        "thin", "straight", "short", "caligraphy", "chunky", "coinstak"
    ]
}


class ASCIILogoEngine:
    """Core Engine to generate, resize, frame, and export ASCII logos."""

    def __init__(self, target_width: Optional[int] = None):
        if target_width is None:
            # Auto-detect terminal width or default to 44 (standard Termux phone screen)
            try:
                term_w = shutil.get_terminal_size((44, 24)).columns
                self.target_width = max(36, term_w)
            except Exception:
                self.target_width = 44
        else:
            self.target_width = target_width

    def render_text(
        self,
        text: str,
        font: str = "slant",
        auto_fit: bool = True
    ) -> Tuple[List[str], str]:
        """
        Renders text to ASCII art using pyfiglet or art.
        If auto_fit is True, automatically falls back to smaller fonts if the output
        exceeds self.target_width, ensuring zero line-wrap corruption on Termux.
        
        Returns:
            Tuple of (rendered_lines, chosen_font)
        """
        if not pyfiglet and not art:
            return ([text], "raw")

        fallback_cascade = [
            font,
            "slant",
            "smslant",
            "small",
            "mini",
            "term"
        ]
        fallback_cascade = list(dict.fromkeys(fallback_cascade))

        chosen_font = font
        rendered_lines = []

        for candidate_font in fallback_cascade:
            lines = self._try_render_figlet(text, candidate_font)
            if not lines:
                continue

            max_line_w = max((len(GradientEngine.strip_ansi(l)) for l in lines), default=0)
            if not auto_fit or max_line_w <= self.target_width or candidate_font == fallback_cascade[-1]:
                rendered_lines = lines
                chosen_font = candidate_font
                break

        while rendered_lines and not rendered_lines[0].strip():
            rendered_lines.pop(0)
        while rendered_lines and not rendered_lines[-1].strip():
            rendered_lines.pop()

        return (rendered_lines, chosen_font)

    def _try_render_figlet(self, text: str, font_name: str) -> Optional[List[str]]:
        """Tries rendering with pyfiglet, then falls back to art library."""
        if pyfiglet:
            try:
                raw_out = pyfiglet.figlet_format(text, font=font_name)
                return raw_out.splitlines()
            except Exception:
                pass
        if art:
            try:
                raw_out = art.text2art(text, font=font_name)
                return raw_out.splitlines()
            except Exception:
                pass
        return None

    # ==========================================================================
    # 3. Cyber HUD & Frame Decoration Engine
    # ==========================================================================

    def decorate_frame(
        self,
        lines: List[str],
        frame_style: str = "cyber_hud",
        header_tag: str = "TUGUMI // RED_CYBER",
        subtitle: Optional[str] = None,
        status_text: Optional[str] = "ONLINE",
        frame_palette: str = "red_cyber",
        center: bool = True,
        padding: int = 1
    ) -> List[str]:
        """
        Wraps ASCII lines in high-tech HUD or box frames.
        
        Supported frame_style:
        - 'cyber_hud': High-tech rounded HUD with telemetry tags
        - 'double_box': Double-line border
        - 'heavy_box': Bold single-line border
        - 'rounded_box': Smooth rounded border
        - 'neon_bracket': Mechanical brackets
        - 'minimal_line': Top and bottom accent lines
        - 'none': Raw lines with alignment only
        """
        if not lines:
            return []

        raw_widths = [len(GradientEngine.strip_ansi(l)) for l in lines]
        content_w = max(raw_widths, default=0)
        
        min_box_w = max(content_w + padding * 2, len(header_tag) + 8 if header_tag else 0)
        if subtitle:
            min_box_w = max(min_box_w, len(subtitle) + 4)
        if status_text:
            min_box_w = max(min_box_w, len(status_text) + 8)

        box_w = max(min_box_w, min(self.target_width - 2, content_w + padding * 2))

        padded_lines = []
        for line in lines:
            raw_w = len(GradientEngine.strip_ansi(line))
            if center:
                left_pad = (box_w - raw_w) // 2
                right_pad = box_w - raw_w - left_pad
                padded_lines.append(" " * left_pad + line + " " * right_pad)
            else:
                right_pad = max(0, box_w - raw_w - padding)
                padded_lines.append(" " * padding + line + " " * right_pad)

        if frame_style == "none":
            return padded_lines

        output = []
        if frame_style == "cyber_hud":
            if header_tag:
                tag_str = f"[ {header_tag} ]"
                dashes = max(1, box_w - len(tag_str) - 2)
                top_border = f"╭─{tag_str}" + "─" * dashes + "╮"
            else:
                top_border = "╭" + "─" * box_w + "╮"
            output.append(top_border)

            if subtitle:
                sub_pad = box_w - len(subtitle) - 2
                output.append(f"│  {subtitle}" + " " * max(0, sub_pad) + "│")
                output.append("├" + "─" * box_w + "┤")

            for pl in padded_lines:
                output.append(f"│{pl}│")

            if status_text:
                stat_str = f"❯ STATUS: {status_text} "
                dashes = max(1, box_w - len(stat_str) - 2)
                bot_border = "╰" + "─" * dashes + f"{stat_str}─╯"
            else:
                bot_border = "╰" + "─" * box_w + "╯"
            output.append(bot_border)

        elif frame_style == "double_box":
            output.append("╔" + "═" * box_w + "╗")
            if header_tag:
                tag_line = f"║  {header_tag}".ljust(box_w + 1) + "║"
                output.append(tag_line)
                output.append("╠" + "═" * box_w + "╣")
            for pl in padded_lines:
                output.append(f"║{pl}║")
            output.append("╚" + "═" * box_w + "╝")

        elif frame_style == "heavy_box":
            output.append("┏" + "━" * box_w + "┓")
            for pl in padded_lines:
                output.append(f"┃{pl}┃")
            output.append("┗" + "━" * box_w + "┛")

        elif frame_style == "rounded_box":
            output.append("╭" + "─" * box_w + "╮")
            for pl in padded_lines:
                output.append(f"│{pl}│")
            output.append("╰" + "─" * box_w + "╯")

        elif frame_style == "minimal_line":
            accent = "─" * box_w
            output.append(accent)
            for pl in padded_lines:
                output.append(pl)
            output.append(accent)

        elif frame_style == "neon_bracket":
            output.append("【 ❖ " + "─" * max(1, box_w - 8) + " ❖ 】")
            for pl in padded_lines:
                output.append(f"  {pl}  ")
            output.append("【 ❖ " + "─" * max(1, box_w - 8) + " ❖ 】")

        else:
            output = padded_lines

        return output


    # ==========================================================================
    # 4. Image-to-ANSI / Unicode TrueColor Converter
    # ==========================================================================

    @staticmethod
    def image_to_ansi(
        image_path: str,
        target_width: int = 44,
        color_mode: str = "truecolor_halfblock"
    ) -> List[str]:
        """
        Converts an image file (PNG/JPG/SVG/WEBP) into ultra-high-resolution ANSI ASCII/Unicode art.
        """
        if not Image:
            return ["Error: Pillow (PIL) is not installed."]
        if not os.path.exists(image_path):
            return [f"Error: File not found: {image_path}"]

        try:
            img = Image.open(image_path).convert("RGBA")
        except Exception as e:
            return [f"Error loading image: {e}"]

        orig_w, orig_h = img.size
        if color_mode == "truecolor_halfblock":
            calc_w = max(10, min(target_width, orig_w))
            calc_h = int(round(orig_h * (calc_w / orig_w)))
            if calc_h % 2 != 0:
                calc_h += 1
            resized = img.resize((calc_w, calc_h), Image.Resampling.LANCZOS)
            pixels = resized.load()

            output_lines = []
            for y in range(0, calc_h, 2):
                line_str = []
                for x in range(calc_w):
                    top_rgba = pixels[x, y]
                    bot_rgba = pixels[x, y + 1] if y + 1 < calc_h else (0, 0, 0, 0)

                    top_r = int(top_rgba[0] * (top_rgba[3] / 255.0))
                    top_g = int(top_rgba[1] * (top_rgba[3] / 255.0))
                    top_b = int(top_rgba[2] * (top_rgba[3] / 255.0))

                    bot_r = int(bot_rgba[0] * (bot_rgba[3] / 255.0))
                    bot_g = int(bot_rgba[1] * (bot_rgba[3] / 255.0))
                    bot_b = int(bot_rgba[2] * (bot_rgba[3] / 255.0))

                    char_code = f"\033[38;2;{top_r};{top_g};{top_b}m\033[48;2;{bot_r};{bot_g};{bot_b}m▀"
                    line_str.append(char_code)
                line_str.append("\033[0m")
                output_lines.append("".join(line_str))
            return output_lines

        else:
            ramp = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
            calc_w = max(10, min(target_width, orig_w))
            calc_h = int(round(orig_h * (calc_w / orig_w) * 0.45))
            resized = img.convert("L").resize((calc_w, calc_h), Image.Resampling.LANCZOS)
            pixels = resized.load()

            output_lines = []
            for y in range(calc_h):
                row = []
                for x in range(calc_w):
                    lum = pixels[x, y]
                    idx = int((lum / 255.0) * (len(ramp) - 1))
                    row.append(ramp[idx])
                output_lines.append("".join(row))
            return output_lines


    # ==========================================================================
    # 5. Multi-Format Exporter
    # ==========================================================================

    @classmethod
    def export(cls, lines: List[str], format_type: str = "ansi") -> str:
        """
        Exports rendered lines to various integration formats.
        """
        if format_type == "ansi":
            return "\n".join(lines)

        elif format_type == "raw":
            return "\n".join([GradientEngine.strip_ansi(l) for l in lines])

        elif format_type == "bash":
            bash_lines = ["#!/usr/bin/env bash", "# Generated by TUGUMI ASCII Logo Engine", ""]
            for l in lines:
                escaped = l.replace("\\", "\\\\").replace('"', '\\"').replace("\033", "\\e")
                bash_lines.append(f'echo -e "{escaped}"')
            return "\n".join(bash_lines)

        elif format_type == "python":
            py_lines = ["# -*- coding: utf-8 -*-", "def print_logo():", "    print(r'''"]
            for l in lines:
                py_lines.append("    " + l)
            py_lines.append("    ''')")
            return "\n".join(py_lines)

        elif format_type == "markdown":
            raw_content = "\n".join([GradientEngine.strip_ansi(l) for l in lines])
            return f"```text\n{raw_content}\n```"

        elif format_type == "html":
            html_lines = [
                '<div style="background-color: #0d1117; color: #c9d1d9; font-family: monospace; padding: 16px; border-radius: 8px; line-height: 1.2; overflow-x: auto; white-space: pre;">'
            ]
            for l in lines:
                span_line = re.sub(
                    r"\033\[38;2;(\d+);(\d+);(\d+)m",
                    r'<span style="color: rgb(\1, \2, \3);">',
                    l
                )
                span_line = span_line.replace("\033[1m", "<strong>").replace("\033[0m", "</span></strong>")
                html_lines.append(span_line)
            html_lines.append("</div>")
            return "\n".join(html_lines)

        return "\n".join(lines)


# ==============================================================================
# Helper Function for One-Shot Generation
# ==============================================================================

def create_ascii_logo(
    text: str,
    palette: str = "red_cyber",
    font: str = "slant",
    direction: str = "horizontal",
    frame: str = "cyber_hud",
    header_tag: str = "TUGUMI // RED_CYBER",
    subtitle: Optional[str] = None,
    status_text: Optional[str] = "ONLINE",
    width: Optional[int] = None,
    bold: bool = True
) -> str:
    """Convenience function to generate a fully styled, framed, responsive ASCII logo."""
    engine = ASCIILogoEngine(target_width=width)
    lines, chosen_font = engine.render_text(text, font=font, auto_fit=True)
    colored_lines = GradientEngine.apply_gradient(lines, palette_input=palette, direction=direction, bold=bold)
    framed_lines = engine.decorate_frame(
        colored_lines,
        frame_style=frame,
        header_tag=header_tag,
        subtitle=subtitle,
        status_text=status_text,
        frame_palette=palette
    )
    return "\n".join(framed_lines)


if __name__ == "__main__":
    demo = create_ascii_logo(
        "TUGUMI",
        palette="red_cyber",
        font="slant",
        frame="cyber_hud",
        header_tag="TUGUMI v5.0",
        subtitle="Cybernetic Autonomous Core",
        status_text="ACTIVE"
    )
    print(demo)
