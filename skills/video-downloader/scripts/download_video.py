#!/data/data/com.termux/files/usr/bin/python3
"""
Universal Video Downloader (Termux & Android Universal Architecture)
===================================================================
Downloads videos or extracts audio from X (Twitter), YouTube, TikTok, Instagram,
Niconico, Bilibili, Twitch, Reddit, Facebook, Bluesky, Threads, Vimeo, and more.

Created for 拓磨様 by つぐみ (TUGUMI)
Engine: Termux & Android Scoped Storage Optimized
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
from urllib.parse import urlparse
from typing import Dict, Any, Optional

PRIMARY_DOWNLOAD_ROOT = "/storage/emulated/0/Download"
FALLBACK_DOWNLOAD_ROOT = "/storage/emulated/0/TUGUMIDesk/Downloads"
LOCAL_FALLBACK_ROOT = os.path.expanduser("~/downloads")


def _is_domain_match(domain: str, targets: list) -> bool:
    for t in targets:
        if domain == t or domain.endswith("." + t):
            return True
    return False


def detect_platform(url: str) -> str:
    """URLからプラットフォーム種別を判定"""
    domain = urlparse(url).netloc.lower()
    if _is_domain_match(domain, ["twitter.com", "x.com", "t.co"]):
        return "X_Twitter"
    elif _is_domain_match(domain, ["youtube.com", "youtu.be"]):
        return "YouTube"
    elif _is_domain_match(domain, ["tiktok.com"]):
        return "TikTok"
    elif _is_domain_match(domain, ["instagram.com"]):
        return "Instagram"
    elif _is_domain_match(domain, ["nicovideo.jp", "nico.ms"]):
        return "Niconico"
    elif _is_domain_match(domain, ["bilibili.com", "b23.tv"]):
        return "Bilibili"
    elif _is_domain_match(domain, ["twitch.tv"]):
        return "Twitch"
    elif _is_domain_match(domain, ["reddit.com", "redd.it"]):
        return "Reddit"
    elif _is_domain_match(domain, ["facebook.com", "fb.watch"]):
        return "Facebook"
    elif _is_domain_match(domain, ["threads.net"]):
        return "Threads"
    elif _is_domain_match(domain, ["bsky.app"]):
        return "Bluesky"
    elif _is_domain_match(domain, ["vimeo.com"]):
        return "Vimeo"
    return "Videos"


def resolve_output_dir(platform: str = "Videos", custom_path: Optional[str] = None, audio_only: bool = False) -> str:
    """Termux / Android ストレージに適合した安全な出力先ディレクトリを解決"""
    if custom_path:
        out_dir = os.path.abspath(os.path.expanduser(custom_path.strip()))
        try:
            os.makedirs(out_dir, exist_ok=True)
            return out_dir
        except Exception:
            pass

    # 音声のみの場合はプラットフォーム内の Audio フォルダに整理
    sub_folder = os.path.join(platform, "Audio") if audio_only else platform

    for root_dir in [PRIMARY_DOWNLOAD_ROOT, FALLBACK_DOWNLOAD_ROOT, LOCAL_FALLBACK_ROOT]:
        try:
            target_dir = os.path.join(root_dir, sub_folder)
            os.makedirs(target_dir, exist_ok=True)
            test_file = os.path.join(target_dir, ".write_test")
            with open(test_file, "w") as f:
                f.write("ok")
            os.remove(test_file)
            return target_dir
        except Exception:
            continue

    fallback_dir = os.path.join(LOCAL_FALLBACK_ROOT, sub_folder)
    os.makedirs(fallback_dir, exist_ok=True)
    return fallback_dir


def find_node_runtime() -> Optional[str]:
    """Node.js ランタイムのパスを探索"""
    candidates = [
        "/data/data/com.termux/files/usr/bin/node",
        shutil.which("node"),
    ]
    for c in candidates:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def run_media_scan(target_path: str):
    """Termux Media Scanner を呼び出してAndroidメディアデータベースに即時反映"""
    try:
        scan_bin = shutil.which("termux-media-scan") or "/data/data/com.termux/files/usr/bin/termux-media-scan"
        if os.path.isfile(scan_bin) and os.access(scan_bin, os.X_OK):
            subprocess.run([scan_bin, "-r", target_path], capture_output=True, timeout=10)
    except Exception:
        pass


def check_yt_dlp():
    """yt-dlp の導入状態を確認"""
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("yt-dlp not found. Installing...", file=sys.stderr)
        subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages", "yt-dlp"], check=True)


def get_video_info(url: str, node_path: Optional[str] = None) -> Dict[str, Any]:
    """動画情報を取得（障害耐性: 失敗してもダウンロードをブロックしない）"""
    cmd = ["yt-dlp", "--dump-json", "--no-playlist", "--no-warnings"]
    if node_path:
        cmd.extend(["--js-runtimes", f"node:{node_path}", "--remote-components", "ejs:github"])
    cmd.append(url)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        return json.loads(line)
                    except Exception:
                        continue
    except Exception as e:
        print(f"Notice: Metadata extraction skipped: {e}", file=sys.stderr)
    return {}


def download_video(
    url: str,
    output_path: Optional[str] = None,
    quality: str = "best",
    format_type: str = "mp4",
    audio_only: bool = False,
    audio_format: str = "mp3"
) -> Dict[str, Any]:
    """
    あらゆる対応プラットフォームから動画または音声をダウンロードする
    """
    check_yt_dlp()
    platform = detect_platform(url)
    out_dir = resolve_output_dir(platform=platform, custom_path=output_path, audio_only=audio_only)
    node_path = find_node_runtime()

    cmd = [
        "yt-dlp",
        "--no-mtime",
        "--no-part",
        "--retries", "3",
        "--fragment-retries", "5",
        "--windows-filenames",
        "--no-playlist",
    ]

    # Node.js ランタイム
    if node_path:
        cmd.extend(["--js-runtimes", f"node:{node_path}", "--remote-components", "ejs:github"])

    # プラットフォーム別最適化
    if platform == "YouTube":
        cmd.extend([
            "--extractor-args", "youtube:player_client=mweb,web",
            "--compat-options", "no-youtube-unavailable-videos"
        ])
    elif platform == "X_Twitter":
        cmd.extend([
            "--no-check-certificates",
            "--add-header", "Referer:https://x.com/",
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "--extractor-args", "twitter:api=graphql,legacy"
        ])
        for cookie_path in [
            os.path.expanduser("~/.config/yt-dlp/x_cookies.txt"),
            os.path.expanduser("~/.config/yt-dlp/twitter_cookies.txt"),
            os.path.expanduser("~/.config/yt-dlp/cookies.txt"),
            os.path.expanduser("~/x_cookies.txt"),
            os.path.expanduser("~/cookies.txt"),
            "/storage/emulated/0/Download/cookies.txt",
            "/storage/emulated/0/Download/x_cookies.txt",
            "/storage/emulated/0/Download/twitter_cookies.txt",
        ]:
            if os.path.isfile(cookie_path):
                print(f"🍪 X (Twitter) Cookieを検出して適用: {cookie_path}")
                cmd.extend(["--cookies", cookie_path])
                break
    elif platform == "Bilibili":
        cmd.extend([
            "--no-check-certificates",
            "--add-header", "Referer:https://www.bilibili.com",
            "--add-header", "User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ])
        for cookie_path in [
            os.path.expanduser("~/.config/yt-dlp/bilibili_cookies.txt"),
            os.path.expanduser("~/bilibili_cookies.txt"),
            os.path.expanduser("~/.config/yt-dlp/cookies.txt"),
            os.path.expanduser("~/cookies.txt"),
        ]:
            if os.path.isfile(cookie_path):
                cmd.extend(["--cookies", cookie_path])
                break
    elif platform == "TikTok":
        cmd.extend(["--no-check-certificates"])
    elif platform == "Instagram":
        cmd.extend(["--no-check-certificates"])

    # 音声のみ vs 動画
    if audio_only:
        cmd.extend([
            "-x",
            "--audio-format", audio_format,
            "--audio-quality", "0",
        ])
    else:
        if quality == "best":
            if platform == "Bilibili":
                format_string = "bestvideo*[vcodec^=avc]+bestaudio/bestvideo*+bestaudio/best"
            elif platform == "X_Twitter":
                format_string = "best[ext=mp4]/best/bestvideo*+bestaudio"
            else:
                format_string = "bestvideo*+bestaudio/best"
        elif quality == "worst":
            format_string = "worstvideo*+worstaudio/worst"
        else:
            height = quality.replace("p", "")
            if platform == "Bilibili":
                format_string = f"bestvideo*[height<={height}][vcodec^=avc]+bestaudio/bestvideo*[height<={height}]+bestaudio/best[height<={height}]/best"
            elif platform == "X_Twitter":
                format_string = f"best[height<={height}][ext=mp4]/best[height<={height}]/bestvideo*[height<={height}]+bestaudio/best"
            else:
                format_string = f"bestvideo*[height<={height}]+bestaudio/best[height<={height}]/best"

        cmd.extend([
            "-f", format_string,
            "--merge-output-format", format_type,
        ])

    # 出力ファイル名テンプレート（Androidのファイル名長制限に適合）
    cmd.extend([
        "-o", f"{out_dir}/%(title).100B [%(id)s].%(ext)s",
    ])

    # URLサニタイズ（クエリパラメータの除去）
    target_dl_url = url.split("?")[0] if ("twitter.com" in url or "x.com" in url) and "/status/" in url else url
    cmd.append(target_dl_url)

    print(f"🎬 Platform: {platform}")
    print(f"🔗 URL: {url}")
    print(f"🎯 Mode: {'Audio (' + audio_format + ')' if audio_only else 'Video (' + quality + ', ' + format_type + ')'}")
    print(f"📁 Output Directory: {out_dir}\n")

    # メタデータ取得（オプショナル）
    info = get_video_info(url, node_path)
    title = info.get("title", "Unknown Title")
    uploader = info.get("uploader", "Unknown Uploader")
    duration = info.get("duration", 0)

    print(f"📌 Title: {title}")
    if duration:
        try:
            d_sec = int(float(duration))
            print(f"⏱️ Duration: {d_sec // 60}:{d_sec % 60:02d}")
        except Exception:
            pass
    if uploader != "Unknown Uploader":
        print(f"👤 Uploader: {uploader}")
    print("")

    try:
        subprocess.run(cmd, check=True)
        # 最も新しく保存されたファイルを特定
        latest_file = None
        try:
            files = [os.path.join(out_dir, f) for f in os.listdir(out_dir) if not f.startswith(".")]
            if files:
                latest_file = max(files, key=os.path.getmtime)
        except Exception:
            pass

        return {
            "success": True,
            "platform": platform,
            "title": title,
            "uploader": uploader,
            "output_dir": out_dir,
            "file_path": latest_file,
            "error": None
        }
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error downloading video: {e}", file=sys.stderr)
        return {
            "success": False,
            "platform": platform,
            "title": title,
            "uploader": uploader,
            "output_dir": out_dir,
            "error": str(e)
        }
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        return {
            "success": False,
            "platform": platform,
            "title": title,
            "uploader": uploader,
            "output_dir": out_dir,
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(
        description="Universal Video Downloader for Termux (X, YouTube, TikTok, Instagram, Niconico, and more)"
    )
    parser.add_argument("url", help="Video URL (X/Twitter, YouTube, TikTok, Instagram, etc.)")
    parser.add_argument(
        "-o", "--output",
        default=None,
        help=f"Output directory (default: {PRIMARY_DOWNLOAD_ROOT}/<Platform>)"
    )
    parser.add_argument(
        "-q", "--quality",
        default="best",
        choices=["best", "1080p", "720p", "480p", "360p", "worst"],
        help="Video quality (default: best)"
    )
    parser.add_argument(
        "-f", "--format",
        default="mp4",
        choices=["mp4", "webm", "mkv"],
        help="Video format (default: mp4)"
    )
    parser.add_argument(
        "-a", "--audio-only",
        action="store_true",
        help="Download only audio (default: MP3)"
    )
    parser.add_argument(
        "--audio-format",
        default="mp3",
        choices=["mp3", "m4a", "flac", "wav", "opus"],
        help="Audio format (default: mp3)"
    )
    parser.add_argument(
        "--json-result",
        action="store_true",
        help="Print result summary as JSON on stdout"
    )

    args = parser.parse_args()

    result = download_video(
        url=args.url,
        output_path=args.output,
        quality=args.quality,
        format_type=args.format,
        audio_only=args.audio_only,
        audio_format=args.audio_format
    )

    if args.json_result:
        print(f"\n__RESULT_JSON__={json.dumps(result, ensure_ascii=False)}")

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()