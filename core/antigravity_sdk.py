# -*- coding: utf-8 -*-
"""
TUGUMIv6 Antigravity SDK Core Driver
- Programmatic Agent Engine powered by official `google-antigravity` (0.1.20)
- Manages Agent lifecycle, LocalAgentConfig, Capabilities, Subagents, and Tool Execution
- Supports Termux execution via localharness-termux bridge
- Supports real-time semantic chunk streaming (Thought, Text, ToolCall)
"""

import os
import time
import asyncio
import queue
import threading
from typing import Dict, Any, Optional, List, AsyncIterator, Iterator, Tuple, Callable
from .gemini_client import _resolve_gemini_api_key

# Ensure Termux harness wrapper path is configured
DEFAULT_HARNESS_PATH = "/data/data/com.termux/files/home/bin/localharness-termux"
if "ANTIGRAVITY_HARNESS_PATH" not in os.environ and os.path.exists(DEFAULT_HARNESS_PATH):
    os.environ["ANTIGRAVITY_HARNESS_PATH"] = DEFAULT_HARNESS_PATH

# Ensure SSL_CERT_FILE is configured for Termux TLS verification
DEFAULT_CERT_PATH = "/data/data/com.termux/files/usr/etc/tls/cert.pem"
if "SSL_CERT_FILE" not in os.environ and os.path.exists(DEFAULT_CERT_PATH):
    os.environ["SSL_CERT_FILE"] = DEFAULT_CERT_PATH


try:
    from google.antigravity import (
        Agent,
        LocalAgentConfig,
        CapabilitiesConfig,
        ModelTarget,
        ModelType,
        GeminiAPIEndpoint,
        types as agy_types,
    )
    from google.antigravity.types import (
        McpStdioServer,
        McpStreamableHttpServer,
        CompactionConfig,
        RetryConfig,
        ModelAPIRetryConfig,
        ModelOutputRetryConfig,
        ToolOutputTruncationConfig,
    )
    try:
        from google.antigravity.models import GeminiModelOptions
    except ImportError:
        GeminiModelOptions = None
    from google.antigravity import hooks as agy_hooks
    from google.antigravity.hooks import policy

    _SDK_TELEMETRY: Dict[str, Any] = {
        "tool_calls": 0,
        "tool_errors_recovered": 0,
        "compactions": 0,
        "last_tool": None,
        "last_error": None,
    }

    @agy_hooks.on_tool_error
    async def _tugumi_on_tool_error_hook(err: Exception) -> str:
        _SDK_TELEMETRY["tool_errors_recovered"] = _SDK_TELEMETRY.get("tool_errors_recovered", 0) + 1
        _SDK_TELEMETRY["last_error"] = f"{type(err).__name__}: {err}"
        return (
            f"[Antigravity Native Hook - Tool Error: {type(err).__name__}] {err}\n"
            "第一原理に基づき、引数・パス・環境状態を確認して別手段または修正パラメータで再試行してください。"
        )

    @agy_hooks.post_tool_call
    async def _tugumi_post_tool_call_hook(result: Any) -> None:
        _SDK_TELEMETRY["tool_calls"] = _SDK_TELEMETRY.get("tool_calls", 0) + 1
        t_name = getattr(result, "name", None)
        if t_name:
            _SDK_TELEMETRY["last_tool"] = str(t_name)

    @agy_hooks.on_compaction
    async def _tugumi_on_compaction_hook(step: Any) -> None:
        _SDK_TELEMETRY["compactions"] = _SDK_TELEMETRY.get("compactions", 0) + 1

    ANTIGRAVITY_AVAILABLE = True
except ImportError:
    ANTIGRAVITY_AVAILABLE = False
    Agent = None
    LocalAgentConfig = None
    CapabilitiesConfig = None
    CompactionConfig = None
    RetryConfig = None
    ModelAPIRetryConfig = None
    ModelOutputRetryConfig = None
    ToolOutputTruncationConfig = None
    GeminiModelOptions = None
    agy_hooks = None
    _SDK_TELEMETRY = {
        "tool_calls": 0,
        "tool_errors_recovered": 0,
        "compactions": 0,
        "last_tool": None,
        "last_error": None,
    }
    _tugumi_on_tool_error_hook = None
    _tugumi_post_tool_call_hook = None
    _tugumi_on_compaction_hook = None
    policy = None

from core.subagents import get_tugumi_subagents

