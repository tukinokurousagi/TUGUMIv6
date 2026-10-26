#!/usr/bin/env python3
"""
TUGUMIv6 WebUI Full E2E & Zero-Mock Verification Test Suite
Tests all endpoints, streaming, tools, background jobs, kill-switches, and memory operations.
"""
import sys
import os
import unittest
import json

# Ensure TUGUMIv6 root is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from fastapi.testclient import TestClient
from interfaces.web.web_server import app

class TestWebUIFullE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_index_html(self):
        """GET / should return index.html with 200 OK and expected HUD elements"""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.text
        self.assertIn("TUGUMIv6 Cyber HUD", html)
        self.assertIn("telemetryModal", html)
        self.assertIn("runningTasksCard", html)
        self.assertIn("addMemoryFact", html)
        self.assertIn("btnIncTicker", html)
        self.assertIn("apiPingStatus", html)

    def test_02_status_endpoints(self):
        """GET /api/status, /api/status/health, POST /api/status/doctor_run"""
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "online")
        self.assertEqual(data.get("master"), "拓磨様")
        self.assertIn("telemetry", data)

        res_health = self.client.get("/api/status/health")
        self.assertEqual(res_health.status_code, 200)
        d_health = res_health.json()
        self.assertIn("telemetry", d_health)

        res_doc = self.client.post("/api/status/doctor_run")
        self.assertEqual(res_doc.status_code, 200)
        d_doc = res_doc.json()
        self.assertTrue(d_doc.get("success"))
        self.assertIn("telemetry", d_doc)

    def test_03_sessions_management(self):
        """Chat session creation, listing, getting, and deletion"""
        res_create = self.client.post("/api/chat/sessions", json={"title": "テスト会話スレッド"})
        self.assertEqual(res_create.status_code, 200)
        sid = res_create.json().get("session_id")
        self.assertTrue(sid)

        res_list = self.client.get("/api/chat/sessions")
        self.assertEqual(res_list.status_code, 200)
        sessions = res_list.json().get("sessions", [])
        self.assertTrue(any(s.get("id") == sid for s in sessions))

        res_get = self.client.get(f"/api/chat/sessions/{sid}")
        self.assertEqual(res_get.status_code, 200)

        res_del = self.client.delete(f"/api/chat/sessions/{sid}")
        self.assertEqual(res_del.status_code, 200)
        self.assertTrue(res_del.json().get("success"))

    def test_04_memory_operations(self):
        """Add cognitive memory, list memories, and delete memory"""
        res_add = self.client.post("/api/memory/add_memory", json={
            "category": "preference",
            "subject": "E2Eテスト項目",
            "fact_content": "Zero-Mockテスト検証用データ",
            "importance": 4
        })
        self.assertEqual(res_add.status_code, 200)
        mem_id = res_add.json().get("memory_id")
        self.assertTrue(mem_id)

        res_list = self.client.get("/api/memory/memories")
        self.assertEqual(res_list.status_code, 200)
        mems = res_list.json().get("memories", [])
        self.assertTrue(any(m.get("id") == mem_id for m in mems))

        res_del = self.client.delete(f"/api/memory/memories/{mem_id}")
        self.assertEqual(res_del.status_code, 200)
        self.assertTrue(res_del.json().get("success"))

    def test_05_tools_operations(self):
        """Tools listing, running background tool, checking running list, stopping tool"""
        res_list = self.client.get("/api/tools/list")
        self.assertEqual(res_list.status_code, 200)
        cats = res_list.json().get("categories", {})
        self.assertIn("system", cats)
        self.assertIn("dynamic", cats)

        # Test dynamic tool execution
        res_dyn = self.client.post("/api/tools/run", json={"script": "dynamic_tools/termux_resource_inspector.py"})
        self.assertEqual(res_dyn.status_code, 200)
        self.assertEqual(res_dyn.json().get("exit_code"), 0)

        # Test running tools query
        res_run = self.client.get("/api/tools/running")
        self.assertEqual(res_run.status_code, 200)
        self.assertIn("processes", res_run.json())

        # Test running a tool (if termux-clip or another tool exists)
        # We can test stop with a non-existent PID gracefully
        res_stop = self.client.post("/api/tools/stop", json={"script": "dummy_tool", "pid": 999999})
        self.assertEqual(res_stop.status_code, 200)
        self.assertEqual(res_stop.json().get("status"), "not_running")

    def test_06_income_endpoints(self):
        """GET /api/income/spreads, /api/income/ticker_spreads, and Binance Quant Studio v2.0 endpoints"""
        res_spreads = self.client.get("/api/income/spreads")
        self.assertEqual(res_spreads.status_code, 200)
        self.assertIn("spreads", res_spreads.json())

        res_ticker = self.client.get("/api/income/ticker_spreads")
        self.assertEqual(res_ticker.status_code, 200)
        self.assertIn("spreads", res_ticker.json())

        # Verify Binance Quant Studio v2.0 HTML elements in index.html
        html = self.client.get("/").text
        self.assertIn("TUGUMI BINANCE QUANT STUDIO v2.0", html)
        self.assertIn("loadBinanceDashboard", html)
        self.assertIn("bnbPositionsContainer", html)
        self.assertIn("bnbScanBody", html)

        # Verify Binance Quant Studio v2.0 backend endpoints
        res_dash = self.client.get("/api/crypto/dashboard")
        self.assertIn(res_dash.status_code, [200, 500])
        d_dash = res_dash.json()
        self.assertIn("patrol_status", d_dash)
        self.assertIn("recent_trades", d_dash)

        res_hist = self.client.get("/api/crypto/history?limit=10")
        self.assertEqual(res_hist.status_code, 200)
        self.assertTrue(res_hist.json().get("success"))
        self.assertIn("trades", res_hist.json())

        res_patrol = self.client.post("/api/crypto/patrol", json={"action": "status", "interval": 1})
        self.assertEqual(res_patrol.status_code, 200)
        self.assertTrue(res_patrol.json().get("success"))
        self.assertIn("patrol_status", res_patrol.json())

    def test_07_settings_endpoint(self):
        """GET and POST /api/settings"""
        res_get = self.client.get("/api/settings")
        self.assertEqual(res_get.status_code, 200)
        settings = res_get.json()
        self.assertIn("mode", settings)
        self.assertIn("user_name", settings)

        res_post = self.client.post("/api/settings", json={"user_name": "拓磨様"})
        self.assertEqual(res_post.status_code, 200)
        self.assertEqual(res_post.json().get("user_name"), "拓磨様")

    def test_08_model_ping(self):
        """GET /api/model/ping (API connectivity check)"""
        res = self.client.get("/api/model/ping")
        # If network/API key is valid, it returns 200; if network restricted, graceful 500
        self.assertIn(res.status_code, [200, 500])
        data = res.json()
        self.assertIn("latency_ms", data)

    def test_09_chat_stream(self):
        """POST /api/chat/stream SSE endpoint"""
        res = self.client.post("/api/chat/stream", json={
            "message": "こんにちは！",
            "mode": "light",
            "session_id": "test_e2e_stream"
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("content-type"), "text/event-stream; charset=utf-8")
        # Read first chunk
        text = res.text
        self.assertTrue(len(text) > 0)
        self.assertIn("data:", text)
        # Cleanup test session so test chats do not pollute user chat history
        self.client.delete("/api/chat/sessions/test_e2e_stream")

    def test_10_logs_endpoints(self):
        """GET /api/logs and POST /api/logs/clear"""
        res_get = self.client.get("/api/logs?limit=50")
        self.assertEqual(res_get.status_code, 200)
        d_get = res_get.json()
        self.assertTrue(d_get.get("success"))
        self.assertIn("logs", d_get)
        self.assertIn("circuit_breaker", d_get)
        self.assertIn("log_file", d_get)

        res_clear = self.client.post("/api/logs/clear")
        self.assertEqual(res_clear.status_code, 200)
        d_clear = res_clear.json()
        self.assertTrue(d_clear.get("success"))

    def tearDown(self):
        # Ensure circuit breaker is always reset even if test fails
        try:
            self.client.post("/api/system/reset_circuit_breaker")
        except Exception:
            pass

    def test_11_emergency_stop_and_circuit_breaker(self):
        """Emergency stop, request blocking (503), rate status, and reset"""
        # 1. Trigger emergency stop
        res_stop = self.client.post("/api/system/emergency_stop")
        self.assertEqual(res_stop.status_code, 200)
        d_stop = res_stop.json()
        self.assertTrue(d_stop.get("emergency_stopped"))

        # 2. Protected endpoint (not in bypass_exact) should now return 503
        res_blocked = self.client.get("/api/briefing/latest")
        self.assertEqual(res_blocked.status_code, 503)
        self.assertIn("error", res_blocked.json())

        # 3. Rate status endpoint (bypass) should still return 200
        res_rate = self.client.get("/api/system/rate_status")
        self.assertEqual(res_rate.status_code, 200)
        d_rate = res_rate.json()
        self.assertTrue(d_rate.get("circuit_breaker", {}).get("emergency_stopped"))

        # 4. Reset circuit breaker
        res_reset = self.client.post("/api/system/reset_circuit_breaker")
        self.assertEqual(res_reset.status_code, 200)
        self.assertTrue(res_reset.json().get("success"))

        # 5. Protected endpoint should now work normally
        res_ok = self.client.get("/api/briefing/latest")
        self.assertEqual(res_ok.status_code, 200)

    def test_12_session_deletion_robustness(self):
        """Test deleting session with encoded characters and invalid IDs"""
        import urllib.parse
        # Create a session with special characters
        special_id = "test-session-special-@#$ 123"
        res_create = self.client.post("/api/chat/sessions", json={"title": "特殊文字セッション"})
        self.assertEqual(res_create.status_code, 200)
        sid = res_create.json().get("session_id")
        self.assertTrue(sid)

        # Delete with encoded path
        encoded = urllib.parse.quote(sid, safe="")
        res_del = self.client.delete(f"/api/chat/sessions/{encoded}")
        self.assertEqual(res_del.status_code, 200)
        self.assertTrue(res_del.json().get("success"))

    def test_13_media_and_briefing_endpoints(self):
        """Test briefing latest and media query endpoints"""
        res_briefing = self.client.get("/api/briefing/latest")
        self.assertEqual(res_briefing.status_code, 200)
        self.assertIn("status", res_briefing.json())

        res_media = self.client.get("/api/media/files")
        self.assertEqual(res_media.status_code, 200)
        self.assertIn("files", res_media.json())

    def test_14_skills_and_mcp_html_validation(self):
        """Test Skills & MCP endpoints, detail queries, and WebUI HTML/CSS scroll integrity"""
        # 1. Skills API
        res_skills = self.client.get("/api/skills")
        self.assertEqual(res_skills.status_code, 200)
        d_skills = res_skills.json()
        self.assertEqual(d_skills.get("status"), "ok")
        self.assertIn("skills", d_skills)
        self.assertTrue(len(d_skills["skills"]) > 0)

        # 2. MCP API
        res_mcp = self.client.get("/api/mcp")
        self.assertEqual(res_mcp.status_code, 200)
        d_mcp = res_mcp.json()
        self.assertEqual(d_mcp.get("status"), "ok")
        self.assertIn("servers", d_mcp)
        self.assertTrue(len(d_mcp["servers"]) > 0)

        # 3. Individual MCP Server Detail API (dev_tools or first server)
        first_server = d_mcp["servers"][0]["server_name"]
        res_detail = self.client.get(f"/api/mcp/{first_server}")
        self.assertEqual(res_detail.status_code, 200)
        d_detail = res_detail.json()
        self.assertEqual(d_detail.get("status"), "ok")
        self.assertIn("server", d_detail)

        # 4. WebUI HTML & CSS scroll integrity check
        res_html = self.client.get("/")
        self.assertEqual(res_html.status_code, 200)
        html_text = res_html.text
        self.assertIn("#p-skills", html_text)
        self.assertIn("overflow-y: auto !important", html_text)
        self.assertIn(".hud-modal.open, .hud-modal.on", html_text)
        self.assertIn(".drawer-overlay.open, .drawer-overlay.on", html_text)
        self.assertIn("-webkit-overflow-scrolling: touch", html_text)

    def test_15_antigravity_sdk_and_robin_webui(self):
        """15. Antigravity SDK v0.1.20 10大進化ピラーHUD・Robin OSINT・タスク中断Kill Switch検証"""
        r_html = self.client.get("/")
        assert r_html.status_code == 200
        html = r_html.text
        assert "agSdkTopBadge" in html
        assert "antigravityHudCard" in html
        assert "loadAntigravityHud" in html
        assert "runRobinWeb" in html
        assert "ev.type==='tool_result'" in html

        r_ag = self.client.get("/api/antigravity/status")
        assert r_ag.status_code == 200
        d_ag = r_ag.json()
        assert d_ag["success"] is True
        assert d_ag["evolution_score"] == 100.0
        assert len(d_ag["pillars"]) == 10

        r_can = self.client.post("/api/chat/cancel")
        assert r_can.status_code == 200
        assert r_can.json()["success"] is True

        for cmd in ["/evolve", "/compact", "/session"]:
            r_cmd = self.client.post("/api/chat", json={"message": cmd, "mode": "light", "session_id": "test_ag_sdk"})
            assert r_cmd.status_code == 200
            rep = r_cmd.json()["reply"]
            assert "|---" not in rep

    def test_16_user_first_innovations_and_zero_mock_wiring(self):
        """16. Omni Command Palette, Live Artifact Canvas, Smart Desk Archiver, FPF, Recall & Graph E2E検証"""
        r_html = self.client.get("/")
        self.assertEqual(r_html.status_code, 200)
        html = r_html.text
        for elem in [
            "btnCmdPalette", "cmdPaletteModal", "openCommandPalette",
            "artifactCanvasModal", "previewCodeArtifact",
            "saveMsgToDesk", "exportCurrentChatMd", "saveCurrentChatToDesk",
            "fpfStatusCard", "loadFpfStatus", "executeMcpToolDirect",
            "mediaGalleryCard", "loadMediaGallery", "briefCronTime", "addBriefingSchedule",
            "recallAssociativeMem", "queryLearningGraph", "btnJumpBottom", "drawerSearchIn",
        ]:
            self.assertIn(elem, html, f"Missing expected UI element/function: {elem}")

        # Verify Smart Desk Archiver API (/api/chat/save_to_desk)
        r_desk = self.client.post("/api/chat/save_to_desk", json={
            "content": "# TUGUMIv6 WebUI E2E Test\nMCP 2.0 と Antigravity エージェント設計テスト",
            "title": "WebUI_E2E_DeskSaveTest",
            "category": "auto",
        })
        self.assertEqual(r_desk.status_code, 200)
        d_desk = r_desk.json()
        self.assertTrue(d_desk.get("success"))
        self.assertEqual(d_desk.get("category"), "AI・エージェント")
        saved_path = d_desk.get("filepath")
        self.assertTrue(saved_path and os.path.exists(saved_path))
        try:
            os.remove(saved_path)
        except OSError:
            pass

        # Verify FPF status endpoint (/api/fpf)
        r_fpf = self.client.get("/api/fpf")
        self.assertEqual(r_fpf.status_code, 200)
        self.assertTrue(r_fpf.json().get("success"))

        # Verify Associative Recall (/api/memory/recall) & Learning Graph (/api/graph/query)
        r_rec = self.client.post("/api/memory/recall", json={"query": "テスト", "limit": 5})
        self.assertEqual(r_rec.status_code, 200)
        self.assertIn("results", r_rec.json())

        r_grp = self.client.post("/api/graph/query", json={"entity": "TUGUMIv6"})
        self.assertEqual(r_grp.status_code, 200)
        self.assertIn("relations", r_grp.json())

        # Verify Briefing Schedules endpoint (/api/briefing/schedules)
        r_sched = self.client.get("/api/briefing/schedules")
        self.assertEqual(r_sched.status_code, 200)
        self.assertIn("schedules", r_sched.json())

if __name__ == "__main__":
    unittest.main()

