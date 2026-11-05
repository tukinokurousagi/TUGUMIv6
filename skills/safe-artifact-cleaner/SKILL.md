---
name: safe-artifact-cleaner
description: "不要な生成物を事前検証した上で安全に一括削除し確認する手順."
version: 0.1.0
author: Hermes
category: ツール
created_at: 2026-10-30T23:26:49Z
---

# Safe Artifact Cleaner

## When to Use
- ユーザーから不要となった生成物や一時ファイルの一括削除を指示された時
- ディスク容量解放のために特定パターンのファイルをクリーンアップする時
- 誤削除を防ぐために対象の事前カウントと事後検証を徹底したい時

## Prerequisites
- bash または sh 環境
- 対象ディレクトリへのアクセス権限および削除権限

## How to Run
```bash
# 1. 対象一覧と件数の事前確認
ls -l /path/to/dir/*.ext
ls -1 /path/to/dir/*.ext | wc -l

# 2. 安全な削除実行
rm -f /path/to/dir/*.ext

# 3. 事後検証とディスク確認
ls -la /path/to/dir/*.ext 2>/dev/null | wc -l
df -h /path/to/dir
```

## Quick Reference
- 対象確認: `ls -la <TARGET_PATTERN>`
- 件数計測: `ls -1 <TARGET_PATTERN> 2>/dev/null | wc -l`
- 削除実行: `rm -f <TARGET_PATTERN>`
- 容量確認: `df -h <TARGET_DIR>`

## Procedure
1. **対象ファイルのインベントリ確認**: 削除対象となるファイルパターンを一覧表示し、削除してはならないファイル（コード、ドキュメント等）が含まれていないか確認する。
2. **対象件数の事前カウント**: 削除予定のファイル総数を記録する。
3. **削除コマンドの実行**: 意図したパターンのみを指定して安全にファイルを削除する（誤爆防止のためワイルドカードのスコープを限定する）。
4. **削除完了の事後検証**: 対象パターンが0件になったことを確認する。
5. **ディスク領域の確認**: 削除後のストレージ空き容量を報告する。

## Pitfalls
- ワイルドカード展開の誤り: `rm -rf *` のような大雑把な指定は避け、拡張子やパスを明示すること。
- 保護対象の混在: 画像削除時にコードやPDFなど別拡張子の重要ファイルが存在しないか事前にスコープを分離すること。

## Verification
- `ls -la <TARGET_PATTERN> 2>/dev/null | wc -l` の出力が `0` であること。
- `df -h` で空き容量が正常に解放されていること。
