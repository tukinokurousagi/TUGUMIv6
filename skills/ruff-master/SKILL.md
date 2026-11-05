---
name: ruff-master
description: Ruff (Rust製超高速Python Linter/Formatter) を極限まで使いこなし、Python 3.14仕様に完全適合した静的解析・自動修正(--fix)・pyproject.toml/ruff.toml設計・ルール体系理解・CI/CD統合・エラー外科的修復を完遂するスキル
---

# Ruff Master スキル (Python 3.14 Specification)

## 1. 概要
本スキルは、Pythonコードの静的解析・フォーマット・インポート整理・型アノテーションチェック・脆弱性検知を電光石火（従来のFlake8/Black/isort/Bandit等の10〜100倍高速）で実行するRust製ツール **Ruff** を、**Python 3.14 (PEP 695, PEP 649/749, PEP 702, PEP 736等) 仕様** に完全適合させて自由自在に操るための専門知識と行動プロトコルです。

Android Termux (Linux aarch64, Python 3.14.6) 環境を含むあらゆるPython開発において、コード品質の維持、不具合の未然検知、自動修正 (`--fix`)、外科的コード修復を自律完遂します。

---

## 2. Python 3.14 時代における Ruff の進化と重要対応

Python 3.14 をターゲットとする開発では、Ruff の強力なルールセットが最新の言語仕様を最大限に活用できるよう拡張されています：

1. **PEP 695 型パラメータ構文 (Type Parameter Syntax)**:
   - `type Point[T] = tuple[T, T]` や `def calculate[T: (int, float)](val: T) -> T:` のネイティブ構文解析。
   - `UP040` により、レガシーな `TypeAlias` や `TypeVar` による冗長な型定義を最新の `type` 文へ自動現代化。
2. **PEP 649 / PEP 749 型アノテーション遅延評価 (Deferred Evaluation)**:
   - `from __future__ import annotations` なしでもアノテーションがオンデマンド評価される仕様に基づき、不要な引用符（UP037）や循環参照の静的チェックが最適化。
3. **最新型アノテーション標準化 (UP006, UP007, UP045)**:
   - `typing.Union[A, B]` → `A | B`
   - `typing.Optional[A]` → `A | None`
   - `typing.List[T]`, `typing.Dict[K, V]` → ビルトイン `list[T]`, `dict[K, V]`
4. **PEP 702 非推奨警告の明示化**:
   - `warnings.deprecated` による廃止予定APIの検知と安全なリファクタリング。
5. **グローバルデフォルト py314 適用**:
   - `~/.config/ruff/ruff.toml` により、リポジトリ個別設定の有無に関わらず常に Python 3.14 基準で解析を実行。

---

## 3. コア行動プロトコル (Lint, Format & Repair Loop)

```
[対象Pythonファイル/ディレクトリ特定]
       │
       ▼
[構文チェック: python3 -m py_compile <file>]
       │ (Pass)
       ▼
[Ruff Format: ruff format <file>] (コードスタイル整形)
       │
       ▼
[Ruff Check 第一撃: ruff check --fix <file>] (Python 3.14モダン化・自動修正を一括解決)
       │
       ├─── エラーゼロ ───> 【合格 (Exit Code 0)】
       │
       ▼ (手動修復が必要なルール検出: F821/F841/B008/E501等)
[ルール調査・解剖: ruff rule <RULE_CODE>]
       │
       ▼
[外科的コード編集 (replace_file_content)]
       │
       ▼
[再検証: ruff check <file>] ─── ループ (未解決なら反復修復) ───> 【合格】
```

### ステップ詳細
1. **構文事前検証 (Syntax Gate)**:
   - Python 3.14 ASTレベルの致命的構文エラーがないか `python3 -m py_compile <filepath>` で確認。
2. **フォーマット (Format Gate)**:
   - `ruff format <filepath>` を実行。Black互換のインデント、クォート、改行位置、PEP 695 構文配置の自動標準化。
3. **自動修復第一撃 (Auto-Fix Gate)**:
   - `ruff check --fix <filepath>`（または安全でない修正も含めるなら `--fix --unsafe-fixes`）。
   - 未使用インポート (F401)、インポート順序 (I001)、不要なf-string (F541)、Python 3.14仕様への型アノテーション現代化 (UP006/UP007/UP040/UP045) を瞬時に解消。
4. **手動外科的修復 (Surgical Repair Gate)**:
   - 自動修正できないセマンティックな警告（未定義変数 F821、スコープ問題、関数のデフォルト引数にミュータブルオブジェクト B006 等）を特定し、前後コンテキストを保った小差分で改修。
5. **ルール仕様確認**:
   - 不明なルールや背景理由を確認する際は `ruff rule <RULE_CODE>` を実行して公式解説・修正例を取得する。
6. **最終確認 (Final Gate)**:
   - `ruff check <filepath>` で Exit Code 0（All checks passed!）を客観確認。

---

## 4. 主要ルールセット体系 (Rule Prefix Matrix)

Ruffは数多くのレガシーツールのルールを統合・内包しています。代表的なプレフィックス：

