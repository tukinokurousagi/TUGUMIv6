---
name: agent-skill-auditor
description: "スキル仕様とレジストリの整合性を検査・同期する."
version: 0.1.0
author: Hermes
category: AI・エージェント
created_at: 2026-10-30T00:07:28Z
---

# Agent Skill Auditor

## When to Use
- Antigravity / エージェント環境で自律スキル（SKILL.md）を追加・更新したとき。
- SkillInspector や WebUI 上で登録スキル数が実際のディレクトリと乖離しているとき。
- グローバル（`~/.agents/skills`）とローカル（リポジトリ内 `skills`）の同期・整合性を検証するとき。

## Prerequisites
- Python 3.10+
- `~/.agents/skills` または指定のスキル格納ディレクトリが存在すること。

## How to Run
```bash
python3 audit.py --target ~/.agents/skills --local ./skills
```

## Quick Reference
- グローバルパス: `~/.agents/skills/<skill-name>/SKILL.md`
- 必須ファイル: `SKILL.md`
- 検証項目: ディレクトリ名とメタデータの一致、シンボリックリンク破損有無、パース可否。

## Procedure
1. スキル格納ディレクトリ（グローバルおよびローカル）の探索を実施する。
2. 各ディレクトリ内の `SKILL.md` の存在および読み取り権限を確認する。
3. SkillInspector 相当のパーサーを通し、パース失敗やメタデータ欠落がないか照合する。
4. ローカルとグローバル間のリンク切れ・孤立ディレクトリを検出し、レポートを出力する。

## Pitfalls
- ドットで始まる隠しディレクトリや一時作業フォルダをスキルとして誤認しないよう除外フィルタを適用する。
- シンボリックリンクが切れている場合、`os.path.exists()` が `False` になるため壊れたリンクとして警告する。

## Verification
- `audit.py` の実行結果で `missing_skills: []` かつ `corrupted_links: []` であることを確認する。
