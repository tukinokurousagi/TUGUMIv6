# -*- coding: utf-8 -*-
"""
TUGUMIv6 Cyber Theme & Visual Engine (SOTA 2026 Edition)
- Inspired by TUGUMI-CLIv5's Red Cyber & Neural Matrix Aesthetics
- Smartphone-Optimized Cyber Box (Width 44-76) with East Asian Width Protection
- Synaptic Neural Matrix Circuit Board & Real-Time Telemetry Gauges
- TrueColor (24-bit RGB) Cyberpunk (Dark) & Sakura Cyber (Light) Palettes
Dedicated to Master Takuma.
"""

import sys
import os
import re
import time
import random
import shutil
import threading
import unicodedata
from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.cells import cell_len
from rich.text import Text

# ==============================================================================
# 1. ANSI Colors & Cyberpunk Style Palette (CLIv5 Compatible & Upgraded)
# ==============================================================================
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    
    # Red & Crimson (CLIv5 Signature)
    RED = "\033[91m"
    BRIGHT_RED = "\033[31;1m"
    DARK_RED = "\033[31m"
    CRIMSON = "\033[38;2;255;0;85m"
    BG_RED = "\033[41m\033[37m\033[1m"
    
    # Neon & Cyber Highlights
    CYAN = "\033[96m"
    NEON_CYAN = "\033[38;5;51m"
    ELECTRIC_BLUE = "\033[38;2;0;240;255m"
    NEON_GREEN = "\033[38;5;46m"
    MINT_GREEN = "\033[38;2;0;255;136m"
    MAGENTA = "\033[95m"
    NEON_MAGENTA = "\033[38;2;255;0;127m"
    SAKURA_PINK = "\033[38;2;255;121;198m"
    VIOLET = "\033[38;2;189;147;249m"
    YELLOW = "\033[93m"
    NEON_GOLD = "\033[38;2;255;184;0m"
    AMBER = "\033[38;5;214m"
    
    # Monochrome & Grays
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    DARK_GRAY = "\033[38;5;240m"
    THOUGHT_GRAY = "\033[38;5;244m"
    BORDER_DIM = "\033[38;5;238m"


# ==============================================================================
# 2. Rich TrueColor テーマ設定
# ==============================================================================
CYBER_PALETTES = {
    "dark": {  # ダークつぐみ: クリムゾン・ブラック・アイス (Hacker Option C / TUGUMI Signature)
        "primary": "#ff0055",      # Blood Crimson Red
        "secondary": "#00f0ff",    # Electric Cyan High-Voltage
        "accent": "#ff0033",       # Neon Crimson Pulse
        "success": "#00ff88",      # Cyber Mint Verified
        "warning": "#ffb800",      # Cyber Amber Warning
        "danger": "#ff0033",       # Breach Alert
        "border": "#ff0055",       # クリムゾン外枠
        "bg_card": "#08090d",      # Stealth Black
        "dim": "#5c6370",          # Shadow Matrix Gray
        "text": "#f0f6fc",         # Crisp Hacker Terminal White
        "logo_palette": "red_cyber", # TrueColor Crimson Cyber Flame
        "header_tag": "BLACK_ICE // CRIMSON_CYBER v6 ☠",
        "subtitle": "TACTICAL OFFENSIVE DECK // MASTER TAKUMA EXCLUSIVE",
        "status_badge": "ROOT_ACCESS",
        "mode_badge": "[bold #ff0055]☠ BLACK_ICE // DARK TUGUMI (CRIMSON CYBER)[/]"
    },
    "light": {  # 通常モード: サクラ・サイバー・ハイブリッド
        "primary": "#ff79c6",      # Sakura Pink
        "secondary": "#8be9fd",    # Soft Cyan
        "accent": "#bd93f9",       # Pastel Violet
        "success": "#50fa7b",      # Spring Green
        "warning": "#ffb86c",      # Soft Amber
        "danger": "#ff5555",       # Coral Red
        "border": "#ff79c6",       # サクラ枠線
        "bg_card": "#12141c",
        "dim": "#6272a4",
        "text": "#f8f8f2",
        "logo_palette": "neon_synth",
        "header_tag": "TUGUMI v6 // SAKURA_NEURAL 🌸",
        "subtitle": "AUTONOMOUS OMNI-AGENT // DEDICATED TO MASTER TAKUMA",
        "status_badge": "ONLINE",
        "mode_badge": "[bold #ff79c6]🌸 つぐみ (通常モード)[/]"
    }
}


