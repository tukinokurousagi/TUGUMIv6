---
name: webapp-testing
description: "【WebUI × API × Playwright × ヘッドレス実機検証 統合マスター】Playwright MCP / ヘッドレス Chromium を駆使し、ローカルWebサーバーの自動起動・停止ライフサイクル（with_server.py）、DOMレンダリング、ボタン・フォーム・イベント発火、トースト通知、ブラウザコンソールエラー（console.error）および 4xx/5xx 通信エラーの監視までを一気通貫で自動検証するWebアプリケーション専門テストスキル。"
created_at: 2026-08-29T06:08:00Z
author: つぐみ (TUGUMI Web QA System)
---

# WebApp Testing & Browser Automation Master
## WebUI × API × Playwright ヘッドレス実機自動検証 統合マスター

本スキルは、Web アプリケーション開発において、**「ローカルサーバーを自動起動し、Playwright（ヘッドレス Chromium）で実際に画面を操作・クリック・検証し、コンソールエラーや通信落ちがないことを実機証明する」** E2E 自動テストフレームワークです。

---

## 🚀 第1部：ローカルサーバー自動ライフサイクル管理 (`with_server.py`)

テスト実行時に手動でサーバーを立ち上げる必要はなく、付属の `scripts/with_server.py` スクリプトで自動起動・ヘルスチェック・安全終了を実行する。

```bash
# 使用構文
python3 ~/.agents/skills/webapp-testing/scripts/with_server.py --server "<サーバー起動コマンド>" --port <ポート番号> -- <テスト実行コマンド>

# 実践例（FastAPI / Flask アプリの Playwright テスト）
python3 ~/.agents/skills/webapp-testing/scripts/with_server.py --server "python3 app.py" --port 8080 -- python3 test_ui_e2e.py
```

### ライフサイクル動作仕様
1. **サーバー起動**: 指定されたコマンド（`app.py` や `npm start`）をバックグラウンド子プロセスとして起動。
2. **ポート導通ヘルスチェック**: 指定ポートが開放され、HTTP 200/OK を返すまで待機（タイムアウトガード付き）。
3. **テストスイート実行**: サーバー稼働を確認後、テストコマンド（Playwright テスト等）を実行。
4. **確実なプロセス終了**: テストの成功・失敗を問わず、サーバープロセスおよび関連子プロセスを `SIGTERM` / `SIGKILL` で完全に停止し、ポートを解放。

---

## 🌐 第2部：Playwright / ヘッドレス Chromium による実機検証プロトコル

Playwright MCP（`playwright_scrape`）または Python Playwright スクリプトを用いて、以下の4大領域を実機検証する。

```
┌────────────────────────────────────────────────────────┐
│ 👁️ 1. DOM Rendering & Semantic Elements                │
│    主要要素(ID/Class/Aria), テキスト, レイアウト崩れなし │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────┴─────────────────────────────┐
│ 🖱️ 2. User Interactions & Events                       │
│    ボタンクリック, フォーム入力, モーダル開閉, タブ切り替え │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────┴─────────────────────────────┐
│ 📡 3. Network & API Request Verification                │
│    Fetch/SSE/WebSocket通信, 200 OKレスポンス, トースト通知│
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────┴─────────────────────────────┐
│ 🚨 4. Console Errors & Network Failure Monitoring      │
│    console.error ゼロ, 404/500 エラーゼロの完全保証     │
└────────────────────────────────────────────────────────┘
```

### 1. 必須検証アサーション
- **コンソールエラー監視**: ページロード中および操作中に JavaScript の未補足例外（`TypeError`, `ReferenceError` 等）が1件も発生していないこと。
- **トースト・通知の出現**: API 通信成功時に「保存しました」「送信完了」等のトースト通知要素が DOM 上に正しくレンダリングされること。
- **ローディング＆エラー復帰**: 処理中のスピナー表示と、ネットワーク遅延時のタイムアウト・安全なエラー表示。

---

## 📋 第3部：WebUI E2E テスト結果レポート

```markdown
# 🌐 WebApp E2E 自動検証レポート

## 1. 検証対象＆テスト環境 (Test Environment)
- **対象URL**: `http://localhost:8080`
- **駆動ブラウザ**: Chromium (Headless / ARM64 Termux Optimized)
- **実行スクリプト**: `tests/test_e2e.py` (via `with_server.py`)

## 2. 実機検証ログ (Verification Evidence)
```
[Server] Starting 'python3 app.py' on port 8080...
[Server] Port 8080 is READY (HTTP 200 OK).
[Test] Navigating to http://localhost:8080...
[Test] Form input: title="Test Post", content="Automated Content"
[Test] Click 'Submit' button -> API POST /api/post (200 OK)
[Test] Verified Toast notification: "Successfully Published"
[Test] Console Error Count: 0
[Test] Network 4xx/5xx Count: 0
[Server] Shutting down server (PID: 12345)... Server stopped.
============================== 1 passed in 1.82s ==============================
```

## 3. 判定 (Verdict)
- **判定**: **✅ 合格 (Zero-Mock Verified)**
- **証明**: DOM・イベント・API・トースト通知・コンソール正常性が実機で完全実証されました。
```

---
*Synthesized and Enhanced by TUGUMI Web QA System*
