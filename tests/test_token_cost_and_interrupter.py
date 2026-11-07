# -*- coding: utf-8 -*-
"""
Unit and Integration Tests for TokenCostTracker and TaskInterrupter
- Tests token counting and Gemini 3.8 Flash JPY pricing calculation
- Tests TaskInterrupter initialization and safe terminal teardown
"""

import unittest
import sys

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
        # 1. ワイド画面（フル詳細表示：モデル名・詳細内訳が含まれる）
        console_wide = Console(record=True, width=120)
        self.tracker.record_turn(prompt_text="Hello", response_text="World")
        self.tracker.render_cost_banner(console_wide)
        output_wide = console_wide.export_text()
        self.assertIn("Gemini 3.8 Flash", output_wide)
        self.assertIn("¥", output_wide)

        # 2. スマホ・ナロー画面（スマート短縮表示：折返し防止）
        console_narrow = Console(record=True, width=60)
        self.tracker.render_cost_banner(console_narrow)
        output_narrow = console_narrow.export_text()
        self.assertIn("¥", output_narrow)
        self.assertIn("Turn:", output_narrow)


class TestTaskInterrupter(unittest.TestCase):
    def test_interrupter_lifecycle(self):
        console = Console()
        interrupter = TaskInterrupter(console)
        # Even if running in non-interactive CI/background, it should not crash
        with interrupter:
            pressed = interrupter.check_esc_pressed()
            self.assertIsInstance(pressed, bool)
        self.assertFalse(interrupter._is_active)

    def test_process_group_pause_and_resume(self):
        """サブプロセス実行中にSIGSTOPで一時停止し、SIGCONTで正常再開・完走できることを検証"""
        import subprocess
        import time
        proc = subprocess.Popen(
            "python3 -c 'import time; time.sleep(0.2); print(\"RESUMED_OK\")'",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True
        )
        TaskInterrupter.register_process(proc)
        try:
            TaskInterrupter.pause_all_active_processes()
            time.sleep(0.1)
            # 一時停止中はまだ終了していないこと
            self.assertIsNone(proc.poll())
            # 再開（SIGCONT）
            TaskInterrupter.resume_all_active_processes()
            stdout, stderr = proc.communicate(timeout=3.0)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("RESUMED_OK", stdout)
        finally:
            TaskInterrupter.unregister_process(proc)

    def test_process_group_termination_unblocks_child_pipes(self):
        """shell=True で孫プロセスがパイプを握っている場合でも terminate_all_active_processes で即座にアンブロックされることを検証"""
        import threading
        import time
        from tools.termux_tools import TermuxTools
        tt = TermuxTools()
        result_holder = {}

        def _runner():
            # 親シェルが別セッション(start_new_session=True)の孫デーモンを起動してパイプFDを保持し続ける最悪ケース
            result_holder["res"] = tt.run_termux_command(
                "python3 -c 'import subprocess, time; subprocess.Popen([\"sleep\", \"10\"], start_new_session=True); time.sleep(10)'",
                timeout=15.0
            )

        t = threading.Thread(target=_runner, daemon=True)
        t.start()
        time.sleep(0.25)
        start_kill = time.time()
        TaskInterrupter.terminate_all_active_processes()
        t.join(timeout=2.0)
        elapsed_kill = time.time() - start_kill
        self.assertFalse(t.is_alive(), "Child process pipe blocked run_termux_command() after termination!")
        self.assertLess(elapsed_kill, 0.25)
        self.assertEqual(result_holder["res"]["exit_code"], -15)


if __name__ == "__main__":
    unittest.main()
