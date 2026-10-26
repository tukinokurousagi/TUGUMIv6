# -*- coding: utf-8 -*-
"""
TUGUMIv6 Web Cloner Engine
- Clones target websites capturing rendered DOM, styles, and assets
- Dual-engine architecture: Headless Chromium (Puppeteer) with urllib fallback
- Base href injection for flawless asset rendering
- Persistence to ~/cloned_sites and TUGUMIDesk sync
"""

import os
import re
import json
import time
import shutil
import urllib.request
import urllib.parse
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional

class WebCloner:
    """Production-grade Web Page Cloner for TUGUMIv6"""

    DEFAULT_CLONE_DIR = os.path.expanduser("~/cloned_sites")
    DESK_CLONE_DIR = "/storage/emulated/0/TUGUMIDesk/クローンサイト"
    CHROMIUM_PATH = "/data/data/com.termux/files/usr/bin/chromium-browser"
    NODE_PATH = "/data/data/com.termux/files/usr/bin/node"
    MCP_NODE_MODULES = "/data/data/com.termux/files/home/.mcp/node_modules"

    def __init__(self, clone_dir: Optional[str] = None):
        self.clone_dir = os.path.abspath(clone_dir or self.DEFAULT_CLONE_DIR)
        os.makedirs(self.clone_dir, exist_ok=True)
        if os.path.exists("/storage/emulated/0/TUGUMIDesk"):
            try:
                os.makedirs(self.DESK_CLONE_DIR, exist_ok=True)
            except Exception:
                pass

    def _sanitize_name(self, text: str) -> str:
        """フォルダ名・ファイル名用サニタイズ"""
        clean = re.sub(r'[^\w\-_.]', '_', text.strip())
        return clean[:40] or "site"

    def _extract_title(self, html: str) -> str:
        """HTMLからtitleタグのテキストを抽出"""
        m = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if m:
            clean = re.sub(r'<[^>]+>', '', m.group(1)).strip()
            return clean[:100]
        return "Untitled Page"

    def _inject_base_tag(self, html: str, base_url: str) -> str:
        """相対パスの画像・CSS・フォントを正しく読み込ませるためのbaseタグとUTF-8を注入"""
        # Ensure utf-8 meta tag exists
        meta_tag = '<meta charset="utf-8">\n'
        base_tag = f'<base href="{base_url}">\n'

        # Check if base tag already exists
        if re.search(r'<base\s+href=', html, re.IGNORECASE):
            # Replace existing base href
            html = re.sub(r'<base\s+href=[\'"][^\'"]*[\'"][^>]*>', base_tag, html, count=1, flags=re.IGNORECASE)
        else:
            # Insert after <head>
            head_m = re.search(r'<head[^>]*>', html, re.IGNORECASE)
            if head_m:
                idx = head_m.end()
                html = html[:idx] + "\n" + meta_tag + base_tag + html[idx:]
            else:
                html = f"<!DOCTYPE html>\n<html><head>\n{meta_tag}{base_tag}</head><body>\n{html}\n</body></html>"

        return html

    def clone_with_puppeteer(self, url: str, timeout: int = 120) -> str:
        """Puppeteer + Headless Chromium による完全SPA/JSレンダリング・DOM取得"""
        if not os.path.exists(self.CHROMIUM_PATH) or not os.path.exists(self.NODE_PATH):
            raise RuntimeError("Chromium or Node.js binary not found")

        # Inline Node.js script using puppeteer-core
        js_code = f"""
const puppeteer = require('puppeteer-core');
const fs = require('fs');

(async () => {{
    const browser = await puppeteer.launch({{
        executablePath: '{self.CHROMIUM_PATH}',
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-extensions'
        ]
    }});
    try {{
        const page = await browser.newPage();
        await page.setUserAgent('Mozilla/5.0 (Linux; Android 14; Termux) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36');
        await page.setViewport({{ width: 1280, height: 800 }});
        
        await page.goto({json.dumps(url)}, {{ waitUntil: 'domcontentloaded', timeout: {timeout * 1000} }});
        await new Promise(r => setTimeout(r, 1500));
        
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
    console.error('PuppeteerError:', err.message);
    process.exit(1);
}});
"""
        env = {
            **os.environ,
            "NODE_PATH": self.MCP_NODE_MODULES,
            "TERM": "dumb"
        }
        res = subprocess.run(
            [self.NODE_PATH, "-e", js_code],
            capture_output=True,
            text=True,
            timeout=timeout + 5,
            env=env
        )
        if res.returncode != 0 or not res.stdout.strip():
            err_msg = res.stderr.strip() or "Puppeteer exited with non-zero code"
            raise RuntimeError(f"Puppeteer failed: {err_msg}")

        return res.stdout

    def clone_with_http(self, url: str, timeout: int = 60) -> str:
        """HTTPフェッチによる高速軽量クローン (フォールバック用)"""
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; Termux) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            encoding = "utf-8"
            if "charset=" in content_type:
                encoding = content_type.split("charset=")[-1].split(";")[0].strip()
            raw_data = resp.read()
            try:
                html = raw_data.decode(encoding)
            except Exception:
                html = raw_data.decode("utf-8", errors="replace")

        return self._inject_base_tag(html, url)

    def clone_url(self, url: str, custom_name: str = "", engine: str = "auto", timeout: int = 120) -> Dict[str, Any]:
        """指定URLのクローンサイトを生成・保存"""
        url = url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc or "website"
        now = datetime.now()
        timestamp_str = now.strftime("%Y%m%d_%H%M%S")
        
        name_part = self._sanitize_name(custom_name) if custom_name else self._sanitize_name(domain)
        site_id = f"{timestamp_str}_{name_part}"
        site_dir = os.path.join(self.clone_dir, site_id)
        os.makedirs(site_dir, exist_ok=True)

        html_content = ""
        engine_used = ""
        error_notes = []

        start_time = time.time()

        if engine in ("auto", "puppeteer"):
            try:
                html_content = self.clone_with_puppeteer(url, timeout=timeout)
                engine_used = "puppeteer"
            except Exception as e:
                error_notes.append(f"Puppeteer attempt failed: {e}")
                if engine == "puppeteer":
                    raise RuntimeError(f"Puppeteer failed: {e}")

        if not html_content and engine in ("auto", "http", "curl"):
            try:
                html_content = self.clone_with_http(url, timeout=min(timeout, 60))
                engine_used = "http_fallback" if engine == "auto" else "http"
            except Exception as e:
                error_notes.append(f"HTTP fetch attempt failed: {e}")
                raise RuntimeError(f"All cloning engines failed: {'; '.join(error_notes)}")

        elapsed_sec = round(time.time() - start_time, 2)
        title = self._extract_title(html_content)

        # 保存
        index_file = os.path.join(site_dir, "index.html")
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        size_bytes = os.path.getsize(index_file)
        size_kb = round(size_bytes / 1024, 1)

        # メタデータ
        meta = {
            "id": site_id,
            "url": url,
            "title": title,
            "name": custom_name or domain,
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": timestamp_str,
            "size_bytes": size_bytes,
            "size_kb": size_kb,
            "engine": engine_used,
            "elapsed_sec": elapsed_sec,
            "path": index_file,
            "preview_endpoint": f"/api/clone/preview/{site_id}"
        }

        meta_file = os.path.join(site_dir, "meta.json")
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # TUGUMIDeskへ同期 (アクセス可能な場合)
        if os.path.exists(self.DESK_CLONE_DIR):
            try:
                desk_target_dir = os.path.join(self.DESK_CLONE_DIR, site_id)
                os.makedirs(desk_target_dir, exist_ok=True)
                shutil.copy2(index_file, os.path.join(desk_target_dir, "index.html"))
                shutil.copy2(meta_file, os.path.join(desk_target_dir, "meta.json"))
                meta["synced_to_desk"] = True
            except Exception:
                meta["synced_to_desk"] = False
        else:
            meta["synced_to_desk"] = False

        return meta

    def list_cloned_sites(self) -> List[Dict[str, Any]]:
        """保存されたクローンサイト一覧を取得（新しい順）"""
        if not os.path.exists(self.clone_dir):
            return []

        sites = []
        for entry in os.listdir(self.clone_dir):
            site_path = os.path.join(self.clone_dir, entry)
            if not os.path.isdir(site_path):
                continue
            meta_file = os.path.join(site_path, "meta.json")
            index_file = os.path.join(site_path, "index.html")
            if os.path.exists(meta_file):
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    sites.append(meta)
                    continue
                except Exception:
                    pass

            if os.path.exists(index_file):
                # Fallback meta if meta.json was missing
                sites.append({
                    "id": entry,
                    "url": "N/A",
                    "title": entry,
                    "name": entry,
                    "created_at": datetime.fromtimestamp(os.path.getmtime(index_file)).strftime("%Y-%m-%d %H:%M:%S"),
                    "size_bytes": os.path.getsize(index_file),
                    "size_kb": round(os.path.getsize(index_file) / 1024, 1),
                    "engine": "unknown",
                    "path": index_file,
                    "preview_endpoint": f"/api/clone/preview/{entry}"
                })

        # 新しい順にソート
        sites.sort(key=lambda s: s.get("created_at", ""), reverse=True)
        return sites

    def get_cloned_site(self, site_id: str) -> Optional[Dict[str, Any]]:
        """特定のクローンサイトのメタデータおよびHTMLファイルパスを取得"""
        site_dir = os.path.join(self.clone_dir, site_id)
        index_file = os.path.join(site_dir, "index.html")
        if not os.path.exists(index_file):
            return None

        meta_file = os.path.join(site_dir, "meta.json")
        if os.path.exists(meta_file):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        return {
            "id": site_id,
            "url": "N/A",
            "title": site_id,
            "path": index_file,
            "preview_endpoint": f"/api/clone/preview/{site_id}"
        }

    def delete_cloned_site(self, site_id: str) -> bool:
        """クローンサイトの削除"""
        site_dir = os.path.join(self.clone_dir, site_id)
        if os.path.exists(site_dir) and os.path.isdir(site_dir):
            shutil.rmtree(site_dir, ignore_errors=True)
            # Remove from desk if present
            desk_dir = os.path.join(self.DESK_CLONE_DIR, site_id)
            if os.path.exists(desk_dir):
                shutil.rmtree(desk_dir, ignore_errors=True)
            return True
        return False
