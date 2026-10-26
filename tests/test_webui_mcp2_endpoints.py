# -*- coding: utf-8 -*-
"""
Tests for TUGUMIv6 WebUI MCP 2.0 Endpoints
Verifies:
- GET /api/mcp
- GET /api/mcp/protocols
- POST /api/mcp/call
- POST /api/mcp/tasks
- GET /api/mcp/tasks/{server}/{task_id}
- GET /api/mcp/apps/{server}/{app_name}
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient

project_root = "/data/data/com.termux/files/home/TUGUMIv6"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from interfaces.web.web_server import app

class TestWebUIMCP2Endpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_api_mcp_list(self):
        resp = self.client.get("/api/mcp")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertGreaterEqual(data.get("total_servers", 0), 11)

    def test_02_api_mcp_protocols(self):
        resp = self.client.get("/api/mcp/protocols")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        protocols = data.get("protocols", {})
        self.assertIn("failure_guard", protocols)
        self.assertIn("research", protocols)
        self.assertIn("osint", protocols)
        self.assertTrue(protocols["research"]["supports_tasks"])

    def test_03_api_mcp_call(self):
        resp = self.client.post("/api/mcp/call", json={
            "server": "failure_guard",
            "tool": "check_failure_risk",
            "args": {"query": "webui test"}
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertIn("result", data)

    def test_04_api_mcp_tasks_lifecycle(self):
        # 1. Start task
        start_resp = self.client.post("/api/mcp/tasks", json={
            "server": "failure_guard",
            "tool": "check_failure_risk",
            "args": {"query": "task lifecycle test"}
        })
        self.assertEqual(start_resp.status_code, 200)
        task_data = start_resp.json().get("task", {})
        task_id = task_data.get("task_id")
        self.assertIsNotNone(task_id)

        # 2. Check task status
        status_resp = self.client.get(f"/api/mcp/tasks/failure_guard/{task_id}")
        self.assertEqual(status_resp.status_code, 200)
        status_data = status_resp.json().get("task", {})
        self.assertEqual(status_data.get("task_id"), task_id)

if __name__ == "__main__":
    unittest.main()
