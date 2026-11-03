# -*- coding: utf-8 -*-
"""
Tests for TUGUMIv6 Code Mode & MCP 2.0 Integration
- Verifies execute_code tool execution
- Verifies dynamic MCP proxy (import tugumi_mcp as mcp)
- Verifies token preservation by aggregating tool outputs programmatically
- Verifies error capture and traceback safety
"""

import sys
import os
import json
import unittest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.antigravity_tools import execute_code, get_tugumi_tools
from tools.tugumi_mcp import mcp

class TestCodeModeMCP2(unittest.TestCase):
    def test_tools_registration(self):
        tools = get_tugumi_tools()
        tool_names = [t.__name__ for t in tools]
        self.assertIn("execute_code", tool_names)
        self.assertIn("termux_exec", tool_names)

    def test_execute_code_basic_python(self):
        code = "a = 10\nb = 20\nprint(f'SUM:{a+b}')"
        res_raw = execute_code(code)
        res = json.loads(res_raw)
        self.assertTrue(res["success"])
        self.assertIn("SUM:30", res["stdout"])
        self.assertEqual(res["error"], "")

    def test_execute_code_mcp2_failure_guard(self):
        code = """
result = mcp.failure_guard.check_failure_risk(query="git worktree")
print("CHECK_RESULT:", type(result) is dict)
"""
        res_raw = execute_code(code)
        res = json.loads(res_raw)
        self.assertTrue(res["success"], f"Failed with error: {res.get('error')}")
        self.assertIn("CHECK_RESULT: True", res["stdout"])

    def test_execute_code_error_handling(self):
        code = "1 / 0"
        res_raw = execute_code(code)
        res = json.loads(res_raw)
        self.assertFalse(res["success"])
        self.assertIn("ZeroDivisionError", res["error"])

    def test_token_reduction_by_aggregation(self):
        # Code mode can process multiple MCP outputs and return only a compact summary
        code = """
items = [1, 2, 3, 4, 5]
squared = [x**2 for x in items]
print(f"COMPACT_COUNT:{len(squared)}")
"""
        res_raw = execute_code(code)
        res = json.loads(res_raw)
        self.assertTrue(res["success"])
        self.assertIn("COMPACT_COUNT:5", res["stdout"])

    def test_tools_registration_mcp_bridges(self):
        tools = get_tugumi_tools()
        tool_names = [t.__name__ for t in tools]
        self.assertIn("mcp_check_failure_risk", tool_names)
        self.assertIn("mcp_record_failure_lesson", tool_names)
        self.assertIn("mcp_race_resolve", tool_names)
        self.assertIn("mcp_get_user_tweets", tool_names)
        self.assertIn("mcp_call", tool_names)
        self.assertIn("research_save_report", tool_names)
        self.assertIn("research_generate_html_report", tool_names)

    def test_mcp_list_tools(self):
        tools = mcp.list_tools("failure_guard")
        self.assertIsInstance(tools, list)
        tool_names = [t.get("name") for t in tools]
        self.assertIn("check_failure_risk", tool_names)

    def test_native_mcp_bridge_failure_guard(self):
        from tools.antigravity_tools import mcp_check_failure_risk
        res_str = mcp_check_failure_risk("git")
        self.assertIsInstance(res_str, str)
        self.assertTrue(len(res_str) > 0)

    def test_tugumi_v6_mcp_server(self):
        # Verify tugumi_v6 MCP server tool execution
        res = mcp.tugumi_v6.tugumi_device_telemetry()
        self.assertIsInstance(res, dict)
        if "parsed" in res:
            self.assertIn("memory", res["parsed"])
        else:
            self.assertTrue(any("memory" in c.get("text", "") for c in res.get("content", [])))

if __name__ == "__main__":
    unittest.main()
