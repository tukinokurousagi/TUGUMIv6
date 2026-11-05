---
name: donut-browser
description: 【Donut Browser アンチディテクト・ブラウザ完全自動化＆MCP制御マスター】オープンソースのプライバシー特化型・アンチフィンガープリントブラウザ「Donut Browser」を、Antigravity CLI および TUGUMIv6 からローカルREST API（ポート10108）およびMCP 2.0（donut_browserツール群）を介して自在に遠隔制御・自動化する専門スキル。Cloudflare・reCAPTCHA v3等のボット検知をバイパスするWebスクレイピング、プロファイル管理、ページ認識（Perception）、要素クリック・文字入力・データ抽出を自律遂行します。
---

# Donut Browser アンチディテクト・ブラウザ制御＆自動化スキル

## 1. 概要
Donut Browser（https://donutbrowser.com）は、Wayfern Chromium フォークを基盤としたオープンソースのアンチディテクト・プライバシー保護ブラウザです。
プロファイルごとに独立したフィンガープリント（User-Agent, Canvas, WebGL, 画面解像度, オーディオ, フォント）、Cookie、拡張機能、プロキシ（HTTP/SOCKS5）、WireGuard VPN を保持し、Webサイトによるアカウント紐付けやブロックを回避します。

本スキルは、Termux / Linux 環境上の **TUGUMIv6** および **Antigravity CLI** から、Donut Browser の Local REST API（`127.0.0.1:10108`）および MCP 2.0 インターフェースを通じてブラウザを自在に操作・自動化するための総合ガイドです。

---

## 2. 統合インターフェース

### 2.1 Antigravity CLI MCP ツール（`donut_browser`）
Antigravity CLI は以下の MCP ツールを通じて Donut Browser を直接操作できます：
- `donut_status`: 接続診断・認証状態・ポート設定の確認
- `donut_config`: トークン・ホスト・ポートの動的変更・保存
- `donut_list_profiles`: 登録プロファイル一覧（ID、名前、OS、プロキシ設定等）の取得
- `donut_get_profile`: 特定プロファイルの完全な設定情報取得
- `donut_create_profile`: 新規プロファイルの作成（OS、フィンガープリント等）
- `donut_run_profile`: プロファイルの起動（CDP URL取得）
- `donut_kill_profile`: プロファイルの停止・終了
- `donut_open_url`: 指定プロファイルでURLを開く
- `donut_perceive`: ページのアクセシビリティツリー・可視テキスト・要素一覧の認識
- `donut_click`: 要素のクリック（ロール、名前、セレクタ指定）
- `donut_type`: フォーム・テキストボックスへの文字列入力
- `donut_extract`: 構造化データ（テーブル、リスト）の自動抽出
- `donut_scrape`: プロファイル起動 → URL遷移 → ページ解析 → 停止を一括実行

### 2.2 CLI 武器コマンド（`donut`）
Termux ターミナルからワンコマンドで実行可能：
```bash
# 接続診断と設定確認
donut status

# 認証トークンやホスト・ポートの設定
donut config --token <YOUR_TOKEN>
donut config --host 127.0.0.1 --port 10108

# プロファイル一覧の表示
donut list

# 新規プロファイル作成
donut create "MyProfile" --os windows --notes "Research account"

# プロファイル起動（URL指定・ヘッドレス指定可能）
donut run <profile_id> --url https://example.com --headless

# 実行中プロファイルの停止
donut stop <profile_id>

# アンチディテクト・ワンクリック高速スクレイピング
donut scrape https://example.com
```

### 2.3 Python SDK & TUGUMIv6 モジュール
```python
# TUGUMIv6 内部からの利用
from tools.donut_tools import get_donut_manager

manager = get_donut_manager()

# 接続診断
health = manager.check_health()
print(health)

# プロファイル一覧
profiles = manager.list_profiles()

# アンチボット回避スクレイピング
result = manager.scrape_url("https://example.com")
print(result["text"])
```

---

## 3. 初期セットアップ手順（APIサーバーの有効化）

Donut Browser の Local REST API はセキュリティのためデフォルトで無効化されています。以下の手順で有効化してください：

1. **Donut Browser アプリ**をデスクトップ等で起動します。
2. アプリ右上の **[Settings]**（設定）→ **[Integrations]**（統合）→ **[Local API]** を開きます。
3. **[Enable Local API Server]** のトグルスイッチを ON にします。
4. 画面に表示される **ポート**（デフォルト: `10108`）と **認証トークン**（Bearer Token）を確認・コピーします。
5. Termux 側でトークンを登録します：
   ```bash
   donut config --token <コピーしたトークン>
   ```
   または環境変数に設定：
   ```bash
   export DONUT_API_TOKEN="<コピーしたトークン>"
   ```
6. `donut status` を実行し、`Connected Successfully!` が表示されれば準備完了です。

---

## 4. エージェント自律運用のベストプラクティス

1. **Cloudflare / Anti-Bot 対策**:
   通常の `curl` や `requests` でブロックされる高度な動的サイトに対しては、`donut_scrape(url=...)` を優先的に使用して Wayfern エンジン経由でコンテンツを取得する。
2. **ヘッドレスとGUIの使い分け**:
   バックグラウンドでの自律データ収集では `headless=True`、ユーザーが画面を目視確認したい場合は `headless=False` を指定する。
3. **プロファイルのリソース管理**:
   `donut_run_profile` で起動したプロファイルは作業完了後に必ず `donut_kill_profile` で終了し、端末リソースを解放する。
