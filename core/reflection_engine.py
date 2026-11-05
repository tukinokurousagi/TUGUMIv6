# -*- coding: utf-8 -*-
"""
TUGUMIv6 Reflection & Failure Guard Engine
- 5 Whys Root Cause Analysis Protocol
- SQLite FTS5 Failure Guard Table Integration
- Pre-execution Risk Verification & Lesson Recording
"""

import os
import re
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional


class ReflectionEngine:
    """5 Whys Self-Reflection & Failure Guard Engine (SQLite FTS5 Enabled)"""

    def __init__(self, db_path: str = "/data/data/com.termux/files/home/TUGUMIv6/data/tugumi_memory.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS failure_guard (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    cause TEXT NOT NULL,
                    forbidden_action TEXT NOT NULL,
                    correct_alternative TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            cols = {row[1] for row in conn.execute("PRAGMA table_info(failure_guard)").fetchall()}
            if "timestamp" not in cols:
                conn.execute("ALTER TABLE failure_guard ADD COLUMN timestamp TEXT DEFAULT ''")
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS failure_guard_fts USING fts5(
                    keyword,
                    cause,
                    forbidden_action,
                    correct_alternative,
                    content='failure_guard',
                    content_rowid='id'
                )
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS failure_guard_ai AFTER INSERT ON failure_guard BEGIN
                    INSERT INTO failure_guard_fts(rowid, keyword, cause, forbidden_action, correct_alternative)
                    VALUES (new.id, new.keyword, new.cause, new.forbidden_action, new.correct_alternative);
                END;
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS failure_guard_ad AFTER DELETE ON failure_guard BEGIN
                    INSERT INTO failure_guard_fts(failure_guard_fts, rowid, keyword, cause, forbidden_action, correct_alternative)
                    VALUES ('delete', old.id, old.keyword, old.cause, old.forbidden_action, old.correct_alternative);
                END;
            """)
            conn.commit()

    def record_failure(
        self,
        keyword: str,
        cause: str,
        forbidden_action: str,
        correct_alternative: str
    ) -> int:
        """Record a failure lesson into the Failure Guard database."""
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO failure_guard (keyword, cause, forbidden_action, correct_alternative, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (keyword, cause, forbidden_action, correct_alternative, now))
            conn.commit()
            return cursor.lastrowid or 0

    def check_risk(self, query: str) -> List[Dict[str, Any]]:
        """Query past failures before executing risky commands (FTS5 + Bidirectional Substring Matching)."""
        results: List[Dict[str, Any]] = []
        seen_ids = set()
        q = (query or "").strip()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if not q:
                cursor.execute("""
                    SELECT * FROM failure_guard
                    ORDER BY id DESC LIMIT 15
                """)
                for row in cursor.fetchall():
                    results.append(dict(row))
                return results

            # 1. FTS5 Full-Text Search
            fts_tokens = [re.sub(r'[^\w\u3040-\u30ff\u4e00-\u9fff\-]', '', tok) for tok in q.split()]
            fts_tokens = [t for t in fts_tokens if len(t) >= 2]
            if fts_tokens:
                fts_expr = " OR ".join(f'"{t}"' for t in fts_tokens[:6])
                try:
                    cursor.execute("""
                        SELECT fg.* FROM failure_guard fg
                        JOIN failure_guard_fts fts ON fg.id = fts.rowid
                        WHERE failure_guard_fts MATCH ?
                        ORDER BY rank LIMIT 10
                    """, (fts_expr,))
                    for row in cursor.fetchall():
                        d = dict(row)
                        seen_ids.add(d["id"])
                        results.append(d)
                except sqlite3.OperationalError:
                    pass

            # 2. Bidirectional LIKE matching (handles both short keyword queries and long task descriptions)
            like_q = f"%{q}%"
            cursor.execute("""
                SELECT * FROM failure_guard
                WHERE keyword LIKE ?
                   OR cause LIKE ?
                   OR forbidden_action LIKE ?
                   OR (LENGTH(keyword) >= 2 AND ? LIKE '%' || keyword || '%')
                ORDER BY id DESC LIMIT 10
            """, (like_q, like_q, like_q, q))
            for row in cursor.fetchall():
                d = dict(row)
                if d["id"] not in seen_ids:
                    seen_ids.add(d["id"])
                    results.append(d)

        return results[:10]

    def analyze_5_whys(self, error_message: str, context_details: str = "") -> Dict[str, Any]:
        """
        Perform a genuine 5-Whys Root Cause Analysis on an error/traceback and context.
        Extracts call stack locations, classifies failure mechanics, cross-references Failure Guard,
        and derives actionable structural countermeasures across all 5 causal layers.
        """
        err_text = (error_message or "Unknown Error").strip()
        ctx_text = (context_details or "").strip()
        combined = f"{err_text}\n{ctx_text}".strip()

        # 1. Stack trace & location extraction
        tb_matches = re.findall(r'File "([^"]+)", line (\d+), in ([^\n]+)', combined)
        affected_location: Optional[str] = None
        if tb_matches:
            last_file, last_line, last_func = tb_matches[-1]
            affected_location = f"{last_file}:{last_line} ({last_func.strip()})"
        else:
            loc_match = re.search(r'([\w./\-]+\.(?:py|sh|js|json)):(\d+)', combined)
            if loc_match:
                affected_location = f"{loc_match.group(1)}:{loc_match.group(2)}"

        # 2. Exception & Error Category Classification
        low = combined.lower()
        if any(k in low for k in ("syntaxerror", "indentationerror", "taberror")):
            category = "SYNTAX_OR_INDENTATION_ERROR"
            why2 = f"構文解析段階でAST構築に失敗（発生箇所: {affected_location or '対象スクリプト'}）。括弧不一致、インデント不整合、または未閉じ文字列が存在したため。"
            why3 = "ファイル編集・生成時に `py_compile` / `ruff check` による事前構文ゲートを通さずにコードが反映されたため。"
            why4 = "差分パッチ適用時の行境界またはインデント幅の検証が不十分であったため。"
            why5 = "【根本原因】編集直後の第1層（構文検証ゲート）および第2層（Ruff静的解析ゲート）の自動強制が不徹底であったこと。"
            recommended_fix = "対象箇所の括弧・インデントを修正し、`python3 -m py_compile` と `ruff check` でExit Code 0を確認する。"
        elif any(k in low for k in ("modulenotfounderror", "importerror", "no module named")):
            category = "MODULE_IMPORT_OR_PATH_ERROR"
            why2 = f"モジュール解決時に必要なパッケージまたは相対パスが見つからなかったため（箇所: {affected_location or 'import文'}）。"
            why3 = "`sys.path` へのワークスペースルート登録漏れ、仮想環境/Termux環境の差異、または循環インポートが発生したため。"
            why4 = "実行時のカレントディレクトリ（CWD）に依存したインポート設計になっていたため。"
            why5 = "【根本原因】絶対パス基準の `sys.path` 初期化と依存モジュール存在確認ガードの欠如。"
            recommended_fix = "プロジェクトルートを `sys.path` に追加し、必要なモジュール・シンボル名を実コードと照合して修正する。"
        elif any(k in low for k in ("attributeerror", "keyerror", "typeerror", "nameerror", "indexerror", "valueerror")):
            category = "DATA_CONTRACT_OR_TYPE_MISMATCH"
            why2 = f"オブジェクト属性・辞書キー・型シグネチャの不整合が発生したため（箇所: {affected_location or '実行ブロック'}）。"
            why3 = "呼び出し元と呼び出し先の間で返却データ構造（`dict` キー名・`None` 返却・引数定義）の契約（Contract）が乖離していたため。"
            why4 = "エッジケース（空配列、`None`、APIエラー応答時）の防御的境界チェック（`.get()` や `isinstance`）が不足していたため。"
            why5 = "【根本原因】モジュール間インターフェース仕様の実機検視不足と境界条件テストの欠落。"
            recommended_fix = "呼び出し先の実際のメソッド定義・返却キーを検視して一致させ、`.get()` 等による防御的フォールバックを追加する。"
        elif any(k in low for k in ("timeout", "timed out", "429", "503", "resource_exhausted", "connection", "urlerror")):
            category = "NETWORK_TIMEOUT_OR_QUOTA_EXHAUSTION"
            why2 = f"外部API通信またはサブプロセス実行が制限時間超過・レート制限に達したため（文脈: {ctx_text[:100] or '通信処理'}）。"
            why3 = "ブロッキングI/Oの長時間滞留、過剰なペイロード送信、または一時的なエンドポイント輻輳が発生したため。"
            why4 = "指数バックオフ（Exponential Backoff + Jitter）や軽量フォールバック経路への自動切替が機能しなかったため。"
            why5 = "【根本原因】タイムアウト上限設計およびサーキットブレーカー・リトライ制御の不足。"
            recommended_fix = "タイムアウト秒数の適正化、指数バックオフ付きリトライ、および軽量フォールバック経路を適用する。"
        elif any(k in low for k in ("sqlite3", "database is locked", "operationalerror", "integrityerror")):
            category = "DATABASE_CONCURRENCY_OR_SCHEMA_ERROR"
            why2 = f"SQLiteデータベース操作中にロック競合またはスキーマ不整合が発生したため（箇所: {affected_location or 'DB層'}）。"
            why3 = "複数スレッドからの同時書き込みや未マイグレーションのテーブル・カラム参照が行われたため。"
            why4 = "WALモード（`PRAGMA journal_mode=WAL`）・`busy_timeout` または `CREATE TABLE IF NOT EXISTS` 初期化が不足していたため。"
            why5 = "【根本原因】DB接続ライフサイクルとスキーマ整合性ガードの設計不備。"
            recommended_fix = "`PRAGMA journal_mode=WAL` と `timeout=30.0` を設定し、テーブル・FTS5スキーマの初期化順序を保証する。"
        elif any(k in low for k in ("permissionerror", "filenotfounderror", "noexec", "read-only", "errno")):
            category = "FILESYSTEM_OR_TERMUX_PERMISSION_ERROR"
            why2 = f"ファイルパス不在またはTermux/Androidストレージ権限・`noexec` 制限に抵触したため（箇所: {affected_location or 'I/O層'}）。"
            why3 = "`/bin/bash` 直書き、`/tmp` 直参照、または `/storage/emulated/0` 上での直接バイナリ実行を試みたため。"
            why4 = "親ディレクトリの事前作成（`os.makedirs(..., exist_ok=True)`）やTermux標準パス（`$PREFIX`, `$TMPDIR`, `$HOME`）への正規化が漏れていたため。"
            why5 = "【根本原因】Android Termux (Linux aarch64) 固有のファイルシステム制約に対する事前ガード不足。"
            recommended_fix = "`os.makedirs` で親ディレクトリを保証し、実行は `$HOME` 配下・一時領域は `$TMPDIR`・シバンはTermux標準を使用する。"
        else:
            category = "RUNTIME_EXECUTION_FAILURE"
            why2 = f"実行時例外または非ゼロ終了コードが発生（箇所: {affected_location or '実行パイプライン'} / 文脈: {ctx_text[:80] or '標準実行'}）。"
            why3 = "入力パラメータまたは環境状態が想定外の境界条件に入った際、適切な例外ハンドリングが行われなかったため。"
            why4 = "事前条件（Precondition）の検証と失敗時の自己修復ルーチンが組み込まれていなかったため。"
            why5 = "【根本原因】一次仕様の事前検視と5層検証ゲートによる動的テスト網羅性の不足。"
            recommended_fix = "コールスタックから発生源を特定し、入力検証と例外ハンドリングを追加した上で実機テストを実行する。"

        # 3. Cross-reference Failure Guard DB
        matched_guards = self.check_risk(f"{err_text} {ctx_text}"[:200])
        if matched_guards:
            top_guard = matched_guards[0]
            recommended_fix = f"{recommended_fix}（過去教訓 [{top_guard.get('keyword')}]: {top_guard.get('correct_alternative')}）"

        first_line = err_text.splitlines()[-1] if err_text.splitlines() else err_text
        why1 = f"表層事象: `{first_line[:200]}` が発生し処理が中断した（コンテキスト: {ctx_text[:120] if ctx_text else '通常実行'}）。"

        return {
            "error": err_text,
            "context": ctx_text,
            "error_category": category,
            "affected_location": affected_location,
            "why1": why1,
            "why2": why2,
            "why3": why3,
            "why4": why4,
            "why5": why5,
            "recommended_fix": recommended_fix,
            "matched_failure_guards": len(matched_guards),
            "summary": (
                f"[{category}] 5 Whys 根本原因分析完了: {why5} ➔ 対策: {recommended_fix}"
            ),
        }
