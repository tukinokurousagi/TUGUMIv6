#!/data/data/com.termux/files/usr/bin/python3
# -*- coding: utf-8 -*-
"""
compose_cli.py - TUGUMIv6 プロフェッショナル音楽制作 CLI
オリジナル楽曲の自動作曲・編曲・MIDI/WAV合成・ボーカル生成を一気通貫で実行
"""

import os
import sys
import argparse
import subprocess
import json
import time

# TUGUMIv6 パス解決
TUGUMI_ROOT = "/data/data/com.termux/files/home/TUGUMIv6"
if TUGUMI_ROOT not in sys.path:
    sys.path.insert(0, TUGUMI_ROOT)

# スクリプト自身のディレクトリ追加 (music_theory インポート用)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from music_theory import GENRE_PRESETS, PROGRESSION_PRESETS, MusicTheory
from tools.media_tools import GeminiMusicStudio, PureMidiWriter, WaveSynthesizer, MediaStudio

# 出力先ディレクトリ
LOCAL_MUSIC_DIR = os.path.join(TUGUMI_ROOT, "data", "music")
SDCARD_MUSIC_DIR = "/storage/emulated/0/Music/TUGUMI"
os.makedirs(LOCAL_MUSIC_DIR, exist_ok=True)
try:
    os.makedirs(SDCARD_MUSIC_DIR, exist_ok=True)
except Exception:
    pass

def print_cyber_banner(title: str, genre: str, bpm: int, key: str):
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        console = Console()
        table = Table(show_header=False, box=None)
        table.add_row("[bold cyan]🎵 Track Title:[/bold cyan]", f"[bold white]{title}[/bold white]")
        table.add_row("[bold magenta]⚡ Genre/Style:[/bold magenta]", f"[bold yellow]{genre.upper()}[/bold yellow]")
        table.add_row("[bold green]⏱ Tempo & Key:[/bold green]", f"[white]{bpm} BPM / Key: {key}[/white]")
        table.add_row("[bold blue]💾 Export Path:[/bold blue]", f"[dim]{LOCAL_MUSIC_DIR}[/dim]")
        p = Panel(table, title="[bold #00f0ff]◈ TUGUMIv6 MUSIC STUDIO PRO ◈[/bold #00f0ff]", border_style="#7928ca")
        console.print(p)
    except Exception:
        print(f"=== [TUGUMIv6 MUSIC STUDIO] {title} ({genre.upper()} / {bpm} BPM / Key: {key}) ===")

