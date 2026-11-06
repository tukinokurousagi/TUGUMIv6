# 小さな天使つぐみ (TUGUMIv6) - Autonomous Omni AI Agent Architecture

<p align="center">
  <img src="docs/assets/tsugumi_thum.png" alt="つぐみ (TUGUMI)" width="360" />
</p>

Android Termux (Linux aarch64) 環境に完全最適化された、自律型オムニAIエージェントフレームワーク。
Antigravity CLI / SWE Autonomous Agent 水準の認知アーキテクチャ、MCP 2.0 (Model Context Protocol) 統合、4層エビングハウス記憶システム、リアルタイムWebUI/CLI、そして多重安全防護を備えています。

---

## 🏛️ アーキテクチャ概要

```
TUGUMIv6/
├── core/                  # 自律実行・推論・オーケストレーション中核
│   ├── antigravity_sdk.py       # Google Antigravity SDK & MCP統合
│   ├── autoheal.py              # 構文・実行時エラーの自律修復エンジン
│   ├── briefing_engine.py       # 定期ブリーフィング生成
│   ├── capability_inspector.py  # 実行環境・依存関係の自己検査
│   ├── deep_research_engine.py  # 深層Webリサーチ
│   ├── dynamic_skill_synthesizer.py # 動的スキル合成
│   ├── engine_manager.py        # モデル・プロバイダー切替管理
│   ├── evolution_engine.py      # 自己進化・改善ループ
│   ├── gemini_client.py         # Google GenAI SDK (Gemini 3/4系)
│   ├── loop_guard.py            # 暴走・無限ループ遮断ガード
│   ├── reflection_engine.py     # 思考・内省エンジン
│   ├── subagents.py             # 専門サブエージェント管理
│   ├── supervisor.py            # タスク監視・オーケストレータ
│   ├── termux_doctor.py         # Termux環境診断・自己診断
│   └── verifier.py              # 5層検証ゲート
├── persona/               # 認知ペルソナ・コンテキスト
│   ├── soul.py                  # ペルソナ定義（Dual Persona）
│   └── context_compressor.py    # トークン節約・文脈圧縮
├── memory/                # 4層ハイブリッド記憶システム
│   ├── sqlite_memory.py         # SQLite FTS5 全文検索記憶
│   ├── rag_engine.py            # 3072次元ベクトルRAG検索
│   ├── learning_graph.py        # ナレッジグラフ＆学習リンク
│   ├── advanced_memory.py       # 忘却曲線連動記憶
│   └── desk_sync.py             # TUGUMIDesk成果物同期
├── tools/                 # 総合ツール武器庫（Arsenal）
│   ├── coding_tools.py          # 高速コード編集・リファクタリング
│   ├── research_tools.py        # 検索・論文・Wikipedia調査
│   ├── media_tools.py           # 楽曲・画像・メディア統合生成
│   ├── binance_tools.py         # 暗号資産トレード制御
│   ├── termux_tools.py          # Termux特有機能（API/通知/TTS）
│   ├── git_healer.py            # Git障害自動修復
│   ├── web_cloner.py            # Webサイト抽出・再構築
│   ├── donut_tools.py           # Donut Browser & ステルススクレイピング制御
│   ├── tugumi_defi_sniper.py    # DeFiアービトラージ監視ツール
│   └── tugumi_mcp.py            # MCP 2.0 ステートレス＆非同期タスクエンジン
├── passive_income/        # 自律型収益化・制作自動化パイプライン
│   ├── auto_media_engine.py     # メディア・動画・記事生成パイプライン
│   ├── freelance_automation.py  # 案件スコアリング・提案書・骨子生成
│   └── ai_idol_generator.py     # AIアイドルIP・宣材・EPUB3写真集生成
├── skills/                # 厳選61種専門SKILLパッケージ実体群
├── crypto_trader/         # 完全自律暗号資産運用エンジン
│   ├── analysis_engine.py       # マルチテクニカル・アルファ分析
│   ├── binance_client.py        # Binance API通信・署名
│   ├── live_executor.py         # リアルタイム注文・3重防護
│   ├── backtester.py            # 過去データバックテスト
│   └── trade_db.py              # 取引履歴・ポートフォリオ管理
├── interfaces/            # ユーザーインターフェース
│   ├── cli/                     # リッチサイバーパンクCLI (Rich/PromptToolkit)
│   └── web/                     # 高機能WebUI (FastAPI + SSE + Tailwind)
├── tests/                 # 堅牢なテストスイート (pytest)
│   ├── test_anti_downgrade_guard.py # ダウングレード防止ゲート
│   ├── test_mcp2_all_servers_e2e.py # 全MCPサーバーE2Eテスト
│   ├── test_webui_e2e.py            # WebUI E2Eテスト
│   └── ...
├── engine_config.json     # エンジン構成設定
├── start_cli.sh           # CLI起動スクリプト
└── start_webui.sh         # WebUI起動スクリプト
```

---

## 🚀 主な機能・特徴

1. **デュアル推論エンジン**:
   - Google Antigravity SDK (`LocalAgentConfig`) による最高峰エージェント推論
   - Google GenAI SDK (`google-genai`) 直結の高速フォールバック推論
2. **MCP 2.0 (Model Context Protocol) 統合**:
   - `failure_guard`, `github`, `horse_racing`, `playwright`, `research`, `robin`, `osint` 等の外部サーバーを透過的マウント
3. **4層エビングハウス記憶システム**:
   - 短期記憶、ワーキングメモリ、SQLite FTS5長期記憶、3072次元ベクトルRAG（Gemini Embedding）
4. **Termux / Android 特権連動**:
   - Shizuku+ 特権シェル連携、バッテリー・ストレージ診断、Termux API通知・メディアスキャン
5. **完全自律暗号資産運用 (Crypto Trader)**:
   - 3重安全防護（利確+25%/トレーリング+15%/損切-8%）、サーキットブレーカー搭載

---

## 🛠️ 起動方法

### CLIモード
```bash
cd ~/TUGUMIv6
./start_cli.sh
```

### WebUIモード (ポート 8086)
```bash
cd ~/TUGUMIv6
./start_webui.sh
# ブラウザで http://localhost:8086 にアクセス
```

### テストの実行
```bash
cd ~/TUGUMIv6
pytest tests/test_anti_downgrade_guard.py -v
```

---

## 🔒 セキュリティ・プライバシー
- APIキーやシークレットは環境変数（`GEMINI_API_KEY`, `BINANCE_API_KEY` 等）または `.env` 経由で注入されます。
- 実行ログ、SQLiteデータベース、ベクトルキャッシュは `.gitignore` によりバージョン管理から除外されています。
