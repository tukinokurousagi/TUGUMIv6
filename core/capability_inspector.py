# -*- coding: utf-8 -*-
"""
TUGUMIv6 Capability Inspector
=============================
Unified inspection engine for SKILL ecosystem and MCP (Model Context Protocol) servers.
Provides structured data for CLI Rich visualization and Web UI REST APIs.

Master: 拓磨様
Engine: TUGUMIv6 Cognitive & Tool Architecture
"""

import os
import re
import json
import time
import datetime
from typing import Dict, Any, List, Optional

HOME = os.path.expanduser("~")
LOCAL_SKILLS_DIR = os.path.join(HOME, "TUGUMIv6", "skills")
GLOBAL_SKILLS_DIR = os.path.join(HOME, ".agents", "skills")
MCP_CONFIG_DIR = os.path.join(HOME, ".gemini", "antigravity-cli", "mcp")


def categorize_skill(name: str) -> str:
    """スキル名から直感的な専門ドメインカテゴリを分類"""
    name_lower = name.lower()
    if any(k in name_lower for k in ["craftsman", "github", "test", "tdd", "regression", "root-cause", "subagent", "git", "coding"]):
        return "SWE & 開発工学"
    elif any(k in name_lower for k in ["brainstorming", "tree-of-thoughts", "writing-plans", "judge", "systematic-debugging", "analyse", "first-principles", "fpf"]):
        return "推論・計画・デバッグ"
    elif any(k in name_lower for k in ["shizuku", "termux", "tasker", "sqlite", "context-compression", "env"]):
        return "システム・Android特権"
    elif any(k in name_lower for k in ["video", "audio", "ascii", "art", "canvas", "slack-gif", "media"]):
        return "メディア・クリエイティブ"
    elif any(k in name_lower for k in ["writer", "reporter", "wiki", "obsidian", "doc", "pdf", "docx", "pptx", "xlsx", "gossip", "horse"]):
        return "リサーチ・ナレッジ生成"
    elif any(k in name_lower for k in ["mcp", "evolution", "guard", "agent", "skill"]):
        return "自律進化・プロトコル"
    return "汎用拡張"


