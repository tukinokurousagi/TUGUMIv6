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
