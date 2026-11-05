"""
Tests for TUGUMIv6 Stealth Web UI & CLI enhancements.
Validates stealth scrape, clone endpoints, and CLI dispatch.
"""

from fastapi.testclient import TestClient
from interfaces.web.web_server import app
from tools.web_cloner import WebCloner

client = TestClient(app)


def test_stealth_status_endpoint():
    """Verifies that /api/stealth/status returns health and stealth readiness."""
    resp = client.get("/api/stealth/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
    health = data.get("health", {})
    assert health.get("stealth_engine_ready") is True
    assert "host" in health


def test_stealth_scrape_endpoint_validation():
    """Verifies that /api/stealth/scrape properly validates empty URL."""
    resp = client.post("/api/stealth/scrape", json={"url": ""})
    assert resp.status_code == 400


def test_stealth_scrape_endpoint_live():
    """Verifies that /api/stealth/scrape successfully extracts content from a real site."""
    resp = client.post("/api/stealth/scrape", json={"url": "https://example.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
    assert "data" in data
    assert data["data"].get("title") == "Example Domain"
    assert "documentation examples" in data["data"].get("text", "")


def test_web_cloner_stealth_engine():
    """Verifies that WebCloner successfully clones a page using stealth engine."""
    cloner = WebCloner()
    meta = cloner.clone_url("https://example.com", custom_name="test_stealth_clone", engine="stealth")
    assert meta["id"] is not None
    assert "Example Domain" in meta["title"]
    assert "Stealth Chromium" in meta["engine"]
    assert meta["size_kb"] > 0
    # Clean up test clone
    cloner.delete_cloned_site(meta["id"])
