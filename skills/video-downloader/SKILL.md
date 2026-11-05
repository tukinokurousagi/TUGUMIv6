---
name: video-downloader
description: Download videos or extract audio from X (Twitter), YouTube, TikTok, Instagram, and other major video platforms with customizable quality and format options. Use this skill whenever the user asks to download, save, or grab videos from X, Twitter, YouTube, or other supported sites. Supports various quality settings (best, 1080p, 720p, 480p, 360p), multiple formats (mp4, webm, mkv), and audio-only downloads as MP3.
---

# Universal Video Downloader (X / Twitter, YouTube & More)

Download videos or extract audio from X (Twitter), YouTube, TikTok, Instagram, and other platforms with full control over quality and format settings.

## Quick Start

The simplest way to download a video:

```bash
# X (Twitter)
python scripts/download_video.py "https://x.com/username/status/1234567890"

# YouTube
python scripts/download_video.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

Downloaded videos are automatically sorted and saved to:
- **X (Twitter)**: `/storage/emulated/0/Download/X_Twitter/`
- **YouTube**: `/storage/emulated/0/Download/YouTube/`
- **Bilibili**: `/storage/emulated/0/Download/Bilibili/` (Mirrored to YouTube album)
- **TikTok / Instagram / Niconico / Others**: `/storage/emulated/0/Download/<Platform>/`
(Fallback: `/storage/emulated/0/TUGUMIDesk/Downloads/<Platform>/`)

## Options

### Quality Settings

Use `-q` or `--quality` to specify video quality:

- `best` (default): Highest quality available
- `1080p`: Full HD
- `720p`: HD
- `480p`: Standard definition
- `360p`: Lower quality
- `worst`: Lowest quality available

Example:
```bash
python scripts/download_video.py "https://x.com/username/status/1234567890" -q 1080p
```

### Format Options

Use `-f` or `--format` to specify output format (video downloads only):

- `mp4` (default): Most compatible
- `webm`: Modern format
- `mkv`: Matroska container

Example:
```bash
python scripts/download_video.py "URL" -f mp4
```

### Audio Only

Use `-a` or `--audio-only` to download only audio as MP3 (or specify `--audio-format`):

```bash
python scripts/download_video.py "URL" -a
```

### Custom Output Directory

Use `-o` or `--output` to specify a custom directory:

```bash
python scripts/download_video.py "URL" -o /custom/path
```

## How It Works

The skill uses `yt-dlp` (Termux & Android optimized):
- Automatically detects the platform (X / Twitter, YouTube, TikTok, etc.)
- Uses platform-optimized extractor arguments and modern JS runtimes
- Selects the best available video/audio streams and merges them cleanly
- Triggers `termux-media-scan` automatically so downloaded media appears immediately in Android gallery/media player apps
- Handles fallback storage paths safely for Android scoped storage