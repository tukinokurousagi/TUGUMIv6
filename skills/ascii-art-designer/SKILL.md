---
name: ascii-art-designer
description: Professional ASCII art logo, banner, and HUD designer for Termux and CUI environments. Use this skill when generating, styling, rendering, or customizing high-impact ASCII logos, Cyber HUD frames, TrueColor (24-bit RGB) gradients, smartphone-responsive terminal banners, or converting images to ANSI half-block art.
license: MIT
---

# ASCII Art & Logo Designer for Termux

This skill provides comprehensive capabilities to design, render, style, and export professional ASCII art logos, banners, HUD cards, and TrueColor terminal art optimized for Termux (Android) and modern CUI environments.

## Core Capabilities

1.  **Multi-Font Rendering**: FIGlet and Art typography supporting 50+ fonts classified into Compact (Mobile), Cyber, Heavy 3D, and Minimal.
2.  **TrueColor (24-Bit RGB) Gradient Engine**: Smooth multi-stop gradient interpolation in 4 directions (horizontal, vertical, diagonal, radial/center-out) across 17+ curated palettes.
3.  **Smartphone Responsive Auto-Fitting**: Automatically detects terminal width (e.g. 44 cols on portrait mobile) and downscales fonts to prevent line-wrapping corruption.
4.  **Cyber HUD & Frame Decorator**: Wraps ASCII banners with cybernetic HUD headers, telemetry status badges, double borders, neon brackets, or minimal accents.
5.  **Image-to-ANSI TrueColor Converter**: Converts images (PNG/JPG/WEBP) into 2x-vertical-resolution ANSI half-block (`▀`) art.
6.  **Multi-Format Exporter**: Exports to Terminal ANSI, Raw Text, Bash Script (`echo -e`), Python snippet, Markdown code block, or Styled HTML.

---

## Bundled Tools & Scripts

