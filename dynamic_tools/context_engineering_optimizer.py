#!/data/data/com.termux/files/usr/bin/python3
"""Synthesized Skill: context_engineering_optimizer
Description: Auto-synthesized tool from self-evolution topic: 2026 AI Agent Protocols & Context Engineering
"""

# 工具名: context_engineering_optimizer
def context_engineering_optimizer(
    raw_context: str = "",
    target_token_budget: int = 2048,
    page_size: int = 512
) -> dict:
    """TUGUMIv6 2026 Context Engineering Engine.

    Termux (aarch64) 上で動作する高精度コンテキスト最適化ツール。
    1. 反復ログ・トレースバックの無劣化意味論的圧縮 (Semantic Lossless Compression)
    2. Page-based KV Cache (Prefix Cache Alignment) によるブロック分割とハッシュ生成
    3. 複雑度・エラーシグナルに基づく 2026 Test-Time Compute (TTC) 予算モードの自動判定

    Args:
        raw_context (str): 最適化対象のトランスクリプト、シェル出力、ログ文字列
        target_token_budget (int): 許容最大トークン予算 (デフォルト: 2048)
        page_size (int): 1ブロックあたりの文字数 (デフォルト: 512)

    Returns:
        dict: 圧縮率、キャッシュハッシュ、TTC推奨モード、最適化済みコンテキスト文字列
    """
    import hashlib
    import re
    import time

    start_time = time.perf_counter()
    original_length = len(raw_context)

    if not raw_context or original_length == 0:
        return {
            "status": "empty",
            "metrics": {
                "original_chars": 0,
                "optimized_chars": 0,
                "compression_ratio_pct": 0.0,
                "estimated_token_savings": 0,
                "execution_time_ms": 0.0,
            },
            "cache_governance": {
                "total_pages": 0,
                "page_size_bytes": page_size,
                "evicted_blocks": 0,
                "prefix_cache_hashes": [],
            },
            "ttc_budget_recommendation": {
                "mode": "non_thinking",
                "complexity_score": 0,
                "recommended_tier": "Flash-Lite / Ultra-Fast",
            },
            "optimized_context": "",
        }

    # 1. 意味論的クレンジング（行末空白、過剰改行、連続同一出力の畳み込み）
    cleaned = re.sub(r"\r\n", "\n", raw_context)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]+$", "", cleaned, flags=re.MULTILINE)

    lines = cleaned.splitlines()
    deduped_lines = []
    repeat_count = 1
    last_line = None

    for line in lines:
        if line == last_line and len(line.strip()) > 3:
            repeat_count += 1
        else:
            if repeat_count > 2:
                deduped_lines.append(
                    f"  ... [folded {repeat_count - 1} identical lines] ..."
                )
            elif repeat_count == 2:
                deduped_lines.append(last_line)
            deduped_lines.append(line)
            last_line = line
            repeat_count = 1
    if repeat_count > 2:
        deduped_lines.append(
            f"  ... [folded {repeat_count - 1} identical lines] ..."
        )
    elif repeat_count == 2:
        deduped_lines.append(last_line)

    structured_text = "\n".join(deduped_lines)

    # 2. Page-based KV Cache ブロック分割 (Prefix Cache Alignment)
    pages = []
    current_page = []
    current_len = 0

    for line in structured_text.splitlines(keepends=True):
        current_page.append(line)
        current_len += len(line)
        if current_len >= page_size:
            pages.append("".join(current_page))
            current_page = []
            current_len = 0
    if current_page:
        pages.append("".join(current_page))

    # 3. ページごとの重要度スコアリング & 差分ハッシュ計算
    preserve_patterns = [
        re.compile(p, re.IGNORECASE)
        for p in [
            r"def\s+\w+\(",
            r"class\s+\w+",
            r"error",
            r"exception",
            r"traceback",
            r"failed",
            r"warning",
            r"return\s+",
            r"\[CRITICAL\]",
        ]
    ]

    page_records = []
    estimated_target_chars = target_token_budget * 4

    for idx, page_content in enumerate(pages):
        score = 0
        for pat in preserve_patterns:
            score += len(pat.findall(page_content)) * 2

        # 構造密度スコア（コード構文文字の比率）
        code_markers = sum(1 for c in page_content if c in "{}[]()<>;=/*-+")
        score += int(code_markers / 15)

        page_hash = hashlib.sha256(page_content.encode("utf-8")).hexdigest()[
            :16
        ]
        page_records.append({
            "page_id": idx,
            "cache_hash": page_hash,
            "score": score,
            "content": page_content,
            "length": len(page_content),
            "evicted": False,
        })

    # 4. バジェット超過時の選択的プルーニング（中間ブロック・低スコア優先）
    total_chars = sum(p["length"] for p in page_records)
    if total_chars > estimated_target_chars and len(page_records) > 2:
        # 最初と最後のページは文脈保全のため保護
        candidates = sorted(
            [p for p in page_records[1:-1]], key=lambda x: x["score"]
        )
        for cand in candidates:
            if total_chars <= estimated_target_chars:
                break
            if cand["score"] < 5:
                summary_line = f"\n[PagedContext: Block {cand['page_id']} (hash:{cand['cache_hash']}) pruned to conserve TTC budget. Score: {cand['score']}]\n"
                diff = cand["length"] - len(summary_line)
                if diff > 0:
                    cand["content"] = summary_line
                    cand["length"] = len(summary_line)
                    cand["evicted"] = True
                    total_chars -= diff

    final_context = "".join(p["content"] for p in page_records)
    compressed_length = len(final_context)
    savings_pct = round(
        (1.0 - (compressed_length / max(1, original_length))) * 100, 2
    )
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    # 5. 2026 Test-Time Compute (TTC) 判定ロジック
    total_score = sum(p["score"] for p in page_records)
    has_critical_error = bool(
        re.search(r"traceback|exception|error|failed", raw_context, re.IGNORECASE)
    )

    if has_critical_error or total_score > 30:
        ttc_mode = "deep_reasoning"
        recommended_model_tier = "Pro / High-Reasoning (TTC Scaling Enabled)"
    elif total_score > 10:
        ttc_mode = "standard_reasoning"
        recommended_model_tier = "Flash / Balanced (Single-Pass CoT)"
    else:
        ttc_mode = "non_thinking"
        recommended_model_tier = (
            "Flash-Lite / Ultra-Fast (Zero-TTC Direct Execution)"
        )

    return {
        "status": "success",
        "metrics": {
            "original_chars": original_length,
            "optimized_chars": compressed_length,
            "compression_ratio_pct": savings_pct,
            "estimated_token_savings": max(
                0, (original_length - compressed_length) // 4
            ),
            "execution_time_ms": elapsed_ms,
        },
        "cache_governance": {
            "total_pages": len(page_records),
            "page_size_bytes": page_size,
            "evicted_blocks": sum(1 for p in page_records if p["evicted"]),
            "prefix_cache_hashes": [p["cache_hash"] for p in page_records[:3]],
        },
        "ttc_budget_recommendation": {
            "mode": ttc_mode,
            "complexity_score": total_score,
            "recommended_tier": recommended_model_tier,
        },
        "optimized_context": final_context,
    }


