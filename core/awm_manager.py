"""
TUGUMIv6 Agent Workflow Memory (AWM) Manager
- ICML 2025/2026 Agent Workflow Memory (AWM) & Skill Distillation Engine
- Multi-Tier Noise & Trash Filter: 些細なタスク、雑談、失敗軌跡、重複データの混入を物理遮断
- Pre-execution Guidance Injection: 過去の成功DAGを初手から先行ロードして推論を最短化
- Asynchronous Background Learner: メインチャット応答後に非同期スレッドで安全に学習
- Self-Cleaning Garbage Collection: 失敗・陳腐化したワークフローの自動パージ
"""

import logging
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

logger = logging.getLogger("TUGUMIv6.AWM")

# Add ~/.agents to path for clean AWM package access
AGENTS_DIR = os.path.expanduser("~/.agents")
if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)

try:
    from awm import AgentWorkflowMemory, MemoryDB, TugumiWorkflowLearner
    AWM_CORE_AVAILABLE = True
except ImportError:
    AWM_CORE_AVAILABLE = False
    MemoryDB = None
    AgentWorkflowMemory = None
    TugumiWorkflowLearner = None


def extract_clean_user_goal(raw_prompt: str) -> str:
    """
    CLI/WebUIのコンテキスト注入ラッパー（長期記憶・対話履歴・RAG・ヘッダー等）を除去し、
    拓磨様の純粋な最新指示テキストのみを抽出する。
    """
    text = (raw_prompt or "").strip()
    if not text:
        return ""

    # AWM蒸留プレフィックスの除去
    if text.startswith("Distill a reusable skill for the goal:"):
        text = text[len("Distill a reusable skill for the goal:"):].strip()

    # 1. WebUI形式: 「【最新指示】\n...」が末尾にある場合はそこだけ抽出
    if "【最新指示】" in text:
        text = text.split("【最新指示】")[-1].strip()

    # 2. CLI形式: 「【マスター拓磨様からの至上指示（最優先・完全遵守要件）】\n...」の先頭ヘッダー除去
    text = re.sub(
        r"^【マスター拓磨様からの至上指示[^】]*】\s*",
        "",
        text
    ).strip()

    # 3. 後続に結合されたRAG・対話履歴・長期記憶・実機測定ブロックを切り離す
    split_markers = (
        "\n\n【📚 参照RAGナレッジ",
        "\n\n【自律参照ナレッジベース",
        "\n\n【参考：直前対話履歴",
        "\n\n【過去対話コンテキスト",
        "\n\n【参考：関連長期記憶】",
        "\n\n【拓磨様の重要設定・絶対方針・コア記憶】",
        "\n\n【実機測定データ】",
    )
    for marker in split_markers:
        if marker in text:
            text = text.split(marker, 1)[0].strip()

    # 万一先頭に長期記憶ブロックだけが残っている場合のフォールバック除去
    if text.startswith("【拓磨様の重要設定・絶対方針・コア記憶】"):
        parts = re.split(r"\n{2,}【[^】]+】\n", text)
        if len(parts) > 1:
            text = parts[-1].strip()

    return text.strip()


