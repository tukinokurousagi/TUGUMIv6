# -*- coding: utf-8 -*-
"""
TUGUMIv6 Boost Comprehensive Improvements Unit Tests
Tests all 6 audited improvements:
1. Isolated tools wired into get_tugumi_tools() and Antigravity execution
2. Workspace sanitation: no .bak auto-creation in file_tools and coding_tools
3. ContextCompressor wired into CLI loop and history pruning/masking
4. Web server SSE streaming and telemetry synchronization
5. DeFiArbitrageMonitor cross-exchange (Binance vs Bybit) comparison
6. LoopGuard tool blocking and Supervisor heartbeat/process monitoring
"""

import os
import sys
import json
import time
import unittest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.antigravity_tools import (
    get_tugumi_tools,
    coding_grep_search,
    coding_read_lines,
    coding_surgical_replace,
    coding_check_syntax,
    termux_run_command,
    termux_privileged_command,
    android_ui_action,
    file_list_tree,
    file_write_safe,
    check_loop_status,
)
from tools.file_tools import FileTools
from tools.coding_tools import CodingTools
from tools.termux_tools import TermuxTools
from core.subagents import get_tugumi_subagents
from core.loop_guard import LoopGuard, default_loop_guard
from core.supervisor import Supervisor
from persona.context_compressor import ContextCompressor
from passive_income.defi_arbitrage_monitor import DeFiArbitrageMonitor
from interfaces.web.web_server import app
from fastapi.testclient import TestClient

