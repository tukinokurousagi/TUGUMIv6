# -*- coding: utf-8 -*-
"""
Tests for TUGUMIv6 Web Cloner & WebUI Clone Studio Integration
"""

import os
import sys
import pytest
from starlette.testclient import TestClient

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tools.web_cloner import WebCloner
from tools.antigravity_tools import get_tugumi_tools
from interfaces.web.web_server import app, TOOL_CATEGORIES

@pytest.fixture
def temp_cloner(tmp_path):
    clone_dir = tmp_path / "cloned_sites"
    cloner = WebCloner(clone_dir=str(clone_dir))
    return cloner

def test_web_cloner_base_tag_injection(temp_cloner):
    """Test that <base href> and utf-8 meta tag are properly injected"""
    sample_html = "<html><head><title>Test Page</title></head><body><h1>Hello</h1></body></html>"
    injected = temp_cloner._inject_base_tag(sample_html, "https://example.com/sub/")
    assert '<base href="https://example.com/sub/">' in injected
    assert '<meta charset="utf-8">' in injected

def test_web_cloner_http_clone(temp_cloner):
    """Test cloning with HTTP engine"""
    res = temp_cloner.clone_url("https://example.com", custom_name="pytest_example", engine="http")
    assert res["status"] == "ok" if "status" in res else True
    assert "pytest_example" in res["id"]
    assert res["url"] == "https://example.com"
    assert os.path.exists(res["path"])
    assert res["size_bytes"] > 0
    assert "Example Domain" in res["title"]

    # Verify listing
    sites = temp_cloner.list_cloned_sites()
    assert len(sites) >= 1
    assert sites[0]["id"] == res["id"]

    # Verify get site
    site_info = temp_cloner.get_cloned_site(res["id"])
    assert site_info is not None
    assert site_info["id"] == res["id"]

    # Verify delete site
    deleted = temp_cloner.delete_cloned_site(res["id"])
    assert deleted is True
    assert temp_cloner.get_cloned_site(res["id"]) is None

def test_web_cloner_puppeteer_engine(temp_cloner):
    """Test cloning with Headless Chromium (Puppeteer) engine"""
    res = temp_cloner.clone_url("https://example.com", custom_name="pytest_puppeteer", engine="puppeteer")
    assert res["engine"] == "puppeteer"
    assert "pytest_puppeteer" in res["id"]
    assert os.path.exists(res["path"])
    assert res["size_bytes"] > 0
    assert "Example Domain" in res["title"]

def test_antigravity_tools_registration():
    """Verify clone_website is registered in antigravity tools"""
    tools = get_tugumi_tools()
    tool_names = [getattr(t, "__name__", str(t)) for t in tools]
    assert "clone_website" in tool_names

def test_tool_categories_has_clone_site():
    """Verify tugumi-clone-site is declared in TOOL_CATEGORIES"""
    network_scripts = [s["name"] for s in TOOL_CATEGORIES["network"]["scripts"]]
    assert "tugumi-clone-site" in network_scripts
    clone_script = next(s for s in TOOL_CATEGORIES["network"]["scripts"] if s["name"] == "tugumi-clone-site")
    assert clone_script["preview_type"] == "web_clone"
    assert clone_script["requires_args"] is True

def test_webui_clone_api_e2e():
    """End-to-End API test for /api/clone/* endpoints using TestClient"""
    client = TestClient(app)

    # 1. Validation test (missing URL)
    resp = client.post("/api/clone/create", json={"url": ""})
    assert resp.status_code == 400

    # 2. Create clone site
    resp = client.post("/api/clone/create", json={
        "url": "https://example.com",
        "name": "e2e_test_site",
        "engine": "http"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    site_id = data["site"]["id"]
    assert "e2e_test_site" in site_id

    # 3. List cloned sites
    list_resp = client.get("/api/clone/list")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["status"] == "ok"
    assert any(s["id"] == site_id for s in list_data["sites"])

    # 4. Preview cloned site HTML
    prev_resp = client.get(f"/api/clone/preview/{site_id}")
    assert prev_resp.status_code == 200
    assert "text/html" in prev_resp.headers.get("content-type", "")
    assert "Example Domain" in prev_resp.text
    assert '<base href="https://example.com">' in prev_resp.text

    # 5. Delete cloned site
    del_resp = client.delete(f"/api/clone/{site_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "ok"

    # 6. Verify 404 after deletion
    prev_resp_after = client.get(f"/api/clone/preview/{site_id}")
    assert prev_resp_after.status_code == 404
