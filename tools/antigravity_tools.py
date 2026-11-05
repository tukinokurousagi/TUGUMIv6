# -*- coding: utf-8 -*-
"""
TUGUMIv6 Antigravity SDK Tool Registry
- Bridges Python tools to Antigravity SDK's native function declaration interface
- Exposes Termux privileged execution, Android inspection, web research, and file system operations
- Clean schemas with docstrings and type annotations for Gemini 3.8 Flash
"""

import subprocess
import shutil
import os
import sys
import io
import contextlib
import traceback
import urllib.request
import urllib.parse
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
try:
    import trafilatura
except ImportError:
    trafilatura = None

from core.loop_guard import default_loop_guard, LoopGuard
from tools.coding_tools import CodingTools
from tools.termux_tools import TermuxTools
from tools.file_tools import FileTools

@default_loop_guard.guard
def termux_exec(command: str) -> str:
    """Executes a bash shell command in the Termux Linux environment.
    
    Args:
        command: The shell command line to execute.
    Returns:
        JSON string containing exit_code, stdout, and stderr.
    """
    tt = TermuxTools()
    res = tt.run_termux_command(command, timeout=300.0)
    return json.dumps(res, ensure_ascii=False)

@default_loop_guard.guard
def termux_privileged_exec(command: str) -> str:
    """Executes a privileged command using Shizuku/rish, su, or adb if available.
    
    Args:
        command: The privileged command to execute.
    Returns:
        JSON string containing exit_code, stdout, stderr, and method_used.
    """
    tt = TermuxTools()
    res = tt.run_privileged_command(command, method="auto", timeout=180.0)
    return json.dumps(res, ensure_ascii=False)

@default_loop_guard.guard
def get_device_status() -> str:
    """Retrieves current Android device battery, temperature, charging status, and memory stats.
    
    Returns:
        JSON string of device telemetry.
    """
    data = {}
    try:
        bat_res = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=5.0)
        if bat_res.returncode == 0:
            data["battery"] = json.loads(bat_res.stdout)
    except Exception as e:
        data["battery_error"] = str(e)

    try:
        mem_res = subprocess.run(["free", "-m"], capture_output=True, text=True, timeout=5.0)
        if mem_res.returncode == 0:
            data["memory"] = mem_res.stdout.strip()
    except Exception as e:
        data["memory_error"] = str(e)

    return json.dumps(data, ensure_ascii=False)

@default_loop_guard.guard
def fetch_url_text(url: str, max_chars: int = 6000) -> str:
    """Extracts readable text content from a given web page URL for deep research.
    Prioritizes high-precision Trafilatura article extraction to eliminate HTML noise.
    
    Args:
        url: The web URL to fetch.
        max_chars: Maximum characters to return (default 6000).
    Returns:
        Extracted text content or error string.
    """
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept-Language": "ja,en;q=0.9"
            }
        )
        with urllib.request.urlopen(req, timeout=90.0) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        # 1. Trafilatura 高精度抽出（広告・ヘッダー・フッター・ナビゲーションの完全排除）
        if trafilatura:
            try:
                extracted = trafilatura.extract(html, include_comments=False, include_tables=True, output_format="txt")
                if extracted and len(extracted.strip()) > 50:
                    meta = trafilatura.extract_metadata(html)
                    meta_str = ""
                    if meta and meta.title:
                        meta_str = f"【タイトル】: {meta.title}\n"
                    body = meta_str + extracted
                    if len(body) > max_chars:
                        body = body[:max_chars] + f"\n... [中略（主要部{max_chars}文字抽出完了）] ..."
                    return body
            except Exception:
                pass

        # 2. BeautifulSoup / 正規表現フォールバック
        cleaned = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', cleaned)
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n... [中略（{max_chars}文字）] ..."
        return text or "[No text content extracted]"
    except Exception as e:
        return f"Failed to fetch {url}: {e}"

@default_loop_guard.guard
def web_search_duckduckgo(query: str, max_results: int = 5, deep_crawl: bool = True) -> str:
    """Searches the web using DuckDuckGo Lite with Mechanical Inline Deep Crawl.
    
    CRITICAL ARCHITECTURE UPGRADE:
    When deep_crawl=True (default), automatically extracts the full raw primary text (via Trafilatura)
    for the top 2 search results and injects them inline into the return JSON under 'extracted_body'.
    This physically guarantees primary source grounding without relying on soft prompt rules.
    
    Args:
        query: The search query keyword.
        max_results: Maximum number of search results to return (default 5).
        deep_crawl: If True, automatically fetches and includes full article text for top hits.
    Returns:
        JSON string of search results list with inline extracted bodies.
    """
    url = "https://lite.duckduckgo.com/lite/"
    data = urllib.parse.urlencode({"q": query}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; Termux) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
        }
    )
    results = []
    try:
        with urllib.request.urlopen(req, timeout=90.0) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        links = re.findall(r'<a\s+[^>]*?href=[\'\"]([^\'\"]+)[\'\"][^>]*?class=[\'\"]result-link[\'\"][^>]*?>(.*?)</a>', html, re.DOTALL)
        if not links:
            links = re.findall(r'<a\s+[^>]*?class=[\'\"]result-link[\'\"][^>]*?href=[\'\"]([^\'\"]+)[\'\"][^>]*?>(.*?)</a>', html, re.DOTALL)
        if not links:
            links = re.findall(r'<a[^>]+href=[\'\"]([^\'\"]+)[\'\"][^>]*>(.*?)</a>', html, re.DOTALL)
        snippets = re.findall(r'<td class=[\'\"]result-snippet[\'\"]>(.*?)</td>', html, re.DOTALL)

        for i in range(min(len(links), len(snippets), max_results)):
            link, raw_title = links[i]
            clean_title = re.sub(r'<[^>]+>', '', raw_title).strip()
            clean_snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip()
            if clean_title and link.startswith("http"):
                item = {
                    "title": clean_title,
                    "url": link.strip(),
                    "snippet": clean_snippet
                }
                # Inline Deep Crawl: 自動生本文抽出（上位2件の一次ソースを強制結合）
                if deep_crawl and i < 2:
                    try:
                        raw_body = fetch_url_text(link.strip(), max_chars=3000)
                        if raw_body and not raw_body.startswith("Failed to fetch"):
                            item["extracted_body"] = raw_body
                        else:
                            item["extracted_body"] = ""
                    except Exception:
                        item["extracted_body"] = ""
                results.append(item)
    except Exception as e:
        return json.dumps({"error": str(e), "query": query})

    return json.dumps(results, ensure_ascii=False)

