#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASCII Logo CLI Tool for Termux
==============================
Command-line interface and interactive studio for generating professional
ASCII art logos, banners, HUD frames, and image-to-ANSI converters.
"""

import sys
import os
import argparse
import shutil
from typing import Optional

# Ensure scripts dir is on python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from ascii_logo_engine import (
    ASCIILogoEngine,
    GradientEngine,
    RGBColor,
    PRESET_PALETTES,
    FONT_CATALOG,
    create_ascii_logo
)


def print_palette_showcase():
    """Prints all preset palettes with live gradient swatches."""
    print("\n\033[1;37m=== 🎨 AVAILABLE COLOR PALETTES ===\033[0m\n")
    sample_text = "████████████████████████████████"
    for name, hex_list in PRESET_PALETTES.items():
        grad = GradientEngine.apply_gradient([sample_text], palette_input=name, direction="horizontal")[0]
        hex_preview = " ".join(hex_list)
        print(f" \033[1;33m{name.ljust(18)}\033[0m {grad}  \033[90m{hex_preview}\033[0m")
    print()


def print_font_showcase(text: str = "TUGUMI", width: int = 44):
    """Prints recommended fonts organized by visual style."""
    print(f"\n\033[1;37m=== 🔤 FONT SHOWCASE FOR: '{text}' ===\033[0m\n")
    engine = ASCIILogoEngine(target_width=width)
    for category, fonts in FONT_CATALOG.items():
        print(f"\033[1;36m▶ CATEGORY: {category.upper()}\033[0m")
        print("─" * 40)
        for font_name in fonts[:5]:  # show top 5 per category
            lines, actual = engine.render_text(text, font=font_name, auto_fit=False)
            if lines:
                colored = GradientEngine.apply_gradient(lines, palette_input="red_cyber", direction="horizontal")
                print(f"\033[1;35m[{font_name}]\033[0m (w={len(GradientEngine.strip_ansi(lines[0]))})")
                for l in colored:
                    print(l)
                print()


def interactive_studio(default_text: str = "TUGUMI"):
    """Interactive CLI menu to craft ASCII logos step by step."""
    print("\033[1;31m")
    print("╭──────────────────────────────────────────╮")
    print("│   ❖ TUGUMI ASCII LOGO STUDIO (CUI) ❖    │")
    print("╰──────────────────────────────────────────╯\033[0m")

    try:
        user_text = input(f"\033[1;37m[1/6] Enter Logo Text [{default_text}]: \033[0m").strip()
        if not user_text:
            user_text = default_text

        print("\nAvailable Palettes: " + ", ".join(list(PRESET_PALETTES.keys())[:8]) + "...")
        user_palette = input("\033[1;37m[2/6] Enter Palette [red_cyber]: \033[0m").strip()
        if not user_palette:
            user_palette = "red_cyber"

        print("\nRecommended Fonts: slant, smslant, small, mini, block, standard, digital, term")
        user_font = input("\033[1;37m[3/6] Enter Font [slant]: \033[0m").strip()
        if not user_font:
            user_font = "slant"

        print("\nFrames: cyber_hud, double_box, heavy_box, rounded_box, neon_bracket, minimal_line, none")
        user_frame = input("\033[1;37m[4/6] Enter Frame Style [cyber_hud]: \033[0m").strip()
        if not user_frame:
            user_frame = "cyber_hud"

        user_header = input("\033[1;37m[5/6] Enter Header Tag [TUGUMI // RED_CYBER]: \033[0m").strip()
        if not user_header:
            user_header = "TUGUMI // RED_CYBER"

        user_subtitle = input("\033[1;37m[6/6] Enter Subtitle (Optional): \033[0m").strip()
        if not user_subtitle:
            user_subtitle = None

        print("\n\033[1;32m=== 🚀 GENERATING LIVE PREVIEW ===\033[0m\n")
        result = create_ascii_logo(
            text=user_text,
            palette=user_palette,
            font=user_font,
            frame=user_frame,
            header_tag=user_header,
            subtitle=user_subtitle,
            status_text="ONLINE"
        )
        print(result)
        print()

    except (KeyboardInterrupt, EOFError):
        print("\n\033[90mStudio exited.\033[0m")


def main():
    parser = argparse.ArgumentParser(
        description="TUGUMI High-Performance ASCII Logo & TrueColor Gradient Designer for Termux"
    )
    parser.add_argument("text", nargs="?", default="TUGUMI", help="Text to render into ASCII art")
    parser.add_argument("-p", "--palette", default="red_cyber", help="Color palette preset or colon-separated hex list (e.g. red_cyber, cyberpunk, #FF0000:#00FF00)")
    parser.add_argument("-f", "--font", default="slant", help="FIGlet/Art font name (slant, smslant, small, mini, block, digital, standard, term, etc.)")
    parser.add_argument("-d", "--direction", default="horizontal", choices=["horizontal", "vertical", "diagonal", "center_out"], help="Gradient direction")
    parser.add_argument("--frame", default="cyber_hud", choices=["cyber_hud", "double_box", "heavy_box", "rounded_box", "neon_bracket", "minimal_line", "none"], help="Border frame style")
    parser.add_argument("--header", default="TUGUMI // RED_CYBER", help="Header title tag for HUD frame")
    parser.add_argument("--subtitle", default=None, help="Subtitle text inside HUD frame")
    parser.add_argument("--status", default="ONLINE", help="Status badge text in HUD footer (e.g. ONLINE, ACTIVE, LOCKED)")
    parser.add_argument("-w", "--width", type=int, default=None, help="Target terminal width (auto-detected if omitted)")
    parser.add_argument("--no-bold", action="store_true", help="Disable bold text styling")
    parser.add_argument("--image", default=None, help="Convert image file (PNG/JPG/WEBP) to TrueColor ANSI art")
    parser.add_argument("--color-mode", default="truecolor_halfblock", choices=["truecolor_halfblock", "ascii_grayscale"], help="Image conversion mode")
    parser.add_argument("-e", "--export", default="ansi", choices=["ansi", "raw", "bash", "python", "markdown", "html"], help="Export format")
    parser.add_argument("-o", "--output", default=None, help="Save output to specified file path")
    parser.add_argument("--list-palettes", action="store_true", help="Show all available color palettes")
    parser.add_argument("--list-fonts", action="store_true", help="Show sample font renderings")
    parser.add_argument("-i", "--interactive", action="store_true", help="Launch interactive studio mode")

    args = parser.parse_args()

    # Special Showcase Modes
    if args.list_palettes:
        print_palette_showcase()
        return

    if args.list_fonts:
        print_font_showcase(text=args.text, width=args.width or 44)
        return

    if args.interactive:
        interactive_studio(default_text=args.text)
        return

    # Image Conversion Mode
    if args.image:
        engine = ASCIILogoEngine(target_width=args.width)
        lines = engine.image_to_ansi(args.image, target_width=engine.target_width, color_mode=args.color_mode)
        final_output = ASCIILogoEngine.export(lines, format_type=args.export)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(final_output)
            print(f"\033[1;32m[+] Image ASCII art saved to: {args.output}\033[0m")
        else:
            print(final_output)
        return

    # Standard Text Logo Generation
    engine = ASCIILogoEngine(target_width=args.width)
    lines, chosen_font = engine.render_text(args.text, font=args.font, auto_fit=True)
    colored_lines = GradientEngine.apply_gradient(
        lines,
        palette_input=args.palette,
        direction=args.direction,
        bold=not args.no_bold
    )
    framed_lines = engine.decorate_frame(
        colored_lines,
        frame_style=args.frame,
        header_tag=args.header,
        subtitle=args.subtitle,
        status_text=args.status,
        frame_palette=args.palette
    )

    final_output = ASCIILogoEngine.export(framed_lines, format_type=args.export)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(final_output)
        print(f"\033[1;32m[+] ASCII logo saved to: {args.output}\033[0m")
    else:
        print(final_output)


if __name__ == "__main__":
    main()
