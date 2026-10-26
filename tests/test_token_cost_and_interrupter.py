# -*- coding: utf-8 -*-
"""
Unit and Integration Tests for TokenCostTracker and TaskInterrupter
- Tests token counting and Gemini 3.8 Flash JPY pricing calculation
- Tests TaskInterrupter initialization and safe terminal teardown
"""

import unittest
import sys
import os

# Add TUGUMIv6 root
sys.path.insert(0, "/data/data/com.termux/files/home/TUGUMIv6")

from interfaces.cli.token_cost_tracker import TokenCostTracker
from interfaces.cli.task_interrupter import TaskInterrupter
from rich.console import Console

class TestTokenCostTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = TokenCostTracker(usd_jpy_rate=155.0)

    def test_token_estimation(self):
        # English estimation: ~4 chars / token
        en_text = "Hello world this is a test string"
        self.assertGreater(self.tracker.estimate_tokens(en_text), 5)

        # Japanese estimation: ~1.2 chars / token
        ja_text = "こんにちは、拓磨様。つぐみです。"
        self.assertGreater(self.tracker.estimate_tokens(ja_text), 10)

    def test_pricing_calculation(self):
        # 10,000 prompt tokens, 5,000 completion tokens
        # Prompt cost: (10,000 / 1M) * $0.075 = $0.00075
        # Completion cost: (5,000 / 1M) * $0.300 = $0.00150
        # Total USD = $0.00225
        # Total JPY = 0.00225 * 155 = 0.34875 円
        meta = {
            "prompt_token_count": 10000,
            "candidates_token_count": 5000,
            "thoughts_token_count": 1000
        }
        res = self.tracker.record_turn(usage_metadata=meta)
        self.assertEqual(res["turn_prompt_tokens"], 10000)
        self.assertEqual(res["turn_completion_tokens"], 5000)
        self.assertAlmostEqual(res["turn_cost_usd"], 0.00225, places=5)
        self.assertAlmostEqual(res["turn_cost_jpy"], 0.34875, places=4)
        self.assertEqual(self.tracker.session_total, 15000)

    def test_render_cost_banner(self):
        console = Console(record=True, width=80)
        self.tracker.record_turn(prompt_text="Hello", response_text="World")
        self.tracker.render_cost_banner(console)
        output = console.export_text()
        self.assertIn("Gemini 3.8 Flash", output)
        self.assertIn("¥", output)


class TestTaskInterrupter(unittest.TestCase):
    def test_interrupter_lifecycle(self):
        console = Console()
        interrupter = TaskInterrupter(console)
        # Even if running in non-interactive CI/background, it should not crash
        with interrupter:
            pressed = interrupter.check_esc_pressed()
            self.assertIsInstance(pressed, bool)
        self.assertFalse(interrupter._is_active)


if __name__ == "__main__":
    unittest.main()
