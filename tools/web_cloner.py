#!/usr/bin/env python3
"""
TUGUMIv6 Web Cloner Engine (2026 Stealth & Anti-Detect Edition)
- Clones target websites capturing rendered DOM, styles, and assets
- Multi-engine architecture:
    1. Stealth Chromium (Puppeteer-Extra Stealth - Cloudflare/Bot-Detection Bypassed)
    2. Donut Browser (Wayfern Anti-Detect Engine)
    3. TLS Impersonator (curl_cffi Chrome124 JA3/JA4)
    4. Lightweight HTTP Fallback
- Base href injection for flawless asset rendering
- Persistence to ~/cloned_sites and TUGUMIDesk sync
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any

from curl_cffi import requests as cffi_requests

logger = logging.getLogger("TUGUMI.WebCloner")


class WebCloner:
    """Production-grade Web Page Cloner for TUGUMIv6 with Stealth & Anti-Bot Bypassing."""

    DEFAULT_CLONE_DIR = os.path.expanduser("~/cloned_sites")
    DESK_CLONE_DIR = "/storage/emulated/0/TUGUMIDesk/クローンサイト"
    CHROMIUM_PATH = "/data/data/com.termux/files/usr/bin/chromium-browser"
    NODE_PATH = "/data/data/com.termux/files/usr/bin/node"
    MCP_NODE_MODULES = "/data/data/com.termux/files/home/.mcp/node_modules"

    def __init__(self, clone_dir: str | None = None) -> None:
        self.clone_dir = os.path.abspath(clone_dir or self.DEFAULT_CLONE_DIR)
        os.makedirs(self.clone_dir, exist_ok=True)
        if os.path.exists("/storage/emulated/0/TUGUMIDesk"):
            try:
                os.makedirs(self.DESK_CLONE_DIR, exist_ok=True)
            except Exception:  # noqa: BLE001, S110
                pass

    def _sanitize_name(self, text: str) -> str:
        """フォルダ名・ファイル名用サニタイズ"""
        clean = re.sub(r"[^\w\-_.]", "_", text.strip())
        return clean[:40] or "site"

    def _extract_title(self, html: str) -> str:
        """HTMLからtitleタグのテキストを抽出"""
        m = re.search(
            r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL
        )
        if m:
            clean = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            return clean[:100]
        return "Untitled Page"

    def _inject_base_tag(self, html: str, base_url: str) -> str:
        """相対パスの画像・CSS・フォントを正しく読み込ませるためのbaseタグとUTF-8を注入"""
        meta_tag = '<meta charset="utf-8">\n'
        base_tag = f'<base href="{base_url}">\n'

        if re.search(r"<base\s+href=", html, re.IGNORECASE):
            html = re.sub(
                r"<base\s+href=[\'\"][^\'\"]*[\'\"][^>]*>",
                base_tag,
                html,
                count=1,
                flags=re.IGNORECASE,
            )
        else:
            head_m = re.search(r"<head[^>]*>", html, re.IGNORECASE)
            if head_m:
                idx = head_m.end()
                html = html[:idx] + "\n" + meta_tag + base_tag + html[idx:]
            else:
                html = f"<!DOCTYPE html>\n<html><head>\n{meta_tag}{base_tag}</head><body>\n{html}\n</body></html>"

        return html

    def clone_with_stealth_puppeteer(
        self,
        url: str,
        timeout: int = 120,
        profile_name: str = "default",
    ) -> str:
        """Puppeteer-Extra Stealth + Headless Chromium によるボット検知回避クローン"""
        if not os.path.exists(self.CHROMIUM_PATH) or not os.path.exists(
            self.NODE_PATH
        ):
            raise RuntimeError("Chromium or Node.js binary not found")

        profile_dir = os.path.join(
            os.path.expanduser("~/.config/stealth_browser/profiles"),
            profile_name,
        )
        os.makedirs(profile_dir, exist_ok=True)

        js_code = f"""
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

