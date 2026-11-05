---
name: rich-cli-craftsman
description: 【高機能・プロフェッショナル・リッチCLI/TUI開発マスター】Python Rich, Textual, prompt_toolkit, Click/Typer, Go Bubble Tea, Rust Ratatui を駆使し、安直なAIスロップ・トイプログラムを完全排除。世界的トップテック企業（Claude Code, LazyGit, Charm.sh）水準の美麗なサイバーパンク/ネオン美学、思考ログ（Thinking）折りたたみ表示、リアルタイムストリーミング、ツール実行可視化インスペクタ、Termux/スマホ画面幅自動追従、East Asian Width防衛を一気通貫で設計・実装する最高峰CLI/TUIエンジニアリングスキル。
---

# rich-cli-craftsman
## 最高峰プロフェッショナル＆リッチCLI/TUI工学マスター規約

> **【絶対至上命題・Zero-Slop CLI 原則】**
> 単なる `print()` の生ANSIベタ書き、静的テキストのスクロール垂れ流し、思考ログやツール実行のブラックボックス化といった「安直なローカルLLMトイプログラム風CLI」を永久に根絶する。
> 息を呑むサイバー美学（Cyberpunk/Neon Aesthetic）、リアルタイムストリーミング、可視化ダッシュボード、スマホ縦画面（Termux aarch64）完全適応を兼ね備えた、世界水準のプロフェッショナルCLIを自律構築する。

---

## 1. 発動トリガー (Triggers)
- 「高機能なCLIを作って」「リッチなデザインのCLIにしたい」「TUIを作りたい」
- 「ターミナル画面をサイバーパンク風にかっこよくして」「ロゴやHUDを配置したい」
- 「AIエージェントの思考プロセスやツール実行をターミナルでリアルタイム可視化したい」
- 「Claude CodeやAiderのような洗練されたターミナル体験を実装したい」
- 「Termuxやスマホ環境でターミナルの文字崩れ・全角ズレを防止したい」
- 「Rich, Textual, prompt_toolkit を使ったCLIを構築・改修したい」

---

## 2. コア・デザイン哲学（Cyberpunk Design Tokens & Visual Hierarchy）

### 2.1 セマンティック・カラーパレット（Cyber-Neon System）
安直な原色（純赤・純青・純緑）を排し、現代的なサイバーパンク／ネオンパレットを使用する。

```python
# Semantic Cyber Palettes
CYBER_PALETTES = {
    "neon_cyber": {
        "primary": "#00f0ff",      # Electric Cyan (メインアクセント)
        "secondary": "#ff007f",    # Neon Magenta / Hot Pink (重要・ハイライト)
        "accent": "#7000ff",       # Deep Purple / Neon Violet (サブアクセント)
        "success": "#00ff88",      # Cyber Green / Matrix Mint (成功・正常)
        "warning": "#ffaa00",      # Electric Amber (警告・注意)
        "danger": "#ff2255",       # Crimson Neon (エラー・危機)
        "bg_dark": "#0a0c10",      # Deep Cyber Void
        "panel_border": "#00e5ff", # 輝く枠線
        "dim": "#5c6370",          # 補足・控えめテキスト
        "text": "#e6edf3",         # 高コントラスト白
    },
    "sakura_cyber": { # 表モード（通常モード）用：上品なサクラ×サイバー
        "primary": "#ff79c6",      # Sakura Pink
        "secondary": "#8be9fd",    # Soft Cyan
        "accent": "#bd93f9",       # Pastel Purple
        "success": "#50fa7b",      # Spring Green
        "warning": "#ffb86c",      # Soft Orange
        "danger": "#ff5555",       # Soft Red
        "panel_border": "#ff79c6", # サクラボーダー
        "dim": "#6272a4",
        "text": "#f8f8f2",
    }
}
```

### 2.2 視覚的階層（Visual Hierarchy）と余白（Whitespace）
1. **Header / HUD**: 起動時に画面上部に配置。ロゴ、モデル情報、ホスト環境、現在のモードを端正なパネルで表示。
2. **Thinking Accordion**: AIの思考過程（Thinking）は専用の薄紫/シアンの折りたたみ枠内にスピナー付きで描画。完了後は要約表示。
3. **Tool Execution Live Tree**: コマンド実行、Web検索、ファイル編集などのツール呼び出しは、`Rich.Tree` と `Spinner` でリアルタイムにネスト展開。
4. **Content / Code Stream**: 回答本文はリアルタイムストリーミング。コードブロックは言語シンタックスハイライト、行番号、ファイル名付きパネルでレンダリング。
5. **Docked Status Bar**: 画面下部にピン留め、またはプロンプト直前に常駐し、トークン数、レスポンス時間、メモリ使用率、バッテリー残量をコンパクトに提示。

