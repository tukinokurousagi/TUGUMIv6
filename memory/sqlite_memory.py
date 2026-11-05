# -*- coding: utf-8 -*-
"""
TUGUMIv6 SQLite Memory Core
- SQLite WAL (Write-Ahead Logging) Mode
- PRAGMA busy_timeout = 60000 (Deadlock-Free in Termux)
- Multithread-Safe with threading.RLock
- FTS5 Full-Text Search Integration
"""

import sqlite3
import threading
import json
import math
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

def compute_ebbinghaus_decay(
    last_accessed_str: str,
    access_count: int = 1,
    importance: int = 3,
    tier: str = "semantic",
    half_life_days: float = 30.0
) -> float:
    """エビングハウス忘却曲線に基づく記憶強度（0.0〜1.0）を計算"""
    if importance >= 5:
        # コアプロファイル・最重要規約は永久不滅（減衰なし）
        return 1.0

    try:
        # SQLite CURRENT_TIMESTAMP: "YYYY-MM-DD HH:MM:SS" または ISO8601
        clean_str = str(last_accessed_str).replace("T", " ")
        if "." in clean_str:
            clean_str = clean_str.split(".")[0]
        last_dt = datetime.strptime(clean_str[:19], "%Y-%m-%d %H:%M:%S")
        elapsed_days = max(0.0, (datetime.now() - last_dt).total_seconds() / 86400.0)
    except Exception:
        elapsed_days = 0.0

    tier_half_lives = {
        "working": 1.0,     # 短期作業（1日で減衰）
        "episodic": 14.0,   # エピソード（2週間）
        "procedural": 60.0, # 手続き・ワークフロー（2ヶ月）
        "semantic": 180.0   # 知識・事実（半年）
    }
    base_half_life = tier_half_lives.get(tier.lower(), half_life_days or 30.0)
    stability = base_half_life * (1.0 + 0.5 * math.log(1.0 + max(0, access_count))) * (0.6 + 0.2 * max(1, min(5, importance)))
    decay = math.exp(- elapsed_days / max(0.1, stability))
    return round(float(decay), 4)

