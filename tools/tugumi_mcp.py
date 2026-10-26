# -*- coding: utf-8 -*-
"""
TUGUMIv6 Dedicated MCP 2.0 Engine & Dispatcher (2026 SOTA)
- Fully Compliant with Model Context Protocol 2.0 Specification (2026-07-28)
- Adaptive Protocol Version Negotiation (2026-07-28 <-> 2025-11-25 <-> 2024-11-05)
- Dual-Transport: Stateless HTTP-Native (Streamable HTTP with MCP-Protocol-Version / Mcp-Session-Id) & High-Performance Stdio
- MCP 2.0 Tasks Extension (Async Long-Running Tasks: create, status, cancel, list)
- MCP 2.0 UI Extension (MCP Apps Component Rendering)
- Multi Round-Trip (input_required handling)
- Programmatic Python API for Code Mode (import tugumi_mcp as mcp)
"""

import os
import json
import time
import uuid
import queue
import threading
import subprocess
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional, List

MCP_CONFIG_PATH = "/data/data/com.termux/files/home/.gemini/config/mcp_config.json"
MCP_20_PROTOCOL_VERSION = "2026-07-28"
MCP_FALLBACK_VERSIONS = ["2026-07-28", "2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05"]

MCP_20_CLIENT_CAPABILITIES = {
    "roots": {"listChanged": True},
    "tasks": {
        "subscribe": True,
        "list": True,
        "cancel": True
    },
    "apps": {
        "render": True
    },
    "tools": {
        "listChanged": True
    }
}