class AWMManager:
    """TUGUMIv6 Native AWM & Skill Distillation Manager with Anti-Noise Protection"""
    def __init__(
        self,
        db_path: str = "/data/data/com.termux/files/home/tugumi_memory.db",
        gemini_client: Any = None,
        model: str = "gemini-3.8-flash"
    ):
        self.db_path = db_path
        self.gemini_client = gemini_client
        self.model = model
        self.enabled = AWM_CORE_AVAILABLE
        self.memory_db = None
        self.awm = None
        self.learner = None
        self.pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="TUGUMI_AWM")
        self.lock = threading.RLock()

        if self.enabled:
            try:
                self.memory_db = MemoryDB(db_path=self.db_path)
                self._init_engines()
            except Exception as e:
                logger.warning(f"[AWMManager] Failed to initialize MemoryDB: {e}")
                self.enabled = False

    def _init_engines(self):
        """MemoryDBが利用可能な場合に AWM & Learner を初期化 (Geminiクライアント未指定時もヒューリスティック/ガード動作可能)"""
        if not self.enabled or not self.memory_db:
            return
        client = getattr(self.gemini_client, "sdk_client", None) or self.gemini_client
        try:
            self.awm = AgentWorkflowMemory(
                memory_db=self.memory_db,
                gemini_client=client,
                model=self.model
            )
            self.learner = TugumiWorkflowLearner(
                memory_db=self.memory_db,
                gemini_client=client,
                model=self.model
            )
        except Exception as e:
            logger.warning(f"[AWMManager] Engine initialization failed: {e}")

    # =========================================================================
    # 1. 多層ノイズ・ゴミデータ蓄積防止フィルター (Multi-Tier Anti-Noise Guard)
    # =========================================================================
    def is_worth_learning(self, user_goal: str, steps: list[dict[str, Any]]) -> tuple[bool, str]:
        """
        実行軌跡が学習に値するか厳格に判定する多層防護ゲート
        - 些細なタスク、雑談、失敗ログ、空モックを物理遮断
        """
        # ゲート1: ラッパー除去後の空・極短ゴール判定
        goal_clean = extract_clean_user_goal(user_goal)
        if len(goal_clean) < 6:
            return False, "User goal is too short (< 6 chars)."

        # ゲート2: 雑談・定型挨拶ブラックリスト遮断
        trivial_phrases = [
            "ping", "hello", "hi", "こんにちは", "おはよう", "こんばんは",
            "ありがとう", "今何時", "天気", "test", "テスト", "status", "who are you"
        ]
        g_lower = goal_clean.lower()
        if any(g_lower == tp or g_lower.startswith(tp + " ") for tp in trivial_phrases):
            return False, f"User goal matches trivial conversation pattern: '{goal_clean}'."

        # ゲート3: 最小ステップ数チェック（ツール実行3回未満は些細タスクとして除外）
        if not steps or len(steps) < 3:
            return False, f"Step count ({len(steps) if steps else 0}) is under threshold (min 3 steps required)."

        # ゲート4: 全ステップ失敗チェック（エラーで中断した軌跡はゴミ化防止のため学習しない）
        success_steps = [s for s in steps if s.get("success", True) and not s.get("error")]
        if not success_steps:
            return False, "Trajectory contains only failed steps."

        # ゲート5: 生コマンド連打スパムチェック
        tool_names = []
        for s in steps:
            raw_t = s.get("tool_name") or s.get("tool") or ""
            tool_names.append(getattr(raw_t, "value", str(raw_t)))
        if len(set(tool_names)) == 1 and tool_names[0] in ("run_command", "execute_bash"):
            # 同一コマンド連打の場合は引数の多様性を確認
            arg_hashes = set()
            for s in steps:
                arg_hashes.add(str(s.get("tool_args") or s.get("args") or ""))
            if len(arg_hashes) <= 1:
                return False, "Trajectory consists of repetitive identical commands."

        return True, "Passed all quality filters."

    def should_distill_skill(self, clean_goal: str) -> bool:
        """
        ~/.agents/skills/ への新規SKILLパッケージ蒸留を行うべきか判定
        - 通常の3ステップ作業ごとに勝手なSKILLフォルダが増殖するのを防止
        - 明示的にスキル化・学習・蒸留を求められた場合のみ ~/.agents/skills/ に生成する
        """
        g = (clean_goal or "").lower()
        skill_triggers = (
            "/learn", "skillを", "skill化", "スキルを", "スキル化", "スキルとして",
            "スキル作成", "skill作成", "distill a skill", "create a skill", "スキル蒸留"
        )
        return any(t in g for t in skill_triggers)

    # =========================================================================
    # 2. 先行ガイダンス注入 (Pre-Execution AWM Guidance Injection)
    # =========================================================================
    def get_guidance_for_prompt(self, user_prompt: str) -> str | None:
        """
        ユーザーのプロンプトに関連する過去の成功DAGワークフローを高速検索し、
        推論プロンプトに注入可能なガイダンス指示テキストを生成
        """
        if not self.enabled or not self.memory_db:
            return None

        prompt_clean = extract_clean_user_goal(user_prompt)
        if len(prompt_clean) < 6:
            return None

        try:
            workflows = self.memory_db.search_awm_workflows(prompt_clean, limit=1)
            if not workflows:
                return None

            wf = workflows[0]
            # 信頼度ゲート：失敗多数のものはガイダンスから除外
            if wf.get("failure_count", 0) > wf.get("success_count", 1):
                return None

            dag = wf.get("abstract_dag", [])
            if not dag or len(dag) < 2:
                return None

            # ガイダンス指示文を構造化整形
            lines = [
                f"\n【💡 AWM実証済み推奨ワークフロー: {wf.get('workflow_name')} (過去成功実績: {wf.get('success_count')}回)】",
                f"目標パターン: {wf.get('goal_pattern')}",
                "推奨実行ステップ（ノイズを排した最短正解手順）:"
            ]
            for s in dag:
                step_num = s.get("step", 1)
                purpose = s.get("purpose", "")
                tool = s.get("tool", "")
                exp = s.get("expected_outcome", "")
                lines.append(f"  {step_num}. [{tool}] {purpose} ➔ 判定基準: {exp}")

            if wf.get("verification_assert"):
                lines.append(f"  検証基準: {wf.get('verification_assert')}")
            lines.append("※上記実証手順を最優先ガイダンスとし、環境制約に応じて柔軟かつ最短手数で遂行してください。\n")

            return "\n".join(lines)
        except Exception as e:
            logger.debug(f"[AWMManager] Guidance search error: {e}")
            return None

    # =========================================================================
    # 3. 非同期バックグラウンド自己学習 (Asynchronous Background Learning)
    # =========================================================================
    def learn_trajectory_async(
        self,
        session_id: str,
        user_goal: str,
        steps: list[dict[str, Any]],
        on_complete: Any | None = None
    ):
        """
        メインチャットの応答性を一切阻害せず、裏のワーカースレッドで安全に学習を実行
        """
        if not self.enabled:
            return

        def _worker():
            try:
                clean_goal = extract_clean_user_goal(user_goal)[:200]
                # 1. ノイズフィルター
                worth, reason = self.is_worth_learning(clean_goal, steps)
                if not worth:
                    logger.debug(f"[AWM Worker] Skipped learning: {reason}")
                    return

                # 2. エンジン再確認
                if not self.awm or not self.learner:
                    self._init_engines()
                if not self.awm or not self.learner:
                    return

                traj = {
                    "traj_id": session_id,
                    "session_id": session_id,
                    "user_goal": clean_goal,
                    "steps": steps,
                    "start_time": time.time()
                }

                # 3. AWM抽象化DAGの生成と保存 (品質ゲート内包)
                workflow = self.awm.abstract_workflow_from_trajectory(traj)
                if workflow and hasattr(self.awm, "_save_workflow"):
                    saved = self.awm._save_workflow(workflow)
                    wf_name = workflow.get("workflow_name", "unnamed")
                    logger.info(f"[AWM Worker] Workflow '{wf_name}' saved status: {saved}")

                # 4. 明示的なスキル化要求時のみ SKILLパッケージを自動蒸留 (~/.agents/skills/)
                # (既存正本スキルの無断上書き禁止 & awm_workflows への重複登録防止)
                result = {"status": "skipped_by_policy"}
                if self.should_distill_skill(clean_goal):
                    result = self.learner.learn_from_text_or_context(
                        request_text=clean_goal,
                        recent_history=steps[-10:],
                        overwrite=False,
                        save_awm=False
                    )
                    if result.get("status") == "success":
                        logger.info(f"[AWM Worker] Skill distilled: {result.get('skill_name')} -> {result.get('skill_path')}")

                if on_complete:
                    on_complete(workflow, result)
            except Exception as ex:
                logger.warning(f"[AWM Worker] Background distillation error: {ex}")

        self.pool.submit(_worker)

    # =========================================================================
    # 4. ガベージコレクション＆品質維持 (Self-Cleaning GC)
    # =========================================================================
    def purge_unreliable_workflows(self, max_failures: int = 2) -> int:
        """失敗多数または低品質・陳腐化したゴミワークフローを完全パージ"""
        if not self.enabled or not self.memory_db:
            return 0
        if hasattr(self.memory_db, "purge_awm_workflows"):
            return self.memory_db.purge_awm_workflows(max_failures=max_failures)
        return 0

    def get_stats(self) -> dict[str, Any]:
        """AWM学習統計の取得"""
        if not self.enabled or not self.memory_db:
            return {"enabled": False, "count": 0, "workflows": []}

        workflows = []
        if hasattr(self.memory_db, "list_awm_workflows"):
            workflows = self.memory_db.list_awm_workflows(limit=50)

        total_success = sum(w.get("success_count", 0) for w in workflows)
        total_failures = sum(w.get("failure_count", 0) for w in workflows)
        estimated_saved_tokens = total_success * 4500  # 1回のDAGショートカットで約4.5Kトークン削減

        return {
            "enabled": True,
            "total_workflows": len(workflows),
            "total_success_replays": total_success,
            "total_failures": total_failures,
            "estimated_saved_tokens": estimated_saved_tokens,
            "workflows": [
                {
                    "name": w.get("workflow_name"),
                    "goal": w.get("goal_pattern")[:60],
                    "steps": len(w.get("abstract_dag", [])),
                    "success": w.get("success_count", 0),
                    "failures": w.get("failure_count", 0),
                    "updated_at": w.get("updated_at")
                }
                for w in workflows
            ]
        }
