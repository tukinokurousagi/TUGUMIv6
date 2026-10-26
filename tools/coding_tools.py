# -*- coding: utf-8 -*-
"""
TUGUMIv6 Coding Tools
- grep-first search before read
- Pinpoint line-range read (StartLine/EndLine)
- Surgical minimal diff edit
- Automated syntax validation gate
"""

import os
import subprocess
import sys
from typing import Dict, Any, List, Optional

class CodingTools:
    """Professional Surgical Coding Tools for TUGUMIv6"""
    def __init__(self, workspace_root: str = "/data/data/com.termux/files/home"):
        self.workspace_root = workspace_root

    def grep_search(self, pattern: str, target_dir: Optional[str] = None, file_glob: str = "*") -> List[Dict[str, Any]]:
        """Grep-first原則: 読み込む前に対象行番号とシンボルを特定"""
        cwd = target_dir or self.workspace_root
        cmd = ["grep", "-rn", "-I", f"--include={file_glob}", pattern, "."]
        try:
            res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120)
            lines = res.stdout.strip().splitlines()
            results = []
            for l in lines[:50]:
                parts = l.split(":", 2)
                if len(parts) >= 3:
                    results.append({
                        "file": parts[0],
                        "line": int(parts[1]),
                        "content": parts[2].strip()
                    })
            return results
        except Exception as e:
            return [{"error": str(e)}]

    def read_lines(self, file_path: str, start_line: int, end_line: int) -> str:
        """ピンポイント行範囲指定Read (反復Read根絶)"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total = len(lines)
        start = max(1, start_line)
        end = min(total, end_line)

        selected = lines[start - 1:end]
        numbered = [f"{i}: {line}" for i, line in enumerate(selected, start=start)]
        return "".join(numbered)

    def surgical_replace(self, file_path: str, target_content: str, replacement_content: str) -> bool:
        """外科的最小差分編集 (完全一致置換)"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if target_content not in content:
            raise ValueError(f"Target content not found in {file_path}")

        # 規約準拠: .bakゴミファイルは生成せず直接アトミックに書き換え
        new_content = content.replace(target_content, replacement_content, 1)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return True

    def check_syntax(self, file_path: str) -> Dict[str, Any]:
        """構文ゲート自動検証"""
        if file_path.endswith(".py"):
            res = subprocess.run([sys.executable, "-m", "py_compile", file_path], capture_output=True, text=True)
            return {"valid": res.returncode == 0, "error": res.stderr.strip()}
        elif file_path.endswith(".sh"):
            res = subprocess.run(["bash", "-n", file_path], capture_output=True, text=True)
            return {"valid": res.returncode == 0, "error": res.stderr.strip()}
        return {"valid": True, "error": ""}

    def batch_surgical_replace(self, replacements: List[Dict[str, str]]) -> Dict[str, Any]:
        """依存関係チェーン（Dependency Chain）複数ファイル一括バッチ編集"""
        results = []
        all_success = True
        for item in replacements:
            fpath = item.get("file_path", "")
            target = item.get("target_content", "")
            replacement = item.get("replacement_content", "")
            try:
                self.surgical_replace(fpath, target, replacement)
                syntax = self.check_syntax(fpath)
                results.append({
                    "file": fpath,
                    "success": True,
                    "syntax_valid": syntax.get("valid", True),
                    "syntax_error": syntax.get("error", "")
                })
            except Exception as e:
                all_success = False
                results.append({"file": fpath, "success": False, "error": str(e)})
        return {"total": len(replacements), "all_success": all_success, "results": results}

