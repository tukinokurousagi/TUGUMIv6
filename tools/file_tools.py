# -*- coding: utf-8 -*-
"""
TUGUMIv6 File & MCP Tools
- Hierarchical File Operations & Tree Inspection
- MCP 2.0 Client Connector
"""

import os
import shutil
from typing import List, Dict, Any, Optional

class FileTools:
    """File & Directory Tree Management for TUGUMIv6"""
    def __init__(self, root_dir: str = "/data/data/com.termux/files/home"):
        self.root_dir = root_dir

    def list_tree(self, path: str, max_depth: int = 2) -> Dict[str, Any]:
        """ディレクトリツリーの構造化取得"""
        def _scan(curr_path: str, depth: int):
            if depth > max_depth or not os.path.exists(curr_path):
                return []
            items = []
            try:
                for entry in sorted(os.scandir(curr_path), key=lambda e: (not e.is_dir(), e.name)):
                    if entry.name.startswith((".", "__pycache__")):
                        continue
                    item = {"name": entry.name, "is_dir": entry.is_dir(), "path": entry.path}
                    if entry.is_dir():
                        item["children"] = _scan(entry.path, depth + 1)
                    items.append(item)
            except Exception:
                pass
            return items

        return {"root": path, "tree": _scan(path, 1)}

    def write_file_safe(self, target_path: str, content: str, make_backup: bool = False) -> bool:
        """安全なファイル書き込み（Workspace Sanitation準拠: 不要な.bakは自動生成しない）"""
        dir_name = os.path.dirname(target_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        if make_backup and os.path.exists(target_path):
            shutil.copy2(target_path, f"{target_path}.tmp_bak")
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True

    def sanitize_workspace(self, directory: Optional[str] = None) -> List[str]:
        """コードベース内の不要な .bak, .orig, *_temp* 等のゴミファイルを全自動クリーンアップ"""
        scan_dir = directory or self.root_dir
        cleaned = []
        if not os.path.exists(scan_dir):
            return cleaned

        junk_patterns = (".bak", ".orig", ".tmp_bak")
        for root, dirs, files in os.walk(scan_dir):
            if any(p in root for p in [".git", "node_modules", ".gemini"]):
                continue
            for f in files:
                if f.endswith(junk_patterns) or "_temp" in f:
                    file_path = os.path.join(root, f)
                    try:
                        os.remove(file_path)
                        cleaned.append(file_path)
                    except Exception:
                        pass
        return cleaned

class MCPClient:
    """MCP 2.0 Client Interface (Stateless & Dynamic Tools)"""
    def __init__(self, mcp_config_dir: str = "/data/data/com.termux/files/home/.gemini/antigravity-cli/mcp"):
        self.mcp_config_dir = mcp_config_dir
        self.available_servers: List[str] = self._discover_servers()

    def _discover_servers(self) -> List[str]:
        if not os.path.exists(self.mcp_config_dir):
            return []
        try:
            return [d for d in os.listdir(self.mcp_config_dir) if os.path.isdir(os.path.join(self.mcp_config_dir, d))]
        except Exception:
            return []

    def get_available_servers(self) -> List[str]:
        return self.available_servers
