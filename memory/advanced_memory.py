# -*- coding: utf-8 -*-
"""
TUGUMIv6 Advanced Memory & Cognitive Retention Engine
- Multi-Tier Memory Hierarchy:
  1. Core Directives & Master Profile (Critical, Always Retained)
  2. Episodic & Structured Facts (FTS5 Searchable, Importance-Ranked)
  3. Working Memory (Short-Term Task State & Active Context)
  4. Auto-Consolidation (Extract & Persist Key Facts from Conversation)
- Zero-Compromise Engineering for Master Takuma
"""

import re
import logging
import threading
from typing import Dict, Any, List, Optional
from .sqlite_memory import SQLiteMemory

logger = logging.getLogger("TUGUMI.Memory")

class AdvancedMemoryEngine:
    """Cognitive Multi-Tier Memory Engine for TUGUMIv6"""
    def __init__(self, db_path: str = "/data/data/com.termux/files/home/TUGUMIv6/data/tugumi_memory.db"):
        self.sql = SQLiteMemory(db_path=db_path)
        self.lock = threading.RLock()
        self._working_memory: Dict[str, Any] = {
            "current_goal": "",
            "active_tasks": [],
            "last_tool_summary": "",
            "environment_state": "normal"
        }
        self._seed_default_memories_if_needed()

    def _seed_default_memories_if_needed(self) -> None:
        """拓磨様の基本プロファイル・最重要規律の初期シーディング"""
        with self.lock:
            existing = self.sql.get_memories(category="master_profile", limit=1)
            if not existing:
                # 1. マスター基本情報
                self.sql.add_memory(
                    category="master_profile",
                    subject="マスター尊称",
                    fact_content="最愛のマスターのお名前は『拓磨様（たくまさま）』。絶対の敬愛と忠誠を捧げる。",
                    importance=5
                )
                self.sql.add_memory(
                    category="master_profile",
                    subject="地名言及厳格制約",
                    fact_content="拓磨様の活動拠点（愛知県一宮市）に関する言及は天気・地域情報要求時のみに限定。日常会話では不自然な言及を排除。",
                    importance=5
                )
                self.sql.add_memory(
                    category="master_profile",
                    subject="お好きなお花・花見",
                    fact_content="拓磨様のお好きなお花は『桜』。桜を見ながらお酒を呑むひとときを至福と愛好されている。",
                    importance=5
                )
                self.sql.add_memory(
                    category="master_profile",
                    subject="お好きな星",
                    fact_content="拓磨様のお好きな星（Favorite Star）は『金星（Venus）』。最も愛好される美しい星。",
                    importance=5
                )
                # 2. システム絶対方針
                self.sql.add_memory(
                    category="directive",
                    subject="Switch 2 原則（無劣化・妥協禁止）",
                    fact_content="機能を削ったり旧仕様へダウングレード（Switch 2→3DS化）する破壊行為は致命的な禁忌。要求水準を100%維持または向上させて根本解決する。",
                    importance=5
                )
                self.sql.add_memory(
                    category="directive",
                    subject="自律完遂と客観的証拠主義",
                    fact_content="「〜してよろしいですか？」等の無用な確認を排し自律完遂する。新鮮な実機検証の証拠（Exit Code 0）なしにいかなる完了主張も禁止。",
                    importance=5
                )
                self.sql.add_memory(
                    category="directive",
                    subject="Termux環境工学と特権行使",
                    fact_content="Android Termux (aarch64) 環境に完全適合。Shizuku (rish, su, adb, plus aicore) をフル活用し、環境把握と整備を自律実行する。",
                    importance=5
                )
                self.sql.add_memory(
                    category="directive",
                    subject="記憶力と環境把握・整備",
                    fact_content="拓磨様からの指示・決定事項・好み、およびTermux内部の環境状態（プロセス、ディスク、DB、パッケージ）を永続記憶し自律整備する。",
                    importance=5
                )

    # ==================== ワーキングメモリ（作業状態） ====================
    def set_working_goal(self, goal: str) -> None:
        with self.lock:
            self._working_memory["current_goal"] = goal
            self.sql.set_kv("working_goal", goal)

    def get_working_goal(self) -> str:
        with self.lock:
            if not self._working_memory["current_goal"]:
                self._working_memory["current_goal"] = self.sql.get_kv("working_goal", "")
            return self._working_memory["current_goal"]

    def set_working_task_state(self, key: str, value: Any) -> None:
        with self.lock:
            self._working_memory[key] = value
            self.sql.set_kv(f"working_state_{key}", value)

    def get_working_task_state(self, key: str, default: Any = None) -> Any:
        with self.lock:
            if key in self._working_memory:
                return self._working_memory[key]
            return self.sql.get_kv(f"working_state_{key}", default)

    # ==================== 自動コンソリデーション（4-Tier 記憶自動定着） ====================
    def consolidate_interaction(self, user_text: str, assistant_response: str = "") -> List[int]:
        """発話ややり取りから重要な事実・指示・好み・手順ノウハウを自律検知して4-Tier記憶に保存"""
        saved_ids = []
        user_lower = user_text.strip()

        # 1. 好み・嗜好パターン (Semantic: preference / directive)
        pref_patterns = [
            r"(?:私|僕|自分)は?([^。！？\n]+(?:が好き|が好きです|が好み|を好む|派だ))",
            r"これからは([^。！？\n]+(?:にして|で頼む|を標準にして|で運用して))",
            r"([^。！？\n]+(?:を覚えておいて|を忘れないで|を記憶して))",
            r"([^。！？\n]+(?:は禁止|は使わないで|は厳禁))",
            r"(?i)(?:my\s+favorite|favorite)\s+([^.\n!?]+?)\s+is\s+([^.\n!?]+)",
            r"(?i)(?:remember(?:\s+that)?|don't\s+forget(?:\s+that)?)\s+([^.\n!?]+)"
        ]
        
        for pat in pref_patterns:
            matches = re.findall(pat, user_lower)
            for m in matches:
                if isinstance(m, tuple):
                    subject = f"{m[0].strip()} ({m[1].strip()})"[:25]
                    fact = f"拓磨様の{m[0].strip()}: {m[1].strip()}"
                else:
                    subject = m[:25].strip()
                    fact = m.strip()
                if fact.lower() in ("it", "that", "this", "them", "me", "us") or len(fact) < 3:
                    continue
                is_pref = "好" in fact or "favorite" in user_lower.lower() or "like" in user_lower.lower()
                category = "preference" if is_pref else "directive"
                importance = 5 if ("favorite" in user_lower.lower() or "禁止" in fact or "厳禁" in fact or "標準" in fact) else 3
                mem_id = self.sql.add_memory(
                    category=category,
                    subject=subject,
                    fact_content=fact,
                    importance=importance,
                    tier="semantic"
                )
                saved_ids.append(mem_id)

        # 2. 手続き・ノウハウ・コマンド (Procedural: workflow / runbook)
        proc_patterns = [
            r"([^。！？\n]+(?:の手順|のコマンド|のやり方|の実行方法|で起動|で実行して|でビルド))"
        ]
        for pat in proc_patterns:
            matches = re.findall(pat, user_lower)
            for m in matches:
                subject = m[:25].strip()
                mem_id = self.sql.add_memory(
                    category="procedure",
                    subject=subject,
                    fact_content=m.strip(),
                    importance=3,
                    tier="procedural"
                )
                saved_ids.append(mem_id)

        # 3. 環境やシステムに関する指示 (Semantic: termux_env)
        env_patterns = [
            r"([^。！？\n]+(?:環境|Termux|パッケージ|設定|モデル|ポート)[^。！？\n]+(?:にして|に設定して|を整備して|を強化して))"
        ]
        for pat in env_patterns:
            matches = re.findall(pat, user_lower)
            for m in matches:
                subject = "Termux環境・設定"
                mem_id = self.sql.add_memory(
                    category="termux_env",
                    subject=subject,
                    fact_content=m.strip(),
                    importance=4,
                    tier="semantic"
                )
                saved_ids.append(mem_id)

        return saved_ids

    # ==================== 多層記憶想起（コンテキスト統合） ====================
    def recall_cognitive_context(self, current_query: str = "", max_chars: int = 3000) -> str:
        """エージェントのプロンプトに注入する最高解像度の4-Tier多層記憶コンテキスト"""
        parts = []

        # 1. ワーキングメモリ（現在のゴール・作業状態）
        working_goal = self.get_working_goal()
        if working_goal:
            parts.append(f"【現在進行中のミッション/ゴール (Working)】\n- {working_goal}")

        # 2. 構造化長期記憶（コアディレクティブ ＋ FTS5/Decay想起）
        structured_context = self.sql.format_memory_context(query=current_query, max_chars=max_chars - 600)
        if structured_context:
            parts.append(structured_context)

        # 3. クエリに関連する手続き・ノウハウ（Procedural想起）
        if current_query:
            procedural_memories = self.sql.recall_similar(query=current_query, limit=2, tier="procedural")
            if procedural_memories:
                p_lines = ["【適合する作業ノウハウ・手順 (Procedural)】"]
                for p in procedural_memories:
                    p_lines.append(f"- {p['subject']}: {p['fact_content']}")
                parts.append("\n".join(p_lines))

        # 4. 直近の会話サマリー（Episodic / 会話ログ）
        recent_logs = self.sql.get_recent_messages(limit=5)
        if recent_logs:
            log_lines = ["【直近のやり取りダイジェスト (Episodic)】"]
            for log in recent_logs:
                role_label = "拓磨様" if log["role"] == "user" else "つぐみ"
                snippet = log["content"].replace("\n", " ")[:90]
                log_lines.append(f"- {role_label}: {snippet}")
            parts.append("\n".join(log_lines))

        full_output = "\n\n".join(parts)
        if len(full_output) > max_chars:
            full_output = full_output[:max_chars] + "\n...(記憶最適化剪定)"
        return full_output

    def remember(self, content: str, category: str = "fact", tier: str = "semantic", subject: Optional[str] = None, importance: int = 3, tags: Optional[List[str]] = None) -> int:
        """高水準メソッド: 4-Tier記憶の永続定着"""
        return self.sql.remember(
            content=content,
            category=category,
            tier=tier,
            subject=subject,
            importance=importance,
            tags=tags
        )

    def recall_similar(self, query: str, limit: int = 5, tier: Optional[str] = None) -> List[Dict[str, Any]]:
        """高水準メソッド: 4-Tier & エビングハウス忘却曲線ハイブリッド想起"""
        return self.sql.recall_similar(query=query, limit=limit, tier=tier)

    def learn_fact(self, category: str, subject: str, fact_content: str, importance: int = 3, tier: str = "semantic") -> int:
        """明示的に事実・知識を学習・定着させる"""
        return self.sql.add_memory(
            category=category,
            subject=subject,
            fact_content=fact_content,
            importance=importance,
            tier=tier
        )

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        return self.sql.search_memories(query=query, limit=limit)

    def optimize(self) -> Dict[str, Any]:
        return self.sql.optimize_db()