@default_loop_guard.guard
def batch_parallel_web_research(topic_or_queries: str, max_sources: int = 5) -> str:
    """Performs lightning-fast multi-angle web research by concurrently searching multiple query angles
    and fetching primary source article text in parallel threads.
    
    CRITICAL EFFICIENCY UPGRADE:
    Eliminates slow, serial, 1-by-1 web browsing. With a single tool call, dynamically expands the topic
    into 4-5 multi-angle search queries, executes searches concurrently, deduplicates URLs, and fetches
    clean primary source article text (up to max_sources) in parallel via ThreadPoolExecutor.
    
    Args:
        topic_or_queries: Research topic (e.g. 'VIVANT 第20話 伏線 考察') or JSON array of query strings.
        max_sources: Maximum number of primary source article bodies to extract (default 5).
    Returns:
        JSON string containing all search queries executed, top unique hits, and full extracted source texts.
    """
    from core.deep_research_engine import DeepResearchEngine
    engine = DeepResearchEngine()

    queries = []
    # JSON 配列判定
    try:
        parsed = json.loads(topic_or_queries)
        if isinstance(parsed, list):
            queries = [str(x).strip() for x in parsed if str(x).strip()]
    except Exception:
        pass

    if not queries:
        category = engine.detect_category(topic_or_queries)
        queries = engine.generate_multi_angle_queries(topic_or_queries, category)

    raw_hits = []
    def _search_q(q: str):
        hits = []
        try:
            hits.extend(engine.search_duckduckgo(q, max_results=3))
            hits.extend(engine.fetch_google_news(q, max_results=2))
        except Exception:
            pass
        return hits

    with ThreadPoolExecutor(max_workers=min(len(queries), 8)) as executor:
        futs = [executor.submit(_search_q, q) for q in queries]
        for fut in as_completed(futs):
            try:
                res = fut.result()
                if res:
                    raw_hits.extend(res)
            except Exception:
                pass

    seen_urls = set()
    unique_hits = []
    for h in raw_hits:
        u = h.get("url", "")
        if u and u not in seen_urls:
            seen_urls.add(u)
            unique_hits.append(h)

    target_hits = unique_hits[:max_sources]
    sources = []
    def _fetch_hit(h: dict):
        u = h.get("url", "")
        text = engine.fetch_page_content(u, max_chars=8000)
        if text and len(text) > 100:
            return {
                "title": h.get("title", ""),
                "url": u,
                "content": text
            }
        return None

    if target_hits:
        with ThreadPoolExecutor(max_workers=min(len(target_hits), 6)) as executor:
            futs = [executor.submit(_fetch_hit, h) for h in target_hits]
            for fut in as_completed(futs):
                try:
                    res = fut.result()
                    if res:
                        sources.append(res)
                except Exception:
                    pass

    return json.dumps({
        "status": "success",
        "topic_or_queries": topic_or_queries,
        "queries_executed": queries,
        "total_unique_hits": len(unique_hits),
        "sources_extracted_count": len(sources),
        "sources": sources
    }, ensure_ascii=False)

@default_loop_guard.guard
def verify_causal_leverage(premise: str, parties_stakes: str, hypothesis: str) -> str:
    """Mechanical Invariant & Leverage Verification Engine for analysis and hypotheses.
    
    Validates logical consistency against 4 general-purpose first-principles invariants:
    1. Leverage & Single-Point-of-Value Retention Invariant: Does the party under coercion/negotiation
       maintain exclusive control of the critical asset? (If transferred/delegated away, the adversary
       loses rational incentive to preserve or bargain with the subject).
    2. Adversary / Counterparty Incentive Compatibility: Is each actor's behavior rational given their stakes?
    3. Epistemic Rigor & Anti-Slop Cliche Guard: Flags hand-waving tropes, placeholders, or unverified clichés.
    4. Stake & Actor Alignment: Extracts actors from `parties_stakes` and verifies structural coverage.
    
    Args:
        premise: The confirmed factual background or system state.
        parties_stakes: The involved actors/factions, their goals, and leverage.
        hypothesis: The prospective theory, architecture decision, or conclusion to stress-test.
    Returns:
        JSON string containing evaluation score (0-100), logical flaws, actor analysis, and recommended verdict.
    """
    import re as _re

    flaws = []
    score = 100

    hypo_text = (hypothesis or "").strip()
    premise_text = (premise or "").strip()
    stakes_text = (parties_stakes or "").strip()
    hypo_lower = hypo_text.lower()
    premise_lower = premise_text.lower()
    combined_context = f"{premise_lower} {stakes_text.lower()}"

    # Actor extraction from parties_stakes (splits by punctuation/delimiters)
    raw_actors = [
        _re.sub(r"（.*?）|\(.*?\)", "", tok).strip()
        for tok in _re.split(r"[、,，・/／\n]+", stakes_text)
        if tok.strip()
    ]
    extracted_actors = [a for a in raw_actors if len(a) >= 2][:10]

    # Invariant 1: Leverage & Survival / Bargaining Power Collapse Detection
    coercion_or_bargaining_markers = [
        "拉致", "拷問", "拘束", "人質", "監禁", "脅迫", "交渉", "買収", "独占", "切り札",
        "ロックイン", "hostage", "coercion", "torture", "leverage", "ransom", "extortion"
    ]
    detachment_or_transfer_markers = [
        "娘に託", "子供に託", "子どもに託", "娘に預", "子供に預", "子どもに預",
        "娘に持たせ", "子供に持たせ", "子どもに持たせ", "娘が持っ", "子供が持っ",
        "娘の中に", "子供の中に", "託されており", "託された", "第三者に託", "別人に預",
        "外部に譲渡", "すでに手放し", "本人は持っていない", "本人は知らない",
        "transferred to", "delegated to", "already handed over"
    ]
    retention_markers = [
        "頭の中にしかな", "脳内にしかな", "本人のみ", "本人しか知ら", "記憶の中に",
        "会えなければ絶対に教えない", "交渉力で生存", "切り札として保持", "独占保持",
        "only in their head", "sole holder", "retains exclusive"
    ]
    if any(k in hypo_lower for k in detachment_or_transfer_markers) and not any(r in hypo_lower for r in retention_markers):
        if any(k in combined_context for k in coercion_or_bargaining_markers):
            flaws.append({
                "type": "LEVERAGE_COLLAPSE_RISK",
                "severity": "CRITICAL",
                "flaw": (
                    "交渉または拘束下にある主体から核心資産（機密・データ・切り札）が第三者（娘・外部等）へ完全に切り離されている場合、"
                    "相手側が本人を生かし続けたり交渉に応じる合理的誘因（インセンティブ）が崩壊します。"
                    "本人が強気の交渉力を維持できている前提と矛盾するため、資産の排他的保持構造を再検証してください。"
                ),
            })
            score -= 40

    # Invariant 2: Counterparty Incentive Contradiction Detection
    incentive_contradiction_markers = [
        "理由もなく解放", "無条件で降伏", "無条件で開示", "利益に反して", "ボランティアで",
        "敵が親切で", "なぜか見逃す", "irrational", "for no reason", "unconditionally"
    ]
    if any(k in hypo_lower for k in incentive_contradiction_markers):
        flaws.append({
            "type": "INCENTIVE_CONTRADICTION",
            "severity": "HIGH",
            "flaw": "当事者・敵対者の合理的利害（ゲーム理論的最適行動）に反する無根拠な行動が仮定されています。",
        })
        score -= 30

    # Invariant 3: Epistemic Rigor & AI Slop / Cliche Detection
    cliche_markers = [
        "身代わり", "影武者", "記憶喪失", "お守り", "暗号ペンダント", "双子の", "実は夢",
        "魔法のよう", "奇跡的に", "なんとなく", "適当に", "todo", "tbd"
    ]
    if any(k in hypo_lower for k in cliche_markers):
        flaws.append({
            "type": "AI_SLOP_CLICHE",
            "severity": "WARNING",
            "flaw": (
                "安直なステレオタイプ・テンプレ展開（お守り、身代わり、影武者、記憶喪失等）または未検証の飛躍が含まれています。"
                "一次ソースの物理的描写・ログ・事実エビデンスに基づいているか再検証が必要です。"
            ),
        })
        score -= 25

    # Invariant 4: Empty or Overly Vague Hypothesis Guard
    if len(hypo_text) < 10:
        flaws.append({
            "type": "INSUFFICIENT_CAUSAL_MECHANISM",
            "severity": "WARNING",
            "flaw": "仮説の記述が短すぎ、因果メカニズム（誰が・どの切り札で・どう均衡を維持するか）が具体化されていません。",
        })
        score -= 25

    score = max(0, min(100, score))
    verdict = "PASS" if score >= 80 else ("WARNING" if score >= 60 else "FAIL")
    result = {
        "verdict": verdict,
        "consistency_score": score,
        "hypothesis_evaluated": hypothesis,
        "extracted_actors": extracted_actors,
        "invariants_checked": [
            "LEVERAGE_RETENTION_INVARIANT",
            "COUNTERPARTY_INCENTIVE_COMPATIBILITY",
            "ANTI_SLOP_CLICHE_GUARD",
            "CAUSAL_MECHANISM_COMPLETENESS",
        ],
        "identified_flaws": flaws,
        "first_principles_guidance": (
            "【第一原理チェック】1. 誰が交渉・システムの主導権（単一障害点／切り札）を握っているか？ "
            "2. 各プレイヤーにとって最も合理的かつ冷徹な最適戦略は何か？ "
            "3. 一次エビデンスから外れた陳腐なテンプレ推測を排除できているか？"
        ),
    }
    return json.dumps(result, ensure_ascii=False, indent=2)

