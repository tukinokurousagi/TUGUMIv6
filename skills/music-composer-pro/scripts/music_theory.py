#!/data/data/com.termux/files/usr/bin/python3
# -*- coding: utf-8 -*-
"""
music_theory.py - TUGUMIv6 音楽理論＆コード進行エンジン
純粋Pythonによる高精度スケール・コード・ジャンル別進行計算
"""

from typing import List, Dict, Tuple, Optional

# ノート名と半音オフセット (C = 0)
NOTE_MAP = {
    "C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3,
    "E": 4, "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8,
    "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11
}

REVERSE_NOTE_MAP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# スケール定義 (半音インターバル)
SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "melodic_minor": [0, 2, 3, 5, 7, 9, 11],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "pentatonic_major": [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "blues": [0, 3, 5, 6, 7, 10],
    "hirajoshi": [0, 2, 3, 7, 8], # 日本の伝統的陰音階
}

# 代表的コード進行プリセット (ディグリー表記: 0-indexed scale degree)
PROGRESSION_PRESETS = {
    "royal_road": { # 王道進行 (IV - V - iii - vi)
        "name": "王道進行 (Royal Road)",
        "degrees": [3, 4, 2, 5],
        "chord_types": ["maj7", "7", "min7", "min7"],
        "mood": "ドラマティック・エモーショナル・J-POP定番"
    },
    "just_the_two_of_us": { # 丸サ進行 (IVM7 - III7 - vi - I7)
        "name": "丸サ・椎名林檎進行 (Just The Two of Us)",
        "degrees": [3, 2, 5, 0],
        "chord_types": ["maj7", "7", "min7", "7"],
        "mood": "洗練・アーバン・Lo-Fi・ネオソウル"
    },
    "komuro": { # 小室進行 (vi - IV - V - I)
        "name": "小室進行 (Komuro Progression)",
        "degrees": [5, 3, 4, 0],
        "chord_types": ["min", "maj", "maj", "maj"],
        "mood": "疾走感・哀愁・ユーロビート・アニメソング"
    },
    "canon": { # カノン進行 (I - V - vi - iii - IV - I - IV - V)
        "name": "カノン進行 (Pachelbel's Canon)",
        "degrees": [0, 4, 5, 2, 3, 0, 3, 4],
        "chord_types": ["maj", "maj", "min", "min", "maj", "maj", "maj", "maj"],
        "mood": "安心感・普遍的感動・クラシカル・バラード"
    },
    "pop_punk": { # 4コードポップ進行 (I - V - vi - IV)
        "name": "4コード進行 (Pop Punk / Axis of Awesome)",
        "degrees": [0, 4, 5, 3],
        "chord_types": ["maj", "maj", "min", "maj"],
        "mood": "爽快・前向き・キャッチー・洋楽ポップス"
    },
    "cyber_synth": { # サイバーシンセ進行 (i - VI - III - VII)
        "name": "サイバーシンセ・ダークウェーブ進行",
        "degrees": [0, 5, 2, 6],
        "chord_types": ["min", "maj", "maj", "maj"],
        "mood": "近未来・サイバーパンク・緊張感・ディストピア"
    },
    "jazz_two_five_one": { # ジャズ定番 (ii7 - V7 - Imaj7 - VI7)
        "name": "ジャズ ii-V-I 進行",
        "degrees": [1, 4, 0, 5],
        "chord_types": ["min7", "7", "maj7", "7"],
        "mood": "ジャジー・知的・バーカウンター・スウィング"
    },
    "ambient_chill": { # アンビエント進行 (Imaj7 - IVmaj7)
        "name": "アンビエント浮遊進行",
        "degrees": [0, 3, 0, 3],
        "chord_types": ["maj7", "maj7", "maj7", "maj7"],
        "mood": "浮遊感・リラックス・瞑想・BGM"
    }
}

