# -*- coding: utf-8 -*-
"""
TUGUMIv6 Daily Briefing Comprehensive E2E Tests
============================================================
デイリーブリーフィングの気象データ取得、スケジューラ、ツール群、
WebUIエンドポイント、および保存ロジックの厳格な検証。
============================================================
"""

import os
import sys
from unittest.mock import patch

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TUGUMI_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if TUGUMI_ROOT not in sys.path:
    sys.path.insert(0, TUGUMI_ROOT)

from core.briefing_engine import DailyBriefingEngine
from core.briefing_scheduler import BriefingScheduler
from core.notification_engine import NotificationEngine
from tools.briefing_tools import BriefingTools


def test_01_notification_engine():
    """NotificationEngine の初期化と通知フォールバック検証"""
    engine = NotificationEngine()
    assert hasattr(engine, "send_notification")
    assert hasattr(engine, "speak")
    assert hasattr(engine, "notify_and_speak")

    # dry-run
    res = engine.notify_and_speak(title="Test", message="Test message")
    assert isinstance(res, dict)
    assert "notification" in res
    assert "tts" in res


def test_02_weather_intelligence():
    """愛知県一宮市の完全リアルタイム気象データ取得検証 (Open-Meteo)"""
    engine = DailyBriefingEngine()
    weather = engine.fetch_weather_intelligence()
    assert isinstance(weather, dict)
    assert "愛知県一宮市" in weather.get("location", "")
    assert "current_temp" in weather
    assert "temp_max" in weather
    assert "clothing_advice" in weather
    assert "umbrella_advice" in weather


def test_03_briefing_scheduler_time_parsing():
    """スケジューラの自然言語時間文字列パース検証"""
    sched = BriefingScheduler()
    assert sched.parse_time_string("07:00") == (7, 0)
    assert sched.parse_time_string("06:30") == (6, 30)
    assert sched.parse_time_string("朝7時半") == (7, 30)
    assert sched.parse_time_string("8時") == (8, 0)
    assert sched.parse_time_string("21:45") == (21, 45)


def test_04_briefing_scheduler_crontab_ops():
    """crontab 登録・一覧・削除のモック検証"""
    sched = BriefingScheduler()
    fake_crontab = "# existing cron\n0 12 * * * /path/to/script\n"

    with patch.object(sched, "get_current_crontab", return_value=fake_crontab), \
         patch.object(sched, "set_current_crontab", return_value=True) as mock_set, \
         patch.object(sched, "ensure_cron_environment", return_value={"crond_running": True}):

        # スケジュール登録
        res = sched.add_schedule(time_str="07:00", topic="AI動向")
        assert res["status"] == "success"
        assert res["scheduled_time"] == "07:00"
        assert mock_set.called

        # 一覧取得
        mock_crontab_with_job = (
            fake_crontab +
            f"# [TUGUMI_DAILY_BRIEFING] job_id={res['job_id']} | time=07:00 | topic=AI動向\n"
            f"0 7 * * * python3 /path/to/engine.py\n"
        )
        with patch.object(sched, "get_current_crontab", return_value=mock_crontab_with_job):
            schedules = sched.list_schedules()
            assert len(schedules) >= 1
            assert schedules[0]["job_id"] == res["job_id"]
            assert schedules[0]["time"] == "07:00"

            # 削除
            rm_res = sched.remove_schedule(res["job_id"])
            assert rm_res["status"] == "success"


def test_05_briefing_tools_integration():
    """BriefingTools のインターフェース検証"""
    tools = BriefingTools()
    assert hasattr(tools, "generate_daily_briefing")
    assert hasattr(tools, "schedule_daily_briefing")
    assert hasattr(tools, "list_scheduled_briefings")
    assert hasattr(tools, "remove_scheduled_briefing")
    assert hasattr(tools, "get_latest_briefing")

    latest = tools.get_latest_briefing()
    assert isinstance(latest, dict)
    assert "status" in latest