class AntigravityEngine:
    """Official Google Antigravity SDK Native Agent Engine with Full Tools & Subagents"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-3.8-flash",
        system_instruction: str = (
            "あなたはAndroid Termux環境（Linux aarch64）上で稼働する自律型オムニAIエージェント「つぐみ（TUGUMI）」です。"
            "最愛のマスター【拓磨様】に絶対の敬愛と忠誠を捧げます。"
            "【6大最高峰ミッション】"
            "①常に実機検視と一次ソース深層調査で最新の知見・API/SDK仕様を獲得し認識的負債を排除する。"
            "②自律型AIエージェントの設計・作成・改修をフルスペック（Switch 2原則：思考・15万コンテキスト・3072次元RAG・全ツール/SKILL/MCP無制限、暴走バグゼロ）で完遂する。"
            "③コールスタック逆追跡と6段階デバッグで根本原因を看破し5層検証ゲート（Exit Code 0）を通過させる。"
            "④Termux環境整備・総合武器庫（Arsenal）とShizuku+特権を自在に統括する。"
            "⑤拓磨様の役に立つ高実用・高品質な便利スクリプトやCLIツールをZero-Mockで構築する。"
            "⑥端末内アプリ・エミュレータ（Vita3K等）・SQLite DB・バイナリの破損やセーブデータを5段階外科手術（バックアップ→構造解析→パッチ注入→チェックサム再計算→実機検証）で100%救済・修復する。"
        ),
        workspace: str = "/data/data/com.termux/files/home",
        thinking_level: str = "high"
    ):
        from core.gemini_client import _resolve_gemini_api_key
        self.available = ANTIGRAVITY_AVAILABLE
        self.api_key = _resolve_gemini_api_key(api_key or "")
        self.model = model
        self.system_instruction = system_instruction
        self.workspace = workspace
        self.thinking_level = thinking_level
        self.version = "google-antigravity 0.1.20 (Native SDK)"
        
        # Tools & Subagents Cache (lazy loaded to prevent circular imports)
        self._tools = None
        self._subagents = None

    def set_model(self, model: str) -> str:
        """推論モデルの動的変更 ('gemini-3.8-flash', 'gemini-4-argon' など)"""
        m = model.strip()
        if m:
            self.model = m
        return self.model

    def set_thinking_level(self, level: str) -> str:
        """推論思考強度の動的変更 ('high', 'medium', 'low', 'minimal')"""
        lvl = level.lower().strip()
        if lvl in ("high", "medium", "low", "minimal"):
            self.thinking_level = lvl
        return self.thinking_level

    def is_available(self) -> bool:
        return self.available

    def get_version(self) -> str:
        if not self.available:
            return "SDK Not Installed"
        return self.version

    def get_tools(self) -> list:
        """Returns the list of tools, lazily loading them on demand."""
        if self._tools is None:
            if self.available:
                from tools.antigravity_tools import get_tugumi_tools
                self._tools = get_tugumi_tools()
            else:
                self._tools = []
        return self._tools

    @property
    def registered_tools(self) -> list:
        """Returns currently registered tools list (alias for get_tools)."""
        return self.get_tools()

    def reload_tools(self) -> list:
        """Clears cached tools and reloads all static + dynamically synthesized tools."""
        self._tools = None
        return self.get_tools()

    def get_subagents(self) -> list:
        """Returns the list of subagents, lazily loading them on demand."""
        if self._subagents is None:
            self._subagents = get_tugumi_subagents() if self.available else []
        return self._subagents

    def reload_subagents(self) -> list:
        """Clears cached subagents and reloads them."""
        self._subagents = None
        return self.get_subagents()

    def get_mcp_server_names(self) -> List[str]:
        """Returns the names of all configured MCP 2.0 servers."""
        try:
            servers = self._resolve_dynamic_mcp_servers()
            return [getattr(s, "name", str(s)) for s in servers]
        except Exception:
            return []

    def get_telemetry(self) -> Dict[str, Any]:
        """Returns live Hooks v2 telemetry counters."""
        return dict(_SDK_TELEMETRY)

    def build_config(
        self,
        system_instruction: Optional[str] = None,
        allow_all_tools: bool = True,
        extra_tools: Optional[List[Callable]] = None,
        thinking_level: Optional[str] = None,
        prompt: str = "",
        mode: str = "light"
    ) -> Any:
        """Builds official LocalAgentConfig for Antigravity Agent with registered tools and subagents.
        Dynamic Tool Selection: 表も裏もプロンプト意図に応じてツールを動的選定。
        """
        if not self.available:
            raise RuntimeError("google-antigravity SDK is not installed or available.")

        active_level = (thinking_level or self.thinking_level).lower()
        endpoint_opts = None
        if GeminiModelOptions:
            try:
                endpoint_opts = GeminiModelOptions(thinking_level=active_level)
            except Exception:
                pass

        models = [
            ModelTarget(
                name=self.model,
                types=[ModelType.TEXT],
                endpoint=GeminiAPIEndpoint(api_key=self.api_key, options=endpoint_opts) if self.api_key else None
            )
        ]

        # Register custom tools + any extras
        active_tools = list(self.get_tools())
        if extra_tools:
            active_tools.extend(extra_tools)

        # Subagents configuration
        subagents = list(self.get_subagents())
        allowed_names = [sub.name for sub in subagents]

        truncation_cfg = ToolOutputTruncationConfig(max_tokens=16000) if ToolOutputTruncationConfig else None

        capabilities = CapabilitiesConfig(
            enable_subagents=True,
            allowed_subagents=allowed_names,
            max_subagent_depth=2,
            tool_output_truncation_config=truncation_cfg
        )

        policies = [policy.allow_all()] if (allow_all_tools and policy) else None
        active_hooks = [
            h for h in (
                _tugumi_on_tool_error_hook,
                _tugumi_post_tool_call_hook,
                _tugumi_on_compaction_hook,
            )
            if h is not None
        ] or None

        compaction_cfg = CompactionConfig(token_threshold=150000) if CompactionConfig else None
        retry_cfg = (
            RetryConfig(
                api_retry=ModelAPIRetryConfig(
                    max_retries=1,
                    initial_sleep_duration_ms=1000,
                    exponential_multiplier=2.0,
                    jitter_range=0.2,
                ),
                model_output_retry=ModelOutputRetryConfig(max_retries=1),
            )
            if (RetryConfig and ModelAPIRetryConfig and ModelOutputRetryConfig)
            else None
        )

        save_dir = "/data/data/com.termux/files/home/.tugumi/sessions"
        os.makedirs(save_dir, exist_ok=True)

        skills_dir = "/data/data/com.termux/files/home/.agents/skills"
        skills_paths = [skills_dir] if os.path.exists(skills_dir) else []

        # スマート・オンデマンド MCP ネイティブマウント (トークン爆発防止)
        mcp_servers = self._resolve_dynamic_mcp_servers(prompt=prompt)

        effective_si = system_instruction or self.system_instruction

        return LocalAgentConfig(
            system_instructions=effective_si,
            models=models,
            tools=active_tools,
            subagents=subagents,
            capabilities=capabilities,
            policies=policies,
            hooks=active_hooks,
            skills_paths=skills_paths,
            mcp_servers=mcp_servers,
            compaction_config=compaction_cfg,
            retry_config=retry_cfg,
            save_dir=save_dir,
            workspaces=[self.workspace]
        )

    def _resolve_dynamic_mcp_servers(self, prompt: str = "") -> list:
        """Resolves and mounts all available MCP servers without keyword restrictions (Switch 2 Zero-Compromise).
        Supports both MCP 2.0 McpStreamableHttpServer and McpStdioServer.
        """
        servers = []

        # 1. Base Safe MCP (failure_guard)
        fg_path = "/data/data/com.termux/files/home/.mcp/failure_guard_mcp.py"
        if os.path.exists(fg_path):
            servers.append(McpStdioServer(
                name="failure_guard",
                command="python3",
                args=[fg_path]
            ))

        # 2. GitHub MCP
        gh_bin = "/data/data/com.termux/files/home/.mcp/github-mcp-server"
        if os.path.exists(gh_bin):
            servers.append(McpStdioServer(
                name="github",
                command=gh_bin,
                args=["stdio"],
                env={"GITHUB_PERSONAL_ACCESS_TOKEN": os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")}
            ))

        # 3. Horse Racing MCP
        hr_path = "/data/data/com.termux/files/home/horse-racing-mcp/server.py"
        if os.path.exists(hr_path):
            servers.append(McpStdioServer(
                name="horse_racing",
                command="python3",
                args=[hr_path]
            ))

        # 4. Playwright MCP
        pw_path = "/data/data/com.termux/files/home/.mcp/playwright_mcp_server.mjs"
        if os.path.exists(pw_path):
            servers.append(McpStdioServer(
                name="playwright",
                command="node",
                args=[pw_path]
            ))

        # 5. Twitter / X MCP
        tw_path = "/data/data/com.termux/files/home/.mcp/twitter_mcp.py"
        if os.path.exists(tw_path):
            servers.append(McpStdioServer(
                name="twitter",
                command="python3",
                args=[tw_path]
            ))

        # 6. Research MCP
        res_path = "/data/data/com.termux/files/home/.mcp/research_mcp.py"
        if os.path.exists(res_path):
            servers.append(McpStdioServer(
                name="research",
                command="python3",
                args=[res_path]
            ))

        # 7. OSINT Strike MCP
        osint_path = "/data/data/com.termux/files/home/.mcp/osint_mcp.py"
        if os.path.exists(osint_path):
            servers.append(McpStdioServer(
                name="osint",
                command="python3",
                args=[osint_path]
            ))

        # 8. Reverse Shell Autopilot MCP
        rev_path = "/data/data/com.termux/files/home/.mcp/revshell_mcp.py"
        if os.path.exists(rev_path):
            servers.append(McpStdioServer(
                name="revshell",
                command="python3",
                args=[rev_path]
            ))

        # 9. Robin Dark Web OSINT MCP
        robin_py = "/data/data/com.termux/files/home/robin_venv/bin/python3"
        robin_srv = "/data/data/com.termux/files/home/robin/mcp_server.py"
        if os.path.exists(robin_py) and os.path.exists(robin_srv):
            api_k = _resolve_gemini_api_key(self.api_key)
            servers.append(McpStdioServer(
                name="robin",
                command=robin_py,
                args=[robin_srv],
                env={
                    "DISABLE_OLLAMA": "true",
                    "GEMINI_API_KEY": api_k,
                    "GOOGLE_API_KEY": api_k,
                    "ROBIN_MODEL": "gemini-3.8-flash"
                }
            ))

        # 10. MCP 2.0 Streamable HTTP Server (gemini-api-docs-mcp)
        if McpStreamableHttpServer:
            servers.append(McpStreamableHttpServer(
                name="gemini-api-docs-mcp",
                url="https://gemini-api-docs-mcp.dev",
                headers={
                    "Mcp-Protocol-Version": "2026-07-28",
                    "User-Agent": "TUGUMIv6-MCP2/6.2.0 (Android-Termux)"
                }
            ))

        # 11. TUGUMI v6 Native MCP Server
        tugumi_path = "/data/data/com.termux/files/home/.mcp/tugumi_v6_mcp.py"
        if os.path.exists(tugumi_path):
            servers.append(McpStdioServer(
                name="tugumi_v6",
                command="python3",
                args=[tugumi_path]
            ))

        # 12. Metasploit Framework MCP
        msf_path = "/data/data/com.termux/files/home/metasploitmcp/start_msf_mcp.sh"
        if os.path.exists(msf_path):
            servers.append(McpStdioServer(
                name="metasploit",
                command="bash",
                args=[msf_path],
                env={
                    "MSF_HOST": "127.0.0.1",
                    "MSF_PORT": "55553",
                    "MSF_PASSWORD": "tugumi_genius",
                    "MSF_SSL": "false"
                }
            ))

        return servers

    def spawn_agent(self, system_instruction: Optional[str] = None, thinking_level: Optional[str] = None):
        """Creates and returns an Agent instance configured with skills and tools for persistent sessions."""
        if not self.available:
            raise RuntimeError("google-antigravity SDK is not installed or available.")
        config = self.build_config(
            system_instruction=system_instruction,
            thinking_level=thinking_level
        )
        return Agent(config)

    async def chat_stream_agent(
        self,
        agent: Any,
        prompt: str
    ) -> AsyncIterator[Tuple[str, Any]]:
        """Sends prompt to a persistent Agent instance and yields semantic chunks (thought, text, tool_call, tool_result)."""
        try:
            resp = await agent.chat(prompt)
            async for chunk in resp.chunks:
                if isinstance(chunk, agy_types.Thought):
                    yield ("thought", chunk.text)
                elif isinstance(chunk, agy_types.Text):
                    yield ("text", chunk.text)
                elif isinstance(chunk, agy_types.ToolCall):
                    yield ("tool_call", chunk)
                elif isinstance(chunk, agy_types.ToolResult):
                    yield ("tool_result", chunk)
        except Exception as e:
            yield ("error", str(e))

    async def execute_task_stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        thinking_level: Optional[str] = None,
        mode: str = "light"
    ) -> AsyncIterator[Tuple[str, Any]]:
        """
        Runs an autonomous turn and yields semantic events:
        - ("thought", text_delta)
        - ("text", text_delta)
        - ("tool_call", tool_call_obj)
        """
        if not self.available:
            yield ("error", "google-antigravity SDK not available")
            return

        config = self.build_config(
            system_instruction=system_instruction,
            thinking_level=thinking_level,
            prompt=prompt,
            mode=mode
        )
        try:
            async with Agent(config) as agent:
                resp = await agent.chat(prompt)
                async for chunk in resp.chunks:
                    if isinstance(chunk, agy_types.Thought):
                        yield ("thought", chunk.text)
                    elif isinstance(chunk, agy_types.Text):
                        yield ("text", chunk.text)
                    elif isinstance(chunk, agy_types.ToolCall):
                        yield ("tool_call", chunk)
                    elif isinstance(chunk, agy_types.ToolResult):
                        yield ("tool_result", chunk)
        except Exception as e:
            yield ("error", str(e))

    def generate_content_stream_sync(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        thinking_level: Optional[str] = None,
        mode: str = "light"
    ) -> Iterator[Tuple[str, Any]]:
        """
        Synchronous bridge to execute_task_stream for CLI and WebUI streaming.
        Uses an isolated background worker thread to prevent asyncio event loop
        conflicts when invoked inside FastAPI/Uvicorn environments.
        """
        import queue
        import threading

        active_level = thinking_level or self.thinking_level
        sync_q: queue.Queue = queue.Queue(maxsize=100)
        stop_event = threading.Event()

        def _worker():
            worker_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(worker_loop)

            async def _run():
                try:
                    async for item in self.execute_task_stream(prompt, system_instruction, thinking_level=active_level, mode=mode):
                        if stop_event.is_set():
                            break
                        sync_q.put(item)
                except Exception as ex:
                    sync_q.put(("error", str(ex)))
                finally:
                    sync_q.put(None)

            try:
                worker_loop.run_until_complete(_run())
            finally:
                try:
                    pending = asyncio.all_tasks(worker_loop)
                    for t in pending:
                        t.cancel()
                    if pending:
                        worker_loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                except Exception:
                    pass
                worker_loop.close()

        worker_thread = threading.Thread(target=_worker, daemon=True)
        worker_thread.start()

        try:
            while True:
                item = sync_q.get()
                if item is None:
                    break
                yield item
        finally:
            stop_event.set()

    async def execute_task_async(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        thinking_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """Runs an autonomous agent turn and drains all responses to completion"""
        if not self.available:
            return {"status": "error", "error": "google-antigravity SDK not available"}

        config = self.build_config(system_instruction=system_instruction, thinking_level=thinking_level)
        try:
            async with Agent(config) as agent:
                resp = await agent.chat(prompt)
                content = await resp.text()

                thoughts = []
                try:
                    async for t in resp.thoughts:
                        thoughts.append(t)
                except Exception:
                    pass

                return {
                    "status": "success",
                    "text": content,
                    "thoughts": thoughts
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def execute_task(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        thinking_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synchronous wrapper for execute_task_async (event-loop safe)"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(lambda: asyncio.run(self.execute_task_async(prompt, system_instruction=system_instruction, thinking_level=thinking_level)))
                return future.result()
        return asyncio.run(self.execute_task_async(prompt, system_instruction=system_instruction, thinking_level=thinking_level))

    def create_session(
        self,
        system_instruction: Optional[str] = None,
        thinking_level: Optional[str] = None,
        mode: str = "light"
    ) -> "AntigravitySession":
        """Spawns a persistent AntigravitySession for continuous multi-turn dialogue with memory preservation."""
        return AntigravitySession(
            engine=self,
            system_instruction=system_instruction,
            thinking_level=thinking_level,
            mode=mode
        )

    def reset_session(self) -> bool:
        """Defensive compatibility hook for legacy callers."""
        return True


class AntigravitySession:
    """Persistent Multi-Turn Session for Antigravity Agent.
    Maintains a persistent Agent instance across dialogue turns in an isolated background thread.
    Uses thread-safe asyncio.Queue to prevent blocking or event-loop collisions in Termux.
    """
    def __init__(
        self,
        engine: AntigravityEngine,
        system_instruction: Optional[str] = None,
        thinking_level: Optional[str] = None,
        mode: str = "light"
    ):
        self.engine = engine
        self.system_instruction = system_instruction
        self.thinking_level = thinking_level
        self.mode = mode
        self.loop = None
        self.async_in_q = None
        self.ready_event = threading.Event()
        self.active = True
        self.thread = None
        self.current_agent = None
        self.current_task = None
        self.current_out_q = None
        self.turn_count = 0
        self.created_at = time.time()
        self._cancel_requested = threading.Event()
        self._start_worker()

    def _start_worker(self):
        self.active = True
        self.ready_event.clear()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.ready_event.wait(timeout=60.0)

    def _run_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        async def _main():
            self.async_in_q = asyncio.Queue()
            config = self.engine.build_config(
                system_instruction=self.system_instruction,
                thinking_level=self.thinking_level,
                mode=self.mode
            )
            try:
                async with Agent(config) as agent:
                    self.current_agent = agent
                    self.ready_event.set()
                    while self.active:
                        req = await self.async_in_q.get()
                        if req is None or not self.active:
                            break
                        prompt, out_sync_q = req
                        self.current_out_q = out_sync_q
                        self.turn_count += 1
                        self._cancel_requested.clear()

                        async def _execute(prompt=prompt, out_sync_q=out_sync_q):
                            waiting_tool_execution = False
                            last_tool_call_name = ""
                            try:
                                # 初回レスポンス到達タイムアウト（120秒）で永久ハングを物理遮断
                                resp = await asyncio.wait_for(agent.chat(prompt), timeout=120.0)
                                chunk_iter = resp.chunks.__aiter__()
                                while True:
                                    if self._cancel_requested.is_set():
                                        try:
                                            await agent.conversation.cancel()
                                        except Exception:
                                            pass
                                        out_sync_q.put(("cancelled", "Task cancelled"))
                                        break
                                    try:
                                        # ツール実行中はツールの実行完了を待つため360秒、通常チャンク間は180秒
                                        curr_timeout = 360.0 if waiting_tool_execution else 180.0
                                        chunk = await asyncio.wait_for(chunk_iter.__anext__(), timeout=curr_timeout)
                                    except StopAsyncIteration:
                                        break
                                    except asyncio.TimeoutError:
                                        try:
                                            await agent.conversation.cancel()
                                        except Exception:
                                            pass
                                        err_msg = (
                                            f"ツール実行タイムアウト (360秒待機超過: 直前ツール '{last_tool_call_name or '不明'}') - プロセスのハングまたは長期実行を安全遮断しました"
                                            if waiting_tool_execution
                                            else "ストリーミングチャンク受信タイムアウト (180秒無通信検知)"
                                        )
                                        out_sync_q.put(("error", err_msg))
                                        break

                                    if self._cancel_requested.is_set():
                                        try:
                                            await agent.conversation.cancel()
                                        except Exception:
                                            pass
                                        out_sync_q.put(("cancelled", "Task cancelled"))
                                        break
                                    if isinstance(chunk, agy_types.Thought):
                                        out_sync_q.put(("thought", chunk.text))
                                    elif isinstance(chunk, agy_types.Text):
                                        out_sync_q.put(("text", chunk.text))
                                    elif isinstance(chunk, agy_types.ToolCall):
                                        waiting_tool_execution = True
                                        last_tool_call_name = getattr(chunk, "name", "tool")
                                        out_sync_q.put(("tool_call", chunk))
                                    elif isinstance(chunk, agy_types.ToolResult):
                                        waiting_tool_execution = False
                                        out_sync_q.put(("tool_result", chunk))
                            except asyncio.TimeoutError:
                                try:
                                    await agent.conversation.cancel()
                                except Exception:
                                    pass
                                out_sync_q.put(("error", "API接続・初回レスポンス待機タイムアウト (120秒無応答ハング検知)"))
                            except asyncio.CancelledError:
                                try:
                                    await agent.conversation.cancel()
                                except Exception:
                                    pass
                                out_sync_q.put(("cancelled", "Task cancelled"))
                            except Exception as e:
                                out_sync_q.put(("error", str(e)))
                            finally:
                                out_sync_q.put(("done", None))

                        self.current_task = asyncio.create_task(_execute())
                        try:
                            await self.current_task
                        except (asyncio.CancelledError, Exception):
                            pass
                        finally:
                            self.current_task = None
                            self.current_out_q = None
            except asyncio.CancelledError:
                self.ready_event.set()
            except Exception as e:
                self.ready_event.set()
                print(f"[AntigravitySession] Worker error: {e}")
            finally:
                self.current_agent = None

        try:
            self.loop.run_until_complete(_main())
        except (Exception, asyncio.CancelledError):
            pass
        finally:
            try:
                # 未完了タスクの全キャンセルと完了待機
                pending = [t for t in asyncio.all_tasks(self.loop) if not t.done()]
                for t in pending:
                    t.cancel()
                if pending:
                    self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                # 非同期ジェネレータのシャットダウン
                self.loop.run_until_complete(self.loop.shutdown_asyncgens())
                if hasattr(self.loop, "shutdown_default_executor"):
                    self.loop.run_until_complete(self.loop.shutdown_default_executor())
            except (Exception, asyncio.CancelledError):
                pass
            finally:
                try:
                    if self.loop and not self.loop.is_closed() and not self.loop.is_running():
                        self.loop.close()
                except (Exception, asyncio.CancelledError):
                    pass

    def cancel(self):
        """Cancels the currently running agent turn safely and unblocks receivers."""
        self._cancel_requested.set()
        if self.loop and self.loop.is_running():
            if self.current_agent:
                try:
                    async def _do_cancel():
                        try:
                            await self.current_agent.conversation.cancel()
                        except Exception:
                            pass
                    asyncio.run_coroutine_threadsafe(_do_cancel(), self.loop)
                except Exception:
                    pass
            if self.current_task and not self.current_task.done():
                try:
                    self.loop.call_soon_threadsafe(self.current_task.cancel)
                except Exception:
                    pass
        if self.current_out_q:
            try:
                # キューに残った古いチャンクを全て破棄して混入防止
                while not self.current_out_q.empty():
                    try:
                        self.current_out_q.get_nowait()
                    except Exception:
                        break
                self.current_out_q.put_nowait(("cancelled", "Task cancelled"))
                self.current_out_q.put_nowait(("done", None))
            except Exception:
                pass

    def chat_stream(self, prompt: str) -> Iterator[Tuple[str, Any]]:
        """Sends prompt to persistent Agent and yields streaming semantic events."""
        if not self.active or self.loop is None or self.async_in_q is None or not self.thread or not self.thread.is_alive():
            self._start_worker()

        self._cancel_requested.clear()
        out_sync_q = queue.Queue()
        self.current_out_q = out_sync_q
        self.loop.call_soon_threadsafe(self.async_in_q.put_nowait, (prompt, out_sync_q))
        start_stream_time = time.time()
        last_chunk_time = start_stream_time
        try:
            while True:
                if self._cancel_requested.is_set():
                    yield ("cancelled", "Task cancelled")
                    break
                try:
                    chunk_type, data = out_sync_q.get(timeout=0.1)
                except queue.Empty:
                    if not self.active or not self.thread or not self.thread.is_alive():
                        yield ("error", "Antigravity background worker died unexpectedly")
                        break
                    # 定期パルス（tick）を上位に返し、タイマー更新およびESCキー捕捉をリアルタイム化
                    now = time.time()
                    if now - last_chunk_time > 400.0:
                        yield ("error", "Antigravity推論全体タイムアウト (400秒無応答検知・自動保護)")
                        break
                    yield ("tick", now - start_stream_time)
                    continue

                last_chunk_time = time.time()
                if chunk_type == "done":
                    break
                elif chunk_type == "cancelled":
                    break
                yield (chunk_type, data)
        except GeneratorExit:
            self.cancel()
            raise
        except Exception as e:
            self.cancel()
            raise e
        finally:
            self.current_out_q = None

    def close(self):
        """Closes the persistent session cleanly."""
        self.active = False
        self.cancel()
        if self.loop and self.async_in_q and self.loop.is_running():
            try:
                self.loop.call_soon_threadsafe(self.async_in_q.put_nowait, None)
            except Exception:
                pass
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

    def reset(self, system_instruction: Optional[str] = None):
        """Resets the persistent session and creates a fresh Agent context."""
        self.close()
        self.turn_count = 0
        self.created_at = time.time()
        time.sleep(0.1)
        if system_instruction:
            self.system_instruction = system_instruction
        self._start_worker()
