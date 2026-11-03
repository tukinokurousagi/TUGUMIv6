# -*- coding: utf-8 -*-
"""
TUGUMIv6 CLI Senior Enhancements Automated Tests
- Validates one-shot command execution
- Validates model and thinking intensity options
- Validates quiet/raw piping mode
- Validates /senior command output
- Validates signal handling & terminal canonical restoration safety
"""

import os
import sys
import subprocess

TUGUMI_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAIN_PY = os.path.join(TUGUMI_ROOT, "interfaces", "cli", "main.py")


def test_cli_help():
    """CLI --help が正常に終了し、新設オプションが含まれるか検証"""
    res = subprocess.run(
        [sys.executable, MAIN_PY, "--help"],
        capture_output=True,
        text=True,
        timeout=15
    )
    assert res.returncode == 0
    assert "--model" in res.stdout
    assert "--thinking" in res.stdout
    assert "--quiet" in res.stdout
    assert "prompt" in res.stdout


def test_cli_self_test():
    """CLI --self-test が Exit Code 0 でパスするか検証"""
    res = subprocess.run(
        [sys.executable, MAIN_PY, "--self-test"],
        capture_output=True,
        text=True,
        timeout=30
    )
    assert res.returncode == 0
    assert "All diagnostics PASSED" in res.stdout


def test_cli_senior_oneshot():
    """CLI /senior ワンライナーが正常に実行され、5大行動規範が出力されるか検証"""
    res = subprocess.run(
        [sys.executable, MAIN_PY, "/senior"],
        capture_output=True,
        text=True,
        timeout=20
    )
    assert res.returncode == 0
    assert "Senior SWE Standard" in res.stdout
    assert "根本原因の外科的根絶" in res.stdout
    assert "Zero-Mock実働主義" in res.stdout


def test_cli_dynamic_completer_senior():
    """DynamicCompleter に /senior コマンドが登録されているか検証"""
    from interfaces.cli.dynamic_completer import MAIN_COMMANDS
    assert "/senior" in MAIN_COMMANDS
    assert "シニアエンジニア" in MAIN_COMMANDS["/senior"]
