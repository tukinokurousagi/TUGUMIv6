# 2026 SOTA Autonomous AI Agent Specifications & Architecture Reference

本リファレンスは、知識カットオフによる認識的負債（Epistemic Debt）を排除し、2026年最新のAI技術・プロトコル・SDK仕様に基づいて商用クラスの自律型AIエージェントを設計・実装するための確定技術仕様書である。

---

## 1. 2026年 標準プロトコル2層モデル（Linux Foundation Agentic AI Foundation）

2026年中盤、乱立していたエージェント通信規格は Linux Foundation 傘下の **Agentic AI Foundation** のもとで以下のクリーンな**2層アーキテクチャ（垂直統合 × 水平統合）**に完全収束した（旧 IBM BeeAI の ACP は A2A へ吸収統合済み）。

### 🔹 Layer 1（垂直統合）: MCP 2.0 (`2026-07-28` Specification / Python SDK v2.x)
- **役割**: Agent ↔ Tool / Data / OS Resources 間の標準接続。
- **必須仕様（2026-07-28 Revision）**:
  - **Adaptive Protocol Negotiation**:
    - クライアント初期化時に `protocolVersion: "2026-07-28"` を提示し、サーバー応答に応じて `2026-07-28` ⇄ `2025-11-25` ⇄ `2024-11-05` を自動ネゴシエーション。
  - **Streamable HTTP & Stateless Core**:
    - HTTPヘッダー `Mcp-Protocol-Version: 2026-07-28` および `Mcp-Session-Id` によるステートレス/ストリーム通信。
  - **Extended Capabilities**:
    - `tasks`: `{"subscribe": True, "list": True, "cancel": True}` （長時間非同期タスクの生成 `start_task`・状態確認 `task_status`・中断 `cancel_task`）
    - `apps`: `{"render": True}` （MCP Apps UI コンポーネント描画）
    - `tools`: `{"listChanged": True}`
  - **Multi Round-Trip (`input_required`)**:
    - ツール実行中に追加情報やユーザー確認が必要な場合、`input_required` または `UrlElicitationRequiredError` を透過ハンドリング。
  - **Termux Ephemeral On-Demand 原則（常駐ゼロ）**:
    - モバイル/Termux環境ではMCPサーバーを常時起動放置せず、ツール呼び出し時のみミリ秒起動し、結果取得直後に `terminate()` でプロセスを完全消滅（待機RAM・バッテリー消費ゼロ）させる。

### 🔹 Layer 2（水平統合＆対人統合）: A2A Protocol (Agent-to-Agent Protocol)
- **役割**: Agent ↔ Agent 間のタスク委譲・協調、および Agent ↔ Human 間の承認・状態通知（旧ACPのスコープを包含）。
- **主要コンポーネント**:
  - **Agent Card (`/.well-known/agent.json`)**: エージェントの能力（Capabilities）、入出力スキーマ、認証要件、エンドポイントを公開するメタデータ。
  - **Task & Artifact Lifecycle**: 委譲されたサブタスクの状態遷移（`submitted` ➔ `working` ➔ `input-required` ➔ `completed` / `failed`）と成果物（Artifact）の構造化返却。
  - **Delegation Boundary（委譲境界）**: サブエージェントへ渡すコンテキストと権限スコープを最小限に分離し、メインエージェントのコンテキスト汚染を防ぐ。

---

## 2. 2026年 最新AI SDK ＆ モデルAPI実装仕様（実機検証済）

### 🔹 Google GenAI SDK (`google-genai` v2.25.0+)
- **⚠️ 絶対禁止（Deprecated）**: `import google.generativeai as genai` （旧パッケージは完全廃止。使用厳禁）
- **✅ 正規インポート＆初期化**:
  ```python
  from google import genai
  from google.genai import types

  client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
  ```
