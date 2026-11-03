# -*- coding: utf-8 -*-
"""
Unit tests for Mechanical Inline Deep Crawl and Causal Leverage Verification.
Verifies that research tools physically inject raw primary sources and stress-test logical hypotheses.
"""

import os
import sys
import json
import unittest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.antigravity_tools import (
    verify_causal_leverage,
    get_tugumi_tools
)
from tools.research_tools import ResearchTools

class TestInlineDeepCrawlAndLeverage(unittest.TestCase):

    def test_01_verify_causal_leverage_flaw_detection(self):
        """Test that verify_causal_leverage flags leverage collapse when secret is detached from hostage."""
        premise = "核融合技術の天才科学者エリシャが敵組織シンシーに拉致され激しい拷問を受けている。"
        parties = "シンシー（敵・データ強奪）、エリシャ（人質・科学者）、乃木・野崎（救出側）"
        
        # 破綻した仮説: データは娘に託されている
        flawed_hypo = "核融合のコアデータは娘プリシャに託されており、娘が持っている。"
        res_raw = verify_causal_leverage(premise, parties, flawed_hypo)
        res = json.loads(res_raw)
        
        self.assertIn("verdict", res)
        self.assertIn("identified_flaws", res)
        self.assertTrue(any(f["type"] == "LEVERAGE_COLLAPSE_RISK" for f in res["identified_flaws"]))
        self.assertLess(res["consistency_score"], 80)

        # 整合した仮説: データは本人の頭の中にしかない
        sound_hypo = "核融合技術のデータはエリシャの頭の中にしかなく、娘に会えなければ絶対に教えないという交渉力で生存を維持している。"
        sound_res_raw = verify_causal_leverage(premise, parties, sound_hypo)
        sound_res = json.loads(sound_res_raw)
        self.assertEqual(sound_res["verdict"], "PASS")
        self.assertEqual(sound_res["consistency_score"], 100)

    def test_02_verify_causal_leverage_cliche_detection(self):
        """Test that verify_causal_leverage flags AI slop stereotypes like amulets or body doubles."""
        premise = "要人が暗殺されそうになっている。"
        parties = "要人、護衛、暗殺者"
        cliche_hypo = "実はお守りの中に暗号があり、身代わりの影武者が死んだ。"
        res = json.loads(verify_causal_leverage(premise, parties, cliche_hypo))
        self.assertTrue(any(f["type"] == "AI_SLOP_CLICHE" for f in res["identified_flaws"]))

    def test_03_tool_registration(self):
        """Test that verify_causal_leverage is properly registered in get_tugumi_tools."""
        tools = get_tugumi_tools()
        tool_names = [getattr(t, "__name__", "") for t in tools]
        self.assertIn("verify_causal_leverage", tool_names)
        self.assertIn("web_search_duckduckgo", tool_names)
        self.assertIn("fetch_url_text", tool_names)

    def test_04_research_tools_search_web_lite_auto_crawl_param(self):
        """Test that ResearchTools.search_web_lite accepts auto_crawl and runs without syntax error."""
        rt = ResearchTools(timeout=5.0)
        # Mock/Offline verification of interface
        import inspect
        sig = inspect.signature(rt.search_web_lite)
        self.assertIn("auto_crawl", sig.parameters)
        self.assertTrue(sig.parameters["auto_crawl"].default)

if __name__ == "__main__":
    unittest.main()
