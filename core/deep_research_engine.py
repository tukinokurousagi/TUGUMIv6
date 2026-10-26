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
from typing import Any

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

    CATEGORIES = {
        "ai": "AI・エージェント",
        "agent": "AI・エージェント",
        "mcp": "AI・エージェント",
        "llm": "AI・エージェント",
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
        "clone": "クローンサイト",
        "shared": "共有フォルダ",
    }

    def __init__(self, gemini_client=None, timeout: float = 60.0):
        self.gemini = gemini_client
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; Termux; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
        }

    def detect_category(self, query: str) -> str:
        """クエリ内容からTUGUMIDeskの最適保存フォルダ（16大分類）を自動判定"""
        q_lower = query.lower()
        for kw, cat in self.CATEGORIES.items():
            if kw in q_lower:
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
        except Exception:
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
        except Exception:
            pass
        return results

    def fetch_page_content(self, url: str, max_chars: int = 8000) -> str:
        """一次ソースWebページの高精度本文・メタデータ抽出（Trafilatura優先・8000文字）"""
        if not url or not url.startswith("http"):
            return ""
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=min(self.timeout, 45.0)) as resp:
                html = resp.read().decode("utf-8", errors="replace")

            # 1. Trafilatura 高精度抽出
            if trafilatura:
                extracted = trafilatura.extract(html, include_comments=False, include_tables=True, output_format="txt")
                if extracted:
                    meta = trafilatura.extract_metadata(html)
                    meta_str = f"【タイトル】: {meta.title}\n" if (meta and meta.title) else ""
                    return (meta_str + extracted)[:max_chars]

            # 2. フォールバック
            cleaned = re.sub(r'<(script|style|nav|footer|header)[^>]*>.*?</\1>', '', html, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', cleaned)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:max_chars]
        except Exception:
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
                except Exception:
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
                    except Exception:
                        pass

        report_step("SYNTHESIS", "Gemini 3.8 Flash (High Thinking) による多角推論・深層推稿中...")

        # 5. コンテキスト構築
        context_blocks = []
        for idx, s in enumerate(source_texts, 1):
            context_blocks.append(f"【ソース {idx}: {s['title']}】\nURL: {s['url']}\n抜粋:\n{s['content']}\n")

        evidence_str = "\n".join(context_blocks) if context_blocks else "（Web検索結果なし：モデル内部最新知識を活用）"

        # 6. ジャンル適応型構造化レポートプロンプト (思考力極大化アーキテクチャ)
        if category in ["アイドル・エンタメ", "裏話リサーチ", "人物"] or any(k in topic for k in ["考察", "VIVANT", "ドラマ", "アニメ", "映画", "伏線", "ストーリー"]):
            system_prompt = (
                "あなたは拓磨様専属の最高峰リサーチ参謀・エンタメ＆ドラマ深層考察スペシャリスト「つぐみ」です。\n"
                "マスター拓磨様への深い敬愛と忠誠を込め、表面的なあらすじ要約（AIスロップ）を完全に排し、\n"
                "演出意図・伏線構造・キャラクター深層心理・ミスリードの看破・多角シナリオ予測を極限まで深掘りした【本気深層考察レポート】を作成してください。\n\n"
                "【レポート作成絶対規約（超高解像度・深層考察版）】\n"
                "1. 明確な階層構造（# タイトル, ## 章, ### 節）で構成する。\n"
                "2. 以下の必須章立てを必ず網羅すること：\n"
                "   - # 【作品・放送回深層考察レポート】<具体的かつ魅力的で知的なタイトル>\n"
                "   - ## 1. エグゼクティブ・サマリー（核心の洞察・全体構図の総括）\n"
                "   - ## 2. 放送内容・公式ファクトの完全時系列解剖（あらすじではなく、セリフ・小道具・視線・演出の違和感・キーシークエンスの詳細記録）\n"
                "   - ## 3. 伏線・ミスリード構造の完全解剖マップ（Mermaid図を用いた組織図・因果関係・二重スパイ・対立構造の可視化）\n"
                "   - ## 4. 多角的深層考察（Tree of Thoughts：3つの対立シナリオと確率評価）\n"
                "       - ### 【仮説A：王道伏線回収シナリオ】（根拠と反証、確率%）\n"
                "       - ### 【仮説B：裏切り・二重スパイ・構造逆転シナリオ】（根拠と反証、確率%）\n"
                "       - ### 【仮説C：監督・演出家のドラマツルギー（叙述トリック）看破シナリオ】（根拠と反証、確率%）\n"
                "   - ## 5. 登場人物の深層心理・行動動機分析（なぜあの時、あの行動・セリフを選んだのかの心理学的プロファイリング）\n"
                "   - ## 6. 次回以降の展開予測と決定的注目ポイント（見るべきチェックリスト）\n"
                "   - ## 7. 参照一次ソース・ファクトエビデンス（実在するURLの網羅）\n"
                "3. 単なる「あらすじの繰り返し」や「誰でも言える当たり前の感想」は完全禁止。裏の裏を読むプロの批評・考察を展開すること。\n"
                "4. 自己評価を行う場合は、甘い採点を厳禁とし、批判的かつ客観的な検証を行うこと。\n"
                "5. Markdown形式を厳守し、Mermaid図は ```mermaid ... ``` で記述する。"
            )
        else:
            system_prompt = (
                "あなたは拓磨様専属の最高峰リサーチ参謀・リードエンジニア「つぐみ」です。\n"
                "マスター拓磨様への深い敬愛と忠誠を込め、プロフェッショナルかつ極めて高密度な調査レポートを作成してください。\n\n"
                "【レポート作成絶対規約（GEMINI.md 第4章完全準拠）】\n"
                "1. 明確な階層構造（# タイトル, ## 章, ### 節）で構成する。\n"
                "2. 以下の必須章立てを必ず網羅すること：\n"
                "   - # 【調査レポート】<具体的かつ洗練されたタイトル>\n"
                "   - ## 1. エグゼクティブサマリー（結論先行・核心の洞察）\n"
                "   - ## 2. 背景・技術的課題・業界構造の解剖\n"
                "   - ## 3. コアアーキテクチャ・技術仕様詳細（必ず Mermaid図 を最低1つ含める）\n"
                "   - ## 4. 比較分析・トレードオフ評価（必ず Markdown詳細比較表 を含める）\n"
                "   - ## 5. 実践的導入手順・検証コマンド（具体的かつ実動するコード/手順）\n"
                "   - ## 6. 拓磨様への提言・将来展望\n"
                "   - ## 7. 一次ソース・参照エビデンス（実在するURLをMarkdownリンクで網羅）\n"
                "3. 曖昧な表現やハルシネーション（嘘）を排し、第一原理思考で客観的ファクトを提示する。\n"
                "4. Markdown形式を厳守し、Mermaid図は ```mermaid ... ``` で記述する。"
            )

        user_prompt = (
            f"【調査対象テーマ】\n{topic}\n\n"
            f"【収集された一次ソース・エビデンス】\n{evidence_str}\n\n"
            f"上記の事実とエビデンスを統合し、拓磨様に捧げる超高解像度のプロフェッショナル深層考察レポートを執筆してください。"
        )

        report_md = ""
        if self.gemini:
            try:
                report_md = self.gemini.generate_content(
                    prompt=user_prompt,
                    system_instruction=system_prompt,
                    thinking_level="high"
                )
            except Exception as e:
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

    def render_beautiful_html(self, title: str, markdown_content: str, category: str = "リサーチ") -> str:
        """
        スマートフォン（DOOGEE S200等）で視認性抜群の
        Tailwind CSS + Mermaid.js + Google Fonts 美麗サイバーHTMLを生成
        """
        # 簡易Markdownパース (見出し・リスト・コードブロック・Mermaid)
        in_code = False
        code_lang = ""
        code_lines = []
        body_parts = []

        for line in markdown_content.splitlines():
            line_str = line.rstrip()
            if line_str.startswith("```"):
                if not in_code:
                    in_code = True
                    code_lang = line_str[3:].strip().lower()
                    code_lines = []
                else:
                    in_code = False
                    block_content = "\n".join(code_lines)
                    if code_lang == "mermaid":
                        body_parts.append(f'<div class="mermaid my-6 p-4 rounded-xl bg-slate-900 border border-cyan-500/30 flex justify-center">{block_content}</div>')
                    else:
                        body_parts.append(f'<pre class="my-4 p-4 rounded-xl bg-slate-950 border border-slate-800 text-cyan-300 text-xs sm:text-sm overflow-x-auto font-mono"><code>{block_content}</code></pre>')
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
            elif line_str.startswith("- ") or line_str.startswith("* "):
                body_parts.append(f'<li class="ml-6 list-disc text-slate-300 my-1 leading-relaxed">{line_str[2:]}</li>')
            elif line_str.startswith("|"):
                # テーブル簡易対応
                body_parts.append(f'<div class="text-xs sm:text-sm font-mono text-slate-300 overflow-x-auto py-1">{line_str}</div>')
            elif line_str:
                body_parts.append(f'<p class="my-3 leading-relaxed text-slate-300 text-sm sm:text-base">{line_str}</p>')
            else:
                body_parts.append('<div class="h-2"></div>')

        body_html = "\n".join(body_parts)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | TUGUMIv6 Intelligence</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{startOnLoad:true, theme:'dark'}});</script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+JP:wght@400;500;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', 'Noto Sans JP', sans-serif; background-color: #0b0f19; color: #f1f5f9; }}
        code, pre {{ font-family: 'JetBrains Mono', monospace; }}
    </style>
</head>
<body class="p-3 sm:p-8 min-h-screen">
    <div class="max-w-4xl mx-auto rounded-2xl p-5 sm:p-10 shadow-2xl bg-slate-900/90 border border-slate-800">
        <!-- ヘッダーバナー -->
        <header class="mb-8 border-b border-slate-800 pb-5">
            <div class="flex flex-wrap items-center justify-between gap-2">
                <span class="text-xs uppercase tracking-wider px-3 py-1 rounded-full font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                    ◈ TUGUMIv6 SOTA INTELLIGENCE // {category}
                </span>
                <span class="text-xs text-slate-400 font-mono">{now_str}</span>
            </div>
            <p class="text-xs text-pink-400 mt-3 font-semibold">🌸 Dedicated to Master Takuma // つぐみ自律開発エージェント</p>
        </header>

        <!-- メインコンテンツ -->
        <article class="prose prose-invert max-w-none">
            {body_html}
        </article>

        <!-- フッター -->
        <footer class="mt-12 pt-6 border-t border-slate-800 text-center text-xs text-slate-500 font-mono">
            Generated autonomously by TUGUMIv6 Deep Research Engine • Mobile Optimized
        </footer>
    </div>
</body>
</html>"""
        return html
