---
name: session-transcript-context-recoverer
description: "直前のセッションログや成果物を解析し、中断した作業の文脈を正確に復元する."
version: 0.1.0
author: Hermes
category: AI・エージェント
created_at: 2026-10-29T17:42:58Z
---

# Session Transcript Context Recoverer

## When to Use
- ユーザーから「前回の続きから」「前のセッション覚えてる？」と指示されたとき。
- セッションが強制終了やタイムアウトで中断し、直前の進行状況やエラー原因を特定したいとき。
- 長大なトランスクリプトから最終ステップの標準出力・標準エラー出力および生成ファイルを素早く確認したいとき。

## Prerequisites
- Python 3.x が実行可能であること。
- `~/.gemini/antigravity/brain/` または指定のセッションログディレクトリへの読み取り権限があること。

## How to Run
ヘルパースクリプト `recover_context.py` を実行して直近のセッションの末尾ステップとツール実行結果を抽出します。
```bash
python3 ~/.agents/skills/session-transcript-context-recoverer/scripts/recover_context.py --lines 10
```

## Quick Reference
| オプション | 説明 | デフォルト |
| :--- | :--- | :--- |
| `--brain-dir` | セッションログのベースディレクトリ | `~/.gemini/antigravity/brain` |
| `--session-id` | 特定のセッションID（省略時は最新を自動選択） | 最新ディレクトリ |
| `--lines` | 取得する末尾ステップ数 | `10` |
| `--step` | 詳細表示する特定のステップ番号 | なし |

## Procedure
1. `recover_context.py` を実行し、最新の `transcript_full.jsonl`（または `transcript.jsonl`）の末尾ステップ一覧を出力する。
2. 最終ステップ付近で実行されたツール名、引数、およびエラーの有無（stdout/stderr）を確認する。
3. 特定のステップの出力が切り詰められている場合は、`--step <番号>` オプションを指定して完全な実行ログを取得する。
4. ログ内で言及されている成果物ディレクトリ（例: `/storage/emulated/0/TUGUMIDesk/...`）やスクリプトの該当行を `ls -laR` や `coding_read_lines` で実地確認し、作業を再開する。

## Pitfalls
- `transcript.jsonl` は出力が省略されている場合があるため、詳細なツール出力を確認する際は `transcript_full.jsonl` を優先して参照すること。
- ツール実行結果の `content` フィールドはマークダウンのコードブロック（````json ... ````）でラップされた二重JSON構造になっていることがあるため、パース時に注意すること。

## Verification
- 直前のセッションの最終ゴール、完了した処理、未完了またはエラーとなった処理の3点が明確に特定できていること。
- 関連するローカルファイルや成果物の存在がファイルシステム上で裏付けられていること。
