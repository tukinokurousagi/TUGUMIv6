# -*- coding: utf-8 -*-
"""
TUGUMIv6 MCP 2.0 Client Interface (2026 SOTA)
- Stateless & Dynamic Tools Integration
- Deep Integration with MCP20Engine (2026-07-28 Spec)
- Tasks Extension & Apps UI Component Support
"""

import os
from typing import List, Dict, Any

class MCPClient:
    """MCP 2.0 Client Interface (Stateless & Dynamic Tools)"""
    def __init__(self, mcp_config_dir: str = "/data/data/com.termux/files/home/.gemini/antigravity-cli/mcp"):
        self.mcp_config_dir = mcp_config_dir
        self.available_servers: List[str] = self._discover_servers()

    def _discover_servers(self) -> List[str]:
        servers = set()
        if os.path.exists(self.mcp_config_dir):
            try:
                for d in os.listdir(self.mcp_config_dir):
                    if os.path.isdir(os.path.join(self.mcp_config_dir, d)):
                        servers.add(d)
            except Exception:
                pass
        
        # Merge with active servers from tugumi_mcp
        try:
            from tools.tugumi_mcp import mcp
            for s in mcp.list_servers():
                servers.add(s)
        except Exception:
            pass

        return sorted(list(servers))

    def get_available_servers(self) -> List[str]:
        return self._discover_servers()

    def call(self, server_name: str, tool_name: str, **kwargs) -> Any:
        from tools.tugumi_mcp import mcp
        return mcp.call(server_name, tool_name, **kwargs)

    def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        from tools.tugumi_mcp import mcp
        return mcp.list_tools(server_name)

    def list_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """Returns all tools across all configured MCP 2.0 servers."""
        from tools.tugumi_mcp import mcp
        return mcp.list_all_tools()

    def start_task(self, server_name: str, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Starts an asynchronous long-running task via MCP 2.0 Tasks Extension."""
        from tools.tugumi_mcp import mcp
        return mcp.start_task(server_name, tool_name, **kwargs)

    def task_status(self, server_name: str, task_id: str) -> Dict[str, Any]:
        """Queries status of an ongoing or completed task via MCP 2.0 Tasks Extension."""
        from tools.tugumi_mcp import mcp
        return mcp.task_status(server_name, task_id)

    def cancel_task(self, server_name: str, task_id: str) -> Dict[str, Any]:
        """Cancels an ongoing asynchronous task via MCP 2.0 Tasks Extension."""
        from tools.tugumi_mcp import mcp
        return mcp.cancel_task(server_name, task_id)

    def render_app(self, server_name: str, app_name: str, **kwargs) -> Dict[str, Any]:
        """Renders a UI component view via MCP 2.0 Apps Extension."""
        from tools.tugumi_mcp import mcp
        return mcp.render_app(server_name, app_name, **kwargs)

    def get_negotiated_version(self, server_name: str) -> str:
        """Returns the negotiated MCP protocol version for the server."""
        from tools.tugumi_mcp import mcp
        return mcp.get_negotiated_version(server_name)

    def __getattr__(self, name: str):
        """Dynamic proxy for direct syntax: mcp_client.<server>.<tool>(**kwargs)"""
        from tools.tugumi_mcp import mcp
        return getattr(mcp, name)
