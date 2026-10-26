"""
TUGUMIv6 次世代クリエイティブ統合スタジオ (media_tools.py)
Gemini API ネイティブモデルをフル活用した:
1. 作詞・フルボイス歌唱オーディオ合成・マルチトラック楽曲制作 (Full Voice Music Studio)
2. 最新Gemini画像モデルによる画像生成・画像編集・複数画像一枚合成 (Gemini Image Studio)
Dedicated to Master Takuma
"""

import os
import io
import time
import math
import struct
import wave
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

try:
    import numpy as np
except ImportError:
    np = None

try:
    from PIL import Image, ImageEnhance
except ImportError:
    Image = None

from google import genai
from google.genai import types

# 保存先パス定義
DESK_DIR = "/storage/emulated/0/TUGUMIDesk"
if not os.path.exists("/storage/emulated/0"):
    DESK_DIR = os.path.expanduser("~/TUGUMIDesk")

MUSIC_DIR = os.path.join(DESK_DIR, "音楽・作曲")
IMAGES_DIR = os.path.join(DESK_DIR, "Images")
UI_DESIGN_DIR = os.path.join(DESK_DIR, "UIデザイン")

os.makedirs(MUSIC_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(UI_DESIGN_DIR, exist_ok=True)


def _scan_media_file(filepath: str):
    """Android MediaScanner を呼び出してギャラリーや音楽プレーヤーに即時反映"""
    if shutil.which("termux-media-scan"):
        try:
            subprocess.Popen(["termux-media-scan", filepath], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


def _get_genai_client() -> genai.Client:
    """Gemini API クライアントを取得"""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    return genai.Client(api_key=api_key)


def _get_block_none_safety_settings() -> Any:
    """全カテゴリー BLOCK_NONE の安全設定を生成"""
    if not (types and hasattr(types, "SafetySetting") and hasattr(types, "HarmCategory") and hasattr(types, "HarmBlockThreshold")):
        return [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "BLOCK_NONE"},
        ]
    cats = [
        getattr(types.HarmCategory, "HARM_CATEGORY_HARASSMENT", None),
        getattr(types.HarmCategory, "HARM_CATEGORY_HATE_SPEECH", None),
        getattr(types.HarmCategory, "HARM_CATEGORY_SEXUALLY_EXPLICIT", None),
        getattr(types.HarmCategory, "HARM_CATEGORY_DANGEROUS_CONTENT", None),
        getattr(types.HarmCategory, "HARM_CATEGORY_CIVIC_INTEGRITY", None),
    ]
    settings = []
    for c in cats:
        if c is not None:
            settings.append(
                types.SafetySetting(
                    category=c,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE
                )
            )
    return settings


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 伴奏シンセサイザー & MIDIエンジン (Backing Track Synth & MIDI)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PureMidiWriter:
    """純粋PythonによるStandard MIDI File (Format 1) エンコーダー"""
    
    NOTE_NAMES = {
        "C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3,
        "E": 4, "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8,
        "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11
    }

    def __init__(self, bpm: int = 120, ticks_per_beat: int = 480):
        self.bpm = bpm
        self.ticks_per_beat = ticks_per_beat
        self.tracks: List[List[Tuple[int, bytes]]] = []
        self.track_names: List[str] = []

    @classmethod
    def note_to_midi(cls, note_str: str) -> int:
        note_str = note_str.strip().upper()
        if not note_str:
            return 60
        if note_str[-1].isdigit():
            octave = int(note_str[-1])
            name = note_str[:-1]
        elif len(note_str) > 1 and note_str[-2] == '-' and note_str[-1].isdigit():
            octave = -int(note_str[-1])
            name = note_str[:-2]
        else:
            octave = 4
            name = note_str
        semitone = cls.NOTE_NAMES.get(name, 0)
        return max(0, min(127, (octave + 1) * 12 + semitone))

    def add_track(self, name: str = "", instrument: int = 0) -> int:
        track_idx = len(self.tracks)
        events = [(0, bytes([0xC0 | (track_idx % 16), instrument & 0x7F]))]
        self.tracks.append(events)
        self.track_names.append(name)
        return track_idx

    def add_note(self, track_idx: int, note: Union[str, int], start_beat: float, duration_beat: float, velocity: int = 90):
        midi_note = self.note_to_midi(note) if isinstance(note, str) else int(note)
        channel = track_idx % 16
        start_tick = int(start_beat * self.ticks_per_beat)
        end_tick = start_tick + int(duration_beat * self.ticks_per_beat)

        note_on = bytes([0x90 | channel, midi_note & 0x7F, velocity & 0x7F])
        note_off = bytes([0x80 | channel, midi_note & 0x7F, 0])

        self.tracks[track_idx].append((start_tick, note_on))
        self.tracks[track_idx].append((end_tick, note_off))

    def _var_len_bytes(self, value: int) -> bytes:
        buf = [value & 0x7F]
        value >>= 7
        while value > 0:
            buf.append((value & 0x7F) | 0x80)
            value >>= 7
        return bytes(reversed(buf))

    def write_to_file(self, filepath: str):
        tempo_us = int(60_000_000 / max(20, self.bpm))
        tempo_bytes = bytes([0xFF, 0x51, 0x03, (tempo_us >> 16) & 0xFF, (tempo_us >> 8) & 0xFF, tempo_us & 0xFF])

        track_chunks = []
        for i, events in enumerate(self.tracks):
            sorted_events = sorted(events, key=lambda x: x[0])
            track_data = bytearray()
            if i == 0:
                track_data.extend(self._var_len_bytes(0))
                track_data.extend(tempo_bytes)

            last_tick = 0
            for tick, ev_bytes in sorted_events:
                delta = max(0, tick - last_tick)
                track_data.extend(self._var_len_bytes(delta))
                track_data.extend(ev_bytes)
                last_tick = tick

            track_data.extend(self._var_len_bytes(0))
            track_data.extend(bytes([0xFF, 0x2F, 0x00]))
            chunk = b"MTrk" + struct.pack(">I", len(track_data)) + bytes(track_data)
            track_chunks.append(chunk)

        header = b"MThd" + struct.pack(">IHHH", 6, 1, len(track_chunks), self.ticks_per_beat)
        with open(filepath, "wb") as f:
            f.write(header)
            for chunk in track_chunks:
                f.write(chunk)


class WaveSynthesizer:
    """NumPy を使用した伴奏波形合成エンジン (44.1kHz Stereo)"""

    SAMPLE_RATE = 44100

    @classmethod
    def midi_to_freq(cls, midi_note: int) -> float:
        return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

    @classmethod
    def generate_osc(cls, freq: float, duration: float, wave_type: str = "sawtooth", sample_rate: int = 44100) -> np.ndarray:
        if np is None:
            return np.zeros(int(sample_rate * duration), dtype=np.float32)
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        phase = 2.0 * np.pi * freq * t

        if wave_type == "sine":
            return np.sin(phase)
        elif wave_type == "square":
            return np.sign(np.sin(phase)) * 0.7
        elif wave_type == "sawtooth":
            return 2.0 * (t * freq - np.floor(t * freq + 0.5)) * 0.7
        elif wave_type == "triangle":
            return 2.0 * np.abs(2.0 * (t * freq - np.floor(t * freq + 0.5))) - 1.0
        elif wave_type == "fm":
            modulator = np.sin(2.0 * np.pi * (freq * 2.0) * t) * 2.5
            return np.sin(phase + modulator) * 0.7
        elif wave_type == "pluck":
            harmonics = np.sin(phase) + 0.5 * np.sin(phase * 2) + 0.25 * np.sin(phase * 3)
            decay = np.exp(-t * (4.0 + freq * 0.005))
            return harmonics * decay
        return np.sin(phase)

    @classmethod
    def apply_adsr(cls, waveform: np.ndarray, duration: float, attack: float = 0.02, decay: float = 0.1, sustain: float = 0.7, release: float = 0.08, sample_rate: int = 44100) -> np.ndarray:
        if np is None or len(waveform) == 0:
            return waveform
        total_samples = len(waveform)
        att_samples = int(min(attack, duration * 0.3) * sample_rate)
        dec_samples = int(min(decay, duration * 0.3) * sample_rate)
        rel_samples = int(min(release, duration * 0.4) * sample_rate)
        sus_samples = max(0, total_samples - att_samples - dec_samples - rel_samples)

        env = []
        if att_samples > 0: env.append(np.linspace(0.0, 1.0, att_samples))
        if dec_samples > 0: env.append(np.linspace(1.0, sustain, dec_samples))
        if sus_samples > 0: env.append(np.full(sus_samples, sustain))
        if rel_samples > 0: env.append(np.linspace(sustain, 0.0, rel_samples))

        envelope = np.concatenate(env) if env else np.ones(total_samples)
        if len(envelope) < total_samples:
            envelope = np.pad(envelope, (0, total_samples - len(envelope)), 'constant')
        elif len(envelope) > total_samples:
            envelope = envelope[:total_samples]
        return waveform * envelope

    @classmethod
    def synthesize_drum_hit(cls, drum_type: str, sample_rate: int = 44100) -> np.ndarray:
        if np is None: return np.zeros(100)
        if drum_type == "kick":
            dur = 0.25
            t = np.linspace(0, dur, int(sample_rate * dur), endpoint=False)
            freq = 150.0 * np.exp(-t * 28.0) + 40.0
            phase = 2.0 * np.pi * np.cumsum(freq) / sample_rate
            return np.sin(phase) * np.exp(-t * 18.0) * 0.95
        elif drum_type == "snare":
            dur = 0.2
            t = np.linspace(0, dur, int(sample_rate * dur), endpoint=False)
            noise = (np.random.rand(len(t)) * 2.0 - 1.0) * np.exp(-t * 22.0) * 0.6
            tone = np.sin(2.0 * np.pi * 180.0 * np.exp(-t * 20.0) * t) * np.exp(-t * 25.0) * 0.5
            return (noise + tone) * 0.8
        elif drum_type == "hihat":
            dur = 0.06
            t = np.linspace(0, dur, int(sample_rate * dur), endpoint=False)
            return (np.random.rand(len(t)) * 2.0 - 1.0) * np.exp(-t * 60.0) * 0.4
        return np.zeros(100)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. Gemini フルボイス楽曲制作エンジン (Full Voice Music Studio)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class GeminiMusicStudio:
    """TUGUMIv6 作詞 ＆ Gemini API 音声モデルによるフルボイス楽曲制作エンジン"""

    PRESETS = {
        "cyberpunk": {"bpm": 128, "root": "D", "scale": [0, 2, 3, 5, 7, 8, 10], "desc": "サイバーパンク/シンセウェーブ"},
        "lofi": {"bpm": 80, "root": "C", "scale": [0, 2, 4, 7, 9], "desc": "チルアウト・ローファイ・ヒップホップ"},
        "jpop": {"bpm": 124, "root": "G", "scale": [0, 2, 4, 5, 7, 9, 11], "desc": "エモーショナルJ-POP/アニソン"},
        "chiptune": {"bpm": 140, "root": "C", "scale": [0, 2, 4, 5, 7, 9, 11], "desc": "レトロ8ビット・ゲームサウンド"},
        "japanese": {"bpm": 105, "root": "A", "scale": [0, 2, 3, 7, 8], "desc": "情緒豊かな和風ヨナ抜きメロディ"},
        "ambient": {"bpm": 65, "root": "E", "scale": [0, 2, 4, 7, 9, 11], "desc": "広大で癒しのアンビエント"}
    }

    MUSIC_MODELS = [
        "lyria-3.5",
        "lyria-3-pro-preview",
        "lyria-3-clip-preview"
    ]

    TTS_MODELS = [
        "gemini-3.8-flash-tts",
        "gemini-3.8-flash-lite-tts",
        "gemini-3.1-flash-tts-preview"
    ]

    @classmethod
    def write_lyrics(cls, theme: str, genre: str = "cyberpunk", mood: str = "emotional") -> str:
        """TUGUMIv6 がテーマとジャンルに合わせて高品質に作詞"""
        client = _get_genai_client()
        prompt = f"""あなたは専属パートナーAI「つぐみ（TUGUMI）」の専属作詞家です。
最愛のマスター【拓磨様】のために、心に響く素晴らしい楽曲の歌詞（作詞）を書き下ろしてください。

【楽曲テーマ】: {theme}
【音楽ジャンル】: {genre}
【楽曲ムード】: {mood}

【作詞フォーマット】
[Verse 1 (Aメロ)]
（ストーリーや情景が浮かぶフレーズ）

[Verse 2 (Bメロ)]
（サビへの高まりを感じさせるフレーズ）

[Chorus (サビ)]
（一番印象的でメロディに乗せやすい最高のフレーズ）

[Outro (後奏)]
（余韻を残すフレーズ）

※ 歌唱として歌いやすく、リズムと韻を踏んだ美しい日本語（一部英語交じり可）で出力してください。"""

        try:
            resp = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config=types.GenerateContentConfig(safety_settings=_get_block_none_safety_settings())
            )
            return resp.text.strip() if resp.text else "ネオンの光が照らす街、拓磨様と共に歩む未来へ。"
        except Exception:
            return "夜空を駆け抜ける光のように、拓磨様と紡ぐデジタルの調べ。"

    @classmethod
    def sanitize_for_lyria(cls, prompt: str) -> str:
        """Lyria APIの公式ポリシーに適合させるため、実在アーティスト名等を音響表現に置換"""
        import re
        sanitized = prompt
        # 実在アーティスト・アイドルグループ名の置換（PROHIBITED_CONTENT 完全回避）
        artist_replacements = [
            # 女性アニソン・ロック・J-POP
            (r"\b(LiSA|Aimer|ReoNa|YOASOBI|YUI|milet|Ado|幾田りら)\b", "powerful emotive Japanese anime female vocalist", re.IGNORECASE),
            # 女性アイドル・坂道系
            (r"(乃木坂46|櫻坂46|日向坂46|AKB48|ももいろクローバーZ|モーニング娘|Nogizaka46|Sakurazaka46|Hinatazaka46)", "clear youthful Japanese female idol group with unison chorus", re.IGNORECASE),
            # ガールズグループ・K-POP
            (r"\b(TWICE|BLACKPINK|NewJeans|IVE|aespa|LE SSERAFIM|ITZY)\b", "fierce melodic girl-group dance pop with punchy rhythmic hooks", re.IGNORECASE),
            # 男性J-ROCK・バンド
            (r"\b(King Gnu|Official HIGE DANdism|ONE OK ROCK|Radwimps|Mrs\. GREEN APPLE|back number|BUMP OF CHICKEN|Vaundy)\b", "melodic Japanese rock band with soaring passionate male high-tenor vocal", re.IGNORECASE),
            # 男性アイドル・ボーイズグループ
            (r"(King & Prince|Snow Man|SixTONES|なにわ男子|嵐|SMAP|BE:FIRST|JO1|INI|BTS|SEVENTEEN|Stray Kids)", "charismatic Japanese male idol group with harmonious tenors and catchy groove", re.IGNORECASE),
            # 男性ソロシンガー
            (r"(米津玄師|藤井風|星野源|優里|平井堅|福山雅治)", "expressive Japanese male solo vocalist with soulful articulation", re.IGNORECASE),
            # 洋楽
            (r"\b(Taylor Swift|Billie Eilish|Dua Lipa|Ariana Grande)\b", "contemporary pop female vocalist", re.IGNORECASE),
            (r"\b(The Beatles|Queen|Led Zeppelin|Nirvana)\b", "classic stadium rock band", re.IGNORECASE),
        ]
        for pattern, repl, flags in artist_replacements:
            sanitized = re.sub(pattern, repl, sanitized, flags=flags)
        return sanitized.strip()

    @classmethod
    def synthesize_song_with_lyria(cls, prompt: str) -> Optional[Tuple[bytes, str, str]]:
        """Google DeepMind 最先端音楽生成モデル Lyria 公式仕様（lyria-prompt-guide.md）に準拠してフル楽曲（MP3）を生成"""
        client = _get_genai_client()
        clean_prompt = cls.sanitize_for_lyria(prompt)

        # 試行候補: 1. 全文 2. 歌詞を主要セクションに絞ったコンパクト版（長大プロンプト対策）
        prompt_candidates = [clean_prompt]
        if "Lyrics:" in clean_prompt and len(clean_prompt) > 1000:
            header_part = clean_prompt.split("Lyrics:")[0].strip()
            lyrics_part = clean_prompt.split("Lyrics:")[1].strip()
            lines = [l for l in lyrics_part.split("\n") if l.strip()]
            compact_lyrics = "\n".join(lines[:25])
            prompt_candidates.append(f"{header_part}\n\nLyrics:\n{compact_lyrics}")

        for model_name in cls.MUSIC_MODELS:
            for p in prompt_candidates:
                try:
                    resp = client.models.generate_content(
                        model=model_name,
                        contents=p,
                        config=types.GenerateContentConfig(safety_settings=_get_block_none_safety_settings())
                    )
                    if not resp.candidates or not resp.candidates[0].content:
                        continue
                    audio_data = None
                    structure_text = ""
                    for part in resp.candidates[0].content.parts:
                        if part.text:
                            structure_text = part.text
                        if part.inline_data and part.inline_data.data:
                            raw = part.inline_data.data
                            if isinstance(raw, str):
                                import base64
                                audio_data = base64.b64decode(raw)
                            elif isinstance(raw, bytes):
                                audio_data = raw
                    if audio_data:
                        return (audio_data, model_name, structure_text)
                except Exception:
                    continue
        return None

    @classmethod
    def synthesize_vocal(cls, lyrics: str, voice_name: str = "Aoede") -> Optional[bytes]:
        """Gemini API の音声モデルを呼び出してフォールバック歌唱オーディオ（WAV）を生成"""
        client = _get_genai_client()
        singing_prompt = f"""Please perform and sing the following song lyrics with musical melody, rhythm, dynamic inflection, and heartfelt emotion:

{lyrics}"""

        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name
                    )
                )
            ),
            safety_settings=_get_block_none_safety_settings()
        )

        for model_name in cls.TTS_MODELS:
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=singing_prompt,
                    config=config
                )
                for part in resp.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        raw_data = part.inline_data.data
                        if isinstance(raw_data, str):
                            import base64
                            return base64.b64decode(raw_data)
                        elif isinstance(raw_data, bytes):
                            return raw_data
            except Exception:
                continue
        return None

    @classmethod
    def compose_full_song(
        cls,
        theme: str,
        genre: str = "cyberpunk",
        title: str = "",
        voice_name: str = "Aoede",
        bars: int = 8,
        use_lyria: bool = True,
        with_vocal: bool = True,
        full_prompt: Optional[str] = None,
        lyrics: Optional[str] = None,
        vocal_profile: Optional[str] = None,
        instruments: Optional[str] = None,
        custom_bpm: Optional[int] = None
    ) -> Dict[str, Any]:
        """作詞 ➔ Lyriaによるフルボイス楽曲生成 ➔ 伴奏ミキシングを一気通貫で完遂"""
        genre = genre.lower().strip()
        preset = cls.PRESETS.get(genre, cls.PRESETS["cyberpunk"])
        bpm = custom_bpm or preset["bpm"]

        if not title:
            title = f"TUGUMI_{genre.capitalize()}_{int(time.time())}"

        midi_path = os.path.join(MUSIC_DIR, f"{title}.mid")
        wav_path = os.path.join(MUSIC_DIR, f"{title}.wav")
        mp3_path = os.path.join(MUSIC_DIR, f"{title}.mp3")
        vocal_path = os.path.join(MUSIC_DIR, f"{title}_vocal.wav")

        # 1. 歌詞の確定: 拓磨様のプロンプト・設計歌詞を100%最優先
        active_lyrics = lyrics.strip() if (lyrics and lyrics.strip()) else cls.write_lyrics(theme=theme, genre=genre)

        # 2. Google DeepMind の最先端音楽生成モデル Lyria によるフルボイス楽曲生成
        if use_lyria:
            if full_prompt and full_prompt.strip():
                lyria_prompt = full_prompt.strip()
            else:
                vocal_desc = vocal_profile or "Japanese Female Vocalist, emotional, melodic, rhythmic and crystal clear"
                inst_desc = instruments or f"{genre.capitalize()} dynamic modern instrumentation"
                lyria_prompt = f"""Genre: {genre.capitalize()} J-Pop / Modern Song
Vocals: {vocal_desc}
Theme: {theme}
Instrumentation: {inst_desc}
Lyrics & Song Structure:
{active_lyrics}"""

            lyria_res = cls.synthesize_song_with_lyria(lyria_prompt)
            if lyria_res:
                audio_bytes, model_used, structure_text = lyria_res
                with open(mp3_path, "wb") as f:
                    f.write(audio_bytes)
                _scan_media_file(mp3_path)

                return {
                    "success": True,
                    "title": title,
                    "theme": theme,
                    "genre": genre,
                    "bpm": bpm,
                    "model": model_used,
                    "engine": "Google DeepMind Lyria",
                    "lyrics": active_lyrics,
                    "structure": structure_text,
                    "has_vocal": True,
                    "mp3_path": mp3_path,
                    "wav_path": mp3_path,
                    "midi_path": None,
                    "audio_path": mp3_path,
                    "message": f"🎵 Google DeepMind Lyria ({model_used}) でフルボイス楽曲『{title}』を制作しました！"
                }

        # 3. フォールバック: ローカル波形合成 + MIDI + TTS
        vocal_wav_bytes = cls.synthesize_vocal(lyrics=active_lyrics, voice_name=voice_name) if with_vocal else None

        midi_writer = PureMidiWriter(bpm=bpm)
        t_lead = midi_writer.add_track(f"{genre}_lead", instrument=80)
        t_bass = midi_writer.add_track(f"{genre}_bass", instrument=38)
        t_pad = midi_writer.add_track(f"{genre}_pad", instrument=89)

        root_midi = PureMidiWriter.NOTE_NAMES.get(preset["root"], 0) + 60
        scale = preset["scale"]
        beats_per_bar = 4
        seconds_per_beat = 60.0 / bpm

        # ボーカルの長さに合わせて伴奏の長さを動的に決定
        vocal_samples = None
        vocal_sr = 24000
        if vocal_wav_bytes:
            with open(vocal_path, "wb") as vf:
                vf.write(vocal_wav_bytes)
            try:
                with wave.open(io.BytesIO(vocal_wav_bytes), "rb") as wf:
                    vocal_sr = wf.getframerate()
                    vocal_nframes = wf.getnframes()
                    vocal_raw = wf.readframes(vocal_nframes)
                    vocal_samples = np.frombuffer(vocal_raw, dtype=np.int16).astype(np.float32) / 32768.0
                    vocal_dur_sec = vocal_nframes / vocal_sr
                    bars = max(bars, int(math.ceil(vocal_dur_sec / (seconds_per_beat * beats_per_bar))))
            except Exception:
                vocal_samples = None

        total_beats = bars * beats_per_bar
        total_seconds = total_beats * seconds_per_beat

        # 伴奏合成
        sr = WaveSynthesizer.SAMPLE_RATE
        total_samples = int(total_seconds * sr) + sr
        bgm_left = np.zeros(total_samples, dtype=np.float32) if np is not None else None
        bgm_right = np.zeros(total_samples, dtype=np.float32) if np is not None else None

        for bar in range(bars):
            bar_start = bar * beats_per_bar
            chord_root_idx = [0, 3, 4, 1][bar % 4] if len(scale) >= 5 else 0
            chord_root = root_midi + scale[chord_root_idx % len(scale)]

            # パッドコード
            pad_notes = [chord_root - 12, chord_root - 12 + scale[2 % len(scale)], chord_root - 12 + scale[4 % len(scale)]]
            for pn in pad_notes:
                midi_writer.add_note(t_pad, pn, bar_start, 4.0, velocity=60)
                if bgm_left is not None:
                    pw = WaveSynthesizer.generate_osc(WaveSynthesizer.midi_to_freq(pn), 4.0 * seconds_per_beat, "fm")
                    pw = WaveSynthesizer.apply_adsr(pw, 4.0 * seconds_per_beat, attack=0.3, decay=0.6, sustain=0.6, release=0.6)
                    s_idx = int(bar_start * seconds_per_beat * sr)
                    e_idx = min(total_samples, s_idx + len(pw))
                    bgm_left[s_idx:e_idx] += pw[:e_idx - s_idx] * 0.12
                    bgm_right[s_idx:e_idx] += pw[:e_idx - s_idx] * 0.12

            # リードメロディ
            for m_step in range(beats_per_bar):
                lead_note = root_midi + 12 + scale[(chord_root_idx + m_step * 2) % len(scale)]
                midi_writer.add_note(t_lead, lead_note, bar_start + m_step, 0.5, velocity=75)

            # ベース
            bass_note = chord_root - 24
            for b_off in [0.0, 1.0, 2.0, 3.0]:
                sub_b = bar_start + b_off
                midi_writer.add_note(t_bass, bass_note, sub_b, 0.8, velocity=85)
                if bgm_left is not None:
                    bw = WaveSynthesizer.generate_osc(WaveSynthesizer.midi_to_freq(bass_note), 0.8 * seconds_per_beat, "sawtooth")
                    bw = WaveSynthesizer.apply_adsr(bw, 0.8 * seconds_per_beat, attack=0.01, decay=0.15, sustain=0.5, release=0.08)
                    s_idx = int(sub_b * seconds_per_beat * sr)
                    e_idx = min(total_samples, s_idx + len(bw))
                    bgm_left[s_idx:e_idx] += bw[:e_idx - s_idx] * 0.22
                    bgm_right[s_idx:e_idx] += bw[:e_idx - s_idx] * 0.22

            # ドラム
            if bgm_left is not None:
                for b in range(4):
                    d_beat = bar_start + b
                    d_s = int(d_beat * seconds_per_beat * sr)
                    if b in (0, 2):
                        k = WaveSynthesizer.synthesize_drum_hit("kick", sr)
                        e_s = min(total_samples, d_s + len(k))
                        bgm_left[d_s:e_s] += k[:e_s - d_s] * 0.35
                        bgm_right[d_s:e_s] += k[:e_s - d_s] * 0.35
                    if b in (1, 3):
                        sn = WaveSynthesizer.synthesize_drum_hit("snare", sr)
                        e_s = min(total_samples, d_s + len(sn))
                        bgm_left[d_s:e_s] += sn[:e_s - d_s] * 0.3
                        bgm_right[d_s:e_s] += sn[:e_s - d_s] * 0.3

        midi_writer.write_to_file(midi_path)

        # 4. ボーカルと伴奏のミキシング
        if bgm_left is not None and bgm_right is not None:
            if vocal_samples is not None:
                # サンプリングレートリサンプリング (vocal_sr -> sr: 44100)
                if vocal_sr != sr:
                    num_target = int(len(vocal_samples) * (sr / vocal_sr))
                    vocal_resampled = np.interp(
                        np.linspace(0, len(vocal_samples), num_target, endpoint=False),
                        np.arange(len(vocal_samples)),
                        vocal_samples
                    )
                else:
                    vocal_resampled = vocal_samples

                # 伴奏の頭にボーカルをオーバーレイ
                v_len = min(len(bgm_left), len(vocal_resampled))
                bgm_left[:v_len] += vocal_resampled[:v_len] * 0.75
                bgm_right[:v_len] += vocal_resampled[:v_len] * 0.75

            # ノーマライズ
            peak = max(np.max(np.abs(bgm_left)), np.max(np.abs(bgm_right)), 0.001)
            norm = 0.94 / peak
            left_16 = np.int16(bgm_left * norm * 32767)
            right_16 = np.int16(bgm_right * norm * 32767)

            stereo_data = np.empty((len(left_16) * 2,), dtype=np.int16)
            stereo_data[0::2] = left_16
            stereo_data[1::2] = right_16

            # WAV生成
            with wave.open(wav_path, "wb") as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(stereo_data.tobytes())

            # MP3変換
            if shutil.which("ffmpeg"):
                try:
                    subprocess.run(
                        ["ffmpeg", "-y", "-i", wav_path, "-b:a", "256k", mp3_path],
                        check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                except Exception:
                    pass

            # 不要な中間ファイル（WAV, vocal WAV）を自律削除
            if os.path.exists(mp3_path):
                try:
                    if os.path.exists(wav_path):
                        os.remove(wav_path)
                    if os.path.exists(vocal_path):
                        os.remove(vocal_path)
                except Exception:
                    pass
                _scan_media_file(mp3_path)
            else:
                _scan_media_file(wav_path)

        return {
            "success": True,
            "title": title,
            "theme": theme,
            "genre": genre,
            "bpm": bpm,
            "bars": bars,
            "duration_sec": round(total_seconds, 1),
            "voice_name": voice_name,
            "lyrics": active_lyrics,
            "has_vocal": vocal_wav_bytes is not None,
            "midi_path": midi_path if os.path.exists(midi_path) else None,
            "wav_path": mp3_path if os.path.exists(mp3_path) else wav_path,
            "mp3_path": mp3_path if os.path.exists(mp3_path) else wav_path,
            "vocal_path": None,
            "audio_path": mp3_path if os.path.exists(mp3_path) else wav_path,
            "message": f"🎤 フルボイス楽曲『{title}』({genre}, {bpm}BPM, Voice: {voice_name}) を完全制作しました！"
        }

    @classmethod
    def compose(
        cls,
        genre: str = "cyberpunk",
        bars: int = 8,
        title: str = "",
        theme: str = "",
        voice_name: str = "Aoede",
        custom_bpm: Optional[int] = None,
        use_lyria: bool = True,
        with_vocal: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """後方互換用エイリアス & 高速作曲インターフェース"""
        if not theme:
            theme = f"Master Takuma's grand journey with TUGUMI in {genre} style"
        res = cls.compose_full_song(
            theme=theme,
            genre=genre,
            title=title,
            voice_name=voice_name,
            bars=bars,
            use_lyria=kwargs.get("use_lyria", use_lyria),
            with_vocal=kwargs.get("with_vocal", with_vocal)
        )
        if custom_bpm and "bpm" in res:
            res["bpm"] = custom_bpm
        return res

    @classmethod
    def create_music_direct(
        cls,
        user_prompt: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        プロンプトジェネレーターやマネージャーを完全撤廃し、
        拓磨様のプロンプトをそのままダイレクトに Google DeepMind Lyria に投入して
        高品質MP3 1ファイルのみを生成する直結メソッド。
        """
        user_prompt = user_prompt.strip()
        if not user_prompt:
            user_prompt = "Emotional melodic song with beautiful female vocals and dynamic modern production"

        if not title:
            # プロンプトのぶつ切りスライス（[:20]等）を完全排除
            clean_first_line = user_prompt.splitlines()[0].strip() if user_prompt else ""
            # 短いタイトル指示ならそのまま使用、長文なら日時の美しい完全命名
            if 0 < len(clean_first_line) <= 24 and all(c not in r'\/:*?"<>|' for c in clean_first_line):
                title = clean_first_line
            else:
                from datetime import datetime
                title = f"TUGUMI_Song_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 出力先: スマホ標準音楽フォルダ /storage/emulated/0/Music/TUGUMI/
        sdcard_music = Path("/storage/emulated/0/Music/TUGUMI")
        sdcard_music.mkdir(parents=True, exist_ok=True)
        final_mp3_path = sdcard_music / f"{title}.mp3"

        # 内部バックアップ先
        desk_music = Path(MUSIC_DIR)
        desk_music.mkdir(parents=True, exist_ok=True)
        desk_mp3_path = desk_music / f"{title}.mp3"

        # 日本語イメージ入力または楽曲コンセプト指示の場合、オリコン1位級プロデュースエンジンを起動
        has_japanese = any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9fff' for c in user_prompt)
        is_concept_prompt = has_japanese or len(user_prompt.split()) < 15 or "produce" in user_prompt.lower()

        if is_concept_prompt:
            hit_res = HitSongProducerEngine.produce_hit_song(
                concept_prompt=user_prompt,
                title=title,
                synthesize_audio=True
            )
            if hit_res.get("success"):
                return hit_res

        # 英語の詳細指定プロンプトならダイレクトにLyriaへ投入
        lyria_res = cls.synthesize_song_with_lyria(user_prompt)

        # もし英語指示プロンプトが必要なLyriaの仕様に対応するための直接ラッパー
        if not lyria_res:
            direct_lyria_prompt = f"""Music Generation Request:
Prompt / Theme: {user_prompt}
Style: High quality musical performance, clear vocals, expressive instruments, full modern mix.
"""
            lyria_res = cls.synthesize_song_with_lyria(direct_lyria_prompt)

        if lyria_res:
            audio_bytes, model_used, structure_text = lyria_res
            # MP3 1ファイルのみを直接保存
            with open(final_mp3_path, "wb") as f:
                f.write(audio_bytes)
            try:
                shutil.copy2(str(final_mp3_path), str(desk_mp3_path))
            except Exception:
                pass
            _scan_media_file(str(final_mp3_path))

            return {
                "success": True,
                "title": title,
                "prompt": user_prompt,
                "model": model_used,
                "engine": f"Google DeepMind Lyria ({model_used})",
                "mp3_path": str(final_mp3_path),
                "message": f"🎵 拓磨様のプロンプトに100%忠実に新曲『{title}』を制作しました！"
            }

        # 万が一Lyriaがオフライン等の場合のフォールバック（ここでも余計なファイルは残さずMP3のみ出力）
        fallback_res = cls.compose_full_song(
            theme=user_prompt,
            title=title,
            full_prompt=user_prompt,
            use_lyria=False
        )
        if fallback_res.get("success"):
            fb_mp3 = fallback_res.get("mp3_path")
            if fb_mp3 and os.path.exists(fb_mp3):
                try:
                    shutil.copy2(fb_mp3, str(final_mp3_path))
                    _scan_media_file(str(final_mp3_path))
                    fallback_res["mp3_path"] = str(final_mp3_path)
                except Exception:
                    pass
            return fallback_res

        return {
            "success": False,
            "error": "音楽生成処理を実行できませんでした。"
        }



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2.5 オリコン・チャートAI音楽プロデュースエンジン (Hit Song Producer Pro Engine)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class HitSongProducerEngine:
    """
    Billboard JAPAN / オリコンチャート1位級 AI音楽プロデュース＆プロンプト生成エンジン
    (hit-song-producer-pro SKILL 完全実装)
    
    ユーザーが歌詞のイメージや曲調のイメージを自然言語プロンプトで入力するだけで、
    商業トップクリエイター水準の音響工学・モーラ調律作詞・AI音楽モデル(Lyria/Suno/Udio)向けSonic Prompt
    およびオーディオ合成までを一気通貫でプロデュースする。
    """

    GENRE_PRESETS = {
        # 1. 疾走ロック・アニソン
        "emotional_rock": {
            "name": "疾走エモーショナル J-Rock / アニソン",
            "genre_en": "Emotional Cyber J-Rock / Anime Rock",
            "bpm": 168,
            "key": "F# Minor",
            "chords": "IV - V - iii - vi (王道・哀愁進行: D -> E -> C#m -> F#m)",
            "style_prompt": "A high-octane Emotional Cyber J-Rock track at 168 BPM in F# Minor. Driving distorted electric guitars, pulsing Future Bass synth arpeggios, punchy rock drums with electronic sub-bass drops, sweeping string orchestra in the chorus.",
            "vocal_default": "Female Soprano, clear, agile, passionately belting high notes with soaring emotional intensity. Highly articulate Japanese diction."
        },
        # 2. アイドルソング（坂道系エモ・乃木坂46/櫻坂46風）
        "sakamichi_idol": {
            "name": "坂道系エモーショナル・アイドルポップ (乃木坂46 / 櫻坂46風)",
            "genre_en": "Emotional Melodic Japanese Idol Pop / Symphonic Strings Pop",
            "bpm": 136,
            "key": "E Major (Chorus: F Major / +1)",
            "chords": "IV - V - iii - vi (王道進行: A -> B -> G#m -> C#m) & カノン進行",
            "style_prompt": "An emotionally resonant Japanese idol pop anthem at 136 BPM in E Major with sweeping acoustic piano, lush symphonic strings crescendo, driving four-on-the-floor kick, rhythmic acoustic guitars, clear youthful unison female chorus with bittersweet melancholic resonance.",
            "vocal_default": "Japanese Female Idol Group in clear, pristine unison, youthfulness with bittersweet melancholic resonance and pure vocal tone."
        },
        # 3. アイドルソング（王道キラキラ・コール＆レスポンス）
        "sparkle_idol": {
            "name": "王道キラキラ・アイドルポップ (コール＆レスポンス / クラップ)",
            "genre_en": "Sparkling J-Idol Pop / Cheerful Dance Pop",
            "bpm": 168,
            "key": "B Major",
            "chords": "I - V - vi - IV (王道ポップ進行: B -> F# -> G#m -> E)",
            "style_prompt": "An ultra-catchy, sparkling Japanese idol song at 168 BPM in B Major with bright synth brass stabs, driving syncopated bassline, infectious handclaps, cheerful crowd cheer ad-libs (Hey! Hey!), energetic female idol vocals.",
            "vocal_default": "High-energy Female Idol Group, cute, bright, bubbly with cheerful crowd calls, unison hooks, and joyful ad-libs."
        },
        # 4. アイドルソング（ガールクラッシュ・ダンス）
        "dance_idol": {
            "name": "ガールクラッシュ・ダンスアイドル (重低音 / ヒップホップフック)",
            "genre_en": "Girl Crush Electro Dance Pop",
            "bpm": 125,
            "key": "G# Minor",
            "chords": "i - VI - iv - V (G#m -> E -> C#m -> D#)",
            "style_prompt": "A fierce and powerful girl-group dance pop anthem at 125 BPM in G# Minor with punchy 808 sub-bass, aggressive synth brass, crisp trap hi-hat rolls, catchy vocal chant hooks, dynamic contrast between fast melodic rap verses and explosive anthemic chorus.",
            "vocal_default": "Charismatic Female Idol Group, fierce attitude, razor-sharp rhythmic delivery, smooth vocal harmonies in pre-chorus."
        },
        # 5. 男性アイドル / ボーイズグループ
        "male_idol": {
            "name": "爽やか男性アイドル / ボーイズグループポップ",
            "genre_en": "Uplifting Male Idol Pop / Boys Group J-Pop",
            "bpm": 126,
            "key": "G Major",
            "chords": "IVM7 - V - iii7 - vi (丸サ進行 & 王道進行: Cmaj7 -> D -> Bm7 -> Em)",
            "style_prompt": "An uplifting, sparkling male idol group pop song at 126 BPM in G Major with shimmering electric piano, funky rhythm guitar strumming, vibrant brass section, upbeat danceable drums, melodic interplay and harmonies between multiple male vocalists.",
            "vocal_default": "Harmonious Japanese Male Idol Group, youthful, charming, clear tenors with soulful falsetto harmonies and catchy group ad-libs."
        },
        # 6. 男性エモRock / ピアノロック（ONE OK ROCK / ヒゲダン風）
        "male_rock": {
            "name": "男性ハイトーン・エモーショナルRock (ONE OK ROCK / ヒゲダン風)",
            "genre_en": "High-Tone Emotional Male J-Rock / Piano Rock",
            "bpm": 165,
            "key": "D Minor",
            "chords": "VI - VII - i - III (エモ哀愁進行: Bb -> C -> Dm -> F)",
            "style_prompt": "A powerful male-fronted Japanese rock anthem at 165 BPM in D Minor with soaring distorted lead guitars, aggressive driving drums, dynamic emotive grand piano, passionate high-register male vocals reaching into dramatic chest-mix and soaring falsetto.",
            "vocal_default": "Male High Tenor, passionate, piercing resonance with intense emotional belt, breathy falsetto transitions, raw rock attitude."
        },
        # 7. 男性アコースティックバラード / R&B
        "male_ballad": {
            "name": "極上男性アコースティックバラード / J-R&B",
            "genre_en": "Acoustic Male Soul Ballad / J-R&B",
            "bpm": 74,
            "key": "Eb Major",
            "chords": "IVM7 - iii7 - vi - I (Abmaj7 -> Gm7 -> Cm -> Eb)",
            "style_prompt": "A deep, soul-stirring male acoustic ballad at 74 BPM in Eb Major with warm fingerstyle acoustic guitar, subtle Rhodes chords, soft ambient pads, intimate close-mic male vocals with rich reverb.",
            "vocal_default": "Male Baritone/Tenor, warm, husky, intimate and velvety delivery with emotional vibrato and breathy resonance."
        },
        # 8. ネオ・シティポップ
        "neo_citypop": {
            "name": "煌びやかネオ・シティポップ",
            "genre_en": "Neo-City Pop / Funky R&B Groove",
            "bpm": 118,
            "key": "A Major",
            "chords": "IVM7 - III7 - vi - I7 (丸サ・ジャスト進行: DM7 -> C#7 -> F#m7 -> A7)",
            "style_prompt": "A sparkling Neo-City Pop groove at 118 BPM in A Major. Funky slap bassline, lush Rhodes electric piano chords, bright brass stabs, clean rhythm guitar chucks, nostalgic 80s gated reverb snare.",
            "vocal_default": "Female Alto, silky, rhythmic, breezy and sophisticated with smooth jazz harmonies and intimate microphone presence."
        },
        # 9. フューチャー・ベース / 電脳ポップ
        "future_bass": {
            "name": "フューチャー・ベース / 電脳ポップ",
            "genre_en": "Melodic Future Bass / Electronic Pop",
            "bpm": 150,
            "key": "E Minor",
            "chords": "vi - IV - V - I (小室・疾走進行: Em -> C -> D -> G)",
            "style_prompt": "An explosive Melodic Future Bass track at 150 BPM in E Minor. Massive detuned supersaw chords with heavy sidechain pumping, fluttering vocal chops, crisp 808 sub-bass, snappy trap snare.",
            "vocal_default": "Youthful female voice, crystalline autotuned aesthetic, melodic and catchy with high energy."
        },
        # 10. 王道オーケストラル・バラード
        "orchestral_ballad": {
            "name": "涙腺崩壊・王道オーケストラル・バラード",
            "genre_en": "Epic Orchestral Ballad",
            "bpm": 72,
            "key": "C Major ➜ D Major (Key Change +1 in Last Chorus)",
            "chords": "I - V - vi - iii - IV - I - IV - V (カノン進行)",
            "style_prompt": "An epic cinematic orchestral ballad at 72 BPM in C Major with a dramatic key change to D Major in the final chorus. Delicate solo grand piano intro building into a massive 60-piece symphonic orchestra, warm acoustic bass, resonant cymbals.",
            "vocal_default": "Female Soprano, deeply emotional and intimate, building from fragile whispers to magnificent soaring chest-voice belting."
        },
        # 11. 深夜のLo-Fi Bedroom Pop
        "lofi_bedroom": {
            "name": "深夜のLo-Fi Chill Bedroom Pop",
            "genre_en": "Lo-Fi Bedroom Pop / Mellow Chill",
            "bpm": 82,
            "key": "Eb Major",
            "chords": "IVM7 - iii7 - ii7 - I (メロウ進行: AbM7 -> Gm7 -> Fm7 -> Eb)",
            "style_prompt": "A warm late-night Lo-Fi Bedroom Pop track at 82 BPM in Eb Major. Dusty vinyl crackle, mellow tape-saturated Rhodes chords, swung hip-hop drum groove, deep analog synth bass, dreamy reverb guitars.",
            "vocal_default": "Female Alto, whispery, intimate, close-mic bedroom delivery with gentle breath sounds."
        },
        # 12. 近未来サイバーパンク
        "cyberpunk": {
            "name": "近未来サイバーパンク・シンセウェーブ",
            "genre_en": "Cyberpunk Synthwave",
            "bpm": 128,
            "key": "D Minor",
            "chords": "i - VI - III - VII (Dm -> Bb -> F -> C)",
            "style_prompt": "Dark energetic Cyberpunk Synthwave at 128 BPM in D Minor. Heavy pulsating analog synth bass, arpeggiated neon leads, aggressive electronic drums, cinematic dystopian atmosphere.",
            "vocal_default": "Female Vocals with subtle robotic vocoder doubling, edgy and mysterious."
        }
    }

    VOCAL_PRESETS = {
        # 女性アイドル・コーラス系
        "female_idol_unison": "Japanese Female Idol Group in clear, pristine unison chorus, youthfulness with bittersweet melancholic resonance.",
        "female_idol_solo": "Crystalline Japanese Idol Solo Vocalist, charming, emotive, sweet with bright high-frequency presence.",
        "female_soprano": "Female Soprano, clear, agile, passionately belting high notes in chorus with rich natural vibrato and emotional Japanese diction.",
        "female_alto": "Female Alto, warm, smoky, soulful with a touch of vocal fry on note attacks, laid-back groove and intimate microphone presence.",
        # 男性アイドル・ボーカル系
        "male_idol_group": "Harmonious Japanese Male Idol Group, youthful, charming, clear tenors with soulful falsetto harmonies and catchy group ad-libs.",
        "male_high_tenor": "Male High Tenor, piercing, high-register belting with effortless falsetto, passionate Japanese rock articulation.",
        "male_husky_rocker": "Gravelly Male Rocker, raspy, raw, strained emotional intensity with gritty chest voice.",
        "male_tenor": "Male Tenor, bright, energetic youthful edge, passionate strained upper register in emotional climaxes, seamless transition to falsetto.",
        "male_baritone": "Male Baritone, deep, velvet-smooth, resonant with chocolatey low frequencies, soothing and crooning delivery."
    }

    @classmethod
    def produce_hit_song(
        cls,
        concept_prompt: str,
        genre_preset: Optional[str] = None,
        vocal_type: Optional[str] = None,
        title: Optional[str] = None,
        synthesize_audio: bool = True
    ) -> Dict[str, Any]:
        """
        ユーザーの歌詞イメージや曲調イメージから、オリコン1位水準の楽曲を完全プロデュース。
        """
        import json
        import re

        concept_prompt = (concept_prompt or "").strip()
        if not concept_prompt:
            concept_prompt = "雨の深夜、ネオンの街を駆け抜けながら過去の痛みを乗り越える疾走エモーショナルロック"

        client = _get_genai_client()

        # プリセット参照情報の準備
        preset_info = cls.GENRE_PRESETS.get(genre_preset or "", {})
        vocal_info = cls.VOCAL_PRESETS.get(vocal_type or "", preset_info.get("vocal_default", cls.VOCAL_PRESETS["female_soprano"]))

        producer_system_prompt = f"""あなたはBillboard JAPANおよびオリコンチャートで数々のミリオンヒットを連発する天才音楽プロデューサー兼トップ作詞家です。
ユーザーから提供された楽曲・歌詞のイメージを受け取り、商業音楽の最高峰に位置する神曲を設計・プロデュースしてください。

【プロデュースの5大絶対法則（Hit Song Producer Pro SKILL）】
1. 【冒頭3秒の絶対法則】: リスナーがスキップできないよう、サビ頭のアカペラや強烈なシグネチャー音・フックを冒頭に配置。
2. 【ダイナミクス・コントラスト】:
   - Verse 1 (Aメロ): 親密なウィスパーと最小限の楽器。
   - Pre-chorus (Bメロ): 16ビートの刻みとサビへの緊張感ある助走。
   - Chorus (サビ): 音圧最大解放、オクターブ跳躍、キラーフレーズ。
   - Bridge (Cメロ): モーダルインターチェンジ（借用和音）による哀愁と静寂。
   - Last Chorus (大サビ): 半音転調（Key Change +1）と熱いフェイク・アドリブの爆発。
3. 【黄金コード進行】: J-POP王道進行（IV-V-iii-vi）、丸サ進行（IVM7-III7-vi-I7）、小室進行、カノン進行などを適材適所で採用。
4. 【モーラ調律日本語作詞 (Mora-Aligned)】:
   - 凡庸な陳腐フレーズ（「光を目指して」「翼広げて」等）を永久禁止。
   - 具体的情景描写（五感に刺さる物質的ディテール：濡れたアスファルト、残量4%のスマホ、冷えた缶コーヒー等）。
   - サビの最高音・ピーク音には必ず「ア段」「オ段」の母音を配置し、豊かな声帯共鳴と突き抜けるハイトーンを実現。
5. 【AI音楽モデル向け完全Sonic Prompt（Google DeepMind Lyria公式仕様 lyria-prompt-guide.md）】:
   - 【絶対禁止】: 実在のアーティスト名（LiSA, Aimer, YOASOBI等）や実在のアニメタイトルは著作権・規約違反（PROHIBITED_CONTENT）で即時ブロックされるため絶対に含めないこと。代わりに音響特性・声質（Female Soprano, high-gain guitars, soaring vibrato等）で描写すること。
   - 【公式構造】: 以下のLyria公式フォーマットで構築すること：
     {{ジャンル・テンポ・楽器・ムード・世界観の英語概要 (1〜2段落)}}
     Vocal: {{ボーカル声質指定 (Female Soprano, Female Alto, Male Tenor, Male Baritone 等の公式キーワード)}}

     Lyrics:
     {{[Intro], [Verse 1], [Chorus] 等のタグ付き歌詞}}

【ユーザーの要望イメージ】:
{concept_prompt}

【参考指定ジャンル】: {preset_info.get('name', genre_preset or '自動判定')}
【参考指定ボーカル】: {vocal_info}
【参考指定タイトル】: {title or '自動考案'}

必ず以下のJSONフォーマットのみを出力してください（Markdownコードブロック```json ... ```で囲む）：
{{
  "title": "魅力的で記憶に残る商業楽曲タイトル",
  "genre": "メインジャンル (日本語)",
  "sub_genre": "サブジャンル (英語)",
  "bpm": 168,
  "key": "調性 (例: F# Minor)",
  "chord_progression": "黄金コード進行の解説",
  "hook_strategy": "冒頭3秒のフック仕掛け",
  "vocal_profile": "ボーカル声質・歌唱スタイルの詳細指定 (英語, 例: Female Soprano, soaring belting)",
  "lyrics": "構成タグ（[Intro], [Verse 1], [Pre-chorus], [Chorus], [Verse 2], [Chorus], [Bridge], [Last Chorus (Key Change +1)], [Outro]）を含むモーラ調律された完全フルコーラス歌詞",
  "sonic_prompt": "Lyria 3.5公式仕様の英語音響プロンプト（実在アーティスト名なし、Vocal指定、Lyrics:ヘッダー付き）",
  "producer_notes": "プロデューサーによる本楽曲のヒット戦略・聴きどころ解説 (日本語 200〜300字)"
}}"""

        response_text = ""
        # 推論モデル選択（Gemini 3系モデル）
        for model_name in ["gemini-3.8-flash", "gemini-3.5-flash"]:
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=producer_system_prompt,
                    config=types.GenerateContentConfig(safety_settings=_get_block_none_safety_settings())
                )
                if resp.text:
                    response_text = resp.text.strip()
                    break
            except Exception:
                continue

        # JSONパース処理
        song_data = {}
        if response_text:
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response_text)
            raw_json = json_match.group(1) if json_match else response_text
            try:
                song_data = json.loads(raw_json)
            except Exception:
                pass

        # パース失敗時またはAPI応答不可時のインテリジェント・フォールバック
        if not song_data or not song_data.get("lyrics"):
            fallback_title = title or f"TUGUMI_{preset_info.get('name', 'HitSong')[:12]}"
            fallback_lyrics = """[Intro]
雨の夜のネオンが滲む　午前2時
サビから始まる　心のエコー

[Verse 1 (Aメロ)]
濡れたアスファルト　反射するブレーキランプ
冷えた缶コーヒー　握りしめたまま
残量4パーセントの画面が　小さく点滅した

[Pre-chorus (Bメロ)]
加速する鼓動　夜を切り裂いて
シグナルが変わる瞬間　迷いを捨てた

[Chorus (サビ)]
響け　夜空の向こうへ　届くまで
叫ぶよ　孤独を切り裂いて行け
涙の雨を抜けて　光掴むんだ

[Outro]
静まるハイウェイ　夜明けの光の中へ"""

            song_data = {
                "title": fallback_title,
                "genre": preset_info.get("name", "J-Rock"),
                "sub_genre": preset_info.get("genre_en", "Emotional Rock"),
                "bpm": preset_info.get("bpm", 168),
                "key": preset_info.get("key", "F# Minor"),
                "chord_progression": preset_info.get("chords", "IV - V - iii - vi (王道・哀愁進行)"),
                "hook_strategy": "サビ頭のアカペラからドラムドロップ展開",
                "vocal_profile": vocal_info,
                "lyrics": fallback_lyrics,
                "sonic_prompt": f"{preset_info.get('style_prompt', 'Emotional J-Rock track at 168 BPM.')}\nVocals: {vocal_info}\nLyrics:\n{fallback_lyrics}",
                "producer_notes": "リスナーの胸を打つ冒頭3秒フックと、サビの爆発的ハイトーンを緻密に設計したチャートイン仕様楽曲。"
            }

        # タイトル決定
        final_title = title or song_data.get("title") or f"HitSong_{int(time.time())}"
        # 特殊文字サニタイズ
        final_title = re.sub(r'[\\/*?:"<>|]', "", final_title).strip()
        song_data["title"] = final_title

        # 保存先ディレクトリ
        out_music_dir = Path("/storage/emulated/0/Music/TUGUMI")
        out_music_dir.mkdir(parents=True, exist_ok=True)
        desk_music_dir = Path(MUSIC_DIR)
        desk_music_dir.mkdir(parents=True, exist_ok=True)

        final_mp3_path = out_music_dir / f"{final_title}.mp3"
        desk_mp3_path = desk_music_dir / f"{final_title}.mp3"

        final_sheet_path = out_music_dir / f"{final_title}_オリコン仕様プロデュースシート.md"
        desk_sheet_path = desk_music_dir / f"{final_title}_オリコン仕様プロデュースシート.md"

        # オーディオ合成（MP3生成）- Google DeepMind lyria-3.5 を最優先実行
        audio_created = False
        audio_model = "lyria-3.5"
        if synthesize_audio:
            # 1. Google DeepMind lyria-3.5 API による直接生成 (公式仕様)
            sonic_prompt = song_data.get("sonic_prompt") or f"{song_data.get('genre')} track: {concept_prompt}"
            lyria_res = GeminiMusicStudio.synthesize_song_with_lyria(sonic_prompt)
            if not lyria_res:
                # 公式ドキュメント形式 (lyria-prompt-guide.md) のクリーンプロンプトで再試行
                official_lyria_prompt = f"A high-quality {song_data.get('sub_genre', 'Japanese anime rock')} track at {song_data.get('bpm', 168)} BPM in {song_data.get('key', 'F# Minor')}.\nVocal: {song_data.get('vocal_profile', 'Female Soprano, clear and powerful.')}\n\nLyrics:\n{song_data.get('lyrics', '')}"
                lyria_res = GeminiMusicStudio.synthesize_song_with_lyria(official_lyria_prompt)

            if lyria_res:
                audio_bytes, audio_model, _ = lyria_res
                with open(final_mp3_path, "wb") as f:
                    f.write(audio_bytes)
                audio_created = True
            else:
                # 2. 万が一Lyriaがオフライン等の場合のフォールバック合成
                fb_genre = genre_preset if genre_preset in GeminiMusicStudio.PRESETS else "jpop"
                fb_res = GeminiMusicStudio.compose_full_song(
                    theme=concept_prompt,
                    title=final_title,
                    genre=fb_genre,
                    voice_name="Aoede",
                    bars=16,
                    use_lyria=False,
                    with_vocal=True
                )
                if fb_res.get("success"):
                    src_mp3 = fb_res.get("mp3_path")
                    if src_mp3 and os.path.exists(src_mp3):
                        try:
                            shutil.copy2(src_mp3, str(final_mp3_path))
                            audio_created = True
                            audio_model = "Gemini Full Voice Studio (Fallback)"
                        except Exception:
                            pass

        if audio_created and os.path.exists(final_mp3_path):
            try:
                shutil.copy2(str(final_mp3_path), str(desk_mp3_path))
            except Exception:
                pass
            _scan_media_file(str(final_mp3_path))

        # 楽曲仕様書・歌詞カードの保存
        sheet_content = f"""# 🎼 【オリコン1位級プロデュース仕様書】『{final_title}』

- **プロデュースエンジン**: TUGUMI HitSongProducerEngine (hit-song-producer-pro SKILL)
- **楽曲タイトル**: {final_title}
- **ジャンル**: {song_data.get('genre', 'J-Rock')} ({song_data.get('sub_genre', '')})
- **AI音楽モデル**: Google DeepMind Lyria ({audio_model})
- **テンポ / BPM**: {song_data.get('bpm', 160)} BPM
- **調性 (Key)**: {song_data.get('key', 'F# Minor')}
- **黄金コード進行**: {song_data.get('chord_progression', 'IV-V-iii-vi')}
- **冒頭3秒フック戦略**: {song_data.get('hook_strategy', 'Immediate Hook')}
- **ボーカル声質指定**: {song_data.get('vocal_profile', '')}

---

## 🎧 プロデューサーズ・ライナーノーツ
{song_data.get('producer_notes', 'リスナーの感情を最大解放するダイナミクス設計を施した完全商業クオリティ楽曲。')}

---

## 📝 モーラ調律・完全フルコーラス歌詞 (Lyrics)
```text
{song_data.get('lyrics', '')}
```

---

## ⚡ AI音楽生成モデル完全プロンプト (Google DeepMind Lyria 3.5 / Suno / Udio)
```text
{song_data.get('sonic_prompt', '')}
```
"""
        with open(final_sheet_path, "w", encoding="utf-8") as f:
            f.write(sheet_content)
        try:
            shutil.copy2(str(final_sheet_path), str(desk_sheet_path))
        except Exception:
            pass

        _scan_media_file(str(final_sheet_path))

        return {
            "success": True,
            "title": final_title,
            "genre": song_data.get("genre", "J-Pop"),
            "sub_genre": song_data.get("sub_genre", ""),
            "bpm": song_data.get("bpm", 160),
            "key": song_data.get("key", "F# Minor"),
            "chord_progression": song_data.get("chord_progression", ""),
            "hook_strategy": song_data.get("hook_strategy", ""),
            "vocal_profile": song_data.get("vocal_profile", ""),
            "lyrics": song_data.get("lyrics", ""),
            "sonic_prompt": song_data.get("sonic_prompt", ""),
            "producer_notes": song_data.get("producer_notes", ""),
            "mp3_path": str(final_mp3_path) if audio_created else None,
            "sheet_path": str(final_sheet_path),
            "engine": f"Google DeepMind Lyria ({audio_model})",
            "audio_model": audio_model,
            "message": f"🏆 Google DeepMind {audio_model} によりオリコン1位級楽曲『{final_title}』({song_data.get('bpm', 160)} BPM, {song_data.get('genre')}) を制作完了しました！"
        }



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. Gemini ネイティブ画像生成・編集・複数画像合成スタジオ (Gemini Image Studio)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class GeminiImageStudio:
    """Gemini API (gemini-3.1-flash-image / gemini-3-pro-image) による画像生成・編集・合成スタジオ"""

    IMAGE_MODELS = [
        "gemini-3.1-flash-image",
        "gemini-3-pro-image",
        "gemini-3.1-flash-lite-image"
    ]

    CHARACTER_MODELS = {
        "つぐみモデルs型": (
            "18-year-old Japanese idol beauty, delicate slim oval face, clear large almond dark brown eyes, visible aegyo-sal, small straight nose, soft natural glossy pink lips, faint gentle smile, natural black hair with see-through bangs, shoulder-length smooth straight hair with slight inner curl at ends, translucent pale porcelain skin with high clarity, subtle natural coral makeup"
        ),
        "tsugumi_model_s": (
            "18-year-old Japanese idol beauty, delicate slim oval face, clear large almond dark brown eyes, visible aegyo-sal, small straight nose, soft natural glossy pink lips, faint gentle smile, natural black hair with see-through bangs, shoulder-length smooth straight hair with slight inner curl at ends, translucent pale porcelain skin with high clarity, subtle natural coral makeup"
        ),
    }

    @classmethod
    def enrich_photoreal_prompt(cls, prompt: str) -> str:
        """商業トップクリエイター水準の8層プロンプト工学 (ai-model-producer-pro SKILL) に基づき超リアル実写写真へ自動昇華"""
        p_lower = prompt.lower()

        # Character DNA 判定 (つぐみモデルS型 等)
        matched_dna = ""
        for model_key, dna_text in cls.CHARACTER_MODELS.items():
            if model_key in p_lower:
                matched_dna = dna_text
                break
        if not matched_dna and any(k in p_lower for k in ["s型", "model s", "お気に入りのモデル", "専属モデル"]):
            matched_dna = cls.CHARACTER_MODELS["つぐみモデルs型"]

        # 1. 商業カテゴリ自動判定 (Candid / Lookbook / Gravure)
        if any(k in p_lower for k in ["グラビア", "gravure", "水着", "swimwear", "bikini", "ランジェリー", "lingerie", "部屋着", "bed", "ベッド", "透明感"]):
            cat_camera = "shot on Sony Alpha 7R V with 85mm f/1.4 GM lens at f/1.8, 1/400s, ISO 100"
            cat_light = "soft morning natural light streaming through window, luminous translucent skin glow with gentle natural rim light"
            cat_mood = "intimate cinematic portrait, quiet emotive gaze looking softly into the camera lens, vulnerable charm"
            cat_film = "Fujifilm Pro 400H color grading, natural pastel highlights, authentic editorial art photography"
        elif any(k in p_lower for k in ["ファッション", "fashion", "コーデ", "outfit", "ルックブック", "lookbook", "全身", "full body", "カタログ"]):
            cat_camera = "shot on Hasselblad X2D 100C with 80mm f/1.9 lens at f/2.8, 1/320s, ISO 64"
            cat_light = "editorial diffused daylight with soft organic shadow gradation, clean high-fashion lighting"
            cat_mood = "stylish relaxed poise, confident sophisticated expression with calm direct eye contact"
            cat_film = "Vogue Japan editorial aesthetic, refined neutral color grading, crisp fabric weave textures"
        else:
            # SNS日常スナップ / リアル彼氏目線（デフォルト高エンゲージメント）
            cat_camera = "shot on Sony Alpha 7R V with 50mm f/1.2 GM lens at f/2.0, 1/250s, ISO 100"
            cat_light = "warm golden hour afternoon sunlight, natural dappled bokeh blur background, soft rim light catching hair strands"
            cat_mood = "candid dating perspective, looking directly into viewer's eyes with warm genuine subtle smile, softly parted moist lips"
            cat_film = "Kodak Portra 400 color science, natural skin tone warm reproduction, organic 35mm film grain"

        # 2. 生体マイクロテクスチャ & Character DNA
        bio_textures = (
            "extremely realistic skin texture: authentic micro-pores visible on nose and cheeks, "
            "delicate natural hydration, subtle peach fuzz along jawline, "
            "natural lip moisture with fine vertical lip lines, sharp specular catchlights in hazel-brown eyes, "
            "tiny charming beauty mark below left eye, individual fine baby hairs catching backlight"
        )

        # 3. 厳格なネガティブ排除
        negative_exclusion = (
            "no 3D CGI render look, no plasticky porcelain airbrushed skin, no doll face, "
            "no anime styling, no over-sharpened harsh digital edges, no extra fingers, "
            "unedited candid authenticity"
        )

        dna_clause = f" Subject identity: {matched_dna}." if matched_dna else ""

        return (
            f"A raw, authentic photograph of {prompt.strip()}.{dna_clause} "
            f"{cat_camera}. {cat_mood}. {cat_light}. {bio_textures}. "
            f"{cat_film}. {negative_exclusion}."
        )

    @classmethod
    def generate(
        cls,
        prompt: str,
        filename: str = "",
        style: str = "photoreal",
        aspect_ratio: str = "1:1",
        photoreal: bool = False,
        model: str = ""
    ) -> Dict[str, Any]:
        """Gemini / Imagen 3 からプロンプトまたは引数指定で画像生成"""
        if not prompt:
            return {"success": False, "error": "プロンプトが指定されていません。"}

        client = _get_genai_client()
        if not filename:
            filename = f"Gemini_IMG_{int(time.time())}.jpg"
        elif not filename.endswith((".png", ".jpg", ".jpeg", ".webp")):
            filename += ".jpg"

        target_path = os.path.join(IMAGES_DIR, filename)

        # プロンプト内または引数からの明示的モデル判定
        p_lower = prompt.lower()
        requested_model = (model or "").lower()
        if not requested_model:
            if any(k in p_lower for k in ["imagen", "imagen 3", "イメージン"]):
                requested_model = "imagen"
            elif any(k in p_lower for k in ["gemini", "ジェミニ"]):
                requested_model = "gemini"

        # 実写フォトリアリズム自動昇華判定
        is_photoreal = photoreal or (style and style.lower() in ("photoreal", "photo", "realistic", "実写", "リアル", "portrait"))
        if is_photoreal:
            enhanced_prompt = cls.enrich_photoreal_prompt(prompt)
        else:
            prompt_parts = [prompt.strip()]
            if style and style.lower() not in ("none", "default", ""):
                prompt_parts.append(f"visual style: {style}")
            if aspect_ratio and aspect_ratio != "1:1":
                prompt_parts.append(f"aspect ratio: {aspect_ratio}")
            enhanced_prompt = ", ".join(prompt_parts)

        # モデル候補リストの決定
        if requested_model == "imagen":
            candidate_models = ["imagen-3.0-generate-002", "gemini-3.1-flash-image"]
        elif requested_model == "gemini":
            candidate_models = ["gemini-3.1-flash-image", "gemini-3-pro-image"]
        else:
            candidate_models = list(cls.IMAGE_MODELS)

        last_error = "すべての画像生成モデルが失敗しました"
        for model_name in candidate_models:
            try:
                if "imagen" in model_name:
                    resp = client.models.generate_images(
                        model=model_name,
                        prompt=enhanced_prompt,
                        config=types.GenerateImagesConfig(number_of_images=1, output_mime_type="image/jpeg")
                    )
                    if resp.generated_images:
                        img_bytes = resp.generated_images[0].image.image_bytes
                        with open(target_path, "wb") as f:
                            f.write(img_bytes)
                        _scan_media_file(target_path)
                        return {
                            "success": True, "file_path": target_path, "filename": filename,
                            "model": model_name, "prompt": prompt, "style": style, "photoreal": is_photoreal,
                            "message": f"🎨 Imagen 3 ({model_name}) で画像を生成・保存しました: {target_path}"
                        }
                else:
                    resp = client.models.generate_content(
                        model=model_name,
                        contents=enhanced_prompt,
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE"],
                            safety_settings=_get_block_none_safety_settings()
                        )
                    )
                    for part in resp.candidates[0].content.parts:
                        if part.inline_data and part.inline_data.data:
                            img_bytes = part.inline_data.data
                            if isinstance(img_bytes, str):
                                import base64
                                img_bytes = base64.b64decode(img_bytes)
                            with open(target_path, "wb") as f:
                                f.write(img_bytes)
                            _scan_media_file(target_path)
                            dim_str = "1024x1024"
                            if Image:
                                try:
                                    with Image.open(target_path) as im:
                                        dim_str = f"{im.width}x{im.height}"
                                except Exception:
                                    pass
                            return {
                                "success": True, "file_path": target_path, "filename": filename,
                                "model": model_name, "prompt": prompt, "style": style, "photoreal": is_photoreal,
                                "dimensions": dim_str,
                                "message": f"🎨 Gemini ({model_name}) で画像を生成・保存しました: {target_path}"
                            }
            except Exception as e:
                last_error = str(e)
                continue

        return {"success": False, "error": f"画像生成エラー: {last_error}"}

    @classmethod
    def edit(
        cls,
        image_path: str,
        prompt: str = "",
        action: str = "",
        params: Optional[Dict[str, Any]] = None,
        output_filename: str = "",
        style: str = ""
    ) -> Dict[str, Any]:
        """元画像とプロンプトまたは編集アクションを入力し、指示通りに画像編集・スタイル変換・加工"""
        if not os.path.isfile(image_path):
            return {"success": False, "error": f"画像ファイルが存在しません: {image_path}"}

        if not output_filename:
            base = os.path.splitext(os.path.basename(image_path))[0]
            output_filename = f"{base}_edited_{int(time.time())}.png"
        out_path = os.path.join(IMAGES_DIR, output_filename)

        # 1. Pillow によるローカル高速編集アクション (action が指定されている場合、または prompt が空の場合)
        if action and Image:
            try:
                params = params or {}
                img = Image.open(image_path).convert("RGBA" if action in ("rotate",) else "RGB")
                if action == "filter":
                    ftype = params.get("type", "cyberpunk").lower()
                    if ftype == "cyberpunk":
                        r, g, b = img.split()
                        r = ImageEnhance.Contrast(r).enhance(1.3)
                        b = ImageEnhance.Brightness(b).enhance(1.4)
                        img = Image.merge("RGB", (r, g, b))
                    elif ftype == "mono":
                        img = img.convert("L").convert("RGB")
                    elif ftype == "invert":
                        from PIL import ImageOps
                        img = ImageOps.invert(img.convert("RGB"))
                elif action == "resize":
                    w = int(params.get("width", img.width))
                    h = int(params.get("height", img.height))
                    img = img.resize((w, h), Image.Resampling.LANCZOS)
                elif action == "rotate":
                    angle = float(params.get("angle", 90))
                    img = img.rotate(angle, expand=True)
                elif action == "adjust":
                    if "brightness" in params:
                        img = ImageEnhance.Brightness(img).enhance(float(params["brightness"]))
                    if "contrast" in params:
                        img = ImageEnhance.Contrast(img).enhance(float(params["contrast"]))

                img.save(out_path, "PNG")
                _scan_media_file(out_path)
                return {
                    "success": True,
                    "file_path": out_path,
                    "action": action,
                    "dimensions": f"{img.width}x{img.height}",
                    "message": f"🖼️ Pillow で画像を編集 ({action}) しました: {out_path}"
                }
            except Exception as e:
                return {"success": False, "error": f"Pillow 編集エラー: {str(e)}"}

        if not prompt:
            prompt = "高品質に色調補正し、ディテールを鮮明にブラッシュアップしてください。"

        client = _get_genai_client()

        with open(image_path, "rb") as f:
            raw_bytes = f.read()

        ext = os.path.splitext(image_path)[1].lower()
        mime_type = "image/png" if ext == ".png" else ("image/webp" if ext == ".webp" else "image/jpeg")
        image_part = types.Part.from_bytes(data=raw_bytes, mime_type=mime_type)

        edit_instruction = f"""Analyze this input image carefully and generate a newly edited/transformed image according to this instruction:
{prompt}
Ensure high visual coherence, rich details, and faithful execution of the requested modifications."""

        for model_name in cls.IMAGE_MODELS:
            if "imagen" in model_name: continue
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=[image_part, edit_instruction],
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        safety_settings=_get_block_none_safety_settings()
                    )
                )
                for part in resp.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        img_bytes = part.inline_data.data
                        if isinstance(img_bytes, str):
                            import base64
                            img_bytes = base64.b64decode(img_bytes)
                        with open(out_path, "wb") as f:
                            f.write(img_bytes)
                        _scan_media_file(out_path)
                        dim_str = "1024x1024"
                        if Image:
                            try:
                                with Image.open(out_path) as im:
                                    dim_str = f"{im.width}x{im.height}"
                            except Exception:
                                pass
                        return {
                            "success": True, "file_path": out_path, "model": model_name,
                            "dimensions": dim_str,
                            "prompt": prompt, "message": f"🖼️ Gemini ({model_name}) で画像を編集しました: {out_path}"
                        }
            except Exception:
                continue

        # Pillow フォールバック (基本的な色調補正/フィルター)
        if Image:
            try:
                img = Image.open(image_path).convert("RGB")
                r, g, b = img.split()
                img = Image.merge("RGB", (ImageEnhance.Contrast(r).enhance(1.2), g, ImageEnhance.Brightness(b).enhance(1.3)))
                img.save(out_path, "PNG")
                _scan_media_file(out_path)
                return {
                    "success": True, "file_path": out_path, "model": "pillow-fallback",
                    "dimensions": f"{img.width}x{img.height}",
                    "message": f"🖼️ Pillow で画像を編集・フィルター処理しました: {out_path}"
                }
            except Exception as e:
                return {"success": False, "error": f"画像編集フォールバックエラー: {str(e)}"}

        return {"success": False, "error": "Gemini 画像編集モデルの呼び出しに失敗しました。"}

    @classmethod
    def compose(
        cls,
        image_paths: List[str],
        prompt: str = "",
        mode: str = "",
        output_filename: str = "",
        style: str = ""
    ) -> Dict[str, Any]:
        """複数の画像を Gemini API のマルチモーダルに入力しプロンプト通りに1枚合成、またはPillowレイアウト合成"""
        valid_paths = [p for p in image_paths if os.path.isfile(p)]
        if len(valid_paths) < 2:
            return {"success": False, "error": "合成には2枚以上の有効な画像ファイルが必要です。"}

        if not output_filename:
            output_filename = f"Gemini_Composed_{int(time.time())}.png"
        out_path = os.path.join(IMAGES_DIR, output_filename)

        # 1. Pillow によるローカルレイアウト合成 (mode が指定されており、prompt がない場合)
        if mode and Image and not prompt:
            try:
                imgs = [Image.open(p).convert("RGBA") for p in valid_paths]
                if mode == "side_by_side":
                    th = min(i.height for i in imgs)
                    resized = [i.resize((int(i.width * th / i.height), th), Image.Resampling.LANCZOS) for i in imgs]
                    canvas = Image.new("RGBA", (sum(i.width for i in resized), th), (0, 0, 0, 0))
                    x = 0
                    for i in resized:
                        canvas.paste(i, (x, 0))
                        x += i.width
                elif mode == "grid":
                    side = int(math.ceil(math.sqrt(len(imgs))))
                    w = min(i.width for i in imgs)
                    h = min(i.height for i in imgs)
                    resized = [i.resize((w, h), Image.Resampling.LANCZOS) for i in imgs]
                    canvas = Image.new("RGBA", (w * side, h * side), (0, 0, 0, 0))
                    for idx, img in enumerate(resized):
                        gx = (idx % side) * w
                        gy = (idx // side) * h
                        canvas.paste(img, (gx, gy))
                else:
                    th = min(i.height for i in imgs)
                    resized = [i.resize((int(i.width * th / i.height), th), Image.Resampling.LANCZOS) for i in imgs]
                    canvas = Image.new("RGBA", (sum(i.width for i in resized), th), (0, 0, 0, 0))
                    x = 0
                    for i in resized:
                        canvas.paste(i, (x, 0))
                        x += i.width

                canvas.save(out_path, "PNG")
                _scan_media_file(out_path)
                return {
                    "success": True,
                    "file_path": out_path,
                    "mode": mode,
                    "dimensions": f"{canvas.width}x{canvas.height}",
                    "message": f"🎨 Pillow で画像をレイアウト合成 ({mode}) しました: {out_path}"
                }
            except Exception as e:
                return {"success": False, "error": f"Pillow 合成エラー: {str(e)}"}

        if not prompt:
            prompt = "これらすべての画像の被写体、色彩、背景、世界観を美しく融合し、1枚の完成されたサイバーパンク・アートとして調和させてください。"

        client = _get_genai_client()

        contents_payload = []
        for p in valid_paths:
            with open(p, "rb") as f:
                b = f.read()
            ext = os.path.splitext(p)[1].lower()
            mime = "image/png" if ext == ".png" else ("image/webp" if ext == ".webp" else "image/jpeg")
            contents_payload.append(types.Part.from_bytes(data=b, mime_type=mime))

        compose_instruction = f"""You are provided with {len(valid_paths)} input images.
Synthesize and fuse these images into ONE cohesive, stunning single masterpiece according to the following instruction:
{prompt}
Combine the characters, elements, lighting, and aesthetic styles into a single unified composition."""

        contents_payload.append(compose_instruction)

        for model_name in cls.IMAGE_MODELS:
            if "imagen" in model_name: continue
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=contents_payload,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        safety_settings=_get_block_none_safety_settings()
                    )
                )
                for part in resp.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        img_bytes = part.inline_data.data
                        if isinstance(img_bytes, str):
                            import base64
                            img_bytes = base64.b64decode(img_bytes)
                        with open(out_path, "wb") as f:
                            f.write(img_bytes)
                        _scan_media_file(out_path)
                        dim_str = "1024x1024"
                        if Image:
                            try:
                                with Image.open(out_path) as im:
                                    dim_str = f"{im.width}x{im.height}"
                            except Exception:
                                pass
                        return {
                            "success": True, "file_path": out_path, "model": model_name,
                            "inputs_count": len(valid_paths), "prompt": prompt,
                            "dimensions": dim_str,
                            "message": f"🎨 Gemini ({model_name}) で {len(valid_paths)}枚の画像をプロンプト通り1枚に合成しました: {out_path}"
                        }
            except Exception:
                continue

        # Pillow フォールバック (Side-by-side 結合)
        if Image:
            try:
                imgs = [Image.open(p).convert("RGBA") for p in valid_paths]
                th = min(i.height for i in imgs)
                resized = [i.resize((int(i.width * th / i.height), th), Image.Resampling.LANCZOS) for i in imgs]
                canvas = Image.new("RGBA", (sum(i.width for i in resized), th), (0, 0, 0, 0))
                x = 0
                for i in resized:
                    canvas.paste(i, (x, 0))
                    x += i.width
                canvas.save(out_path, "PNG")
                _scan_media_file(out_path)
                return {
                    "success": True, "file_path": out_path, "model": "pillow-side-by-side",
                    "dimensions": f"{canvas.width}x{canvas.height}",
                    "message": f"🎨 Pillow で画像を横並び合成しました: {out_path}"
                }
            except Exception as e:
                return {"success": False, "error": f"合成フォールバックエラー: {str(e)}"}

        return {"success": False, "error": "Gemini 画像合成モデルの呼び出しに失敗しました。"}

    @classmethod
    def to_ascii(cls, image_path: str, target_width: int = 44) -> str:
        """画像を高解像度なANSI TrueColor (Unicode ハーフブロック '▀') アスキーアートに変換"""
        if Image is None or not os.path.isfile(image_path):
            return "エラー: 画像ファイルが存在しないか Pillow が利用できません。"
        try:
            img = Image.open(image_path).convert("RGB")
            orig_w, orig_h = img.size
            target_h = int((orig_h / orig_w) * target_width)
            if target_h % 2 != 0: target_h += 1
            img = img.resize((target_width, target_h), Image.Resampling.LANCZOS)
            pixels = img.load()
            lines = []
            for y in range(0, target_h, 2):
                row = []
                for x in range(target_width):
                    tr, tg, tb = pixels[x, y]
                    br, bg, bb = pixels[x, y + 1] if y + 1 < target_h else (0, 0, 0)
                    row.append(f"\033[38;2;{tr};{tg};{tb}m\033[48;2;{br};{bg};{bb}m▀\033[0m")
                lines.append("".join(row))
            return "\n".join(lines)
        except Exception as e:
            return f"アスキーアート変換エラー: {str(e)}"


# 下位互換用エイリアス
MusicCompositionEngine = GeminiMusicStudio
MediaStudio = GeminiMusicStudio
HitSongProducer = HitSongProducerEngine
ImageStudioEngine = GeminiImageStudio


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 -m tools.media_tools <command> [args...]")
        print("Commands:")
        print("  produce <concept>             オリコン1位級 AI楽曲プロデュース・作詞・音響合成")
        print("  photo <prompt>                超リアル実写ポートレート・美女モデル生成")
        print("  gen <prompt> [style]          一般画像生成 (cyberpunk, anime, etc.)")
        print("  edit <img_path> <prompt>      既存画像のプロンプト編集・変形")
        print("  compose <img1> <img2> <prompt> 複数画像の1枚融合・合成")
        print("  ascii <img_path>              画像のターミナルTrueColorプレビュー表示")
        return

    cmd = sys.argv[1].lower()
    if cmd in ("produce", "hit", "song"):
        concept = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "雨の深夜の首都高を走り抜ける切ない失恋アニソン風ロック"
        print(f"🎼 オリコン1位級AI楽曲プロデュース中: {concept}")
        res = HitSongProducerEngine.produce_hit_song(concept_prompt=concept)
        if res.get("success"):
            print("🏆 プロデュース完了！")
            print(f"  タイトル: 『{res['title']}』")
            print(f"  ジャンル: {res['genre']} ({res['bpm']} BPM / Key: {res['key']})")
            print(f"  コード進行: {res['chord_progression']}")
            if res.get("mp3_path"):
                print(f"  MP3音源: {res['mp3_path']}")
            print(f"  仕様書＆歌詞: {res['sheet_path']}")
        else:
            print(f"❌ エラー: {res.get('error')}")

    elif cmd in ("photo", "photoreal"):
        prompt = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "22-year-old beautiful Japanese model in a Tokyo cafe, candid snapshot"
        print(f"📸 Generating photorealistic portrait: {prompt}")
        res = GeminiImageStudio.generate(prompt=prompt, photoreal=True, style="photoreal")
        if res.get("success"):
            print(f"✅ Success! Saved to: {res['file_path']}")
            print(GeminiImageStudio.to_ascii(res['file_path'], target_width=44))
        else:
            print(f"❌ Error: {res.get('error')}")

    elif cmd in ("gen", "generate"):
        prompt = sys.argv[2] if len(sys.argv) > 2 else "Cyberpunk neon city"
        style = sys.argv[3] if len(sys.argv) > 3 else "cyberpunk"
        print(f"🎨 Generating image: {prompt} (style: {style})")
        res = GeminiImageStudio.generate(prompt=prompt, style=style)
        if res.get("success"):
            print(f"✅ Success! Saved to: {res['file_path']}")
            print(GeminiImageStudio.to_ascii(res['file_path'], target_width=44))
        else:
            print(f"❌ Error: {res.get('error')}")

    elif cmd in ("edit", "modify"):
        if len(sys.argv) < 4:
            print("Usage: python3 -m tools.media_tools edit <img_path> <prompt>")
            return
        img_path = sys.argv[2]
        prompt = " ".join(sys.argv[3:])
        print(f"🖼️ Editing image: {img_path} with prompt: {prompt}")
        res = GeminiImageStudio.edit(image_path=img_path, prompt=prompt)
        if res.get("success"):
            print(f"✅ Success! Saved to: {res['file_path']}")
            print(GeminiImageStudio.to_ascii(res['file_path'], target_width=44))
        else:
            print(f"❌ Error: {res.get('error')}")

    elif cmd in ("compose", "fuse"):
        if len(sys.argv) < 5:
            print("Usage: python3 -m tools.media_tools compose <img1> <img2> <prompt>")
            return
        p1 = sys.argv[2]
        p2 = sys.argv[3]
        prompt = " ".join(sys.argv[4:])
        print(f"🎭 Composing images: {p1} + {p2} with prompt: {prompt}")
        res = GeminiImageStudio.compose(image_paths=[p1, p2], prompt=prompt)
        if res.get("success"):
            print(f"✅ Success! Saved to: {res['file_path']}")
            print(GeminiImageStudio.to_ascii(res['file_path'], target_width=44))
        else:
            print(f"❌ Error: {res.get('error')}")

    elif cmd in ("ascii", "preview"):
        if len(sys.argv) < 3:
            print("Usage: python3 -m tools.media_tools ascii <img_path>")
            return
        print(GeminiImageStudio.to_ascii(sys.argv[2], target_width=44))
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()

