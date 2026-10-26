# -*- coding: utf-8 -*-
"""
TUGUMIv6 Notification & TTS Engine
Android Termux 通知 (termux-notification) および 音声合成読み上げ (termux-tts-speak) を管理。
音声合成時にアルファベットや専門用語（TUGUMI, API, MCP等）を自然な日本語読み仮名へ自動正規化。
"""

import os
import re
import subprocess
import shutil
from typing import Dict, Optional


def normalize_speech_text(text: str) -> str:
    """
    TTS音声合成用にテキストを自然な日本語読み・発音に正規化
    - TUGUMI -> つぐみ (「たぐみ」等の英語フォニックス誤読を完全排除)
    - Markdown記号やURLの除去
    - 専門用語・略語の読み仮名化
    - 日本語文字に隣接しても確実に置換できるようASCII境界ルックアラウンドを採用
    """
    if not text:
        return ""

    # Markdown URLリンク [テキスト](URL) -> テキスト
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # URL単体除去
    text = re.sub(r'https?://\S+', '', text)
    # 見出しマーク、太字・斜体、コードブロック記号の除去
    text = re.sub(r'[`#*_\~>]', '', text)

    # 固有名詞・略語の読み仮名マッピング（長い語句・複合語を優先置換）
    # ※日本語の助詞が直後に来てもマッチするよう (?<![a-zA-Z0-9]) と (?![a-zA-Z0-9]) を使用
    phonetic_map = [
        ('TUGUMI-CLIv6', 'つぐみシーエルアイブイシックス'),
        ('TUGUMI-CLIv5', 'つぐみシーエルアイブイファイブ'),
        ('TUGUMI-GPTv5', 'つぐみジーピーティーブイファイブ'),
        ('TUGUMIv6', 'つぐみブイシックス'),
        ('TUGUMIv5', 'つぐみブイファイブ'),
        ('TUGUMIDesk', 'つぐみデスク'),
        ('TUGUMI', 'つぐみ'),
        ('tugumi', 'つぐみ'),
        ('TSUGUMI', 'つぐみ'),
        ('tsugumi', 'つぐみ'),
        ('Antigravity', 'アンチグラビティ'),
        ('Gemini', 'ジェミニ'),
        ('Termux', 'ターマックス'),
        ('WebUI', 'ウェブユーアイ'),
        ('MCP', 'エムシーピー'),
        ('API', 'エーピーアイ'),
        ('CLI', 'シーエルアイ'),
        ('SDK', 'エスディーケー'),
        ('AI', 'エーアイ'),
        ('E2E', 'イートゥイー'),
        ('URL', 'ユーアールエル'),
        ('WAL', 'ウォル'),
        ('SQLite', 'エスキューライト'),
        ('FTS5', 'エフティーエスファイブ'),
        ('RSS', 'アールエスエス'),
    ]

    for word, replacement in phonetic_map:
        # 前後に英数字がない境界（日本語文字や記号、空白に隣接していてもマッチ）
        pattern = rf'(?<![a-zA-Z0-9]){re.escape(word)}(?![a-zA-Z0-9])'
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # 連続空白や改行の整理
    text = re.sub(r'\s+', ' ', text).strip()
    return text


class NotificationEngine:
    """Termux-API を活用した通知 & 音声読み上げエンジン"""
    def __init__(self):
        self.notification_bin = shutil.which("termux-notification") or "/data/data/com.termux/files/usr/bin/termux-notification"
        self.tts_bin = shutil.which("termux-tts-speak") or "/data/data/com.termux/files/usr/bin/termux-tts-speak"
        self.notify_enable = os.environ.get("TUGUMI_NOTIFY_ENABLE", "true").lower() in ("true", "1", "yes")
        self.tts_enable = os.environ.get("TUGUMI_TTS_ENABLE", "true").lower() in ("true", "1", "yes")

    def send_notification(
        self,
        title: str = "TUGUMIv6",
        content: str = "",
        priority: str = "high",
        id_tag: str = "tugumi_briefing"
    ) -> bool:
        """Android 通知を送信"""
        if not self.notify_enable:
            return False
        if not os.path.exists(self.notification_bin):
            return False

        try:
            cmd = [
                self.notification_bin,
                "--title", title,
                "--content", content,
                "--priority", priority,
                "--id", id_tag
            ]
            subprocess.run(cmd, capture_output=True, timeout=20)
            return True
        except Exception:
            return False

    def speak(self, text: str, rate: float = 1.0, pitch: float = 1.0, lang: str = "ja") -> bool:
        """音声合成 (TTS) で読み上げ（日本語読み正規化・言語ja指定済み）"""
        if not self.tts_enable:
            return False
        if not os.path.exists(self.tts_bin):
            return False

        try:
            # 音声用にテキストを正規化（「TUGUMI」->「つぐみ」等の誤読根絶）
            clean_text = normalize_speech_text(text)
            if not clean_text:
                return False

            # バックグラウンドで非同期読み上げ (日本語言語明示 -l ja)
            cmd = [self.tts_bin, "-l", lang, "-r", str(rate), "-p", str(pitch), clean_text]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False

    def notify_and_speak(self, title: str, message: str, speak_text: Optional[str] = None) -> Dict[str, bool]:
        """通知とTTS読み上げを同時に実行"""
        n_res = self.send_notification(title=title, content=message)
        s_text = speak_text or message
        s_res = self.speak(s_text)
        return {"notification": n_res, "tts": s_res}
