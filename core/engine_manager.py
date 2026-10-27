# -*- coding: utf-8 -*-
"""
TUGUMIv6 Engine Manager
- Coordinates Native Antigravity SDK Engine and Direct Gemini Client
- Provides unified agent execution and streaming dispatch
- Configurable primary backend (Antigravity SDK Native or Direct Gemini)
"""

import json
import os
from typing import Dict, Any, Optional, Iterator, Tuple
from .gemini_client import GeminiClient, _resolve_gemini_api_key
from .antigravity_sdk import AntigravityEngine
from .awm_manager import AWMManager

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
        thinking_level: Optional[str] = None
    ) -> str:
        """単発実行 (エラー時に別エンジンで勝手に2重実行しない Fail-Fast 設計)"""
        active_level = thinking_level or self.thinking_level
        effective_sys_inst, _ = self._inject_awm_guidance(prompt, system_instruction)

        if self.antigravity.is_available() and self.primary_engine == "antigravity":
            res = self.antigravity.execute_task(
                prompt,
                system_instruction=effective_sys_inst,
                thinking_level=active_level
            )
            if res.get("status") == "success":
                return res.get("text", "")
            raise RuntimeError(f"Antigravity execution stopped (Fail-Fast): {res.get('error')}")
        return self.gemini.generate_content(
            prompt=prompt,
            system_instruction=effective_sys_inst,
            thinking_level=active_level
        )

    def generate_stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        thinking_level: Optional[str] = None,
        mode: str = "light"
    ) -> Iterator[Tuple[str, Any]]:
        """
        ストリーミング実行 (エラー時に第2・第3エンジンへ勝手に連鎖して3重課金するフォールバックを完全廃止)
        AWM先行ガイダンス注入および非同期バックグラウンド自己学習を透過実行
        """
        active_level = thinking_level or self.thinking_level
        effective_sys_inst, _ = self._inject_awm_guidance(prompt, system_instruction)

        collected_steps: list[dict[str, Any]] = []
        step_idx = 1
        is_success = True

        if self.antigravity.is_available() and self.primary_engine == "antigravity":
            try:
                sess = self.get_or_create_session(
                    system_instruction=effective_sys_inst,
                    thinking_level=active_level,
                    mode=mode
                )
                if sess:
                    for chunk in sess.chat_stream(prompt):
                        typ, val = chunk
                        if typ == "tool_call":
                            t_name = getattr(val, "name", str(val))
                            t_args = getattr(val, "arguments", {}) or getattr(val, "args", {})
                            collected_steps.append({
                                "step_index": step_idx,
                                "tool_name": t_name,
                                "tool_args": t_args,
                                "success": True
                            })
                            step_idx += 1
                        elif typ == "error":
                            is_success = False
                        yield chunk

                    # ターン完了後、ノイズフィルター通過時のみ裏でAWM学習
                    if is_success and collected_steps and hasattr(self, "awm") and self.awm:
                        self.awm.learn_trajectory_async(
                            session_id=f"sess_{int(time.time())}",
                            user_goal=prompt[:200],
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
        if self.session and hasattr(self.session, "cancel"):
            try:
                self.session.cancel()
            except Exception:
                pass

    def get_or_create_session(
        self,
        system_instruction: Optional[str] = None,
        thinking_level: Optional[str] = None,
        mode: str = "light"
    ) -> Any:
        """Returns the active persistent AntigravitySession, creating one if not present."""
        if not self.antigravity.is_available():
            return None
        active_level = thinking_level or self.thinking_level
        target_model = getattr(self.antigravity, "model", None)

        # モデル/思考強度が変わった場合、旧Agentに束縛された常駐セッションを破棄して再構築
        # (AntigravitySession は生成時の build_config() で Agent を固定するため、属性変更だけでは推論に反映されない)
        if self.session is not None and getattr(self.session, "active", False):
            bound_model = getattr(self.session, "_bound_model", None)
            bound_level = getattr(self.session, "thinking_level", None)
            if bound_model != target_model or (bound_level or "").lower() != (active_level or "").lower():
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
        """Resets the persistent AntigravitySession for a new conversation context."""
        if self.session:
            try:
                self.session.reset(system_instruction=system_instruction)
            except Exception:
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
