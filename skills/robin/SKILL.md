---
name: robin
description: "AI-Powered Dark Web OSINT Intelligence Suite。Torネットワーク経由で16基のオニオン検索エンジンを横断探索し、生データを安全にスクレイピングしてGemini 3.8 Flashによる高度な脅威インテリジェンスレポートを生成・TUGUMIDeskへ自動保存します。トリガー: /robin, ダークウェブ調査, オニオン検索, ダークウェブで調べて, ダークウェブ, Robinで検索"
---

# 🦅 Robin Dark Web OSINT Intelligence Skill

本スキルは、Tor ネットワーク上のダークウェブ（.onion サイト）を調査・分析し、チャット画面上に構造化された脅威インテリジェンスレポートを即座に提示するための自律型 OSINT スキルです。

ブラウザの起動や別ターミナルへの切り替えを行わず、**チャット入力欄で `/robin <キーワード>` と入力するだけで完全自律調査**を完遂します。

---

## 1. 調査フローと手順

拓磨様から `/robin <クエリ>` またはダークウェブ調査の指示を受けた際、つぐみは以下の手順を完全自律で実行します：

### ステップ 1: ヘルスチェックと Tor 起動確認
- MCP ツール `robin_health` を呼び出し、Tor プロキシが稼働しているか確認する。
- もし Tor が未起動（down）の場合は、`run_command` で `tor > /dev/null 2>&1 &` を実行して自動起動する。

### ステップ 2: 調査ドメイン（プリセット）の自動判定
ユーザーのクエリから最適なドメインプリセットを判定する（指定がない場合は `threat_intel`）：
- `threat_intel`: 一般的なサイバー犯罪・脅威インテリジェンス・漏洩情報（デフォルト）
- `ransomware_malware`: ランサムウェア組織、リークブログ動向、マルウェア検体、C2インフラ
- `personal_identity`: 個人情報流出、漏洩データベース、アカウント露出
- `corporate_espionage`: 企業機密漏洩、インサイダー活動、ソースコード流出

### ステップ 3: 調査の実行（MCP ツール駆動）
- MCP ツール `robin_investigate` を呼び出す：
  - `query`: 拓磨様から指定された調査キーワード
  - `preset`: 判定したドメインキー
  - `user_chose`: `true`
  - `model`: `gemini-3.8-flash`
  - `max_results`: `100`（または適切な件数）
  - `max_scrape`: `20`
- 16 基のオニオン検索エンジン探索 ➔ フィルタリング ➔ Tor スクレイピング ➔ インテリジェンス構造化が自動的に完了する。

### ステップ 4: レポートの TUGUMIDesk 自動保存
- 調査結果を `/storage/emulated/0/TUGUMIDesk/裏話リサーチ/YYYYMMDD_Robin_OSINT_<クエリ>.md` に自動保存する。
- 内部バックアップ（`~/robin/investigations/`）にも記録される。

### ステップ 5: チャット上へのリッチ報告
以下の構造化フォーマットで、拓磨様にわかりやすく明瞭に報告する：
1. **調査概要**: 検索ヒット件数、読破したオニオンサイト数、調査ステータス
2. **主要インテリジェンス・サマリー (Findings)**:
   - 脅威アクター / 組織
   - 漏洩データ / マルウェア検体
   - 暗号資産ウォレットアドレス（BTC, XMR等）
   - オニオンインフラ（.onion アドレス一覧）
3. **参照オニオンソース一覧**: ページタイトルと .onion URL
4. **推奨ネクストアクション / 探索ピボット (Pivots)**
5. **保存先ファイルリンク**: TUGUMIDesk の Markdown パス

---

## 2. 実行コマンド例

- `/robin LockBit ransomware decryptor leak`
- `/robin dark AI LLM forum`
- `/robin 企業機密漏洩データベース`
- `/robin 暗号資産ウォレット 不正送金`
