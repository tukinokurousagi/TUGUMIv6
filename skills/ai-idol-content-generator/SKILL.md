---
name: ai-idol-content-generator
description: "清楚系AIアイドルの動画とKindle写真集を自動生成する."
version: 0.1.0
author: Hermes
category: AI・エージェント
created_at: 2026-10-29T16:36:38Z
---

# AI Idol Content Generator

清楚系AIアイドルのDNAアンカー固定、縦型ショート動画、およびKindle写真集用アセットの一括自動生成と出版用パッケージングを行う。

## When to Use
- 清楚系（黒髪・透明感・上品系）AIアイドルのキャラクターIPを構築・展開するとき
- TikTok/YouTube Shorts向けの9:16縦型音声付きショート動画を自動生成するとき
- Amazon KDP向けのKindleデジタル写真集パッケージ（EPUB/PDF組版）をワンストップで出力したいとき

## Prerequisites
- Python 3.10以上 (`edge-tts`, `Pillow`, `reportlab` 等が利用可能であること)
- FFmpeg (`ffmpeg`, `ffprobe`)
- 画像生成APIまたはローカル生成パイプライン

## How to Run
```bash
tugumi-idol all --name nagi_shiraishi --style seiso
```

## Quick Reference
- キャラクターDNA設定: `scripts/dna_profiles.json`
- CLIコマンド: `tugumi-idol {video|kindle|all} --name <id> --style {seiso|gal|casual}`
- 出力先: `/storage/emulated/0/TUGUMIDesk/副業・収益化/AIアイドル_<name>/`

## Procedure
1. キャラクターのDNAプロンプト（外見・表情・服装の固定プロンプト）を定義・検証する。
2. シナリオ構成（自己紹介・日常会話等）から音声（edge-tts）およびVTT字幕を生成する。
3. DNA固定プロンプトに基づき9:16比率のポートレートビジュアルを生成・キャッシュする。
4. FFmpegを用いて静止画・音声・字幕を合成し、15秒縦型MP4動画をレンダリングする。
5. 同一キャラクターのビジュアル群をKindle写真集仕様（表紙・目次・高解像度レイアウト）に自動組版する。

## Pitfalls
- `edge-tts` 実行時に環境変数やPATHが通っていない場合があるため、`sys.executable -m edge_tts` 形式で呼び出すこと。
- 画像生成APIを無駄に消費しないよう、生成済み画像が存在する場合はキャッシュを再利用すること。
- 清楚系モデルでは過度なメイクや露出を避け、一貫した光量と肌質プロンプトを固定すること。

## Verification
- `ffprobe` で出力MP4の解像度が1080x1920、音声コーデックがAAC、長さが適正であることを確認する。
- 写真集ディレクトリに対象画像と組版済みPDF/EPUBが生成されていることを確認する。
