"""
TUGUMIv6 Proactive Research & Report Tools
- Autonomous Web Search & Crawling
- Evidence Grounding & Fact Verification
- Professional Inverted Pyramid & IMRaD Report Generation
"""

import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

try:
    import trafilatura
except ImportError:
    trafilatura = None
try:
    import markdown
except ImportError:
    markdown = None
try:
    import tabulate
except ImportError:
    tabulate = None
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

class ResearchTools:
    """Proactive Evidence Grounding & Professional Research Engine"""
    def __init__(self, timeout: float = 90.0):
        self.timeout = timeout

    def search_news_rss(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Google News RSS を用いたリアルタイム一次ソース・ニュース検索"""
        encoded_query = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ja&gl=JP&ceid=JP:ja"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            }
        )
        results = []
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                root = ET.fromstring(resp.read())
                items = root.findall(".//item")
                for item in items[:max_results]:
                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    desc_elem = item.find("description")
                    pub_elem = item.find("pubDate")
                    source_elem = item.find("source")

                    title = title_elem.text if title_elem is not None else ""
                    link = link_elem.text if link_elem is not None else ""
                    desc = desc_elem.text if desc_elem is not None else ""
                    pub_date = pub_elem.text if pub_elem is not None else ""
                    source = source_elem.text if source_elem is not None else ""

                    clean_desc = re.sub(r'<[^>]+>', '', desc).strip()

                    results.append({
                        "title": title.strip(),
                        "url": link.strip(),
                        "snippet": clean_desc or title.strip(),
                        "pub_date": pub_date.strip(),
                        "source": source.strip()
                    })
        except Exception as e:  # noqa: BLE001
            results.append({"error": str(e), "query": query})
        return results

    def search_web_lite(self, query: str, max_results: int = 5, auto_crawl: bool = True) -> list[dict[str, Any]]:
        """DuckDuckGo + Yahoo Japan + Google News RSS ハイブリッド3重冗長Web検索
        
        Mechanical Inline Deep Crawl:
        auto_crawl=True の場合、上位2件のURL本文（Trafilatura）を自動抽出して 'extracted_body' に強制同梱。
        プロンプトの指示・ルールに頼らず、検索実行時に生本文を物理的に供給する。
        """
        results = []
        
        # 1. DuckDuckGo HTML
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                }
            )
            with urllib.request.urlopen(req, timeout=min(self.timeout, 12.0)) as resp:
                html = resp.read().decode("utf-8", errors="replace")

            matches = re.findall(r'<a class="result__url" href="([^"]+)">\s*([^<]+)\s*</a>.*?<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', html, re.DOTALL)
            for m in matches[:max_results]:
                link, display_url, snippet = m
                clean_snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                results.append({
                    "title": display_url.strip(),
                    "url": link.strip(),
                    "snippet": clean_snippet
                })
        except Exception:  # noqa: BLE001, S110
            pass

        # 2. Yahoo Japan Organic Search Fallback
        if not results and BeautifulSoup:
            try:
                yahoo_url = f"https://search.yahoo.co.jp/search?p={urllib.parse.quote(query)}"
                req = urllib.request.Request(
                    yahoo_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                        "Accept-Language": "ja,en;q=0.9"
                    }
                )
                with urllib.request.urlopen(req, timeout=min(self.timeout, 12.0)) as resp:
                    y_html = resp.read().decode("utf-8", errors="replace")
                soup = BeautifulSoup(y_html, "html.parser")
                for heading in soup.find_all(re.compile(r"^h[2-4]$")):
                    a = heading.find_parent("a") or heading.find("a")
                    if a and a.get("href"):
                        link = a.get("href")
                        if not link.startswith("http") or "yahoo.co.jp" in link and "search" in link:
                            continue
                        title = heading.get_text(strip=True)
                        card = heading.find_parent("li") or heading.find_parent("div")
                        snippet = ""
                        if card:
                            texts = [p.get_text(strip=True) for p in card.find_all(["p", "span"]) if len(p.get_text(strip=True)) > 20]
                            if texts:
                                snippet = texts[0]
                        results.append({"title": title, "url": link, "snippet": snippet})
                        if len(results) >= max_results:
                            break
            except Exception:  # noqa: BLE001, S110
                pass

        # 3. Google News RSS Fallback
        if not results:
            rss_results = self.search_news_rss(query, max_results=max_results)
            if rss_results and "error" not in rss_results[0]:
                results = rss_results

        # Mechanical Inline Deep Crawl: 上位2件の生本文およびOGP画像を物理的に自動注入
        if auto_crawl and results:
            for _idx, r in enumerate(results[:2]):
                url = r.get("url")
                if url and url.startswith("http"):
                    try:
                        raw_body = self.fetch_url_markdown(url)
                        if raw_body and not raw_body.startswith("[Error"):
                            r["extracted_body"] = raw_body[:3000]
                            # OGP画像抽出
                            img_match = re.search(r"【代表画像/OGP】:\s*(https?://[^\s\n]+)", raw_body)
                            if img_match:
                                r["image_url"] = img_match.group(1).strip()
                        else:
                            r["extracted_body"] = ""
                    except Exception:  # noqa: BLE001
                        r["extracted_body"] = ""

        return results

    def fetch_url_markdown(self, url: str) -> str:
        """一次ソースWebページの高精度本文・OGP画像・メタデータ抽出（trafilaturaエンジン優先）"""
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                html = resp.read().decode("utf-8", errors="replace")

            og_image = ""
            # OGP画像抽出
            for pat in [
                r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']',
                r'<meta\s+content=["\']([^"\']+)["\']\s+property=["\']og:image["\']',
                r'<meta\s+name=["\']twitter:image["\']\s+content=["\']([^"\']+)["\']'
            ]:
                m = re.search(pat, html, re.IGNORECASE)
                if m:
                    candidate = m.group(1).strip()
                    if candidate.startswith("//"):
                        og_image = "https:" + candidate
                    elif candidate.startswith("http"):
                        og_image = candidate
                    elif url:
                        og_image = urllib.parse.urljoin(url, candidate)
                    break

            # 1. Trafilatura 高精度抽出
            if trafilatura:
                extracted = trafilatura.extract(html, include_comments=False, include_tables=True, output_format="txt")
                if extracted:
                    meta = trafilatura.extract_metadata(html)
                    meta_str = ""
                    if meta and meta.title:
                        meta_str += f"【タイトル】: {meta.title}\n"
                    if not og_image and meta and meta.image:
                        og_image = meta.image
                    if og_image:
                        meta_str += f"【代表画像/OGP】: {og_image}\n"
                    if len(extracted) > 8000:
                        extracted = extracted[:8000] + "\n... [中略（主要部8,000文字抽出）] ..."
                    return meta_str + extracted

            # 2. BeautifulSoup / 正規表現フォールバック
            cleaned = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', cleaned)
            text = re.sub(r'\s+', ' ', text).strip()
            fallback_meta = f"【代表画像/OGP】: {og_image}\n" if og_image else ""

            # Check for Cloudflare / Bot Wall keywords
            if any(k in text.lower() for k in ["turnstile", "captcha", "verify you are human", "checking your browser", "cf-ray", "access denied"]) or len(text) < 100:
                raise RuntimeError("Bot detection or Cloudflare challenge encountered")

            return fallback_meta + text[:4000]
        except Exception as e:  # noqa: BLE001
            # Autonomous Stealth Browser & Anti-Bot Fallback (Donut / Stealth Chromium)
            try:
                from tools.donut_tools import get_donut_manager
                mgr = get_donut_manager()
                res = mgr.scrape_url(url)
                stealth_text = res.get("text", "").strip()
                engine_name = res.get("engine", "Stealth Native")
                if stealth_text:
                    prefix = f"【アンチボット自動回避エンジン ({engine_name}) による抽出】\n"
                    return prefix + stealth_text[:8000]
            except Exception as stealth_e:  # noqa: BLE001
                return f"[Error fetching URL {url}: {e} (Stealth Fallback Error: {stealth_e})]"
            return f"[Error fetching URL {url}: {e}]"

    def format_professional_report(self, title: str, summary: str, evidence: list[str], details: str) -> str:
        """反転ピラミッド形式のプロフェッショナルレポート出力"""
        report = f"# 【調査レポート】{title}\n\n"
        report += f"## 1. エグゼクティブサマリー (結論先行)\n{summary}\n\n"
        report += "## 2. 客観的エビデンス・一次ソース\n"
        for ev in evidence:
            report += f"- {ev}\n"
        report += f"\n## 3. 詳細分析・技術仕様\n{details}\n"
        return report

    def format_commercial_report(
        self,
        title: str,
        exec_summary: str,
        evidence_matrix: list[list[str]],
        conflict_matrix: list[list[str]],
        details_body: str,
        mermaid_diagram: str = "",
        comparison_table: str = "",
        action_plan: str = "",
        primary_sources: list[dict[str, str]] | None = None,
        key_visuals: list[str] | None = None
    ) -> str:
        """商用100点満点基準の完全構造化プロフェッショナルレポート生成"""
        import time
        now_date = time.strftime("%Y-%m-%d")
        
        report = (
            f"# 【調査レポート】{title}\n\n"
            f"> **メタデータ**: 作成日: {now_date} | 調査参謀: つぐみ (TUGUMIv6 Intelligence) | 機密度: 社外秘・商用マスター\n\n"
            f"## 1. エグゼクティブ・サマリー (結論先行)\n"
            f"{exec_summary}\n\n"
        )

        if key_visuals:
            report += "## 2. 視覚的エビデンス・キービジュアル\n"
            for kv in key_visuals:
                report += f"- ![{title}]({kv})\n"
            report += "\n"

        if evidence_matrix and tabulate:
            report += "## 3. 多角エビデンス検証マトリクス\n\n"
            report += tabulate.tabulate(evidence_matrix, headers="firstrow", tablefmt="github") + "\n\n"

        if conflict_matrix and tabulate:
            report += "## 4. ファクト矛盾・論争点検証マトリクス\n\n"
            report += tabulate.tabulate(conflict_matrix, headers="firstrow", tablefmt="github") + "\n\n"

        if mermaid_diagram:
            report += f"## 5. コアアーキテクチャ・構造可視化\n\n```mermaid\n{mermaid_diagram.strip()}\n```\n\n"

        report += f"## 6. 詳細分析・技術仕様\n{details_body}\n\n"

        if comparison_table:
            report += f"## 7. 比較分析・トレードオフ評価\n\n{comparison_table}\n\n"

        if action_plan:
            report += f"## 8. 将来展望・拓磨様への具体的提言＆ToDo\n\n{action_plan}\n\n"

        if primary_sources:
            report += "## 9. 参照一次ソース・正規エビデンス一覧\n"
            for s in primary_sources:
                name = s.get("title", s.get("url", "一次ソース"))
                url = s.get("url", "")
                report += f"- [{name}]({url})\n"
            report += "\n"

        return report

    def save_markdown_report(self, title: str, content: str, category: str = "リサーチ") -> dict[str, Any]:
        """TUGUMIDesk配下の指定カテゴリ（規約第4章16大分類）に日付入りMarkdownレポートを安全に保存"""
        import os
        import time
        category_map = {
            "説明書": "説明書", "マニュアル": "説明書", "guide": "説明書",
            "ai": "AI・エージェント", "ai・エージェント": "AI・エージェント", "エージェント": "AI・エージェント",
            "システム": "システム開発", "システム開発": "システム開発", "開発": "システム開発",
            "セキュリティ": "セキュリティ",
            "リサーチ": "リサーチ", "技術調査": "リサーチ", "調査": "リサーチ",
            "裏話": "裏話リサーチ", "裏話リサーチ": "裏話リサーチ",
            "アイドル": "アイドル・エンタメ", "アイドル・エンタメ": "アイドル・エンタメ", "エンタメ": "アイドル・エンタメ",
            "人物": "人物",
            "心理学": "心理学・カウンセリング", "心理学・カウンセリング": "心理学・カウンセリング", "カウンセリング": "心理学・カウンセリング",
            "競馬": "競馬予想", "競馬予想": "競馬予想",
            "副業": "副業・収益化", "副業・収益化": "副業・収益化", "収益化": "副業・収益化",
            "デイリー": "デイリーブリーフィング", "デイリーブリーフィング": "デイリーブリーフィング", "ブリーフィング": "デイリーブリーフィング",
            "ui": "UIデザイン", "uiデザイン": "UIデザイン", "webapps": "WebApps",
            "クローン": "クローンサイト", "クローンサイト": "クローンサイト",
            "agent設定ファイル": "Agent設定ファイル", "設定": "Agent設定ファイル",
            "共有フォルダ": "共有フォルダ", "共有": "共有フォルダ",
        }
        normalized_category = category_map.get(str(category).lower().strip(), str(category).strip())
        if not normalized_category:
            normalized_category = "リサーチ"

        date_str = time.strftime("%Y%m%d")
        safe_title = re.sub(r'[\s/\\:*?"<>|]+', '_', title).strip("_")
        filename = f"{date_str}_{safe_title}.md"
        
        base_dir = f"/storage/emulated/0/TUGUMIDesk/{normalized_category}"
        if not os.path.exists(base_dir):
            base_dir = os.path.expanduser(f"~/TUGUMIDesk/{normalized_category}")
        os.makedirs(base_dir, exist_ok=True)

        target_path = os.path.join(base_dir, filename)
        # 既存ファイルがある場合は連番
        counter = 1
        while os.path.exists(target_path):
            filename = f"{date_str}_{safe_title}_{counter}.md"
            target_path = os.path.join(base_dir, filename)
            counter += 1

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "success": True,
            "filename": filename,
            "path": target_path,
            "size_bytes": len(content.encode("utf-8"))
        }

    def render_beautiful_html(self, title: str, markdown_content: str, theme: str = "Midnight Galaxy") -> str:
        """MarkdownレポートをPython markdownエンジン + Tailwind CSS + Mermaid.js + Printスタイルの商用最高峰美麗HTMLに変換"""
        themes = {
            "Midnight Galaxy": {"bg": "#0f172a", "text": "#f8fafc", "card": "#1e293b", "primary": "#3b82f6", "accent": "#8b5cf6", "border": "rgba(59, 130, 246, 0.3)"},
            "Cyberpunk": {"bg": "#0a0a12", "text": "#e0f2fe", "card": "#131325", "primary": "#00f0ff", "accent": "#ff007f", "border": "rgba(0, 240, 255, 0.3)"},
            "Modern Light": {"bg": "#f8fafc", "text": "#0f172a", "card": "#ffffff", "primary": "#2563eb", "accent": "#4f46e5", "border": "rgba(226, 232, 240, 0.8)"}
        }
        t = themes.get(theme, themes["Midnight Galaxy"])

        # 1. Mermaidコードブロックの一時置換保護
        mermaid_blocks = []
        def _save_mermaid(match):
            idx = len(mermaid_blocks)
            code = match.group(1).strip()
            mermaid_blocks.append(code)
            return f"\n\n<!--MERMAID_PLACEHOLDER_{idx}-->\n\n"

        processed_md = re.sub(r'```mermaid\s*\n(.*?)\n```', _save_mermaid, markdown_content, flags=re.DOTALL)

        # 2. Python markdown エンジンによる本格レンダリング（表、コードブロック、目次完備）
        body_html = None
        if markdown:
            try:
                body_html = markdown.markdown(
                    processed_md,
                    extensions=["tables", "fenced_code", "nl2br", "sane_lists"]
                )
            except Exception:  # noqa: BLE001
                body_html = None

        if not body_html:
            # フォールバック簡易変換
            html_lines = []
            for line in processed_md.splitlines():
                line_str = line.strip()
                if line_str.startswith("# "):
                    html_lines.append(f"<h1 class='text-2xl font-bold mt-6 mb-4' style='color:{t['primary']}'>{line_str[2:]}</h1>")
                elif line_str.startswith("## "):
                    html_lines.append(f"<h2 class='text-xl font-semibold mt-5 mb-3 border-b pb-2' style='border-color:{t['accent']}; color:{t['accent']}'>{line_str[3:]}</h2>")
                elif line_str.startswith("### "):
                    html_lines.append(f"<h3 class='text-lg font-medium mt-4 mb-2'>{line_str[4:]}</h3>")
                elif line_str.startswith("- "):
                    html_lines.append(f"<li class='ml-4 list-disc text-slate-300'>{line_str[2:]}</li>")
                elif line_str:
                    html_lines.append(f"<p class='my-2 leading-relaxed text-slate-300'>{line_str}</p>")
                else:
                    html_lines.append("<br/>")
            body_html = "\n".join(html_lines)

        # 3. Mermaidブロックの復元
        for idx, m_code in enumerate(mermaid_blocks):
            mermaid_html = (
                f'<div class="mermaid my-6 p-4 rounded-xl bg-slate-900 border border-cyan-500/30 flex justify-center overflow-x-auto shadow-inner">'
                f'{m_code}'
                f'</div>'
            )
            body_html = body_html.replace(f"<!--MERMAID_PLACEHOLDER_{idx}-->", mermaid_html)
            body_html = body_html.replace(f"&lt;!--MERMAID_PLACEHOLDER_{idx}--&gt;", mermaid_html)

        html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | TUGUMIv6 Intelligence</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{startOnLoad:true, theme:'dark', securityLevel:'loose'}});</script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+JP:wght@400;500;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', 'Noto Sans JP', sans-serif; background-color: {t['bg']}; color: {t['text']}; }}
        pre, code {{ font-family: 'JetBrains Mono', monospace; }}
        table {{ width: 100%; border-collapse: collapse; margin: 1.5rem 0; border-radius: 0.5rem; overflow: hidden; }}
        th {{ background-color: rgba(255, 255, 255, 0.08); color: {t['primary']}; font-weight: 600; padding: 0.75rem 1rem; border-bottom: 2px solid rgba(255, 255, 255, 0.15); text-align: left; }}
        td {{ padding: 0.75rem 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.06); }}
        tr:nth-child(even) {{ background-color: rgba(255, 255, 255, 0.02); }}
        tr:hover {{ background-color: rgba(255, 255, 255, 0.05); }}
        pre {{ background-color: #050811; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 0.75rem; padding: 1rem; overflow-x: auto; margin: 1.25rem 0; }}
        blockquote {{ border-left: 4px solid {t['primary']}; padding-left: 1rem; color: #94a3b8; font-style: italic; margin: 1rem 0; }}
        h1, h2, h3, h4 {{ color: #f8fafc; font-weight: 700; margin-top: 1.5rem; margin-bottom: 0.75rem; }}
        h1 {{ font-size: 1.75rem; color: {t['primary']}; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.5rem; }}
        h2 {{ font-size: 1.35rem; color: {t['accent']}; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 0.25rem; }}
        h3 {{ font-size: 1.15rem; }}
        ul, ol {{ margin-left: 1.5rem; margin-bottom: 1rem; }}
        li {{ margin-bottom: 0.25rem; }}
        img {{ max-width: 100%; border-radius: 0.75rem; margin: 1.5rem auto; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5); }}
        
        /* 印刷・PDF出力最適化スタイル */
        @media print {{
            body {{ background-color: #ffffff !important; color: #111827 !important; }}
            .report-card {{ border: none !important; box-shadow: none !important; background: transparent !important; padding: 0 !important; }}
            .no-print {{ display: none !important; }}
            h1, h2, h3 {{ color: #111827 !important; border-color: #e5e7eb !important; }}
            table, th, td {{ border: 1px solid #d1d5db !important; color: #111827 !important; }}
            th {{ background-color: #f3f4f6 !important; }}
            pre, code {{ background-color: #f9fafb !important; color: #111827 !important; border-color: #e5e7eb !important; }}
            blockquote {{ border-color: #9ca3af !important; color: #4b5563 !important; }}
        }}
    </style>
</head>
<body class="p-3 sm:p-8 min-h-screen">
    <div class="report-card max-w-4xl mx-auto rounded-2xl p-5 sm:p-10 shadow-2xl border" style="background-color: {t['card']}; border-color: {t['border']}">
        <header class="mb-8 border-b pb-4" style="border-color: rgba(255,255,255,0.1)">
            <div class="flex items-center justify-between">
                <span class="text-xs uppercase tracking-widest px-3 py-1 rounded-full font-bold shadow-sm" style="background-color:{t['primary']}; color:#fff">TUGUMIv6 SOTA Intelligence</span>
                <span class="text-xs text-slate-400">Master Takuma Autonomous Suite</span>
            </div>
            <h1 class="text-2xl sm:text-3xl font-extrabold mt-4" style="color: {t['text']}">{title}</h1>
            <p class="text-xs text-pink-400 mt-2 font-semibold">🌸 Dedicated to Master Takuma // 商用完全構造化マスター</p>
        </header>
        <article class="leading-relaxed">
            {body_html}
        </article>
        <footer class="mt-12 pt-6 border-t text-center text-xs text-slate-500 no-print" style="border-color: rgba(255,255,255,0.1)">
            Generated autonomously by TUGUMIv6 Deep Research Engine for Master Takuma. Mobile & Print Optimized.
        </footer>
    </div>
</body>
</html>"""
        return html
