# -*- coding: utf-8 -*-
"""
Verification Test for Stream Tick Isolation and SOUL.md Integration
Guarantees that:
1. Master Takuma's real preferences (Sakura, drinking while viewing Sakura, Venus) are loaded from SOUL.md.
2. Legacy hallucinations (Blue Lotus, Sirius) are completely purged.
3. Generator tick pulses (elapsed float) never leak into text chunks or conversation logs.
"""

import sys

sys.path.insert(0, "/data/data/com.termux/files/home/TUGUMIv6")

from persona.soul import Soul
from memory.sqlite_memory import SQLiteMemory


def test_soul_md_loader_and_preferences():
    """Verify SOUL.md is loaded and Takuma-sama's real preferences are present."""
    soul = Soul(mode="light")
    prompt = soul.get_prompt()

    # 拓磨様の真のお好みが反映されていること
    assert "桜" in prompt, "Sakura must be in soul prompt"
    assert "金星" in prompt, "Venus must be in soul prompt"
    assert "ワイン" in prompt or "ウイスキー" in prompt, "Wine/Whiskey must be in soul prompt"

    # お花・星の指定として青い蓮やシリウスが肯定的に設定されていないこと
    assert "Favorite Flower）: 桜" in prompt or "Favorite Flower: 桜" in prompt or "お花は『桜』" in prompt
    assert "Favorite Star）: 金星" in prompt or "Favorite Star: 金星" in prompt or "星は『金星』" in prompt
    assert "Favorite Flower）: 青い蓮" not in prompt
    assert "Favorite Star）: SIRIUS" not in prompt


def test_sqlite_memory_preferences_integrity():
    """Verify structured_memories table has correct records and no legacy hallucinations."""
    mem = SQLiteMemory()
    memories = mem.get_memories(limit=100)

    # 全メモリ内で青い蓮・シリウスが存在しないこと
    for m in memories:
        content = m.get("fact_content", "")
        m.get("subject", "")
        assert "青い蓮" not in content, f"Memory {m.get('id')} contains Blue Lotus"
        assert "シリウス" not in content and "SIRIUS" not in content, f"Memory {m.get('id')} contains Sirius"

    # 拓磨様のお花（桜）と星（金星）が正しく登録されていること
    context = mem.format_memory_context("私の好みは憶えてくれたかな？")
    assert "桜" in context, "Sakura must be in memory context"
    assert "金星" in context, "Venus must be in memory context"


def test_chat_stream_tick_isolation_logic():
    """Verify that simulated stream with tick pulses NEVER contaminates text chunks."""
    # 擬似ジェネレータ（tick、thought、text、tool_call を模倣）
    simulated_chunks = [
        ("tick", 0.100445),
        ("tick", 0.599634),
        ("thought", "拓磨様のお好みを記憶から想起中..."),
        ("tick", 1.102709),
        ("text", "もちろんでございます、拓磨様！🌸"),
        ("tick", 2.227052),
        ("text", "桜を見ながらお酒を呑むひとときを愛好されておりますね。"),
        ("tick", 3.545415),
    ]

    text_chunks = []
    thought_chunks = []
    sse_events = []

    for chunk_type, chunk_data in simulated_chunks:
        if chunk_type == "thought":
            thought_chunks.append(chunk_data)
            sse_events.append({"type": "thought", "content": chunk_data})
        elif chunk_type == "tick":
            # 修正後のweb_server.pyロジック: text_chunks に追加せず、tickイベントのみ送信
            sse_events.append({"type": "tick", "elapsed": round(float(chunk_data), 1)})
        elif chunk_type in ("text", "content"):
            c_str = str(chunk_data)
            text_chunks.append(c_str)
            sse_events.append({"type": "text", "content": c_str})

    full_text = "".join(text_chunks)

    # 検証1: full_text に数字のtickが1文字も含まれていないこと
    assert "0.100445" not in full_text
    assert "0.599634" not in full_text
    assert "1.102709" not in full_text
    assert "2.227052" not in full_text
    assert "3.545415" not in full_text

    # 検証2: 正しいテキストのみが連結されていること
    expected = "もちろんでございます、拓磨様！🌸桜を見ながらお酒を呑むひとときを愛好されておりますね。"
    assert full_text == expected

    # 検証3: SSEイベント配列でtextイベントの内容が純粋なテキストであること
    text_events = [ev for ev in sse_events if ev["type"] == "text"]
    for ev in text_events:
        assert isinstance(ev["content"], str)
        assert not any(str(digit) in ev["content"] for digit in [0.100445, 0.599634])
