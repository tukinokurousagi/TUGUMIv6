# -*- coding: utf-8 -*-
"""
TUGUMIv6 Engine Manager
- Coordinates Native Antigravity SDK Engine and Direct Gemini Client
- Provides unified agent execution and streaming dispatch
- Configurable primary backend (Antigravity SDK Native or Direct Gemini)
"""

import json
import logging
import os
import time
from typing import Dict, Any, Optional, Iterator, Tuple
from .gemini_client import GeminiClient, _resolve_gemini_api_key
from .antigravity_sdk import AntigravityEngine
from .awm_manager import AWMManager, extract_clean_user_goal

logger = logging.getLogger(__name__)

class EngineManager:
    """Master Engine Dispatcher with Native Antigravity SDK Core"""
    def __init__(self, config_path: str = "/data/data/com.termux/files/home/TUGUMIv6/engine_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.primary_engine = self.config.get("primary_engine", "antigravity")

        api_k = _resolve_gemini_api_key(self.config.get("api_key", ""))
        self.gemini = GeminiClient(
            api_key=api_k,
            model=self.config.get("gemini_model", "gemini-3.8-flash"),
            fallback_model=self.config.get("fallback_model", "gemini-3.5-flash"),
            fallback_model_lite=self.config.get("fallback_model_lite", "gemini-3.5-flash-lite"),
            embedding_model=self.config.get("embedding_model", "gemini-embedding-2"),
            timeout=self.config.get("timeout", 300.0),
            max_retries=1
        )

        self.antigravity = AntigravityEngine(
            api_key=api_k,
            model=self.config.get("gemini_model", "gemini-3.8-flash"),
            workspace=self.config.get("workspace", "/data/data/com.termux/files/home")
        )
        self.thinking_level = self.config.get("thinking_level", "high")
        self.gemini.set_thinking_level(self.thinking_level)
        self.session = None
        self.awm = AWMManager(
            gemini_client=self.gemini,
            model=self.config.get("gemini_model", "gemini-3.8-flash")
        )
        self._rag_engine = None
        self._skills_dir = "/data/data/com.termux/files/home/.agents/skills"
        self._last_skills_mtime = self._compute_skills_signature()
        try:
            from tools.mcp_ja_enforcer import enforce_mcp_schemas_japanese
            enforce_mcp_schemas_japanese(check_only=False)
        except Exception:
            pass

    def _compute_skills_signature(self) -> float:
        """
        ~/.agents/skills 直下の増減および各サブディレクトリ内の SKILL.md 編集を
        両方高速検知するための複合更新シグネチャを算出
        """
        if not os.path.exists(self._skills_dir):
            return 0.0
        try:
            max_mtime = os.path.getmtime(self._skills_dir)
            count = 0
            for entry in os.listdir(self._skills_dir):
                if entry.startswith("."):
                    continue
                s_dir = os.path.join(self._skills_dir, entry)
                if os.path.isdir(s_dir):
                    count += 1
                    md_path = os.path.join(s_dir, "SKILL.md")
                    if os.path.exists(md_path):
                        m = os.path.getmtime(md_path)
                        if m > max_mtime:
                            max_mtime = m
            return round(max_mtime + (count * 1e-6), 6)
        except Exception:
            return 0.0

    def _get_rag_engine(self) -> Optional[Any]:
        """HybridRAGEngineの遅延ロード"""
        if self._rag_engine is not None:
            return self._rag_engine
        try:
            from memory.rag_engine import HybridRAGEngine
            self._rag_engine = HybridRAGEngine(gemini_client=self.gemini)
        except Exception as e:
            logger.debug(f"[EngineManager] Failed to init HybridRAGEngine: {e}")
            self._rag_engine = None
        return self._rag_engine

    def _inject_rag_context(
        self,
        prompt: str,
        system_instruction: Optional[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """ユーザープロンプトから関連ナレッジを自動検索し、システム指示に自然に注入 (Zero-Shot Auto-RAG)"""
        if not prompt or not prompt.strip():
            return system_instruction, None

        # 既に上位（CLI/WebUI）でRAGコンテキストが注入済みの場合は二重検索をスキップ
        if "【📚 参照RAGナレッジ" in prompt or (system_instruction and "参照RAGナレッジ" in system_instruction):
            return system_instruction, None

        rag = self._get_rag_engine()
        if not rag:
            return system_instruction, None

        clean_query = extract_clean_user_goal(prompt) or prompt
        rag_context = None
        try:
            if hasattr(rag, "retrieve_for_context"):
                bundle = rag.retrieve_for_context(clean_query, top_k=3)
                if bundle.get("has_hits") and bundle.get("context_text"):
                    rag_context = bundle["context_text"]
            else:
                results = rag.search_hybrid(clean_query, top_k=3)
                if results:
                    snippets = []
                    for idx, r in enumerate(results):
                        content = (r.get("clean_text") or r.get("text") or r.get("content") or "").strip()
                        title = r.get("title", "Unknown")
                        cat = r.get("folder") or r.get("category") or "General"
                        if content:
                            snippets.append(f"[{idx + 1}] ドキュメント: `{title}` (カテゴリ: {cat})\n{content}")
                    if snippets:
                        rag_context = (
                            "【自律参照ナレッジベース (Auto-RAG Knowledge)】\n"
                            "以下の情報は、ローカルナレッジベース（TUGUMI_RAG等）から自動検索された確定情報です。\n"
                            "拓磨様への回答やタスク実行時に優先的な事実として自然に反映してください。\n"
                            + "\n---\n".join(snippets)
                        )
        except Exception as e:
            logger.debug(f"[EngineManager] Auto-RAG search error: {e}")

        if not rag_context:
            return system_instruction, None

        merged = (system_instruction or "").strip()
        if merged:
            merged = f"{merged}\n\n{rag_context}"
        else:
            merged = rag_context
        return merged, rag_context

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[EngineManager] Error reading config: {e}")
        return {}

    @property
    def current_model(self) -> str:
        """現在のアクティブモデル名"""
        return getattr(self.gemini, "model", self.config.get("gemini_model", "gemini-3.8-flash"))

    def normalize_model_name(self, name: str) -> str:
        """モデル名のエイリアスを正式なAPIモデル名に正規化"""
        clean = name.lower().strip()
        alias_map = {
            "argon": "gemini-4-argon",
            "gemini-4": "gemini-4-argon",
            "gemini-4-argon": "gemini-4-argon",
            "4": "gemini-4-argon",
            "4-argon": "gemini-4-argon",
            "flash": "gemini-3.8-flash",
            "3.8": "gemini-3.8-flash",
            "3.8-flash": "gemini-3.8-flash",
            "gemini-3.8": "gemini-3.8-flash",
            "gemini-3.8-flash": "gemini-3.8-flash",
            "pro": "gemini-3.0-pro",
            "3.0-pro": "gemini-3.0-pro",
            "gemini-3.0-pro": "gemini-3.0-pro",
            "3-pro": "gemini-3.0-pro",
            "3.5": "gemini-3.5-flash",
            "3.5-flash": "gemini-3.5-flash",
            "gemini-3.5-flash": "gemini-3.5-flash",
            "lite": "gemini-3.5-flash-lite",
            "flash-lite": "gemini-3.5-flash-lite",
            "gemini-3.5-flash-lite": "gemini-3.5-flash-lite"
        }
        return alias_map.get(clean, clean)

    def set_model(self, model: str, persist: bool = True) -> str:
        """推論モデルを変更 ('gemini-3.8-flash', 'gemini-4-argon' 等)"""
        norm = self.normalize_model_name(model)
        self.gemini.set_model(norm)
        if hasattr(self.antigravity, "set_model"):
            self.antigravity.set_model(norm)
        if persist:
            try:
                self.config["gemini_model"] = norm
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[EngineManager] Failed to persist gemini_model: {e}")
        return norm

    def set_thinking_level(self, level: str, persist: bool = True) -> str:
        """思考強度レベルを変更 ('high', 'medium', 'low', 'minimal')"""
        lvl = level.lower().strip()
        if lvl in ("high", "medium", "low", "minimal"):
            self.thinking_level = lvl
            self.gemini.set_thinking_level(lvl)
            if hasattr(self.antigravity, "set_thinking_level"):
                self.antigravity.set_thinking_level(lvl)
            if persist:
                try:
                    self.config["thinking_level"] = lvl
                    with open(self.config_path, "w", encoding="utf-8") as f:
                        json.dump(self.config, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    print(f"[EngineManager] Failed to persist thinking_level: {e}")
        return self.thinking_level

    def set_primary_engine(self, engine_name: str, persist: bool = True) -> str:
        """プライマリ推論エンジン ('antigravity' | 'gemini') を動的切替"""
        clean = (engine_name or "antigravity").lower().strip()
        if clean not in ("antigravity", "gemini"):
            clean = "antigravity"
        self.primary_engine = clean
        if persist:
            try:
                self.config["primary_engine"] = clean
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[EngineManager] Failed to persist primary_engine: {e}")
        return self.primary_engine

    def get_antigravity_status(self) -> Dict[str, Any]:
        """Antigravity SDK・常駐セッション・10大ピラー・ツール・MCP・Hooks v2のリアルタイム状態を一括取得"""
        ag = getattr(self, "antigravity", None)
        ag_avail = bool(ag and ag.is_available())
        sess = getattr(self, "session", None)
        sess_active = bool(
            sess is not None
            and getattr(sess, "active", False)
            and getattr(sess, "thread", None) is not None
            and sess.thread.is_alive()
            and getattr(sess, "current_agent", None) is not None
        )
        turn_count = getattr(sess, "turn_count", 0) if sess else 0
        sess_mode = getattr(sess, "mode", "light") if sess else "light"
        uptime_sec = round(time.time() - getattr(sess, "created_at", time.time()), 1) if (sess and sess_active) else 0.0

        tools_list = ag.get_tools() if ag_avail else []
        subagents_list = [getattr(s, "name", str(s)) for s in (ag.get_subagents() if ag_avail else [])]
        mcp_names = ag.get_mcp_server_names() if (ag_avail and hasattr(ag, "get_mcp_server_names")) else []
        telemetry = ag.get_telemetry() if (ag_avail and hasattr(ag, "get_telemetry")) else {}

        skill_count = 0
        if os.path.exists(self._skills_dir):
            skill_count = len([
                d for d in os.listdir(self._skills_dir)
                if os.path.isdir(os.path.join(self._skills_dir, d)) and not d.startswith(".")
            ])

        return {
            "available": ag_avail,
            "sdk_version": "0.1.20",
            "version_label": ag.get_version() if ag else "SDK Not Installed",
            "primary_engine": self.primary_engine,
            "current_model": self.current_model,
            "thinking_level": self.thinking_level,
            "session": {
                "active": sess_active,
                "turn_count": turn_count,
                "mode": sess_mode,
                "uptime_sec": uptime_sec,
                "save_dir": "/data/data/com.termux/files/home/.tugumi/sessions",
            },
            "registered_tools_count": len(tools_list),
            "skills_count": skill_count,
            "subagents": subagents_list,
            "mcp_servers": mcp_names,
            "telemetry": telemetry,
            "evolution_score": 100.0,
        }

    def _inject_awm_guidance(self, prompt: str, system_instruction: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """AWMから先行ガイダンスを取得し、システム指示に安全に注入"""
        awm_guidance = None
        if hasattr(self, "awm") and self.awm:
            try:
                awm_guidance = self.awm.get_guidance_for_prompt(prompt)
            except Exception:
                pass

        if not awm_guidance:
            return system_instruction, None

        merged_instruction = (system_instruction or "").strip()
        if merged_instruction:
            merged_instruction = f"{merged_instruction}\n\n{awm_guidance}"
        else:
            merged_instruction = awm_guidance
        return merged_instruction, awm_guidance

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        thinking_level: Optional[str] = None,
        mode: str = "light"
    ) -> str:
        """単発実行 (エラー時に別エンジンで勝手に2重実行しない Fail-Fast 設計)"""
        active_level = thinking_level or self.thinking_level
        effective_sys_inst, _ = self._inject_awm_guidance(prompt, system_instruction)
        effective_sys_inst, rag_ctx = self._inject_rag_context(prompt, effective_sys_inst)
        effective_prompt = prompt
        if rag_ctx and rag_ctx[:80] not in effective_prompt and "【📚 参照RAGナレッジ" not in effective_prompt:
            effective_prompt = f"{effective_prompt}\n\n{rag_ctx}"

        if self.antigravity.is_available() and self.primary_engine == "antigravity":
            res = self.antigravity.execute_task(
                effective_prompt,
                system_instruction=effective_sys_inst,
                thinking_level=active_level
            )
            if res.get("status") == "success":
                return res.get("text", "")
            raise RuntimeError(f"Antigravity execution stopped (Fail-Fast): {res.get('error')}")
        return self.gemini.generate_content(
            prompt=effective_prompt,
            system_instruction=effective_sys_inst,
            thinking_level=active_level
        )

    def generate_stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        thinking_level: Optional[str] = None,
        mode: str = "light",
        user_goal: Optional[str] = None,
        is_steering: bool = False
    ) -> Iterator[Tuple[str, Any]]:
        """
        ストリーミング実行 (エラー時に第2・第3エンジンへ勝手に連鎖して3重課金するフォールバックを完全廃止)
        AWM先行ガイダンス注入・Smart Auto-RAG常駐セッション透過注入および非同期バックグラウンド自己学習を透過実行
        ※ is_steering=True (ESC一時停止からの軌道修正・即時再開時) は、重たいRAG埋め込みAPI再通信やディスクスキャンを完全バイパスし、Antigravity CLI同様に0.01秒で速攻再開する！
        """
        active_level = thinking_level or self.thinking_level
        clean_goal = extract_clean_user_goal(user_goal or prompt)
        if is_steering:
            effective_sys_inst = system_instruction
            effective_prompt = prompt
        else:
            effective_sys_inst, _ = self._inject_awm_guidance(clean_goal, system_instruction)
            effective_sys_inst, rag_ctx = self._inject_rag_context(prompt, effective_sys_inst)
            # 常駐AntigravitySessionは初回生成時のsystem_instructionを保持するため、
            # 2ターン目以降も最新ターンのRAGコンテキストが確実にAgentへ届くようプロンプト側にも透過注入する
            effective_prompt = prompt
            if rag_ctx and rag_ctx[:80] not in effective_prompt and "【📚 参照RAGナレッジ" not in effective_prompt:
                effective_prompt = f"{effective_prompt}\n\n{rag_ctx}"

        collected_steps: list[dict[str, Any]] = []
        step_idx = 1
        is_success = True

        if self.antigravity.is_available() and self.primary_engine == "antigravity":
            try:
                sess = self.get_or_create_session(
                    system_instruction=effective_sys_inst,
                    thinking_level=active_level,
                    mode=mode,
                    fast_reuse=is_steering
                )
                if sess:
                    for chunk in sess.chat_stream(effective_prompt):
                        typ, val = chunk
                        if typ == "tool_call":
                            raw_name = getattr(val, "name", None) or (val.get("name", "tool") if isinstance(val, dict) else str(val))
                            t_name = getattr(raw_name, "value", str(raw_name))
                            t_args = (
                                getattr(val, "arguments", None)
                                or getattr(val, "args", None)
                                or (val.get("args", {}) if isinstance(val, dict) else {})
                            )
                            collected_steps.append({
                                "step_index": step_idx,
                                "tool_name": t_name,
                                "tool_args": t_args if isinstance(t_args, dict) else {"value": str(t_args)},
                                "success": True
                            })
                            step_idx += 1
                        elif typ == "tool_result":
                            err = (
                                getattr(val, "error", None)
                                or getattr(val, "exception", None)
                                or (val.get("error") if isinstance(val, dict) else None)
                            )
                            res_val = getattr(val, "result", None) if not isinstance(val, dict) else val.get("result")
                            if collected_steps:
                                if err:
                                    collected_steps[-1]["success"] = False
                                    collected_steps[-1]["error"] = str(err)[:300]
                                if res_val is not None:
                                    collected_steps[-1]["observation"] = str(res_val)[:300]
                        elif typ == "error":
                            is_success = False
                        yield chunk

                    # ターン完了後、ノイズフィルター通過時のみ裏でAWM学習
                    if is_success and collected_steps and hasattr(self, "awm") and self.awm:
                        self.awm.learn_trajectory_async(
                            session_id=f"sess_{int(time.time())}",
                            user_goal=clean_goal[:200],
                            steps=collected_steps
                        )
                    return
            except Exception as e:
                yield ("error", f"Session error (stopped immediately to prevent duplicate API billing): {e}")
                return

        for chunk in self.gemini.generate_content_stream(
            prompt=prompt,
            system_instruction=effective_sys_inst,
            thinking_level=active_level
        ):
            yield chunk

    def get_awm_stats(self) -> Dict[str, Any]:
        """AWM学習統計の取得"""
        if hasattr(self, "awm") and self.awm:
            return self.awm.get_stats()
        return {"enabled": False, "count": 0}

    def purge_awm_workflows(self, max_failures: int = 2) -> int:
        """失敗多数または低品質・陳腐化したワークフローをパージ"""
        if hasattr(self, "awm") and self.awm:
            return self.awm.purge_unreliable_workflows(max_failures=max_failures)
        return 0

    def cancel_active_task(self):
        """Cancels any running agent turn in the active persistent session."""
        try:
            from interfaces.cli.task_interrupter import TaskInterrupter
            TaskInterrupter.terminate_all_active_processes()
        except Exception:
            pass
        if self.session and hasattr(self.session, "cancel"):
            try:
                self.session.cancel()
                return True
            except Exception:
                pass
        return False

    def set_paused(self, paused: bool):
        """Freezes or unfreezes session timeout timers during ESC TASK PAUSED state."""
        if self.session and hasattr(self.session, "set_paused"):
            try:
                self.session.set_paused(paused)
            except Exception:
                pass

    def _check_skills_updated(self) -> bool:
        """スキルディレクトリ(~/.agents/skills)および各SKILL.mdの更新有無をシグネチャで超高速検知"""
        if not os.path.exists(self._skills_dir):
            return False
        try:
            curr_sig = self._compute_skills_signature()
            if curr_sig != self._last_skills_mtime:
                self._last_skills_mtime = curr_sig
                return True
        except Exception:
            pass
        return False

    def reload_session(self, system_instruction: Optional[str] = None) -> bool:
        """スキルや設定の更新を常駐AntigravitySessionに即座に反映（無停止ホットリロード）"""
        if self.session is not None and getattr(self.session, "active", False):
            try:
                self.session.close()
            except Exception:
                pass
            self.session = None
        return True

    def reload_skills(self) -> Dict[str, Any]:
        """全SKILLエコシステム・動的合成ツールの最新状態を取得し、常駐セッションもホットリロード"""
        skills_updated = self._check_skills_updated()
        if hasattr(self, "antigravity") and self.antigravity:
            if hasattr(self.antigravity, "reload_tools"):
                self.antigravity.reload_tools()
            if hasattr(self.antigravity, "reload_subagents"):
                self.antigravity.reload_subagents()
        self.reload_session()
        skill_count = 0
        if os.path.exists(self._skills_dir):
            skill_count = len([
                d for d in os.listdir(self._skills_dir)
                if os.path.isdir(os.path.join(self._skills_dir, d)) and not d.startswith(".")
            ])
        return {
            "success": True,
            "skills_updated": skills_updated,
            "total_skills": skill_count,
            "registered_tools": len(self.antigravity.get_tools()) if (hasattr(self, "antigravity") and self.antigravity) else 0,
            "timestamp": time.time()
        }

    def get_or_create_session(
        self,
        system_instruction: Optional[str] = None,
        thinking_level: Optional[str] = None,
        mode: str = "light",
        fast_reuse: bool = False
    ) -> Any:
        """Returns the active persistent AntigravitySession, creating one if not present."""
        if not self.antigravity.is_available():
            return None
        if fast_reuse and self.session is not None and getattr(self.session, "active", False):
            return self.session
        active_level = thinking_level or self.thinking_level
        target_model = getattr(self.antigravity, "model", None)

        # モデル/思考強度、またはSKILL定義が変更された場合、旧Agentに束縛された常駐セッションを破棄して再構築
        # (AntigravitySession は生成時の build_config() で Agent を固定するため、属性変更だけでは推論に反映されない)
        skills_changed = self._check_skills_updated()
        if self.session is not None and getattr(self.session, "active", False):
            bound_model = getattr(self.session, "_bound_model", None)
            bound_level = getattr(self.session, "thinking_level", None)
            if skills_changed or bound_model != target_model or (bound_level or "").lower() != (active_level or "").lower():
                try:
                    self.session.close()
                except Exception:
                    pass
                self.session = None

        if self.session is None or not getattr(self.session, "active", False):
            self.session = self.antigravity.create_session(
                system_instruction=system_instruction,
                thinking_level=active_level,
                mode=mode
            )
            self.session._bound_model = target_model
        return self.session

    def reset_session(self, system_instruction: Optional[str] = None):
        """Resets the persistent AntigravitySession cleanly so a fresh one spawns on next turn."""
        if self.session is not None:
            try:
                self.session.close()
            except Exception:
                pass
            self.session = None

    def spawn_agent(self, system_instruction: Optional[str] = None, thinking_level: Optional[str] = None) -> Any:
        """Spawns an official Antigravity Agent instance for persistent sessions."""
        active_level = thinking_level or self.thinking_level
        return self.antigravity.spawn_agent(
            system_instruction=system_instruction,
            thinking_level=active_level
        )

    def chat_stream_agent(self, agent: Any, prompt: str):
        """Streams semantic events from persistent Agent instance."""
        return self.antigravity.chat_stream_agent(agent, prompt)
