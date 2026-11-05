---
name: rokujin-fortune-advisor
description: "六壬神課エンジンを用いて日々の全体運や指針を鑑定する."
version: 0.1.0
author: Hermes
category: ツール
created_at: 2026-10-29T07:36:33Z
---

# 六壬神課デイリー運勢アドバイザー

## When to Use
- ユーザーから毎日の運勢、全体運、意思決定の助言を求められた時
- 六壬神課（占事略决）に基づく課式（天地盤・四課三伝）と神将の配置から指針を導き出す時

## Prerequisites
- Python 3.8 以上
- `~/.agents/skills/senji-ryakketsu-rokujin/scripts/senji_advisor.py` または本スキルのヘルパースクリプト

## How to Run
```bash
python3 scripts/rokujin_eval.py "本日の全体運および仕事・健康・対人関係の指針"
```

## Quick Reference
- 全体運鑑定: `python3 scripts/rokujin_eval.py "マスターの今日の全体運"`
- 特定課題の意思決定: `python3 scripts/rokujin_eval.py "新機能リリースの吉凶と対策"`

## Procedure
1. ユーザーの意図と鑑定対象（今日全体の運勢、特定プロジェクト、対人関係など）を抽出する。
2. 占断実行スクリプトに鑑定クエリを引数として渡し、六壬神課の課式（干支・三伝・十二天将）を算出する。
3. 出力された課式構造（初伝・中伝・末伝、十二神将の吉凶、旺相休囚死）を解析する。
4. 運勢の結論だけでなく、具体的かつ前向きな行動指針（吉を活かし凶を避ける策）をまとめて報告する。

## Pitfalls
- 抽象的な吉凶のみを伝えると実務に役立たないため、行動可能なアクションプランに落とし込む。
- 月将と占時の算定が正確に行われているか確認する。

## Verification
- スクリプトがリターンコード0で課式結果（三伝、四課、天将配置）を出力すること。
- 鑑定結果に行動指針と注意点が明瞭に含まれていること。