class SkillInspector:
    """TUGUMIv6 SKILLエコシステムの深層調査エンジン"""

    def __init__(self, local_dir: str = LOCAL_SKILLS_DIR, global_dir: Optional[str] = None):
        self.local_dir = local_dir
        self.global_dir = global_dir

    def list_skills(self) -> List[Dict[str, Any]]:
        """配備されている全SKILLの一覧とメタデータを構造化取得"""
        skills = []
        seen = set()

        # 1. TUGUMIv6専用ローカル (~/TUGUMIv6/skills) のみをスキャン（グローバルの不要SKILL逆流を防止）
        search_dirs = [self.local_dir] if not self.global_dir else [self.local_dir, self.global_dir]

        for s_dir in search_dirs:
            if not os.path.exists(s_dir):
                continue
            for entry in sorted(os.listdir(s_dir)):
                if entry.startswith(".") or entry in seen:
                    continue
                full_path = os.path.join(s_dir, entry)
                skill_md_path = os.path.join(full_path, "SKILL.md")

                if os.path.isdir(full_path) and os.path.exists(skill_md_path):
                    seen.add(entry)
                    meta = self._parse_skill_md(skill_md_path, entry)
                    scripts_dir = os.path.join(full_path, "scripts")
                    has_scripts = os.path.exists(scripts_dir) and len(os.listdir(scripts_dir)) > 0
                    
                    skills.append({
                        "name": entry,
                        "title": meta.get("name", entry),
                        "description": meta.get("description", "説明なし"),
                        "category": categorize_skill(entry),
                        "path": full_path,
                        "is_symlink": os.path.islink(full_path),
                        "has_scripts": has_scripts,
                        "status": "Active"
                    })

        return sorted(skills, key=lambda x: (x["category"], x["name"]))

    def get_skill_detail(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """特定SKILLのMarkdown全文、スクリプト一覧等の詳細を取得"""
        search_dirs = [d for d in [self.local_dir, self.global_dir] if d]
        for s_dir in search_dirs:
            full_path = os.path.join(s_dir, skill_name)
            skill_md = os.path.join(full_path, "SKILL.md")
            if os.path.exists(skill_md):
                try:
                    with open(skill_md, "r", encoding="utf-8", errors="ignore") as f:
                        raw_content = f.read()
                    
                    scripts = []
                    scripts_dir = os.path.join(full_path, "scripts")
                    if os.path.exists(scripts_dir):
                        scripts = [f for f in os.listdir(scripts_dir) if not f.startswith(".")]

                    meta = self._parse_skill_md(skill_md, skill_name)
                    return {
                        "name": skill_name,
                        "description": meta.get("description", ""),
                        "category": categorize_skill(skill_name),
                        "path": full_path,
                        "content": raw_content,
                        "scripts": scripts,
                        "status": "Active"
                    }
                except Exception as e:
                    return {"name": skill_name, "error": str(e)}
        return None

    def _parse_skill_md(self, filepath: str, fallback_name: str) -> Dict[str, str]:
        """SKILL.md の YAML フロントマターから name / description を抽出"""
        res = {"name": fallback_name, "description": ""}
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(4096)
            
            # YAML Frontmatter (---\n ... \n---)
            m = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
            if m:
                fm = m.group(1)
                for line in fm.splitlines():
                    if line.startswith("name:"):
                        res["name"] = line.replace("name:", "").strip().strip("'\"")
                    elif line.startswith("description:"):
                        res["description"] = line.replace("description:", "").strip().strip("'\"")
            
            # フロントマターがない場合のフォールバック（# タイトル、または最初の段落）
            if not res["description"]:
                lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#") and not l.startswith("---")]
                if lines:
                    res["description"] = lines[0][:150]
        except Exception:
            pass
        return res


class MCPInspector:
    """TUGUMIv6 MCP (Model Context Protocol) サーバー・ツール深層調査エンジン"""

    def __init__(self, mcp_dir: str = MCP_CONFIG_DIR):
        self.mcp_dir = mcp_dir

    def list_servers(self) -> List[Dict[str, Any]]:
        """登録・連携されている全MCPサーバーと各ツールの概要を取得"""
        servers = []
        if not os.path.exists(self.mcp_dir):
            return servers

        for entry in sorted(os.listdir(self.mcp_dir)):
            server_dir = os.path.join(self.mcp_dir, entry)
            if not os.path.isdir(server_dir) or entry.startswith("."):
                continue

            tools = []
            instructions = ""

            for fname in sorted(os.listdir(server_dir)):
                fpath = os.path.join(server_dir, fname)
                if fname.endswith(".json"):
                    tool_name = fname[:-5]
                    tool_info = self._parse_tool_schema(fpath, tool_name)
                    tools.append(tool_info)
                elif fname.lower() == "instructions.md":
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            instructions = f.read(500).strip()
                    except Exception:
                        pass

            servers.append({
                "name": entry,
                "server_name": entry,
                "status": "Active (MCP 2.0)",
                "tool_count": len(tools),
                "tools": tools,
                "instructions_preview": instructions[:120] if instructions else "なし",
                "path": server_dir
            })

        return servers

    def get_server_detail(self, server_name: str) -> Optional[Dict[str, Any]]:
        """特定MCPサーバーの全ツールJSONスキーマ詳細を取得 (オンデマンドライブ取得フォールバック対応)"""
        server_dir = os.path.join(self.mcp_dir, server_name)
        if not os.path.exists(server_dir) or not os.path.isdir(server_dir):
            try:
                from tools.tugumi_mcp import mcp as live_mcp
                live_tools = live_mcp.list_tools(server_name)
                if live_tools:
                    formatted_tools = []
                    for t in live_tools:
                        schema = t.get("inputSchema", t.get("parameters", {}))
                        formatted_tools.append({
                            "name": t.get("name", ""),
                            "description": t.get("description", "説明なし").split("\n")[0],
                            "parameters": schema,
                            "schema_raw": t
                        })
                    return {
                        "name": server_name,
                        "server_name": server_name,
                        "status": "On-Demand (MCP 2.0 Ephemeral)",
                        "tool_count": len(formatted_tools),
                        "instructions": "On-Demand Ephemeral MCP Server",
                        "tools": formatted_tools,
                        "path": "~/.gemini/config/mcp_config.json"
                    }
            except Exception:
                pass
            return None

        tools = []
        instructions = ""
        instructions_path = os.path.join(server_dir, "instructions.md")
        if os.path.exists(instructions_path):
            try:
                with open(instructions_path, "r", encoding="utf-8", errors="ignore") as f:
                    instructions = f.read()
            except Exception:
                pass

        for fname in sorted(os.listdir(server_dir)):
            if fname.endswith(".json"):
                fpath = os.path.join(server_dir, fname)
                tool_name = fname[:-5]
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        schema = json.load(f)
                    tools.append({
                        "name": tool_name,
                        "description": schema.get("description", "説明なし"),
                        "parameters": schema.get("parameters", {}),
                        "schema_raw": schema
                    })
                except Exception as e:
                    tools.append({"name": tool_name, "error": str(e)})

        return {
            "name": server_name,
            "server_name": server_name,
            "status": "Active (MCP 2.0)",
            "tool_count": len(tools),
            "instructions": instructions,
            "tools": tools,
            "path": server_dir
        }

    def _parse_tool_schema(self, filepath: str, fallback_name: str) -> Dict[str, Any]:
        """JSONスキーマからツール名、説明、必須引数を抽出"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            params = data.get("parameters", {})
            properties = params.get("properties", {})
            required = params.get("required", [])
            args_summary = ", ".join(f"{k}*" if k in required else k for k in properties.keys())

            return {
                "name": fallback_name,
                "description": data.get("description", "説明なし").split("\n")[0][:100],
                "args_summary": args_summary or "引数なし",
                "required_args": required
            }
        except Exception as e:
            return {"name": fallback_name, "description": f"Schema load error: {e}", "args_summary": "-"}


def inspect_fpf_status() -> Dict[str, Any]:
    """FPF (First-Principles Framework) 前提鮮度・認識的負債監査"""
    skill_path = os.path.join(GLOBAL_SKILLS_DIR, "first-principles-engine", "SKILL.md")
    skill_active = os.path.exists(skill_path)

    core_files = [
        os.path.join(HOME, "TUGUMIv6", "engine_config.json"),
        os.path.join(HOME, "TUGUMIv6", "persona", "soul.py"),
        os.path.join(HOME, "TUGUMIv6", "core", "engine_manager.py"),
        os.path.join(HOME, ".agents", "TSUGUMI_MEMORY.md"),
    ]
    file_audits = []
    now = time.time()
    for fp in core_files:
        if os.path.exists(fp):
            mtime = os.path.getmtime(fp)
            dt = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            age_hours = (now - mtime) / 3600
            freshness = "Fresh" if age_hours < 48 else "Moderate" if age_hours < 168 else "Decayed"
            file_audits.append({
                "file": os.path.basename(fp),
                "path": fp,
                "updated_at": dt,
                "freshness": freshness,
                "age_hours": round(age_hours, 1)
            })

    decayed_count = sum(1 for f in file_audits if f["freshness"] == "Decayed")
    debt_score = max(0, 100 - (decayed_count * 20))

    return {
        "engine_active": skill_active,
        "engine_name": "first-principles-engine (FPF Core v6)",
        "evidence_freshness_status": "EXCELLENT" if debt_score >= 80 else "WARNING",
        "epistemic_debt_score": debt_score,
        "files_audited": file_audits,
        "core_tenets": [
            "Evidence is perishable (証拠は生鮮食品である)",
            "Anti-Cutoff Bias (オフカット知識・一般論の疑念化)",
            "Context Drift Guard (変更差分からの前提崩壊自動検知)",
            "First-Principles Reset (物理的事実・入出力からゼロベース再構築)"
        ]
    }

