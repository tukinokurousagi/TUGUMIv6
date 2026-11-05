---
name: mcp2-stateless-engine
description: MCP 2.0 (2026-07-28 Specification) 完全準拠ステートレス・マルチトランスポート＆拡張機能運用スキル。Stateless Core、HTTP-Nativeヘッダー、Multi Round-Trip(input_required)、Tasks Extension非同期タスク制御、MCP Apps UIコンポーネント描画を透過的に管理・実行する。
---

# MCP 2.0 完全運用スキル (mcp2-stateless-engine)

## 概要
2026年7月28日策定の「Model Context Protocol (MCP) 2.0 Specification」に完全準拠した運用手順書です。
TUGUMI-CLIv5 および TUGUMI-GPTv5 で、90種以上の外部MCPツール、非同期Tasks、MCP Apps UIをセッションレス・超高速・高信頼に運用します。

## 5大コア機能と利用方法

### 1. 完全ステートレスツール実行 (`call_mcp`)
```python
# 同期実行 (Stateless HTTP-Native / Stdio)
call_mcp(
    server_name="github",
    tool_name="list_issues",
    tool_args={"repo": "owner/repo"}
)
```

### 2. 非同期長時間タスク実行 (Tasks Extension)
```python
# バックグラウンドTaskとして開始
call_mcp(
    server_name="research",
    tool_name="deep_crawl",
    tool_args={"query": "2026 AI Trends"},
    mode="task"
)
```

### 3. Task 状態管理・進捗・中断 (`mcp2_task_control`)
```python
# 進捗確認
mcp2_task_control(action="status", task_id="task_12345678")

# タスク中断（Graceful Interruption連携）
mcp2_task_control(action="cancel", task_id="task_12345678")

# 一覧取得
mcp2_task_control(action="list")
```

### 4. MCP Apps UIコンポーネント描画 (`mcp2_render_app`)
```python
# WebUI (Bento Grid) 用のUIコンポーネント取得
mcp2_render_app(
    server_name="horse_racing",
    app_name="odds_matrix_view",
    app_args={"race_id": "2026090201"}
)
```

### 5. Multi Round-Trip (`input_required`)
ツールが追加引数や確認を求めた場合、自動的に `input_required` シグナルを受信し、ユーザー確認プロンプトを提示して安全に追加入力を処理します。