# ==============================================================================
# 3. 表示幅計算 & サイバーボックス (スマホ縦画面 44-76 適合)
# ==============================================================================
def get_display_width(s: str) -> int:
    """全角日本語・半角英数・絵文字・ANSIエスケープシーケンスを考慮した正確な表示幅を算出"""
    clean_s = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', s)
    w = 0
    for ch in clean_s:
        cp = ord(ch)
        status = unicodedata.east_asian_width(ch)
        if status in ('W', 'F') or (0x1F300 <= cp <= 0x1FAFF) or (0x2600 <= cp <= 0x27BF):
            w += 2
        else:
            w += 1
    return w

def get_terminal_width(default: int = 76, min_width: int = 44, max_width: int = 90) -> int:
    """Termuxの画面幅を取得し、スマホ最適幅にクランプ"""
    try:
        cols = shutil.get_terminal_size(fallback=(default, 24)).columns
        return max(min_width, min(cols, max_width))
    except Exception:
        return default

def cyber_box(lines: list, title: str = "", width: int = 44, border_color: str = Colors.RED):
    """
    スマホ画面（幅44〜76文字）にジャストフィットするRed Cyber HUDボックス
    CLIv5直系の美学：┌─[ TITLE ]──┐ と ├──────┤ と └──────┘
    """
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    title_plain = ansi_escape.sub('', title)
    title_w = get_display_width(title_plain)
    dash_cnt = max(0, width - 4 - title_w)
    
    header = f"{border_color}┌─[ {Colors.BOLD}{title}{Colors.RESET}{border_color} ]" + "─" * max(0, dash_cnt - 2) + f"┐{Colors.RESET}"
    print(header)
    for line in lines:
        if line == "---":
            print(f"{border_color}├" + "─" * (width - 2) + f"┤{Colors.RESET}")
            continue
        plain = ansi_escape.sub('', line)
        lw = get_display_width(plain)
        pad = max(0, width - 4 - lw)
        print(f"{border_color}│{Colors.RESET} {line}" + " " * pad + f" {border_color}│{Colors.RESET}")
    print(f"{border_color}└" + "─" * (width - 2) + f"┘{Colors.RESET}")

def make_gauge_bar(val: int, length: int = 6, color: str = Colors.BRIGHT_RED) -> str:
    """サイバーHUDゲージバー (例: [████░░]) を生成"""
    filled = max(0, min(length, int(round(length * val / 100.0))))
    return f"{color}" + "█" * filled + f"{Colors.DARK_GRAY}" + "░" * (length - filled) + f"{Colors.RESET}"


# ==============================================================================
# 4. リアルタイム・アニメーションスピナー (LiveSpinner)
# ==============================================================================
class LiveSpinner:
    """ターミナル上で思考・処理中に流麗に回転するサイバースピナー"""
    def __init__(self, message: str = "", style_color: str = Colors.NEON_CYAN):
        self.message = message
        self.color = style_color
        self.running = False
        self.thread = None
        self.start_time = 0.0

    def start(self, message: str = None):
        if message:
            self.message = message
        self.running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def update(self, message: str):
        self.message = message

    def _spin(self):
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        idx = 0
        while self.running:
            elapsed = time.time() - self.start_time
            sys.stdout.write(f"\r\033[K{self.color}{frames[idx % len(frames)]}{Colors.RESET} {self.message} {Colors.GRAY}({elapsed:.1f}s){Colors.RESET}")
            sys.stdout.flush()
            idx += 1
            time.sleep(0.08)

    def stop(self, clear_line: bool = True):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.2)
        if clear_line:
            sys.stdout.write("\r\033[K")
            sys.stdout.flush()


