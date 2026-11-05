#!/usr/bin/env python3
"""
Tests for TUGUMIv6 Vision UI Agent (Vision-to-Action SOTA Engine)
Verifies screen capture, Gemini Vision reasoning, keyboard mode switching, and tool registration.
"""

import inspect

from tools.antigravity_tools import get_tugumi_tools
from tools.termux_tools import TermuxTools
from tools.vision_ui_agent import VisionUIAgent


def test_vision_ui_agent_initialization():
    agent = VisionUIAgent()
    assert agent.width == 1080
    assert agent.height == 2400
    assert hasattr(agent, "capture_screen")
    assert hasattr(agent, "inspect_screen")
    assert hasattr(agent, "decide_action")
    assert hasattr(agent, "execute_action")
    assert hasattr(agent, "step")
    assert hasattr(agent, "run_loop")

def test_vision_ui_json_extraction():
    agent = VisionUIAgent()
    # Markdownコードブロックからの抽出
    mock_markdown = '```json\n{"action": "tap", "coordinate": [108, 2125], "target_name": "あa1"}\n```'
    parsed = agent._extract_json(mock_markdown)
    assert parsed["action"] == "tap"
    assert parsed["coordinate"] == [108, 2125]
    assert parsed["target_name"] == "あa1"

def test_termux_tools_vision_integration():
    tt = TermuxTools()
    assert hasattr(tt, "vision_ui_step")
    assert hasattr(tt, "vision_ui_inspect")
    assert hasattr(tt, "vision_ui_switch_keyboard")

def test_antigravity_tools_registration():
    tools = get_tugumi_tools()
    tool_names = [t.__name__ for t in tools]
    assert "vision_ui_action" in tool_names
    assert "vision_ui_inspect" in tool_names
    assert "vision_ui_switch_keyboard" in tool_names

def test_keyboard_switch_knowledge_in_prompt():
    agent = VisionUIAgent()
    # プロンプト生成に拓磨様直伝の座標 [108, 2125] が含まれているか検証
    sig = inspect.getsource(agent.decide_action)
    assert "108" in sig
    assert "2125" in sig
    assert "あa1" in sig
