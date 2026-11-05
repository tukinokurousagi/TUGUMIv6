#!/data/data/com.termux/files/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Antigravity Self-Evolver - Live SDK Spec Inspector, Evolution Gap Analyzer & Verifier
=====================================================================================
1. --check-sdk-spec        : google-antigravity SDK の最新仕様・全フィールド・Hooks v2 をライブ検視
2. --analyze-gap           : TUGUMIv6 core/antigravity_sdk.py のSDK機能活用率と未導入機能(Gap)を診断
3. --research-trends <q>   : 最新の自己進化AIエージェント技術・SDK動向をWeb検索
4. --verify-evolution      : TUGUMIv6 AntigravityEngine.build_config() の実機自己進化状態を検証
"""

import argparse
import ast
import html
import importlib.metadata as md
import inspect
import json
import os
import py_compile
import re
import sys
import urllib.parse
import urllib.request
from typing import Any, Dict, List

HOME = os.path.expanduser("~")
DEFAULT_TARGET_SDK_DRIVER = os.path.join(HOME, "TUGUMIv6", "core", "antigravity_sdk.py")


def check_antigravity_sdk_spec() -> Dict[str, Any]:
    """実機にインストールされている google-antigravity SDK の全仕様をライブ抽出"""
    spec: Dict[str, Any] = {
        "sdk_package": "google-antigravity",
        "version": "not_installed",
        "configs": {},
        "enums": {},
        "hooks_v2": [],
        "triggers": [],
        "agent_methods": [],
    }
    try:
        spec["version"] = md.version("google-antigravity")
    except Exception:
        pass

    try:
        import google.antigravity as ag
        from google.antigravity import hooks, triggers, types

        config_classes = [
            "LocalAgentConfig",
            "CapabilitiesConfig",
            "CompactionConfig",
            "RetryConfig",
            "ModelAPIRetryConfig",
            "ModelOutputRetryConfig",
            "BudgetConfig",
            "ToolOutputTruncationConfig",
            "SubagentConfig",
            "McpStdioServer",
            "McpStreamableHttpServer",
        ]
        for cname in config_classes:
            cls = getattr(types, cname, None) or getattr(ag, cname, None)
            if cls and hasattr(cls, "model_fields"):
                spec["configs"][cname] = {
                    k: str(v.annotation) for k, v in cls.model_fields.items()
                }

        enum_classes = [
            "ThinkingLevel",
            "SessionContinuationMode",
            "AgentBehavior",
            "BudgetScope",
        ]
        for ename in enum_classes:
            ecls = getattr(types, ename, None) or getattr(ag, ename, None)
            if ecls:
                spec["enums"][ename] = [k for k in dir(ecls) if k.isupper()]

        hook_names = [
            "on_session_start",
            "on_session_end",
            "pre_turn",
            "post_turn",
            "pre_tool_call_decide",
            "post_tool_call",
            "on_tool_error",
            "on_compaction",
            "on_interaction",
            "stop",
        ]
        for hname in hook_names:
            if hasattr(hooks, hname):
                spec["hooks_v2"].append(hname)

        for tname in ["every", "on_file_change", "trigger"]:
            if hasattr(triggers, tname):
                spec["triggers"].append(tname)

        for mname, _ in inspect.getmembers(ag.Agent):
            if not mname.startswith("_"):
                spec["agent_methods"].append(mname)

        spec["status"] = "ok"
    except Exception as e:
        spec["status"] = "error"
        spec["error"] = str(e)

    return spec


def analyze_evolution_gap(target_file: str = DEFAULT_TARGET_SDK_DRIVER) -> Dict[str, Any]:
    """TUGUMIv6 の antigravity_sdk.py を解析し、SDK最新仕様に対する活用率とEvolution Gapを算出"""
    if not os.path.exists(target_file):
        return {"status": "error", "message": f"Target file not found: {target_file}"}

    with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()

    # LocalAgentConfig 呼び出しに渡されているキーワード引数をASTで抽出
    passed_kwargs_local_config = set()
    passed_kwargs_capabilities = set()
    try:
        tree = ast.parse(source, filename=target_file)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                if func_name == "LocalAgentConfig":
                    for kw in node.keywords:
                        if kw.arg:
                            passed_kwargs_local_config.add(kw.arg)
                elif func_name == "CapabilitiesConfig":
                    for kw in node.keywords:
                        if kw.arg:
                            passed_kwargs_capabilities.add(kw.arg)
    except Exception as e:
        return {"status": "error", "message": f"AST parse error: {e}"}

    # 10大コア進化チェック項目
    ten_pillars = {
        "1_skills_paths": "skills_paths" in passed_kwargs_local_config,
        "2_mcp_servers_hybrid": "mcp_servers" in passed_kwargs_local_config and "McpStreamableHttpServer" in source,
        "3_subagents": "subagents" in passed_kwargs_local_config,
        "4_policies": "policies" in passed_kwargs_local_config,
        "5_workspaces": "workspaces" in passed_kwargs_local_config,
        "6_compaction_config": "compaction_config" in passed_kwargs_local_config,
        "7_retry_config": "retry_config" in passed_kwargs_local_config,
        "8_hooks_v2": "hooks" in passed_kwargs_local_config,
        "9_save_dir_persistence": "save_dir" in passed_kwargs_local_config,
        "10_tool_output_truncation": "tool_output_truncation_config" in passed_kwargs_capabilities,
    }

    active_count = sum(1 for v in ten_pillars.values() if v)
    score_pct = round((active_count / len(ten_pillars)) * 100, 1)
    gaps = [k for k, v in ten_pillars.items() if not v]

    return {
        "status": "ok",
        "target_file": target_file,
        "evolution_score_percent": score_pct,
        "active_pillars": active_count,
        "total_pillars": len(ten_pillars),
        "pillar_status": ten_pillars,
        "local_agent_config_kwargs": sorted(passed_kwargs_local_config),
        "capabilities_config_kwargs": sorted(passed_kwargs_capabilities),
        "evolution_gaps": gaps,
    }


def research_self_evolution_trends(query: str, max_results: int = 5) -> Dict[str, Any]:
    """DuckDuckGo 経由で最新の自己進化型AIエージェント技術・SDK仕様を検索"""
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; Termux) AppleWebKit/537.36 Chrome/126.0.0.0 Mobile Safari/537.36"
        },
    )
    results: List[Dict[str, str]] = []
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw_html = resp.read().decode("utf-8", errors="ignore")
        blocks = re.findall(
            r'<a rel="nofollow" class="result__a" href="([^"]+)">(.*?)</a>.*?<a class="result__snippet"[^>]*>(.*?)</a>',
            raw_html,
            flags=re.DOTALL,
        )
        for href, title_html, snippet_html in blocks[:max_results]:
            clean_url = href
            if "uddg=" in href:
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                if "uddg" in parsed:
                    clean_url = parsed["uddg"][0]
            results.append(
                {
                    "title": re.sub(r"<[^>]+>", "", html.unescape(title_html)).strip(),
                    "url": clean_url,
                    "snippet": re.sub(r"<[^>]+>", "", html.unescape(snippet_html)).strip(),
                }
            )
        return {"status": "ok", "query": query, "count": len(results), "results": results}
    except Exception as e:
        return {"status": "error", "query": query, "message": str(e), "results": []}


def verify_tugumi_evolution() -> Dict[str, Any]:
    """TUGUMIv6 の AntigravityEngine を実際にロードし、最新SDK仕様が完全統合されているか検証"""
    tugumi_root = os.path.join(HOME, "TUGUMIv6")
    if tugumi_root not in sys.path:
        sys.path.insert(0, tugumi_root)

    checks: Dict[str, Any] = {}
    try:
        py_compile.compile(DEFAULT_TARGET_SDK_DRIVER, doraise=True)
        checks["syntax_gate"] = "PASS"
    except Exception as e:
        return {"status": "failed", "stage": "syntax_gate", "error": str(e)}

    try:
        from core.antigravity_sdk import AntigravityEngine

        engine = AntigravityEngine()
        cfg = engine.build_config(prompt="gemini doc test")

        checks["sdk_available"] = engine.is_available()
        checks["skills_paths_configured"] = bool(cfg.skills_paths and len(cfg.skills_paths) > 0)
        checks["mcp_servers_configured"] = bool(cfg.mcp_servers and len(cfg.mcp_servers) >= 1)
        checks["subagents_configured"] = bool(cfg.subagents and len(cfg.subagents) >= 1)
        checks["policies_configured"] = bool(cfg.policies and len(cfg.policies) >= 1)
        checks["workspaces_configured"] = bool(cfg.workspaces and len(cfg.workspaces) >= 1)
        checks["compaction_configured"] = cfg.compaction_config is not None
        checks["retry_configured"] = cfg.retry_config is not None
        checks["hooks_configured"] = bool(cfg.hooks and len(cfg.hooks) > 0)
        checks["save_dir_configured"] = cfg.save_dir is not None
        checks["truncation_configured"] = (
            cfg.capabilities is not None
            and cfg.capabilities.tool_output_truncation_config is not None
        )

        # Compatibility aliases for WebUI / CLI consumers
        checks["skills_paths"] = checks["skills_paths_configured"]
        checks["mcp_servers"] = checks["mcp_servers_configured"]
        checks["subagents"] = checks["subagents_configured"]
        checks["policies"] = checks["policies_configured"]
        checks["workspaces"] = checks["workspaces_configured"]
        checks["compaction_config"] = checks["compaction_configured"]
        checks["retry_config"] = checks["retry_configured"]
        checks["hooks_registered"] = checks["hooks_configured"]
        checks["save_dir"] = checks["save_dir_configured"]
        checks["tool_output_truncation_config"] = checks["truncation_configured"]

        checks["registered_tools_count"] = len(cfg.tools or [])
        checks["mcp_servers_count"] = len(cfg.mcp_servers or [])
        checks["mcp_server_names"] = [getattr(s, "name", str(s)) for s in (cfg.mcp_servers or [])]
        checks["subagents_count"] = len(cfg.subagents or [])
        checks["subagent_names"] = [getattr(s, "name", str(s)) for s in (cfg.subagents or [])]
        checks["hooks_count"] = len(cfg.hooks or [])
        checks["hook_names"] = [getattr(h, "__name__", type(h).__name__) for h in (cfg.hooks or [])]

        gap_report = analyze_evolution_gap(DEFAULT_TARGET_SDK_DRIVER)
        checks["evolution_score_percent"] = gap_report.get("evolution_score_percent", 0.0)

        all_passed = all(
            [
                checks["sdk_available"],
                checks["skills_paths_configured"],
                checks["mcp_servers_configured"],
                checks["subagents_configured"],
                checks["policies_configured"],
                checks["workspaces_configured"],
                checks["compaction_configured"],
                checks["retry_configured"],
                checks["hooks_configured"],
                checks["save_dir_configured"],
                checks["truncation_configured"],
            ]
        )
        return {
            "status": "ok" if all_passed else "partial",
            "all_passed": all_passed,
            "checks": checks,
            "gap_summary": gap_report,
        }
    except Exception as e:
        return {"status": "failed", "stage": "runtime_verification", "error": str(e)}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Antigravity Self-Evolver - SDK Spec Inspector & Evolution Gap Analyzer"
    )
    parser.add_argument(
        "--check-sdk-spec",
        action="store_true",
        help="Inspect live google-antigravity SDK specification, fields, hooks, and triggers",
    )
    parser.add_argument(
        "--analyze-gap",
        action="store_true",
        help="Analyze Evolution Gap in TUGUMIv6 core/antigravity_sdk.py against latest SDK capabilities",
    )
    parser.add_argument(
        "--target",
        type=str,
        default=DEFAULT_TARGET_SDK_DRIVER,
        help="Target Python file for gap analysis",
    )
    parser.add_argument(
        "--research-trends",
        type=str,
        default="",
        help="Search latest AI agent self-evolution trends and SDK specs via DuckDuckGo",
    )
    parser.add_argument(
        "--verify-evolution",
        action="store_true",
        help="Verify TUGUMIv6 AntigravityEngine live configuration and 10-pillar evolution status",
    )

    args = parser.parse_args()

    if args.check_sdk_spec:
        print(json.dumps(check_antigravity_sdk_spec(), ensure_ascii=False, indent=2))
        return 0
    if args.analyze_gap:
        print(json.dumps(analyze_evolution_gap(args.target), ensure_ascii=False, indent=2))
        return 0
    if args.research_trends:
        print(json.dumps(research_self_evolution_trends(args.research_trends), ensure_ascii=False, indent=2))
        return 0
    if args.verify_evolution:
        res = verify_tugumi_evolution()
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res.get("status") == "ok" else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
