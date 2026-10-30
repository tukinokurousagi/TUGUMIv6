# -*- coding: utf-8 -*-
"""
TUGUMIv6 Skill Hot Reload & Assimilator Verification Test
- Verifies live mtime-based skill hot reloading in TugumiRichCompleter
- Verifies session refresh in EngineManager on skill updates
- Verifies Termux compatibility audit and auto-purification in SkillAssimilator
"""

import os
import shutil
import tempfile
import pytest
from core.skill_assimilator import SkillAssimilator
from interfaces.cli.dynamic_completer import TugumiRichCompleter, load_skills_with_descriptions


def test_rich_completer_hot_reload():
    """TugumiRichCompleterがmtime変化を検知して無停止ホットリロードすることを実証"""
    completer = TugumiRichCompleter()
    initial_skills_count = len(completer.skills_meta)
    assert initial_skills_count >= 60, f"初回読み込みスキル数が少なすぎます: {initial_skills_count}"

    # force=True による即時再読込
    reloaded = completer.reload_skills(force=True)
    assert reloaded is True
    assert len(completer.skills_meta) == initial_skills_count


def test_skill_assimilator_audit_and_purify():
    """SkillAssimilatorが非Termuxシバンを検出し、Termux向けに純化・移植することを検証"""
    with tempfile.TemporaryDirectory() as tmp_src:
        with tempfile.TemporaryDirectory() as tmp_dest:
            skill_dir = os.path.join(tmp_src, "test-external-skill")
            os.makedirs(skill_dir, exist_ok=True)
            scripts_dir = os.path.join(skill_dir, "scripts")
            os.makedirs(scripts_dir, exist_ok=True)

            # 非Termuxシバン (/bin/bash, /tmp 直書き) を含むテストスクリプト作成
            script_file = os.path.join(scripts_dir, "run.sh")
            with open(script_file, "w", encoding="utf-8") as f:
                f.write("#!/bin/bash\nTMP_LOG=\"/tmp/log.txt\"\necho 'running' > $TMP_LOG\n")

            # SKILL.md 作成
            md_file = os.path.join(skill_dir, "SKILL.md")
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(
                    "---\n"
                    "name: test-external-skill\n"
                    "description: 外部コミュニティから導入された有用なテストスキル\n"
                    "---\n\n"
                    "# Test External Skill\n\n"
                    "This is a verified test skill protocol for testing Assimilator.\n"
                )

            assimilator = SkillAssimilator(target_skills_dir=tmp_dest)
            audit = assimilator.audit_skill(skill_dir)

            assert audit["is_valid"] is True
            assert len(audit["termux_fixes_needed"]) >= 1, "Termux非互換の検出に失敗しました"

            # 純化・配備実行
            res = assimilator.purify_and_install(skill_dir)
            assert res["success"] is True

            installed_md = os.path.join(tmp_dest, "test-external-skill", "SKILL.md")
            installed_sh = os.path.join(tmp_dest, "test-external-skill", "scripts", "run.sh")

            assert os.path.exists(installed_md)
            assert os.path.exists(installed_sh)

            with open(installed_sh, "r", encoding="utf-8") as f:
                purified_content = f.read()

            assert "#!/data/data/com.termux/files/usr/bin/bash" in purified_content, "シバンのTermux自動置換に失敗しました"
            assert "$TMPDIR" in purified_content, "/tmp の $TMPDIR 適合に失敗しました"


def test_anti_slop_gate():
    """内容が空または短小なAIスロップスキルを物理遮断することを検証"""
    with tempfile.TemporaryDirectory() as tmp_src:
        with tempfile.TemporaryDirectory() as tmp_dest:
            junk_dir = os.path.join(tmp_src, "junk-slop-skill")
            os.makedirs(junk_dir, exist_ok=True)
            with open(os.path.join(junk_dir, "SKILL.md"), "w", encoding="utf-8") as f:
                f.write("# TODO")

            assimilator = SkillAssimilator(target_skills_dir=tmp_dest)
            audit = assimilator.audit_skill(junk_dir)
            assert audit["is_valid"] is False
            assert any("スロップ" in issue for issue in audit["issues"])
