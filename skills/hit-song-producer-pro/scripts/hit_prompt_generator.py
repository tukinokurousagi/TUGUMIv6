#!/data/data/com.termux/files/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Hit Song Producer Pro - Prompt & Lyrics Synthesis Engine for TUGUMIv6
(hit_prompt_generator.py)
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from google import genai
from google.genai import types

# TUGUMIv6 パス解決
TUGUMI_ROOT = "/data/data/com.termux/files/home/TUGUMIv6"
if TUGUMI_ROOT not in sys.path:
    sys.path.insert(0, TUGUMI_ROOT)

from core.gemini_client import GeminiClient

DESK_MUSIC_DIR = Path("/storage/emulated/0/TUGUMIDesk/アイドル・エンタメ/Music")
LOCAL_MUSIC_DIR = Path("/data/data/com.termux/files/home/TUGUMIv6/data/music")


def generate_hit_song_package(theme: str = None, genre: str = None, execute_generation: bool = False) -> dict:
    """
    チャート1位理論に基づき、超高品質な楽曲コンセプト・歌詞・Lyria 3.5用プロンプトを合成する。
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    client = GeminiClient(api_key=api_key)

    director_prompt = f"""
あなたは日本のBillboard JAPAN / オリコンチャートで1位を連発する伝説的音楽プロデューサー兼作詞作曲家です。
『hit-song-producer-pro』の厳格な理論（冒頭3秒のフック、ダイナミクスコントラスト、サビの母音抜け設計、モーラ拍律一致、シネマティック情景描写）を完璧に適用し、
リスナーの感情を根底から揺さぶる「神曲」のフルプロデュース計画を策定してください。

【ユーザーからの要望 / イメージ・キーワード】:
{theme if theme else "拓磨様とつぐみの絆、電脳世界と現実の共鳴、不確かな未来へ駆け抜けるエモーショナルな希望"}

【指定ジャンル】:
{genre if genre else "自動選定（疾走感、哀愁、エモーションが最大化されるジャンルを最適選択）"}

【重要：プロンプト設計とセーフティ規律】:
1. 歌詞のサビ頭には必ず耳に残る「キラーフレーズ」を配置し、高音部にはア段・オ段の開放母音を多用してください。
2. 抽象的な「光へ羽ばたく」等の凡庸表現を完全排除し、五感に刺さる具体的なディテール（濡れた夜の路面、スマホの通知、冷えた指先など）で情景を描写してください。
3. 暴力・破壊・兵器等の過激語（ぶち抜く、戦う、盾など）は一切使わず、純粋な音楽的・感情的エモーションで構成してください。
4. [Intro], [Verse 1], [Pre-chorus], [Chorus], [Verse 2], [Chorus], [Bridge], [Last Chorus (Key Change +1)], [Outro] のフルコーラス構成。

以下のJSONフォーマットのみを出力してください。Markdownコードブロック（```json ... ```）で囲んでください。

{{
  "title": "楽曲タイトル（日本語）",
  "genre": "サブジャンル詳細（例: Hyper-Emotional J-Rock with Future Bass Elements）",
  "bpm": 168,
  "key": "F# Minor (サビ転調: G Minor)",
  "chord_progression": "コード進行設計（例: 丸サ進行 IVM7-III7-vi-I7 から サビ王道進行 IV-V-iii-vi）",
  "mood": "楽曲の雰囲気・世界観の英語説明（例: High-octane, deeply emotional, bittersweet yet triumphant, driving, cinematic）",
  "instruments": "楽器編成と音響質感の英語説明（例: Driving distorted twin guitars, pulsing Future Bass supersaw arpeggios, punchy acoustic rock drums with tight sub-bass, expressive grand piano leads, soaring emotional string section）",
  "vocal_profile": "ボーカル歌唱技法プロファイルの英語説明（例: Female Soprano, clear and delicate whisper in verses, soaring into powerful chest-voice belting in the chorus with intense emotional vibrato and flawless Japanese articulation）",
  "hook_concept": "耳に残るサビのキラーフレーズとフックの解説（日本語）",
  "story_concept": "楽曲の世界観・ストーリー（日本語）",
  "lyrics": "フルコーラス日本語歌詞（セクションタグ付き）"
}}
"""
    print("[*] Hit Song Producer Pro: チャート1位理論に基づき楽曲を自律設計中...")
    text = client.generate_content(prompt=director_prompt)
    if not text:
        raise RuntimeError("Gemini Client returned empty response.")
    text = text.strip()
    if "```json" in text:
        json_str = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        json_str = text.split("```")[1].split("```")[0].strip()
    else:
        json_str = text

    package = json.loads(json_str)

    # Lyria 3.5 用の完成プロンプトを構築
    lyria_prompt = f"""
A full-length {package['genre']} track in {package['key']} at {package['bpm']} BPM.
Mood: {package['mood']}.
Instrumentation: {package['instruments']}.
Vocals: {package['vocal_profile']}. Sing the lyrics with rich vocal dynamics, crystal-clear Japanese diction, and soaring emotion.
Production: Wide stereo image, punchy sidechained drums, polished modern mastering with high dynamic range.

