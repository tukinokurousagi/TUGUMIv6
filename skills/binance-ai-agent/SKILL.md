---
name: binance-ai-agent
description: バイナンス（Binance Japan）実口座の資産倍増自律運用、リアルタイムAI相場分析、3重防護パトロール（利確+25%/トレーリング+15%/損切-8%）、成行決済、TUGUMIDesk速報レポート連携を自然言語で統括する完全自律運用スキル
---

# Binance AI Autonomous Trader (バイナンスAI自律運用スキル)

拓磨様が「バイナンスの運用状況教えて」「今の資産・損益どう？」「倍増進捗見せて」「有望銘柄スキャンして」「自律パトロール回して」「SUIを利確して」「全ポジション決済して」「レポート出して」と指示された際に自動で起動し、Termux上の `binance-ai` エンジンおよび自律パトロールシステムを実行します。

## 🎯 運用の基本骨子（拓磨様専属 2x Doubling Mode）
- **初期軍資金**: ¥887.00
- **目標倍増金額**: ¥1,774.00 (2.00x)
- **3重プロテクション**:
  1. 通常スイング利確: `+25.0%`
  2. トレーリングストップ: `+15.0%` 追従開始、最高到達点から `-4.0%` 反落で自動利確（利益確保）
  3. 損切り防護ライン: `-8.0%`（元本保護）
- **過剰分散ガード**: 最大保有枠 5銘柄（超少額集中投資による最速倍増アプローチ）
- **超省電力アーキテクチャ**: 常駐ループを排した「Run & Terminate」（毎時0分に2秒で診断・約定・即終了、バッテリー消費ゼロ）

---

## 🛠️ 主な機能と実行コマンド

### 1. リアルタイム資産・損益HUD（スマホ画面最適化）
```bash
binance-ai status
```
- 現在の総資産、初期比損益率、倍増目標進捗（%）、保有銘柄ごとの取得単価/現在価格/損益率、cron稼働状態をカード形式で一発表示。

### 2. 倍増目標ダッシュボード & 即時パトロール
```bash
binance-ai target
```
- プログレスバー付き倍増進捗表示に加え、その場でリアルタイム相場スキャン＆自律パトロールを実行。

### 3. 次期倍増ターゲット銘柄 AIスキャン
```bash
binance-ai scan-2x
```
- 日本円（JPY）ペアの主要17銘柄を全自動スキャン。出来高、RSI、移動平均線、モメンタムからAIスコアを算出し、次に仕込むべき有望銘柄を特定。

### 4. ポジションの手動成行決済・緊急退避
```bash
# 特定銘柄の全量成行売却（日本円へ利確・退避）
binance-ai close SUI
binance-ai close PEPE

# 全保有ポジションの一括成行決済
binance-ai close --all
```

### 5. TUGUMIDesk レポート即時出力
```bash
binance-ai report
```
- `/storage/emulated/0/TUGUMIDesk/仮想通貨/BINANCE_LIVE_REPORT.md` を最新状態に即時更新・生成。

### 6. 自律パトロール（定期巡回）の管理
```bash
binance-ai cron status           # 巡回稼働状況の確認
binance-ai cron start --interval 1 # 1時間ごとの巡回開始
binance-ai cron stop             # 巡回の停止
binance-ai cron run              # 今すぐ1回手動パトロール実行
```

### 7. 特定銘柄の個別AI診断
```bash
binance-ai analyze BTC
binance-ai analyze SOL
```
