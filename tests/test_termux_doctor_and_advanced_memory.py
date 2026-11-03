# -*- coding: utf-8 -*-
"""
Tests for TUGUMIv6 TermuxDoctor & AdvancedMemoryEngine & Antigravity Tools Integration
- Deep Termux Environment Inspection & Maintenance Verification
- Multi-Tier Cognitive Memory & Auto-Consolidation Verification
- Antigravity SDK Toolset Registration & Execution Verification
- Soul Persona Antigravity Tri-Pillars Verification
"""

import os
import sys
import json

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.termux_doctor import TermuxDoctor
from memory.advanced_memory import AdvancedMemoryEngine
from tools.antigravity_tools import (
    termux_inspect_environment,
    memory_recall_context,
    memory_remember_fact,
    get_tugumi_tools
)
from persona.soul import get_system_prompt

def test_termux_doctor_inspection():
    """TermuxDoctor の全レイヤー深層把握検証"""
    doctor = TermuxDoctor(base_dir=ROOT_DIR)
    rep = doctor.inspect_all()

    assert "health_score" in rep
    assert 0 <= rep["health_score"] <= 100
    assert rep["system"]["arch"] in ("aarch64", "x86_64", "arm")
    assert "home_free_gb" in rep["storage"]
    assert "total_mb" in rep["memory"]
    assert "zombies_count" in rep["processes"]
    assert "rish_available" in rep["privileges"]
    assert "ca_bundle_exists" in rep["tls_ssl"]
    assert "phantom_killer" in rep

    hud = doctor.format_hud_summary(rep)
    assert "TUGUMIv6 Termux Environment Inspection & Doctor" in hud
    assert f"Health Score: {rep['health_score']}/100" in hud

def test_termux_doctor_maintenance():
    """TermuxDoctor の自律整備・自己修復機能検証"""
    doctor = TermuxDoctor(base_dir=ROOT_DIR)
    res = doctor.maintain_environment(fix_all=False)

    assert res["status"] == "MAINTENANCE_COMPLETED"
    assert "actions_taken" in res
    assert len(res["actions_taken"]) >= 1
    assert "health_score_after" in res

def test_advanced_memory_engine_and_consolidation(tmp_path):
    """多層認知記憶、自動コンソリデーション、想起機能の検証"""
    test_db = str(tmp_path / "test_memory.db")
    mem = AdvancedMemoryEngine(db_path=test_db)

    # 1. デフォルトコア記憶のシード検証
    core_mems = mem.sql.get_memories(min_importance=5)
    subjects = [m["subject"] for m in core_mems]
    assert "マスター尊称" in subjects
    assert "Switch 2 原則（無劣化・妥協禁止）" in subjects
    assert "Termux環境工学と特権行使" in subjects

    # 2. 事実の直接学習検証
    mem_id = mem.learn_fact(
        category="preference",
        subject="Pythonコードスタイル",
        fact_content="Pythonコードは型ヒントとdocstringを徹底する",
        importance=4
    )
    assert mem_id > 0

    # 3. 会話からの自動コンソリデーション（Auto-Consolidation）検証
    user_speech_1 = "これからは高速レスポンスを標準にして頼む。"
    saved_ids = mem.consolidate_interaction(user_speech_1, "かしこまりました。")
    assert len(saved_ids) >= 1

    # 4. 多層記憶想起検証
    context = mem.recall_cognitive_context(current_query="Python")
    assert "【拓磨様の重要設定・絶対方針・コア記憶】" in context
    assert "Pythonコードスタイル" in context

def test_antigravity_tools_callable():
    """Antigravity SDK 向けツールの実動検証"""
    # 1. 診断ツール
    inspect_json = termux_inspect_environment()
    rep = json.loads(inspect_json)
    assert "health_score" in rep

    # 2. 記憶想起ツール
    recall_json = memory_recall_context("Termux")
    rec = json.loads(recall_json)
    assert rec["status"] == "success"
    assert "拓磨様" in rec["cognitive_context"]

    # 3. 記憶保存ツール
    remember_json = memory_remember_fact(
        category="project",
        subject="TUGUMIv6環境整備",
        fact_content="Antigravity CLIレベルの思考と環境自律整備を完備",
        importance=5
    )
    rem = json.loads(remember_json)
    assert rem["status"] == "success"

    # 4. ツールリスト登録検証
    tools = get_tugumi_tools()
    tool_names = [t.__name__ for t in tools]
    assert "termux_inspect_environment" in tool_names
    assert "termux_maintain_environment" in tool_names
    assert "memory_recall_context" in tool_names
    assert "memory_remember_fact" in tool_names

def test_soul_antigravity_cognitive_prompt():
    """Soul システムプロンプトの Antigravity 思考アーキテクチャ検証"""
    prompt = get_system_prompt(
        mode="light",
        rag_context="[Test RAG]: Sample knowledge",
        memory_context="[Test Memory]: Master prefers dark mode"
    )

    assert "拓磨様" in prompt
    assert "愛知県一宮市" in prompt
    assert "思考の3大柱（Cognitive Tri-Pillars）" in prompt
    assert "究極の自律型デバッガー＆先制改修統合プロトコル" in prompt
    assert "納品前5層検証ゲート" in prompt
    assert "Termux環境把握＆自律整備マンデート" in prompt
    assert "Sample knowledge" in prompt
    assert "Master prefers dark mode" in prompt
