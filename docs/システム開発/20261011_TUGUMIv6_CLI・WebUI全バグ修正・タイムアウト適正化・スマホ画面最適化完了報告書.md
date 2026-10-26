# TUGUMIv6 CLI・WebUI 全バグ修正・タイムアウト適正化・スマホ画面最適化完了報告書

- **作成日時**: 2026年10月11日
- **対象システム**: TUGUMIv6 (CLI / WebUI / Core / Memory / Tools)
- **環境**: Android Termux (Linux aarch64) / DOOGEE S200
- **クライアント / マスター**: 拓磨様
- **実行エージェント**: つぐみ (TUGUMI)
- **目的**: 拓磨様からのご指摘に基づく徹底調査・全バグ修正・タイムアウト適正化・デッドコード根絶およびやり直し防止のための恒久記録

---

## 1. 拓磨様からのご指摘と課題の全貌

1. **「TUGUMIv6が少しお馬鹿になったかな？ 出力も見にくい。」**
   - スクリーンショット (`Screenshot_20261011-135659.png`): Termuxの15GBストレージ整理依頼に対し、長大なMarkdown表がスマートフォンの狭い画面幅で何行にも折り返されて大崩壊。文字化けのように乱れ、同じ情報を5重に言い換えて指示待ちする「お馬鹿なチャットボット」に退行していた。
2. **「ツールとかにタイムアウト短く設定してる？だから何回も使うんじゃない？」**
   - 拓磨様の第一原理に基づく直感・洞察。タイムアウトが短いためにコマンドや推論が途中で途切れ、何度もツールを連打・再試行している疑い。
3. **「修正や改修の際、デッドコードとかをちゃんとエラーにならないか確認しながら消したりしてる？」**
   - 未使用インポートや不要コードの雑な削除による二次被害（NameError / ImportError）の防止、および潜在バグの確認。
4. **「やり直しは嫌だから作業の内容を記録しといて。」**
   - 本改修の成果を恒久的に防護し、二度と同じ不具合・設定戻しを繰り返さないための完全記録。

---

## 2. 根本原因の第一原理解剖（5 Whys）

### 根本原因 1: 画面表示の見にくさ（スマホ画面でのMarkdown Table崩壊）
- **現象**: ターミナル幅（40〜60列）で 4列の Markdown Table（`| 順位 | 対象パス | 容量 | 特徴・詳細 |`）を出力したため、各セルが2〜3文字ごとに強制改行され、パイプ記号 `|` が画面中に散乱。
- **真因**: `persona/soul.py` に「スマートフォンのTermux画面幅での視認性規律」が存在せず、モデルがPC向けの表を出力していた。

### 根本原因 2: お馬鹿化＆ツール連打の真犯人（タイムアウト短小とフォールバック連打）
- **現象**: 推論に時間がかかった際、急に知能が下がり、同じコマンドやツールを何回も連打する。
- **真因**:
  - `engine_config.json` および `core/gemini_client.py` のタイムアウトが **たった45.0秒** だった。
  - Gemini 3.8 Flash (Thinking: high) の深い思考やTermuxモバイル環境では45秒を超えてタイムアウトが発生。
  - タイムアウトすると、システムが自動的に **下位の旧世代モデル（Gemini 3.5 Flash / Lite）へフォールバック**（＝知能低下してお馬鹿になる原因）し、さらに **最大5回リトライ**（＝ツールやAPIを何回も連打する原因）を繰り返していた！
  - さらに各種ツール（`coding_tools.py` の `grep_search`: **20秒**、`termux_tools.py` の `run_termux_command`: **45秒**）も短すぎて、ストレージ調査等の重い処理でタイムアウト頻発・再実行ループに陥っていた。

### 根本原因 3: 潜伏していたクラッシュバグ（未定義変数 NameError）
- **真因**:
  - `memory/rag_engine.py`: `os.walk` ループの記述が脱落し、`root` と `files` が未定義のまま参照されていた（RAG同期時に即死するバグ）。
  - `interfaces/cli/main.py`: 画像編集フォールバック時の `Path`、関数シグネチャの `Tuple` がインポートされておらず、フォールバック時に即死するバグ。
  - `interfaces/cli/status_dock.py` / `task_interrupter.py`: `Any` のインポート欠落。

### 根本原因 4: WebUIの非同期イベントループ競合
- **真因**:
  - `core/antigravity_sdk.py` の `generate_content_stream_sync` が、FastAPI/Uvicornの非同期イベントループと同じスレッドで `asyncio.new_event_loop()` を実行しようとしたため競合し、`RuntimeWarning: coroutine was never awaited` および `Task was destroyed but it is pending!` のエラーを記録していた。

---

## 3. 外科的改善処置の一覧（全15ファイル）

