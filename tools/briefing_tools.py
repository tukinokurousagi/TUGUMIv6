# -*- coding: utf-8 -*-
"""
TUGUMIv6 Daily Briefing Tools
============================================================
AIエージェントが自律的にインテリジェント・デイリーブリーフィングの
生成、最新内容確認、定期実行スケジュール登録・削除を実行するためのツールモジュール。
============================================================
"""

import os
import sys
import glob
from typing import Dict, Any, List, Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TUGUMI_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if TUGUMI_ROOT not in sys.path:
    sys.path.insert(0, TUGUMI_ROOT)

class BriefingTools:
    """インテリジェント・デイリーブリーフィング自律実行・管理ツール"""

    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = workspace_root or TUGUMI_ROOT
        from core.briefing_engine import DailyBriefingEngine
        from core.briefing_scheduler import BriefingScheduler
        self.engine = DailyBriefingEngine(workspace_root=self.workspace_root)
        self.scheduler = BriefingScheduler(workspace_root=self.workspace_root)


    def generate_daily_briefing(
        self,
        topic: Optional[str] = None,
        note: Optional[str] = None,
        save_desk: bool = True,
        notify: bool = True
    ) -> Dict[str, Any]:
        """
        愛知県一宮市の天気・AI動向・推し活エンタメ・実機メトリクスを網羅した
        本日のデイリーブリーフィングを即座に生成し、TUGUMIDeskへの保存およびスマホ通知を行います。
        """
        return self.engine.generate_briefing(
            focus_topic=topic,
            note=note,
            save_desk=save_desk,
            send_notify=notify
        )

    def schedule_daily_briefing(
        self,
        time_str: str = "07:00",
        topic: Optional[str] = None,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        指定時刻（例: '07:00' や '朝7時半'）にデイリーブリーフィングを毎朝自動作成・保存・通知するcron定期タスクを自律登録します。
        """
        return self.scheduler.add_schedule(time_str=time_str, topic=topic, note=note)

    def list_scheduled_briefings(self) -> List[Dict[str, Any]]:
        """
        現在登録されている定期デイリーブリーフィングのスケジュール一覧を取得します。
        """
        return self.scheduler.list_schedules()

    def remove_scheduled_briefing(self, job_id: str) -> Dict[str, Any]:
        """
        指定された job_id の定期デイリーブリーフィングスケジュールを削除します。
        """
        return self.scheduler.remove_schedule(job_id=job_id)

    def get_latest_briefing(self) -> Dict[str, Any]:
        """
        直近に作成された最新のデイリーブリーフィングを取得します。
        """
        desk_dir = "/storage/emulated/0/TUGUMIDesk/デイリーブリーフィング"
        local_dir = os.path.join(self.workspace_root, "data", "briefings")

        candidates = []
        if os.path.exists(desk_dir):
            candidates.extend(glob.glob(os.path.join(desk_dir, "*.md")))
        if os.path.exists(local_dir):
            candidates.extend(glob.glob(os.path.join(local_dir, "*.md")))

        if not candidates:
            return {"status": "not_found", "message": "保存されたブリーフィングがまだありません。"}

        # 更新日時順にソート
        candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        latest_file = candidates[0]

        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                content = f.read()
            html_candidate = latest_file.replace(".md", ".html")
            html_path = html_candidate if os.path.exists(html_candidate) else None
            return {
                "status": "success",
                "filepath": latest_file,
                "html_filepath": html_path,
                "filename": os.path.basename(latest_file),
                "mtime": os.path.getmtime(latest_file),
                "content": content
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "filepath": latest_file}
