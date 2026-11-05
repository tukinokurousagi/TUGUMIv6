# TrueColor RGB Color Palettes & Aesthetic Gradients

This reference documents the curated TrueColor (24-bit RGB) palettes optimized for OLED screens, Android Termux, and cybernetic aesthetic designs.

---

## 1. Curated Palette Presets

### A. Cyber & Red Themes (Signature TUGUMI Aesthetics)
*   **`red_cyber`**: Crimson Red (`#FF0033`) $\to$ Hot Red (`#FF3366`) $\to$ Neon Orange (`#FF6600`) $\to$ Amber (`#FFAA00`)
    *   *Mood*: High-energy cybernetic core, primary system banner.
*   **`crimson_flame`**: Dark Red (`#8B0000`) $\to$ Pure Red (`#FF0000`) $\to$ Orange Red (`#FF4500`) $\to$ Orange (`#FFA500`)
    *   *Mood*: Intense fire, combat HUD, critical status.
*   **`blood_moon`**: Midnight Crimson (`#4A0000`) $\to$ Deep Blood (`#990000`) $\to$ Pure Blood (`#E60000`) $\to$ Neon Red (`#FF4D4D`)
    *   *Mood*: Stealth, Dark TUGUMI, gothic cyber.

### B. Neon & Synthwave Themes
*   **`cyberpunk`**: Electric Cyan (`#00F0FF`) $\to$ Neon Purple (`#7000FF`) $\to$ Hot Pink (`#FF007F`) $\to$ Bright Yellow (`#FFE600`)
    *   *Mood*: Cyberpunk 2077, high contrast neon street aesthetics.
*   **`neon_synth`**: Deep Violet (`#9900FF`) $\to$ Vivid Purple (`#CC00FF`) $\to$ Neon Magenta (`#FF00AA`) $\to$ Aqua Cyan (`#00FFFF`)
    *   *Mood*: 80s Retrowave, Outrun, synthesizer.
*   **`tokyo_night`**: Indigo Blue (`#4158D0`) $\to$ Magenta Pink (`#C850C0`) $\to$ Warm Tangerine (`#FFCC70`)
    *   *Mood*: Tokyo Night city lights, sophisticated gradient.
*   **`miami_vice`**: Hot Magenta (`#F107A3`) $\to$ Purple (`#7B2CBF`) $\to$ Bright Turquoise (`#00F5D4`)
    *   *Mood*: Tropical synth, retro palm aesthetics.

### C. Matrix & Security Themes
*   **`matrix`**: Shadow Green (`#003311`) $\to$ Terminal Green (`#009933`) $\to$ Neon Emerald (`#00FF66`) $\to$ Pale Phosphor (`#99FF99`)
    *   *Mood*: Classic Matrix rain, CLI security scanner, hacker tools.
*   **`emerald_hacker`**: Forest Green (`#0B6623`) $\to$ Sea Green (`#2E8B57`) $\to$ Spring Green (`#00FF7F`) $\to$ Aquamarine (`#7FFFD4`)
    *   *Mood*: Modern clean cybersecurity, AI neural graph.
*   **`terminal_amber`**: Dark Amber (`#663300`) $\to$ Rust Orange (`#CC6600`) $\to$ Neon Amber (`#FF9900`) $\to$ Phosphor Glow (`#FFCC66`)
    *   *Mood*: Retro CRT phosphor amber monitors (VT220 style).

### D. Futuristic & Luxury Themes
*   **`ice_glacier`**: Navy Ice (`#001F3F`) $\to$ Azure (`#0074D9`) $\to$ Glacier Cyan (`#7FDBFF`) $\to$ Frost White (`#E0FFFF`)
    *   *Mood*: Clean, chilled, server health OK, arctic data lake.
*   **`electric_violet`**: Dark Void (`#240046`) $\to$ Royal Purple (`#7B2CBF`) $\to$ Neon Violet (`#9D4EDD`) $\to$ Lavender Glow (`#E0AAFF`)
    *   *Mood*: Quantum computing, neural synthesis.
*   **`gold_luxury`**: Bronze Brown (`#5E4B1F`) $\to$ Dark Goldenrod (`#B8860B`) $\to$ Metallic Gold (`#FFD700`) $\to$ Platinum Cornsilk (`#FFF8DC`)
    *   *Mood*: VIP, supreme master, DeFi yields, premium tier.
*   **`monochrome`**: Charcoal (`#444444`) $\to$ Steel Gray (`#888888`) $\to$ Light Silver (`#CCCCCC`) $\to$ Pure White (`#FFFFFF`)
    *   *Mood*: Stealth, minimalist, distraction-free.

---

## 2. Custom Palette Specification
You can supply arbitrary custom color stops using colon or comma-separated hex codes:
```bash
# Two-stop gradient: Pure Cyan to Pure Magenta
python3 logo_cli.py "MY_LOGO" -p "#00FFFF:#FF00FF"

# Four-stop custom gradient
python3 logo_cli.py "DEFI_DEX" -p "#11998E:#38EF7D:#FFD200:#F7971E"
```
