# -*- coding: utf-8 -*-
"""
TUGUMIv6 TUGUMIDesk Storage Synchronizer (規約第4章純化プロトコル完全準拠)
- TUGUMIDesk純化原則: 内部DB/キャッシュ/ログのDesk同期を永久廃止
- 成果物・閲覧専用化: ~/.agents/TSUGUMI_MEMORY.md を /storage/emulated/0/TUGUMIDesk/Agent設定ファイル/ に複製同期
"""

import os
import shutil
import time
from typing import Dict, Any

class DeskSync:
    """External Storage Synchronizer for TUGUMIv6 (Purified Edition)"""
    def __init__(
        self,
        local_memory_file: str = "/data/data/com.termux/files/home/.agents/TSUGUMI_MEMORY.md",
        desk_agent_config_dir: str = "/storage/emulated/0/TUGUMIDesk/Agent設定ファイル"
    ):
        self.local_memory_file = os.path.expanduser(local_memory_file)
        self.desk_agent_config_dir = desk_agent_config_dir
        if not os.path.exists("/storage/emulated/0/TUGUMIDesk"):
            self.desk_agent_config_dir = os.path.expanduser("~/TUGUMIDesk/Agent設定ファイル")

    def sync_to_desk(self) -> Dict[str, Any]:
        """規約第4章に準拠し、TSUGUMI_MEMORY.mdを閲覧用フォルダへ複製保存"""
        if not os.path.exists(self.desk_agent_config_dir):
            try:
                os.makedirs(self.desk_agent_config_dir, exist_ok=True)
            except Exception as e:
                return {"status": "error", "message": f"Cannot create desk config dir: {e}"}

        synced_files = []
        if os.path.exists(self.local_memory_file):
            dst = os.path.join(self.desk_agent_config_dir, "TSUGUMI_MEMORY.md")
            try:
                shutil.copy2(self.local_memory_file, dst)
                synced_files.append("TSUGUMI_MEMORY.md")
            except Exception as e:
                print(f"[DeskSync] Error syncing TSUGUMI_MEMORY.md: {e}")

        return {
            "status": "success",
            "synced_count": len(synced_files),
            "files": synced_files,
            "destination": self.desk_agent_config_dir,
            "timestamp": time.time(),
            "policy": "Purified: Artifacts and TSUGUMI_MEMORY only"
        }