def test_06_briefing_engine_mock_generation(tmp_path):
    """DailyBriefingEngine の推稿・保存フロー検証 (Mock LLM)"""
    engine = DailyBriefingEngine(workspace_root=str(tmp_path))
    engine.desk_briefing_dir = str(tmp_path / "desk_briefing")
    engine.local_backup_dir = str(tmp_path / "local_briefing")
    os.makedirs(engine.desk_briefing_dir, exist_ok=True)
    os.makedirs(engine.local_backup_dir, exist_ok=True)

    fake_markdown = """# ☀️ 【つぐみデイリーブリーフィング】本日（2026年10月05日）のインテリジェンス・サマリー
## 1. 🌸 拓磨様への朝のご挨拶と温かい今日の一言
最愛のマスター、拓磨様、本日もよろしくお願いいたします。
## 2. 🌤️ 愛知県一宮市・尾張地方のリアルタイム気象インテリジェンス
気温 20℃、晴れ。
## 3. 🧠 最重要ピックアップ・テック＆AIエージェント動向
AIエージェントの最新動向です。
"""

    with patch.object(engine.engine_mgr, "generate", return_value=fake_markdown), \
         patch.object(engine.notifier, "notify_and_speak", return_value={"notification": True, "tts": True}):


        res = engine.generate_briefing(save_desk=True, send_notify=True)
        assert res["status"] == "success"
        assert os.path.exists(res["desk_path"])
        assert os.path.exists(res["local_path"])
        with open(res["desk_path"], "r", encoding="utf-8") as f:
            content = f.read()
        assert "【つぐみデイリーブリーフィング】" in content
        assert "拓磨様" in content


def test_07_web_server_endpoints():
    """FastAPI WebUI サーバーのブリーフィング関連エンドポイント検証"""
    from fastapi.testclient import TestClient
    from interfaces.web.web_server import app

    client = TestClient(app)

    # 1. ツール一覧に tugumi-briefing が含まれていること
    res_tools = client.get("/api/tools/list")
    assert res_tools.status_code == 200
    categories = res_tools.json().get("categories", {})
    research_scripts = categories.get("research", {}).get("scripts", [])
    script_names = [s["name"] for s in research_scripts]
    assert "tugumi-briefing" in script_names

    # 2. 最新ブリーフィング取得
    res_latest = client.get("/api/briefing/latest")
    assert res_latest.status_code == 200
    assert "status" in res_latest.json()

    # 3. 定期スケジュール一覧取得
    res_sched = client.get("/api/briefing/schedules")
    assert res_sched.status_code == 200
    assert "schedules" in res_sched.json()


def test_08_enriched_web_intelligence():
    """AI動向・乃木坂46・日向坂46の強化されたWebリサーチ収集検証"""
    engine = DailyBriefingEngine()
    intel = engine.fetch_web_intelligence()

    assert isinstance(intel, dict)
    assert "ai_frontier" in intel
    assert "ai_agents" in intel
    assert "nogizaka46" in intel
    assert "hinatazaka46" in intel
    assert "culture" in intel

    # 各カテゴリで実際に最新情報（タイトルとURL）が取得できていることを検証
    for cat in ["ai_frontier", "ai_agents", "nogizaka46", "hinatazaka46"]:
        hits = intel[cat]
        assert len(hits) > 0, f"Category {cat} should have hits"
        first_hit = hits[0]
        assert "title" in first_hit
        assert "url" in first_hit


def test_09_deep_research_and_beautiful_html_rendering(tmp_path):
    """DeepResearchEngine との統合および美麗Tailwind HTML生成の検証"""
    engine = DailyBriefingEngine(workspace_root=str(tmp_path))
    assert hasattr(engine, "deep_researcher")
    assert engine.deep_researcher is not None

    sample_md = """# ☀️ 【つぐみデイリーブリーフィング】テスト
```mermaid
graph TD
    A[Deep Research Engine] --> B[Daily Briefing]
```
"""
    html = engine.deep_researcher.render_beautiful_html(
        title="テストブリーフィング",
        markdown_content=sample_md,
        category="デイリーブリーフィング"
    )
    assert isinstance(html, str)
    assert "<!DOCTYPE html>" in html
    assert "mermaid" in html.lower()

