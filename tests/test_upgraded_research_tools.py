# -*- coding: utf-8 -*-
"""
TUGUMIv6 Upgraded Research Tools Unit & E2E Test Suite
- Trafilatura Body Extraction
- Hybrid Multi-source Web Search (DDG + Yahoo JP + RSS)
- Markdown Engine Table & Code Rendering
"""

import pytest
from tools.research_tools import ResearchTools

def test_research_tools_initialization():
    rt = ResearchTools()
    assert rt.timeout == 90.0

def test_search_web_lite_resilience():
    rt = ResearchTools()
    results = rt.search_web_lite("Python 3.14", max_results=2)
    assert isinstance(results, list)
    assert len(results) > 0
    assert "url" in results[0]
    assert "title" in results[0]

def test_render_beautiful_html_markdown_table():
    rt = ResearchTools()
    sample_md = """# Performance Verification Report
| System | Status | Architecture |
| :--- | :--- | :--- |
| TUGUMIv6 Core | 100% Operational | MCP 2.0 + Termux Arsenal |
| Antigravity CLI | Fully Synchronized | Switch 2 Standard |

- Test completed autonomously without degradation.
"""
    html = rt.render_beautiful_html("System Health Audit", sample_md)
    assert "<!DOCTYPE html>" in html
    assert "<table" in html
    assert "TUGUMIv6 Core" in html
    assert "Switch 2 Standard" in html
    assert "Tailwind CSS" not in html or "cdn.tailwindcss.com" in html
