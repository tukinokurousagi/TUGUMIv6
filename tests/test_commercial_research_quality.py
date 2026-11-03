"""
TUGUMIv6 Commercial Research Quality & Evidence Grounding Test Suite
- Fact Conflict Detection & Verification Matrix
- Commercial 100-Point Report Structuring (Meta, Exec Summary, Mermaid, Tables, Action Plan)
- Mobile & Print Optimized Beautiful HTML Rendering (@media print, Mermaid.js, Tailwind CSS)
- OGP / Key Visual Extraction
"""

import importlib.util

from tools.research_tools import ResearchTools


def test_detect_fact_conflicts_logic():
    """research_mcp の detect_fact_conflicts 相当の論理が正しく動作するか検証"""
    spec = importlib.util.spec_from_file_location("research_mcp", "/data/data/com.termux/files/home/.mcp/research_mcp.py")
    mcp_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mcp_mod)

    sample_conflicting_text = """
    【ソースA】2026年3月にバージョン 2.0 がリリースされた。完全無料で誰でも利用可能である。
    【ソースB】2025-11-01にver 1.5が発表。一部機能は有料であり、エンタープライズは非対応。料金は月額$50ドル。
    """
    res = mcp_mod.detect_fact_conflicts(sample_conflicting_text)
    assert res["status"] == "success"
    assert "### ⚠️ ファクト矛盾・論争点検証マトリクス" in res["content"]
    assert "年代・日付" in res["content"]
    assert "バージョン情報" in res["content"]
    assert res["has_conflicts"] is True

def test_format_commercial_report_structure():
    """ResearchTools.format_commercial_report が商用最高峰の必須章立てを完全網羅するか検証"""
    rt = ResearchTools()
    
    title = "自律型AIエージェント最新アーキテクチャ 2026"
    summary = "MCP 2.0およびA2Aプロトコル標準化により、ステートレス自律エージェントが商用基幹システムへ完全定着。"
    evidence_matrix = [
        ["情報源", "カテゴリ", "信頼性", "ステータス"],
        ["arXiv:2603.12345", "一次学術論文", "最高", "検証済"],
        ["Anthropic / Google公式", "一次技術仕様", "高", "検証済"]
    ]
    conflict_matrix = [
        ["検証カテゴリ", "検出要素", "ステータス"],
        ["プロトコル仕様", "MCP 2.0 vs 旧1.x", "最新版へ統一"]
    ]
    mermaid_code = """
    flowchart TD
        User --> Orchestrator
        Orchestrator --> SubAgent1
        Orchestrator --> SubAgent2
    """
    comparison_table = """
    | 項目 | 従来型 (1.x) | SOTA (2.0) |
    | :--- | :--- | :--- |
    | 通信 | SSE / StdIO | Stateless HTTP Stream |
    """
    action_plan = "- [ ] Termux 内 MCP 2.0 完全移行\n- [ ] 5層検証ゲート自動適用"
    sources = [{"title": "Google MCP Specification", "url": "https://spec.modelcontextprotocol.io"}]
    key_visuals = ["https://example.com/assets/architecture_diagram.png"]

    report_md = rt.format_commercial_report(
        title=title,
        exec_summary=summary,
        evidence_matrix=evidence_matrix,
        conflict_matrix=conflict_matrix,
        details_body="詳細分析テキスト...",
        mermaid_diagram=mermaid_code,
        comparison_table=comparison_table,
        action_plan=action_plan,
        primary_sources=sources,
        key_visuals=key_visuals
    )

    assert "# 【調査レポート】" in report_md
    assert "エグゼクティブ・サマリー" in report_md
    assert "視覚的エビデンス・キービジュアル" in report_md
    assert "多角エビデンス検証マトリクス" in report_md
    assert "ファクト矛盾・論争点検証マトリクス" in report_md
    assert "```mermaid" in report_md
    assert "比較分析・トレードオフ評価" in report_md
    assert "将来展望・拓磨様への具体的提言＆ToDo" in report_md
    assert "参照一次ソース・正規エビデンス一覧" in report_md
    assert "https://spec.modelcontextprotocol.io" in report_md

def test_render_beautiful_html_commercial_elements():
    """美麗HTMLがMermaid.js、Tailwind CSS、印刷スタイル(@media print)を備えているか検証"""
    rt = ResearchTools()
    sample_md = """# Commercial SOTA Audit
    
```mermaid
graph TD
    A[Data Acquisition] --> B[Trafilatura Deep Body]
    B --> C[Cross-Source Audit]
    C --> D[Commercial Report]
```

| Engine | Score | Performance |
| :--- | :--- | :--- |
| TUGUMIv6 Deep Research | 100/100 | SOTA Grade |
"""
    html = rt.render_beautiful_html("SOTA Report", sample_md)
    assert "<!DOCTYPE html>" in html
    assert "mermaid.initialize" in html
    assert "@media print" in html
    assert "TUGUMIv6 SOTA Intelligence" in html
    assert "class=\"mermaid" in html or "mermaid my-6" in html

def test_og_image_extraction_logic():
    """HTML文字列からのOGP画像抽出が正常に動作するか検証"""
    spec = importlib.util.spec_from_file_location("research_mcp", "/data/data/com.termux/files/home/.mcp/research_mcp.py")
    mcp_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mcp_mod)

    sample_html = """<!DOCTYPE html>
    <html>
    <head>
        <meta property="og:title" content="Test Page">
        <meta property="og:image" content="https://img.example.com/cover.jpg">
    </head>
    <body><h1>Hello</h1></body>
    </html>
    """
    img = mcp_mod._extract_og_image(sample_html, base_url="https://img.example.com")
    assert img == "https://img.example.com/cover.jpg"
