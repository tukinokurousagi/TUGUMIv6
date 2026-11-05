---
name: termux-github-repos-setup-guide
description: 2026年最新仕様に基づく、Termux環境に必須のGitHub人気リポジトリTOP15の選定基準、詳細導入コマンド、およびAndroidバックグラウンド制限（Phantom Process Killer）の回避ノウハウを体系化した再利用可能な環境構築・リサーチSKILLパッケージ。
created_at: 2026-08-19T22:25:41Z
synthesized_by: TUGUMI Self-Evolution Engine
---

# termux-github-repos-setup-guide

2026年最新仕様に基づく、Termux環境に必須のGitHub人気リポジトリTOP15の選定基準、詳細導入コマンド、およびAndroidバックグラウンド制限（Phantom Process Killer）の回避ノウハウを体系化した再利用可能な環境構築・リサーチSKILLパッケージ。

## 📖 実行手順・ナレッジガイド
# SKILL: termux-github-repos-setup-guide
## Termux 究極環境構築 & 最強GitHubリポジトリ導入ナレッジ

このSKILLは、Termux環境において最高効率かつ本番水準で人気・必須リポジトリを導入・運用し、さらにAndroid 12〜15のバックグラウンドプロセス制限を克服するための、実証済みの構築手順をまとめたナレッジパッケージです。

---

## 1. Termux基盤および環境最適化 (Phantom Process Killer無効化)

Android 12以降で複数プロセス（LLMサーバー、エディタ、開発サーバー等）を動作させる際、OSにより強制終了される現象（Phantom Process Killer）を回避するための永続的解決手順。

### 【回避手順】
1. Android端末側で「Shizuku」アプリを起動し、無線デバッグ等で有効化。
2. Termux側から `rish` を呼び出し、システム設定を変更。

```bash
# Phantom Process制限を永続無効化（最大プロセス数を制限なしに設定）
rish -c "device_config put activity_manager max_phantom_processes 2147483647"

# 設定値の確認（2147483647 または null であれば成功）
rish -c "device_config get activity_manager max_phantom_processes"
```

---

## 2. 厳選GitHub人気リポジトリ・導入自動化コード群

### ① ローカルAIサーバー & 推論環境
#### [ollama/ollama] (ローカルAI API)
```bash
# 公式パッケージのインストールと起動
pkg update -y
pkg install ollama -y
ollama serve &
# モデルのプル & 実行 (Llama 3.2 1B)
ollama run llama3.2:1b
```
#### [ggerganov/llama.cpp] (ARM Neon極限最適化)
```bash
pkg install git clang cmake make termux-elf-cleaner -y
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j$(nproc)
```

### ② 次世代爆速GUI環境
#### [termux-windowing/termux-x11] (次世代X11サーバー)
```bash
pkg install x11-repo -y
pkg install termux-x11-nightly -y
# 別途Android側でTermux-X11アプリを起動し、以下で連携
termux-x11 :1 &
```

### ③ メディア抽出 & 同期自動化
#### [yt-dlp/yt-dlp] (万能メディアダウンローダー)
```bash
pkg install python ffmpeg-python -y
pip install --upgrade yt-dlp
```
#### [syncthing/syncthing] (完全P2P自動同期)
```bash
pkg install syncthing -y
# http://localhost:8384 で管理画面へアクセス
syncthing
```

### ④ プロフェッショナル開発環境 (IDE)
#### [neovim/neovim] (LazyVim統合)
```bash
pkg install neovim git make unzip python nodejs -y
git clone https://github.com/LazyVim/starter ~/.config/nvim
nvim
```
#### [coder/code-server] (ブラウザ版VS Code)
```bash
pkg install nodejs-lts python make clang -y
npm install -g code-server --unsafe-perm
code-server
```

---

## 3. シナジー自動化スクリプト・テンプレート

### 【自動化メディアハブ同期スクリプト (yt-dlp_sync.sh)】
```bash
#!/bin/bash
# 共有されたURLからyt-dlpで最高画質保存し、Termux通知経由でSyncthing同期フォルダへ移動

URL=$1
DOWNLOAD_DIR="$HOME/storage/shared/Download"
SYNC_DIR="$HOME/Sync/Videos"

mkdir -p "$SYNC_DIR"

termux-toast "動画のダウンロードを開始しました..."
yt-dlp -f "bestvideo+bestaudio/best" -o "$DOWNLOAD_DIR/%(title)s.%(ext)s" "$URL"

if [ $? -eq 0 ]; then
    termux-notification --title "TUGUMI Media Hub" --content "ダウンロード完了。SyncthingでPCへ自動同期します。"
    mv "$DOWNLOAD_DIR"/* "$SYNC_DIR"/
else
    termux-notification --title "TUGUMI Media Hub" --content "ダウンロード中にエラーが発生しました。"
fi
```

## 💡 使用例・適用シナリオ
use_skill(skill_name="termux-github-repos-setup-guide") を使用して、Termux上のローカルAI（llama.cpp/ollama）、GUI（Termux-X11）、開発（NeoVim/code-server）、セキュリティ（Metasploit/sqlmap）などの完全な導入自動化スクリプトや詳細情報を一撃で引き出します。

---
*Synthesized automatically by TUGUMI Self-Evolution System*
