import os
import sys
import unittest

sys.path.insert(0, "/data/data/com.termux/files/home/TUGUMIv6")

from core.engine_manager import EngineManager
from core.antigravity_sdk import AntigravityEngine
from tools.antigravity_tools import get_tugumi_tools
from core.subagents import get_tugumi_subagents

class TestFullToolsAndSubagentsIntegration(unittest.TestCase):
    def setUp(self):
        self.mgr = EngineManager()

    def test_tools_and_subagents_registered(self):
        engine = self.mgr.antigravity
        self.assertTrue(engine.is_available())
        tools = get_tugumi_tools()
        subagents = get_tugumi_subagents()
        self.assertGreaterEqual(len(tools), 4, "Must have at least 4 registered tools")
        self.assertGreaterEqual(len(subagents), 2, "Must have researcher and sysops subagents")

    def test_live_tool_calling_device_status(self):
        """Verify the agent autonomously calls get_device_status tool"""
        engine = self.mgr.antigravity
        prompt = "Call get_device_status and report the battery percentage."
        res = engine.execute_task(prompt)
        self.assertEqual(res["status"], "success", f"Execution failed: {res.get('error')}")
        self.assertTrue(len(res["text"]) > 0)
        print("\n[TOOL CALL RESULT]:", res["text"])

if __name__ == "__main__":
    unittest.main()