class TestTUGUMIv6BoostImprovements(unittest.TestCase):

    def setUp(self):
        self.tmp_test_file = os.path.join(project_root, "data", "test_tmp_sanitation.txt")
        with open(self.tmp_test_file, "w", encoding="utf-8") as f:
            f.write("Line 1: Hello Master Takuma\nLine 2: Target to replace\nLine 3: End\n")

    def tearDown(self):
        if os.path.exists(self.tmp_test_file):
            try:
                os.remove(self.tmp_test_file)
            except Exception:
                pass
        # Clean any bak if ever created
        bak = f"{self.tmp_test_file}.bak"
        if os.path.exists(bak):
            try:
                os.remove(bak)
            except Exception:
                pass

    # 1. Wire isolated tools into get_tugumi_tools
    def test_improvement_1_tools_wired(self):
        tools = get_tugumi_tools()
        names = [t.__name__ for t in tools]
        expected_tools = [
            "execute_code",
            "termux_exec",
            "termux_privileged_exec",
            "get_device_status",
            "web_search_duckduckgo",
            "fetch_url_text",
            "coding_grep_search",
            "coding_read_lines",
            "coding_surgical_replace",
            "coding_check_syntax",
            "termux_run_command",
            "termux_privileged_command",
            "android_ui_action",
            "file_list_tree",
            "file_write_safe",
            "check_loop_status",
        ]
        for exp in expected_tools:
            self.assertIn(exp, names, f"Expected tool '{exp}' not found in get_tugumi_tools()")
        self.assertGreaterEqual(len(tools), 16)

        # Subagents verification
        subagents = get_tugumi_subagents()
        sub_names = [s.name for s in subagents]
        self.assertIn("researcher", sub_names)
        self.assertIn("sysops", sub_names)
        self.assertIn("code_craftsman", sub_names)

    # 2. Workspace sanitation: no .bak auto-creation
    def test_improvement_2_no_bak_creation_and_sanitation(self):
        ft = FileTools()
        # Test file_tools.write_file_safe
        ft.write_file_safe(self.tmp_test_file, "Updated content without bak")
        self.assertFalse(os.path.exists(f"{self.tmp_test_file}.bak"), "Rule violation: .bak was created by write_file_safe")

        # Test bare filename (empty dirname) safety
        bare_tmp = os.path.join(project_root, "data", "bare_test.tmp")
        ft.write_file_safe(bare_tmp, "bare file content")
        self.assertTrue(os.path.exists(bare_tmp))
        os.remove(bare_tmp)

        # Test coding_tools.surgical_replace
        ct = CodingTools()
        ct.surgical_replace(self.tmp_test_file, "Updated content", "Surgically replaced content")
        self.assertFalse(os.path.exists(f"{self.tmp_test_file}.bak"), "Rule violation: .bak was created by surgical_replace")

        # Test sanitize_workspace
        dummy_bak = os.path.join(project_root, "data", "dummy_junk.bak")
        with open(dummy_bak, "w") as f:
            f.write("junk")
        cleaned = ft.sanitize_workspace(directory=os.path.join(project_root, "data"))
        self.assertIn(dummy_bak, cleaned)
        self.assertFalse(os.path.exists(dummy_bak))

    # 3. ContextCompressor pruning, masking, and token defense
    def test_improvement_3_context_compressor(self):
        cc = ContextCompressor(max_output_lines=20)
        # Test observation masking
        huge_output = "\n".join([f"Output line {i}" for i in range(100)])
        masked = cc.mask_observation(huge_output, tool_name="termux_exec")
        self.assertIn("Observation Masked", masked)
        self.assertIn("lines truncated by TUGUMIv6 ContextGuard", masked)
        self.assertLess(len(masked.splitlines()), 90)

        # Test history pruning
        messages = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}"} for i in range(30)]
        pruned = cc.prune_history(messages, max_turns=6)
        self.assertEqual(len(pruned), 6)
        self.assertEqual(pruned[0]["content"], "msg 0")
        self.assertEqual(pruned[-1]["content"], "msg 29")

        # Test edge cases: max_turns <= 2
        self.assertEqual(len(cc.prune_history(messages, max_turns=2)), 2)
        self.assertEqual(len(cc.prune_history(messages, max_turns=1)), 1)
        self.assertEqual(len(cc.prune_history(messages, max_turns=0)), 0)

        # Test estimate tokens
        est = cc.estimate_tokens("テスト対話テキスト")
        self.assertGreaterEqual(est, 1)

    # 4. Web server SSE streaming and telemetry
    def test_improvement_4_web_streaming_and_telemetry(self):
        client = TestClient(app)
        # Status endpoint
        resp = client.get("/api/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("session_tokens", data)
        self.assertIn("session_cost_jpy", data)
        self.assertEqual(data["master"], "拓磨様")
        self.assertIn("supervisor_health", data)
        self.assertIn("heartbeats", data["supervisor_health"])

        # Stream endpoint
        with client.stream("POST", "/api/chat/stream", json={"message": "ping", "mode": "light"}) as stream_resp:
            self.assertEqual(stream_resp.status_code, 200)
            events = []
            for line in stream_resp.iter_lines():
                if line and line.startswith("data: "):
                    events.append(json.loads(line[6:]))
                    if len(events) >= 2:
                        break
            self.assertGreaterEqual(len(events), 1)

    # 5. DeFiArbitrageMonitor cross-exchange comparison
    def test_improvement_5_cross_exchange_arbitrage(self):
        mon = DeFiArbitrageMonitor()

        # Deterministic spatial arbitrage math test
        orig_b = mon.fetch_binance_tickers
        orig_by = mon.fetch_bybit_tickers
        try:
            # Route 1: Buy Binance ($60,000 ask) -> Sell Bybit ($60,300 bid)
            mon.fetch_binance_tickers = lambda syms: {"BTCUSDT": {"bid": 59990.0, "ask": 60000.0}}
            mon.fetch_bybit_tickers = lambda syms: {"BTCUSDT": {"bid": 60300.0, "ask": 60310.0}}
            calc1 = mon.scan_cross_exchange_spreads(["BTCUSDT"])
            self.assertEqual(len(calc1), 1)
            self.assertTrue(calc1[0]["is_profitable"])
            self.assertEqual(calc1[0]["buy_exchange"], "Binance")
            self.assertEqual(calc1[0]["sell_exchange"], "Bybit")
            self.assertAlmostEqual(calc1[0]["spread_pct"], 0.5, places=2)

            # Route 2: Buy Bybit ($3,000 ask) -> Sell Binance ($3,030 bid)
            mon.fetch_binance_tickers = lambda syms: {"ETHUSDT": {"bid": 3030.0, "ask": 3035.0}}
            mon.fetch_bybit_tickers = lambda syms: {"ETHUSDT": {"bid": 2995.0, "ask": 3000.0}}
            calc2 = mon.scan_cross_exchange_spreads(["ETHUSDT"])
            self.assertEqual(len(calc2), 1)
            self.assertTrue(calc2[0]["is_profitable"])
            self.assertEqual(calc2[0]["buy_exchange"], "Bybit")
            self.assertEqual(calc2[0]["sell_exchange"], "Binance")
            self.assertAlmostEqual(calc2[0]["spread_pct"], 1.0, places=2)
        finally:
            mon.fetch_binance_tickers = orig_b
            mon.fetch_bybit_tickers = orig_by

        # Live network query check (if network is reachable)
        live_spreads = mon.scan_cross_exchange_spreads(symbols=["BTCUSDT", "ETHUSDT"])
        valid = [s for s in live_spreads if "error" not in s]
        if valid:
            for s in valid:
                self.assertIn("symbol", s)
                self.assertIn("binance_price", s)
                self.assertIn("bybit_price", s)
                self.assertIn("direction", s)
                self.assertIn("spread_pct", s)
                self.assertIn("is_profitable", s)

        # Backward compatibility check
        legacy_spreads = mon.scan_binance_ticker_spreads()
        self.assertGreaterEqual(len(legacy_spreads), 1)

    # 6. LoopGuard & Supervisor enhancements
    def test_improvement_6_loop_guard_and_supervisor(self):
        # LoopGuard testing
        lg = LoopGuard(threshold=3)
        self.assertFalse(lg.record_call("test_tool", "arg=1"))
        self.assertFalse(lg.record_call("test_tool", "arg=1"))
        # 3rd identical call triggers loop detection
        self.assertTrue(lg.record_call("test_tool", "arg=1"))

        # Test LoopGuard 2-cycle flailing detection
        lg.reset()
        self.assertFalse(lg.record_call("tool_a", "1"))
        self.assertFalse(lg.record_call("tool_b", "2"))
        self.assertFalse(lg.record_call("tool_a", "1"))
        self.assertFalse(lg.record_call("tool_b", "2"))
        self.assertFalse(lg.record_call("tool_a", "1"))
        self.assertTrue(lg.record_call("tool_b", "2"), "2-cycle flailing loop must be detected")

        # Test LoopGuard decorator
        @lg.guard
        def protected_tool(x: int) -> str:
            return f"result_{x}"

        lg.reset()
        res1 = protected_tool(42)
        self.assertEqual(res1, "result_42")
        res2 = protected_tool(42)
        self.assertEqual(res2, "result_42")
        res3_raw = protected_tool(42)
        res3 = json.loads(res3_raw)
        self.assertTrue(res3.get("loop_blocked"))
        self.assertIn("LoopGuard Error", res3.get("error"))

        # Supervisor heartbeat & process monitoring
        sup = Supervisor(base_dir=project_root)
        hb = sup.record_heartbeat("unit_test", metadata={"status": "testing"})
        self.assertEqual(hb["pid"], os.getpid())

        check_hb = sup.check_heartbeat("unit_test", max_staleness_sec=5.0)
        self.assertTrue(check_hb["alive"])
        self.assertEqual(check_hb["component"], "unit_test")

        # System health check
        health = sup.health_check_system()
        self.assertIn("supervisor", health)
        self.assertIn("heartbeats", health)
        self.assertIn("processes", health)
        self.assertIn("unit_test", health["heartbeats"])

        # TermuxTools fallback returns all required keys
        tt = TermuxTools()
        res_priv = tt.run_privileged_command("echo test", method="invalid_method")
        self.assertIn("exit_code", res_priv)
        self.assertIn("stdout", res_priv)
        self.assertIn("stderr", res_priv)
        self.assertIn("method_used", res_priv)
        self.assertEqual(res_priv["exit_code"], -1)

if __name__ == "__main__":
    unittest.main()
