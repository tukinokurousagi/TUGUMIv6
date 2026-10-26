# -*- coding: utf-8 -*-
"""
TUGUMIv6 Reflection Engine & Failure Guard
- Self-Reflection on Error or Correction (5 Whys Analysis)
- Root Cause Tracing & Preventive Action Derivation
- SQLite FTS5 Failure Guard Table Integration
- Pre-execution Risk Check
"""

import sqlite3
from typing import Dict, Any, List, Optional

class ReflectionEngine:
    """Self-Reflection, Root Cause Analyzer & Failure Guard Manager"""
    def __init__(self, db_path: str = "/data/data/com.termux/files/home/TUGUMIv6/data/tugumi_memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Failure Guard テーブル初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=60000;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS failure_guard (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    cause TEXT NOT NULL,
                    forbidden_action TEXT NOT NULL,
                    correct_alternative TEXT NOT NULL,
                    traceback TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

    def record_failure(
        self,
        keyword: str,
        cause: str,
        forbidden_action: str,
        correct_alternative: str,
        traceback_str: Optional[str] = None
    ) -> int:
        """失敗を内省し、二度と繰り返さないようFailure Guardへ記録"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA busy_timeout=60000;")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO failure_guard (keyword, cause, forbidden_action, correct_alternative, traceback)
                VALUES (?, ?, ?, ?, ?)
            """, (keyword, cause, forbidden_action, correct_alternative, traceback_str or ""))
            conn.commit()
            return cursor.lastrowid

    def check_risk(self, query: str) -> List[Dict[str, Any]]:
        """作業着手前のリスク照合 (過去の同一失敗・禁止事項の有無を検知)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM failure_guard
                WHERE keyword LIKE ? OR cause LIKE ? OR forbidden_action LIKE ?
                ORDER BY id DESC LIMIT 5
            """, (f"%{query}%", f"%{query}%", f"%{query}%"))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def analyze_5_whys(self, error_message: str, context_details: str = "") -> Dict[str, str]:
        """5 Whys による根本原因分析の論理フレームワーク生成"""
        # 第一原理思考に基づく原因分解
        analysis = {
            "symptom": error_message,
            "why1": f"なぜ起きたか: 実行時パラメータまたは環境制約との不一致 ({error_message[:60]})",
            "why2": "なぜ不一致だったか: 前提条件または事前チェックの欠落",
            "why3": "なぜ欠落したか: エビデンス照会（API実測/Dry-run）を行わず推測で進めたため",
            "root_cause": "推測による実行（Flailing）。一次ソースの確認と構文ゲートのスキップが主因",
            "countermeasure": "事前チェック（grep-first / check_risk）と実行後5層検証ゲートの絶対遵守"
        }
        return analysis
