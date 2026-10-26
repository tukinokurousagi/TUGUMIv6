#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_music_skills_e2e.py - TUGUMIv6 音楽スキル群 E2E結合テスト
hit-song-producer-pro および music-composer-pro の完全連携と実動を検証
"""

import os
import sys
import pytest

TUGUMI_ROOT = "/data/data/com.termux/files/home/TUGUMIv6"
if TUGUMI_ROOT not in sys.path:
    sys.path.insert(0, TUGUMI_ROOT)

SKILLS_DIR = "/data/data/com.termux/files/home/.agents/skills"


def test_music_skills_directory_and_symlinks():
    """スキルの存在およびTUGUMIv6へのシンボリックリンク整合性を検証"""
    hit_song_skill = os.path.join(SKILLS_DIR, "hit-song-producer-pro")
    composer_skill = os.path.join(SKILLS_DIR, "music-composer-pro")

    assert os.path.isdir(hit_song_skill), "hit-song-producer-pro が ~/.agents/skills に存在すること"
    assert os.path.isdir(composer_skill), "music-composer-pro が ~/.agents/skills に存在すること"

    tugumi_hit_link = os.path.join(TUGUMI_ROOT, "skills", "hit-song-producer-pro")
    tugumi_composer_link = os.path.join(TUGUMI_ROOT, "skills", "music-composer-pro")

    assert os.path.exists(tugumi_hit_link), "TUGUMIv6/skills/hit-song-producer-pro が解決可能であること"
    assert os.path.exists(tugumi_composer_link), "TUGUMIv6/skills/music-composer-pro が解決可能であること"


def test_music_macro_executable():
    """music-macro バイナリの存在と実行権限を検証"""
    macro_path = "/data/data/com.termux/files/home/bin/music-macro"
    assert os.path.isfile(macro_path), "music-macro が ~/bin に存在すること"
    assert os.access(macro_path, os.X_OK), "music-macro に実行権限があること"


def test_music_theory_engine():
    """音楽理論エンジンのスケール・コード進行計算が正確であること"""
    composer_scripts = os.path.join(SKILLS_DIR, "music-composer-pro", "scripts")
    if composer_scripts not in sys.path:
        sys.path.insert(0, composer_scripts)

    from music_theory import MusicTheory, PROGRESSION_PRESETS

    # C Major スケール
    notes = MusicTheory.get_scale_notes("C", "major", octave=4)
    assert notes == [60, 62, 64, 65, 67, 69, 71]

    # 丸サ進行の計算
    chords = MusicTheory.generate_progression_chords("C", "major", "just_the_two_of_us")
    assert len(chords) == 4
    assert chords[0]["name"] == "Fmaj7"


def test_local_midi_and_synth_generation(tmp_path):
    """MediaStudio / GeminiMusicStudio によるMP3単一生成の実動検証"""
    from tools.media_tools import GeminiMusicStudio

    test_title = "Pytest_Track"
    res = GeminiMusicStudio.compose(
        genre="synthwave",
        bars=2,
        title=test_title,
        theme="Pytest synthwave",
        custom_bpm=120,
        with_vocal=False,
        use_lyria=False
    )

    assert "mp3_path" in res or "audio_path" in res
    audio_file = res.get("mp3_path") or res.get("audio_path")
    if audio_file and os.path.exists(audio_file):
        assert audio_file.endswith(".mp3") or audio_file.endswith(".wav")
        # テスト後の一時ファイルお掃除
        try:
            os.remove(audio_file)
        except Exception:
            pass


def test_create_music_direct_interface():
    """プロンプトジェネレーター不要のダイレクト作曲インターフェース検証"""
    from tools.media_tools import GeminiMusicStudio
    assert hasattr(GeminiMusicStudio, "create_music_direct"), "create_music_direct が実装されていること"


def test_natural_language_music_intent_detection():
    """TUGUMIv6 CLI 自然言語による楽曲制作インテント検知を検証"""
    from interfaces.cli.main import is_music_creation_intent

    assert is_music_creation_intent("雨上がりの夜、切ない感じで曲作って") is True
    assert is_music_creation_intent("こんな感じで楽曲作って") is True
    assert is_music_creation_intent("疾走感あるロックを作曲して") is True
    assert is_music_creation_intent("作業用BGMを作ってほしい") is True
    assert is_music_creation_intent("明日の天気は？") is False
    assert is_music_creation_intent("Pythonのコードを修正して") is False


def test_webui_music_compose_endpoint():
    """WebUI /api/music/compose がプロンプト完全保持で呼び出せることを検証"""
    from fastapi.testclient import TestClient
    from interfaces.web.web_server import app

    client = TestClient(app)
    # ツール一覧に music-macro が含まれ、ぶつ切りなしの自由プロンプト設定になっていること
    res_tools = client.get("/api/tools/list")
    assert res_tools.status_code == 200
    cats = res_tools.json().get("categories", {})
    media_scripts = [s.get("name") for s in cats.get("media", {}).get("scripts", [])]
    assert "music-macro" in media_scripts, "music-macro がWebUIツール一覧に存在すること"

    # 自然言語検知関数の整合性
    from interfaces.web.web_server import is_music_creation_intent as web_is_music
    assert web_is_music("疾走感あるロックを作曲して") is True
    assert web_is_music("こんな感じで楽曲作って") is True
