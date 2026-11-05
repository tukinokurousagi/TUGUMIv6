---
name: shizukuplus
description: "Shizuku+ (https://github.com/thejaustin/ShizukuPlus) を Termux 環境でフル活用するための専用スキル。特権シェル (rish)、Shizuku+ CLI (plus: aicore, storage, vm, am, wm, su, doctor)、SU Bridge (su) を介した Android システム・UI・プロセスの完全自動制御・診断プロトコル。"
---

# ShizukuPlus (Shizuku+) Termux 統合運用スキル

本スキルは、**Shizuku+ (ShizukuPlus)** の新機能を Termux から100%引き出し、Android 端末の高度な自動化・システム制御・ストレージ操作・UI自動化を行うための運用ガイドです。

---

## 🛠️ コマンド体系

### 1. 特権シェル: `rish` / `su`
- **対話シェル**: `rish` または `su`
- **コマンド実行**:
  ```bash
  rish -c "pm list packages"
  su -c "am start -n <package>/<activity>"
  ```
- **MagiskSU 互換チェック**:
  ```bash
  su -v   # 出力: 26.4:MAGISKSU
  su -V   # 出力: 26400
  ```

### 2. Shizuku+ CLI Helper: `plus`
Shizuku+ 固有の拡張 API を直接制御するコマンドラインツールです。

| コマンド | 説明 |
|---|---|
| `plus doctor` | システム診断（サーバーUID、SELinux、Plus機能有効状態、端末情報） |
| `plus aicore [touch\|swipe\|text\|dump\|pixel]` | AI 向け UI 自動化・階層ダンプ・画面ピクセル取得 |
| `plus storage [ls\|cat\|rm\|mkdir\|stat]` | 特権ストレージ管理 (`/data/app/`, `/Android/data/` 等) |
| `plus am [freeze\|unfreeze\|stop\|clear\|kill-all]` | ディーププロセス制御・アプリ凍結/解除 |
| `plus wm [immersive\|dex-high-refresh]` | ウィンドウ・表示設定の切り替え |
| `plus log` | サーバー側の特権アクティビティログ表示 |
| `plus spoof` | デバイス偽装状態の確認 |
| `plus su [command]` | SU Bridge 経由でのコマンド実行 |

---

## 🚀 内部構成・配置パス
- **DEX 実体 (Android 14+ 適合 / 読み取り専用 400)**:  
  `/data/data/com.termux/files/usr/share/shizuku/rish_shizuku.dex`
- **実行バイナリ**:
  - `/data/data/com.termux/files/usr/bin/rish` および `~/bin/rish`
  - `/data/data/com.termux/files/usr/bin/plus` および `~/bin/plus`
  - `~/bin/su` (SU Bridge ラッパー)
- **ソース / バックアップ保管場所**:
  `/storage/emulated/0/SHIZUKU/`
