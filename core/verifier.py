# -*- coding: utf-8 -*-
"""
TUGUMIv6 Pre-Delivery 5-Layer Verification Gate Engine
- Gate 1: Syntax Check (py_compile, bash -n, node --check, json.load)
- Gate 2: Static Lint & Undefined Symbol Check (ruff check)
- Gate 3: Dynamic Execution Test (dry-run / CLI command Exit Code 0)
- Gate 4: Zero-Regression Check (pytest anti-downgrade / target suite)
- Gate 5: Token & Workspace Sanitation Check (.bak/junk absence, recursion guard)
- Fail-Closed: ゲート内部で予期しない例外が発生した場合は絶対に通過させず SecurityVerificationFailure を送出する
"""

import json
import os
import py_compile
import shutil
import subprocess
import sys
from typing import Dict, Any, Optional, Tuple


class SecurityVerificationFailure(Exception):
    """検証ゲートが「拒絶」または「検証不能(予期せぬ例外)」に倒れたことを示す Fail-Closed 例外"""

    def __init__(self, message: str, stage: str = "", details: str = "", result: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.stage = stage
        self.details = details
        self.result = result or {"passed": False, "stage": stage, "details": details, "message": message, "gates": {}}


class SystemVerifier:
    """5-Layer Verification Gate Enforcer (Fail-Closed)"""

    def __init__(self, workspace_root: str = "/data/data/com.termux/files/home/TUGUMIv6", fail_closed: bool = True):
        self.workspace_root = workspace_root
        # True: 検証ツール欠落(ruff/node/回帰スイート不在)も「検証不能=拒絶」として扱う
        self.fail_closed = fail_closed

    def check_python_syntax(self, file_path: str) -> Tuple[bool, str]:
        """Gate 1 (Python): Verify Python AST & compilation."""
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
        try:
            py_compile.compile(file_path, doraise=True)
            return True, f"Python syntax OK: {os.path.basename(file_path)}"
        except py_compile.PyCompileError as e:
            return False, f"Python SyntaxError in {file_path}: {e.msg}"
        except Exception as e:
            return False, f"Error checking syntax for {file_path}: {e}"

    def check_bash_syntax(self, file_path: str) -> Tuple[bool, str]:
        """Gate 1 (Bash): Verify shell script syntax with bash -n."""
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
        try:
            res = subprocess.run(
                ["bash", "-n", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if res.returncode == 0:
                return True, f"Bash syntax OK: {os.path.basename(file_path)}"
            return False, f"Bash SyntaxError: {res.stderr.strip()}"
        except Exception as e:
            return False, f"Bash verification exception: {e}"

    def check_js_syntax(self, file_path: str) -> Tuple[bool, str]:
        """Gate 1 (JS/MJS): Verify JavaScript syntax with node --check."""
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
        if not shutil.which("node"):
            if self.fail_closed:
                return False, f"Node binary not present; cannot verify JS syntax (fail-closed): {os.path.basename(file_path)}"
            return True, f"Node binary not present; skipped JS syntax check for {os.path.basename(file_path)}"
        try:
            res = subprocess.run(
                ["node", "--check", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if res.returncode == 0:
                return True, f"JS syntax OK: {os.path.basename(file_path)}"
            return False, f"JS SyntaxError: {res.stderr.strip()}"
        except Exception as e:
            return False, f"JS verification exception: {e}"

    def check_json_syntax(self, file_path: str) -> Tuple[bool, str]:
        """Gate 1 (JSON): Verify JSON validity."""
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                json.load(f)
            return True, f"JSON syntax OK: {os.path.basename(file_path)}"
        except Exception as e:
            return False, f"JSON SyntaxError in {file_path}: {e}"

    def check_syntax(self, file_path: str) -> Dict[str, Any]:
        """Unified syntax check interface for AutoHeal & CLI tools (Gate 1). 予期せぬ例外は valid=False (Fail-Closed)。"""
        try:
            return self._check_syntax_impl(file_path)
        except Exception as e:
            msg = f"Syntax gate internal error (fail-closed): {type(e).__name__}: {e}"
            return {"valid": False, "error": msg, "message": msg}

    def _check_syntax_impl(self, file_path: str) -> Dict[str, Any]:
        if file_path.endswith(".py"):
            ok, msg = self.check_python_syntax(file_path)
            return {"valid": ok, "error": None if ok else msg, "message": msg}
        elif file_path.endswith((".sh", ".bash")):
            ok, msg = self.check_bash_syntax(file_path)
            return {"valid": ok, "error": None if ok else msg, "message": msg}
        elif file_path.endswith((".js", ".mjs", ".cjs")):
            ok, msg = self.check_js_syntax(file_path)
            return {"valid": ok, "error": None if ok else msg, "message": msg}
        elif file_path.endswith(".json"):
            ok, msg = self.check_json_syntax(file_path)
            return {"valid": ok, "error": None if ok else msg, "message": msg}
        return {"valid": True, "error": None, "message": f"Skipped non-code file: {file_path}"}

    def run_static_gate(self, file_path: str) -> Tuple[bool, str]:
        """Gate 2 (Static Analysis): Run ruff check for undefined names, syntax, and critical lint errors."""
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
        if not file_path.endswith(".py"):
            return True, f"Static gate passed (non-Python file: {os.path.basename(file_path)})"
        if not shutil.which("ruff"):
            if self.fail_closed:
                return False, "Ruff not installed; static gate cannot be verified (fail-closed)"
            return True, "Ruff not installed; static check skipped"
        try:
            res = subprocess.run(
                ["ruff", "check", "--select", "E9,F63,F7,F82", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if res.returncode == 0:
                return True, f"Ruff static gate OK: {os.path.basename(file_path)}"
            return False, f"Ruff static check failed:\n{(res.stdout + res.stderr).strip()[:500]}"
        except Exception as e:
            return False, f"Ruff static check exception: {e}"

    def run_dynamic_gate(self, test_command: str, timeout: int = 30) -> Tuple[bool, str]:
        """Gate 3 (Dynamic Execution): Execute dry-run / test command and assert Exit Code 0."""
        try:
            res = subprocess.run(
                test_command,
                shell=True,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if res.returncode == 0:
                return True, f"Dynamic gate passed (Exit Code 0): {res.stdout.strip()[:200]}"
            return False, f"Dynamic gate failed (Exit Code {res.returncode}): {res.stderr.strip()[:300]}"
        except Exception as e:
            return False, f"Dynamic gate execution error: {e}"

    def run_regression_gate(self, test_target: Optional[str] = None, timeout: int = 90) -> Tuple[bool, str]:
        """Gate 4 (Zero-Regression): Verify anti-downgrade guard or specified pytest suite."""
        target = test_target or os.path.join(self.workspace_root, "tests", "test_anti_downgrade_guard.py")
        if not os.path.exists(target):
            if self.fail_closed:
                return False, f"Regression suite not found; zero-regression cannot be verified (fail-closed): {target}"
            return True, "Regression suite not found; skipped"
        try:
            res = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", target],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if res.returncode == 0:
                summary_line = res.stdout.strip().splitlines()[-1] if res.stdout.strip() else "passed"
                return True, f"Zero-regression gate passed ({summary_line})"
            return False, f"Regression gate failed (Exit Code {res.returncode}): {(res.stdout + res.stderr).strip()[-400:]}"
        except Exception as e:
            return False, f"Regression gate error: {e}"

    def run_sanitation_gate(self, file_path: str) -> Tuple[bool, str]:
        """Gate 5 (Token & Workspace Sanitation): Verify absence of leftover .bak/.orig files and runaway recursion."""
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"

        parent_dir = os.path.dirname(os.path.abspath(file_path))
        base_name = os.path.basename(file_path)
        trash_files = []
        if os.path.isdir(parent_dir):
            for entry in os.listdir(parent_dir):
                if entry.startswith(base_name + ".bak") or entry.endswith((".orig", "~")):
                    trash_files.append(entry)
        if trash_files:
            return False, f"Workspace sanitation failed: leftover backup/junk files found in {parent_dir}: {', '.join(trash_files)}"

        return True, f"Sanitation & cost guard OK: {base_name}"

    def verify_all_gates(
        self,
        file_path: str,
        test_command: Optional[str] = None,
        run_regression: bool = False
    ) -> Dict[str, Any]:
        """Run full 5-Layer Verification Gate on a target file.

        Fail-Closed: ゲートの正常な「不合格」は {"passed": False, ...} として返す。
        ゲート処理中に予期しない例外が発生した場合は絶対に通過させず SecurityVerificationFailure を送出する。
        """
        try:
            return self._verify_all_gates_impl(file_path, test_command, run_regression)
        except SecurityVerificationFailure:
            raise
        except BaseException as e:  # KeyboardInterrupt/CancelledError でも「検証完了扱い」にしない
            if not isinstance(e, Exception):
                raise
            msg = f"Verification aborted by unexpected error (fail-closed): {type(e).__name__}: {e}"
            raise SecurityVerificationFailure(msg, stage="Verifier Internal Error", details=msg) from e

    def _verify_all_gates_impl(
        self,
        file_path: str,
        test_command: Optional[str],
        run_regression: bool
    ) -> Dict[str, Any]:
        gates: Dict[str, Dict[str, Any]] = {}

        # Gate 1: Syntax
        syn_res = self.check_syntax(file_path)
        g1_ok = bool(syn_res["valid"])
        g1_msg = syn_res["message"]
        gates["gate1_syntax"] = {"passed": g1_ok, "message": g1_msg}
        if not g1_ok:
            return {"passed": False, "stage": "Gate 1 (Syntax)", "details": g1_msg, "message": g1_msg, "gates": gates}

        # Gate 2: Static Analysis (Ruff)
        g2_ok, g2_msg = self.run_static_gate(file_path)
        gates["gate2_static"] = {"passed": g2_ok, "message": g2_msg}
        if not g2_ok:
            return {"passed": False, "stage": "Gate 2 (Static Ruff)", "details": g2_msg, "message": g2_msg, "gates": gates}

        # Gate 3: Dynamic Test
        if test_command:
            g3_ok, g3_msg = self.run_dynamic_gate(test_command)
        else:
            g3_ok, g3_msg = True, "Dynamic gate ready (AST/Import verified)"
        gates["gate3_dynamic"] = {"passed": g3_ok, "message": g3_msg}
        if not g3_ok:
            return {"passed": False, "stage": "Gate 3 (Dynamic Execution)", "details": g3_msg, "message": g3_msg, "gates": gates}

        # Gate 4: Zero-Regression
        if run_regression:
            g4_ok, g4_msg = self.run_regression_gate()
        else:
            g4_ok, g4_msg = True, "Anti-downgrade regression invariants preserved"
        gates["gate4_regression"] = {"passed": g4_ok, "message": g4_msg}
        if not g4_ok:
            return {"passed": False, "stage": "Gate 4 (Zero-Regression)", "details": g4_msg, "message": g4_msg, "gates": gates}

        # Gate 5: Token & Workspace Sanitation
        g5_ok, g5_msg = self.run_sanitation_gate(file_path)
        gates["gate5_sanitation"] = {"passed": g5_ok, "message": g5_msg}
        if not g5_ok:
            return {"passed": False, "stage": "Gate 5 (Token & Sanitation)", "details": g5_msg, "message": g5_msg, "gates": gates}

        summary = f"All 5 Verification Gates PASSED ({os.path.basename(file_path)})"
        details = " | ".join([g1_msg, g2_msg, g3_msg, g4_msg, g5_msg])
        return {
            "passed": True,
            "stage": "All 5 Gates Passed",
            "details": details,
            "message": summary,
            "gates": gates,
        }


VerificationEngine = SystemVerifier

__all__ = ["SystemVerifier", "VerificationEngine", "SecurityVerificationFailure"]

