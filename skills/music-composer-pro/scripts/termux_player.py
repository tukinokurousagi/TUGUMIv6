#!/data/data/com.termux/files/usr/bin/python3
# -*- coding: utf-8 -*-
"""
termux_player.py - TUGUMIv6 音楽プレイヤー＆オーディオマネージャー
Termux API (termux-media-player) および Android Intent と連携した再生コントローラー
"""

import os
import sys
import subprocess
import argparse
from typing import List, Dict

MUSIC_DIR = "/data/data/com.termux/files/home/TUGUMIv6/data/music"
SDCARD_MUSIC_DIR = "/storage/emulated/0/Music/TUGUMI"

def list_tracks() -> List[Dict]:
    tracks = []
    if os.path.exists(MUSIC_DIR):
        for f in sorted(os.listdir(MUSIC_DIR)):
            if f.endswith((".wav", ".mp3", ".mid", ".ogg")):
                p = os.path.join(MUSIC_DIR, f)
                tracks.append({
                    "filename": f,
                    "path": p,
                    "size": os.path.getsize(p),
                    "mtime": os.path.getmtime(p)
                })
    return sorted(tracks, key=lambda x: x["mtime"], reverse=True)

def play(path: str):
    if not os.path.exists(path):
        print(f"[!] File not found: {path}", file=sys.stderr)
        return False
    print(f"[*] Playing track: {os.path.basename(path)}")
    try:
        res = subprocess.run(["termux-media-player", "play", path], capture_output=True, text=True)
        if res.returncode == 0:
            print("[✔] Playing via termux-media-player")
            return True
    except Exception:
        pass

    # フォールバック: termux-open
    print("[*] Launching via Android default audio handler (termux-open)...")
    subprocess.run(["termux-open", path], capture_output=True)
    return True

def stop():
    try:
        subprocess.run(["termux-media-player", "stop"], capture_output=True)
        print("[✔] Playback stopped.")
    except Exception as e:
        print(f"[!] Stop error: {e}")

def pause():
    try:
        subprocess.run(["termux-media-player", "pause"], capture_output=True)
        print("[✔] Playback paused.")
    except Exception as e:
        print(f"[!] Pause error: {e}")

def info():
    try:
        res = subprocess.run(["termux-media-player", "info"], capture_output=True, text=True)
        print(res.stdout if res.stdout else "No track currently playing.")
    except Exception as e:
        print(f"[!] Info error: {e}")

def main():
    parser = argparse.ArgumentParser(description="TUGUMIv6 Termux Music Player")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="生成済み楽曲一覧を表示")
    p_play = sub.add_parser("play", help="楽曲を再生")
    p_play.add_argument("track", nargs="?", default="", help="トラック番号またはファイルパス")
    sub.add_parser("stop", help="再生停止")
    sub.add_parser("pause", help="一時停止")
    sub.add_parser("info", help="再生中トラック情報")

    args = parser.parse_args()

    if args.command == "list" or not args.command:
        tracks = list_tracks()
        if not tracks:
            print(f"楽曲ファイルはまだ生成されていません: {MUSIC_DIR}")
            return
        print(f"\n🎵 TUGUMIv6 制作済み楽曲ライブラリ ({len(tracks)} 曲):")
        print("-" * 65)
        for i, t in enumerate(tracks[:15], 1):
            sz_kb = t["size"] / 1024.0
            print(f"[{i:2d}] {t['filename']:<45} ({sz_kb:6.1f} KB)")
        print("-" * 65)
        print("再生コマンド: python3 termux_player.py play 1")

    elif args.command == "play":
        tracks = list_tracks()
        if not tracks:
            print("再生可能な楽曲がありません。")
            return
        target_path = ""
        if args.track.isdigit():
            idx = int(args.track) - 1
            if 0 <= idx < len(tracks):
                target_path = tracks[idx]["path"]
        elif args.track:
            target_path = args.track
        else:
            # 最新の曲を再生
            target_path = tracks[0]["path"]

        if target_path:
            play(target_path)

    elif args.command == "stop":
        stop()
    elif args.command == "pause":
        pause()
    elif args.command == "info":
        info()

if __name__ == "__main__":
    main()