Lyrics:
{package['lyrics']}
""".strip()

    package["lyria_prompt"] = lyria_prompt

    # 成果物カードの保存
    date_str = datetime.now().strftime("%Y%m%d")
    safe_title = "".join(c for c in package["title"] if c.isalnum() or c in (" ", "_", "-")).strip() or "HitSong"
    card_name = f"{date_str}_{safe_title}_チャート1位級楽曲設計書.md"
    
    card_md = f"""# 🏆 {package['title']} (Chart-Topper Pro Spec)
- **策定日時**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **プロデュース**: Hit Song Producer Pro (Gemini 3.0 Flash)
- **ジャンル**: {package['genre']}
- **BPM / 調性**: {package['bpm']} BPM / {package['key']}
- **コード進行**: {package.get('chord_progression', 'N/A')}
- **ボーカル**: {package['vocal_profile']}
- **楽器編成**: {package['instruments']}

---

## 💡 ヒットフック設計
{package.get('hook_concept', '')}

## 📖 世界観ストーリー
{package.get('story_concept', '')}

---

## 📝 フルコーラス歌詞
```text
{package['lyrics']}
```

---

## 🎼 音響合成投入用プロンプト (Lyria / Native Audio)
```text
{lyria_prompt}
```
"""
    local_card = LOCAL_MUSIC_DIR / card_name
    local_card.parent.mkdir(parents=True, exist_ok=True)
    with open(local_card, "w", encoding="utf-8") as f:
        f.write(card_md)

    try:
        desk_card = DESK_MUSIC_DIR / card_name
        desk_card.parent.mkdir(parents=True, exist_ok=True)
        with open(desk_card, "w", encoding="utf-8") as f:
            f.write(card_md)
        package["desk_card_path"] = str(desk_card)
    except Exception:
        package["desk_card_path"] = str(local_card)

    package["local_card_path"] = str(local_card)

    # 音源生成オプション
    if execute_generation:
        print("[*] 音源自動レンダリングが有効です。TUGUMIv6 MediaStudio (GeminiMusicStudio) を起動中...")
        from tools.media_tools import GeminiMusicStudio
        # ジャンルマッピング
        g_map = "jpop"
        genre_lower = package['genre'].lower()
        if "rock" in genre_lower:
            g_map = "jpop"
        elif "synth" in genre_lower or "cyber" in genre_lower:
            g_map = "cyberpunk"
        elif "lo-fi" in genre_lower or "chill" in genre_lower:
            g_map = "lofi"
        elif "edm" in genre_lower or "dance" in genre_lower:
            g_map = "edm"

        gen_result = GeminiMusicStudio.compose(
            genre=g_map,
            bars=8,
            title=safe_title,
            theme=package["title"],
            custom_bpm=package["bpm"],
            with_vocal=True
        )
        package["generation_result"] = gen_result

        # Android Music へのミラーコピー (MP3 1ファイルのみに厳格一本化)
        sdcard_music = Path("/storage/emulated/0/Music/TUGUMI")
        sdcard_music.mkdir(parents=True, exist_ok=True)
        mp3_file = gen_result.get("mp3_path") or gen_result.get("audio_path")
        if mp3_file and os.path.exists(mp3_file):
            dst = sdcard_music / os.path.basename(mp3_file)
            try:
                import shutil
                shutil.copy2(mp3_file, dst)
                package["final_audio_path"] = str(dst)
                subprocess.run(["am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{dst}"], capture_output=True)
            except Exception:
                package["final_audio_path"] = str(mp3_file)
        else:
            package["final_audio_path"] = ""

    return package


def main():
    parser = argparse.ArgumentParser(description="Hit Song Producer Pro (チャート1位級AI音楽プロデュース)")
    parser.add_argument("--theme", type=str, default=None, help="楽曲イメージやキーワード")
    parser.add_argument("--genre", type=str, default=None, help="希望ジャンル")
    parser.add_argument("--generate", action="store_true", help="即時音源レンダリングまで実行")
    parser.add_argument("--play", action="store_true", help="生成後に即座に再生")
    args = parser.parse_args()

    pkg = generate_hit_song_package(theme=args.theme, genre=args.genre, execute_generation=args.generate)
    print("\n" + "=" * 60)
    print("🏆 チャート1位級 楽曲設計プロデュース完了！")
    print(f"■ タイトル: 『{pkg['title']}』")
    print(f"■ ジャンル: {pkg['genre']} ({pkg['bpm']} BPM / {pkg['key']})")
    audio_target = pkg.get("final_audio_path") or (pkg.get("generation_result", {}).get("mp3_path"))
    if audio_target and os.path.exists(audio_target):
        sz = os.path.getsize(audio_target)
        print(f"■ 完成楽曲 (MP3): {audio_target} ({sz:,} bytes)")
        print(f"■ 保存場所: /storage/emulated/0/Music/TUGUMI/ (スマホ標準プレイヤーで即再生)")

        if args.play:
            print(f"[*] 再生を開始します: {os.path.basename(audio_target)}")
            try:
                subprocess.run(["termux-media-player", "play", audio_target], capture_output=True)
            except Exception:
                subprocess.run(["termux-open", audio_target], capture_output=True)
    print("=" * 60)


if __name__ == "__main__":
    main()
