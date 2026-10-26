# -*- coding: utf-8 -*-
"""
TUGUMIv6 Learning Graph
- Knowledge Graph representation (Entities & Relations)
- Dynamic concept linking and learning from interactions
"""

import sqlite3
import json
from typing import List, Dict, Any

class LearningGraph:
    """Dynamic Knowledge & Concept Graph Store"""
    def __init__(self, db_path: str = "/data/data/com.termux/files/home/TUGUMIv6/data/tugumi_memory.db"):
        self.db_path = db_path
        self._init_schema()

    def _init_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA busy_timeout = 60000;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS graph_nodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_name TEXT UNIQUE NOT NULL,
                    category TEXT NOT NULL,
                    attributes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS graph_edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_entity TEXT NOT NULL,
                    target_entity TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

    def add_node(self, name: str, category: str = "concept", attributes: Dict[str, Any] = None) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA busy_timeout = 60000;")
            conn.execute("""
                INSERT OR REPLACE INTO graph_nodes (entity_name, category, attributes)
                VALUES (?, ?, ?)
            """, (name, category, json.dumps(attributes or {}, ensure_ascii=False)))
            conn.commit()

    def add_edge(self, source: str, target: str, relation: str, weight: float = 1.0) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA busy_timeout = 60000;")
            conn.execute("""
                INSERT INTO graph_edges (source_entity, target_entity, relation, weight)
                VALUES (?, ?, ?, ?)
            """, (source, target, relation, weight))
            conn.commit()

    def query_related(self, entity: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT target_entity, relation, weight FROM graph_edges
                WHERE source_entity = ?
                UNION
                SELECT source_entity as target_entity, relation, weight FROM graph_edges
                WHERE target_entity = ?
            """, (entity, entity))
            return [dict(r) for r in cur.fetchall()]
