---
name: termux-context-aware-reporter
description: "端末環境とWeb検索情報を統合して調査レポートを作成する."
version: 0.1.0
author: Hermes
category: リサーチ
created_at: 2026-10-30T16:50:50Z
---

# Context-Aware Research Reporter

## When to Use
- ユーザーからメニュー番号や簡略指示を受け、システム状態と外部リサーチを組み合わせたレポートを生成する場合。
- バッテリー残量や現在地周辺の天候など、実行環境の文脈を反映した詳細レポートを作成する場合。

## Prerequisites
- Termux環境またはLinuxシェル環境。
- `curl` コマンドが利用可能であること。
- インターネット接続（Open-Meteo APIおよび検索ツールへのアクセス）。

## How to Run
1. スクリプトやメニューの定義を特定（必要に応じてメニュー定義ファイルを検索）。
2. バッテリーおよび気象API (`api.open-meteo.com`) から環境コンテキストを取得。
3. 指定キーワードについてWeb検索を実行。
4. 模範レポート形式に準拠してマークダウンレポートを出力。

## Quick Reference
```bash
# 気象データ取得例（緯度経度指定）
curl -s "https://api.open-meteo.com/v1/forecast?latitude=35.3039&longitude=136.8031&current=temperature_2m,relative_humidity_2m,weather_code&timezone=Asia%2FTokyo"

# メニュー項目確認
grep -rn "^[[:space:]]*[0-9]\+)" ~/bin/
```

## Procedure
1. **指示解析とスクリプト検証**: 番号指示（例: 「6」）の場合、`~/bin/` 配下のシェルメニュー定義を grep して対応する処理内容を同定する。
2. **端末・環境コンテキスト収集**: `get_battery_info` ツールや Open-Meteo API から温度・湿度・天候コードを取得する。
3. **対象テーマのWebリサーチ**: `web_search_duckduckgo` 等を利用して最新情報・トピックを検索する。
4. **統合レポート作成**: 成功例リファレンスの構成（基本情報、活動実績、エピソード、分析）に沿って構造化されたドキュメントを作成・保存する。

## Pitfalls
- 番号単体の指示を勝手な推測で処理せず、既存スクリプト（server-menu 等）の定義箇所を特定して対応項目を確認すること。
- 緯度経度の固定値依存を避け、必要に応じて位置情報設定を参照すること。
- Web検索結果の日付と事実関係の整合性を確認すること。

## Verification
- 生成されたレポートに端末状態・気象データ・最新トピックが漏れなく反映されているか確認。
- マークダウンの構文および見出し階層が崩れていないか検証。
