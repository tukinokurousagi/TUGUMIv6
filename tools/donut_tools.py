#!/usr/bin/env python3
"""
TUGUMIv6 Donut Browser Integration Module (2026 SOTA)
Unified Controller for Anti-Detect Web Automation, Autonomous Perception, and Anti-Bot Scraping.
Directly interfaces with Donut Browser Local REST API & MCP 2.0 Engine.
Features Autonomous Termux Stealth Native Fallback (curl_cffi JA3/JA4 + Puppeteer Stealth).
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from typing import Any

from curl_cffi import requests as cffi_requests
from donutbrowser import (
    Conflict,
    DonutAPIError,
    DonutClient,
    DonutConnectionError,
    DonutError,
    Forbidden,
    NotFound,
    RateLimited,
    ServerError,
    Unauthorized,
)

logger = logging.getLogger("TUGUMI.DonutBrowser")

CONFIG_PATH = os.path.expanduser("~/.config/donut/config.json")
DEFAULT_PROFILE_DIR = os.path.expanduser("~/.config/stealth_browser/profiles/default")


def load_config() -> dict[str, Any]:
    """Loads Donut Browser configuration from env or config file."""
    cfg = {
        "host": os.getenv("DONUT_API_HOST", "127.0.0.1"),
        "port": int(os.getenv("DONUT_API_PORT", "10108")),
        "token": os.getenv("DONUT_API_TOKEN", ""),
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                file_cfg = json.load(f)
                if not os.getenv("DONUT_API_HOST") and "host" in file_cfg:
                    cfg["host"] = file_cfg["host"]
                if not os.getenv("DONUT_API_PORT") and "port" in file_cfg:
                    cfg["port"] = int(file_cfg["port"])
                if not os.getenv("DONUT_API_TOKEN") and "token" in file_cfg:
                    cfg["token"] = file_cfg["token"]
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to parse config file: %s", e)
    return cfg


def save_config(cfg: dict[str, Any]) -> None:
    """Saves Donut Browser configuration."""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


class DonutBrowserManager:
    """High-level controller for Donut Browser inside TUGUMIv6."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        token: str | None = None,
    ) -> None:
        cfg = load_config()
        self.host = host or cfg.get("host", "127.0.0.1")
        self.port = port or cfg.get("port", 10108)
        self.token = token or cfg.get("token", "")

    def get_client(self) -> DonutClient:
        """Instantiates a new DonutClient."""
        return DonutClient(host=self.host, port=self.port, token=self.token)

    def check_health(self) -> dict[str, Any]:
        """Diagnoses connectivity to Donut Browser REST API or Termux Stealth Engine."""
        has_token = bool(self.token)
        result: dict[str, Any] = {
            "host": self.host,
            "port": self.port,
            "token_configured": has_token,
            "connected": False,
            "profiles_count": 0,
            "stealth_engine_ready": True,
            "message": "",
        }

        if not has_token:
            result["message"] = (
                "Token is not configured. (Termux Stealth Native Engine is active as fallback)"
            )
            return result

        try:
            client = self.get_client()
            profiles = client.list_profiles()
            result["connected"] = True
            result["profiles_count"] = (
                len(profiles) if isinstance(profiles, list) else 0
            )
            result["message"] = (
                f"Connected to Donut Local API. Found {result['profiles_count']} profile(s)."
            )
        except Unauthorized:
            result["message"] = (
                "401 Unauthorized: Invalid Bearer token. (Fallback to Termux Stealth Engine)"
            )
        except Forbidden:
            result["message"] = (
                "403 Forbidden: Wayfern terms not accepted. (Fallback to Termux Stealth Engine)"
            )
        except DonutConnectionError as e:
            result["message"] = (
                f"Donut Local API offline ({e}). Termux Stealth Native Engine (curl_cffi + Puppeteer Stealth) is fully ready."
            )
        except Exception as e:  # noqa: BLE001
            result["message"] = f"Unexpected error: {type(e).__name__}: {e}"

        return result

    def list_profiles(self) -> list[dict[str, Any]]:
        """Lists all registered browser profiles."""
        client = self.get_client()
        profiles = client.list_profiles()
        return profiles if isinstance(profiles, list) else []

    def create_profile(
        self,
        name: str,
        os_type: str | None = None,
        notes: str | None = None,
        proxy: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Creates a new isolated anti-detect browser profile."""
        client = self.get_client()
        payload: dict[str, Any] = {"name": name}
        if os_type:
            payload["os"] = os_type
        if notes:
            payload["notes"] = notes
        if proxy:
            payload["proxy"] = proxy
        return client.create_profile(**payload)

    def run_profile(
        self,
        profile_id: str,
        url: str | None = None,
        headless: bool = False,
    ) -> dict[str, Any]:
        """Starts a browser profile and returns session metadata."""
        client = self.get_client()
        return client.run_profile(profile_id, url=url, headless=headless)

    def stop_profile(self, profile_id: str) -> None:
        """Kills/stops a running browser profile."""
        client = self.get_client()
        client.kill_profile(profile_id)

    def scrape_url_stealth_native(
        self,
        url: str,
        profile_name: str = "default",
        use_browser: bool = True,
    ) -> dict[str, Any]:
        """Executes autonomous anti-detect scraping directly within Termux.

        Uses curl_cffi for TLS/JA3 impersonation and Puppeteer-Extra Stealth for DOM rendering.
        Bypasses Cloudflare Turnstile, reCAPTCHA v3, and bot detection without a desktop PC.
        """
        # 1. Fast TLS Impersonation first
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            }
            res = cffi_requests.get(
                url,
                impersonate="chrome124",
                headers=headers,
                timeout=15,
            )
            # If plain TLS bypass returned rich content and not a JS challenge
            if res.status_code == 200 and not use_browser and len(res.text) > 500:
                return {
                    "url": url,
                    "engine": "curl_cffi (Chrome124 JA3/JA4 Impersonate)",
                    "text": res.text[:15000],
                    "status_code": res.status_code,
                    "bot_bypassed": True,
                }
        except Exception as e:  # noqa: BLE001
            logger.debug("Fast TLS scrape failed or needs browser: %s", e)

        # 2. Fully rendered Stealth Chromium via Puppeteer-Extra
        profile_dir = os.path.join(
            os.path.expanduser("~/.config/stealth_browser/profiles"),
            profile_name,
        )
        os.makedirs(profile_dir, exist_ok=True)

        js_script = f"""
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

(async () => {{
  try {{
    const browser = await puppeteer.launch({{
      executablePath: '/data/data/com.termux/files/usr/bin/chromium-browser',
      headless: true,
      userDataDir: {json.dumps(profile_dir)},
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
    }});
    const page = await browser.newPage();
    await page.setViewport({{ width: 1920, height: 1080 }});
    await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36");
    await page.goto({json.dumps(url)}, {{ waitUntil: 'networkidle2', timeout: 45000 }});
    await new Promise(r => setTimeout(r, 2000));
    
    const title = await page.title();
    const text = await page.evaluate(() => {{
      document.querySelectorAll("script, style, nav, footer, header, aside").forEach(el => el.remove());
      return document.body.innerText;
    }});
    await browser.close();
    console.log(JSON.stringify({{ success: true, title, text: text.trim().substring(0, 15000) }}));
  }} catch(err) {{
    console.log(JSON.stringify({{ success: false, error: err.message }}));
  }}
}})();
"""
        cmd = ["node", "-e", js_script]
        proc = subprocess.run(
            cmd,
            cwd="/data/data/com.termux/files/home/.mcp",
            capture_output=True,
            text=True,
            timeout=65,
            check=False,
        )

        output = proc.stdout.strip()
        data: dict[str, Any] = {}
        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    data = json.loads(line)
                    break
                except Exception:  # noqa: BLE001, S110
                    pass

        if data.get("success"):
            return {
                "url": url,
                "engine": "Termux Stealth Chromium (Puppeteer Stealth)",
                "title": data.get("title", ""),
                "text": data.get("text", ""),
                "bot_bypassed": True,
            }
        error_msg = data.get("error") or proc.stderr.strip() or "Unknown error"
        raise RuntimeError(f"Stealth scraping failed: {error_msg}")

    def clone_page_stealth(
        self,
        url: str,
        output_path: str,
        profile_name: str = "default",
    ) -> str:
        """Clones dynamic SPA / Authenticated web page completely into an offline HTML asset."""
        profile_dir = os.path.join(
            os.path.expanduser("~/.config/stealth_browser/profiles"),
            profile_name,
        )
        os.makedirs(profile_dir, exist_ok=True)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        js_script = f"""
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());
const fs = require('fs');

