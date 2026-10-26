import os
import sys
import unittest

# Add TUGUMIv6 root
sys.path.insert(0, "/data/data/com.termux/files/home/TUGUMIv6")

from core.engine_manager import EngineManager
from core.antigravity_sdk import AntigravityEngine

class TestAntigravitySDKIntegration(unittest.TestCase):
    def setUp(self):
        self.mgr = EngineManager()

    def test_engine_has_antigravity_sdk(self):
        self.assertIsInstance(self.mgr.antigravity, AntigravityEngine)
        self.assertTrue(self.mgr.antigravity.is_available())
        self.assertIn("0.1.20", self.mgr.antigravity.get_version())

    def test_antigravity_agent_live_turn(self):
        res = self.mgr.antigravity.execute_task(
            prompt="Reply with the exact word 'OPUS_AND_SOL_APPROVED' and nothing else.",
            system_instruction="You are TUGUMI v6 Antigravity SDK engine."
        )
        self.assertEqual(res["status"], "success", f"Execution failed: {res.get('error')}")
        self.assertIn("OPUS_AND_SOL_APPROVED", res["text"])
    def test_skills_paths_configured(self):
        config = self.mgr.antigravity.build_config()
        self.assertTrue(len(config.skills_paths) > 0, "skills_paths must not be empty")
        self.assertTrue(os.path.exists(config.skills_paths[0]), f"skills_paths directory must exist: {config.skills_paths[0]}")
        print("\n[E2E VERIFIED] skills_paths configured:", config.skills_paths)

    def test_persistent_agent_multi_turn_memory(self):
        import asyncio
        async def _run():
            agent = self.mgr.spawn_agent(system_instruction="You are TUGUMI v6.")
            async with agent:
                # Turn 1
                r1 = await agent.chat("Remember this specific password: PHOENIX_9900.")
                t1 = ""
                async for c in r1.chunks:
                    if hasattr(c, "text"): t1 += c.text
                self.assertTrue(len(t1) > 0)
                
                # Turn 2
                r2 = await agent.chat("What was the password? Reply ONLY the password.")
                t2 = ""
                async for c in r2.chunks:
                    if hasattr(c, "text"): t2 += c.text
                self.assertIn("PHOENIX_9900", t2)
                print("\n[E2E VERIFIED] Persistent Multi-Turn Memory Verified:", t2.strip())
        asyncio.run(_run())

if __name__ == "__main__":
    unittest.main()
