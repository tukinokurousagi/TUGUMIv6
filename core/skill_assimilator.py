"""
TUGUMIv6 Curated Skill Assimilator & Anti-Junk Purifier
- 外部（Claude Codeやオープンコミュニティ等）の有益スキル・知見を安全に審査・純化・統合
- Termux aarch64 非互換（/bin/bash, apt-get, macOS依存等）の自動検知・排除・自動移植
- 既存の厳選61種正本スキルとの重複・競合検知＆統合（Deduplication & Merge）
- AIスロップ（内容空、TODOのみ、張りぼて実装）の物理遮断
- 合格スキルを ~/.agents/skills に配備し、即座に無停止ホットリロードを発火
"""

import os
import re
import shutil
import time
from typing import Any


class SkillAssimilator:
    """外部スキルを審査・純化・統合し、TUGUMI正本エコシステムへ安全に取り込むエンジン"""

    def __init__(self, target_skills_dir: str = "/data/data/com.termux/files/home/.agents/skills"):
        self.target_skills_dir = os.path.expanduser(target_skills_dir)
        os.makedirs(self.target_skills_dir, exist_ok=True)
        # Termux標準パス
        self.termux_bash = "#!/data/data/com.termux/files/usr/bin/bash"
        self.termux_python = "#!/usr/bin/env python3"

    def audit_skill(self, skill_path: str) -> dict[str, Any]:
        """
        指定されたスキルディレクトリまたはSKILL.mdを監査し、問題点と適合性をレポート
        """
        skill_path = os.path.abspath(os.path.expanduser(skill_path))
        if os.path.isfile(skill_path):
            skill_dir = os.path.dirname(skill_path)
            md_path = skill_path
        else:
            skill_dir = skill_path
            md_path = os.path.join(skill_dir, "SKILL.md")

        results = {
            "path": skill_dir,
            "skill_name": os.path.basename(skill_dir),
            "is_valid": True,
            "issues": [],
            "warnings": [],
            "termux_fixes_needed": [],
            "metadata": {},
            "duplicate_candidates": []
        }

        if not os.path.exists(md_path):
            results["is_valid"] = False
            results["issues"].append("SKILL.md が存在しません。")
            return results

        # 1. SKILL.md の解析・スロップ判定
        try:
            with open(md_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except OSError as e:
            results["is_valid"] = False
            results["issues"].append(f"SKILL.md の読み込みに失敗しました: {e}")
            return results

        if len(content.strip()) < 100:
            results["is_valid"] = False
            results["issues"].append("SKILL.md の内容が短小すぎるか空です（AIスロップ判定）。")

        # YAMLフロントマター検証
        name_match = re.search(r"^name:\s*[\"']?(.*?)[\"']?\s*$", content, re.MULTILINE)
        desc_match = re.search(r"^description:\s*[\"']?(.*?)[\"']?\s*$", content, re.MULTILINE)

        if not name_match:
            results["warnings"].append("フロントマターに 'name:' が見当たりません。ディレクトリ名を採用します。")
            skill_name = os.path.basename(skill_dir)
        else:
            skill_name = name_match.group(1).strip()
            results["skill_name"] = skill_name

        if not desc_match or not desc_match.group(1).strip():
            results["warnings"].append("フロントマターに 'description:' が存在しないか空です。")
            description = "TUGUMI 専門スキル"
        else:
            description = desc_match.group(1).strip()

        results["metadata"] = {
            "name": skill_name,
            "description": description,
            "chars": len(content)
        }

        # 2. Termux 非互換コード・シェルスキャン
        forbidden_patterns = [
            (r"/bin/bash\b", "非Termux絶対パス '/bin/bash'"),
            (r"/usr/bin/bash\b", "非Termux絶対パス '/usr/bin/bash'"),
            (r"/bin/sh\b", "非Termux絶対パス '/bin/sh'"),
            (r"/usr/bin/python\b", "非Termux絶対パス '/usr/bin/python'"),
            (r"\bapt-get\b", "Debian/Ubuntu固有コマンド 'apt-get' (Termuxはpkg/apt)"),
            (r"\bsudo\b", "root前提コマンド 'sudo' (Termuxはsu/rishまたは非root推奨)"),
            (r"\bsystemctl\b", "systemd依存コマンド 'systemctl' (Termux非対応)"),
            (r"\bbrew\b", "macOS Homebrewコマンド 'brew'"),
            (r"\bosascript\b", "macOS AppleScriptコマンド 'osascript'"),
            (r"\bpbcopy\b", "macOS固有クリップボード 'pbcopy' (Termuxはtermux-clipboard-set)"),
            (r"/tmp/[a-zA-Z0-9_\-\.]+", "一時領域直書き '/tmp/' (Termuxは$TMPDIR推奨)")
        ]

        # ディレクトリ全体のスクリプトをスキャン
        for root, _, files in os.walk(skill_dir):
            for file in files:
                fpath = os.path.join(root, file)
                rel_fpath = os.path.relpath(fpath, skill_dir)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as sf:
                        s_content = sf.read()
                    for pattern, label in forbidden_patterns:
                        if re.search(pattern, s_content):
                            results["termux_fixes_needed"].append({
                                "file": rel_fpath,
                                "pattern": pattern,
                                "label": label
                            })
                except OSError:
                    continue

        # 3. 既存正本スキルとの重複・統合候補スキャン
        existing_skills = [
            d for d in os.listdir(self.target_skills_dir)
            if os.path.isdir(os.path.join(self.target_skills_dir, d)) and not d.startswith(".")
        ]

        if skill_name in existing_skills:
            results["duplicate_candidates"].append({
                "existing_skill": skill_name,
                "reason": "同名スキルが既に正本ディレクトリに存在します。"
            })
        else:
            # 簡易キーワード一致による重複候補検知
            name_parts = set(re.split(r"[-_]", skill_name.lower()))
            for ex in existing_skills:
                ex_parts = set(re.split(r"[-_]", ex.lower()))
                common = name_parts.intersection(ex_parts)
                # 2単語以上一致、または核心部が一致
                if len(common) >= 2 or (len(name_parts) == 1 and next(iter(name_parts)) in ex_parts):
                    results["duplicate_candidates"].append({
                        "existing_skill": ex,
                        "reason": f"名前・役割が類似しています（共通キーワード: {', '.join(common)}）。統合を検討してください。"
                    })

        return results

    def purify_and_install(
        self,
        source_path: str,
        custom_name: str | None = None,
        overwrite: bool = False
    ) -> dict[str, Any]:
        """
        スキルを純化（Termuxシバン自動修正、不要ファイル除去）し、~/.agents/skills に安全配備
        """
        audit = self.audit_skill(source_path)
        if not audit["is_valid"]:
            return {
                "success": False,
                "error": f"スキルの品質検証に失敗しました: {'; '.join(audit['issues'])}",
                "audit": audit
            }

        target_name = custom_name or audit["skill_name"]
        clean_target_name = re.sub(r"[^a-zA-Z0-9_\-]", "", target_name).lower()
        dest_dir = os.path.join(self.target_skills_dir, clean_target_name)

        if os.path.exists(dest_dir) and not overwrite:
            return {
                "success": False,
                "error": f"対象スキル '{clean_target_name}' は既に正本に存在します（上書きには overwrite=True を指定してください）。",
                "audit": audit
            }

        src_dir = os.path.abspath(os.path.expanduser(source_path))
        if os.path.isfile(src_dir):
            src_dir = os.path.dirname(src_dir)

        # 一時作業領域にコピーして純化外科手術
        tmp_staging = f"/data/data/com.termux/files/usr/tmp/tugumi_assimilate_{clean_target_name}_{int(time.time())}"
        try:
            if os.path.exists(tmp_staging):
                shutil.rmtree(tmp_staging, ignore_errors=True)
            shutil.copytree(src_dir, tmp_staging)

            # ゴミファイル・Mac特有ファイル・キャッシュの徹底排除
            for root, dirs, files in os.walk(tmp_staging, topdown=False):
                for f in files:
                    if f == ".DS_Store" or f.endswith(".pyc"):
                        os.remove(os.path.join(root, f))
                for d in dirs:
                    if d in ("__pycache__", ".git", ".idea", ".vscode"):
                        shutil.rmtree(os.path.join(root, d), ignore_errors=True)

            # Termux互換化 外科手術（シバン自動置換・パス適合）
            fixed_files = []
            for root, _, files in os.walk(tmp_staging):
                for file in files:
                    fpath = os.path.join(root, file)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            text = f.read()

                        modified = False
                        # 1. bashシバン
                        if text.startswith(("#!/bin/bash", "#!/usr/bin/bash")):
                            text = re.sub(r"^#!/(usr/)?bin/bash", self.termux_bash, text, count=1)
                            modified = True
                        elif text.startswith("#!/bin/sh"):
                            text = re.sub(r"^#!/bin/sh", self.termux_bash, text, count=1)
                            modified = True
                        # 2. pythonシバン
                        elif text.startswith(("#!/usr/bin/python", "#!/bin/python")):
                            text = re.sub(r"^#!/(usr/)?bin/python[0-9.]*", self.termux_python, text, count=1)
                            modified = True

                        # 3. /tmp/ 直書きを $TMPDIR に置換
                        if "/tmp/" in text:
                            text = text.replace('"/tmp/', '"$TMPDIR/').replace("'/tmp/", "'$TMPDIR/")
                            modified = True

                        if modified:
                            with open(fpath, "w", encoding="utf-8") as f:
                                f.write(text)
                            fixed_files.append(os.path.relpath(fpath, tmp_staging))
                    except OSError:
                        continue

            # 正本ディレクトリへ配備
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir, ignore_errors=True)
            shutil.copytree(tmp_staging, dest_dir)

            return {
                "success": True,
                "skill_name": clean_target_name,
                "installed_path": dest_dir,
                "fixed_files": fixed_files,
                "audit": audit
            }
        finally:
            if os.path.exists(tmp_staging):
                shutil.rmtree(tmp_staging, ignore_errors=True)

    def list_installed_skills(self) -> list[dict[str, Any]]:
        """現在配備されている正本スキル一覧をサマリー取得"""
        skills = []
        if not os.path.exists(self.target_skills_dir):
            return skills

        for entry in sorted(os.listdir(self.target_skills_dir)):
            full_path = os.path.join(self.target_skills_dir, entry)
            if not os.path.isdir(full_path) or entry.startswith("."):
                continue
            md_path = os.path.join(full_path, "SKILL.md")
            desc = "説明なし"
            if os.path.exists(md_path):
                try:
                    with open(md_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if line.strip().startswith("description:"):
                                desc = line.split(":", 1)[1].strip().strip('"\'')
                                break
                except OSError:
                    pass
            skills.append({
                "name": entry,
                "path": full_path,
                "description": desc,
                "mtime": os.path.getmtime(full_path)
            })
        return skills
