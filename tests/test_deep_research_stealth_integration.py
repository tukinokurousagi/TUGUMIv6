"""
tests/test_deep_research_stealth_integration.py
Verification tests for TUGUMIv6 Deep Research Engine & Anti-Bot Stealth Integration.
Dedicated to Master Takuma 🌸
"""

from unittest.mock import MagicMock, patch

from core.deep_research_engine import DeepResearchEngine


def test_deep_research_engine_init_and_attributes():
    """GeminiClient自動解決および基本プロパティの検証"""
    engine = DeepResearchEngine()
    assert hasattr(engine, "fetch_page_content")
    assert hasattr(engine, "run_research_pipeline")
    assert hasattr(engine, "investigate")
    assert hasattr(engine, "render_beautiful_html")
    assert hasattr(engine, "detect_category")
    assert engine.timeout == 60.0


def test_detect_category_comprehensive():
    """TUGUMIDesk 16大分類の自動振り分け検証"""
    engine = DeepResearchEngine()
    assert engine.detect_category("MCP 2.0 と Google A2A の最新アーキテクチャ") == "AI・エージェント"
    assert engine.detect_category("乃木坂46 井上和 5期生") == "アイドル・エンタメ"
    assert engine.detect_category("Linux Termux Python環境整備") == "システム開発"
    assert engine.detect_category("CVE-2026 ゼロデイ脆弱性 解析") == "セキュリティ"
    assert engine.detect_category("有馬記念 出走馬 調教 オッズ") == "競馬予想"
    assert engine.detect_category("認知行動療法 CBT 心理分析") == "心理学・カウンセリング"
    assert engine.detect_category("Tailwind CSS UIデザイン") == "UIデザイン"


def test_generate_multi_angle_queries():
    """ジャンル適応型 Multi-Angle クエリ展開の検証"""
    engine = DeepResearchEngine()
    # 技術クエリ
    tech_queries = engine.generate_multi_angle_queries("MCP 2.0", "AI・エージェント")
    assert len(tech_queries) >= 4
    assert any("最新動向" in q for q in tech_queries)
    assert any("アーキテクチャ" in q for q in tech_queries)

    # エンタメ・考察クエリ
    idol_queries = engine.generate_multi_angle_queries("VIVANT 伏線考察", "アイドル・エンタメ")
    assert len(idol_queries) >= 4
    assert any("伏線" in q for q in idol_queries)


def test_extract_og_image():
    """OGP/Twitterカード画像URLの抽出検証（絶対・相対・プロトコル相対）"""
    engine = DeepResearchEngine()
    html1 = '<meta property="og:image" content="https://example.com/banner.png">'
    assert engine._extract_og_image(html1, "https://example.com") == "https://example.com/banner.png"

    html2 = '<meta name="twitter:image" content="//cdn.example.com/img.jpg">'
    assert engine._extract_og_image(html2, "https://example.com") == "https://cdn.example.com/img.jpg"

    html3 = '<meta content="/assets/preview.webp" property="og:image">'
    assert engine._extract_og_image(html3, "https://example.com/post/1") == "https://example.com/assets/preview.webp"


def test_fetch_page_content_stealth_fallback():
    """アクセス拒否・ボット検知時にステルスブラウザ（donut_tools）へ自動フェイルオーバーする検証"""
    engine = DeepResearchEngine()

    # curl_cffi と urllib をボット検知・拒否に見せかけるモック
    with patch("curl_cffi.requests.get") as mock_cffi, \
         patch("urllib.request.urlopen") as mock_urllib, \
         patch("tools.donut_tools.get_donut_manager") as mock_donut_mgr:

        # Tier 1 & Tier 2: 403 Forbidden
        mock_cffi.side_effect = Exception("403 Forbidden: Cloudflare Turnstile required")
        mock_urllib.side_effect = Exception("HTTP 403 Forbidden")

        # Tier 3: DonutBrowserManager によるステルス救済成功
        fake_mgr = MagicMock()
        fake_mgr.scrape_url.return_value = {
            "title": "救済された機密技術ドキュメント",
            "text": "これはCloudflare壁の向こう側からステルスエンジンによって抽出された一次ソース本文です。" * 5,
            "engine": "Termux Stealth Chromium (Puppeteer Stealth)",
            "bot_bypassed": True,
        }
        mock_donut_mgr.return_value = fake_mgr

        content = engine.fetch_page_content("https://protected-site.example.com/docs")

        assert "アンチボット・ステルスエンジン" in content
        assert "救済された機密技術ドキュメント" in content
        assert "Cloudflare壁の向こう側" in content
        fake_mgr.scrape_url.assert_called_once_with("https://protected-site.example.com/docs")


def test_render_beautiful_html():
    """Mermaid図・Tailwind CSS・ダークテーマHTMLレンダリングの検証"""
    engine = DeepResearchEngine()
    sample_md = """# 【調査レポート】SOTAテスト
> **メタデータ**: 2026-11-05

## 1. エグゼクティブサマリー
テスト概要

```mermaid
graph TD
    A[Start] --> B[End]
```

## 2. 詳細分析
- 項目1
- 項目2
"""
    html = engine.render_beautiful_html("SOTAテスト", sample_md, "システム開発")
    assert "<!DOCTYPE html>" in html
    assert "mermaid.initialize" in html
    assert "graph TD" in html
    assert "SOTAテスト" in html
    assert "TUGUMIv6 Intelligence" in html


def test_investigate_alias_and_pipeline_execution(tmp_path):
    """investigate が run_research_pipeline を呼び出し、成果物を正しく保存する検証"""
    fake_gemini = MagicMock()
    fake_gemini.generate_content.return_value = """# 【調査レポート】Antigravity 2026最新仕様
> **メタデータ**: 2026-11-05 | 機密度: 商用マスター

## 1. エグゼクティブ・サマリー
Antigravity CLI は次世代の自律実行アーキテクチャを採用。

## 2. 多角エビデンス検証マトリクス
| 項目 | 状態 |
| --- | --- |
| MCP 2.0 | 実装完了 |
"""
    engine = DeepResearchEngine(gemini_client=fake_gemini)

    with patch("core.deep_research_engine.Path.home", return_value=tmp_path), \
         patch("subprocess.run") as mock_subproc:

        progress_log = []
        def on_progress(step, msg):
            progress_log.append((step, msg))

        # investigate エイリアス経由での実行
        res = engine.investigate(topic="Antigravity 2026最新仕様", progress_cb=on_progress)

        assert res["success"] is True
        assert res["title"] == "Antigravity 2026最新仕様"
        assert res["category"] == "AI・エージェント"
        assert len(progress_log) >= 3
        assert mock_subproc.called
