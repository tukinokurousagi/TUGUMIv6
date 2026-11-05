# Antigravity SDK (v0.1.20+) Complete Specification & 2026 Self-Evolution Reference

本リファレンスは、最新のAIエージェント自己進化（Self-Evolving AI Agents）の研究知見と、Google公式 `google-antigravity` SDK の実機ソースコード検視結果を統合した確定技術仕様書である。

---

## 1. 2026年 自己進化型AIエージェント（Self-Evolving AI Agents）の5大技術基盤

2026年の最新研究（`arXiv:2605.13941 EvolveMem`, `arXiv:2508.07407 Comprehensive Survey of Self-Evolving AI Agents`, `AWM`, `Voyager`）において、自律型AIエージェントの自己進化は「モデルの重み更新」ではなく、**「非パラメトリック構成要素（SDK Harness / Memory / Tools / Skills / Context / Topology）の閉ループ自律最適化」**として定義される。

- **1. Harness & SDK Co-Evolution（SDKハーネス共進化）**:
  - インストールされているSDK（`google-antigravity`, `google-genai`, `mcp`）が提供する最新機能と、現在のエージェント実装コードとの差分（**Evolution Gap**）を継続的に監査し、未活用のネイティブ機能（自動Compaction、指数バックオフRetry、Hooks v2、出力Truncation等）を自律統合する。
- **2. EvolveMem（記憶と検索機構の2段階共進化）**:
  - 記憶データ（エピソード・事実）を蓄えるだけでなく、検索クエリ機構（SQLite FTS5 + 重要度スコア + 鮮度減衰）と2層分離（個人記憶 `tugumi_memory.db` ⇄ 社内共有ナレッジ `company_knowledge.db`）を共に進化させる。
- **3. AWM & Voyager Skill Synthesis（動的スキル・ツール合成）**:
  - 解決した高度なタスクの軌跡（Trajectory）を抽象化し、`SKILL.md` + `scripts/` + `references/` の3層構造を持つ再利用可能なスキルとして結晶化する。
- **4. Switch 2 Principle（機能劣化なき真のコンテキスト最適化）**:
  - コストやトークン削減のために思考力・ツール・出力品質を削る「3DS化（ダウングレード）」を絶対禁止とする。
  - 代わりに `CompactionConfig`（閾値到達時のロスレス自動要約）、`ToolOutputTruncationConfig`（暴走出力の安全切り詰め）、およびエフェメラル・オンデマンドMCPによって、**知能・網羅性を引き上げつつオーバーヘッドのみを極小化**する。
- **5. Closed-Loop Regression Gate（5層検証ゲートによる無劣化保証）**:
  - 自己進化によるコード・設定変更後は、必ず構文・AST監査・SDK仕様検証・E2E実機テスト（`Exit Code 0`）を通過させ、回帰（Regression）ゼロを客観的に実証する。

---

## 2. Google Antigravity SDK (`google-antigravity` v0.1.20+) 確定仕様

### 🔹 2.1 `LocalAgentConfig` 全26フィールド仕様（実機検視済）
`google.antigravity.LocalAgentConfig` に渡せる正規フィールド一覧：
- **コア指示・モデル系**:
  - `system_instructions`: `str | SystemInstructions | CustomSystemInstructions | TemplatedSystemInstructions`
  - `model`: `str | None`
  - `models`: `Sequence[ModelTarget] | None`
  - `api_key`: `str | None`
  - `vertex`: `bool | None`, `project`: `str | None`, `location`: `str | None`
  - `response_schema`: `Any | None`
- **能力・ツール・スキル・サブエージェント系**:
  - `capabilities`: `CapabilitiesConfig | None`
  - `tools`: `Sequence[Callable | PythonTool] | None`
  - `skills_paths`: `Sequence[str | Path] | None` （例: `["/data/data/com.termux/files/home/.agents/skills"]`）
  - `subagents`: `Sequence[SubagentConfig] | None`
  - `mcp_servers`: `Sequence[McpStdioServer | McpStreamableHttpServer] | None`
- **自律制御・フック・トリガー・ポリシー系**:
  - `policies`: `Sequence[DecideHook] | None` （例: `[policy.allow_all()]`）
  - `hooks`: `Sequence[Hook] | None` （Hooks v2 デコレータでラップした関数群）
  - `triggers`: `Sequence[Trigger] | None` （`triggers.every`, `triggers.on_file_change`）
