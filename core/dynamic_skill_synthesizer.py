# -*- coding: utf-8 -*-
"""
TUGUMIv6 Dynamic Skill Synthesizer & Self-Evolution
- Synthesizes reusable python tools/scripts from successful workflows
- Hot-reloads synthesized skills into dynamic tool registry
- Enables perpetual self-evolution without restarting the agent
"""

import os
import sys
import importlib
import inspect
from typing import Dict, Any, Callable, List

class DynamicSkillSynthesizer:
    """Self-Evolution & Dynamic Skill Synthesis Engine"""
    def __init__(self, dynamic_tools_dir: str = "/data/data/com.termux/files/home/TUGUMIv6/dynamic_tools"):
        self.dynamic_tools_dir = dynamic_tools_dir
        os.makedirs(self.dynamic_tools_dir, exist_ok=True)
        if self.dynamic_tools_dir not in sys.path:
            sys.path.insert(0, self.dynamic_tools_dir)
        self.registry: Dict[str, Callable] = {}
        self.load_all_skills()

    def synthesize_tool(self, tool_name: str, code_content: str, description: str = "") -> bool:
        """新しいPythonツールスクリプトを自己生成し、即座に動的ロード"""
        clean_name = tool_name.replace("-", "_").lower()
        file_path = os.path.join(self.dynamic_tools_dir, f"{clean_name}.py")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f'"""Synthesized Skill: {clean_name}\nDescription: {description}\n"""\n\n')
            f.write(code_content)

        return self.load_tool_file(clean_name)

    def load_tool_file(self, module_name: str) -> bool:
        """単一の動的モジュールをインポート/リロード"""
        try:
            if module_name in sys.modules:
                mod = importlib.reload(sys.modules[module_name])
            else:
                mod = importlib.import_module(module_name)

            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                # Ignore private functions, 'main' runners, and functions imported from other modules
                if (callable(attr) and not attr_name.startswith("_") and 
                    inspect.isfunction(attr) and attr_name != "main" and
                    getattr(attr, "__module__", None) == mod.__name__):
                    self.registry[f"{module_name}.{attr_name}"] = attr
            return True
        except Exception as e:
            print(f"[DynamicSkillSynthesizer] Failed to load {module_name}: {e}")
            return False

    def load_all_skills(self) -> None:
        """保存されている全動的スキルをロード"""
        for fn in os.listdir(self.dynamic_tools_dir):
            if fn.endswith(".py") and not fn.startswith("__"):
                mod_name = fn[:-3]
                self.load_tool_file(mod_name)

    def list_synthesized_skills(self) -> List[str]:
        return list(self.registry.keys())

    def execute_skill(self, skill_name: str, *args, **kwargs) -> Any:
        if skill_name in self.registry:
            return self.registry[skill_name](*args, **kwargs)
        raise ValueError(f"Skill '{skill_name}' not found in dynamic registry.")
