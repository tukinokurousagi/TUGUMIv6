---
name: termux-bilibili-widget
description: "Termux widget setup for downloading Bilibili videos."
version: 0.1.0
author: Hermes
category: ツール
created_at: 2026-10-27T23:59:00Z
---

# Termux Bilibili Widget Setup

## When to Use
- Need to download Bilibili videos directly from Android via Termux Widget shortcuts.
- Parsing URLs from shared Bilibili app text containing Chinese characters or short links (`b23.tv`).
- Resolving yt-dlp extraction errors like `Unable to extract initial state` on Bilibili URLs.

## Prerequisites
- Termux and Termux:Widget installed on Android.
- Termux API package (`pkg install termux-api`) and Android app installed.
- `python`, `yt-dlp`, and `ffmpeg` installed in Termux (`pkg install python ffmpeg && pip install yt-dlp`).
- Storage permissions granted (`termux-setup-storage`).

## How to Run
```bash
# 1. Install helper script and patch
python3 setup_bilibili_widget.py

# 2. Test URL extractor with sample inputs
python3 url_extractor.py "【乃木坂46】Route 246 https://b23.tv/BV1rP411378L 点赞"

# 3. Trigger widget shortcut directly from CLI
bash ~/.shortcuts/tasks/📺_Bilibili動画ダウンロード.sh
```

## Quick Reference
- Widget shortcut path: `~/.shortcuts/tasks/📺_Bilibili動画ダウンロード.sh`
- Download directory: `/storage/emulated/0/Download/Bilibili/`
- Supported inputs: `b23.tv/*`, `BV...`, `av...`, full Bilibili URLs, or raw shared strings with Chinese text.

## Procedure
1. **Setup Download Directory & Shortcut Tree**: Create `~/.shortcuts/tasks` and ensure target storage directory `/storage/emulated/0/Download/Bilibili` exists.
2. **Deploy Strict URL Parser**: Implement a dedicated URL extractor that isolates ASCII URL characters from full-width symbols and Asian characters.
3. **Handle yt-dlp Extractor Compatibility**: Apply WBI API fallback or update yt-dlp if `Unable to extract initial state` occurs due to Bilibili CSR changes.
4. **Write Widget Shell Script**: Create the interactive shortcut script using `termux-dialog` for URL input, running `yt-dlp` in background with single-video safety constraints (`--no-playlist` by default), and triggering `termux-notification` upon completion.
5. **Set Execution Permissions & Validate**: Run `chmod +x` on shortcut scripts and execute syntax validation (`bash -n`).

## Pitfalls
- **Broad Regex Matching**: Using generic `[^\s]+` captures Chinese punctuation marks (e.g., `【`, `）`) and trailing punctuation, breaking `yt-dlp` parsing.
- **Unbounded Playlist Downloads**: Downloading multi-part Bilibili collections without `--no-playlist` or `--playlist-items` will quickly exhaust device storage.
- **Termux Background Kill**: Large videos may fail if Android battery optimizations kill Termux; acquire wakelock via `termux-wake-lock` during downloads.

## Verification
- Run unit tests verifying `smart_extract_url` with raw BV codes, short URLs, and noisy shared text.
- Trigger the widget script and verify download file presence in `/storage/emulated/0/Download/Bilibili/`.
