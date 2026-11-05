---
name: agent-craftsman
description: 【エージェント・スキル・カスタム拡張 統合開発マスター】Claude Code および Antigravity におけるカスタムエージェント（Agent）、スキル（Skill）、スラッシュコマンド（Command）、Git/実行フック（Hook）、行動ルール（Rule）の設計・開発・テスト・最適化を一気通貫で完遂する統合エンジニアリングスキル。Anthropic/Google公式ベストプラクティスおよび厳格なTDD（テスト駆動プロンプト工学）に完全準拠。
---

# Agent Craftsman: エージェント＆カスタム拡張 統合開発マニュアル

## 1. 概要
`agent-craftsman` は、旧来乱立していた拡張開発系スキル（`create-skill`, `writing-skills`, `create-agent`, `create-command`, `create-hook`, `create-rule`, `create-workflow-command`, `apply-anthropic-skill-best-practices`, `skill-creator`, `test-skill`, `test-prompt`）を1つに統合した決定版スキルです。

Claude Code（`~/.claude/`）および Antigravity（`~/.gemini/` / `.agents/`）の規格に完全適合した拡張機能を自律開発します。

---

## 2. 制作カテゴリと標準仕様

### ① Skill（スキル）作成
- **配置**: `skills/<skill-name>/SKILL.md`
- **フロントマター必須要素**:
  ```yaml
  ---
  name: <kebab-case-name>
  description: <発動トリガーとなる具体的キーワード・状況と提供価値を明記した説明文>
  ---
  ```
- **設計指針**:
  - Progressive Disclosure（段階的開示）に対応し、概要説明文は200〜300文字程度で的確に記述。
  - 手順は具体的かつ再現可能なステップ、検証コマンド、エッジケース対応を含める。

### ② Agent（カスタムサブエージェント）作成
- **仕様**: システムプロンプト、許可ツールセット、実行モデル（inherit/flash/pro）、動作コンテキストの定義。
- **設計指針**: 単一責任の原則を保ち、明確な入出力スキーマと自己終了条件を定義。

### ③ Slash Command（コマンド）＆ Workflow Command
- **仕様**: ユーザーが `/command-name` で呼び出すショートカット手順の定義。
- **設計指針**: 複雑な反復作業（レビュー、Gitコミット、デプロイ検証等）を1発で実行可能にする。

### ④ Hook（フック）＆ Rule（ルール）作成
- **Hook**: ツール実行前（pre-tool）や終了時（post-run）に自動実行される安全検証スクリプト。
- **Rule**: `AGENTS.md` / `GEMINI.md` / `rules/*.md` に記述される恒久行動制約。

---

## 3. TDD式 プロンプト＆スキル検証サイクル（Red-Green-Refactor）
1. **Red（ベースライン測定）**: スキル/プロンプト適用前にモデルが失敗するタスク（エッジケース・ハルシネーション例）を定義。
2. **Green（実装と検証）**: スキルを適用してタスクを実行し、期待通りの出力・ツール呼び出しが行われることを実証。
3. **Refactor（トークン最適化）**: 冗長な表現を削ぎ落とし、最短トークンで最大の推論精度を叩き出すよう文面を研ぎ澄ます。