| Prefix | 元ツール / 目的 | 代表的ルール・Python 3.14適用機能 |
|---|---|---|
| **UP** | pyupgrade | **Python 3.14現代的構文へのアップグレード** (`type T = ...`, `X \| None`, `list[T]`) |
| **E / W** | pycodestyle | PEP8スタイル違反、空白、インデント、比較演算 |
| **F** | Pyflakes | 未定義変数 (F821)、未使用変数 (F841)、未使用インポート (F401) |
| **I** | isort | インポートのグルーピング・アルファベット順ソート (I001) |
| **B** | flake8-bugbear | ミュータブルなデフォルト引数 (B006)、ループ内関数定義 (B023) |
| **S** | flake8-bandit | セキュリティ脆弱性 (SQLi, hardcoded password, insecure hash) |
| **C90** | mccabe | 循環的複雑度 (Cyclomatic Complexity) の上限チェック |
| **SIM** | flake8-simplify | 冗長なif文・代入・コンテキストマネージャの簡素化 |
| **T20** | flake8-print | 本番コード内の `print` 文残存検知 |
| **PTH** | flake8-use-pathlib | `os.path` ではなく現代的な `pathlib.Path` の使用推奨 |
| **RUF** | Ruff独自 | Ruff特有の最適化、asyncio誤用検知、内部バグ予防 |

---

## 5. プロジェクト設定ベストプラクティス (Python 3.14仕様)

### 5.1 グローバル設定 (`~/.config/ruff/ruff.toml`)
すべてのプロジェクトの基底となるユーザーレベル設定：
```toml
# Ruff Global Configuration: ~/.config/ruff/ruff.toml
target-version = "py314"
line-length = 100
indent-width = 4

[lint]
select = [
    "E",     # pycodestyle errors
    "W",     # pycodestyle warnings
    "F",     # Pyflakes
    "I",     # isort
    "B",     # flake8-bugbear
    "UP",    # pyupgrade (Python 3.14 modern syntax)
    "SIM",   # flake8-simplify
    "RUF",   # Ruff-specific rules
]
ignore = [
    "E501",  # 行長制限 (Formatterに任せるため無視推奨)
    "B008",  # FastAPI等のDepends()による関数呼び出し引数許可
]
fixable = ["ALL"]
unfixable = []

[lint.isort]
combine-as-imports = true
force-single-line = false

[lint.per-file-ignores]
"tests/**/*.py" = ["S101", "D"]  # テスト内のassert許可
"__init__.py" = ["F401"]         # 公開用インポート許可

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

### 5.2 プロジェクト個別設定 (`pyproject.toml`) に組み込む場合
```toml
[tool.ruff]
target-version = "py314"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "RUF"]
ignore = ["E501", "B008"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

---

## 6. よく遭遇するエラーと外科的修復パターン (Python 3.14編)

| ルールコード | 症状・警告内容 | 外科的修復アプローチ (Python 3.14) |
|---|---|---|
| **UP040** | `non-pep695-type-alias` | `MyType = TypeAliasType(...)` や `MyType: TypeAlias = ...` を `type MyType[T] = list[T]` に修正。 |
| **UP006** | `deprecated-collection-type` | `from typing import List, Dict` → ビルトイン `list[int]`, `dict[str, Any]` に自動変換。 |
| **UP007** | `non-pep604-annotation` | `Union[int, str]` → `int \| str` に自動修正。 |
| **UP045** | `non-pep604-annotation-optional` | `Optional[float]` → `float \| None` に自動修正。 |
| **F401** | `unused-import` (未使用インポート) | `ruff check --fix` で自動削除。ライブラリ公開用なら `__all__ = [...]` に含めるか `# noqa: F401`。 |
| **F821** | `undefined-name` (未定義変数名) | モジュール先頭でインポートを追加、または変数定義順序の修正。 |
| **F841** | `unused-variable` (未使用ローカル変数) | 不要なら削除。戻り値のアンパック等で必要なら `_` またはプレフィックス `_var` に改名。 |
| **B006** | `mutable-argument-default` (可変引数) | `def func(items=[])` → `def func(items: list[Any] \| None = None): if items is None: items = []`。 |
| **I001** | `unsorted-imports` (インポート未ソート) | `ruff check --fix` で自動整列（標準ライブラリ → サードパーティ → ローカルの3段構成）。 |
| **SIM102** | `collapsible-if` (ネスト単一if) | `if a: if b:` → `if a and b:` に統合。 |

---

## 7. コマンドライン実践集 (Cheat Sheet)

```bash
# 1. 基本的なLintチェック (Python 3.14仕様)
ruff check .

# 2. 自動修正可能な問題を即座に修復 (型現代化・未使用整理)
ruff check --fix .

# 3. 安全でない修正 (unsafe fixes) も含めてアグレッシブに修復
ruff check --fix --unsafe-fixes .

# 4. コードフォーマッタの実行 (PEP 695完全対応)
ruff format .

# 5. 特定のファイルのみをチェック＆フォーマット
ruff check --fix path/to/script.py
ruff format path/to/script.py

# 6. ルールの詳細な背景と修正例を調べる
ruff rule UP040

# 7. 差分だけをプレビュー (Dry-run)
ruff check --diff .
ruff format --diff .

# 8. 現在解決されているターゲットバージョンや設定の確認
ruff check --show-settings | grep target_version
```
