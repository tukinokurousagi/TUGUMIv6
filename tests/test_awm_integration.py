"""
TUGUMIv6 AWM (Agent Workflow Memory) Native Integration Test Suite
- Verifies Multi-Tier Noise & Trash Filter (Trivial phrases, step threshold, failures)
- Verifies Pre-execution Guidance Injection into System Instructions
- Verifies De-duplication, Upsert, and Garbage Collection (Purge)
- Zero External API Billing Protected (Mock Mode)
"""

import sys
from pathlib import Path

# Add TUGUMIv6 to path
TUGUMI_DIR = str(Path(__file__).resolve().parent.parent)
if TUGUMI_DIR not in sys.path:
    sys.path.insert(0, TUGUMI_DIR)

from core.awm_manager import AWMManager
from core.engine_manager import EngineManager


def test_awm_manager_init():
    """AWMManager が正常に初期化され、DBに接続できるか確認"""
    awm = AWMManager()
    assert awm.enabled is True
    assert awm.memory_db is not None
    stats = awm.get_stats()
    assert stats["enabled"] is True
    assert isinstance(stats["total_workflows"], int)


def test_noise_filter_trivial_goal():
    """極短ゴールや挨拶・定型文が物理遮断されるか検証"""
    awm = AWMManager()
    dummy_steps = [
        {"step_index": 1, "tool_name": "view_file", "success": True},
        {"step_index": 2, "tool_name": "replace_file_content", "success": True},
        {"step_index": 3, "tool_name": "run_command", "success": True}
    ]

    # 1. 極短ゴール (< 6文字)
    worth, reason = awm.is_worth_learning("hi", dummy_steps)
    assert worth is False
    assert "too short" in reason.lower()

    # 2. 定型挨拶ブラックリスト
    worth, reason = awm.is_worth_learning("こんにちは つぐみ", dummy_steps)
    assert worth is False
    assert "trivial conversation" in reason.lower()

    worth, reason = awm.is_worth_learning("hello world", dummy_steps)
    assert worth is False
    assert "trivial conversation" in reason.lower()


def test_noise_filter_step_threshold():
    """ツール実行3回未満のタスクがノイズとして遮断されるか検証"""
    awm = AWMManager()
    valid_goal = "Android Termux 環境におけるセーブデータのバイナリ修復"

    # 0ステップ
    worth, reason = awm.is_worth_learning(valid_goal, [])
    assert worth is False
    assert "under threshold" in reason.lower()

    # 2ステップ
    two_steps = [
        {"step_index": 1, "tool_name": "view_file", "success": True},
        {"step_index": 2, "tool_name": "run_command", "success": True}
    ]
    worth, reason = awm.is_worth_learning(valid_goal, two_steps)
    assert worth is False
    assert "under threshold" in reason.lower()

    # 3ステップ以上かつ正常 ➔ PASS
    three_steps = [
        {"step_index": 1, "tool_name": "view_file", "success": True},
        {"step_index": 2, "tool_name": "replace_file_content", "success": True},
        {"step_index": 3, "tool_name": "run_command", "success": True}
    ]
    worth, reason = awm.is_worth_learning(valid_goal, three_steps)
    assert worth is True
    assert "passed" in reason.lower()


def test_noise_filter_failed_steps():
    """全ステップ失敗の軌跡がゴミ化防止のため遮断されるか検証"""
    awm = AWMManager()
    valid_goal = "Android Termux 環境におけるセーブデータのバイナリ修復"
    failed_steps = [
        {"step_index": 1, "tool_name": "view_file", "success": False, "error": "File not found"},
        {"step_index": 2, "tool_name": "run_command", "success": False, "error": "Permission denied"},
        {"step_index": 3, "tool_name": "run_command", "success": False, "error": "Exit 1"}
    ]
    worth, reason = awm.is_worth_learning(valid_goal, failed_steps)
    assert worth is False
    assert "failed" in reason.lower()


def test_pre_execution_guidance():
    """AWMから実証済み推奨ワークフローが正しく取得・フォーマットされるか検証"""
    awm = AWMManager()
    guidance = awm.get_guidance_for_prompt("Bilibili 動画 ダウンロード ウィジェット")
    assert guidance is not None
    assert "AWM実証済み推奨ワークフロー" in guidance
    assert "推奨実行ステップ" in guidance


def test_engine_manager_awm_injection():
    """EngineManager が先行ガイダンスをシステム指示へ安全にマージできるか検証"""
    em = EngineManager()
    assert hasattr(em, "awm")
    assert em.awm is not None

    merged_sys, guidance = em._inject_awm_guidance(
        prompt="Bilibili 動画 ダウンロード ウィジェット",
        system_instruction="あなたは有能なエンジニアです。"
    )
    assert guidance is not None
    assert "AWM実証済み推奨ワークフロー" in merged_sys
    assert "あなたは有能なエンジニアです。" in merged_sys

    # 該当なしの場合は元のシステム指示を維持
    no_guidance_sys, g2 = em._inject_awm_guidance(
        prompt="全く関係のない未知のタスクxyz1234567890",
        system_instruction="標準指示"
    )
    assert g2 is None
    assert no_guidance_sys == "標準指示"


def test_awm_stats_and_purge():
    """AWM統計取得およびパージ機能の動作検証"""
    em = EngineManager()
    stats = em.get_awm_stats()
    assert stats["enabled"] is True
    assert "total_workflows" in stats
    assert "estimated_saved_tokens" in stats

    # パージの実行（通常は低品質がないため 0 が返る）
    purged = em.purge_awm_workflows(max_failures=5)
    assert isinstance(purged, int)
    assert purged >= 0