- **✅ Thinking（思考プロセス）＆ Safety 設定の正規パターン**:
  - `types.ThinkingConfig` の有効フィールド: `include_thoughts` (`bool`), `thinking_budget` (`int`), `thinking_level` (`"MINIMAL"` | `"LOW"` | `"MEDIUM"` | `"HIGH"`)
  ```python
  config = types.GenerateContentConfig(
      system_instruction="あなたは自律型AIエージェントです。",
      temperature=0.2,
      thinking_config=types.ThinkingConfig(
          include_thoughts=True,
          thinking_level="LOW",  # または MINIMAL / MEDIUM / HIGH / thinking_budget=1024
      ),
      safety_settings=[
          types.SafetySetting(
              category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
              threshold=types.HarmBlockThreshold.BLOCK_NONE,
          ),
          types.SafetySetting(
              category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
              threshold=types.HarmBlockThreshold.BLOCK_NONE,
          ),
          types.SafetySetting(
              category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
              threshold=types.HarmBlockThreshold.BLOCK_NONE,
          ),
          types.SafetySetting(
              category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
              threshold=types.HarmBlockThreshold.BLOCK_NONE,
          ),
      ],
  )
  response = client.models.generate_content(
      model="gemini-3.8-flash",  # または拓磨様指定モデル（gemma-4-31b-it 等）
      contents="タスク指示",
      config=config,
  )
  ```

### 🔹 Google Antigravity SDK (`google-antigravity` v0.1.20+)
- **✅ `LocalAgentConfig` の正規フィールド一覧（全26種・実機確認済）**:
  - `system_instructions`, `capabilities`, `tools`, `policies`, `hooks`, `triggers`, `mcp_servers`, `workspaces`, `conversation_id`, `session_continuation_mode`, `save_dir`, `app_data_dir`, `response_schema`, `skills_paths`, `subagents`, `debug_config`, `retry_config`, `budget_config`, `compaction_config`, `env`, `model`, `models`, `api_key`, `vertex`, `project`, `location`
- **✅ `ThinkingLevel` 列挙値**:
  - `MINIMAL`, `LOW`, `MEDIUM`, `HIGH`, `EXTRA_HIGH`
- **✅ 常駐セッション＆スキル自律認識・ハイブリッドMCP構成パターン**:
  ```python
  import google.antigravity as ag
  from google.antigravity.types import (
      LocalAgentConfig,
      CompactionConfig,
      McpStdioServer,
      McpStreamableHttpServer,
  )

  config = LocalAgentConfig(
      system_instructions="システムプロンプト",
      skills_paths=["/data/data/com.termux/files/home/.agents/skills"],
      save_dir="/data/data/com.termux/files/home/.tugumi/sessions",
      conversation_id="session_001",
      compaction_config=CompactionConfig(token_threshold=150000),
      mcp_servers=[
          McpStdioServer(name="failure_guard", command="python3", args=["server.py"]),
      ],
  )
  ```

### 🔹 4大商用エージェントSDKの特性と適材適所（2026 Landscape）
- **1. Google Antigravity SDK / Google ADK**
  - **強み**: 階層型マルチエージェント（Supervisor/Worker）、ネイティブ `skills_paths` 認識、`CompactionConfig` 自動文脈圧縮、A2A/MCPハイブリッド統合、Gemini 3系・マルチモーダルとの深い統合。
  - **最適用途**: Termux自律エージェント（TUGUMIv6）、長期間セッション維持、大規模ツール＆スキル統合。
- **2. Anthropic Claude Agent SDK（旧 Claude Code SDK）**
  - **強み**: OSレベル制御（Bash/File/Glob）、MCPネイティブ双方向通信、Hooks機構、Extended Thinking。
  - **最適用途**: 自律コーディング、OS直結型ローカル自動化。
- **3. OpenAI Agents SDK（旧 Swarm 進化版, v2.x）**
  - **強み**: 100種以上のモデル抽象化（Model-Agnostic）、宣言的 Handoff、Sandbox Agents（隔離実行環境）、Harness-Compute Separation（制御プレーンと実行環境の分離）、3層並列 Guardrails。
  - **最適用途**: 異種モデル混在（マルチモデル・ルーティング）やシンプルなハンドオフ連携。
