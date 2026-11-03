# -*- coding: utf-8 -*-
"""
Unit & Integration Tests for TUGUMIv6 4-Tier & Ebbinghaus Decay Memory Engine
"""

import sys

# Ensure TUGUMIv6 is in path
TUGUMI_ROOT = "/data/data/com.termux/files/home/TUGUMIv6"
if TUGUMI_ROOT not in sys.path:
    sys.path.insert(0, TUGUMI_ROOT)

from memory.sqlite_memory import SQLiteMemory, compute_ebbinghaus_decay
from memory.advanced_memory import AdvancedMemoryEngine

def test_ebbinghaus_decay_formula():
    """エビングハウス忘却曲線の数学的挙動をテスト"""
    # 1. importance=5 は永久不滅 (1.0固定)
    score_core = compute_ebbinghaus_decay("2020-01-01 00:00:00", access_count=1, importance=5)
    assert score_core == 1.0

    # 2. 直近アクセスされた記憶はスコアほぼ 1.0
    from datetime import datetime
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    score_now = compute_ebbinghaus_decay(now_str, access_count=1, importance=3, tier="semantic")
    assert score_now >= 0.99

    # 3. 過去のアクセスは減衰する
    score_past = compute_ebbinghaus_decay("2026-01-01 00:00:00", access_count=1, importance=3, tier="working")
    assert score_past < 0.5

    # 4. アクセス回数が多いほど減衰しにくい（定着強化）
    score_frequent = compute_ebbinghaus_decay("2026-08-01 00:00:00", access_count=100, importance=3, tier="procedural")
    score_rare = compute_ebbinghaus_decay("2026-08-01 00:00:00", access_count=1, importance=3, tier="procedural")
    assert score_frequent > score_rare

def test_4tier_remember_and_recall(tmp_path):
    """4-Tier記憶の永続保存とハイブリッド想起をテスト"""
    test_db = str(tmp_path / "test_memory.db")
    mem = SQLiteMemory(db_path=test_db)

    # 4-Tier それぞれに記憶を登録
    id_w = mem.remember("本日のTermux環境デバッグ作業中", category="task", tier="working")
    id_e = mem.remember("2026-10-08のセッションでメモリ拡張を実施完了", category="summary", tier="episodic")
    id_s = mem.remember("拓磨様の最優先規則：Switch 2原則（無劣化・妥協禁止）", category="directive", tier="semantic", importance=5)
    id_p = mem.remember("TermuxでのSQLite WAL設定手順: PRAGMA journal_mode=WAL;", category="procedure", tier="procedural")

    assert id_w > 0
    assert id_e > 0
    assert id_s > 0
    assert id_p > 0

    # procedural のみフィルタして想起
    res_p = mem.recall_similar("SQLite WAL", tier="procedural")
    assert len(res_p) >= 1
    assert res_p[0]["tier"] == "procedural"
    assert "WAL" in res_p[0]["fact_content"]
    assert "decay_score" in res_p[0]
    assert "hybrid_score" in res_p[0]

    # 全tier対象の想起
    res_all = mem.recall_similar("Switch 2")
    assert len(res_all) >= 1
    assert res_all[0]["importance"] == 5
    assert res_all[0]["decay_score"] == 1.0

def test_advanced_memory_engine_4tier(tmp_path):
    """AdvancedMemoryEngineの自動コンソリデーションとコンテキスト生成をテスト"""
    test_db = str(tmp_path / "test_advanced.db")
    engine = AdvancedMemoryEngine(db_path=test_db)

    # 1. Proceduralパターンの自動検知
    saved_ids = engine.consolidate_interaction("Termuxでのテスト実行のコマンドは pytest tests/ です。")
    assert len(saved_ids) >= 1

    # 2. Cognitive Context 生成
    ctx = engine.recall_cognitive_context(current_query="テスト実行")
    assert "【拓磨様の重要設定・絶対方針・コア記憶】" in ctx
    assert len(ctx) > 100

def test_mcp_memory_tool_functions(tmp_path):
    """MCPツール内部関数の直接実行テスト"""
    test_db = str(tmp_path / "test_mcp.db")
    mem = SQLiteMemory(db_path=test_db)

    # store
    eid = mem.remember("MCP経由で保存された重要な知見", category="fact", tier="semantic", tags=["mcp", "v6"])
    assert eid > 0

    # recall
    results = mem.recall_similar("重要な知見", limit=3, tier="semantic")
    assert len(results) == 1
    assert results[0]["id"] == eid
    assert results[0]["decay_score"] >= 0.99
