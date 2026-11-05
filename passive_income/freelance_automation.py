# -*- coding: utf-8 -*-
"""
TUGUMIv6 Autonomous Freelance Proposal, Technical Architecture & Deliverable Pipeline
- Analyzes client requirements or technical specifications
- Generates architecture proposals, WBS estimates, and verification-ready deliverables
- Saves structured Markdown reports to TUGUMIDesk/副業・収益化/
"""

import os
import re
import time
from datetime import datetime
from typing import Dict, Any, Optional

from core.gemini_client import GeminiClient


class FreelanceAutomationEngine:
    """Autonomous Technical Proposal & Engineering Deliverable Generator"""

    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
        output_dir: str = "/storage/emulated/0/TUGUMIDesk/副業・収益化"
    ):
        self._client = gemini_client
        self.output_dir = output_dir
        try:
            os.makedirs(self.output_dir, exist_ok=True)
        except Exception:
            self.output_dir = "/data/data/com.termux/files/home/TUGUMIv6/data/freelance"
            os.makedirs(self.output_dir, exist_ok=True)

    @property
    def client(self) -> GeminiClient:
        if self._client is None:
            self._client = GeminiClient()
        return self._client

    def generate_proposal_and_spec(
        self,
        project_title: str,
        client_requirements: str,
        tech_stack: str = "Python 3.14 / FastAPI / Tailwind CSS / SQLite WAL"
    ) -> Dict[str, Any]:
        """Generate a comprehensive technical proposal, architecture blueprint, and WBS."""
        prompt = (
            f"あなたは最高峰のリードソフトウェアアーキテクト兼技術コンサルタントです。\n"
            f"以下の案件要件に対して、即座に受注・実装可能な技術提案書およびシステム設計仕様書（Markdown形式）を作成してください。\n\n"
            f"【案件名】: {project_title}\n"
            f"【クライアント要件】: {client_requirements}\n"
            f"【推奨技術スタック】: {tech_stack}\n\n"
            f"【必須構成】:\n"
            f"1. エグゼクティブサマリー（課題解決の核心と提供価値）\n"
            f"2. システムアーキテクチャ設計（Mermaid `flowchart TD` 図を含む）\n"
            f"3. モジュール分割とAPI/DBインターフェース定義\n"
            f"4. WBS（作業分解構成図）とマイルストーン計画\n"
            f"5. 品質保証・5層検証計画とセキュリティ対策\n"
        )
        content = self.client.generate_content(prompt=prompt)
        date_str = datetime.now().strftime("%Y%m%d")
        safe_title = re.sub(r'[\\/:*?"<>|\s]+', "_", project_title).strip("_")[:40] or "案件提案書"
        file_path = os.path.join(self.output_dir, f"技術提案書_{safe_title}_{date_str}.md")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "status": "success",
            "project_title": project_title,
            "file_path": file_path,
            "char_count": len(content),
            "timestamp": int(time.time()),
        }
