# -*- coding: utf-8 -*-
import unittest
import sys
import time

sys.path.insert(0, "/data/data/com.termux/files/home/TUGUMIv6")

from core.engine_manager import EngineManager

class TestSteeringE2E(unittest.TestCase):
    def setUp(self):
        self.mgr = EngineManager()

    def test_steering_flow(self):
        """Simulate exactly the CLI main.py steering flow:
        1. stream begins
        2. user interrupts via ESC (break + cancel_active_task)
        3. user injects steering prompt
        4. new stream starts with steering prompt and completes successfully
        """
        # Step 1: Start stream
        stream1 = self.mgr.generate_stream(
            prompt="Tell me a very long story about a cyberpunk samurai.",
            system_instruction="You are TUGUMI v6.",
            mode="dark"
        )
        first_chunk_received = False
        for _chunk_type, _chunk_data in stream1:
            first_chunk_received = True
            break  # Simulates ESC interrupt

        self.assertTrue(first_chunk_received)

        # Step 2: Cancel active task
        self.mgr.cancel_active_task()
        if hasattr(stream1, "close"):
            try: stream1.close()
            except Exception: pass
        time.sleep(0.5)

        # Step 3 & 4: Resume with steering prompt
        steered_prompt = "マスター拓磨様からの割り込み指示: '即座に短く挨拶だけせよ'"
        stream2 = self.mgr.generate_stream(
            prompt=steered_prompt,
            system_instruction="You are TUGUMI v6.",
            mode="dark"
        )
        
        output_chunks = []
        start_t = time.time()
        for chunk_type, chunk_data in stream2:
            if chunk_type == "text":
                output_chunks.append(chunk_data)
            # Timeout guard: must complete within 20s without hanging
            if time.time() - start_t > 20:
                break

        full_output = "".join(output_chunks)
        print("\n[Steering Flow Verified] Output:", full_output[:100])
        self.assertGreater(len(full_output), 0, "Steered stream should produce output without deadlocking")

if __name__ == "__main__":
    unittest.main()
