"""
Tests for TUGUMIv6 and Antigravity CLI Donut Browser Integration.
Verifies MCP 2.0 schemas, configuration, high-level manager, and offline safety.
"""

import json
import os

from tools.donut_tools import (
    DonutBrowserManager,
    get_donut_manager,
    load_config,
    save_config,
)

MCP_CONFIG_PATH = "/data/data/com.termux/files/home/.gemini/config/mcp_config.json"
MCP_SCHEMA_DIR = "/data/data/com.termux/files/home/.gemini/antigravity-cli/mcp/donut_browser"


def test_donut_tools_import_and_singleton():
    """Verifies that DonutBrowserManager can be imported and initialized."""
    mgr = get_donut_manager()
    assert isinstance(mgr, DonutBrowserManager)
    assert mgr.host in ("127.0.0.1", "localhost") or isinstance(mgr.host, str)
    assert isinstance(mgr.port, int)


def test_donut_config_persistence(tmp_path, monkeypatch):
    """Verifies that config loading and saving works cleanly."""
    fake_config = tmp_path / "config.json"
    monkeypatch.setattr("tools.donut_tools.CONFIG_PATH", str(fake_config))

    test_cfg = {"host": "192.168.1.100", "port": 10200, "token": "test-token-123"}
    save_config(test_cfg)

    loaded = load_config()
    assert loaded["host"] == "192.168.1.100"
    assert loaded["port"] == 10200
    assert loaded["token"] == "test-token-123"


def test_donut_check_health_unconfigured():
    """Verifies that check_health gracefully handles missing token/connection without raising."""
    mgr = DonutBrowserManager(token="")
    health = mgr.check_health()
    assert isinstance(health, dict)
    assert health["connected"] is False
    assert "Token is not configured" in health["message"]


def test_donut_mcp_tools_exposed():
    """Verifies that the MCP server exposes all required Donut Browser automation tools."""
    import sys
    sys.path.insert(0, "/data/data/com.termux/files/home/.mcp")
    import donut_browser_mcp

    assert hasattr(donut_browser_mcp, "donut_status")
    assert hasattr(donut_browser_mcp, "donut_config")
    assert hasattr(donut_browser_mcp, "donut_list_profiles")
    assert hasattr(donut_browser_mcp, "donut_get_profile")
    assert hasattr(donut_browser_mcp, "donut_create_profile")
    assert hasattr(donut_browser_mcp, "donut_run_profile")
    assert hasattr(donut_browser_mcp, "donut_kill_profile")
    assert hasattr(donut_browser_mcp, "donut_open_url")
    assert hasattr(donut_browser_mcp, "donut_perceive")
    assert hasattr(donut_browser_mcp, "donut_click")
    assert hasattr(donut_browser_mcp, "donut_type")
    assert hasattr(donut_browser_mcp, "donut_extract")
    assert hasattr(donut_browser_mcp, "donut_scrape")


def test_antigravity_mcp_config_registration():
    """Verifies that donut_browser is registered in Antigravity CLI's mcp_config.json."""
    assert os.path.exists(MCP_CONFIG_PATH)
    with open(MCP_CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    servers = data.get("mcpServers", {})
    assert "donut_browser" in servers
    assert servers["donut_browser"].get("disabled") is False
    assert "donut_browser_mcp.py" in servers["donut_browser"]["args"][0]


def test_antigravity_mcp_schemas_validity():
    """Verifies that all Antigravity CLI tool schemas exist and are valid JSON."""
    assert os.path.isdir(MCP_SCHEMA_DIR)
    expected_tools = [
        "donut_status",
        "donut_config",
        "donut_list_profiles",
        "donut_get_profile",
        "donut_create_profile",
        "donut_run_profile",
        "donut_kill_profile",
        "donut_open_url",
        "donut_perceive",
        "donut_click",
        "donut_type",
        "donut_extract",
        "donut_scrape",
    ]
    for tool in expected_tools:
        schema_file = os.path.join(MCP_SCHEMA_DIR, f"{tool}.json")
        assert os.path.exists(schema_file), f"Missing schema file: {schema_file}"
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = json.load(f)
        assert schema.get("name") == tool
        assert "description" in schema
        assert "parameters" in schema