# ==============================================================================
# 5. CYBERNETIC NEURAL MATRIX (CLIv5 象徴的回路基板 ASCII アート)
# ==============================================================================
def format_hud_model_name(model_name: str) -> str:
    """HUD表示用にモデル名を正規化・整形"""
    m = (model_name or "gemini-3.8-flash").lower()
    if "argon" in m or "gemini-4" in m:
        return "Gemini 4 Argon"
    elif "3.8" in m or ("flash" in m and "lite" not in m and "3.5" not in m):
        return "Gemini 3.8 Flash"
    elif "pro" in m:
        return "Gemini 3.0 Pro"
    elif "lite" in m or "3.5" in m:
        return "Gemini 3.5 Flash-Lite"
    else:
        return model_name


def print_ascii_neural_matrix(animate: bool = True, mode: str = "light", model_name: str = "gemini-3.8-flash"):
    """
    スマホ縦画面（幅44〜48文字枠）に完全適合した Ultra-Cool Cybernetic Neural Matrix & HUD
    CLIv5直系の回路基板アスキーアート × 2026年TUGUMIv6最新スペック
    """
    p_color = Colors.CRIMSON if mode == "dark" else Colors.SAKURA_PINK
    s_color = Colors.NEON_CYAN if mode == "dark" else Colors.CYAN
    border_color = Colors.RED if mode == "dark" else Colors.SAKURA_PINK

    if animate:
        print(f"\n{s_color}🧠 [SYNAPTIC_CORTEX] TUGUMIv6 Neural Matrix Synchronizing...{Colors.RESET}")
        steps = [
            ("LEFT_CORTEX", "左脳: 論理推論・自律コード合成・5層ゲート [ACTIVE]"),
            ("RIGHT_CORTEX", "右脳: 多層認知記憶・直感・共感トポロジー [100%]"),
            ("SYNAPSE_BUS", "シナプスバス: 100Tbps 超伝導光ファイバー直結"),
            ("NEOCORTEX", "大脳新皮質: 128マルチヘッド・アテンション全開")
        ]
        pulse_chars = ["⚡", "✦", "●", "◆", "★"]
        for phase, desc in steps:
            p = random.choice(pulse_chars)
            sys.stdout.write(f"\r\033[K{p_color}[{p} {phase}]{Colors.RESET} ➔ {Colors.WHITE}{desc}{Colors.RESET}")
            sys.stdout.flush()
            time.sleep(0.18)
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()

    # ── Cyberpunk Neural Circuit Board Design (Width: 44) ──
    hud_model = format_hud_model_name(model_name)
    arch_str = f"{Colors.WHITE}{hud_model} (TTC_HIGH){Colors.RESET}" if mode == "dark" else f"{Colors.WHITE}{hud_model} (High){Colors.RESET}"
    eng_str = f"{Colors.CRIMSON}Antigravity Black-Ice Core{Colors.RESET}" if mode == "dark" else f"{Colors.ELECTRIC_BLUE}Antigravity SDK Native{Colors.RESET}"
    mem_str = f"{Colors.NEON_CYAN}4-Tier FTS5 + WAL [SECURE]{Colors.RESET}" if mode == "dark" else f"{Colors.MINT_GREEN}Multi-Tier FTS5 + WAL{Colors.RESET}"
    doc_str = f"{Colors.AMBER}TermuxDoctor Armor Shield{Colors.RESET}" if mode == "dark" else f"{Colors.AMBER}TermuxDoctor Auto-Heal{Colors.RESET}"
    core_str = f"{p_color}{Colors.BOLD}拓磨様専属 (BLACK_ICE つぐみ){Colors.RESET}" if mode == "dark" else f"{p_color}{Colors.BOLD}拓磨様専属 (つぐみ){Colors.RESET}"

    logo_lines = [
        f"  {s_color}╔══╗{Colors.RESET} {Colors.WHITE}{Colors.BOLD}N E U R A L{Colors.RESET}  {s_color}╔══╗{Colors.RESET} ",
        f"  {s_color}╚╗╔╝{Colors.RESET}{Colors.GRAY}━━━━━━━━━━━━━━{Colors.RESET}{s_color}╚╗╔╝{Colors.RESET} ",
        f"   {s_color}╠╣{Colors.RESET} {p_color}M A T R I X{Colors.RESET} {Colors.WHITE}{Colors.BOLD}v6{Colors.RESET} {s_color}╠╣{Colors.RESET}  ",
        "---",
        f" {Colors.GRAY}┌{'─' * 8}┐{Colors.RESET}      {Colors.GRAY}┌{'─' * 8}┐{Colors.RESET}",
        f" {Colors.GRAY}│{s_color} ◆ IN_0 {Colors.RESET}{Colors.GRAY}├──┐   │{Colors.YELLOW} ◇ HD_0 {Colors.RESET}{Colors.GRAY}│{Colors.RESET}",
        f" {Colors.GRAY}│{s_color} ◆ IN_1 {Colors.RESET}{Colors.GRAY}├─┐├───┤{Colors.YELLOW} ◇ HD_1 {Colors.RESET}{Colors.GRAY}│{Colors.RESET}",
        f" {Colors.GRAY}│{s_color} ◆ IN_2 {Colors.RESET}{Colors.GRAY}├┐│├───┤{Colors.YELLOW} ◇ HD_2 {Colors.RESET}{Colors.GRAY}│{Colors.RESET}",
        f" {Colors.GRAY}└{'─' * 8}┘│││   └{'─' * 3}┬{'─' * 4}┘{Colors.RESET}",
        f"  {p_color}⚡{Colors.GRAY}───────┘││       │{Colors.RESET}  {Colors.GRAY}┌{'─' * 5}┐{Colors.RESET}",
        f"  {p_color}⚡{Colors.GRAY}────────┘│   ┌───┤{Colors.NEON_GREEN} OUT {Colors.RESET}{Colors.GRAY}│{Colors.RESET}",
        f"  {p_color}⚡{Colors.GRAY}─────────┘   │   └{'─' * 5}┘{Colors.RESET}",
        f" {Colors.GRAY}┌{'─' * 8}┐{Colors.RESET}    {Colors.GRAY}│{Colors.RESET}            ",
        f" {Colors.GRAY}│{p_color} ■ BIAS  {Colors.RESET}{Colors.GRAY}├────┘{Colors.RESET}  {Colors.YELLOW}△ LOSS{Colors.RESET}   ",
        f" {Colors.GRAY}└{'─' * 8}┘{Colors.RESET}      {Colors.YELLOW}▽ 0.0001{Colors.RESET} ",
        "---",
        f"{s_color}❖ ARCH{Colors.RESET}    {arch_str}",
        f"{s_color}❖ ENGINE{Colors.RESET}  {eng_str}",
        f"{s_color}❖ MEMORY{Colors.RESET}  {mem_str}",
        f"{s_color}❖ SHIELD{Colors.RESET}  {doc_str}",
        f"{s_color}❖ CORE{Colors.RESET}    {core_str}"
    ]

    print()
    matrix_title = f"{Colors.WHITE}BLACK_ICE NEURAL MATRIX v6{Colors.RESET}" if mode == "dark" else f"{Colors.WHITE}CYBERNETIC NEURAL MATRIX v6{Colors.RESET}"
    cyber_box(logo_lines, matrix_title, width=44, border_color=border_color)
    print()


