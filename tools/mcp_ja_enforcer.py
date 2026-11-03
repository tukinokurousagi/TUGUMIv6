#!/data/data/com.termux/files/usr/bin/python3
# -*- coding: utf-8 -*-
"""
TUGUMIv6 MCP Japanese Description Enforcer & Self-Healing Engine
===============================================================
Ensures that all MCP tool descriptions across schemas, source files, and
inspectors strictly maintain Japanese definitions without regression.

Master: 拓磨様
Engine: TUGUMIv6 SOTA Multi-Layer Persistence
"""

import os
import sys
import json
from typing import Tuple

TUGUMI_ROOT = "/data/data/com.termux/files/home/TUGUMIv6"
if TUGUMI_ROOT not in sys.path:
    sys.path.insert(0, TUGUMI_ROOT)

from core.capability_inspector import MCP_TOOL_JA_DESCRIPTIONS

MCP_SCHEMA_DIR = os.path.expanduser("~/.gemini/antigravity-cli/mcp")


def enforce_mcp_schemas_japanese(check_only: bool = False) -> Tuple[int, int, list]:
    """全MCPスキーマJSONファイルの説明文が日本語であることを検証・自己修復"""
    total_checked = 0
    updated_count = 0
    issues = []

    if not os.path.exists(MCP_SCHEMA_DIR):
        return 0, 0, ["MCP schema directory not found"]

    for root, _, files in os.walk(MCP_SCHEMA_DIR):
        for f in files:
            if not f.endswith(".json"):
                continue
            tool_name = f[:-5]
            if tool_name not in MCP_TOOL_JA_DESCRIPTIONS:
                continue

            total_checked += 1
            fpath = os.path.join(root, f)
            expected_desc = MCP_TOOL_JA_DESCRIPTIONS[tool_name]

            try:
                with open(fpath, "r", encoding="utf-8") as jf:
                    data = json.load(jf)
                current_desc = data.get("description", "").strip()

                if current_desc != expected_desc:
                    issues.append((tool_name, fpath, current_desc, expected_desc))
                    if not check_only:
                        data["description"] = expected_desc
                        with open(fpath, "w", encoding="utf-8") as jf:
                            json.dump(data, jf, ensure_ascii=False, indent=2)
                        updated_count += 1
            except Exception as e:
                issues.append((tool_name, fpath, f"Error: {e}", expected_desc))

    return total_checked, updated_count, issues


def verify_source_mcp_files_japanese() -> list:
    """主要MCPサーバーのソースコードdocstringが日本語であることを確認"""
    issues = []
    checks = [
        ("/data/data/com.termux/files/home/.mcp/tugumi_v6_mcp.py", "tugumi_exec", "Termux Linux環境"),
        ("/data/data/com.termux/files/home/.mcp/tugumi_v6_mcp.py", "tugumi_device_telemetry", "Android実機"),
        ("/data/data/com.termux/files/home/.mcp/failure_guard_mcp.py", "check_failure_risk", "危険な操作"),
        ("/data/data/com.termux/files/home/.mcp/twitter_mcp.py", "get_user_tweets", "指定したX"),
        ("/data/data/com.termux/files/home/.mcp/osint_mcp.py", "shodan_internetdb_lookup", "Shodan InternetDB"),
        ("/data/data/com.termux/files/home/horse-racing-mcp/server.py", "race_resolve", "自然言語のレース指定"),
        ("/data/data/com.termux/files/home/robin/mcp_server.py", "robin_search", "オニオン検索エンジン"),
        ("/data/data/com.termux/files/home/.mcp/playwright_mcp_server.mjs", "playwright_scrape", "Puppeteer"),
    ]

    for fpath, tool_name, expected_kw in checks:
        if not os.path.exists(fpath):
            issues.append(f"ファイル未検出: {fpath}")
            continue
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if expected_kw not in content:
                issues.append(f"{fpath} の {tool_name} に日本語キーワード '{expected_kw}' が含まれていません（先祖返りの可能性）")
        except Exception as e:
            issues.append(f"{fpath} 読み込み失敗: {e}")

    return issues


def main():
    check_only = "--check" in sys.argv
    print("🌸 TUGUMIv6 MCP 日本語説明文 永続化・整合性ガード")
    print(f"モード: {'[検査のみ]' if check_only else '[自動同期・修復]'}")

    total, updated, issues = enforce_mcp_schemas_japanese(check_only=check_only)
    source_issues = verify_source_mcp_files_japanese()

    print(f"✅ スキーマ検査件数: {total}件")
    if updated > 0:
        print(f"🔧 自動修復適用件数: {updated}件")

    all_issues = issues + source_issues
    if all_issues:
        print(f"\n⚠️ 検出された先祖返り・乖離: {len(all_issues)}件")
        for item in all_issues:
            print(f"  - {item}")
        if check_only:
            sys.exit(1)
    else:
        print("🎉 すべてのMCP説明文が完全に日本語で維持・永続化されています！")
        sys.exit(0)


if __name__ == "__main__":
    main()