class SQLiteMemory:
    """Thread-Safe WAL-Enabled SQLite Memory for TUGUMIv6"""
    def __init__(self, db_path: str = "/data/data/com.termux/files/home/TUGUMIv6/data/tugumi_memory.db"):
        self.db_path = db_path
        self.lock = threading.RLock()
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=60.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA busy_timeout = 60000;")
        return conn

    def _init_schema(self) -> None:
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 1. 会話・対話ログ
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT DEFAULT 'default',
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        mode TEXT DEFAULT 'light',
                        tokens_estimate INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                # 既存テーブルへのsession_idカラム追加（マイグレーション）
                try:
                    cursor.execute("ALTER TABLE conversation_logs ADD COLUMN session_id TEXT DEFAULT 'default';")
                except Exception:
                    pass
                # 1.5 チャットセッション・スレッド管理
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_sessions (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                # デフォルトセッション確保
                cursor.execute("""
                    INSERT OR IGNORE INTO chat_sessions (id, title) VALUES ('default', 'メインチャット');
                """)
                # 2. キーバリュー設定
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS kv_store (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                # 3. ナレッジ・FTS5
                cursor.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                        title,
                        content,
                        category,
                        source_path
                    );
                """)
                # 4. 長期・エピソード・構造化記憶（Cognitive Multi-Tier Memory）
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS structured_memories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tier TEXT DEFAULT 'semantic', -- 'working', 'episodic', 'semantic', 'procedural'
                        category TEXT NOT NULL, -- 'preference', 'directive', 'master_profile', 'decision', 'termux_env', 'project'
                        subject TEXT NOT NULL,
                        fact_content TEXT NOT NULL,
                        importance INTEGER DEFAULT 3, -- 1 (low) to 5 (critical)
                        access_count INTEGER DEFAULT 0,
                        last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        decay_score REAL DEFAULT 1.0,
                        decay_half_life_days REAL DEFAULT 30.0,
                        tags TEXT DEFAULT ''
                    );
                """)
                # 既存テーブルへの4-Tier・減衰カラム追加マイグレーション
                for col_name, col_type in [
                    ("tier", "TEXT DEFAULT 'semantic'"),
                    ("decay_score", "REAL DEFAULT 1.0"),
                    ("decay_half_life_days", "REAL DEFAULT 30.0"),
                    ("tags", "TEXT DEFAULT ''")
                ]:
                    try:
                        cursor.execute(f"ALTER TABLE structured_memories ADD COLUMN {col_name} {col_type};")
                    except Exception:
                        pass

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_memories_cat_imp 
                    ON structured_memories (category, importance DESC);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_memories_tier_decay 
                    ON structured_memories (tier, decay_score DESC);
                """)
                cursor.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                        subject,
                        fact_content,
                        category,
                        content=structured_memories,
                        content_rowid=id
                    );
                """)
                # FTS5 自動同期トリガー
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS trg_memories_ai AFTER INSERT ON structured_memories BEGIN
                        INSERT INTO memory_fts(rowid, subject, fact_content, category) 
                        VALUES (new.id, new.subject, new.fact_content, new.category);
                    END;
                """)
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS trg_memories_ad AFTER DELETE ON structured_memories BEGIN
                        INSERT INTO memory_fts(memory_fts, rowid, subject, fact_content, category) 
                        VALUES ('delete', old.id, old.subject, old.fact_content, old.category);
                    END;
                """)
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS trg_memories_au AFTER UPDATE ON structured_memories BEGIN
                        INSERT INTO memory_fts(memory_fts, rowid, subject, fact_content, category) 
                        VALUES ('delete', old.id, old.subject, old.fact_content, old.category);
                        INSERT INTO memory_fts(rowid, subject, fact_content, category) 
                        VALUES (new.id, new.subject, new.fact_content, new.category);
                    END;
                """)
                conn.commit()

    def create_session(self, session_id: Optional[str] = None, title: str = "新しい会話") -> str:
        """新規チャットセッション（スレッド）を作成"""
        import uuid
        sid = session_id or f"sess_{uuid.uuid4().hex[:8]}"
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO chat_sessions (id, title, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (sid, title))
                conn.commit()
                return sid

    def get_sessions(self) -> List[Dict[str, Any]]:
        """全チャットセッション（スレッド）を最新更新順に取得"""
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, title, created_at, updated_at
                    FROM chat_sessions
                    ORDER BY updated_at DESC
                """)
                rows = cursor.fetchall()
                if not rows:
                    # 空ならdefaultセッションを作成して返す
                    self.create_session("default", "メインチャット")
                    return [{"id": "default", "title": "メインチャット"}]
                return [dict(r) for r in rows]

    def get_session_messages(self, session_id: str = "default", limit: int = 50) -> List[Dict[str, Any]]:
        """指定セッション内の対話メッセージを古い順で取得"""
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT role, content, mode, session_id, created_at
                    FROM conversation_logs
                    WHERE session_id = ?
                    ORDER BY id DESC LIMIT ?
                """, (session_id, limit))
                rows = cursor.fetchall()
                return [dict(r) for r in reversed(rows)]

    def delete_session(self, session_id: str) -> int:
        """指定セッションの全メッセージおよびセッションレコードを物理削除"""
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM conversation_logs WHERE session_id = ?;", (session_id,))
                deleted = cursor.rowcount
                cursor.execute("DELETE FROM chat_sessions WHERE id = ?;", (session_id,))
                conn.commit()

                # 全スレッド消去時またはdefault消去時は、空のdefaultセッションを自動再生成して整合性を保護
                cursor.execute("SELECT COUNT(*) FROM chat_sessions;")
                cnt = cursor.fetchone()[0]
                if cnt == 0 or session_id == "default":
                    cursor.execute("INSERT OR IGNORE INTO chat_sessions (id, title) VALUES ('default', 'メインチャット');")
                    conn.commit()

                try:
                    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                except Exception:
                    pass
                return deleted

    def add_message(self, role: str, content: str, mode: str = "light", session_id: str = "default") -> int:
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # セッション確保
                cursor.execute("INSERT OR IGNORE INTO chat_sessions (id, title) VALUES (?, '新しい会話');", (session_id,))
                cursor.execute("""
                    INSERT INTO conversation_logs (session_id, role, content, mode, tokens_estimate)
                    VALUES (?, ?, ?, ?, ?)
                """, (session_id, role, content, mode, max(1, len(content) // 3)))
                msg_id = cursor.lastrowid

                # ユーザーの初回発言ならスレッドタイトルを発言先頭から自動生成
                if role == "user":
                    cursor.execute("SELECT COUNT(*) as cnt FROM conversation_logs WHERE session_id = ? AND role = 'user'", (session_id,))
                    u_cnt = cursor.fetchone()["cnt"]
                    if u_cnt <= 1:
                        auto_title = content.strip().split("\n")[0][:24]
                        if len(content.strip()) > 24:
                            auto_title += "..."
                        cursor.execute("UPDATE chat_sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (auto_title, session_id))
                    else:
                        cursor.execute("UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (session_id,))

                conn.commit()
                return msg_id

    def get_recent_messages(self, limit: int = 15, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if session_id:
                    cursor.execute("""
                        SELECT role, content, mode, session_id, created_at
                        FROM conversation_logs
                        WHERE session_id = ?
                        ORDER BY id DESC LIMIT ?
                    """, (session_id, limit))
                else:
                    cursor.execute("""
                        SELECT role, content, mode, session_id, created_at
                        FROM conversation_logs
                        ORDER BY id DESC LIMIT ?
                    """, (limit,))
                rows = cursor.fetchall()
                # 古い順に戻す
                return [dict(r) for r in reversed(rows)]

    def clear_conversation_history(self) -> int:
        """全会話履歴およびセッションを完全消去し、ディスクWALもトランケートする"""
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM conversation_logs;")
                deleted = cursor.rowcount
                cursor.execute("DELETE FROM chat_sessions;")
                cursor.execute("INSERT INTO chat_sessions (id, title) VALUES ('default', 'メインチャット');")
                try:
                    cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'conversation_logs';")
                except Exception:
                    pass
                conn.commit()
                try:
                    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                except Exception:
                    pass
                return deleted

    def index_knowledge(self, title: str, content: str, category: str = "doc", source_path: str = "") -> None:
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO knowledge_fts (title, content, category, source_path)
                    VALUES (?, ?, ?, ?)
                """, (title, content, category, source_path))
                conn.commit()

    def search_knowledge_fts(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        SELECT title, content, category, source_path, rank
                        FROM knowledge_fts
                        WHERE knowledge_fts MATCH ?
                        ORDER BY rank LIMIT ?
                    """, (query, limit))
                    rows = cursor.fetchall()
                    return [dict(r) for r in rows]
                except Exception:
                    # 記号などでMATCHエラー時の安全フォールバック
                    cursor.execute("""
                        SELECT title, content, category, source_path, 0 as rank
                        FROM knowledge_fts
                        WHERE content LIKE ?
                        LIMIT ?
                    """, (f"%{query}%", limit))
                    rows = cursor.fetchall()
                    return [dict(r) for r in rows]

    # ==================== Key-Value 設定ストア ====================
    def set_kv(self, key: str, value: Any) -> None:
        """KV設定を永続化（JSONシリアライズ）"""
        val_str = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO kv_store (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
                """, (key, val_str))
                conn.commit()

    def get_kv(self, key: str, default: Any = None) -> Any:
        """KV設定を取得"""
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM kv_store WHERE key = ?", (key,))
                row = cursor.fetchone()
                if not row:
                    return default
                val_str = row[0]
                try:
                    return json.loads(val_str)
                except Exception:
                    return val_str

    def delete_kv(self, key: str) -> bool:
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM kv_store WHERE key = ?", (key,))
                conn.commit()
                return cursor.rowcount > 0

    def list_kv(self) -> Dict[str, Any]:
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT key, value FROM kv_store ORDER BY key")
                result = {}
                for row in cursor.fetchall():
                    try:
                        result[row[0]] = json.loads(row[1])
                    except Exception:
                        result[row[0]] = row[1]
                return result

    # ==================== 構造化・長期・エピソード記憶 (4-Tier & Decay) ====================
    def add_memory(self, category: str, subject: str, fact_content: str, importance: int = 3, tier: str = "semantic", tags: str = "") -> int:
        """重要な事実・拓磨様の好み・決定事項・環境知識を4-Tier長期記憶に追加"""
        importance = max(1, min(5, importance))
        tier = tier if tier in ("working", "episodic", "semantic", "procedural") else "semantic"
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 既存の同一subject+categoryがあれば更新、なければ挿入
                cursor.execute("""
                    SELECT id FROM structured_memories
                    WHERE category = ? AND subject = ?
                """, (category, subject))
                existing = cursor.fetchone()
                if existing:
                    mem_id = existing[0]
                    cursor.execute("""
                        UPDATE structured_memories
                        SET fact_content = ?, importance = ?, tier = ?, tags = ?,
                            access_count = access_count + 1, last_accessed_at = CURRENT_TIMESTAMP, decay_score = 1.0
                        WHERE id = ?
                    """, (fact_content, importance, tier, tags, mem_id))
                    conn.commit()
                    return mem_id
                else:
                    cursor.execute("""
                        INSERT INTO structured_memories (category, subject, fact_content, importance, tier, tags, decay_score)
                        VALUES (?, ?, ?, ?, ?, ?, 1.0)
                    """, (category, subject, fact_content, importance, tier, tags))
                    conn.commit()
                    return cursor.lastrowid

    def remember(self, content: str, category: str = "fact", tier: str = "semantic", subject: Optional[str] = None, importance: int = 3, tags: Optional[List[str]] = None) -> int:
        """内容テキストから自動要約Subjectを生成し記憶を永続定着（MCP/エージェント標準）"""
        tag_str = ",".join(tags) if isinstance(tags, list) else (tags or "")
        if not subject:
            first_line = content.strip().split("\n")[0]
            clean_subject = re.sub(r"^[#\-\*\s]+", "", first_line)[:25].strip()
            subject = clean_subject or f"{category}_{tier}"
        return self.add_memory(
            category=category,
            subject=subject,
            fact_content=content,
            importance=importance,
            tier=tier,
            tags=tag_str
        )

    def get_memories(self, category: Optional[str] = None, tier: Optional[str] = None, limit: int = 15, min_importance: int = 1) -> List[Dict[str, Any]]:
        """カテゴリ・Tier・重要度順で記憶を取得"""
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                conditions = ["importance >= ?"]
                params: List[Any] = [min_importance]

                if category:
                    conditions.append("category = ?")
                    params.append(category)
                if tier:
                    conditions.append("tier = ?")
                    params.append(tier)

                where_clause = " AND ".join(conditions)
                params.append(limit)

                cursor.execute(f"""
                    SELECT id, category, subject, fact_content, importance, access_count, created_at, last_accessed_at,
                           tier, decay_score, decay_half_life_days, tags
                    FROM structured_memories
                    WHERE {where_clause}
                    ORDER BY importance DESC, last_accessed_at DESC LIMIT ?
                """, tuple(params))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]

    def get_tier_stats(self) -> Dict[str, Any]:
        """4-Tier別の件数、平均減衰スコア、統計サマリーを返却"""
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT tier, COUNT(*) as cnt, AVG(decay_score) as avg_decay, SUM(access_count) as total_acc
                    FROM structured_memories
                    GROUP BY tier
                """)
                rows = cursor.fetchall()
                tier_stats: Dict[str, Any] = {}
                for r in rows:
                    t_name = r["tier"] or "semantic"
                    tier_stats[t_name] = {
                        "count": r["cnt"],
                        "avg_decay": round(r["avg_decay"] or 1.0, 3),
                        "total_access": r["total_acc"] or 0
                    }
                cursor.execute("SELECT COUNT(*), AVG(decay_score), SUM(access_count) FROM structured_memories")
                total_row = cursor.fetchone()
                return {
                    "total_count": total_row[0] or 0,
                    "overall_avg_decay": round(total_row[1] or 1.0, 3),
                    "total_access_count": total_row[2] or 0,
                    "tiers": tier_stats
                }

    def search_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """FTS5およびLIKEフォールバックを用いた記憶のハイブリッド検索"""
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                rows = []
                # 1. まず FTS5 全文検索を試行
                try:
                    cursor.execute("""
                        SELECT m.id, m.category, m.subject, m.fact_content, m.importance, m.created_at,
                               m.tier, m.access_count, m.last_accessed_at, m.decay_score, m.decay_half_life_days, m.tags, f.rank
                        FROM memory_fts f
                        JOIN structured_memories m ON m.id = f.rowid
                        WHERE memory_fts MATCH ?
                        ORDER BY f.rank LIMIT ?
                    """, (query, limit))
                    rows = cursor.fetchall()
                except Exception:
                    rows = []

                # 2. 日本語単語境界等でFTS5が0件の場合はLIKE部分一致にフォールバック
                if not rows:
                    cursor.execute("""
                        SELECT id, category, subject, fact_content, importance, created_at,
                               tier, access_count, last_accessed_at, decay_score, decay_half_life_days, tags, 0.0 as rank
                        FROM structured_memories
                        WHERE subject LIKE ? OR fact_content LIKE ? OR tags LIKE ?
                        ORDER BY importance DESC, last_accessed_at DESC LIMIT ?
                    """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))
                    rows = cursor.fetchall()

                return [dict(r) for r in rows]

    def recall_similar(self, query: str, limit: int = 5, tier: Optional[str] = None, min_decay: float = 0.01) -> List[Dict[str, Any]]:
        """4-Tier & エビングハウス忘却曲線対応のハイブリッド想起（MCP/エージェント標準）"""
        candidates = self.search_memories(query=query, limit=max(limit * 3, 15))
        if not candidates:
            candidates = self.get_memories(limit=max(limit * 2, 10))

        scored_records = []
        for r in candidates:
            rec = dict(r)
            r_tier = rec.get("tier", "semantic") or "semantic"
            if tier and r_tier != tier:
                continue

            last_acc = rec.get("last_accessed_at", rec.get("created_at", ""))
            acc_cnt = rec.get("access_count", 0)
            imp = rec.get("importance", 3)
            h_life = rec.get("decay_half_life_days", 30.0)

            cur_decay = compute_ebbinghaus_decay(
                last_accessed_str=last_acc,
                access_count=acc_cnt,
                importance=imp,
                tier=r_tier,
                half_life_days=h_life
            )
            rec["decay_score"] = cur_decay
            if cur_decay < min_decay and imp < 5:
                continue

            rank_val = rec.get("rank")
            rank_score = 1.0 / (1.0 + abs(float(rank_val))) if rank_val is not None else 0.5
            hybrid_score = (rank_score * 0.4) + (cur_decay * 0.4) + ((imp / 5.0) * 0.2)
            rec["hybrid_score"] = round(hybrid_score, 4)
            scored_records.append(rec)

        scored_records.sort(key=lambda x: x.get("hybrid_score", 0.0), reverse=True)
        top_results = scored_records[:limit]

        # 想起された記憶をtouch（アクセス強化・定着）
        for item in top_results:
            if "id" in item:
                self.touch_memory(item["id"])
            item.setdefault("key", item.get("subject", ""))
            item.setdefault("value", item.get("fact_content", ""))

        return top_results

    def recall(self, query: str, limit: int = 5, tier: Optional[str] = None) -> List[Dict[str, Any]]:
        """Alias for recall_similar with backward-compatible key/value fields."""
        return self.recall_similar(query=query, limit=limit, tier=tier)

    def decay_all_memories(self) -> int:
        """全記憶のエビングハウス減衰スコアを一括再計算して更新"""
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, last_accessed_at, access_count, importance, tier, decay_half_life_days FROM structured_memories")
                rows = cursor.fetchall()
                updated_count = 0
                for row in rows:
                    decay = compute_ebbinghaus_decay(
                        last_accessed_str=row["last_accessed_at"],
                        access_count=row["access_count"],
                        importance=row["importance"],
                        tier=row["tier"] or "semantic",
                        half_life_days=row["decay_half_life_days"] or 30.0
                    )
                    cursor.execute("UPDATE structured_memories SET decay_score = ? WHERE id = ?", (decay, row["id"]))
                    updated_count += 1
                conn.commit()
                return updated_count

    def touch_memory(self, memory_id: int) -> None:
        """記憶の参照カウンタとタイムスタンプを更新し、減衰スコアを1.0に再ブースト"""
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE structured_memories
                    SET access_count = access_count + 1, last_accessed_at = CURRENT_TIMESTAMP, decay_score = 1.0
                    WHERE id = ?
                """, (memory_id,))
                conn.commit()

    def delete_memory(self, memory_id: int) -> bool:
        """記憶をID指定で削除"""
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM structured_memories WHERE id = ?", (memory_id,))
                conn.commit()
                return cursor.rowcount > 0

    def delete_knowledge(self, doc_id: int) -> bool:
        """FTS5ナレッジ知識をrowid指定で削除"""
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM knowledge_fts WHERE rowid = ?", (doc_id,))
                conn.commit()
                return cursor.rowcount > 0

    def format_memory_context(self, query: str = "", max_chars: int = 2500) -> str:
        """プロンプトに注入する高密度な記憶コンテキストを生成"""
        lines = []
        
        # 1. 最重要コアディレクティブ・拓磨様プロファイル (importance >= 4)
        core_memories = self.get_memories(min_importance=4, limit=10)
        if core_memories:
            lines.append("【拓磨様の重要設定・絶対方針・コア記憶】")
            for m in core_memories:
                lines.append(f"- [{m['category']}] {m['subject']}: {m['fact_content']}")

        # 2. クエリに関連する記憶検索 (FTS5)
        if query:
            search_results = self.search_memories(query, limit=5)
            relevant = [m for m in search_results if m['id'] not in [c['id'] for c in core_memories]]
            if relevant:
                lines.append("【関連する過去記憶・コンテキスト】")
                for m in relevant:
                    lines.append(f"- ({m['category']}) {m['subject']}: {m['fact_content']}")

        full_text = "\n".join(lines)
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars] + "\n...(一部記憶省略)"
        return full_text

    # ==================== データベース保守・健全化 ====================
    def optimize_db(self) -> Dict[str, Any]:
        """WALチェックポイント、インデックス最適化、整合性検証を実行"""
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check;")
                integrity = cursor.fetchone()[0]
                cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                chk = cursor.fetchall()
                cursor.execute("PRAGMA optimize;")
                return {
                    "status": "optimized",
                    "integrity": integrity,
                    "wal_checkpoint": [tuple(r) for r in chk] if chk else "ok",
                    "db_path": self.db_path
                }