# ==============================================================================
# 6. リッチコンソール & 起動サイバーバナー
# ==============================================================================
# ascii_logo_engine の探索 & ロード
ASCII_LOGO_PATH = os.path.expanduser("~/.agents/skills/ascii-art-designer/scripts")
if ASCII_LOGO_PATH not in sys.path:
    sys.path.insert(0, ASCII_LOGO_PATH)

try:
    from ascii_logo_engine import create_ascii_logo
except ImportError:
    create_ascii_logo = None

def get_rich_console(mode: str = "light") -> Console:
    """モードに応じたTrueColor Rich Consoleを生成"""
    p = CYBER_PALETTES.get(mode, CYBER_PALETTES["light"])
    custom_theme = Theme({
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
    return Console(theme=custom_theme, color_system="truecolor", width=get_terminal_width())

def print_cyber_banner(console: Console, mode: str = "light", show_matrix: bool = False, model_name: str = "gemini-3.8-flash"):
    """
    現代の最高峰AIエージェントに相応しい洗練された統合Hero Headerを描画
    - スラントASCIIロゴとシステムテレメトリを二重囲みせず1つの端正なサイバーカードに統合
    - スマホ縦画面（44カラム〜）からPC広幅（76〜90カラム）まで East Asian Width 防衛で完全追従
    """
    palette_cfg = CYBER_PALETTES.get(mode, CYBER_PALETTES["light"])
    term_width = min(get_terminal_width(), 76)
    is_dark = (mode == "dark")
    border_col = palette_cfg["border"]
    primary = palette_cfg["primary"]
    secondary = palette_cfg["secondary"]
    status_text = palette_cfg.get("status_badge", "ONLINE")
    header_tag = palette_cfg.get("header_tag", "TUGUMI v6 // SAKURA_NEURAL 🌸")
    sub_title = "☠ 拓磨様専属 タクティカルデッキ" if is_dark else "🌸 拓磨様専属 自律型オムニAI"
    hud_model = format_hud_model_name(model_name)
    model_label = f"{hud_model} (TTC HIGH)"
    engine_label = "Antigravity Black-Ice Core" if is_dark else "Antigravity SDK Native"

    top_char, bottom_char = ("┌", "└") if is_dark else ("╭", "╰")
    top_r, bottom_r = ("┐", "┘") if is_dark else ("╮", "╯")

    # メモリ実況取得
    mem_pct = 50
    try:
        if os.path.exists("/proc/meminfo"):
            with open("/proc/meminfo") as f:
                d = dict(line.split(":") for line in f if ":" in line)
                t = int(d.get("MemTotal", "0").split()[0])
                a = int(d.get("MemAvailable", "0").split()[0])
                if t > 0:
                    mem_pct = int(round((t - a) / t * 100))
    except Exception:
        pass

    # 1. Header Line
    title_text = Text.from_markup(f" [bold {primary}]{header_tag}[/] ")
    title_len = cell_len(title_text.plain)
    dash_count = max(0, term_width - 4 - title_len)
    top_bar = Text()
    top_bar.append(top_char + "─[", style=border_col)
    top_bar.append_text(title_text)
    top_bar.append("]" + "─" * dash_count + top_r, style=border_col)
    console.print(top_bar)

    # 2. Hero Body
    inner_width = term_width - 4
    if term_width >= 62:
        logo_lines = [
            " ______  __  ________  ____  ____  ____  ",
            "/_  __/ / / / / ____/ / / / /  |/  /  _/  ",
            " / / / /_/ / /_/ / /_/ / / /|_/ // /     ",
            "/_/  \\____/\\____/\\____/_/_/  /_/___/     "
        ]
        meta_lines = [
            f"[{primary}]{sub_title}[/]",
            f"[bold white]{model_label}[/]",
            f"[green]{engine_label}[/]",
            "[dim]Termux aarch64 · 4-Tier Memory[/]"
        ]
        for l, m in zip(logo_lines, meta_lines):
            l_text = Text.from_markup(f"[{secondary}]{l}[/]")
            m_text = Text.from_markup(m)
            l_len = cell_len(l_text.plain)
            m_len = cell_len(m_text.plain)
            pad = max(1, inner_width - l_len - m_len)
            row = Text()
            row.append("│ ", style=border_col)
            row.append_text(l_text)
            row.append(" " * pad)
            row.append_text(m_text)
            row.append(" │", style=border_col)
            console.print(row)
    else:
        # スマホ狭幅画面 (44-61 cols)
        meta_lines = [
            f"[{primary}]{sub_title}[/]",
            f"[bold white]🧠 {model_label}[/]",
            f"[green]⚡ {engine_label}[/]",
            "[dim]📱 Termux aarch64 · 4-Tier Memory[/]"
        ]
        for m in meta_lines:
            m_text = Text.from_markup(m)
            m_len = cell_len(m_text.plain)
            pad = max(0, inner_width - m_len)
            row = Text()
            row.append("│ ", style=border_col)
            row.append_text(m_text)
            row.append(" " * pad)
            row.append(" │", style=border_col)
            console.print(row)

    # 3. Divider
    div = Text()
    div.append("├" + "─" * (term_width - 2) + "┤", style=border_col)
    console.print(div)

    # 4. Telemetry Bar
    t_left = Text.from_markup(f" [green]📚 3072d RAG[/] │ [yellow]💾 RAM: {mem_pct}%[/] │ [dim]🔋 100%[/] │ [dim]💡 '/' でコマンド補完[/]")
    t_len = cell_len(t_left.plain)
    if t_len > inner_width:
        t_left = Text.from_markup(f" [green]📚 3072d[/] │ [yellow]💾 {mem_pct}%[/] │ [dim]💡 '/' で補完[/]")
        t_len = cell_len(t_left.plain)
    t_pad = max(0, inner_width - t_len)
    row_t = Text()
    row_t.append("│", style=border_col)
    row_t.append_text(t_left)
    row_t.append(" " * t_pad)
    row_t.append(" │", style=border_col)
    console.print(row_t)

    # 5. Bottom Status
    status_badge = Text.from_markup(f" ❯ STATUS: [bold green]{status_text}[/] ─{bottom_r}")
    st_len = cell_len(status_badge.plain)
    dash_bot = max(0, term_width - 1 - st_len)
    bot = Text()
    bot.append(bottom_char + "─" * dash_bot, style=border_col)
    bot.append_text(status_badge)
    console.print(bot)
    console.print()

    # 回路基板の描画（明示的ONの場合のみ）
    if show_matrix:
        print_ascii_neural_matrix(animate=False, mode=mode, model_name=model_name)

def _print_fallback_banner(console: Console, palette_cfg: dict, term_width: int):
    p_color = palette_cfg.get("primary", "cyan")
    ascii_art = (
        f"[bold {p_color}]  _____ _   _  ____ _   _ __  __ ___ [/bold {p_color}]\n"
        f"[bold {p_color}] |_   _| | | |/ ___| | | |  \\/  |_ _|[/bold {p_color}]\n"
        f"[bold {p_color}]   | | | | | | |  _| | | | |\\/| || | [/bold {p_color}]\n"
        f"[bold {p_color}]   | | | |_| | |_| | |_| | |  | || | [/bold {p_color}]\n"
        f"[bold {p_color}]   |_|  \\___/ \\____|\\___/|_|  |_|___|[/bold {p_color}]\n"
        f"[dim white]  ⚡ TUGUMIv6 // DEDICATED TO MASTER TAKUMA 🌸[/dim white]"
    )
    panel_w = max(40, min(term_width, 76))
    console.print(Panel(ascii_art, border_style=palette_cfg.get("border", "cyan"), subtitle="[bold green]ONLINE[/bold green]", width=panel_w))
