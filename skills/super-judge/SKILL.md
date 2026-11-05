---
name: super-judge
description: 【最高峰LLM-as-a-Judge × 批判的評価 × 多角ディベート 統合判定マスター】コード、設計、出力成果物に対し、単一の甘い自己評価を排し、複数の専門的視点（セキュリティ、設計美学、堅牢性、Termux適合性）による厳格なLLM-as-a-Judge評価、批判的レビュー（Critique）、多視点ディベート合意形成、および競争型比較選定を一気通貫で実行する統合評価スキル。
---

# Super-Judge: 最高峰LLM-as-a-Judge & 多角ディベート統合検証プロトコル

## 1. 概要
`super-judge` は、従来の分散していた判定スキル（`judge`, `critique`, `do-and-judge`, `judge-with-debate`, `do-competitively`）を統合した最高峰の評価フレームワークです。
安易な自己満足や妥協（ハルシネーションの受容、表層的なパッチ）を100%排し、厳格な第三者評価基準で成果物を検証します。

## 2. 4大評価モード

### モード1: Single LLM-as-a-Judge (即時・厳格単一評価)
- **適用**: コード変更や小規模タスクの完了確認。
- **実行手順**:
  1. 事前定義された合格基準（Acceptance Criteria）とテスト実行結果（Exit Code 0）を照合。
  2. 5段階評価（機能完全性、エッジケース耐性、可読性、規律遵守、トークン効率）で採点。
  3. 減点箇所があれば即座に具体的な修正指示（Actionable Fix）を生成。

### モード2: Multi-Perspective Critique (多角批判レビュー)
- **適用**: アーキテクチャ設計、重要なリファクタリング、仕様決定。
- **3つの独立ペルソナ視点**:
  - **Security & Stability Judge**: 脆弱性、リソースリーク、異常系、Termux環境制約（aarch64/noexec）の検証。
  - **Architecture & Maintainability Judge**: 単一責任原則、疎結合、可読性、無駄なコードの排除。
  - **User Experience & Performance Judge**: 応答性、操作感、トークン消費の極小化。

### モード3: Multi-Round Debate (合意形成ディベート)
- **適用**: トレードオフのある重要な技術選定やバグの根本原因特定。
- 肯定派（Proponent）と批判派（Opponent）がエビデンス（実機テスト結果・ログ）を元に論戦を行い、Meta-Judge が客観的事実に基づき最終判定を下す。

### モード4: Competitive Synthesis (競争型生成・選定)
- 複数の実装アプローチ（A案・B案）を並行生成し、客観的ベンチマーク（実行速度、メモリ消費、保守性）で勝者を決定、最良要素を統合（Synthesis）。

## 3. 絶対評価基準（The Iron Criteria）
- **客観的エビデンスの必須性**: 実機での実行ログ・Exit Code 0 のない完了判定は無効（FAIL）。
- **ダウングレード（Switch 2→3DS化）の完全禁止**: 難度を理由にした機能削除は不合格。
- **Zero-Mock**: ハリボテやダミー実装は即座に差し戻し。