---

## 3. 実践エンジニアリング・アーキテクチャ（Python Stack）

### 3.1 推奨アーキテクチャ・スタック
- **描画・レイアウト・装飾**: `rich.console.Console`, `rich.live.Live`, `rich.panel.Panel`, `rich.table.Table`, `rich.tree.Tree`, `rich.markdown.Markdown`, `rich.syntax.Syntax`
- **対話入力・コマンド補完**: `prompt_toolkit.PromptSession`, `prompt_toolkit.completion.FuzzyWordCompleter`, `prompt_toolkit.key_binding.KeyBindings`
- **引数・CLIエントリーポイント**: `argparse` または `typer` / `click`

### 3.2 思考プロセスの動的折りたたみ（Thinking Accordion Pattern）
```python
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner

console = Console()

def render_thinking_block(thought_text: str, is_active: bool = True):
    spinner = "⠋ " if is_active else "✔ "
    title = f"[bold #bd93f9]{spinner}Deep Thinking (Thinking Level: HIGH)[/bold #bd93f9]"
    return Panel(
        thought_text.strip(),
        title=title,
        border_style="#6272a4" if not is_active else "#bd93f9",
        padding=(0, 1),
    )
```

### 3.3 ツール実行のリアルタイム可視化（Live Tool Inspector Pattern）
```python
from rich.tree import Tree
from rich.live import Live

def display_tool_call(tool_name: str, args: dict, result_summary: str = None, status: str = "running"):
    icon = "⚡" if status == "running" else "✔"
    color = "yellow" if status == "running" else "green"
    
    tree = Tree(f"[{color}]{icon} [{tool_name}][/]")
    args_node = tree.add("[dim]Arguments[/]")
    for k, v in args.items():
        args_node.add(f"[cyan]{k}[/]: [white]{str(v)[:60]}[/]")
        
    if result_summary:
        tree.add(f"[bold green]Result:[/] [dim]{result_summary}[/]")
    return tree
```

### 3.4 外科的差分表示（Surgical Syntax Diff Pattern）
```python
from rich.syntax import Syntax

def print_diff_preview(file_path: str, diff_text: str):
    syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"[bold cyan]File Diff: {file_path}[/]", border_style="cyan"))
```

---

## 4. Termux (Android aarch64) 固有工学＆環境適応

1. **画面幅（Columns）の自動追従と安全リフロー**:
   - `shutil.get_terminal_size(fallback=(80, 24)).columns` を常に取得。
   - スマホ縦画面（幅60〜80）でパネルのタイトルや罫線が折り返して崩れるのを防止するため、最大幅制限または比率計算を適用。
2. **East Asian Width（全角半角幅）完全防衛**:
   - 日本語文字や絵文字（🌸, ⚡, 👑）はターミナル上で2カラム消費する。
   - `unicodedata.east_asian_width` を考慮した文字長計算を行い、罫線と右端境界のズレを完全に排除。
3. **パイプ・リダイレクト時の安全フォールバック (`isatty`)**:
   - `sys.stdout.isatty()` が `False` の場合、Rich のカラー装飾・ANSIコードを無効化し、純粋なテキストを出力して他コマンドとのパイプ連携（`| grep`, `> file.txt`）を破壊しない。
4. **Graceful Signal Handling**:
   - `signal.SIGINT` (Ctrl+C) 受信時にターミナルのカーソル（`\033[?25h`）と画面バッファを必ず復元して終了する。

---

## 5. 納品前5層検証ゲート（Verification Protocol）
1. **構文ゲート**: `python3 -m py_compile <cli_script>` で構文エラー皆無を確認。
2. **描画テスト**: スマホ最小幅（60カラム）とデスクトップ幅（120カラム）の双方で描画崩れがないことをシミュレーション実証。
3. **実機起動テスト**: `--help`, `--self-test`, 実対話モードが例外なくExit Code 0で終了することを確認。
4. **ノーデグレ検証**: 既存のビジネスロジック、APIクライアント、RAG検索、メモリ永続化との連携が100%維持されていることを確認。
