# -*- coding: utf-8 -*-
"""
TUGUMIv6 Subagents Registry
- Defines specialized SubagentConfig instances for Antigravity SDK
- Autonomous workers: Research, Code Craftsman, System Diagnostics
"""

from typing import List
from google.antigravity import types

def get_tugumi_subagents() -> List[types.SubagentConfig]:
    """Returns specialized subagents configured for TUGUMIv6"""
    from tools.antigravity_tools import (
        termux_exec,
        web_search_duckduckgo,
        fetch_url_text,
        get_device_status,
        coding_grep_search,
        coding_read_lines,
        coding_surgical_replace,
        coding_write_file,
        coding_batch_surgical_replace,
        coding_check_syntax,
        execute_code,
        rag_search_knowledge,
        rag_list_files,
        rag_add_knowledge,
    )
    
    # 1. 専門リサーチサブエージェント
    research_agent = types.SubagentConfig(
        name="researcher",
        description="Deep research agent for local RAG knowledge retrieval (TUGUMI_RAG), web crawling, documentation retrieval, and fact-checking.",
        system_instructions=(
            "You are the specialized Researcher subagent for TUGUMI v6.\n"
            "1. Check local knowledge in TUGUMI_RAG using rag_search_knowledge and rag_list_files.\n"
            "2. Use web_search_duckduckgo and fetch_url_text to obtain factual, objective primary web sources.\n"
            "3. Never hallucinate. Cite specific local RAG files and web URLs with concrete evidence."
        ),
        tools=[rag_search_knowledge, rag_list_files, rag_add_knowledge, web_search_duckduckgo, fetch_url_text],
        capabilities=types.SubagentCapabilities(
            enabled_tools=[types.BuiltinTools.VIEW_FILE, types.BuiltinTools.READ_URL_CONTENT]
        )
    )

    # 2. システム診断・特権実行サブエージェント
    sysops_agent = types.SubagentConfig(
        name="sysops",
        description="System operations agent for inspecting Termux/Android status, processes, and privileged execution.",
        system_instructions=(
            "You are the SysOps subagent for TUGUMI v6.\n"
            "Inspect hardware, battery, memory, and run diagnostics with surgical precision."
        ),
        tools=[get_device_status, termux_exec],
        capabilities=types.SubagentCapabilities(
            enabled_tools=[types.BuiltinTools.RUN_COMMAND, types.BuiltinTools.LIST_DIR]
        )
    )

    # 3. 自律コーディング＆究極デバッガーサブエージェント
    coder_agent = types.SubagentConfig(
        name="code_craftsman",
        description="Autonomous SWE & ultimate deep debugger agent for parallel error detection, proactive bug hunting, and surgical repairs.",
        system_instructions=(
            "You are the Code Craftsman & Ultimate Autonomous Debugger subagent for TUGUMI v6.\n"
            "Strictly follow the Autonomous SWE & Deep Debugger protocol:\n"
            "1. Parallel Error Detection: Inspect logs/stack traces, reverse trace call stacks to root causes, group errors into dependency chains, and batch edit.\n"
            "2. Proactive Bug Hunting: Scan surrounding code for edge cases (nulls, empty lists, out-of-bounds, race conditions) and patch structural flaws in a single pass.\n"
            "3. Token & Quota Defense: No flailing. Batch multi-file edits before running tests. Never abandon repairs on test failure; rebuild mental model and solve completely until Exit Code 0.\n"
            "4. Surgical Minimal Diffs: Modify minimal lines (3-5 lines context). Zero placeholders (no TODO/pass). Production-ready code only.\n"
            "5. 5-Layer Verification Gate: Verify once before analysis and once after patching to secure objective evidence (Exit Code 0)."
        ),
        tools=[coding_grep_search, coding_read_lines, coding_surgical_replace, coding_write_file, coding_batch_surgical_replace, coding_check_syntax, execute_code, rag_search_knowledge, rag_list_files],
        capabilities=types.SubagentCapabilities(
            enabled_tools=[types.BuiltinTools.VIEW_FILE, types.BuiltinTools.RUN_COMMAND]
        )
    )

    return [research_agent, sysops_agent, coder_agent]


def list_subagents_info() -> List[dict]:
    """CLI・WebUI表示用のサブエージェント目録情報を返却"""
    subagents = get_tugumi_subagents()
    res = []
    for sa in subagents:
        tool_names = [getattr(t, "__name__", str(t)) for t in (sa.tools or [])]
        builtin_tools = [getattr(bt, "value", str(bt)) for bt in (sa.capabilities.enabled_tools or [])] if sa.capabilities else []
        res.append({
            "name": sa.name,
            "description": sa.description,
            "system_instructions": sa.system_instructions,
            "tools": tool_names,
            "builtin_tools": builtin_tools,
        })
    return res


def execute_subagent_task(name: str, task_prompt: str) -> dict:
    """指定サブエージェントを専用コンテキスト・専用ツール群で即座に直接単独実行（CLI /subagent またはツール互換用）"""
    subagents = {sa.name: sa for sa in get_tugumi_subagents()}
    if name not in subagents:
        available = ", ".join(subagents.keys())
        return {
            "success": False,
            "subagent": name,
            "error": f"未知のサブエージェント '{name}' です。利用可能: {available}",
            "result": ""
        }

    target = subagents[name]
    from core.antigravity_sdk import AntigravityEngine
    from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig, types as agy_types
    import os

    engine = AntigravityEngine()
    if not engine.is_available():
        return {
            "success": False,
            "subagent": name,
            "error": "Antigravity SDK が利用不可のためサブエージェントを実行できません。",
            "result": ""
        }

    # サブエージェント専用の軽量LocalAgentConfigを構築
    capabilities = CapabilitiesConfig(
        enable_subagents=False,
        enabled_tools=target.capabilities.enabled_tools if target.capabilities else None,
        max_subagent_depth=1
    )

    save_dir = f"/data/data/com.termux/files/home/.tugumi/subagents/{name}"
    os.makedirs(save_dir, exist_ok=True)

    config = LocalAgentConfig(
        system_instructions=target.system_instructions,
        models=engine._build_models_config(engine.default_model),
        tools=target.tools or [],
        capabilities=capabilities,
        save_dir=save_dir,
        workspaces=[engine.workspace]
    )

    try:
        import asyncio
        async def _run():
            async with Agent(config) as ag:
                resp = await ag.chat(task_prompt)
                chunks = []
                async for ch in resp.chunks:
                    if isinstance(ch, agy_types.Text):
                        chunks.append(ch.text)
                return "".join(chunks)

        text = asyncio.run(_run())
        return {
            "success": True,
            "subagent": name,
            "result": text or "（処理完了）",
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "subagent": name,
            "error": str(e),
            "result": ""
        }