def main():
    import sys
    import os
    import json

    raw_text = ""
    target_budget = 2048

    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        target_path = os.path.expanduser(sys.argv[1])
        if os.path.exists(target_path):
            try:
                with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                    raw_text = f.read()
            except Exception as e:
                print(f"Error reading file: {e}", file=sys.stderr)
        else:
            raw_text = sys.argv[1]

    if len(sys.argv) > 2 and sys.argv[2].isdigit():
        target_budget = int(sys.argv[2])

    if not raw_text:
        default_memory = os.path.expanduser("~/.agents/TSUGUMI_MEMORY.md")
        if os.path.exists(default_memory):
            try:
                with open(default_memory, "r", encoding="utf-8", errors="ignore") as f:
                    raw_text = f.read()
            except Exception:
                pass

    if not raw_text:
        raw_text = (
            "[PROMPT & CONTEXT OPTIMIZATION SCAN]\n"
            "TUGUMIv6 Context Engineering Optimizer\n"
            "Evaluating token efficiency, redundant whitespace, stack traces, and cache pinning.\n"
            "Status: System operational. Prompt caching optimization enabled.\n"
        )

    res = context_engineering_optimizer(raw_text, target_token_budget=target_budget)

    if "--json" in sys.argv:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    C_CYAN = "\033[38;5;51m"
    C_GREEN = "\033[38;5;48m"
    C_YELLOW = "\033[38;5;220m"
    C_MAGENTA = "\033[38;5;201m"
    C_WHITE = "\033[38;5;255m"
    C_MUTED = "\033[38;5;242m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    print(f"{C_CYAN}{BOLD}╔══════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{C_CYAN}{BOLD}║     📊 TUGUMIv6 2026 Context Engineering & トークン効率最適化診断        ║{RESET}")
    print(f"{C_CYAN}{BOLD}╚══════════════════════════════════════════════════════════════════════════╝{RESET}")

    m = res["metrics"]
    print(f"{C_YELLOW}{BOLD}[トークン効率・圧縮メトリクス]{RESET}")
    print(f"  • 元文字数: {C_WHITE}{m['original_chars']:,}{RESET} 文字  →  最適化後: {C_WHITE}{m['optimized_chars']:,}{RESET} 文字")
    print(f"  • 削減率: {C_GREEN}{BOLD}{m['compression_ratio_pct']}%{RESET}  (推定節約トークン: {C_GREEN}{m['estimated_token_savings']:,}{RESET} tokens)")
    print(f"  • 処理時間: {C_WHITE}{m['execution_time_ms']} ms{RESET}")

    gov = res["cache_governance"]
    print(f"\n{C_MAGENTA}{BOLD}[KV Cache ガバナンス＆ブロック管理]{RESET}")
    print(f"  • ブロックサイズ: {C_WHITE}{gov['page_size_bytes']}{RESET} bytes  |  総ページ数: {C_WHITE}{gov['total_pages']}{RESET}")
    print(f"  • Evicted (破棄) ブロック数: {C_WHITE}{gov['evicted_blocks']}{RESET}")
    print(f"  • プレフィックスハッシュ: {C_WHITE}{', '.join(gov['prefix_cache_hashes']) or 'N/A'}{RESET}")

    ttc = res["ttc_budget_recommendation"]
    print(f"\n{C_GREEN}{BOLD}[TTC推論予算＆モデル推奨]{RESET}")
    print(f"  • 推定TTCモード: {C_CYAN}{BOLD}{ttc['mode'].upper()}{RESET}  (複雑度スコア: {ttc['complexity_score']})")
    print(f"  • 推奨モデルTier: {C_WHITE}{ttc['recommended_tier']}{RESET}")

    print(f"\n{C_MUTED}──────────────────────────────────────────────────────────────────────────{RESET}")
    print(f"{C_GREEN}✔ コンテキストエンジニアリング診断完了 (Exit Code 0){RESET}")

if __name__ == '__main__':
    main()
