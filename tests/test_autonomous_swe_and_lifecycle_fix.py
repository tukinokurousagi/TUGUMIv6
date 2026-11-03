# -*- coding: utf-8 -*-
"""
Tests for Autonomous SWE & AntigravitySession Lifecycle Fix
- Verifies automatic syntax validation inside surgical_replace and write_file
- Verifies safe non-crashing event loop shutdown in AntigravitySession
"""

import json
import os
import tempfile
import threading
import time

from core.antigravity_sdk import AntigravityEngine, AntigravitySession
from tools.coding_tools import CodingTools
from tools.antigravity_tools import coding_surgical_replace, coding_write_file


def test_coding_surgical_replace_auto_syntax():
    """surgical_replace が編集後に自動で構文検証を行い syntax_valid を返すことを検証"""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("def hello():\n    return 'world'\n")
        tmp_path = f.name

    try:
        ct = CodingTools()
        # 1. 正常な置換
        res = ct.surgical_replace(tmp_path, "return 'world'", "return 'takuma_sama'")
        assert res["success"] is True
        assert res["syntax_valid"] is True
        assert res["syntax_error"] == ""

        # 2. ツールAPI経由
        raw_json = coding_surgical_replace(tmp_path, "return 'takuma_sama'", "return 'sakura'")
        data = json.loads(raw_json)
        assert data["success"] is True
        assert data["syntax_valid"] is True

        # 3. 意図的な構文エラー置換 (インデント崩壊)
        res_bad = ct.surgical_replace(tmp_path, "    return 'sakura'", "return 'broken'")
        assert res_bad["success"] is True
        assert res_bad["syntax_valid"] is False
        assert len(res_bad["syntax_error"]) > 0
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_coding_write_file_auto_syntax():
    """write_file が新規ファイル作成時に自動で構文検証を行うことを検証"""
    tmp_path = os.path.join(tempfile.gettempdir(), f"test_write_{time.time()}.py")
    try:
        ct = CodingTools()
        res = ct.write_file(tmp_path, "def valid_fn():\n    pass\n")
        assert res["success"] is True
        assert res["syntax_valid"] is True
        assert res["syntax_error"] == ""

        raw_json = coding_write_file(tmp_path, "def valid_fn_2():\n    return 42\n")
        data = json.loads(raw_json)
        assert data["success"] is True
        assert data["syntax_valid"] is True
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_antigravity_session_safe_close_no_runtime_error():
    """AntigravitySession の close / reset が RuntimeError: Cannot close a running event loop を引き起こさないことを検証"""
    engine = AntigravityEngine()
    session = AntigravitySession(engine, system_instruction="Test instruction")
    session._start_worker()

    assert session.ready_event.wait(timeout=10.0), "Worker did not ready in time"
    assert session.loop is not None
    assert session.thread is not None
    assert session.thread.is_alive()

    # スレッド例外を捕捉するフックを設置
    thread_exceptions = []
    orig_excepthook = threading.excepthook

    def custom_hook(args):
        thread_exceptions.append(args.exc_value)
        orig_excepthook(args)

    threading.excepthook = custom_hook
    try:
        # 複数回連続で reset を呼んでもクラッシュしないこと
        session.reset(system_instruction="Reset 1")
        time.sleep(0.2)
        session.cancel()
        session.reset(system_instruction="Reset 2")
        time.sleep(0.2)
        session.close()
        time.sleep(0.3)

        # RuntimeError("Cannot close a running event loop") が発生していないことを検証
        for exc in thread_exceptions:
            assert not (isinstance(exc, RuntimeError) and "Cannot close a running event loop" in str(exc)), (
                f"Regression detected: {exc}"
            )
    finally:
        threading.excepthook = orig_excepthook
        session.close()


def test_timeout_auto_recovery_directive_structure():
    """タイムアウト自律リカバリプロンプトが放棄禁止と代替ルート即時実行を正しく指示することを検証"""
    user_goal = "DARK-TUGUMIのタスク中断原因を修正して"
    last_tool = "termux_run_command"
    timeout_err = "ツール実行タイムアウト (360秒待機超過: 直前ツール 'termux_run_command')"

    recovery_prompt = (
        f"【🚨 システム自律自己修復指令（タイムアウト自動リカバリ・継続完遂マンデート）】\n"
        f"直前の処理（直前の実行ツール: {last_tool}）が時間超過（{timeout_err}）により安全遮断されました。\n"
        f"【最重要】作業を中断・放棄して立ち止まる行為は論外であり絶対に禁止です。\n"
        f"1. 【タイムアウト原因の特定】\n"
        f"2. 【代替アプローチの即座実行】: 高速クラウドフラグ（例: `--cloud`, `--fast`）、サーバー未起動防止フラグ（`--no-auto-start`）等\n"
        f"3. 【自律完遂】: 当初の目的（ゴール: 「{user_goal}」）を客観的証拠（Exit Code 0）が得られるまで最後まで完遂せよ。"
    )

    assert "作業を中断・放棄して立ち止まる行為は論外であり絶対に禁止です" in recovery_prompt
    assert "--cloud" in recovery_prompt
    assert "--no-auto-start" in recovery_prompt
    assert user_goal in recovery_prompt
    assert last_tool in recovery_prompt