# ジャンル別サウンドデザインプリセット
GENRE_PRESETS = {
    "lofi": {
        "bpm": 82,
        "key": "Eb",
        "scale": "major",
        "progression": "just_the_two_of_us",
        "instruments": {"lead": 4, "pad": 89, "bass": 33}, # Rhodes/Electric Piano, Pad, Fingered Bass
        "swing": 0.2,
        "description": "Chill Lo-Fi HipHop (丸サ進行 + エレピ + ビンテージ感)"
    },
    "synthwave": {
        "bpm": 118,
        "key": "A",
        "scale": "minor",
        "progression": "cyber_synth",
        "instruments": {"lead": 80, "pad": 88, "bass": 38}, # Saw Lead, Synth Pad, Synth Bass
        "swing": 0.0,
        "description": "80s Cyberpunk Synthwave (Sawリード + パルスベース + 疾走感)"
    },
    "jpop": {
        "bpm": 132,
        "key": "F",
        "scale": "major",
        "progression": "royal_road",
        "instruments": {"lead": 81, "pad": 49, "bass": 34}, # Lead, String Ensemble, Picked Bass
        "swing": 0.0,
        "description": "J-POP / Anime Anthem (王道進行 + ストリングス + キャッチーメロディ)"
    },
    "cyberpunk": {
        "bpm": 128,
        "key": "D",
        "scale": "minor",
        "progression": "cyber_synth",
        "instruments": {"lead": 84, "pad": 92, "bass": 39}, # Charang, Space Voice, Synth Bass 2
        "swing": 0.0,
        "description": "TUGUMI Cyberpunk Darkwave (重低音アシッド + 金属的リード)"
    },
    "ambient": {
        "bpm": 65,
        "key": "C",
        "scale": "major",
        "progression": "ambient_chill",
        "instruments": {"lead": 11, "pad": 89, "bass": 32}, # Vibraphone, Warm Pad, Acoustic Bass
        "swing": 0.0,
        "description": "Deep Ambient / Meditation (浮遊コード + ベルリード)"
    },
    "edm": {
        "bpm": 128,
        "key": "G",
        "scale": "minor",
        "progression": "pop_punk",
        "instruments": {"lead": 87, "pad": 90, "bass": 38}, # Lead 8, Polysynth, Synth Bass
        "swing": 0.0,
        "description": "High-Energy Festival EDM (4つ打ち + ドロップ展開)"
    },
    "piano_solo": {
        "bpm": 76,
        "key": "C",
        "scale": "major",
        "progression": "canon",
        "instruments": {"lead": 0, "pad": 0, "bass": 0}, # Acoustic Grand Piano
        "swing": 0.05,
        "description": "Classical Piano Solo (カノン進行 + 優美なアルペジオ)"
    }
}

class MusicTheory:
    """音楽理論・コード生成ユーティリティ"""

    @staticmethod
    def note_name_to_midi(name: str, octave: int = 4) -> int:
        clean = name.strip().upper()
        semi = NOTE_MAP.get(clean, 0)
        return (octave + 1) * 12 + semi

    @staticmethod
    def midi_to_note_name(midi: int) -> str:
        semi = midi % 12
        octave = (midi // 12) - 1
        return f"{REVERSE_NOTE_MAP[semi]}{octave}"

    @classmethod
    def get_scale_notes(cls, root_name: str, scale_type: str = "major", octave: int = 4) -> List[int]:
        root_midi = cls.note_name_to_midi(root_name, octave)
        intervals = SCALES.get(scale_type, SCALES["major"])
        return [root_midi + iv for iv in intervals]

    @classmethod
    def build_chord(cls, root_midi: int, chord_type: str = "maj") -> List[int]:
        """コードタイプに応じたノート配列（MIDIノート番号）を生成"""
        c_type = chord_type.lower()
        if "maj7" in c_type:
            intervals = [0, 4, 7, 11]
        elif "min7" in c_type:
            intervals = [0, 3, 7, 10]
        elif "7" in c_type: # ドミナントセブンス
            intervals = [0, 4, 7, 10]
        elif "dim" in c_type:
            intervals = [0, 3, 6, 9]
        elif "aug" in c_type:
            intervals = [0, 4, 8]
        elif "min" in c_type:
            intervals = [0, 3, 7]
        elif "sus4" in c_type:
            intervals = [0, 5, 7]
        else: # メジャー
            intervals = [0, 4, 7]
        return [root_midi + iv for iv in intervals]

    @classmethod
    def generate_progression_chords(cls, key: str, scale_type: str, prog_key: str, octave: int = 4) -> List[Dict]:
        """進行プリセットに基づいて各小節のコード構成を生成"""
        prog = PROGRESSION_PRESETS.get(prog_key, PROGRESSION_PRESETS["royal_road"])
        scale_notes = cls.get_scale_notes(key, scale_type, octave)
        num_scale = len(scale_notes)

        chord_sequence = []
        for i, deg in enumerate(prog["degrees"]):
            c_type = prog["chord_types"][i % len(prog["chord_types"])]
            root_deg = deg % num_scale
            root_midi = scale_notes[root_deg]
            notes = cls.build_chord(root_midi, c_type)
            chord_name = f"{cls.midi_to_note_name(root_midi)[:-1]}{c_type}"
            chord_sequence.append({
                "bar": i + 1,
                "name": chord_name,
                "root_midi": root_midi,
                "chord_type": c_type,
                "notes": notes,
                "bass_note": root_midi - 12
            })
        return chord_sequence