- **セッション永続化・自己修復・コンテキスト管理系（自己進化の要）**:
  - `compaction_config`: `CompactionConfig | None` （例: `CompactionConfig(token_threshold=150000)`）
  - `retry_config`: `RetryConfig | None` （APIエラー・モデル出力エラーの自動リトライ）
  - `budget_config`: `BudgetConfig | None` （最大モデル呼出・ツール呼出・トークン上限）
  - `save_dir`: `str | Path | None` （セッション履歴の自動保存先ディレクトリ）
  - `conversation_id`: `str | None`
  - `session_continuation_mode`: `SessionContinuationMode | None` (`CREATE_ONLY`, `CREATE_OR_RESUME`, `RESUME`)
  - `workspaces`: `Sequence[str | Path] | None`
  - `app_data_dir`: `str | Path | None`
  - `env`: `Mapping[str, str] | None`
  - `debug_config`: `Any | None`

---

### 🔹 2.2 `CapabilitiesConfig` 全10フィールド仕様
```python
from google.antigravity.types import (
    CapabilitiesConfig,
    AgentBehavior,
    ToolOutputTruncationConfig,
)

capabilities = CapabilitiesConfig(
    enable_subagents=True,
    agent_behavior=AgentBehavior.AUTONOMOUS,
    allowed_subagents=["researcher", "code_craftsman", "sysops"],
    max_subagent_depth=2,
    compaction_threshold=150000,
    tool_output_truncation_config=ToolOutputTruncationConfig(max_tokens=16000),
)
```

---

### 🔹 2.3 `CompactionConfig` ＆ `RetryConfig` による自律耐久設計
```python
from google.antigravity.types import (
    CompactionConfig,
    RetryConfig,
    ModelAPIRetryConfig,
    ModelOutputRetryConfig,
)

compaction_config = CompactionConfig(token_threshold=150000)

retry_config = RetryConfig(
    api_retry=ModelAPIRetryConfig(
        max_retries=3,
        initial_sleep_duration_ms=1000,
        exponential_multiplier=2.0,
        jitter_range=0.2,
    ),
    model_output_retry=ModelOutputRetryConfig(
        max_retries=2,
    ),
)
```

---

### 🔹 2.4 Antigravity Hooks v2（全9種ライフサイクルフック）仕様
`from google.antigravity import hooks` で提供される公式デコレータ群。関数をデコレートするだけで `LocalAgentConfig(hooks=[...])` に直接登録できる：

- **1. `@hooks.pre_tool_call_decide`** (`DecideHook[types.ToolCall]`):
  - ツール実行前に発火。`types.HookResult(allow=True)` または `HookResult(allow=False, message="理由")` を返す。
- **2. `@hooks.post_tool_call`** (`InspectHook[types.ToolResult]`):
  - ツール実行直後に発火（非ブロッキング読取専用）。実行結果の監視・ロギングに使用。
- **3. `@hooks.on_tool_error`** (`TransformHook[Exception, Any]`):
  - ツールが例外を投げた際に発火。カスタムエラー文字列（自己修復のヒント付きメッセージ）を返すと、生スタックトレースの代わりにモデルへ伝達され、自律修復率が劇的に向上する。
  ```python
  @hooks.on_tool_error
  async def handle_tool_error(err: Exception) -> str:
      return f"[Tool Execution Error: {type(err).__name__}] {err} -> 第一原理に基づき引数・ファイルパス・権限を確認して別手段または修正パラメータで再試行してください。"
  ```
- **4. `@hooks.on_compaction`** (`InspectHook[types.Step]`):
  - コンテキスト自動圧縮（Compaction）が発生した際に発火。
- **5. `@hooks.on_session_start` / `@hooks.on_session_end`**:
  - セッション開始時・終了時に発火。
- **6. `@hooks.pre_turn` / `@hooks.post_turn`**:
  - 各ターンの開始前（`types.Content` 検査）・終了後（応答文字列検査）に発火。
- **7. `@hooks.stop`** (`TransformHook[types.StopArgs, types.StopHookResult]`):
  - エージェントがアイドル状態に達した際、終了するか継続するかを制御。

---

### 🔹 2.5 Antigravity Native Triggers 仕様
`from google.antigravity import triggers` で提供されるイベント駆動トリガー：
- **`triggers.every(interval_seconds, callback)`**:
  - 指定秒数ごとに非同期コールバック `async def cb(ctx: TriggerContext)` を実行。
- **`triggers.on_file_change(path, callback)`**:
  - 指定パス配下のファイル変更検知時に `async def cb(ctx: TriggerContext, changes: Sequence[FileChange])` を実行。