@default_loop_guard.guard
def execute_code(code: str) -> str:
    """Executes arbitrary Python code in the TUGUMIv6 runtime environment (Code Mode).
    
    Use this for:
    - Data processing, mathematical calculations, algorithmic tasks, and complex logic
    - MCP tools programmatic aggregation via `from tools.tugumi_mcp import mcp`
    
    IMPORTANT RESTRICTIONS:
    - Do NOT use this for daily device tasks like timers, alarms, or sleep loops!
    - For device operations (alarm, timer, volume, notification, tts), use Termux:API commands or Android Intents directly via `termux_run_command`.
    - Do NOT write blocking `while True: time.sleep()` scripts.
    
    Args:
        code: Complete executable Python code block. Print desired output to stdout.
    Returns:
        JSON string containing stdout, stderr, and execution status.
    """
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    
    # Ensure TUGUMIv6 root is in sys.path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        
    global_env = {
        "__name__": "__main__",
        "__file__": "code_mode_runtime.py",
        "sys": sys,
        "os": os,
        "json": json,
        "CodingTools": CodingTools,
        "TermuxTools": TermuxTools,
        "FileTools": FileTools,
        "LoopGuard": LoopGuard,
    }
    
    try:
        from tools.tugumi_mcp import mcp
        global_env["mcp"] = mcp
    except Exception as e:
        stderr_buf.write(f"Note: tugumi_mcp preload warning: {e}\n")

    success = True
    error_msg = ""
    with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
        try:
            exec(code, global_env)
        except Exception:
            success = False
            error_msg = traceback.format_exc()

    return json.dumps({
        "success": success,
        "stdout": stdout_buf.getvalue(),
        "stderr": stderr_buf.getvalue(),
        "error": error_msg
    }, ensure_ascii=False)

# ==================== Coding & Autonomous SWE Tools ====================

@default_loop_guard.guard
def coding_grep_search(pattern: str, target_dir: str = "", file_glob: str = "*") -> str:
    """Grep-first search before read: searches for patterns across files and returns matching lines.

    Args:
        pattern: String or regex pattern to search for.
        target_dir: Directory to search in (defaults to workspace root).
        file_glob: File glob pattern filter (e.g. '*.py').
    Returns:
        JSON string of matched files, line numbers, and content snippets.
    """
    ct = CodingTools()
    res = ct.grep_search(pattern, target_dir=target_dir or None, file_glob=file_glob)
    return json.dumps(res, ensure_ascii=False)

@default_loop_guard.guard
def coding_read_lines(file_path: str, start_line: int = 1, end_line: int = 100) -> str:
    """Reads specific lines from a file using pinpoint line range (StartLine/EndLine).

    Args:
        file_path: Path to the target file.
        start_line: 1-indexed starting line number.
        end_line: 1-indexed ending line number.
    Returns:
        Numbered lines content string.
    """
    ct = CodingTools()
    try:
        return ct.read_lines(file_path, start_line, end_line)
    except Exception as e:
        return f"Error: {e}"

@default_loop_guard.guard
def coding_surgical_replace(file_path: str, target_content: str, replacement_content: str) -> str:
    """Performs surgical minimal diff replacement by exact match without creating .bak files.
    NOTE: Automatically executes built-in syntax validation (Syntax Gate) upon replacement,
    eliminating the need to call coding_check_syntax separately.

    Args:
        file_path: Target file path.
        target_content: Exact substring to be replaced.
        replacement_content: New replacement content.
    Returns:
        JSON string with success status and syntax validation:
        {"success": true, "file": file_path, "syntax_valid": true, "syntax_error": ""}
    """
    ct = CodingTools()
    try:
        res = ct.surgical_replace(file_path, target_content, replacement_content)
        if isinstance(res, dict):
            return json.dumps(res, ensure_ascii=False)
        return json.dumps({"success": True, "file": file_path, "syntax_valid": True})
    except Exception as e:
        return json.dumps({"success": False, "file": file_path, "error": str(e), "syntax_valid": False})

@default_loop_guard.guard
def coding_check_syntax(file_path: str) -> str:
    """Performs standalone syntax validation gate on Python or Shell scripts without running them.
    NOTE: coding_surgical_replace and file_write_safe ALREADY perform syntax validation automatically.
    Do NOT call this repeatedly or redundantly after edits.

    Args:
        file_path: Path to script file to validate.
    Returns:
        JSON string with validation status and error if any.
    """
    ct = CodingTools()
    res = ct.check_syntax(file_path)
    return json.dumps(res, ensure_ascii=False)

@default_loop_guard.guard
def coding_write_file(file_path: str, content: str) -> str:
    """Creates a new file or completely overwrites an existing file with built-in syntax validation.
    Creates parent directories automatically.

    Args:
        file_path: Target file path.
        content: Complete file content to write.
    Returns:
        JSON string containing success status, syntax validation, and file path.
    """
    ct = CodingTools()
    try:
        res = ct.write_file(file_path, content)
        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "file": file_path, "error": str(e), "syntax_valid": False})