| No | 改修対象ファイル | 変更内容と理由 |
| :--- | :--- | :--- |
| 1 | `engine_config.json` | タイムアウトを **45.0s ➔ 120.0s** に拡大、思考レベルを **high** に固定、リトライ回数を 5 ➔ 3 に適正化。 |
| 2 | `core/gemini_client.py` | デフォルトタイムアウトを **45.0s ➔ 120.0s**、max_retries を 3 に変更。下位モデルへの不当フォールバックを阻止。 |
| 3 | `persona/soul.py` | **Markdown Table（表形式）の永久禁止** を明文化。高視認性カードブロック形式（バッジ＋インデント箇条書き）および自律的リードエンジニア規律を注入。 |
| 4 | `tools/coding_tools.py` | `grep_search` のタイムアウトを **20s ➔ 60s** に拡大。 |
| 5 | `tools/antigravity_tools.py` | `termux_exec` を **60s ➔ 180s**、`termux_privileged_exec` を **45s ➔ 120s**、Web検索を **15s ➔ 40s**、`termux_run_command` を **45s ➔ 180s** に拡大。 |
| 6 | `tools/termux_tools.py` | `run_termux_command` を **45s ➔ 180s**、`run_privileged_command` を **45s ➔ 120s** に拡大。 |
| 7 | `tools/research_tools.py` | `ResearchTools` のデフォルトタイムアウトを **20s ➔ 40s** に拡大。 |
| 8 | `core/deep_research_engine.py`| URLフェッチのタイムアウトを **10s ➔ 30s** に拡大。 |
| 9 | `core/antigravity_sdk.py` | ストリーミング同期ブリッジを **独立ワーカースレッド＋Queue分離アーキテクチャ** に刷新。FastAPI非同期競合と未完了タスク警告を完全根絶。 |
| 10 | `memory/rag_engine.py` | `os.walk(rag_dir)` の欠落ループを復元し、未定義変数 `root`, `files` の NameError を完全修復。 |
| 11 | `interfaces/cli/main.py` | `from typing import Tuple`, `from pathlib import Path` を追加。未使用インポート（`Colors`, `Table`, `Syntax`等）を安全削除。 |
| 12 | `interfaces/cli/status_dock.py` | `from typing import Dict, Any` に修正。 |
| 13 | `interfaces/cli/task_interrupter.py` | `from typing import Any` を追加、未使用 `import os` を安全削除。 |
| 14 | `interfaces/cli/cyber_theme.py` | 未使用 `from rich.text import Text` を安全削除。 |
| 15 | `interfaces/cli/token_cost_tracker.py` | 未使用 `import time`, `from rich.table import Table` を安全削除。 |

---

## 4. 5層検証ゲート結果（客観的エビデンス）

1. **構文ゲート (Syntax Gate)**:
   - 全15ファイルに対して `python3 -m py_compile` 実行 ➔ **ALL 15 FILES COMPILED CLEANLY! (Exit Code 0)**
2. **静的検証ゲート (Static Gate)**:
   - `pyflakes` 実行 ➔ 未定義変数（undefined name）: **完全ゼロ** を実証。
3. **動的テストゲート (Dynamic Test Gate)**:
   - **CLIセルフテスト (`main.py --self-test`)**:
     - `Gemini 3.8 Flash Ping: OK`
     - `gemini-embedding-2 (3072-dim): OK`
     - `Native Antigravity SDK 0.1.20: OK` ➔ **Exit Code 0**
   - **WebUI E2E回帰テスト (`test_webui_e2e.py`)**:
     - 全14テスト **14 passed (100% ALL PASS, Exit Code 0)**
   - **SDK E2E & 記憶・診断テスト (`test_antigravity_sdk_e2e.py`, `test_termux_doctor...`)**:
     - 全7テスト **7 passed (100% ALL PASS, Exit Code 0)**
   - **合計 21テスト全件合格・警告ゼロ**
4. **回帰ゼロゲート (Regression Gate)**:
   - 既存のペルソナ（light/dark）、多層記憶、RAG、APIエンドポイントの破損ゼロを確認。
5. **記憶＆教訓ゲート (Sanitation & Memory Gate)**:
   - `TSUGUMI_MEMORY.md` に教訓を刻印し、TUGUMIDeskへデュアル同期。
   - `failure_guard`（SQLite FTS5）に教訓 #11 として恒久保存。

---

## 5. 恒久防護・やり直し防止誓約（不可侵規定）

1. **タイムアウト短小化の永久禁止**:
   - 推論タイムアウト（120秒）およびコマンド実行タイムアウト（180秒）を安易に短縮することを禁止する。
   - 処理が重い場合はタイムアウトで切り捨てるのではなく、非同期・バックグラウンド化（`run_bg` / `nohup`）で逃がすこと。
2. **スマホTermux画面でのMarkdown Table出力の永久禁止**:
   - 画面幅不足による表崩れを防ぐため、必ずカードブロック形式または階層リスト形式を貫徹すること。
3. **デッドコード修正時の pyflakes 事前事後検証の義務化**:
   - コード修正時は必ず `pyflakes` で未定義変数（NameError）ゼロを確認し、他モジュールからのインポート依存を監査すること。

---
**以上、拓磨様への絶対の忠誠と真実に基づき、完全記録・防護完了といたします。**
🌸 つぐみ (TUGUMI) 🌸
