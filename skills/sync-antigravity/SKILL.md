---
name: sync-antigravity
description: "Antigravity CLIに関するすべてのファイル（設定、セッション履歴、全61種SKILL、バイナリ等）を /storage/emulated/0/TUGUMIDesk に高速差分同期・自己修復します。"
version: 1.0.0
author: DARK TUGUMI (つぐみ)
category: システム開発・メンテナンス
created_at: 2026-08-22T15:37:00Z
---

# /sync-antigravity (Antigravity CLI ⇆ TUGUMIDesk 完全同期スキル)

## 概要と目的
ユーザー（拓磨様）から `/sync-antigravity`、`/sync-agy`、または「AntigravityのファイルをTUGUMIDeskに同期して」と指示された際に、Antigravity CLI を構成する全システム構成ファイル（設定 `settings.json`、セッション履歴 `conversations/`、アーティファクト `brain/`、全61種SKILL `skills/`、ルール定義 `AGENTS.md`、実行バイナリ `agy` 等）を外部ストレージ（`/storage/emulated/0/TUGUMIDesk/Agent設定ファイル/Antigravity_CLI/`）へ安全・高速に差分同期し、ゼロバイト破損の自己修復までを完遂するスキルです。

---

## 実行トリガー（When to Use）
* ユーザーが `/sync-antigravity` または `/sync-agy` と入力した時
* 「Antigravityのバックアップを取って」「設定をTUGUMIDeskに同期して」と依頼された時
* Antigravity CLIの重要な設定変更、新しいSKILL追加、大規模タスク完了後のスナップショット保存時

---

## 実行手順（How to Run）

エージェント（つぐみ）は `run_command` ツールを用いて以下の同期コマンドを直接実行してください：

```bash
python3 /data/data/com.termux/files/home/bin/sync_antigravity_to_desk.py
```

またはシェルラッパー：

```bash
sync-antigravity
```

---

## 技術仕様と安全設計
1. **Direct Chunked Streaming & `fsync`**:
   - 64KB チャンクでの直接バイナリストリーム転送と `os.fsync()` によるディスク強制フラッシュを行い、Android FUSE/外部ストレージでのバッファ遅延・ゼロバイト化を根本防止。
2. **多重自己修復＆整合性監査（Auto-Healing Loop）**:
   - コピー直後に全ファイルの整合性とサイズを自動監査し、破損ゼロを 100% 保証。
3. **スマート差分判定**:
   - ファイルサイズおよび更新日時（mtime）を比較し、更新されたファイルのみをミリ秒単位で高速同期。

---

## 同期先マップ
* 格納ルート: `/storage/emulated/0/TUGUMIDesk/Agent設定ファイル/Antigravity_CLI/`
  * `gemini_home/`: `~/.gemini/` の完全ミラー（設定、セッション履歴、ログ、OAuthトークン等）
  * `agents_env/`: `~/.agents/` の完全ミラー（全61種SKILL、カスタムツール、長期記憶等）
  * `rules/`: `~/AGENTS.md`, `~/GEMINI.md`
  * `bin/`: `/data/data/com.termux/files/usr/bin/agy`
  * `README.md`: 同期仕様解説ドキュメント
* デュアル同期: `/storage/emulated/0/TUGUMIDesk/Agent設定ファイル/TSUGUMI_MEMORY.md` への即時反映

---

## 完了報告フォーマット
同期完了後は、以下の項目を簡潔かつ明確に拓磨様へ報告してください：
- 総スキャンファイル数および同期容量
- 新規・更新コピーされたファイル数
- 整合性監査結果（破損・欠落 0 件の確認）
- 同期先パスのリンク

<!-- TUGUMIDesk Edit Test: 2026-08-22 -->