@default_loop_guard.guard
def coding_batch_surgical_replace(replacements_json: str) -> str:
    """Performs multi-file batch surgical replacements for Dependency Chains before testing.

    Args:
        replacements_json: JSON string list of objects, each containing:
            'file_path', 'target_content', 'replacement_content'
    Returns:
        JSON string containing batch results, all_success flag, and per-file syntax validation.
    """
    ct = CodingTools()
    try:
        items = json.loads(replacements_json)
        if not isinstance(items, list):
            return json.dumps({"success": False, "error": "replacements_json must be a JSON array of objects."})
        res = ct.batch_surgical_replace(items)
        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


# ==================== Termux & Shizuku+ Super-Privilege Tools ====================

@default_loop_guard.guard
def termux_run_command(cmd: str, timeout: float = 300.0, cwd: str = "") -> str:
    """Executes a Termux shell command with explicit timeout and working directory.

    Args:
        cmd: Command string to execute.
        timeout: Execution timeout in seconds.
        cwd: Working directory path (optional).
    Returns:
        JSON string of exit_code, stdout, stderr.
    """
    tt = TermuxTools()
    res = tt.run_termux_command(cmd, timeout=timeout, cwd=cwd or None)
    return json.dumps(res, ensure_ascii=False)

@default_loop_guard.guard
def termux_privileged_command(cmd: str, method: str = "auto", timeout: float = 180.0) -> str:
    """Executes a privileged command via Shizuku+ (rish), su, or adb with automatic fallback.

    Args:
        cmd: Privileged command to execute.
        method: Privileged execution method ('auto', 'rish', 'su', 'adb').
        timeout: Execution timeout in seconds.
    Returns:
        JSON string containing exit_code, stdout, stderr, method_used.
    """
    tt = TermuxTools()
    res = tt.run_privileged_command(cmd, method=method, timeout=timeout)
    return json.dumps(res, ensure_ascii=False)

@default_loop_guard.guard
def android_ui_action(action_type: str, arg1: str = "", arg2: str = "", arg3: str = "", arg4: str = "") -> str:
    """Performs Android UI automation (touch, swipe, text, key) via Shizuku+/AICore+.

    Args:
        action_type: Action type ('touch', 'swipe', 'text', 'key').
        arg1: First parameter (e.g. x, text, or keycode).
        arg2: Second parameter (e.g. y).
        arg3: Third parameter (e.g. x2 for swipe).
        arg4: Fourth parameter (e.g. y2 for swipe).
    Returns:
        JSON string of action result.
    """
    tt = TermuxTools()
    args = [a for a in [arg1, arg2, arg3, arg4] if a != ""]
    res = tt.android_ui_action(action_type, *args)
    return json.dumps(res, ensure_ascii=False)

# ==================== Workspace & File Tools ====================

@default_loop_guard.guard
def file_list_tree(path: str = "", max_depth: int = 2) -> str:
    """Lists structured directory hierarchy tree.

    Args:
        path: Path to directory (defaults to home).
        max_depth: Maximum recursion depth.
    Returns:
        JSON string of directory tree structure.
    """
    target = path or "/data/data/com.termux/files/home"
    ft = FileTools(root_dir=target)
    res = ft.list_tree(target, max_depth=max_depth)
    return json.dumps(res, ensure_ascii=False)

@default_loop_guard.guard
def file_write_safe(target_path: str, content: str) -> str:
    """Safely writes file without polluting workspace with .bak files.
    Automatically performs built-in syntax validation for Python and Shell scripts.

    Args:
        target_path: Path of file to write.
        content: Text content to write.
    Returns:
        JSON string indicating success and syntax validation status.
    """
    ft = FileTools()
    ct = CodingTools()
    try:
        ok = ft.write_file_safe(target_path, content, make_backup=False)
        syntax_res = ct.check_syntax(target_path) if target_path.endswith((".py", ".sh", ".bash")) else {"valid": True, "error": ""}
        return json.dumps({
            "success": ok,
            "file": target_path,
            "syntax_valid": syntax_res.get("valid", True),
            "syntax_error": syntax_res.get("error", "")
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "file": target_path, "error": str(e), "syntax_valid": False})

def check_loop_status() -> str:
    """Returns current LoopGuard status, call counts, and history to prevent runaway loops."""
    return json.dumps({
        "threshold": default_loop_guard.threshold,
        "history_count": len(default_loop_guard.get_history()),
        "recent_calls": default_loop_guard.get_history()[-10:]
    }, ensure_ascii=False)

