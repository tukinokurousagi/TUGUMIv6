---
name: ai-idol-ip-producer
description: Termux上でAIアイドルIPの事業設計、Character DNA完全固定の清楚系・超リアル宣材写真生成、edge-tts音声＆VTT字幕合成、著作権フリーBGM生成、15秒ショート動画（MP4）3本合成、およびAmazon KDP完全準拠のKindleデジタル写真集（EPUB3 + PDF）出力までをコマンド一発で全自動化するスキル。
---

# AI Idol IP Producer (`tugumi-idol`)

## 概要
note記事『AIアイドル収益化の全知識』の事業フレームワークと、TUGUMIv6のマルチモーダル生成基盤（`GeminiImageStudio` / `edge-tts` / `ffmpeg` / `Pillow`）を完全統合した、Termux完結型のAIタレントIP＆Kindle写真集製造パイプラインです。

## 5段階＋Kindle写真集の自動製造フロー
- **Step 1 (`init`)**: 5つの事業設計メモ（ターゲット・欲求・媒体・商品・継続理由）、Character DNA 5大アンカー（21歳・清楚系ヒロイン「白石 凪」等）、および最初の15秒台本3本（①自己紹介・②商品紹介・③キャラらしい一言）をJSON出力。
- **Step 2 (`audit`)**: 年齢設定20歳以上、実在芸能人・既存IP非依存、AI明示ラベル、炎上NGワード排除の4大コンプライアンス監査を自動実行。
- **Step 3 (`build` - Visual)**: `GeminiImageStudio` (`gemini-3.1-flash-image`) を用い、左目下の泣きぼくろ等のDNAアンカーを固定した9:16縦長（`1080x1920`）の超高精細ポートレートを3シーン自動生成。
- **Step 4 (`build` - Audio & BGM)**: `edge-tts` (`ja-JP-NanamiNeural`) による自然な日本語ボイス＋VTT字幕生成と、100%著作権クリアの透明感アコースティックBGM（WAV）のローカル合成。
- **Step 5 (`build` - Video)**: `Pillow` ガラスモーフィズム日本語テロップ描画＋`ffmpeg` ズームパン演出・BGMミキシングにより、そのままTikTok/Reels/Shortsへ投稿できる15秒MP4動画を3本生成。
- **Step 6 (`kindle` - Kindle Photo Book)**: 生成した清楚系グラビア・ポートレート群から、表紙・扉絵・詩的キャプション付き本編・奥付（AI生成明示・権利表記）を備えた **Amazon KDP固定レイアウトEPUB 3.0 (`.epub`)** および **高解像度写真集 (`.pdf`, `1600x2560`)** を自動ビルド。

## コマンド使用方法

```bash
# 全工程（設計➔監査➔画像3枚➔音声➔BGM➔15秒動画3本➔Kindle写真集）を一発実行
tugumi-idol all --name nagi_shiraishi --style seiso

# Kindleデジタル写真集（EPUB3 + PDF）のみを再ビルド
tugumi-idol kindle --name nagi_shiraishi --style seiso

# 15秒ショート動画3本のみをビルド
tugumi-idol build --name nagi_shiraishi --style seiso
```

## 出力先ディレクトリ
- `/storage/emulated/0/TUGUMIDesk/副業・収益化/AIアイドル_<name>/`
  - `project_spec.json` / `事業設計＆台本シート.md`
  - `audit_report.json` (権利・安全監査レポート)
  - `images/scene_01.png` 〜 `scene_03.png` (9:16 清楚系宣材・日常カット)
  - `audio/voice_01.mp3` 〜 `voice_03.mp3` + `seiso_ambient_bgm.wav`
  - `videos/short_01_intro.mp4` 〜 `short_03_quote.mp4` (15秒ショート動画3本)
  - `Kindle写真集/<name>_Kindle写真集_清楚系グラビア.epub` & `.pdf`
