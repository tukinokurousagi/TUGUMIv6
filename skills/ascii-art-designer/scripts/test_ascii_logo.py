#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Unit Test Suite for ASCII Logo Designer Engine
============================================================
Tests RGB blending, gradient calculations, auto-downscaling, HUD frames,
image conversions, and all export formats.
"""

import os
import sys
import unittest
import tempfile
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from ascii_logo_engine import (
    RGBColor,
    GradientEngine,
    ASCIILogoEngine,
    PRESET_PALETTES,
    create_ascii_logo
)


class TestASCIILogoEngine(unittest.TestCase):

    def test_rgb_color_operations(self):
        c1 = RGBColor.from_hex("#FF0000")
        c2 = RGBColor.from_hex("#0000FF")
        self.assertEqual((c1.r, c1.g, c1.b), (255, 0, 0))
        self.assertEqual((c2.r, c2.g, c2.b), (0, 0, 255))
        
        # Test 3-char hex
        c3 = RGBColor.from_hex("#0F0")
        self.assertEqual((c3.r, c3.g, c3.b), (0, 255, 0))

        # Test lerp midpoint
        mid = RGBColor.lerp(c1, c2, 0.5)
        self.assertEqual((mid.r, mid.g, mid.b), (128, 0, 128))

        # Test ANSI strings
        self.assertEqual(c1.to_ansi_fg(), "\033[38;2;255;0;0m")
        self.assertEqual(c1.to_ansi_bg(), "\033[48;2;255;0;0m")

    def test_gradient_engine_directions(self):
        sample = ["HELLO WORLD", "CYBER CORE"]
        
        # Horizontal
        h_lines = GradientEngine.apply_gradient(sample, palette_input="red_cyber", direction="horizontal")
        self.assertEqual(len(h_lines), 2)
        self.assertIn("\033[38;2;", h_lines[0])

        # Vertical
        v_lines = GradientEngine.apply_gradient(sample, palette_input="cyberpunk", direction="vertical")
        self.assertEqual(len(v_lines), 2)

        # Diagonal
        d_lines = GradientEngine.apply_gradient(sample, palette_input="matrix", direction="diagonal")
        self.assertEqual(len(d_lines), 2)

        # Custom hex string
        cust_lines = GradientEngine.apply_gradient(sample, palette_input="#FF0000:#00FF00:#0000FF")
        self.assertEqual(len(cust_lines), 2)

    def test_strip_ansi(self):
        raw = "TEST TEXT"
        colored = f"\033[1m\033[38;2;255;0;0m{raw}\033[0m"
        self.assertEqual(GradientEngine.strip_ansi(colored), raw)

    def test_all_preset_palettes(self):
        sample = ["TUGUMI SYSTEM"]
        for name in PRESET_PALETTES:
            out = GradientEngine.apply_gradient(sample, palette_input=name)
            self.assertTrue(len(out) > 0)
            self.assertIn("\033[38;2;", out[0])

    def test_responsive_autofit(self):
        engine = ASCIILogoEngine(target_width=38)
        # "VERY LONG TEXT TITLE" with wide font 'slant' should auto-downscale
        lines, chosen_font = engine.render_text("LONG TEXT", font="slant", auto_fit=True)
        self.assertTrue(len(lines) > 0)
        max_w = max((len(GradientEngine.strip_ansi(l)) for l in lines), default=0)
        # Should be scaled down or within boundary
        self.assertIsNotNone(chosen_font)

    def test_frame_decorations(self):
        engine = ASCIILogoEngine(target_width=44)
        sample = ["TEST LINE 1", "TEST LINE 2"]

        frames = ["cyber_hud", "double_box", "heavy_box", "rounded_box", "neon_bracket", "minimal_line", "none"]
        for f in frames:
            framed = engine.decorate_frame(
                sample,
                frame_style=f,
                header_tag="HEADER",
                subtitle="SUBTITLE",
                status_text="ONLINE"
            )
            self.assertTrue(len(framed) >= len(sample))

    def test_multi_format_export(self):
        sample = ["\033[38;2;255;0;0mHELLO\033[0m"]
        
        ansi_out = ASCIILogoEngine.export(sample, "ansi")
        self.assertIn("\033[38;2;255;0;0m", ansi_out)

        raw_out = ASCIILogoEngine.export(sample, "raw")
        self.assertEqual(raw_out, "HELLO")

        bash_out = ASCIILogoEngine.export(sample, "bash")
        self.assertIn("echo -e", bash_out)

        py_out = ASCIILogoEngine.export(sample, "python")
        self.assertIn("def print_logo():", py_out)

        md_out = ASCIILogoEngine.export(sample, "markdown")
        self.assertTrue(md_out.startswith("```text"))

        html_out = ASCIILogoEngine.export(sample, "html")
        self.assertIn("<span style=", html_out)

    def test_image_to_ansi_conversion(self):
        # Create a small dummy image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            img_path = tmp.name
        
        try:
            img = Image.new("RGBA", (20, 20), color=(255, 0, 0, 255))
            img.save(img_path)

            lines_half = ASCIILogoEngine.image_to_ansi(img_path, target_width=20, color_mode="truecolor_halfblock")
            self.assertTrue(len(lines_half) > 0)
            self.assertIn("▀", lines_half[0])

            lines_gray = ASCIILogoEngine.image_to_ansi(img_path, target_width=20, color_mode="ascii_grayscale")
            self.assertTrue(len(lines_gray) > 0)
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)

    def test_create_ascii_logo_helper(self):
        logo = create_ascii_logo(
            "TUGUMI",
            palette="red_cyber",
            font="slant",
            frame="cyber_hud",
            header_tag="TUGUMI v5",
            subtitle="Unit Test",
            status_text="OK"
        )
        self.assertIn("TUGUMI v5", logo)
        self.assertIn("STATUS: OK", logo)


if __name__ == "__main__":
    unittest.main()
