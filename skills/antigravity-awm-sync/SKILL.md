---
name: antigravity-awm-sync
description: "Synchronize Antigravity session traces into AWM skills."
version: 0.1.0
author: Hermes
category: AI・エージェント
created_at: 2026-10-27T23:56:14Z
---

# Antigravity AWM Interceptor & Skill Distiller

## When to Use
- Antigravity CLIのセッション実行履歴(`transcript.jsonl`)からノイズを除去し、再利用可能なAWM (Agent Workflow Memory) DAGおよびSKILLパッケージを生成・同期する場合。
- API仕様変更やモデル更新に伴い、インタセプタスクリプトを復旧・更新する場合。

## Prerequisites
- Python 3.10以上
- `google-genai` パッケージおよび有効な `GEMINI_API_KEY` 環境変数
- AWMコアパッケージ (`~/.agents/awm`)
- Antigravity CLIのログディレクトリ (`~/.gemini/antigravity-cli/brain/`)

## How to Run
```bash
# 1. 環境と構文の整合性検証
python3 -m py_compile ~/ag_awm_interceptor.py

# 2. 指定セッションのAWM学習・スキル同期の実行
python3 ~/ag_awm_interceptor.py --conv "<CONVERSATION_UUID>" --goal "<TARGET_GOAL>"
```

## Quick Reference
- ログディレクトリ: `~/.gemini/antigravity-cli/brain/<CONV_ID>/.system_generated/logs/transcript.jsonl`
- スクリプトバックアップ: `cp ag_awm_interceptor.py ag_awm_interceptor.py.bak_$(date +%Y%m%d)`
- オプション引数:
  - `--conv`: 対象セッションUUID
  - `--goal`: 学習対象ゴール概要
  - `--model`: 使用Geminiモデル (デフォルト: `gemini-2.5-flash` / `gemini-3.8-flash` 等)

## Procedure
1. **環境変数の事前チェック**: `GEMINI_API_KEY` が設定されていることを確認。
2. **既存スクリプトのバックアップ**: 変更を加える前に `ag_awm_interceptor.py` を日付付きで複製。
3. **スクリプト修正・再設定**: トークン計測、API 503/429リトライ機構、引数マッピング(`tool_calls` vs `arguments`)の補正を組み込む。
4. **構文チェックと実行権限付与**: `chmod +x` を行い、`python3 -m py_compile` で構文エラーがないことを確認。
5. **対象ログの確認**: 対象セッションディレクトリ内に `transcript.jsonl` が存在することを確認。
6. **AWM同期実行**: `--conv` と `--goal` を指定して同期スクリプトを実行し、正常終了を検証。

## Pitfalls
- APIキー未定義時にGeminiクライアント初期化でクラッシュするため、実行前に環境変数を確認すること。
- Antigravity CLIのログ形式変更により、ツール引数が `arguments` ではなく `tool_calls` に格納されている場合があるため、両形式をフォールバック解決するパーサーが必要。
- 一時的な 503 UNAVAILABLE や 429 エラーに対して指数バックオフリトライを挟まないと長大セッションの蒸留が失敗する。

## Verification
- `python3 -m py_compile ag_awm_interceptor.py` がリターンコード 0 を返す。
- 実行ログにトークン消費量と「Workflow distilled successfully」が出力される。