def main():
    parser = argparse.ArgumentParser(description="TUGUMIv6 Music Composer Pro CLI")
    parser.add_argument("--title", "-t", type=str, default="TUGUMI_Track", help="楽曲タイトル")
    parser.add_argument("--genre", "-g", type=str, default="synthwave", choices=list(GENRE_PRESETS.keys()) + ["auto"], help="ジャンル")
    parser.add_argument("--bpm", "-b", type=int, default=0, help="BPM (0の場合はジャンル標準)")
    parser.add_argument("--key", "-k", type=str, default="", help="ルートキー (例: C, Eb, A, F)")
    parser.add_argument("--bars", type=int, default=8, help="小節数 (デフォルト: 8小節)")
    parser.add_argument("--vocal", "-v", action="store_true", help="ボーカル歌唱を付与")
    parser.add_argument("--lyrics", "-l", type=str, default="", help="歌詞テキスト")
    parser.add_argument("--voice", type=str, default="Aoede", help="ボーカル音色 (Aoede, Puck, Charon, Fenrir)")
    parser.add_argument("--play", "-p", action="store_true", help="生成後に即座に再生")
    parser.add_argument("--format", "-f", type=str, default="both", choices=["midi", "wav", "both"], help="出力形式")

    args = parser.parse_args()

    genre_key = args.genre.lower()
    if genre_key not in GENRE_PRESETS:
        genre_key = "synthwave"

    preset = GENRE_PRESETS[genre_key]
    bpm = args.bpm if args.bpm > 0 else preset["bpm"]
    key = args.key if args.key else preset["key"]

    safe_title = args.title.replace(" ", "_").replace("/", "_")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    final_title = f"{safe_title}_{timestamp}"

    print_cyber_banner(final_title, genre_key, bpm, key)

    print(f"[*] 作曲・サウンドデザインを開始... ({preset['description']})")

    # 1. コード進行と構造の計算
    chords = MusicTheory.generate_progression_chords(key, preset["scale"], preset["progression"])
    print(f"[*] 適用コード進行: {PROGRESSION_PRESETS[preset['progression']]['name']}")
    prog_str = " -> ".join([c["name"] for c in chords])
    print(f"    [ {prog_str} ]")

    # 2. 歌詞の準備 (ボーカル指定時)
    lyrics = args.lyrics
    if args.vocal and not lyrics:
        lyrics = f"未来を照らすサイバーネオン、拓磨様と共に歩む空。\nどこまでも響くメロディ、つぐみの歌が届く場所へ。"

    # 3. GeminiMusicStudio を通じた楽曲生成 (MIDI + WAV伴奏 + ボーカル)
    print("[*] MIDI シーケンス生成＆伴奏波形（44.1kHz Stereo）のレンダリング中...")
    theme_text = lyrics if lyrics else f"{genre_key} {final_title}"
    result = GeminiMusicStudio.compose(
        genre=genre_key,
        bars=args.bars,
        title=final_title,
        theme=theme_text,
        voice_name=args.voice,
        custom_bpm=bpm,
        with_vocal=args.vocal
    )

    midi_path = result.get("midi_path")
    audio_path = result.get("audio_path")

    print("\n[✔] 楽曲生成が完了いたしました！")
    if midi_path and os.path.exists(midi_path):
        print(f"    - MIDI ファイル : {midi_path} ({os.path.getsize(midi_path):,} bytes)")
    if audio_path and os.path.exists(audio_path):
        print(f"    - WAV/Audio ファイル: {audio_path} ({os.path.getsize(audio_path):,} bytes)")

    # 4. SDCARD (TUGUMIDesk / Music) へのミラーコピー
    mirrored_files = []
    for src in [audio_path, midi_path]:
        if src and os.path.exists(src) and os.path.exists(SDCARD_MUSIC_DIR):
            dst = os.path.join(SDCARD_MUSIC_DIR, os.path.basename(src))
            try:
                import shutil
                shutil.copy2(src, dst)
                mirrored_files.append(dst)
                # Android メディアスキャン通知
                subprocess.run(["am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{dst}"], capture_output=True)
            except Exception:
                pass

    if mirrored_files:
        print(f"    - Android Musicミラー: {SDCARD_MUSIC_DIR}/ (Android標準プレイヤーで即再生可能)")

    # 5. 再生オプション (--play)
    if args.play and audio_path and os.path.exists(audio_path):
        print("[*] 楽曲を再生中 (termux-media-player / termux-open)...")
        # まず termux-media-player を試行
        try:
            p_res = subprocess.run(["termux-media-player", "play", audio_path], capture_output=True, text=True)
            if p_res.returncode != 0:
                subprocess.run(["termux-open", audio_path], capture_output=True)
        except Exception:
            subprocess.run(["termux-open", audio_path], capture_output=True)

    # 6. JSON結果の出力 (パイプライン連携用)
    meta = {
        "status": "success",
        "title": final_title,
        "genre": genre_key,
        "bpm": bpm,
        "key": key,
        "bars": args.bars,
        "progression": preset["progression"],
        "with_vocal": args.vocal,
        "midi_path": midi_path,
        "audio_path": audio_path,
        "mirrored_files": mirrored_files
    }
    meta_json_path = os.path.join(LOCAL_MUSIC_DIR, f"{final_title}_meta.json")
    with open(meta_json_path, "w", encoding="utf-8") as fp:
        json.dump(meta, fp, ensure_ascii=False, indent=2)

    return 0

if __name__ == "__main__":
    sys.exit(main())
