# Termux & Mobile CUI Best Practices for ASCII Art

Mobile terminal emulators like Termux have specific screen constraints and rendering behaviors. Following these best practices guarantees pixel-perfect, flicker-free, and uncorrupted display on Android devices.

---

## 1. Screen Width Constraints & Auto-Fitting

### Standard Screen Dimensions
*   **Android Portrait (Vertical Phone)**: Typically **40 to 48 columns** (characters wide) at standard font zoom.
*   **Android Landscape (Horizontal Phone / Tablet)**: **80 to 120+ columns**.
*   **Termux Default Baseline**: Designing for **44 columns** ensures guaranteed zero line-wrapping on virtually all mobile screens.

### Why Line-Wrapping Breaks ASCII Art
If a single ASCII art line is 46 chars wide on a 44-col screen, the 2 trailing characters wrap to the next line, disastrously displacing all subsequent lines into an illegible scramble.

### How ASCIILogoEngine Solves This
1.  **Width Detection**: Dynamically reads terminal columns via `shutil.get_terminal_size()` or user-specified `-w 44`.
2.  **Smart Cascade Fallback**: If font `slant` renders at 52 columns (exceeding 44), the engine automatically tries `smslant` (38 cols) $\to$ `small` (36 cols) $\to$ `mini` (30 cols) $\to$ `term` (24 cols).
3.  **ANSI-Safe Stripping**: Length calculations always strip ANSI color escape codes to measure true visual character width.

---

## 2. Integration into `.bashrc` & Startup Scripts

To make a custom logo greet you every time you open Termux:

### Method A: Fast One-Command Direct Generation
Add to `~/.bashrc` or `~/.termux_startup.sh`:
```bash
# Display TUGUMI Cyber Logo on startup
python3 ~/.agents/skills/ascii-art-designer/scripts/logo_cli.py "TUGUMI" -p red_cyber -f slant --subtitle "Autonomous Core" --status "READY" -w 44
```

### Method B: Pre-Compiled Zero-Latency Bash Snippet (Instant 0.001s launch)
Generate a native `echo -e` script once:
```bash
python3 ~/.agents/skills/ascii-art-designer/scripts/logo_cli.py "TUGUMI" -p red_cyber -f slant --header "TUGUMI v5.0" --subtitle "Takuma's Personal Assistant" --export bash -o ~/.tugumi_banner.sh
chmod +x ~/.tugumi_banner.sh
```
Then simply add to `~/.bashrc`:
```bash
~/.tugumi_banner.sh
```

---

## 3. Unicode Block Elements & TrueColor Support

### TrueColor ANSI 24-Bit RGB
Termux supports full 24-bit TrueColor via:
*   Foreground: `\033[38;2;<R>;<G>;<B>m`
*   Background: `\033[48;2;<R>;<G>;<B>m`
*   Reset: `\033[0m`

### Half-Block Pixel Trick (`▀` / U+2580)
In `image_to_ansi` mode:
*   Top pixel color $\to$ Foreground RGB
*   Bottom pixel color $\to$ Background RGB
*   Character `▀` (Upper Half Block) renders both pixels in a single character cell!
*   **Result**: 2x vertical resolution for images, icons, and avatars directly in Termux!

### Box Drawing Characters
*   Corners: `╭` `╮` `╯` `╰` `╔` `╗` `╚` `╝` `┏` `┓` `┗` `┛`
*   Edges: `─` `│` `═` `║` `━` `┃`
*   T-Junctions: `├` `┤` `╠` `╣` `┣` `┫`
*   Shading: `░` (25%), `▒` (50%), `▓` (75%), `█` (100%)
