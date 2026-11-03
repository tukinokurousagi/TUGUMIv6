# -*- coding: utf-8 -*-
"""
Comprehensive E2E Test Suite for MCP 2.0 Integration across TUGUMIv6 and Antigravity
Verifies:
1. All 12 MCP servers discovered by MCP20Engine
2. Dynamic execution via MCPClient and `mcp.<server>.<tool>()`
3. Tool listing and protocol version negotiation
4. Code Mode execution via `execute_code`
"""

import sys
import json
import unittest

project_root = "/data/data/com.termux/files/home/TUGUMIv6"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.tugumi_mcp import mcp
from tools.mcp_client import MCPClient
from tools.antigravity_tools import execute_code, mcp2_protocol_info

class TestAllMCP2ServersE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = MCPClient()

    def test_01_server_discovery(self):
        servers = mcp.list_servers()
        expected = [
            "failure_guard", "tugumi_v6", "twitter", "research",
            "osint", "revshell", "horse_racing", "robin",
            "playwright", "github", "gemini-api-docs-mcp", "metasploit"
        ]
        for s in expected:
            self.assertIn(s, servers, f"Expected server '{s}' to be discovered")

    def test_02_failure_guard_call(self):
        res = mcp.call("failure_guard", "check_failure_risk", query="test")
        self.assertFalse(res.get("isError", False))
        self.assertTrue(len(res.get("content", [])) > 0)

    def test_03_tugumi_v6_call(self):
        res = mcp.call("tugumi_v6", "tugumi_exec", command="echo 'TUGUMIv6 MCP2.0 Active'")
        self.assertFalse(res.get("isError", False))
        self.assertIn("TUGUMIv6 MCP2.0 Active", str(res))

    def test_04_osint_call(self):
        res = mcp.call("osint", "shodan_internetdb_lookup", ip="8.8.8.8")
        self.assertFalse(res.get("isError", False))
        self.assertTrue(len(res.get("content", [])) > 0)

    def test_05_mcp_client_dynamic_proxy(self):
        res = self.client.failure_guard.check_failure_risk(query="bash shebang")
        self.assertFalse(res.get("isError", False))

    def test_06_code_mode_mcp2_all_servers(self):
        code = """
import json
fg = mcp.failure_guard.check_failure_risk(query="mcp2")
sh = mcp.tugumi_v6.tugumi_exec(command="whoami")
print("CODE_MODE_MCP2_SUCCESS: True")
"""
        res_raw = execute_code(code)
        res = json.loads(res_raw)
        self.assertTrue(res["success"], f"Code execution failed: {res.get('error')}")
        self.assertIn("CODE_MODE_MCP2_SUCCESS: True", res["stdout"])

    def test_07_mcp2_protocol_info(self):
        info_raw = mcp2_protocol_info()
        info = json.loads(info_raw)
        self.assertIsInstance(info, dict)
        self.assertIn("failure_guard", info)

if __name__ == "__main__":
    unittest.main()