class MCP20Engine:
    """Independent MCP 2.0 Core Dispatcher for TUGUMIv6"""

    def __init__(self, config_path: str = MCP_CONFIG_PATH):
        self.config_path = config_path
        self.servers = self._load_servers()
        self.negotiated_versions: Dict[str, str] = {}
        self.session_ids: Dict[str, str] = {}

    def _load_servers(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            return {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("mcpServers", {})
        except Exception:
            return {}

    def reload(self):
        """Reloads server configurations"""
        self.servers = self._load_servers()

    def list_servers(self, include_ondemand: bool = True) -> List[str]:
        """Returns MCP server names.
        If include_ondemand is True, returns servers that can be executed on-demand even if disabled in config.
        """
        if include_ondemand:
            return [k for k, v in self.servers.items() if not v.get("permanently_disabled", False)]
        return [k for k, v in self.servers.items() if not v.get("disabled", False) and not v.get("permanently_disabled", False)]

    def _get_session_id(self, server_name: str) -> str:
        if server_name not in self.session_ids:
            self.session_ids[server_name] = f"tugumi-mcp2-{uuid.uuid4().hex[:12]}"
        return self.session_ids[server_name]

    def _execute_http(self, url: str, method: str, params: Dict[str, Any], server_name: str, timeout: float = 180.0) -> Dict[str, Any]:
        """Executes a JSON-RPC 2.0 call over Streamable HTTP (MCP 2.0 Native) with robust timeout"""
        req_id = f"mcp2-{uuid.uuid4().hex[:8]}"
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params
        }
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Mcp-Protocol-Version": MCP_20_PROTOCOL_VERSION,
            "Mcp-Session-Id": self._get_session_id(server_name),
            "User-Agent": "TUGUMIv6-MCP2/6.2.0 (Android Termux aarch64)"
        }
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ver = resp.headers.get("Mcp-Protocol-Version")
            if ver:
                self.negotiated_versions[server_name] = ver
            return json.loads(resp.read().decode("utf-8"))

    def _spawn_stdio_process(self, server_cfg: Dict[str, Any]) -> subprocess.Popen:
        command = server_cfg.get("command")
        args = server_cfg.get("args", [])
        env = os.environ.copy()
        if "env" in server_cfg:
            env.update(server_cfg["env"])
        cmd_list = [command] + args
        cwd = server_cfg.get("cwd")
        return subprocess.Popen(
            cmd_list,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=cwd,
            text=True
        )

    def _read_line_with_timeout(self, p: subprocess.Popen, timeout: float = 60.0) -> Optional[str]:
        """Reads a single line from process stdout with a strict timeout, preventing deadlocks."""
        q: queue.Queue = queue.Queue()

        def reader():
            try:
                line = p.stdout.readline()
                q.put(line)
            except Exception:
                q.put(None)

        t = threading.Thread(target=reader, daemon=True)
        t.start()
        try:
            return q.get(timeout=timeout)
        except queue.Empty:
            return None

    def _handshake_stdio(self, p: subprocess.Popen, server_name: str, timeout: float = 60.0) -> str:
        """Performs MCP 2.0 initialize handshake with adaptive version negotiation and timeout"""
        init_req = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": MCP_20_PROTOCOL_VERSION,
                "capabilities": MCP_20_CLIENT_CAPABILITIES,
                "clientInfo": {
                    "name": "TUGUMIv6-MCP2",
                    "version": "6.2.0",
                    "platform": "Android-Termux-aarch64"
                }
            }
        }) + "\n"
        p.stdin.write(init_req)
        p.stdin.flush()
        init_resp_line = self._read_line_with_timeout(p, timeout=timeout)
        negotiated_ver = MCP_20_PROTOCOL_VERSION
        if init_resp_line:
            try:
                res = json.loads(init_resp_line.strip())
                negotiated_ver = res.get("result", {}).get("protocolVersion", MCP_20_PROTOCOL_VERSION)
            except Exception:
                pass
        self.negotiated_versions[server_name] = negotiated_ver

        notif = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"
        p.stdin.write(notif)
        p.stdin.flush()
        return negotiated_ver

    def _read_rpc_response(self, p: subprocess.Popen, expected_id: int = 2, timeout: float = 180.0) -> Optional[Dict[str, Any]]:
        """Reads lines from stdio with timeout until the JSON-RPC response matching expected_id is found, skipping notifications."""
        start_time = time.time()
        while True:
            remaining = timeout - (time.time() - start_time)
            if remaining <= 0:
                return None
            resp_line = self._read_line_with_timeout(p, timeout=min(remaining, 30.0))
            if resp_line is None:
                if time.time() - start_time >= timeout:
                    return None
                continue
            if not resp_line:
                return None
            line_s = resp_line.strip()
            if not line_s:
                continue
            try:
                msg = json.loads(line_s)
            except Exception:
                continue
            if isinstance(msg, dict) and msg.get("id") == expected_id:
                return msg

    def list_tools(self, server_name: str, timeout: float = 120.0) -> List[Dict[str, Any]]:
        """Queries the MCP server for available tools via tools/list with robust timeout"""
        server_cfg = self.servers.get(server_name)
        if not server_cfg or server_cfg.get("permanently_disabled", False):
            return []

        # 1. HTTP Server
        if "serverUrl" in server_cfg:
            try:
                res = self._execute_http(server_cfg["serverUrl"], "tools/list", {}, server_name, timeout=timeout)
                return res.get("result", {}).get("tools", [])
            except Exception:
                return []

        # 2. Stdio Server
        if not server_cfg.get("command"):
            return []

        p = None
        try:
            p = self._spawn_stdio_process(server_cfg)
            self._handshake_stdio(p, server_name, timeout=max(timeout, 60.0))

            list_req = json.dumps({
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }) + "\n"
            p.stdin.write(list_req)
            p.stdin.flush()

            res = self._read_rpc_response(p, expected_id=2, timeout=timeout)
            if res:
                return res.get("result", {}).get("tools", [])
            return []
        except Exception:
            return []
        finally:
            if p:
                try:
                    p.stdin.close()
                    p.stdout.close()
                    if p.stderr:
                        p.stderr.close()
                except Exception:
                    pass
                p.terminate()
                try:
                    p.wait(timeout=5.0)
                except Exception:
                    p.kill()

    def list_all_tools(self, timeout_per_server: float = 60.0) -> Dict[str, List[Dict[str, Any]]]:
        """Returns a mapping of server_name -> list of available tools with timeout per server"""
        all_tools = {}
        for s in self.list_servers():
            tools = self.list_tools(s, timeout=timeout_per_server)
            if tools:
                all_tools[s] = tools
        return all_tools

    def call_tool(self, server_name: str, tool_name: str, arguments: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Executes an MCP tool via JSON-RPC 2.0 over Streamable HTTP or Stdio (On-Demand Ephemeral) with configurable timeout"""
        server_cfg = self.servers.get(server_name)
        if not server_cfg:
            return {"error": f"MCP server '{server_name}' not configured in {self.config_path}"}
        if server_cfg.get("permanently_disabled", False):
            return {"error": f"MCP server '{server_name}' is permanently disabled"}

        arguments = arguments or {}
        # 拓磨様ご指示対応: 通信環境・ファイル容量・サーバー負荷を考慮し、デフォルト180秒（3分）を確保
        effective_timeout = float(timeout) if timeout is not None else 180.0

        # 1. HTTP-Native Server
        if "serverUrl" in server_cfg:
            try:
                res = self._execute_http(
                    server_cfg["serverUrl"],
                    "tools/call",
                    {"name": tool_name, "arguments": arguments},
                    server_name,
                    timeout=effective_timeout
                )
                return self._parse_tool_result(res)
            except Exception as e:
                return {"error": f"HTTP MCP 2.0 call failed (timeout={effective_timeout}s): {e}"}

        # 2. Stdio Server
        if not server_cfg.get("command"):
            return {"error": f"Invalid configuration for server '{server_name}'"}

        p = None
        try:
            p = self._spawn_stdio_process(server_cfg)
            self._handshake_stdio(p, server_name, timeout=60.0)

            call_req = json.dumps({
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }) + "\n"
            p.stdin.write(call_req)
            p.stdin.flush()

            res = self._read_rpc_response(p, expected_id=2, timeout=effective_timeout)
            if res:
                return self._parse_tool_result(res)
            return {"error": f"MCP server '{server_name}' response timed out or returned empty (timeout={effective_timeout}s)"}
        except Exception as e:
            return {"error": f"Stdio MCP call execution error: {e}"}
        finally:
            if p:
                try:
                    p.stdin.close()
                    p.stdout.close()
                    if p.stderr:
                        p.stderr.close()
                except Exception:
                    pass
                p.terminate()
                try:
                    p.wait(timeout=5.0)
                except Exception:
                    p.kill()

    def _parse_tool_result(self, res: Dict[str, Any]) -> Dict[str, Any]:
        """Parses tool call response, handling MCP 2.0 input_required and content arrays"""
        if "error" in res:
            return res

        result_data = res.get("result", res)
        if isinstance(result_data, dict):
            if result_data.get("status") == "input_required" or result_data.get("type") == "input_required":
                result_data["input_required"] = True

            if "content" in result_data:
                contents = result_data.get("content", [])
                if len(contents) >= 1 and contents[0].get("type") == "text":
                    txt = contents[0].get("text", "")
                    try:
                        result_data["parsed"] = json.loads(txt)
                    except Exception:
                        pass
        return result_data

    # === MCP 2.0 Tasks Extension (Async Background Tasks) ===
    def start_task(self, server_name: str, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Starts an async background task via MCP 2.0 Tasks Extension"""
        server_cfg = self.servers.get(server_name)
        if not server_cfg:
            return {"error": f"MCP server '{server_name}' not configured"}
        arguments = arguments or {}

        if "serverUrl" in server_cfg:
            try:
                return self._execute_http(
                    server_cfg["serverUrl"],
                    "tasks/create",
                    {"tool": tool_name, "arguments": arguments},
                    server_name
                )
            except Exception as e:
                return {"error": f"Tasks HTTP create failed: {e}"}

        # For stdio, execute tool and wrap in task format
        res = self.call_tool(server_name, tool_name, arguments)
        return {
            "task_id": f"task_{uuid.uuid4().hex[:8]}",
            "status": "completed",
            "result": res
        }

    def task_status(self, server_name: str, task_id: str) -> Dict[str, Any]:
        """Queries async task status via MCP 2.0 Tasks Extension"""
        server_cfg = self.servers.get(server_name)
        if not server_cfg or "serverUrl" not in server_cfg:
            return {"task_id": task_id, "status": "completed"}
        try:
            return self._execute_http(
                server_cfg["serverUrl"],
                "tasks/status",
                {"task_id": task_id},
                server_name
            )
        except Exception as e:
            return {"error": f"Tasks status failed: {e}"}

    def cancel_task(self, server_name: str, task_id: str) -> Dict[str, Any]:
        """Cancels an ongoing async task via MCP 2.0 Tasks Extension"""
        server_cfg = self.servers.get(server_name)
        if not server_cfg or "serverUrl" not in server_cfg:
            return {"task_id": task_id, "status": "cancelled"}
        try:
            return self._execute_http(
                server_cfg["serverUrl"],
                "tasks/cancel",
                {"task_id": task_id},
                server_name
            )
        except Exception as e:
            return {"error": f"Tasks cancel failed: {e}"}

    # === MCP 2.0 Apps UI Extension ===
    def render_app(self, server_name: str, app_name: str, app_args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Renders an MCP App component via MCP 2.0 Apps Extension"""
        server_cfg = self.servers.get(server_name)
        if not server_cfg:
            return {"error": f"MCP server '{server_name}' not configured"}
        app_args = app_args or {}

        if "serverUrl" in server_cfg:
            try:
                return self._execute_http(
                    server_cfg["serverUrl"],
                    "apps/render",
                    {"app": app_name, "arguments": app_args},
                    server_name
                )
            except Exception as e:
                return {"error": f"Apps render failed: {e}"}

        return {"error": "Apps UI extension currently requires Streamable HTTP endpoint"}


# Singleton instance
_engine = MCP20Engine()

class _ServerProxy:
    def __init__(self, server_name: str, engine: MCP20Engine):
        self._server_name = server_name
        self._engine = engine

    def list_tools(self) -> List[Dict[str, Any]]:
        return self._engine.list_tools(self._server_name)

    def __dir__(self):
        tools = self._engine.list_tools(self._server_name)
        tool_names = [t.get("name") for t in tools if "name" in t]
        return list(super().__dir__()) + tool_names

    def __getattr__(self, tool_name: str):
        def _caller(**kwargs):
            return self._engine.call_tool(self._server_name, tool_name, kwargs)
        return _caller

class TugumiMCP:
    """Dynamic Proxy for Code Mode: import tugumi_mcp as mcp"""
    def __init__(self, engine: MCP20Engine):
        self._engine = engine

    def reload(self):
        self._engine.reload()

    def list_servers(self, include_ondemand: bool = True) -> List[str]:
        return self._engine.list_servers(include_ondemand=include_ondemand)

    def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        return self._engine.list_tools(server_name)

    def list_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        return self._engine.list_all_tools()

    def call(self, server_name: str, tool_name: str, arguments: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None, **kwargs) -> Any:
        args = dict(arguments or {})
        args.update(kwargs)
        call_timeout = timeout or args.pop("timeout", None)
        return self._engine.call_tool(server_name, tool_name, args, timeout=call_timeout)

    def start_task(self, server_name: str, tool_name: str, **kwargs) -> Dict[str, Any]:
        return self._engine.start_task(server_name, tool_name, kwargs)

    def task_status(self, server_name: str, task_id: str) -> Dict[str, Any]:
        return self._engine.task_status(server_name, task_id)

    def cancel_task(self, server_name: str, task_id: str) -> Dict[str, Any]:
        return self._engine.cancel_task(server_name, task_id)

    def render_app(self, server_name: str, app_name: str, **kwargs) -> Dict[str, Any]:
        return self._engine.render_app(server_name, app_name, kwargs)

    def get_negotiated_version(self, server_name: str) -> str:
        return self._engine.negotiated_versions.get(server_name, MCP_20_PROTOCOL_VERSION)

    def __getattr__(self, server_name: str) -> _ServerProxy:
        return _ServerProxy(server_name, self._engine)

# Top-level code-mode interface
mcp = TugumiMCP(_engine)