def termux_inspect_environment() -> str:
    """Deeply inspects the Termux environment (Android version, kernel, storage usage, RAM, zombie processes, Shizuku privileges, TLS/CA cert, SQLite WAL integrity, and Phantom Process Killer status)."""
    try:
        from core.termux_doctor import TermuxDoctor
        doctor = TermuxDoctor()
        rep = doctor.inspect_all()
        return json.dumps(rep, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def termux_maintain_environment(fix_all: bool = True) -> str:
    """Performs autonomous maintenance on Termux: cleans zombie processes, purges stale temp files, optimizes SQLite databases (WAL checkpoint), fixes TLS/SSL_CERT_FILE, and neutralizes Phantom Process Killer."""
    try:
        from core.termux_doctor import TermuxDoctor
        doctor = TermuxDoctor()
        rep = doctor.maintain_environment(fix_all=fix_all)
        return json.dumps(rep, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def memory_recall_context(query: str = "") -> str:
    """Recalls multi-tier cognitive memory: core master directives, preferences, structured facts, and FTS5 searchable relevant past interactions."""
    try:
        from memory.advanced_memory import AdvancedMemoryEngine
        mem = AdvancedMemoryEngine()
        context = mem.recall_cognitive_context(current_query=query)
        return json.dumps({"status": "success", "cognitive_context": context}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def memory_remember_fact(category: str, subject: str, fact_content: str, importance: int = 3) -> str:
    """Stores a critical fact, preference, user directive, or environmental configuration into persistent cognitive memory."""
    try:
        from memory.advanced_memory import AdvancedMemoryEngine
        mem = AdvancedMemoryEngine()
        mem_id = mem.learn_fact(category=category, subject=subject, fact_content=fact_content, importance=importance)
        return json.dumps({"status": "success", "memory_id": mem_id, "subject": subject}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def rag_sync_all_files(max_files: int = 10000, force: bool = False) -> str:
    """Scans and synchronizes all files and folders under /storage/emulated/0/TUGUMIDesk/TUGUMI_RAG recursively into SQLite FTS5 and Vector Cache.

    Args:
        max_files: Maximum number of files to index (default 10000).
        force: Whether to force full re-indexing of all files even if unchanged.
    Returns:
        JSON string containing newly_indexed_chunks, unchanged_files, and total_active_chunks.
    """
    try:
        from memory.rag_engine import HybridRAGEngine
        rag = HybridRAGEngine()
        stats = rag.ingest_all(max_files=max_files, force=force)
        return json.dumps({"status": "success", "stats": stats}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

def rag_search_knowledge(query: str, top_k: int = 5, folder_filter: str = "") -> str:
    """Performs hybrid deep search (FTS5 + dense vector embeddings) across all documents in TUGUMI_RAG knowledge base.

    Args:
        query: Search question or keywords.
        top_k: Number of most relevant knowledge chunks to return (default 5).
        folder_filter: Optional folder or category filter.
    Returns:
        JSON string containing matched document chunks, file sources, and relevance scores.
    """
    try:
        from memory.rag_engine import HybridRAGEngine
        rag = HybridRAGEngine()
        ff = folder_filter.strip() if folder_filter else None
        results = rag.search_hybrid(query=query, top_k=top_k, folder_filter=ff)
        return json.dumps({"status": "success", "count": len(results), "results": results}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

def rag_add_knowledge(title: str, content: str, category: str = "task_knowledge") -> str:
    """Adds a new knowledge document or finding into the TUGUMIv6 3072-dim Hybrid RAG knowledge base.

    Args:
        title: Clear title of the knowledge document.
        content: Full markdown or text content to index into RAG.
        category: Category / folder tag (e.g. 'task_knowledge', 'self_evolution', 'research', 'manual').
    Returns:
        JSON string confirming RAG registration and indexing status.
    """
    try:
        from memory.rag_engine import HybridRAGEngine
        rag = HybridRAGEngine()
        ok = rag.add_knowledge(title=title, text=content, category=category or "task_knowledge")
        return json.dumps({"status": "success" if ok else "error", "title": title, "category": category}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

def rag_list_files(folder_filter: str = "") -> str:
    """Lists all indexed files and folder statistics in the TUGUMIv6 RAG knowledge base (TUGUMI_RAG).

    Args:
        folder_filter: Optional substring to filter by folder or path.
    Returns:
        JSON string with total counts, folder breakdown, and indexed file list.
    """
    try:
        from memory.rag_engine import HybridRAGEngine
        rag = HybridRAGEngine()
        summary = rag.get_status_summary()
        files = rag.list_indexed_files(folder_filter=folder_filter if folder_filter else None)
        return json.dumps({
            "status": "success",
            "total_indexed_files": summary.get("total_indexed_files", 0),
            "total_chunks": summary.get("total_chunks", 0),
            "embedded_chunks": summary.get("embedded_chunks", 0),
            "folder_stats": summary.get("folder_stats", {}),
            "files_count": len(files),
            "files": files
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

@default_loop_guard.guard
def clone_website(url: str, custom_name: str = "", engine: str = "auto") -> str:
    """Clones a target website using Headless Chromium (Puppeteer) or HTTP engine, injecting <base href> to ensure all styles, images, and fonts render accurately. Saves the replica HTML to ~/cloned_sites and syncs to TUGUMIDesk.

    Args:
        url: The web URL to clone (e.g. https://example.com).
        custom_name: Optional custom identifier/folder name.
        engine: Rendering engine ('auto', 'puppeteer', 'http').
    Returns:
        JSON string containing site_id, title, path, preview_endpoint, and status.
    """
    try:
        from tools.web_cloner import WebCloner
        cloner = WebCloner()
        res = cloner.clone_url(url=url, custom_name=custom_name, engine=engine)
        return json.dumps({"status": "success", "result": res}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@default_loop_guard.guard
def clone_git_repository(
    url: str,
    dest_dir: str = "",
    shallow: bool = True,
    install_deps: bool = True,
    auto_heal: bool = False
) -> str:
    """Clones a GitHub/Git repository, automatically adapts to Termux (bionic libc, shebangs, paths, Python 3.14+), installs dependencies, and validates syntax.

    Args:
        url: The Git/GitHub repository URL or 'user/repo'.
        dest_dir: Optional custom destination folder.
        shallow: If True, uses shallow clone (--depth 1) for speed and disk conservation.
        install_deps: If True, automatically resolves and installs dependencies (pip/npm).
        auto_heal: Disabled by default to prevent background API token consumption.
    Returns:
        JSON string containing repo_name, target_dir, languages, adapt_stats, heal_stats, and status.
    """
    try:
        from tools.git_healer import GitHealer
        healer = GitHealer(verbose=False)
        res = healer.execute(
            repo_url=url,
            dest_dir=dest_dir or None,
            shallow=shallow,
            install_deps=install_deps,
            auto_heal=False,
            run_test=True
        )
        return json.dumps({"status": "success", "result": res}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@default_loop_guard.guard
def generate_image(prompt: str, filename: str = "", aspect_ratio: str = "1:1", style: str = "none") -> str:
    """Generates studio-grade photorealistic portraits (Tsugumi Model S Character DNA) or images using Gemini 3.1 Flash Image / Imagen 3.0 and saves them to TUGUMIDesk.

    Args:
        prompt: Description of the image or portrait to generate (English or Japanese). Supports 'tsugumi_model_s' / 'つぐみモデルS型'.
        filename: Optional target filename (e.g. 'cyber_avatar.png').
        aspect_ratio: Aspect ratio ('1:1', '16:9', '9:16', '4:3', '3:4', '21:9').
        style: Visual style preset ('cyberpunk', 'anime', 'photorealistic', 'ui_mockup', 'pixel_art', 'watercolor', 'none').
    Returns:
        JSON string containing success status, file_path, and message.
    """
    try:
        from tools.media_tools import ImageStudioEngine
        res = ImageStudioEngine.generate(prompt=prompt, filename=filename, aspect_ratio=aspect_ratio, style=style)
        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

@default_loop_guard.guard
def edit_image(image_path: str, action: str, params_json: str = "{}", output_filename: str = "") -> str:
    """Edits an existing image using Pillow (resize, crop, filter, adjust brightness/contrast, rotate, watermark).

    Args:
        image_path: Path to the existing image file.
        action: Edit action ('filter', 'adjust', 'resize', 'crop', 'rotate', 'flip', 'watermark').
        params_json: JSON string of parameters (e.g. '{"type": "cyberpunk"}' or '{"brightness": 1.2, "contrast": 1.3}').
        output_filename: Optional output filename.
    Returns:
        JSON string containing success status, file_path, and message.
    """
    try:
        from tools.media_tools import ImageStudioEngine
        params = json.loads(params_json) if isinstance(params_json, str) else params_json
        res = ImageStudioEngine.edit(image_path=image_path, action=action, params=params, output_filename=output_filename)
        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

@default_loop_guard.guard
def compose_images(image_paths_json: str, mode: str = "side_by_side", output_filename: str = "") -> str:
    """Composes two or more images into a single image (side-by-side, vertical, overlay/blend).

    Args:
        image_paths_json: JSON array of image file paths (e.g. '["/path/to/img1.png", "/path/to/img2.png"]').
        mode: Composition mode ('side_by_side', 'vertical', 'overlay', 'blend').
        output_filename: Optional output filename.
    Returns:
        JSON string containing success status, file_path, and message.
    """
    try:
        from tools.media_tools import ImageStudioEngine
        paths = json.loads(image_paths_json) if isinstance(image_paths_json, str) else image_paths_json
        res = ImageStudioEngine.compose(image_paths=paths, mode=mode, output_filename=output_filename)
        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

@default_loop_guard.guard
def convert_image_to_ascii(image_path: str, target_width: int = 44, color_mode: str = "truecolor_halfblock") -> str:
    """Converts an image into high-resolution ANSI TrueColor (24-bit RGB) ASCII art.

    Args:
        image_path: Path to the image file.
        target_width: Width in terminal characters (default: 44, fitted for mobile Termux screen).
        color_mode: 'truecolor_halfblock' (24-bit ANSI color) or 'ascii_grayscale'.
    Returns:
        ANSI formatted ASCII art string.
    """
    try:
        from tools.media_tools import ImageStudioEngine
        return ImageStudioEngine.to_ascii(image_path=image_path, target_width=target_width, color_mode=color_mode)
    except Exception as e:
        return f"Error: {str(e)}"

@default_loop_guard.guard
def compose_music(genre: str = "cyberpunk", bars: int = 8, title: str = "", bpm: int = 0) -> str:
    """Composes music and synthesizes multi-track MIDI, WAV, and MP3 audio files on Termux.

    Args:
        genre: Music genre/preset ('cyberpunk', 'lofi', 'chiptune', 'japanese', 'ambient').
        bars: Number of musical bars (default: 8).
        title: Title of the song/track.
        bpm: Optional custom BPM (beats per minute, 40-240).
    Returns:
        JSON string containing track title, genre, bpm, duration_sec, midi_path, wav_path, and mp3_path.
    """
    try:
        from tools.media_tools import MusicCompositionEngine
        custom_bpm = bpm if bpm > 0 else None
        res = MusicCompositionEngine.compose(genre=genre, bars=bars, title=title, custom_bpm=custom_bpm)
        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

@default_loop_guard.guard
def download_media_video(
    url: str,
    quality: str = "best",
    format_type: str = "mp4",
    audio_only: bool = False,
    audio_format: str = "mp3"
) -> str:
    """Universal Video & Audio Downloader for YouTube, X (Twitter), Bilibili, TikTok, Instagram, Niconico, and more.

    Args:
        url: The video URL (YouTube, X/Twitter, Bilibili, TikTok, Instagram, Niconico, Reddit, etc.)
        quality: Video quality ('best', '1080p', '720p', '480p', '360p', 'worst'). Default is 'best'.
        format_type: Video container format ('mp4', 'webm', 'mkv'). Default is 'mp4'.
        audio_only: If True, extract only audio as MP3. Default is False.
        audio_format: Audio format when audio_only is True ('mp3', 'm4a', 'flac', 'wav', 'opus'). Default is 'mp3'.
    Returns:
        JSON string containing download status, platform, title, uploader, saved file path, and output directory.
    """
    try:
        import sys
        downloader_script_dir = os.path.expanduser("~/.agents/skills/video-downloader/scripts")
        if downloader_script_dir not in sys.path:
            sys.path.insert(0, downloader_script_dir)
        import download_video as dv

        res = dv.download_video(
            url=url,
            quality=quality,
            format_type=format_type,
            audio_only=audio_only,
            audio_format=audio_format
        )

        # 拓磨様がいつもの「YouTube」アルバムからも即座に見られるよう安全にミラー配置
        file_path = res.get("file_path")
        save_dir = res.get("output_dir", "")
        yt_dir = "/storage/emulated/0/Download/YouTube"
        if file_path and os.path.isfile(file_path):
            try:
                os.makedirs(yt_dir, exist_ok=True)
                if os.path.abspath(save_dir) != os.path.abspath(yt_dir):
                    shutil.copy2(file_path, yt_dir)
            except Exception:
                pass

        # メディアスキャン発行
        try:
            scan_bin = shutil.which("termux-media-scan") or "/data/data/com.termux/files/usr/bin/termux-media-scan"
            if os.path.isfile(scan_bin):
                subprocess.run([scan_bin, "-r", save_dir], capture_output=True, timeout=30)
                subprocess.run([scan_bin, "-r", yt_dir], capture_output=True, timeout=30)
        except Exception:
            pass

        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

# ==================== Research & Reporting Tools ====================

@default_loop_guard.guard
def research_save_report(title: str, markdown_content: str, category: str = "リサーチ") -> str:
    """Saves a comprehensive markdown research report into TUGUMIDesk with date and category hierarchy.
    
    Args:
        title: Clear title of the report in Japanese.
        markdown_content: The full markdown content of the report.
        category: Subdirectory in TUGUMIDesk (e.g. 'リサーチ', 'AI・エージェント', 'システム開発').
    Returns:
        JSON string containing success status, path, and filename.
    """
    try:
        from tools.research_tools import ResearchTools
        rt = ResearchTools()
        res = rt.save_markdown_report(title=title, content=markdown_content, category=category)
        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

@default_loop_guard.guard
def research_generate_html_report(title: str, markdown_content: str, theme: str = "Midnight Galaxy") -> str:
    """Renders a markdown report into a visual, standalone Tailwind CSS HTML document.
    
    Args:
        title: Report title.
        markdown_content: Markdown body.
        theme: Theme preset ('Midnight Galaxy', 'Cyberpunk', 'Modern Light').
    Returns:
        HTML string of the rendered document.
    """
    try:
        from tools.research_tools import ResearchTools
        rt = ResearchTools()
        return rt.render_beautiful_html(title=title, markdown_content=markdown_content, theme=theme)
    except Exception as e:
        return f"<!-- Error rendering HTML report: {e} -->"

# ==================== MCP 2.0 Native Function Bridges ====================

@default_loop_guard.guard
def mcp_check_failure_risk(query: str) -> str:
    """危険な操作や未知の作業を実行する前に、過去の失敗教訓やアンチパターン（SQLite FTS5）を事前検索してリスクを回避します。
    
    Args:
        query: 実行予定の操作内容やキーワード（例: 'git push', 'pip install', 'sqlite lock', 'shebang'）。
    Returns:
        過去の失敗事例、禁止行為、および推奨される安全な代替策を含むJSON文字列。
    """
    try:
        from tools.tugumi_mcp import mcp
        res = mcp.failure_guard.check_failure_risk(query=query)
        return json.dumps(res, ensure_ascii=False) if isinstance(res, (dict, list)) else str(res)
    except Exception as e:
        return json.dumps({"error": f"Failure guard check failed: {e}"})

@default_loop_guard.guard
def mcp_record_failure_lesson(keyword: str, cause: str, forbidden_action: str, correct_alternative: str) -> str:
    """新しく発見された失敗の根本原因、絶対に繰り返してはならない禁止事項、および実証済みの正しい代替策をSQLite FTS5失敗記憶に永続記録します。
    
    Args:
        keyword: 失敗を識別・トリガーする特徴的キーワード。
        cause: 技術的な詳細根本原因。
        forbidden_action: 今後二度と行ってはならない誤った操作。
        correct_alternative: 実証された正しい解決コマンドまたは代替手段。
    Returns:
        記録結果と登録IDを含む確認JSON文字列。
    """
    try:
        from tools.tugumi_mcp import mcp
        res = mcp.failure_guard.record_failure_lesson(
            keyword=keyword,
            cause=cause,
            forbidden_action=forbidden_action,
            correct_alternative=correct_alternative
        )
        return json.dumps(res, ensure_ascii=False) if isinstance(res, (dict, list)) else str(res)
    except Exception as e:
        return json.dumps({"error": f"Recording failure lesson failed: {e}"})

@default_loop_guard.guard
def mcp_race_resolve(date: str, venue: str, race_number: int, race_name: str = "") -> str:
    """自然言語のレース指定（開催日、競馬場、レース番号）から、一意に確定・検証された正規レース情報を特定します。
    
    Args:
        date: レース開催日（YYYY-MM-DD または YYYYMMDD形式）。
        venue: 競馬場名（例: '東京', '中山', '阪神', '京都', '大井'）。
        race_number: レース番号（1〜12）。
        race_name: 任意のレース名（例: '天皇賞（秋）'）。
    Returns:
        確定したレースIDおよび詳細情報のJSON文字列。
    """
    try:
        from tools.tugumi_mcp import mcp
        res = mcp.horse_racing.race_resolve(date=date, venue=venue, race_number=race_number, race_name=race_name)
        return json.dumps(res, ensure_ascii=False) if isinstance(res, (dict, list)) else str(res)
    except Exception as e:
        return json.dumps({"error": f"Horse race resolution failed: {e}"})

@default_loop_guard.guard
def mcp_get_user_tweets(username: str, max_tweets: int = 5) -> str:
    """x-scraper MCPサーバーを経由して、指定したX (Twitter) ユーザーの最新ツイート一覧を取得します。
    
    Args:
        username: Xのユーザー名（@マーク不要）。
        max_tweets: 取得するツイートの最大件数（デフォルト: 5）。
    Returns:
        最新ツイート本文および投稿日時の整形文字列。
    """
    try:
        from tools.tugumi_mcp import mcp
        res = mcp.twitter.get_user_tweets(username=username, max_tweets=max_tweets)
        return str(res)
    except Exception as e:
        return json.dumps({"error": f"Fetching user tweets failed: {e}"})

@default_loop_guard.guard
def mcp_call(server_name: str, tool_name: str, arguments_json: str = "{}") -> str:
    """稼働中の任意のMCPサーバー（github, playwright, research, tugumi_v6等）のツールを直接呼び出して実行します。
    
    Args:
        server_name: 対象MCPサーバー名（例: 'github', 'playwright', 'research', 'tugumi_v6'）。
        tool_name: 実行するMCPツール名（例: 'search_repositories', 'playwright_scrape'）。
        arguments_json: ツール引数を格納したJSON文字列。
    Returns:
        MCPツールの実行結果（JSON文字列またはテキスト）。
    """
    try:
        from tools.tugumi_mcp import mcp
        args = json.loads(arguments_json) if arguments_json else {}
        res = mcp.call(server_name, tool_name, **args)
        return json.dumps(res, ensure_ascii=False) if isinstance(res, (dict, list)) else str(res)
    except Exception as e:
        return json.dumps({"error": f"MCP tool execution failed: {e}"})

@default_loop_guard.guard
def mcp2_start_task(server_name: str, tool_name: str, arguments_json: str = "{}") -> str:
    """MCP 2.0 Tasks Extension仕様に準拠し、長時間実行される非同期バックグラウンドタスクを開始します。
    
    Args:
        server_name: 対象MCPサーバー名。
        tool_name: 非同期実行するツール名。
        arguments_json: ツール引数のJSON文字列。
    Returns:
        task_idおよび初期状態を含むJSON文字列。
    """
    try:
        from tools.tugumi_mcp import mcp
        args = json.loads(arguments_json) if arguments_json else {}
        res = mcp.start_task(server_name, tool_name, **args)
        return json.dumps(res, ensure_ascii=False) if isinstance(res, (dict, list)) else str(res)
    except Exception as e:
        return json.dumps({"error": f"MCP 2.0 task start failed: {e}"})

@default_loop_guard.guard
def mcp2_task_status(server_name: str, task_id: str) -> str:
    """MCP 2.0 Tasks Extensionに準拠し、実行中または完了した非同期タスクの進捗状況・実行結果を照会します。
    
    Args:
        server_name: 対象MCPサーバー名。
        task_id: 照会するタスクの一意識別子（task_id）。
    Returns:
        タスクのステータス、進捗度、または実行結果を含むJSON文字列。
    """
    try:
        from tools.tugumi_mcp import mcp
        res = mcp.task_status(server_name, task_id)
        return json.dumps(res, ensure_ascii=False) if isinstance(res, (dict, list)) else str(res)
    except Exception as e:
        return json.dumps({"error": f"MCP 2.0 task status query failed: {e}"})

@default_loop_guard.guard
def mcp2_task_cancel(server_name: str, task_id: str) -> str:
    """MCP 2.0 Tasks Extensionに準拠し、実行中の非同期バックグラウンドタスクを安全に中断・キャンセルします。
    
    Args:
        server_name: 対象MCPサーバー名。
        task_id: キャンセルするタスクの一意識別子（task_id）。
    Returns:
        キャンセル処理結果を含む確認JSON文字列。
    """
    try:
        from tools.tugumi_mcp import mcp
        res = mcp.cancel_task(server_name, task_id)
        return json.dumps(res, ensure_ascii=False) if isinstance(res, (dict, list)) else str(res)
    except Exception as e:
        return json.dumps({"error": f"MCP 2.0 task cancel failed: {e}"})

@default_loop_guard.guard
def mcp2_render_app(server_name: str, app_name: str, app_args_json: str = "{}") -> str:
    """MCP 2.0 Apps Extensionに準拠し、WebUI / Bento Grid用の対話型UIコンポーネントビューを描画します。
    
    Args:
        server_name: 対象MCPサーバー名。
        app_name: 描画するUIビュー名。
        app_args_json: 描画パラメータのJSON文字列。
    Returns:
        HTMLまたはJSON形式のUIコンポーネントデータ。
    """
    try:
        from tools.tugumi_mcp import mcp
        args = json.loads(app_args_json) if app_args_json else {}
        res = mcp.render_app(server_name, app_name, **args)
        return json.dumps(res, ensure_ascii=False) if isinstance(res, (dict, list)) else str(res)
    except Exception as e:
        return json.dumps({"error": f"MCP 2.0 app render failed: {e}"})

@default_loop_guard.guard
def mcp2_protocol_info(server_name: str = "") -> str:
    """MCP 2.0仕様に基づく各MCPサーバーとのプロトコルバージョン合意状況および対応機能バッジを取得します。
    
    Args:
        server_name: 照会するサーバー名（省略時は全アクティブサーバーの情報を返却）。
    Returns:
        プロトコルバージョンおよび機能サポート情報を含むJSON文字列。
    """
    try:
        from tools.tugumi_mcp import mcp
        if server_name:
            ver = mcp.get_negotiated_version(server_name)
            tools = mcp.list_tools(server_name)
            return json.dumps({
                "server": server_name,
                "protocol_version": ver,
                "tools_count": len(tools),
                "is_mcp2": ver >= "2026-07-28" or ver >= "2025-11-25"
            }, ensure_ascii=False)
        else:
            servers = mcp.list_servers()
            info = {}
            for s in servers:
                info[s] = {
                    "negotiated_version": mcp.get_negotiated_version(s),
                    "is_mcp2": mcp.get_negotiated_version(s) >= "2025-11-25"
                }
            return json.dumps(info, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"MCP 2.0 info failed: {e}"})

@default_loop_guard.guard
def mcp_metasploit_list_exploits(search_term: str = "") -> str:
    """Metasploit Frameworkで利用可能なエクスプロイトモジュールを検索・一覧取得します。
    
    Args:
        search_term: 検索するキーワード（例: 'eternalblue', 'smb', 'apache'）。
    Returns:
        合致するモジュール名と概要の一覧JSON文字列。
    """
    try:
        from tools.tugumi_mcp import mcp
        res = mcp.metasploit.list_exploits(search_term=search_term)
        return json.dumps(res, ensure_ascii=False) if isinstance(res, (dict, list)) else str(res)
    except Exception as e:
        return json.dumps({"error": f"Metasploit list exploits failed: {e}"})

@default_loop_guard.guard
def mcp_metasploit_run_exploit(exploit_name: str, rhost: str, rport: int, lhost: str, lport: int, payload_name: str = "", extra_options_json: str = "{}") -> str:
    """Metasploit Frameworkのエクスプロイトモジュールをターゲットに対して安全に実行します。
    
    Args:
        exploit_name: 実行するエクスプロイトモジュール名（例: 'unix/webapp/wp_admin_shell_upload'）。
        rhost: 標的IPアドレスまたはホスト名。
        rport: 標的ポート番号。
        lhost: リバース接続を受信するローカルIPアドレス。
        lport: リバース接続を受信するローカルポート番号。
        payload_name: ペイロード名（例: 'generic/shell_reverse_tcp'）。
        extra_options_json: 追加オプションのJSON文字列。
    Returns:
        エクスプロイト実行結果およびセッション確立状態のJSON文字列。
    """
    try:
        from tools.tugumi_mcp import mcp
        extra = json.loads(extra_options_json) if extra_options_json else {}
        options = {"RHOSTS": rhost, "RPORT": rport, **extra}
        res = mcp.metasploit.run_exploit(
            exploit_name=exploit_name,
            options=options,
            payload_name=payload_name if payload_name else None,
            payload_options={"LHOST": lhost, "LPORT": lport} if lhost else None
        )
        return json.dumps(res, ensure_ascii=False) if isinstance(res, (dict, list)) else str(res)
    except Exception as e:
        return json.dumps({"error": f"Metasploit run exploit failed: {e}"})

# ==================== Company Knowledge Hub Bridges ====================

@default_loop_guard.guard
def company_knowledge_search(query: str, category: str = "") -> str:
    """Searches the shared company knowledge base (~/.tugumi/company_knowledge.db) using FTS5.
    IMPORTANT: This returns verified organizational knowledge. Used strictly as temporary Read-Only context; do NOT import these records into local personal memory DB.
    
    Args:
        query: Keywords to search in corporate articles.
        category: Optional category filter (e.g. 'システム共通基盤', '業務マニュアル', '端末環境仕様').
    Returns:
        JSON string list of matched articles with id, category, title, and content.
    """
    sys.path.insert(0, os.path.expanduser("~/.tugumi"))
    try:
        from knowledge_hub import CompanyKnowledgeHub
        hub = CompanyKnowledgeHub()
        hits = hub.search(query=query, category=category if category else None, limit=4)
        return json.dumps({"status": "success", "hits": hits}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

@default_loop_guard.guard
def company_knowledge_publish(title: str, content: str, category: str = "システム共通基盤", tags: str = "") -> str:
    """Publishes a verified corporate knowledge document to the shared company knowledge base.
    
    Args:
        title: Title of the knowledge article.
        content: Markdown content of verified findings, system specs, or procedures.
        category: Category (e.g. 'システム共通基盤', '業務マニュアル', '端末環境仕様', 'AI・エージェント').
        tags: Comma-separated tags.
    Returns:
        JSON string with created article ID.
    """
    sys.path.insert(0, os.path.expanduser("~/.tugumi"))
    try:
        from knowledge_hub import CompanyKnowledgeHub
        hub = CompanyKnowledgeHub()
        aid = hub.publish(title=title, content=content, category=category, author_agent="TUGUMIv6", tags=tags)
        return json.dumps({"status": "success", "article_id": aid}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

def get_tugumi_tools() -> list:
    """Returns the list of all registered callable tools for Antigravity SDK."""
    tools = [
        execute_code,
        termux_exec,
        termux_privileged_exec,
        get_device_status,
        batch_parallel_web_research,
        web_search_duckduckgo,
        fetch_url_text,
        verify_causal_leverage,
        clone_website,
        clone_git_repository,
        # Creative Media, Image & Music
        generate_image,
        edit_image,
        compose_images,
        convert_image_to_ascii,
        compose_music,
        download_media_video,
        # Coding & Autonomous SWE
        coding_grep_search,
        coding_read_lines,
        coding_surgical_replace,
        coding_write_file,
        coding_batch_surgical_replace,
        coding_check_syntax,
        # Termux & Shizuku+
        termux_run_command,
        termux_privileged_command,
        android_ui_action,
        termux_inspect_environment,
        termux_maintain_environment,
        # Memory & Cognitive Retention
        memory_recall_context,
        memory_remember_fact,
        # RAG Knowledge Engine (TUGUMI_RAG / Obsidian / TUGUMIDesk)
        rag_sync_all_files,
        rag_search_knowledge,
        rag_add_knowledge,
        rag_list_files,
        # Company Knowledge Hub (Shared Database)
        company_knowledge_search,
        company_knowledge_publish,
        # File Tools
        file_list_tree,
        file_write_safe,
        # Loop Guard
        check_loop_status,
        # Research & Reporting
        research_save_report,
        research_generate_html_report,
        # MCP 2.0 Native Function Bridges & Stateless/Tasks/Apps Extensions (2026-07-28)
        mcp_check_failure_risk,
        mcp_record_failure_lesson,
        mcp_race_resolve,
        mcp_get_user_tweets,
        mcp_call,
        mcp_metasploit_list_exploits,
        mcp_metasploit_run_exploit,
        mcp2_start_task,
        mcp2_task_status,
        mcp2_task_cancel,
        mcp2_render_app,
        mcp2_protocol_info,
    ]
    try:
        from core.dynamic_skill_synthesizer import DynamicSkillSynthesizer
        synth = DynamicSkillSynthesizer()
        registered_names = {getattr(t, "__name__", "") for t in tools}
        for func in synth.registry.values():
            fn_name = getattr(func, "__name__", "")
            if func not in tools and fn_name and fn_name not in registered_names and fn_name != "main":
                tools.append(func)
                registered_names.add(fn_name)
    except Exception:
        pass
    return tools
