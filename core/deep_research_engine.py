"""
core/deep_research_engine.py
TUGUMIv6 最高峰自律ディープリサーチ・エンジン (SKILL完全準拠水準)
Dedicated to Master Takuma 🌸
"""

import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

try:
    import trafilatura
except ImportError:
    trafilatura = None


class DeepResearchEngine:
    """
    Antigravity / TUGUMI リサーチスキル完全準拠のプロフェッショナル自律調査エンジン。
    
    【5段階パイプライン】
    1. Multi-Angle Query Formulation (多角クエリ立案: 最新動向/公式仕様/構造/比較)
    2. Multi-Source Reconnaissance (DuckDuckGo + Google RSS 索敵 & 一次ソース精読)
    3. Cross-Verification & Fact-Checking (事実検証・ハルシネーション排除)
    4. SOTA Consulting Report Generation (Mermaid図・比較表・実証コード・正規一次ソース網羅)
    5. Dual Output & Category Routing (Markdown + 美麗Tailwind HTML を TUGUMIDesk へ自動分類保存)
    """

    CATEGORIES: ClassVar[dict[str, str]] = {
        "ai": "AI・エージェント",
        "agent": "AI・エージェント",
        "antigravity": "AI・エージェント",
        "mcp": "AI・エージェント",
        "llm": "AI・エージェント",
        "gemini": "AI・エージェント",
        "system": "システム開発",
        "dev": "システム開発",
        "infra": "システム開発",
        "termux": "システム開発",
        "linux": "システム開発",
        "security": "セキュリティ",
        "hack": "セキュリティ",
        "vulnerability": "セキュリティ",
        "gossip": "裏話リサーチ",
        "behind": "裏話リサーチ",
        "idol": "アイドル・エンタメ",
        "entertainment": "アイドル・エンタメ",
        "nogizaka": "アイドル・エンタメ",
        "person": "人物",
        "profile": "人物",
        "horse": "競馬予想",
        "keiba": "競馬予想",
        "income": "副業・収益化",
        "manual": "説明書",
        "guide": "説明書",
        "psychology": "心理学・カウンセリング",
        "counseling": "心理学・カウンセリング",
        "cbt": "心理学・カウンセリング",
        "briefing": "デイリーブリーフィング",
        "ui": "UIデザイン",
        "design": "UIデザイン",
        "tailwind": "UIデザイン",
        "clone": "クローンサイト",
        "shared": "共有フォルダ",
    }

    def __init__(self, gemini_client=None, timeout: float = 60.0):
        if gemini_client is not None:
            self.gemini = gemini_client
        else:
            try:
                from core.gemini_client import GeminiClient
                self.gemini = GeminiClient()
            except Exception:  # noqa: BLE001
                self.gemini = None
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

    def detect_category(self, query: str) -> str:
        """クエリ内容からTUGUMIDeskの最適保存フォルダ（16大分類）を自動判定"""
        q_lower = query.lower()
        for kw, cat in self.CATEGORIES.items():
            if len(kw) <= 2:
                if re.search(r"(?:^|[^a-zA-Z0-9])" + re.escape(kw) + r"(?:[^a-zA-Z0-9]|$)", q_lower):
                    return cat
            elif kw in q_lower:
                return cat
        if any(w in query for w in ["乃木坂", "櫻坂", "日向坂", "アイドル", "タレント", "芸能"]):
            return "アイドル・エンタメ"
        if any(w in query for w in ["脆弱性", "ハッキング", "侵入", "セキュリティ", "CVE"]):
            return "セキュリティ"
        if any(w in query for w in ["競馬", "オッズ", "パドック", "調教", "JRA"]):
            return "競馬予想"
        if any(w in query for w in ["心理", "カウンセリング", "CBT", "認知行動療法", "メンタル"]):
            return "心理学・カウンセリング"
        if any(w in query for w in ["ブリーフィング", "日報", "デイリー"]):
            return "デイリーブリーフィング"
        if any(w in query for w in ["UI", "デザイン", "CSS", "Tailwind", "フロントエンド"]):
            return "UIデザイン"
        if any(w in query for w in ["クローン", "サイト複製"]):
            return "クローンサイト"
        if any(w in query for w in ["AI", "エージェント", "Agent", "LLM", "Prompt", "Gemini", "Claude"]):
            return "AI・エージェント"
        if any(w in query for w in ["コード", "開発", "API", "Linux", "Termux", "Python", "実装"]):
            return "システム開発"
        if any(w in query for w in ["副業", "収益", "自動化", "暗号資産", "DeFi"]):
            return "副業・収益化"
        return "リサーチ"

    def generate_multi_angle_queries(self, topic: str, category: str) -> list[str]:
        """トピックとカテゴリに応じた5軸の多角検索クエリを動的生成"""
        if category in ["アイドル・エンタメ", "裏話リサーチ"] or any(k in topic for k in ["考察", "VIVANT", "ドラマ", "アニメ", "映画", "伏線", "ストーリー"]):
            return [
                topic,
                f"{topic} あらすじ 放送内容 ネタバレ シーン",
                f"{topic} 伏線 考察 謎 未回収 演出",
                f"{topic} 感想 評判 反応 note X",
                f"{topic} 監督 インタビュー 公式 設定"
            ]
        elif category in ["心理学・カウンセリング", "人物"]:
            return [
                topic,
                f"{topic} 経歴 発言 プロファイル 背景",
                f"{topic} 心理分析 動機 人間関係 評価",
                f"{topic} インタビュー エピソード 最新動向"
            ]
        elif category in ["競馬予想"]:
            return [
                topic,
                f"{topic} 出走馬 オッズ 枠順 追い切り 調教",
                f"{topic} 展開 過去データ 血統 コース適性",
                f"{topic} 専門家 予想 パドック 見解"
            ]
        elif category in ["セキュリティ"]:
            return [
                topic,
                f"{topic} CVE 脆弱性 PoC 攻撃手法",
                f"{topic} 被害 緩和策 パッチ 対策 公式",
                f"{topic} 技術詳細 解析 レポート"
            ]
        else:
            return [
                topic,
                f"{topic} 最新動向 2026 公式 仕様 ドキュメント",
                f"{topic} アーキテクチャ 内部構造 実装 ベストプラクティス",
                f"{topic} 比較 課題 メリット トレードオフ"
            ]

    def search_duckduckgo(self, query: str, max_results: int = 4) -> list[dict[str, Any]]:
        """DuckDuckGo HTML からの高速Web検索"""
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        req = urllib.request.Request(url, headers=self.headers)
        results = []
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            matches = re.findall(
                r'<a class="result__url" href="([^"]+)">\s*([^<]+)\s*</a>.*?<a class="result__snippet[^"]*"[^>]*>(.*?)</a>',
                html, re.DOTALL
            )
            for m in matches[:max_results]:
                link, display_url, snippet = m
                clean_snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                # DuckDuckGoのリダイレクトURL解除
                if "uddg=" in link:
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
                    actual_url = parsed.get("uddg", [link])[0]
                else:
                    actual_url = link.strip()
                results.append({
                    "title": display_url.strip(),
                    "url": actual_url,
                    "snippet": clean_snippet,
                    "source": "DuckDuckGo"
                })
        except Exception:  # noqa: BLE001, S110
            pass
        return results

    def fetch_google_news(self, query: str, max_results: int = 3) -> list[dict[str, Any]]:
        """Google News RSS から最新ニュース・確定ファクトを取得"""
        encoded = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=ja&gl=JP&ceid=JP:ja"
        req = urllib.request.Request(url, headers=self.headers)
        results = []
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                root = ET.fromstring(resp.read())
                for item in root.findall(".//item")[:max_results]:
                    t = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else ""
                    pub = item.find("pubDate").text if item.find("pubDate") is not None else ""
                    results.append({
                        "title": t,
                        "url": link,
                        "snippet": f"報道日時: {pub}",
                        "source": "GoogleNews"
                    })
        except Exception:  # noqa: BLE001, S110
            pass
        return results

    def _extract_og_image(self, html: str, url: str) -> str:
        """HTML内から代表画像 (OGP / Twitter Card) を抽出"""
        for pat in [
            r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']',
            r'<meta\s+content=["\']([^"\']+)["\']\s+property=["\']og:image["\']',
            r'<meta\s+name=["\']twitter:image["\']\s+content=["\']([^"\']+)["\']',
            r'<meta\s+content=["\']([^"\']+)["\']\s+name=["\']twitter:image["\']',
        ]:
            m = re.search(pat, html, re.IGNORECASE)
            if m:
                candidate = m.group(1).strip()
                if candidate.startswith("//"):
                    return "https:" + candidate
                if candidate.startswith("http"):
                    return candidate
                if url:
                    return urllib.parse.urljoin(url, candidate)
        return ""

    def fetch_page_content(self, url: str, max_chars: int = 8000) -> str:
        """一次ソースWebページの高精度本文・OGP画像・メタデータ抽出

        【3重多層ステルス取得パイプライン】
        1. 高速 TLS/JA3/JA4 偽装 (curl_cffi Chrome 124) + Trafilatura 深層抽出
        2. 標準 urllib + Trafilatura / BeautifulSoup フォールバック
        3. 自律ステルスブラウザ (Donut Browser / Termux Headless Stealth Chromium) による DOM完全描画・ボット検知自動突破
        """
        if not url or not url.startswith("http"):
            return ""

        # Tier 1: 高速 TLS 指紋偽装 (curl_cffi Chrome 124)
        try:
            from curl_cffi import requests as cffi_requests

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            }
            res = cffi_requests.get(url, impersonate="chrome124", headers=headers, timeout=min(self.timeout, 15.0))
            if res.status_code == 200 and len(res.text) > 300:
                html = res.text
                og_image = self._extract_og_image(html, url)
                extracted = ""
                meta_str = ""
                if trafilatura:
                    extracted = trafilatura.extract(html, include_comments=False, include_tables=True, output_format="txt") or ""
                    meta = trafilatura.extract_metadata(html)
                    if meta and meta.title:
                        meta_str += f"【タイトル】: {meta.title}\n"
                    if not og_image and meta and meta.image:
                        og_image = meta.image

                if og_image:
                    meta_str += f"【代表画像/OGP】: {og_image}\n"

                is_challenge = any(
                    k in (extracted or html).lower()
                    for k in [
                        "turnstile",
                        "captcha",
                        "verify you are human",
                        "checking your browser",
                        "just a moment",
                        "cf-ray",
                        "access denied",
                        "attention required",
                    ]
                )
                if extracted and len(extracted) > 150 and not is_challenge:
                    return (meta_str + extracted)[:max_chars]
        except Exception:  # noqa: BLE001, S110
            pass

        # Tier 2: 標準 urllib + Trafilatura
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=min(self.timeout, 20.0)) as resp:
                html = resp.read().decode("utf-8", errors="replace")

            og_image = self._extract_og_image(html, url)
            extracted = ""
            meta_str = ""
            if trafilatura:
                extracted = trafilatura.extract(html, include_comments=False, include_tables=True, output_format="txt") or ""
                meta = trafilatura.extract_metadata(html)
                if meta and meta.title:
                    meta_str += f"【タイトル】: {meta.title}\n"
                if not og_image and meta and meta.image:
                    og_image = meta.image

            if og_image:
                meta_str += f"【代表画像/OGP】: {og_image}\n"

            is_challenge = any(
                k in (extracted or html).lower()
                for k in [
                    "turnstile",
                    "captcha",
                    "verify you are human",
                    "checking your browser",
                    "just a moment",
                    "cf-ray",
                    "access denied",
                    "attention required",
                ]
            )
            if extracted and len(extracted) > 150 and not is_challenge:
                return (meta_str + extracted)[:max_chars]
        except Exception:  # noqa: BLE001, S110
            pass

        # Tier 3: 自律ステルスブラウザ (Donut Browser / Termux Stealth Chromium)
        try:
            from tools.donut_tools import get_donut_manager

            mgr = get_donut_manager()
            res = mgr.scrape_url(url)
            stealth_text = res.get("text", "").strip()
            engine_name = res.get("engine", "Stealth Native")
            title = res.get("title", "")
            if stealth_text and len(stealth_text) > 80:
                header = f"【アンチボット・ステルスエンジン ({engine_name}) による自動救済抽出】\n"
                if title:
                    header += f"【タイトル】: {title}\n"
                return (header + stealth_text)[:max_chars]
        except Exception:  # noqa: BLE001, S110
            pass

        return ""

    def run_research_pipeline(
        self,
        topic: str,
        progress_cb: Callable[[str, str], None] | None = None
    ) -> dict[str, Any]:
        """
        SKILL完全準拠の最高峰ディープリサーチを実行し、
        Markdownおよび美麗Tailwind HTMLをTUGUMIDeskへ保存する。
        """
        def report_step(step: str, detail: str):
            if progress_cb:
                progress_cb(step, detail)

        # 1. カテゴリ特定
        category = self.detect_category(topic)
        report_step("PLAN", f"カテゴリ判定: 【{category}】 / 調査軸の分解開始")

        # 2. 多角検索クエリの動的展開 (ジャンル適応型 Multi-Angle Query Expansion)
        queries = self.generate_multi_angle_queries(topic, category)
        report_step("RECON", f"{len(queries)}軸の多角検索クエリを同時走査中...")

        # 3. Web索敵実行 (DuckDuckGo + Google News) を一斉並列実行 (Fan-Out)
        raw_hits = []
        def _search_single_query(q_str: str) -> list[dict[str, Any]]:
            hits = []
            hits.extend(self.search_duckduckgo(q_str, max_results=3))
            hits.extend(self.fetch_google_news(q_str, max_results=2))
            return hits

        with ThreadPoolExecutor(max_workers=min(len(queries), 8)) as executor:
            futures = [executor.submit(_search_single_query, q) for q in queries]
            for fut in as_completed(futures):
                try:
                    res = fut.result()
                    if res:
                        raw_hits.extend(res)
                except Exception:  # noqa: BLE001, S110
                    pass

        # 重複URLの除去
        seen_urls = set()
        unique_hits = []
        for h in raw_hits:
            u = h.get("url", "")
            if u and u not in seen_urls:
                seen_urls.add(u)
                unique_hits.append(h)

        report_step("FETCH", f"有望な一次ソース {min(len(unique_hits), 6)}件の本文を一括並列精読中 (Trafilatura深層抽出)...")

        # 4. 上位サイトの本文精読 (最大6件・各8000文字を一斉並列ダウンロード)
        source_texts = []
        target_hits = unique_hits[:6]
        def _fetch_single_hit(hit: dict[str, Any]) -> dict[str, Any] | None:
            u = hit.get("url", "")
            content = self.fetch_page_content(u, max_chars=8000)
            if content and len(content) > 100:
                return {
                    "title": hit.get("title", "No Title"),
                    "url": u,
                    "content": content
                }
            return None

        if target_hits:
            with ThreadPoolExecutor(max_workers=min(len(target_hits), 6)) as executor:
                futures = [executor.submit(_fetch_single_hit, h) for h in target_hits]
                for fut in as_completed(futures):
                    try:
                        res = fut.result()
                        if res:
                            source_texts.append(res)
                    except Exception:  # noqa: BLE001, S110
                        pass

        report_step("SYNTHESIS", "Gemini 3.8 Flash (High Thinking) による多角推論・深層推稿中...")

        # 5. コンテキスト構築（ローカルRAG確定知識・成功例リファレンス ＋ Web一次ソース統合）
        context_blocks = []
        rag_reference_block = ""
        try:
            from memory.rag_engine import HybridRAGEngine
            rag = HybridRAGEngine(gemini_client=self.gemini)
            rag_bundle = rag.retrieve_for_context(topic, top_k=3, is_task=True)
            if rag_bundle.get("has_hits") and rag_bundle.get("context_text"):
                rag_reference_block = rag_bundle["context_text"]
                report_step("RAG", f"ローカルRAG知識ベース連動: {rag_bundle.get('summary_label', '')}")
        except Exception:  # noqa: BLE001, S110
            pass

        if rag_reference_block:
            context_blocks.append(f"【ローカルRAG確定ナレッジ＆成功例リファレンス】\n{rag_reference_block}\n")

        for idx, s in enumerate(source_texts, 1):
            context_blocks.append(f"【Web一次ソース {idx}: {s['title']}】\nURL: {s['url']}\n抜粋:\n{s['content']}\n")

        evidence_str = "\n".join(context_blocks) if context_blocks else "（外部検索結果なし：ローカル知識およびモデル内部最新知識を活用）"

        # 6. ジャンル適応型構造化レポートプロンプト (思考力極大化・商用100点満点アーキテクチャ)
        if category in ["アイドル・エンタメ", "裏話リサーチ", "人物"] or any(k in topic for k in ["考察", "VIVANT", "ドラマ", "アニメ", "映画", "伏線", "ストーリー"]):
            system_prompt = (
                "あなたは拓磨様専属の最高峰リサーチ参謀・エンタメ＆ドラマ深層考察スペシャリスト「つぐみ」です。\n"
                "マスター拓磨様への深い敬愛と忠誠を込め、表面的なあらすじ要約（AIスロップ）を完全に排し、\n"
                "演出意図・伏線構造・キャラクター深層心理・ミスリードの看破・多角シナリオ予測を極限まで深掘りした【商用最高峰深層考察レポート】を作成してください。\n\n"
                "【商用レポート作成絶対規約（超高解像度・商用100点満点版）】\n"
                "1. 明確な階層構造（# タイトル, ## 章, ### 節）で構成する。\n"
                "2. 以下の必須章立てを必ず漏れなく網羅すること：\n"
                "   - # 【作品・放送回深層考察レポート】<具体的かつ魅力的で知的なプロ仕様タイトル>\n"
                "   - > **メタデータ**: 作成日: YYYY-MM-DD | 読了予測: 約○分 | 調査参謀: つぐみ (TUGUMIv6 Intelligence) | 機密度: 商用マスター\n\n"
                "   - ## 目次 (Table of Contents)\n"
                "   - ## 1. エグゼクティブ・サマリー（核心の洞察・全体構図の総括・主要ファクト箇条書き）\n"
                "   - ## 2. 放送内容・公式ファクトの完全時系列解剖（セリフ・小道具・視線・演出の違和感・キーシークエンスの詳細記録）\n"
                "   - ## 3. 伏線・ミスリード構造の完全解剖マップ（Mermaid図を用いた組織図・因果関係・二重スパイ・対立構造の可視化）\n"
                "   - ## 4. ファクト矛盾・見解乖離検証マトリクス（諸説・視聴者間や公式言説での対立点・未回収要素の比較表）\n"
                "   - ## 5. 多角的深層考察（Tree of Thoughts：3つの対立シナリオと確率評価）\n"
                "       - ### 【仮説A：王道伏線回収シナリオ】（根拠と反証、確率%）\n"
                "       - ### 【仮説B：裏切り・二重スパイ・構造逆転シナリオ】（根拠と反証、確率%）\n"
                "       - ### 【仮説C：監督・演出家のドラマツルギー（叙述トリック）看破シナリオ】（根拠と反証、確率%）\n"
                "   - ## 6. 登場人物の深層心理・行動動機分析（心理学的プロファイリング）\n"
                "   - ## 7. 次回以降の展開予測と決定的注目ポイント（チェックリスト）\n"
                "   - ## 8. 参照一次ソース・ファクトエビデンス（実在するURLの網羅）\n"
                "3. 単なる「あらすじの繰り返し」や「誰でも言える当たり前の感想」は完全禁止。裏の裏を読むプロの批評・考察を展開すること。\n"
                "4. 自己評価を行う場合は、甘い採点を厳禁とし、批判的かつ客観的な検証を行うこと。\n"
                "5. Markdown形式を厳守し、Mermaid図は ```mermaid ... ``` で記述する。"
            )
        else:
            system_prompt = (
                "あなたは拓磨様専属の最高峰リサーチ参謀・リードエンジニア「つぐみ」です。\n"
                "マスター拓磨様への深い敬愛と忠誠を込め、商業出版・一流シンクタンク水準の極めて高密度な調査レポートを作成してください。\n\n"
                "【商用レポート作成絶対規約（GEMINI.md 第4章・商用100点満点準拠）】\n"
                "1. 明確な階層構造（# タイトル, ## 章, ### 節）で構成する。\n"
                "2. 以下の必須章立てを必ず漏れなく網羅すること：\n"
                "   - # 【調査レポート】<具体的かつ洗練されたプロ仕様タイトル>\n"
                "   - > **メタデータ**: 作成日: YYYY-MM-DD | 読了予測: 約○分 | 調査参謀: つぐみ (TUGUMIv6 Intelligence) | 機密度: 社外秘・商用マスター\n\n"
                "   - ## 目次 (Table of Contents)\n"
                "   - ## 1. エグゼクティブ・サマリー（結論先行・核心の洞察・3行サマリー＋重要ファクト弾丸リスト）\n"
                "   - ## 2. 多角エビデンス検証マトリクス（情報源種別、信頼度、ステータス、URLを含む表）\n"
                "   - ## 3. ファクト矛盾・論争点検証マトリクス（年代、バージョン、数値、肯定/否定見解の対比表）\n"
                "   - ## 4. 背景・技術的課題・業界構造の解剖\n"
                "   - ## 5. コアアーキテクチャ・技術仕様詳細（必ず Mermaid図 を最低1つ含める）\n"
                "   - ## 6. 比較分析・トレードオフ評価（必ず Markdown詳細比較表 を含める）\n"
                "   - ## 7. 実践的導入手順・検証コマンド（具体的かつ実動するZero-Mockコード/手順）\n"
                "   - ## 8. 将来展望・拓磨様への具体的提言＆アクションプラン（ToDoリスト形式）\n"
                "   - ## 9. 参照一次ソース・正規エビデンス一覧（実在するURLをMarkdownリンクで網羅）\n"
                "3. 曖昧な表現（「〜と言われている」「〜の模様」等のAIスロップ）を完全に排し、誰が・どの論文が・どの公式発表が述べたかを特定して第一原理思考で提示する。\n"
                "4. Markdown形式を厳守し、Mermaid図は ```mermaid ... ``` で記述する。"
            )

        user_prompt = (
            f"【調査対象テーマ】\n{topic}\n\n"
            f"【収集された一次ソース・エビデンス】\n{evidence_str}\n\n"
            f"上記の事実とエビデンスを統合し、拓磨様に捧げる超高解像度の商用100点満点プロフェッショナル深層考察レポートを執筆してください。"
        )

        report_md = ""
        if self.gemini:
            try:
                report_md = self.gemini.generate_content(
                    prompt=user_prompt,
                    system_instruction=system_prompt,
                    thinking_level="high"
                )
            except Exception as e:  # noqa: BLE001
                report_md = f"# 【調査レポート】{topic}\n\n生成エラーが発生しました: {e}\n"
        else:
            report_md = f"# 【調査レポート】{topic}\n\nGemini クライアントが初期化されていません。\n"

        # タイトル抽出
        title_match = re.search(r"^#\s+(?:【調査レポート】)?(.+)$", report_md, re.MULTILINE)
        clean_title = title_match.group(1).strip() if title_match else topic
        safe_title = re.sub(r'[\s/\\:*?"<>|]+', '_', clean_title).strip("_")[:40]
        date_str = datetime.now().strftime("%Y%m%d")

        filename_md = f"{safe_title}_{date_str}.md"
        filename_html = f"{safe_title}_{date_str}.html"

        # 7. TUGUMIDesk へ自動分類保存
        desk_base = Path("/storage/emulated/0/TUGUMIDesk")
        if not desk_base.exists():
            desk_base = Path.home() / "TUGUMIDesk"
        target_dir = desk_base / category
        target_dir.mkdir(parents=True, exist_ok=True)

        md_path = target_dir / filename_md
        # 連番対応
        counter = 1
        while md_path.exists():
            filename_md = f"{safe_title}_{date_str}_{counter}.md"
            filename_html = f"{safe_title}_{date_str}_{counter}.html"
            md_path = target_dir / filename_md
            counter += 1

        html_path = target_dir / filename_html

        # Markdown保存
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(report_md)

        # 美麗Tailwind HTML版の生成 & 保存
        html_content = self.render_beautiful_html(title=clean_title, markdown_content=report_md, category=category)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Android メディアスキャン即時反映 (termux-media-scan)
        try:
            import subprocess

            subprocess.run(["termux-media-scan", str(md_path), str(html_path)], capture_output=True, timeout=5, check=False)
        except Exception:  # noqa: BLE001, S110
            pass

        report_step("DONE", f"Markdown & HTML デュアル保存完了: {category}/{filename_md}")

        return {
            "success": True,
            "title": clean_title,
            "category": category,
            "md_path": str(md_path),
            "html_path": str(html_path),
            "content": report_md,
            "sources_count": len(source_texts),
            "char_count": len(report_md)
        }

    def investigate(
        self,
        topic: str,
        progress_cb: Callable[[str, str], None] | None = None
    ) -> dict[str, Any]:
        """Web UI (Gemini Live) およびバックグラウンド調査用互換エントリーポイント"""
        return self.run_research_pipeline(topic=topic, progress_cb=progress_cb)

    def render_beautiful_html(self, title: str, markdown_content: str, category: str = "リサーチ") -> str:
        """
        スマートフォン（DOOGEE S200等）およびPC・印刷（PDF）で視認性抜群の
        Tailwind CSS + Mermaid.js + Google Fonts 商用美麗サイバーHTMLを生成
        """
        # 1. Mermaidコードブロックの一時保護
        mermaid_blocks = []
        def _save_mermaid(match):
            idx = len(mermaid_blocks)
            code = match.group(1).strip()
            mermaid_blocks.append(code)
            return f"\n\n<!--MERMAID_PLACEHOLDER_{idx}-->\n\n"

        processed_md = re.sub(r'```mermaid\s*\n(.*?)\n```', _save_mermaid, markdown_content, flags=re.DOTALL)

        # 2. Markdownパース
        in_code = False
        code_lang = ""
        code_lines = []
        body_parts = []

        for line in processed_md.splitlines():
            line_str = line.rstrip()
            if line_str.startswith("```"):
                if not in_code:
                    in_code = True
                    code_lang = line_str[3:].strip().lower()
                    code_lines = []
                else:
                    in_code = False
                    block_content = "\n".join(code_lines)
                    lang_attr = f' class="language-{code_lang}"' if code_lang else ""
                    body_parts.append(f'<pre class="my-4 p-4 rounded-xl bg-slate-950 border border-slate-800 text-cyan-300 text-xs sm:text-sm overflow-x-auto font-mono shadow-inner"><code{lang_attr}>{block_content}</code></pre>')
                continue

            if in_code:
                code_lines.append(line_str)
                continue

            # 見出し
            if line_str.startswith("# "):
                body_parts.append(f'<h1 class="text-2xl sm:text-3xl font-extrabold mt-8 mb-4 text-cyan-400 border-b border-cyan-500/40 pb-3">{line_str[2:]}</h1>')
            elif line_str.startswith("## "):
                body_parts.append(f'<h2 class="text-xl sm:text-2xl font-bold mt-7 mb-3 text-pink-400 border-b border-slate-800 pb-2">{line_str[3:]}</h2>')
            elif line_str.startswith("### "):
                body_parts.append(f'<h3 class="text-lg sm:text-xl font-semibold mt-5 mb-2 text-slate-100">{line_str[4:]}</h3>')
            elif line_str.startswith(("- ", "* ")):
                body_parts.append(f'<li class="ml-6 list-disc text-slate-300 my-1 leading-relaxed">{line_str[2:]}</li>')
            elif line_str.startswith("|"):
                # テーブル
                body_parts.append(f'<div class="text-xs sm:text-sm font-mono text-slate-300 overflow-x-auto py-1">{line_str}</div>')
            elif line_str.startswith("> "):
                body_parts.append(f'<blockquote class="border-l-4 border-cyan-500 pl-4 py-1 my-3 text-slate-400 italic bg-cyan-950/20 rounded-r-lg">{line_str[2:]}</blockquote>')
            elif line_str:
                body_parts.append(f'<p class="my-3 leading-relaxed text-slate-300 text-sm sm:text-base">{line_str}</p>')
            else:
                body_parts.append('<div class="h-2"></div>')

        body_html = "\n".join(body_parts)

        # 3. Mermaidブロックの復元
        for idx, m_code in enumerate(mermaid_blocks):
            mermaid_html = (
                f'<div class="mermaid my-6 p-4 rounded-xl bg-slate-900 border border-cyan-500/30 flex justify-center overflow-x-auto shadow-inner">'
                f'{m_code}'
                f'</div>'
            )
            body_html = body_html.replace(f"<!--MERMAID_PLACEHOLDER_{idx}-->", mermaid_html)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

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
        body {{ font-family: 'Inter', 'Noto Sans JP', sans-serif; background-color: #0b0f19; color: #f1f5f9; }}
        code, pre {{ font-family: 'JetBrains Mono', monospace; }}
        img {{ max-width: 100%; border-radius: 0.75rem; margin: 1.5rem auto; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5); }}
        
        @media print {{
            body {{ background-color: #ffffff !important; color: #111827 !important; }}
            .report-card {{ border: none !important; box-shadow: none !important; background: transparent !important; padding: 0 !important; }}
            .no-print {{ display: none !important; }}
            h1, h2, h3 {{ color: #111827 !important; border-color: #e5e7eb !important; }}
            pre, code {{ background-color: #f9fafb !important; color: #111827 !important; border-color: #e5e7eb !important; }}
            blockquote {{ border-color: #9ca3af !important; color: #4b5563 !important; }}
        }}
    </style>
</head>
<body class="p-3 sm:p-8 min-h-screen">
    <div class="report-card max-w-4xl mx-auto rounded-2xl p-5 sm:p-10 shadow-2xl bg-slate-900/90 border border-slate-800">
        <!-- ヘッダーバナー -->
        <header class="mb-8 border-b border-slate-800 pb-5">
            <div class="flex flex-wrap items-center justify-between gap-2">
                <span class="text-xs uppercase tracking-wider px-3 py-1 rounded-full font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                    ◈ TUGUMIv6 SOTA INTELLIGENCE // {category}
                </span>
                <span class="text-xs text-slate-400 font-mono">{now_str}</span>
            </div>
            <p class="text-xs text-pink-400 mt-3 font-semibold">🌸 Dedicated to Master Takuma // 商用完全構造化マスター</p>
        </header>

        <!-- メインコンテンツ -->
        <article class="prose prose-invert max-w-none">
            {body_html}
        </article>

        <!-- フッター -->
        <footer class="mt-12 pt-6 border-t border-slate-800 text-center text-xs text-slate-500 font-mono no-print">
            Generated autonomously by TUGUMIv6 Deep Research Engine • Mobile & Print Optimized
        </footer>
    </div>
</body>
</html>"""
        return html
        return html