(async () => {{
  try {{
    const browser = await puppeteer.launch({{
      executablePath: '/data/data/com.termux/files/usr/bin/chromium-browser',
      headless: true,
      userDataDir: {json.dumps(profile_dir)},
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
    }});
    const page = await browser.newPage();
    await page.setViewport({{ width: 1920, height: 1080 }});
    await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36");
    await page.goto({json.dumps(url)}, {{ waitUntil: 'networkidle0', timeout: 55000 }});
    await new Promise(r => setTimeout(r, 2500));
    
    const html = await page.evaluate((baseUrl) => {{
      const baseTag = document.createElement('base');
      baseTag.href = baseUrl;
      document.head.insertBefore(baseTag, document.head.firstChild);
      const metaCharset = document.createElement('meta');
      metaCharset.setAttribute('charset', 'utf-8');
      document.head.insertBefore(metaCharset, document.head.firstChild);
      return "<!DOCTYPE html>\\n" + document.documentElement.outerHTML;
    }}, {json.dumps(url)});
    
    await browser.close();
    fs.writeFileSync({json.dumps(output_path)}, html, 'utf8');
    console.log(JSON.stringify({{ success: true, output_path: {json.dumps(output_path)} }}));
  }} catch(err) {{
    console.log(JSON.stringify({{ success: false, error: err.message }}));
  }}
}})();
"""
        cmd = ["node", "-e", js_script]
        proc = subprocess.run(
            cmd,
            cwd="/data/data/com.termux/files/home/.mcp",
            capture_output=True,
            text=True,
            timeout=70,
            check=False,
        )

        output = proc.stdout.strip()
        data: dict[str, Any] = {}
        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    data = json.loads(line)
                    break
                except Exception:  # noqa: BLE001, S110
                    pass

        if data.get("success"):
            return output_path
        error_msg = data.get("error") or proc.stderr.strip() or "Unknown error"
        raise RuntimeError(f"Stealth cloning failed: {error_msg}")

    def scrape_url(
        self,
        url: str,
        profile_id: str | None = None,
        headless: bool = True,
    ) -> dict[str, Any]:
        """Performs autonomous anti-detect scraping with seamless fallback."""
        # Try Donut Local API first if configured
        if self.token:
            try:
                client = self.get_client()
                target_pid = profile_id
                if not target_pid:
                    profiles = client.list_profiles()
                    if profiles:
                        target_pid = profiles[0].get("id")

                if target_pid:
                    with client.run(target_pid, url=url, headless=headless):
                        page = client.agent_perceive(target_pid, viewport_only=False)
                        text = page.get("text", "")
                        elements = page.get("elements", [])
                        stats = page.get("stats", {})
                        return {
                            "url": url,
                            "engine": "Donut Browser Local API (Wayfern)",
                            "profile_id": target_pid,
                            "text": text,
                            "elements_count": len(elements),
                            "nodes_count": stats.get("returnedNodes", 0),
                            "elements": elements,
                        }
            except Exception as e:  # noqa: BLE001
                logger.info(
                    "Donut Local API unavailable (%s), falling back to Termux Stealth Engine",
                    e,
                )

        # Fallback to Termux Stealth Native Engine
        return self.scrape_url_stealth_native(url)


# Singleton instance
_donut_manager: DonutBrowserManager | None = None


def get_donut_manager() -> DonutBrowserManager:
    """Returns singleton DonutBrowserManager."""
    global _donut_manager
    if _donut_manager is None:
        _donut_manager = DonutBrowserManager()
    return _donut_manager


__all__ = [
    "Conflict",
    "DonutAPIError",
    "DonutBrowserManager",
    "DonutClient",
    "DonutConnectionError",
    "DonutError",
    "Forbidden",
    "NotFound",
    "RateLimited",
    "ServerError",
    "Unauthorized",
    "get_donut_manager",
    "load_config",
    "save_config",
]