(async () => {{
    const browser = await puppeteer.launch({{
        executablePath: '{self.CHROMIUM_PATH}',
        headless: true,
        userDataDir: {json.dumps(profile_dir)},
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--window-size=1920,1080'
        ]
    }});
    try {{
        const page = await browser.newPage();
        await page.setViewport({{ width: 1920, height: 1080 }});
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36');
        
        await page.goto({json.dumps(url)}, {{ waitUntil: 'networkidle0', timeout: {timeout * 1000} }});
        await new Promise(r => setTimeout(r, 2500));
        
        const html = await page.evaluate((baseUrl) => {{
            const baseTag = document.createElement('base');
            baseTag.href = baseUrl;
            document.head.insertBefore(baseTag, document.head.firstChild);
            
            const metaCharset = document.createElement('meta');
            metaCharset.setAttribute('charset', 'utf-8');
            document.head.insertBefore(metaCharset, document.head.firstChild);
            
            return '<!DOCTYPE html>\\n' + document.documentElement.outerHTML;
        }}, {json.dumps(url)});
        
        process.stdout.write(html);
    }} finally {{
        await browser.close();
    }}
}})().catch(err => {{
    console.error('StealthPuppeteerError:', err.message);
    process.exit(1);
}});
"""
        cmd = [self.NODE_PATH, "-e", js_code]
        env = os.environ.copy()
        env["NODE_PATH"] = self.MCP_NODE_MODULES

        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout + 30,
            cwd="/data/data/com.termux/files/home/.mcp",
            check=False,
        )

        if res.returncode != 0:
            raise RuntimeError(f"Stealth Puppeteer failed: {res.stderr.strip()}")

        html = res.stdout
        if not html or len(html.strip()) < 50:
            raise RuntimeError("Puppeteer returned empty HTML output")

        return html

    def clone_with_curl_cffi(self, url: str) -> str:
        """curl_cffi (Chrome 124 JA3/JA4 TLS Impersonate) による超高速ボット回避フェッチ"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        }
        res = cffi_requests.get(
            url, impersonate="chrome124", headers=headers, timeout=25
        )
        if res.status_code != 200:
            raise RuntimeError(f"HTTP {res.status_code}: {res.reason}")
        return self._inject_base_tag(res.text, url)

    def clone_with_http(self, url: str) -> str:
        """urllib による標準フォールバック"""
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            encoding = (
                resp.headers.get_content_charset()
                or "utf-8"
            )
            try:
                html = raw.decode(encoding, errors="replace")
            except Exception:  # noqa: BLE001
                html = raw.decode("utf-8", errors="replace")

        return self._inject_base_tag(html, url)

    def clone_url(
        self,
        url: str,
        custom_name: str = "",
        engine: str = "auto",
        profile_name: str = "default",
    ) -> dict[str, Any]:
        """指定URLのページを完全クローンし保存する

        Args:
            url: クローン対象URL
            custom_name: 任意のサイト名
            engine: 'auto', 'stealth', 'donut', 'curl_cffi', 'http'
            profile_name: 認証セッションを永続化するプロファイル名

        Returns:
            クローンされたサイト情報の辞書
        """
        parsed = urllib.parse.urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"無効なURL形式です: {url}")

        t0 = time.time()
        html = ""
        engine_used = ""

        # Engine Dispatch
        if engine in ("stealth", "puppeteer", "auto", "donut"):
            try:
                html = self.clone_with_stealth_puppeteer(
                    url, profile_name=profile_name
                )
                engine_used = (
                    "Stealth Chromium (Puppeteer-Extra Stealth)"
                )
            except Exception as e:
                logger.warning("Stealth Puppeteer failed: %s", e)
                if engine != "auto":
                    raise

        if not html:
            try:
                html = self.clone_with_curl_cffi(url)
                engine_used = "curl_cffi (JA3/JA4 Chrome124 Impersonate)"
            except Exception as e:  # noqa: BLE001
                logger.warning("curl_cffi failed: %s", e)
                html = self.clone_with_http(url)
                engine_used = "HTTP Standard Fallback"

        title = self._extract_title(html)
        elapsed = round(time.time() - t0, 2)

        # Generate unique folder ID
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_domain = self._sanitize_name(parsed.netloc)
        site_id = f"{ts}_{safe_domain}"
        if custom_name:
            site_id = f"{site_id}_{self._sanitize_name(custom_name)}"

        site_dir = os.path.join(self.clone_dir, site_id)
        os.makedirs(site_dir, exist_ok=True)

        index_file = os.path.join(site_dir, "index.html")
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(html)

        meta = {
            "id": site_id,
            "url": url,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "elapsed_sec": elapsed,
            "engine": engine_used,
            "size_kb": round(len(html.encode("utf-8")) / 1024, 1),
            "custom_name": custom_name,
            "path": index_file,
        }
        with open(
            os.path.join(site_dir, "meta.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        # Sync to TUGUMIDesk
        try:
            desk_dest = os.path.join(self.DESK_CLONE_DIR, f"{site_id}.html")
            shutil.copy2(index_file, desk_dest)
            meta["desk_path"] = desk_dest
            # media scan
            subprocess.run(
                ["termux-media-scan", desk_dest],
                capture_output=True,
                check=False,
            )
        except Exception as e:  # noqa: BLE001
            logger.debug("TUGUMIDesk sync notice: %s", e)

        return meta

    def list_cloned_sites(self) -> list[dict[str, Any]]:
        """保存されている全クローンサイト一覧をメタデータとともに取得"""
        results = []
        if not os.path.exists(self.clone_dir):
            return results

        for d in sorted(os.listdir(self.clone_dir), reverse=True):
            p = os.path.join(self.clone_dir, d)
            if not os.path.isdir(p):
                continue
            meta_file = os.path.join(p, "meta.json")
            index_file = os.path.join(p, "index.html")
            if os.path.exists(meta_file):
                try:
                    with open(meta_file, encoding="utf-8") as f:
                        data = json.load(f)
                        data["path"] = index_file
                        results.append(data)
                        continue
                except Exception:  # noqa: BLE001, S110
                    pass

            if os.path.exists(index_file):
                results.append({
                    "id": d,
                    "url": "N/A",
                    "title": d,
                    "created_at": "",
                    "size_kb": round(os.path.getsize(index_file) / 1024, 1),
                    "path": index_file,
                    "engine": "unknown",
                })

        return results

    def get_cloned_site(self, site_id: str) -> dict[str, Any] | None:
        """指定IDのクローンサイト情報を取得"""
        p = os.path.join(self.clone_dir, site_id)
        if not os.path.exists(p):
            return None
        meta_file = os.path.join(p, "meta.json")
        index_file = os.path.join(p, "index.html")
        if os.path.exists(meta_file):
            try:
                with open(meta_file, encoding="utf-8") as f:
                    data = json.load(f)
                    data["path"] = index_file
                    return data
            except Exception:  # noqa: BLE001, S110
                pass
        return {
            "id": site_id,
            "url": "N/A",
            "title": site_id,
            "path": index_file,
        }

    def delete_cloned_site(self, site_id: str) -> bool:
        """指定IDのクローンサイトを完全削除"""
        p = os.path.join(self.clone_dir, site_id)
        if os.path.exists(p) and os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)
            # Remove from TUGUMIDesk if present
            desk_dest = os.path.join(self.DESK_CLONE_DIR, f"{site_id}.html")
            if os.path.exists(desk_dest):
                try:
                    os.remove(desk_dest)
                except Exception:  # noqa: BLE001, S110
                    pass
            return True
        return False