*   [`scripts/ascii_logo_engine.py`](file:///data/data/com.termux/files/home/.agents/skills/ascii-art-designer/scripts/ascii_logo_engine.py): Core rendering, gradient math, framing, and conversion engine.
*   [`scripts/logo_cli.py`](file:///data/data/com.termux/files/home/.agents/skills/ascii-art-designer/scripts/logo_cli.py): CLI interface and interactive studio for instant generation.
*   [`scripts/test_ascii_logo.py`](file:///data/data/com.termux/files/home/.agents/skills/ascii-art-designer/scripts/test_ascii_logo.py): Comprehensive unit test suite.
*   [`references/font_catalog.md`](file:///data/data/com.termux/files/home/.agents/skills/ascii-art-designer/references/font_catalog.md): Complete FIGlet/Art font catalog and size guides.
*   [`references/color_palettes.md`](file:///data/data/com.termux/files/home/.agents/skills/ascii-art-designer/references/color_palettes.md): Palette definitions, hex values, and aesthetic themes.
*   [`references/hud_frames.md`](file:///data/data/com.termux/files/home/.agents/skills/ascii-art-designer/references/hud_frames.md): Cyber HUD frame styles and status telemetry badges.
*   [`references/termux_best_practices.md`](file:///data/data/com.termux/files/home/.agents/skills/ascii-art-designer/references/termux_best_practices.md): Mobile layout principles and `.bashrc` integration.

---

## Workflow Guide

### 1. Generating Quick Logos via CLI

To generate a logo directly in the terminal:
```bash
# Standard TUGUMI Red Cyber HUD Banner
python3 ~/.agents/skills/ascii-art-designer/scripts/logo_cli.py "TUGUMI" -p red_cyber -f slant --header "TUGUMI v5.0" --subtitle "Cybernetic Core" --status "ACTIVE"

# Tokyo Night Developer Logo
python3 ~/.agents/skills/ascii-art-designer/scripts/logo_cli.py "TAKUMA" -p tokyo_night -f slant --frame rounded_box --header "LABORATORY"

# Matrix Hacker Terminal Banner
python3 ~/.agents/skills/ascii-art-designer/scripts/logo_cli.py "SECURITY" -p matrix -f cybermedium --frame neon_bracket --status "LOCKED"

# Gold Luxury DeFi Banner
python3 ~/.agents/skills/ascii-art-designer/scripts/logo_cli.py "DEFI-YIELD" -p gold_luxury -f small --frame double_box --subtitle "Arbitrage Engine"
```

### 2. Exploring Fonts & Palettes

To view all available color palettes with live visual swatches:
```bash
python3 ~/.agents/skills/ascii-art-designer/scripts/logo_cli.py --list-palettes
```

To preview how a specific text looks across multiple fonts:
```bash
python3 ~/.agents/skills/ascii-art-designer/scripts/logo_cli.py "HELLO" --list-fonts
```

To launch the interactive step-by-step studio:
```bash
python3 ~/.agents/skills/ascii-art-designer/scripts/logo_cli.py --interactive
```

---

### 3. Programmatic Usage in Python Code

To embed ASCII logos directly into Python CLI applications or agents:

```python
import sys
sys.path.insert(0, "/data/data/com.termux/files/home/.agents/skills/ascii-art-designer/scripts")
from ascii_logo_engine import create_ascii_logo, ASCIILogoEngine, GradientEngine

# 1. One-shot generation
logo = create_ascii_logo(
    text="TUGUMI",
    palette="red_cyber",     # 'red_cyber', 'cyberpunk', 'matrix', 'tokyo_night', etc.
    font="slant",            # 'slant', 'smslant', 'small', 'mini', 'block'
    direction="horizontal",  # 'horizontal', 'vertical', 'diagonal', 'center_out'
    frame="cyber_hud",       # 'cyber_hud', 'double_box', 'heavy_box', 'rounded_box', 'none'
    header_tag="TUGUMI v5.0",
    subtitle="Autonomous Multi-Agent Core",
    status_text="ONLINE",
    width=44                 # Mobile screen width clamp
)
print(logo)

# 2. Custom multi-stop hex gradient
custom_logo = create_ascii_logo(
    text="QUANTUM",
    palette="#00FFFF:#7000FF:#FF007F",
    font="smslant",
    frame="neon_bracket"
)
print(custom_logo)
```

---

### 4. Converting Images to High-Resolution ANSI Art

To convert any image (PNG/JPG/WEBP) to 24-bit TrueColor ANSI half-block art:

```bash
# TrueColor 2x Half-Block mode (Recommended for logos & icons)
python3 ~/.agents/skills/ascii-art-designer/scripts/logo_cli.py --image path/to/icon.png -w 40

# Grayscale character ramp mode
python3 ~/.agents/skills/ascii-art-designer/scripts/logo_cli.py --image path/to/icon.png --color-mode ascii_grayscale -w 40
```

---

### 5. Exporting for Startup Scripts & Web / Markdown

```bash
# Export as a standalone zero-latency Bash script for ~/.bashrc
python3 ~/.agents/skills/ascii-art-designer/scripts/logo_cli.py "TUGUMI" -p red_cyber --export bash -o ~/.tugumi_banner.sh
chmod +x ~/.tugumi_banner.sh

# Export as Styled HTML for web reports / TUGUMIDesk
python3 ~/.agents/skills/ascii-art-designer/scripts/logo_cli.py "REPORT" -p tokyo_night --export html -o report_logo.html

# Export as clean Markdown code block
python3 ~/.agents/skills/ascii-art-designer/scripts/logo_cli.py "AUDIT" -p matrix --export markdown -o banner.md
```

---

## Design Principles for Termux

1.  **Mobile Width Budget**: Target **44 characters** as default baseline for smartphone vertical screens.
2.  **Contrast & Legibility**: Use high-contrast color stops (e.g. Bright Red $\to$ Orange $\to$ Gold) so letters pop vividly against dark terminal backgrounds (`#000000` / `#0d1117`).
3.  **Frame Harmony**: Choose `cyber_hud` for AI agent launchers, `double_box` for formal documents, and `neon_bracket` for compact utilities.
