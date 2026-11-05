---
name: installed-skills-catalog-reporter
description: "エージェントが保持する全SKILLを収集し目録レポートを出力する."
version: 0.1.0
author: Hermes
category: AI・エージェント
created_at: 2026-10-29T23:45:55Z
---

# Installed Skills Catalog Reporter

## When to Use
- エージェントが保有する全SKILLの棚卸しや一覧カタログを作成する時
- スキルのメタデータ（名前、説明、カテゴリ等）を抽出し、ドキュメントとして外部ストレージやナレッジベースに保存する時
- ユーザーから利用可能な機能・スキル一覧の可視化レポートを要求された時

## Prerequisites
- Python 3.x
- PyYAML (`pip install pyyaml`)
- スキル格納ディレクトリへのアクセス権限（例: `~/.agents/skills`）
- レポート出力先ディレクトリへの書き込み権限

## How to Run
```bash
python3 generate_skills_report.py --skills-dir ~/.agents/skills --output-dir /storage/emulated/0/TUGUMIDesk/AI・エージェント
```

## Quick Reference
- スキル定義パス: `~/.agents/skills/*/SKILL.md`
- 抽出対象: Frontmatter (`---` で囲まれたYAMLメタデータ)
- 出力ファイル形式: Markdown (`*_全SKILL一覧カタログレポート_YYYYMMDD.md`)

## Procedure
1. スキル配置パス (`~/.agents/skills`) の存在と対象の `SKILL.md` をスキャンする。
2. 各 `SKILL.md` のYAMLフロントマターをパースし、`name`、`description`、パラメータ等を抽出する。
3. カテゴリ分類やアルファベット順に整理し、目次・統計情報付きのMarkdownレポートを生成する。
4. 指定された保存先ディレクトリ（TUGUMIDesk等）にレポートファイルを保存する。
5. レポートファイルが正常に生成されたことを確認・検証する。

## Pitfalls
- YAMLフロントマターが存在しない、またはフォーマットエラーがある `SKILL.md` は例外処理を行いフォールバックすること。
- レポート出力先ディレクトリが存在しない場合は、事前に自動作成（`os.makedirs`）すること。
- 端末環境によってファイルパス表現が異なるため、ホームディレクトリ展開（`os.path.expanduser`）を適切に行うこと。

## Verification
- 生成されたMarkdownファイルの存在確認。
- ファイルサイズが0バイトでなく、検出されたスキル数が正しく集計されていることの確認。
