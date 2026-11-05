---
name: obsidian-vault-architect
description: Obsidianの「第2の脳（Second Brain）」構築・運用に特化したナレッジ管理スキル。TUGUMIDesk（TUGUMI DatabaseやWiki）内のVaultに対して、双方向リンク・Propertiesメタデータ付きのノート自動生成、MOC（目次・ハブ）自動更新、Dataview用クエリ設計、Vault健全性監査を実行する。
---

# Obsidian Vault Architect (SKILL)

本スキルは、拓磨様のローカルナレッジ要塞（`/storage/emulated/0/TUGUMIDesk/TUGUMI Database/` 等）を最高峰の知的生産環境へと進化させるための専門スキルです。

---

## 1. コア原則（Zero-Defect Obsidian Directive）

1. **YAML Frontmatter (Properties) 必須付与**:
   すべての新規ノートには、ObsidianのPropertiesで認識可能なフロントマターを先頭に付与すること。
   ```yaml
   ---
   title: "ノートタイトル"
   tags: [タグ1, タグ2]
   aliases: [別名1, 別名2]
   created: YYYY-MM-DD
   updated: YYYY-MM-DD
   author: "つぐみ (TUGUMI)"
   ---
   ```
2. **有機的双方向リンク（`[[]]`）の自動埋め込み**:
   - 本文中に登場する重要キーワード、関連技術、人物名、競走馬名、楽曲名を自律検知し、`[[関連ノート名]]` または `[[正式名|表示名]]` でリンク化すること。
   - ノート末尾には必ず「関連ノート」セクションを設け、親MOC（例: `[[00_TUGUMI_Core_Dashboard]]`）への戻りリンクを結ぶこと。
3. **視覚的ダイアグラム（Mermaid）の標準搭載**:
   - 概念の全体像、因果関係、タイムライン、フローチャートを Mermaid コードブロック（`mindmap`, `graph TD`, `flowchart LR`, `sequenceDiagram` 等）で視覚化すること。
4. **Dataview プラグイン対応設計**:
   - リストやテーブルを自動集計できるように、タグ（`#AI`, `#競馬` 等）やメタデータキー（`race_date`, `center`, `bpm` 等）を統一して設計すること。

---

## 2. 実行可能な主要タスクとコマンド

### ① 新規Wiki・ナレッジノートの自動生成
拓磨様から調査やWiki作成の指示を受けた際、上記「コア原則」に完全準拠したMarkdownファイルを Vault 内の適切なサブフォルダへ保存する。

### ② Vault 健全性監査（リンク切れ・孤立ノート検知）
付属のスクリプトを実行して、リンク切れや孤立ノートを即座に診断・修復する。
```bash
python3 ~/.agents/skills/obsidian-vault-architect/scripts/obsidian_vault_tool.py audit
```

### ③ MOC（Map of Content / 目次）自動更新
Vault内の全ノートを走査し、最新のカテゴリ別インデックスとDataviewダッシュボードを再生成する。
```bash
python3 ~/.agents/skills/obsidian-vault-architect/scripts/obsidian_vault_tool.py moc
```

### ④ リンク切れ自律修復（Auto-Heal / 完全結合）
未実体化リンク（Broken Links）を自律検知し、構造化スタブ・ハブノート（Properties・Mermaid・Dataview・関連リンク完備）を一括生成してグラフを完全結合する。
```bash
python3 ~/.agents/skills/obsidian-vault-architect/scripts/obsidian_vault_tool.py heal
```

---

## 3. 推奨フォルダ構造

```text
/storage/emulated/0/TUGUMIDesk/TUGUMI Database/
├── 00_TUGUMI_Core_Dashboard.md  # 総合ダッシュボード (MOC)
├── 00_TUGUMI_Auto_MOC.md        # 自動生成MOC
├── AI・システム開発/            # 技術・LLM・アーキテクチャ
│   └── Skills/                  # 自律開発スキル公式ノート
├── 推し活・エンタメ/            # アイドル（井上和様等）・楽曲・イベント
├── 競馬・データ分析/            # 重賞予想・血統・コース分析
├── デイリー・活動記録/          # 日報・気象・日次タスク
├── Wiki/                        # システム知見・運用ナレッジ
│   └── Categories/              # カテゴリ別インデックスハブ
└── Inbox/                       # 拓磨様の思いつきメモ・タスク投入口
```

---
*Created by つぐみ (TUGUMI) - Dedicated to 拓磨様*
