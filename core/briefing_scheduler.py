# -*- coding: utf-8 -*-
"""
TUGUMIv6 Cron & Schedule Manager for Daily Briefing
============================================================
指定時刻（毎朝〇時など）でのインテリジェント・デイリーブリーフィング
自動生成・通知タスクをcrontabへ登録・一覧・削除・管理するエンジン。
AIツールの自律実行およびCLI、WebUIから呼び出し可能。
============================================================
"""

import os
import sys
import re
import uuid
import subprocess
from typing import List, Dict, Any, Optional, Tuple

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TUGUMI_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if TUGUMI_ROOT not in sys.path:
    sys.path.insert(0, TUGUMI_ROOT)

PYTHON_BIN = sys.executable or "/data/data/com.termux/files/usr/bin/python3"
BRIEFING_ENGINE_SCRIPT = os.path.join(TUGUMI_ROOT, "core", "briefing_engine.py")
LOG_PATH = os.path.join(TUGUMI_ROOT, "logs", "cron_briefing.log")


class BriefingScheduler:
    """crontab を用いたデイリーブリーフィング定期実行スケジューラ"""

    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = workspace_root or TUGUMI_ROOT
        self.log_dir = os.path.join(self.workspace_root, "logs")
        os.makedirs(self.log_dir, exist_ok=True)

    def ensure_cron_environment(self) -> Dict[str, Any]:
        """crond デーモンの起動確認 & termux-wake-lock の確認"""
        status = {"crond_running": False, "wake_lock_enabled": False}

        # 1. termux-wake-lock 実行（スリープ時のcron停止防止）
        try:
            subprocess.run(["termux-wake-lock"], capture_output=True, timeout=20)
            status["wake_lock_enabled"] = True
        except Exception:
            pass

        # 2. crond プロセス確認
        try:
            ps_res = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=20)
            if "crond" in ps_res.stdout:
                status["crond_running"] = True
            else:
                # 起動を試みる
                subprocess.run(["crond"], capture_output=True, timeout=20)
                # 再確認
                ps_res2 = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=20)
                if "crond" in ps_res2.stdout:
                    status["crond_running"] = True
        except Exception as e:
            status["error"] = str(e)

        return status

    def parse_time_string(self, time_str: str) -> Tuple[int, int]:
        """
        '07:00', '7:30', '6時', '6:00', '朝7時半', '21:15' などの時間文字列を (hour, minute) に変換
        """
        time_str = time_str.strip().lower()

        # 7:30 or 07:00
        m = re.search(r'(\d{1,2})[:：](\d{1,2})', time_str)
        if m:
            h = int(m.group(1))
            minute = int(m.group(2))
            return h % 24, minute % 60

        # 7時半
        m = re.search(r'(\d{1,2})\s*時\s*半', time_str)
        if m:
            h = int(m.group(1))
            return h % 24, 30

        # 7時 or 7
        m = re.search(r'(\d{1,2})\s*(?:時)?', time_str)
        if m:
            h = int(m.group(1))
            return h % 24, 0

        # デフォルト: 朝 07:00
        return 7, 0

    def get_current_crontab(self) -> str:
        """現在のcrontab内容を取得"""
        try:
            res = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=20)
            if res.returncode == 0:
                return res.stdout
        except Exception:
            pass
        return ""

    def set_current_crontab(self, content: str) -> bool:
        """crontabを安全に更新"""
        try:
            p = subprocess.Popen(
                ["crontab", "-"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = p.communicate(input=content, timeout=20)
            return p.returncode == 0
        except Exception as e:
            print(f"[Crontab Error] {e}", file=sys.stderr)
            return False

    def add_schedule(
        self,
        time_str: str = "07:00",
        topic: Optional[str] = None,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        デイリーブリーフィング作成タスクをcrontabに登録
        """
        cron_env = self.ensure_cron_environment()
        hour, minute = self.parse_time_string(time_str)
        job_id = uuid.uuid4().hex[:8]

        # 実行コマンド作成
        args = []
        if topic:
            args.extend(["--topic", f'"{topic}"'])
        if note:
            args.extend(["--note", f'"{note}"'])
        arg_str = " " + " ".join(args) if args else ""

        cmd = f'{PYTHON_BIN} {BRIEFING_ENGINE_SCRIPT}{arg_str} >> {LOG_PATH} 2>&1'
        tag_comment = (
            f"# [TUGUMI_DAILY_BRIEFING] job_id={job_id} | time={hour:02d}:{minute:02d} | "
            f"topic={topic or '総合インテリジェンス'}"
        )
        cron_line = f"{minute} {hour} * * * {cmd}"

        current_crontab = self.get_current_crontab().strip()
        lines = current_crontab.splitlines() if current_crontab else []
        new_lines = []
        skip_next = False

        # 同一トピック（またはデフォルトブリーフィング）の既存ジョブがあれば更新・置換
        for line in lines:
            if skip_next:
                skip_next = False
                continue
            if "[TUGUMI_DAILY_BRIEFING]" in line:
                # 既存ジョブを置換
                skip_next = True
                continue
            new_lines.append(line)

        new_lines.append(tag_comment)
        new_lines.append(cron_line)

        updated_crontab = "\n".join(new_lines) + "\n"
        success = self.set_current_crontab(updated_crontab)

        if not success:
            raise RuntimeError("crontab の更新に失敗しました。")

        return {
            "status": "success",
            "job_id": job_id,
            "scheduled_time": f"{hour:02d}:{minute:02d}",
            "cron_expression": f"{minute} {hour} * * *",
            "topic": topic or "毎朝の総合インテリジェンス・ブリーフィング",
            "log_path": LOG_PATH,
            "cron_environment": cron_env
        }

    def list_schedules(self) -> List[Dict[str, Any]]:
        """現在登録中のデイリーブリーフィング定期タスク一覧を取得"""
        crontab_txt = self.get_current_crontab()
        if not crontab_txt:
            return []

        schedules = []
        lines = crontab_txt.splitlines()
        for i, line in enumerate(lines):
            if "[TUGUMI_DAILY_BRIEFING]" in line:
                m_id = re.search(r'job_id=([a-f0-9]+)', line)
                m_time = re.search(r'time=(\d{2}:\d{2})', line)
                m_topic = re.search(r'topic=([^|]+)', line)

                job_id = m_id.group(1) if m_id else "unknown"
                time_val = m_time.group(1) if m_time else "unknown"
                topic_val = m_topic.group(1).strip() if m_topic else "総合インテリジェンス"

                cron_cmd = lines[i + 1] if (i + 1) < len(lines) else ""

                schedules.append({
                    "job_id": job_id,
                    "time": time_val,
                    "topic": topic_val,
                    "command": cron_cmd
                })

        return schedules

    def remove_schedule(self, job_id: str) -> Dict[str, Any]:
        """指定された job_id の定期ブリーフィングタスクを crontab から削除"""
        crontab_txt = self.get_current_crontab()
        if not crontab_txt:
            return {"status": "not_found", "message": "登録されているcronタスクはありません。"}

        lines = crontab_txt.splitlines()
        new_lines = []
        removed = False
        skip_next = False

        for line in lines:
            if skip_next:
                skip_next = False
                continue
            if "[TUGUMI_DAILY_BRIEFING]" in line and f"job_id={job_id}" in line:
                skip_next = True
                removed = True
                continue
            new_lines.append(line)

        if not removed:
            return {"status": "not_found", "message": f"job_id={job_id} が見つかりませんでした。"}

        updated_crontab = "\n".join(new_lines) + "\n" if new_lines else ""
        success = self.set_current_crontab(updated_crontab)
        return {
            "status": "success" if success else "error",
            "removed_job_id": job_id
        }

    def clear_all(self) -> Dict[str, Any]:
        """登録されている全ブリーフィング定期タスクを一括削除"""
        crontab_txt = self.get_current_crontab()
        if not crontab_txt:
            return {"status": "success", "removed_count": 0}

        lines = crontab_txt.splitlines()
        new_lines = []
        count = 0
        skip_next = False

        for line in lines:
            if skip_next:
                skip_next = False
                continue
            if "[TUGUMI_DAILY_BRIEFING]" in line:
                skip_next = True
                count += 1
                continue
            new_lines.append(line)

        updated_crontab = "\n".join(new_lines) + "\n" if new_lines else ""
        self.set_current_crontab(updated_crontab)
        return {"status": "success", "removed_count": count}


# 便利関数群
def add_briefing_schedule(time_str: str = "07:00", topic: Optional[str] = None, note: Optional[str] = None) -> Dict[str, Any]:
    return BriefingScheduler().add_schedule(time_str=time_str, topic=topic, note=note)

def list_scheduled_briefings() -> List[Dict[str, Any]]:
    return BriefingScheduler().list_schedules()

def remove_scheduled_briefing(job_id: str) -> Dict[str, Any]:
    return BriefingScheduler().remove_schedule(job_id=job_id)