- **4. LangGraph / Pydantic AI**
  - **強み**: 厳密な状態グラフ（StateGraph）、Send APIによる真の並列Fan-out/Fan-in、型安全な構造化入出力。
  - **最適用途**: 決定論的なDAGワークフローと厳格な監査が必要なパイプライン。

---

## 3. 本番マルチエージェント 6大オーケストレーション・トポロジー

2026年の研究（AdaptOrch / Google Agent Bake-Off）により、**「単一エージェントに全タスクを詰め込むとコンテキスト飽和と専門性希釈で崩壊する」「基盤モデルの差以上にオーケストレーション・トポロジーの選択が性能を12〜23%向上させ、処理時間を最大6分の1に短縮する」**ことが実証されている。

- **Pattern 1: Sequential Pipeline（直列パイプライン）**
  - 構造: `[Recon] ➔ [Analyze] ➔ [Implement] ➔ [Verify]`
  - 適用: ステップ間の依存関係が明確な定型エンジニアリングタスク。
- **Pattern 2: Parallel Fan-out / Fan-in（並列分散・集約）**
  - 構造: `Supervisor ➔ [Worker A || Worker B || Worker C] ➔ Synthesizer`
  - 適用: 多角的Webリサーチ、複数モジュール同時監査、競合仮説検証（全体レイテンシ＝最大ワーカー1つ分に短縮）。
- **Pattern 3: Hierarchical Supervisor-Worker（階層型監督・専門ワーカー）**
  - 構造: トップ監督者が意図解析とDAG分解を行い、専門ツールを持つワーカーへ委譲。
  - 適用: フルスタック開発、複雑なOS運用。
- **Pattern 4: Declarative Handoff（宣言的ハンドオフ）**
  - 構造: トリアージエージェントが専門エージェントへ制御権と最小コンテキストを直接移譲。
  - 適用: 日常タスク（レベルA）と高難度エンジニアリング（レベルB）の即座の切り替え。
- **Pattern 5: Evaluator-Optimizer / LLM-as-a-Judge Loop（批判的検証・自己改善ループ）**
  - 構造: `Generator ⇄ Critic/Judge (5層検証ゲート)`
  - 適用: コード生成後の構文・静的・動的テスト・回帰チェックと自律修復。
- **Pattern 6: Ephemeral Subagent Isolation（エフェメラル・サブエージェント隔離）**
  - 構造: 大量のログやWebページを読む調査を独立サブエージェントで実行し、蒸留された結論（数百トークン）のみを親へ返却。
  - 適用: メインコンテキストのトークン爆発防止（Context Engineering の Isolate 原則）。

---

## 4. Android Termux (Linux aarch64) 特化・自律エージェント実装の鉄則

- **パス規約の厳守**:
  - `/tmp` や `/usr/bin` のハードコードは禁止。必ず `os.environ.get("TMPDIR", "/data/data/com.termux/files/usr/tmp")` および `$PREFIX` を使用する。
- **SQLite 並行耐性の強制**:
  - 記憶DBや状態DBを開く際は、必ず接続直後に以下を実行して `database is locked` を根絶する：
    ```python
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=60000;")
    ```
- **非ブロッキング＆OSネイティブ優先**:
  - 待機処理でメインループを止めない。日常の端末操作（アラーム、通知、TTS、バッテリー確認）は Termux:API や Android Intent を1行で呼び出す。
- **ユーザー指定要件の100%絶対反映**:
  - マスター拓磨様から指定されたモデル名（例: `gemma-4-31b-it`, `gemini-3.8-flash` 等）、APIパラメータ（`BLOCK_NONE`, `thinking_level` 等）、フレームワーク要件は1文字も勝手に改変・省略せずコードへ忠実に実装する。
