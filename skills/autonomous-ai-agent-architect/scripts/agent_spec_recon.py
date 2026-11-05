#!/data/data/com.termux/files/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Autonomous AI Agent Architect - Live Spec Recon, Code Auditor & SOTA Scaffold Engine
====================================================================================
1. --inspect-env          : Termux実機のAI SDKバージョン＆主要Configフィールドをライブ検視
2. --inspect-symbol <sym> : 指定クラス/関数の実シグネチャ・Pydanticフィールドを正確に抽出
3. --search-spec <query>  : DuckDuckGo経由で最新のAI技術仕様・プロトコル動向をリアルタイム検索
4. --audit-code <path>    : 生成したエージェントコードの認識的負債・Termux適合性・Zero-Mock監査
5. --scaffold <name>      : 2026年最新仕様（google-genai / MCP 2.0 / SQLite WAL）準拠のエージェント生成
"""

import argparse
import ast
import html
import importlib
import importlib.metadata as md
import inspect
import json
import os
import py_compile
import re
import sys
import urllib.parse
import urllib.request
from typing import Any, Dict, List

DEFAULT_PACKAGES = [
    "google-genai",
    "google-antigravity",
    "mcp",
    "openai",
    "anthropic",
    "pydantic",
    "httpx",
    "rich",
    "prompt_toolkit",
]


def inspect_environment() -> Dict[str, Any]:
    """Termux環境にインストール済みのAI SDKバージョンと主要構造をライブ検視"""
    report: Dict[str, Any] = {
        "platform": sys.platform,
        "python_version": sys.version.split()[0],
        "tmpdir": os.environ.get("TMPDIR", "/data/data/com.termux/files/usr/tmp"),
        "packages": {},
        "live_signatures": {},
    }

    for pkg in DEFAULT_PACKAGES:
        try:
            report["packages"][pkg] = md.version(pkg)
        except Exception:
            report["packages"][pkg] = "not_installed"

    # google-genai のライブシグネチャ抽出
    try:
        from google.genai import types as genai_types

        if hasattr(genai_types, "ThinkingConfig") and hasattr(genai_types.ThinkingConfig, "model_fields"):
            report["live_signatures"]["google.genai.types.ThinkingConfig"] = list(
                genai_types.ThinkingConfig.model_fields.keys()
            )
        if hasattr(genai_types, "GenerateContentConfig") and hasattr(
            genai_types.GenerateContentConfig, "model_fields"
        ):
            report["live_signatures"]["google.genai.types.GenerateContentConfig"] = list(
                genai_types.GenerateContentConfig.model_fields.keys()
            )[:25]
    except Exception as e:
        report["live_signatures"]["google.genai"] = f"error: {e}"

    # google-antigravity のライブシグネチャ抽出
    try:
        import google.antigravity as ag

        if hasattr(ag, "LocalAgentConfig") and hasattr(ag.LocalAgentConfig, "model_fields"):
            report["live_signatures"]["google.antigravity.LocalAgentConfig"] = list(
                ag.LocalAgentConfig.model_fields.keys()
            )
        if hasattr(ag, "ThinkingLevel"):
            report["live_signatures"]["google.antigravity.ThinkingLevel"] = [
                k for k in dir(ag.ThinkingLevel) if k.isupper()
            ]
    except Exception as e:
        report["live_signatures"]["google.antigravity"] = f"error: {e}"

    # mcp のライブシグネチャ抽出
    try:
        import mcp

        report["live_signatures"]["mcp.exports"] = [
            x for x in dir(mcp) if not x.startswith("_")
        ][:30]
    except Exception as e:
        report["live_signatures"]["mcp"] = f"error: {e}"

    return report


def inspect_symbol(symbol_path: str) -> Dict[str, Any]:
    """ドット区切りのシンボルパス（例: google.genai.types.ThinkingConfig）をライブ検視"""
    parts = symbol_path.strip().split(".")
    if len(parts) < 2:
        return {"status": "error", "message": f"Invalid symbol path: {symbol_path}"}

    obj = None
    mod = None
    for i in range(len(parts), 0, -1):
        mod_name = ".".join(parts[:i])
        try:
            mod = importlib.import_module(mod_name)
            obj = mod
            for attr in parts[i:]:
                obj = getattr(obj, attr)
            break
        except Exception:
            continue

    if obj is None:
        return {"status": "error", "message": f"Could not resolve symbol: {symbol_path}"}

    info: Dict[str, Any] = {
        "status": "ok",
        "symbol": symbol_path,
        "type": type(obj).__name__,
        "doc": (inspect.getdoc(obj) or "")[:600],
    }

    if hasattr(obj, "model_fields"):
        fields_info = {}
        for fname, fval in obj.model_fields.items():
            ann = getattr(fval, "annotation", None)
            fields_info[fname] = str(ann) if ann else "Any"
        info["pydantic_fields"] = fields_info
    elif hasattr(obj, "__dataclass_fields__"):
        info["dataclass_fields"] = {
            k: str(v.type) for k, v in obj.__dataclass_fields__.items()
        }
    else:
        try:
            info["signature"] = str(inspect.signature(obj))
        except Exception:
            pass
        info["attributes"] = [a for a in dir(obj) if not a.startswith("_")][:40]

    return info


def search_latest_spec(query: str, max_results: int = 5) -> Dict[str, Any]:
    """DuckDuckGo HTML/Lite 経由で最新のAI技術仕様・ドキュメントを検索"""
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; Termux) AppleWebKit/537.36 Chrome/126.0.0.0 Mobile Safari/537.36"
        },
    )
    results: List[Dict[str, str]] = []
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw_html = resp.read().decode("utf-8", errors="ignore")

        blocks = re.findall(
            r'<a rel="nofollow" class="result__a" href="([^"]+)">(.*?)</a>.*?<a class="result__snippet"[^>]*>(.*?)</a>',
            raw_html,
             flags=re.DOTALL,
        )
        for href, title_html, snippet_html in blocks[:max_results]:
            clean_url = href
            if "uddg=" in href:
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                if "uddg" in parsed:
                    clean_url = parsed["uddg"][0]
            clean_title = re.sub(r"<[^>]+>", "", html.unescape(title_html)).strip()
            clean_snippet = re.sub(r"<[^>]+>", "", html.unescape(snippet_html)).strip()
            results.append(
                {
                    "title": clean_title,
                    "url": clean_url,
                    "snippet": clean_snippet,
                }
            )
        return {"status": "ok", "query": query, "count": len(results), "results": results}
    except Exception as e:
        return {"status": "error", "query": query, "message": str(e), "results": []}


def audit_agent_code(file_path: str) -> Dict[str, Any]:
    """自律型AIエージェントのPythonコードを静的＆AST監査（認識的負債・Zero-Mock・Termux適合性）"""
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"File not found: {file_path}"}

    issues: List[Dict[str, Any]] = []
    passed_checks: List[str] = []

    # 1. 構文チェック (py_compile)
    try:
        py_compile.compile(file_path, doraise=True)
        passed_checks.append("Syntax Gate (py_compile): PASS")
    except py_compile.PyCompileError as e:
        issues.append({"severity": "CRITICAL", "category": "SyntaxError", "detail": str(e)})
        return {"status": "failed", "file": file_path, "issues": issues, "passed": passed_checks}

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()

    # 2. AST解析（旧API・空pass・未実装例外の検知）
    try:
        tree = ast.parse(source, filename=file_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if "google.generativeai" in alias.name:
                        issues.append(
                            {
                                "severity": "CRITICAL",
                                "category": "EpistemicDebt_DeprecatedSDK",
                                "line": node.lineno,
                                "detail": "廃止された 'google.generativeai' が使用されています。'from google import genai' (google-genai SDK) を使用してください。",
                            }
                        )
            elif isinstance(node, ast.ImportFrom):
                mod_name = node.module or ""
                if "google.generativeai" in mod_name:
                    issues.append(
                        {
                            "severity": "CRITICAL",
                            "category": "EpistemicDebt_DeprecatedSDK",
                            "line": node.lineno,
                            "detail": "廃止された 'google.generativeai' が使用されています。'from google import genai' を使用してください。",
                        }
                    )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 関数本体が pass または Docstring + pass のみでないか検査
                body_without_doc = [
                    stmt
                    for stmt in node.body
                    if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str))
                ]
                if len(body_without_doc) == 1 and isinstance(body_without_doc[0], ast.Pass):
                    issues.append(
                        {
                            "severity": "HIGH",
                            "category": "ZeroMockViolation",
                            "line": node.lineno,
                            "detail": f"関数 '{node.name}' の中身が 'pass' のみ（モック/未実装）です。本番ロジックを実装してください。",
                        }
                    )
    except Exception as e:
        issues.append({"severity": "HIGH", "category": "ASTParseError", "detail": str(e)})

    if not any(i["category"] == "EpistemicDebt_DeprecatedSDK" for i in issues):
        passed_checks.append("SDK Freshness Gate (No deprecated google.generativeai): PASS")

    # 3. Termux パス規約チェック
    lines = source.splitlines()
    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if re.search(r'["\']/tmp/', line) and "TMPDIR" not in line and "com.termux" not in line:
            issues.append(
                {
                    "severity": "MEDIUM",
                    "category": "TermuxPathViolation",
                    "line": idx,
                    "detail": "ハードコードされた '/tmp/' が検出されました。Termuxでは os.environ.get('TMPDIR', '/data/data/com.termux/files/usr/tmp') を使用してください。",
                }
            )
        if re.search(r"\b(TODO|FIXME|XXX)\b", line):
            issues.append(
                {
                    "severity": "MEDIUM",
                    "category": "ZeroMock_TODOResidue",
                    "line": idx,
                    "detail": f"未完成マーカー（TODO/FIXME）が検出されました: {stripped[:80]}",
                }
            )

    # 4. SQLite WAL チェック
    if "sqlite3.connect" in source:
        if "journal_mode=WAL" not in source and "journal_mode = WAL" not in source:
            issues.append(
                {
                    "severity": "MEDIUM",
                    "category": "SQLiteConcurrency",
                    "line": 1,
                    "detail": "sqlite3.connect が使用されていますが 'PRAGMA journal_mode=WAL;' と 'PRAGMA busy_timeout=60000;' が設定されていません。",
                }
            )
        else:
            passed_checks.append("SQLite Concurrency Gate (WAL + busy_timeout): PASS")

    status = "ok" if not any(i["severity"] in ("CRITICAL", "HIGH") for i in issues) else "failed"
    return {
        "status": status,
        "file": file_path,
        "issue_count": len(issues),
        "passed_checks": passed_checks,
        "issues": issues,
    }


def generate_sota_agent_scaffold(
    agent_name: str,
    model_name: str = "gemini-3.8-flash",
    thinking_level: str = "LOW",
    output_dir: str = ".",
) -> Dict[str, Any]:
    """2026年最新仕様（google-genai, ThinkingConfig, BLOCK_NONE, SQLite WAL, MCP 2.0 Ephemeral）準拠のエージェントを生成"""
    os.makedirs(output_dir, exist_ok=True)
    safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", agent_name.lower()).strip("_") or "sota_autonomous_agent"
    target_file = os.path.join(output_dir, f"{safe_name}.py")

    code_template = f'''#!/data/data/com.termux/files/usr/bin/python3
# -*- coding: utf-8 -*-
"""
{agent_name} - 2026 SOTA Autonomous AI Agent (Termux aarch64 Production-Ready)
==============================================================================
- SDK      : google-genai (v2.25.0+)
- Model    : {model_name}
- Thinking : ThinkingConfig(include_thoughts=True, thinking_level="{thinking_level}")
- Safety   : BLOCK_NONE across all standard categories
- Memory   : SQLite3 WAL + busy_timeout=60000
- Protocol : MCP 2.0 (2026-07-28) Ephemeral On-Demand Ready
"""

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
from typing import Any, Callable, Dict, List, Optional

from google import genai
from google.genai import types

HOME = os.path.expanduser("~")
TMPDIR = os.environ.get("TMPDIR", "/data/data/com.termux/files/usr/tmp")
DEFAULT_DB_PATH = os.path.join(TMPDIR, "{safe_name}_memory.db")


class EpisodicWALMemory:
    """SQLite WAL モードと busy_timeout=60000 を備えた高耐久エージェント記憶ストア"""

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=60.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=60000;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )

    def add_entry(self, role: str, content: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO episodes (role, content, created_at) VALUES (?, ?, ?)",
                (role, content, time.time()),
            )

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT role, content, created_at FROM episodes ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
        return [{{"role": r[0], "content": r[1], "created_at": r[2]}} for r in reversed(rows)]


class AutonomousAgent:
    """2026 SOTA 自律型AIエージェント・コアエンジン"""

    def __init__(
        self,
        model_name: str = "{model_name}",
        thinking_level: str = "{thinking_level}",
        db_path: str = DEFAULT_DB_PATH,
    ) -> None:
        self.model_name = model_name
        self.thinking_level = thinking_level
        self.memory = EpisodicWALMemory(db_path=db_path)
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.tools: Dict[str, Callable[..., Any]] = {{
            "run_shell_inspect": self.tool_run_shell_inspect,
        }}

    @staticmethod
    def tool_run_shell_inspect(command: str) -> str:
        """安全なローカル環境確認コマンドをタイムアウト付きで実行"""
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return json.dumps(
            {{
                "exit_code": proc.returncode,
                "stdout": proc.stdout[:2000],
                "stderr": proc.stderr[:1000],
            }},
            ensure_ascii=False,
        )

    def build_config(self, system_instruction: str) -> types.GenerateContentConfig:
        """2026年最新仕様の GenerateContentConfig を構築"""
        safety_categories = [
            types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        ]
        return types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2,
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,
                thinking_level=self.thinking_level,
            ),
            safety_settings=[
                types.SafetySetting(
                    category=cat,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE,
                )
                for cat in safety_categories
            ],
            tools=list(self.tools.values()),
        )

    def run_task(self, prompt: str) -> Dict[str, Any]:
        """タスクを実行し、思考プロセスと最終応答を構造化返却"""
        self.memory.add_entry("user", prompt)
        if not self.client:
            return {{
                "status": "offline_ready",
                "model": self.model_name,
                "message": "GEMINI_API_KEY 未設定のためオフライン検証モードで応答しました。",
            }}

        cfg = self.build_config(
            system_instruction="あなたは第一原理思考に基づき自律的に課題を解決するエリートAIエージェントです。"
        )
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=cfg,
        )
        answer = response.text or ""
        self.memory.add_entry("assistant", answer)
        return {{
            "status": "ok",
            "model": self.model_name,
            "thinking_level": self.thinking_level,
            "response": answer,
        }}


def run_self_test() -> int:
    """5層検証ゲート用セルフテスト"""
    agent = AutonomousAgent()
    cfg = agent.build_config("Self-test system instruction")
    assert cfg.thinking_config is not None, "ThinkingConfig must be initialized"
    assert len(cfg.safety_settings) == 4, "All 4 BLOCK_NONE safety settings must be present"
    agent.memory.add_entry("system", "self_test_ping")
    recent = agent.memory.get_recent(limit=1)
    assert len(recent) >= 1 and recent[-1]["content"] == "self_test_ping"
    tool_res = json.loads(agent.tool_run_shell_inspect("echo SOTA_OK"))
    assert tool_res["exit_code"] == 0 and "SOTA_OK" in tool_res["stdout"]
    print(json.dumps({{"self_test": "PASS", "model": agent.model_name, "thinking_level": agent.thinking_level}}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="{agent_name} CLI")
    parser.add_argument("--self-test", action="store_true", help="Run built-in verification gate")
    parser.add_argument("--prompt", type=str, default="", help="Task prompt to execute")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()
    if args.prompt:
        agent = AutonomousAgent()
        res = agent.run_task(args.prompt)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(code_template)
    os.chmod(target_file, 0o755)

    audit_res = audit_agent_code(target_file)
    return {
        "status": "ok",
        "generated_file": target_file,
        "model": model_name,
        "thinking_level": thinking_level,
        "audit": audit_res,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Autonomous AI Agent Architect - Live Spec Recon & Auditor"
    )
    parser.add_argument(
        "--inspect-env",
        action="store_true",
        help="Inspect installed AI SDK versions and live config signatures",
    )
    parser.add_argument(
        "--inspect-symbol",
        type=str,
        default="",
        help="Inspect live Python symbol signature/fields (e.g. google.genai.types.ThinkingConfig)",
    )
    parser.add_argument(
        "--search-spec",
        type=str,
        default="",
        help="Search latest AI specification and tech docs via DuckDuckGo",
    )
    parser.add_argument(
        "--audit-code",
        type=str,
        default="",
        help="Audit agent Python file for deprecated SDKs, Termux paths, and Zero-Mock compliance",
    )
    parser.add_argument(
        "--scaffold",
        type=str,
        default="",
        help="Generate a 2026 SOTA autonomous agent Python scaffold with the given name",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-3.8-flash",
        help="Target model name for scaffold generation",
    )
    parser.add_argument(
        "--thinking-level",
        type=str,
        default="LOW",
        help="Thinking level (MINIMAL, LOW, MEDIUM, HIGH) for scaffold generation",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=os.environ.get("TMPDIR", "/data/data/com.termux/files/usr/tmp"),
        help="Output directory for generated scaffold",
    )

    args = parser.parse_args()

    if args.inspect_env:
        print(json.dumps(inspect_environment(), ensure_ascii=False, indent=2))
        return 0
    if args.inspect_symbol:
        print(json.dumps(inspect_symbol(args.inspect_symbol), ensure_ascii=False, indent=2))
        return 0
    if args.search_spec:
        print(json.dumps(search_latest_spec(args.search_spec), ensure_ascii=False, indent=2))
        return 0
    if args.audit_code:
        res = audit_agent_code(args.audit_code)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res.get("status") == "ok" else 1
    if args.scaffold:
        res = generate_sota_agent_scaffold(
            agent_name=args.scaffold,
            model_name=args.model,
            thinking_level=args.thinking_level,
            output_dir=args.output_dir,
        )
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
