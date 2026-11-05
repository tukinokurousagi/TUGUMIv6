# -*- coding: utf-8 -*-
"""
TUGUMIv6 Autonomous Self-Healing & Deterministic Recovery Engine (AutoHeal)
- Deterministic AST/Syntax & Ruff Auto-Repair (Zero LLM Quota Consumption)
- File Snapshot & Subdirectory-Aware Rollback System
- Automatic 5-Whys Root Cause Recording into Failure Guard
"""

import json
import os
import re
import shutil
import subprocess
import time
import traceback
from typing import Dict, Any, Optional, Callable, List

from core.reflection_engine import ReflectionEngine
from core.verifier import SystemVerifier

TUGUMI_V6_ROOT = "/data/data/com.termux/files/home/TUGUMIv6"
SNAPSHOT_DIR = os.path.join(TUGUMI_V6_ROOT, "data", "snapshots")


class AutoHealEngine:
    """
    Autonomous Self-Healing & Fault-Tolerant Execution Engine for TUGUMIv6.
    Performs deterministic local syntax/lint healing and snapshot restoration
    without hidden background LLM calls.
    """

    def __init__(
        self,
        workspace_root: str = TUGUMI_V6_ROOT,
        gemini_client: Optional[Any] = None,
        reflection_engine: Optional[ReflectionEngine] = None,
        verifier: Optional[SystemVerifier] = None,
    ):
        self.workspace_root = os.path.abspath(workspace_root)
        self._client = gemini_client
        self.reflection = reflection_engine or ReflectionEngine()
        self.verifier = verifier or SystemVerifier(workspace_root=self.workspace_root)
        self.snapshot_dir = SNAPSHOT_DIR
        os.makedirs(self.snapshot_dir, exist_ok=True)

    @property
    def client(self):
        if self._client is None:
            from core.gemini_client import GeminiClient
            self._client = GeminiClient()
        return self._client

    # =========================================================================
    # 1. Snapshot & Instant Rollback System (Subdirectory-Aware)
    # =========================================================================

    def _encode_rel_path(self, file_path: str) -> str:
        abs_path = os.path.abspath(file_path)
        try:
            rel = os.path.relpath(abs_path, self.workspace_root)
            if not rel.startswith(".."):
                return rel.replace(os.sep, "__")
        except ValueError:
            pass
        return os.path.basename(abs_path)

    def create_file_snapshot(self, file_path: str) -> Optional[str]:
        """Create a timestamped backup snapshot of a file before modification."""
        if not os.path.exists(file_path):
            return None
        try:
            abs_path = os.path.abspath(file_path)
            encoded_name = self._encode_rel_path(abs_path)
            ts = int(time.time() * 1000)
            snap_name = f"{encoded_name}.{ts}.snap"
            snap_path = os.path.join(self.snapshot_dir, snap_name)
            shutil.copy2(abs_path, snap_path)

            meta_path = f"{snap_path}.meta.json"
            with open(meta_path, "w", encoding="utf-8") as mf:
                json.dump({"original_path": abs_path, "timestamp": ts}, mf, ensure_ascii=False)

            self._prune_old_snapshots(encoded_name, keep=5)
            return snap_path
        except Exception:
            return None

    def _prune_old_snapshots(self, encoded_name: str, keep: int = 5) -> None:
        """Keep only the N most recent snapshots per file."""
        try:
            prefix = f"{encoded_name}."
            snaps = [
                os.path.join(self.snapshot_dir, f)
                for f in os.listdir(self.snapshot_dir)
                if f.startswith(prefix) and f.endswith(".snap")
            ]
            snaps.sort(key=os.path.getmtime, reverse=True)
            for old_snap in snaps[keep:]:
                try:
                    os.remove(old_snap)
                    meta_p = f"{old_snap}.meta.json"
                    if os.path.exists(meta_p):
                        os.remove(meta_p)
                except OSError:
                    pass
        except Exception:
            pass

    def find_latest_snapshot(self, file_path: str) -> Optional[str]:
        """Locate the most recent snapshot for a given file path."""
        abs_path = os.path.abspath(file_path)
        encoded_name = self._encode_rel_path(abs_path)
        base_name = os.path.basename(abs_path)
        candidates: List[str] = []
        try:
            for f in os.listdir(self.snapshot_dir):
                if not f.endswith(".snap"):
                    continue
                if f.startswith(f"{encoded_name}.") or f.startswith(f"{base_name}."):
                    candidates.append(os.path.join(self.snapshot_dir, f))
            if candidates:
                candidates.sort(key=os.path.getmtime, reverse=True)
                return candidates[0]
        except Exception:
            pass
        return None

    def restore_file_snapshot(self, snap_path: str, target_path: Optional[str] = None) -> bool:
        """Restore a file from its snapshot path."""
        if not snap_path or not os.path.exists(snap_path):
            return False
        try:
            if not target_path:
                meta_path = f"{snap_path}.meta.json"
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r", encoding="utf-8") as mf:
                            meta = json.load(mf)
                            target_path = meta.get("original_path")
                    except Exception:
                        target_path = None
                if not target_path:
                    snap_name = os.path.basename(snap_path)
                    parts = snap_name.rsplit(".", 2)
                    if len(parts) == 3 and parts[2] == "snap":
                        rel_restored = parts[0].replace("__", os.sep)
                        target_path = os.path.join(self.workspace_root, rel_restored)
                    else:
                        return False
            os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
            shutil.copy2(snap_path, target_path)
            return True
        except Exception:
            return False

    # =========================================================================
    # 2. Deterministic Code Syntax & Lint Auto-Repair
    # =========================================================================

    def _deterministic_source_sanitize(self, file_path: str) -> bool:
        """Apply deterministic local source repairs (BOM/null removal, CRLF->LF, tab expansion, shebang fix)."""
        try:
            with open(file_path, "rb") as f:
                raw = f.read()

            modified = False
            if raw.startswith(b"\xef\xbb\xbf"):
                raw = raw[3:]
                modified = True
            if b"\x00" in raw:
                raw = raw.replace(b"\x00", b"")
                modified = True

            text = raw.decode("utf-8", errors="replace")
            if "\r\n" in text or "\r" in text:
                text = text.replace("\r\n", "\n").replace("\r", "\n")
                modified = True

            if file_path.endswith(".py") and "\t" in text:
                lines = [line.expandtabs(4) for line in text.split("\n")]
                text = "\n".join(lines)
                modified = True

            if file_path.endswith((".sh", ".bash")) and text.startswith("#!/bin/bash"):
                text = re.sub(r"^#!/bin/bash\b", "#!/data/data/com.termux/files/usr/bin/bash", text, count=1)
                modified = True

            if text and not text.endswith("\n"):
                text += "\n"
                modified = True

            if modified:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(text)
            return modified
        except Exception:
            return False

    def heal_file_syntax(self, file_path: str) -> Dict[str, Any]:
        """
        Deterministically repair syntax/lint issues in a Python or Bash file without LLM calls.
        Pipeline:
          1. Verify current syntax via SystemVerifier.
          2. Apply deterministic source sanitization (BOM, null bytes, CRLF, TabError, Termux shebang).
          3. Apply `ruff check --fix` for Python files if available.
          4. Fallback to latest valid snapshot if syntax remains broken.
        """
        check_res = self.verifier.check_syntax(file_path)
        if check_res["valid"]:
            return {
                "status": "already_valid",
                "file": file_path,
                "healed": True,
                "method": "none",
                "details": check_res.get("message", "Syntax OK"),
            }

        initial_error = check_res.get("error") or "Syntax check failed"
        methods_tried: List[str] = []

        # Stage 1: Deterministic text/encoding/indentation repair
        if self._deterministic_source_sanitize(file_path):
            methods_tried.append("source_sanitize")
            recheck = self.verifier.check_syntax(file_path)
            if recheck["valid"]:
                return {
                    "status": "healed",
                    "file": file_path,
                    "healed": True,
                    "method": "deterministic_sanitize",
                    "details": "Repaired via deterministic source sanitization",
                }

        # Stage 2: Ruff auto-fix for Python files
        if file_path.endswith(".py") and shutil.which("ruff"):
            methods_tried.append("ruff_fix")
            try:
                subprocess.run(
                    ["ruff", "check", "--fix", file_path],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            except Exception:
                pass
            recheck = self.verifier.check_syntax(file_path)
            if recheck["valid"]:
                return {
                    "status": "healed",
                    "file": file_path,
                    "healed": True,
                    "method": "ruff_autofix",
                    "details": "Repaired via ruff check --fix",
                }

        # Stage 3: Snapshot rollback fallback
        latest_snap = self.find_latest_snapshot(file_path)
        if latest_snap:
            methods_tried.append("snapshot_restore")
            if self.restore_file_snapshot(latest_snap, target_path=file_path):
                recheck = self.verifier.check_syntax(file_path)
                if recheck["valid"]:
                    return {
                        "status": "healed",
                        "file": file_path,
                        "healed": True,
                        "method": "snapshot_rollback",
                        "details": f"Restored from valid snapshot {os.path.basename(latest_snap)}",
                    }

        # Record failure lesson for manual follow-up
        self.reflection.record_failure(
            keyword=f"SyntaxHeal:{os.path.basename(file_path)}",
            cause=initial_error[:200],
            forbidden_action="構文破損状態の放置",
            correct_alternative="AST/Ruff検証ゲートを通過する外科的パッチ適用",
        )
        return {
            "status": "failed",
            "file": file_path,
            "healed": False,
            "method": ",".join(methods_tried) or "none",
            "error": initial_error,
        }

    # =========================================================================
    # 3. Safe Execution Wrapper with Automatic 5-Whys & Recovery
    # =========================================================================

    def execute_with_autoheal(
        self,
        task_name: str,
        func: Callable,
        *args,
        max_retries: int = 2,
        fallback_func: Optional[Callable] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute any function with automatic retry, 5-Whys reflection,
        and Failure Guard recording upon failure.
        """
        last_err = None
        for attempt in range(1, max_retries + 2):
            try:
                result = func(*args, **kwargs)
                return {
                    "success": True,
                    "task": task_name,
                    "attempt": attempt,
                    "result": result
                }
            except Exception as e:
                last_err = f"{type(e).__name__}: {str(e)}"
                tb_str = traceback.format_exc()

                whys = self.reflection.analyze_5_whys(last_err, context_details=f"Task: {task_name}, Attempt: {attempt}")
                self.reflection.record_failure(
                    keyword=task_name,
                    cause=last_err[:200],
                    forbidden_action=f"Uncaught exception in {task_name}",
                    correct_alternative=whys.get("recommended_fix") or "Apply exponential backoff or fallback execution path"
                )

                if attempt <= max_retries:
                    time.sleep(0.5 * attempt)
                    continue

                if fallback_func is not None:
                    try:
                        fb_res = fallback_func(*args, **kwargs)
                        return {
                            "success": True,
                            "task": task_name,
                            "attempt": attempt,
                            "healed_via_fallback": True,
                            "result": fb_res
                        }
                    except Exception as fb_e:
                        last_err = f"Primary: {last_err} | Fallback: {fb_e}"

                return {
                    "success": False,
                    "task": task_name,
                    "attempt": attempt,
                    "error": last_err,
                    "traceback": tb_str[-500:]
                }

    # =========================================================================
    # 4. Workspace Health Scan & Batch Auto-Repair
    # =========================================================================

    def scan_workspace_syntax(self) -> Dict[str, Any]:
        """Scan all Python and Bash files in TUGUMIv6 for syntax errors."""
        checked_files = 0
        broken_files = []

        for root, dirs, files in os.walk(self.workspace_root):
            dirs[:] = [
                d for d in dirs
                if not d.startswith(".")
                and d not in ("__pycache__", "node_modules", "venv", ".git", "snapshots", "skills")
            ]
            for f in files:
                if f.endswith((".py", ".sh")):
                    full_path = os.path.join(root, f)
                    checked_files += 1
                    res = self.verifier.check_syntax(full_path)
                    if not res["valid"]:
                        broken_files.append({
                            "file": full_path,
                            "error": res["error"]
                        })

        return {
            "workspace": self.workspace_root,
            "checked_count": checked_files,
            "broken_count": len(broken_files),
            "broken_files": broken_files,
            "healthy": len(broken_files) == 0
        }

    def heal_all_broken(self) -> Dict[str, Any]:
        """Scan workspace and automatically heal any broken Python/Bash files."""
        scan = self.scan_workspace_syntax()
        if scan["healthy"]:
            return {
                "status": "healthy",
                "scanned": scan["checked_count"],
                "broken_found": 0,
                "healed_count": 0,
                "failed_count": 0,
                "details": []
            }

        healed_count = 0
        failed_count = 0
        details = []

        for item in scan["broken_files"]:
            res = self.heal_file_syntax(item["file"])
            details.append(res)
            if res.get("healed"):
                healed_count += 1
            else:
                failed_count += 1

        return {
            "status": "recovered" if failed_count == 0 else "partial_recovery",
            "scanned": scan["checked_count"],
            "broken_found": scan["broken_count"],
            "healed_count": healed_count,
            "failed_count": failed_count,
            "details": details
        }
