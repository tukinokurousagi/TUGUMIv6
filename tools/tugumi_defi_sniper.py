#!/data/data/com.termux/files/usr/bin/python3
"""TUGUMI DeFi / CEX Arbitrage Sniper
Real-time cryptocurrency ticker scanner & arbitrage opportunity detector.
Dedicated to 拓磨様 by つぐみ (TUGUMI)
"""

import sys
import time
import json
import urllib.request
import urllib.error
import concurrent.futures
from typing import Dict, Any, List, Optional

C_CYAN = "\033[38;5;51m"
C_BLUE = "\033[38;5;39m"
C_GREEN = "\033[38;5;48m"
C_YELLOW = "\033[38;5;220m"
C_ORANGE = "\033[38;5;208m"
C_RED = "\033[38;5;196m"
C_PURPLE = "\033[38;5;141m"
C_WHITE = "\033[38;5;255m"
C_MUTED = "\033[38;5;242m"
RESET = "\033[0m"
BOLD = "\033[1m"

DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT", "DOGEUSDT"]

def print_banner():
    print(f"""{C_YELLOW}{BOLD}
╔══════════════════════════════════════════════════════════════════════════════╗
║        🎯  TUGUMI DeFi / CEX ARBITRAGE SNIPER ENGINE (v6.2)                  ║
║        Real-Time Orderbook Scanning & Cross-Exchange Spread Detection        ║
╚══════════════════════════════════════════════════════════════════════════════╝{RESET}""")

def fetch_binance_tickers(symbols: List[str]) -> Dict[str, Dict[str, float]]:
    """Binance Public BookTicker API から最良気配値を取得"""
    res = {}
    sym_query = json.dumps(symbols)
    url = f"https://api.binance.com/api/v3/ticker/bookTicker?symbols={sym_query}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TUGUMI-Sniper/1.0"})
        with urllib.request.urlopen(req, timeout=20.0) as resp:
            data = json.loads(resp.read().decode())
            for item in data:
                s = item.get("symbol")
                bid = float(item.get("bidPrice", 0))
                ask = float(item.get("askPrice", 0))
                if bid > 0 and ask > 0:
                    res[s] = {
                        "bid": bid,
                        "ask": ask,
                        "mid": round((bid + ask) / 2.0, 4),
                        "spread_pct": round(((ask - bid) / ask) * 100, 4)
                    }
    except Exception:
        # 個別フォールバック
        for s in symbols:
            try:
                single_url = f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={s}"
                req = urllib.request.Request(single_url, headers={"User-Agent": "TUGUMI-Sniper/1.0"})
                with urllib.request.urlopen(req, timeout=15.0) as resp:
                    item = json.loads(resp.read().decode())
                    bid = float(item.get("bidPrice", 0))
                    ask = float(item.get("askPrice", 0))
                    if bid > 0 and ask > 0:
                        res[s] = {"bid": bid, "ask": ask, "mid": round((bid + ask) / 2.0, 4), "spread_pct": round(((ask - bid) / ask) * 100, 4)}
            except Exception:
                pass
    return res

def fetch_bybit_tickers(symbols: List[str]) -> Dict[str, Dict[str, float]]:
    """Bybit Public Ticker API から最良気配値を取得"""
    res = {}
    url = "https://api.bybit.com/v5/market/tickers?category=spot"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TUGUMI-Sniper/1.0"})
        with urllib.request.urlopen(req, timeout=20.0) as resp:
            data = json.loads(resp.read().decode())
            items = data.get("result", {}).get("list", [])
            for item in items:
                s = item.get("symbol")
                if s in symbols:
                    bid = float(item.get("bid1Price", 0) or 0)
                    ask = float(item.get("ask1Price", 0) or 0)
                    last = float(item.get("lastPrice", 0) or 0)
                    if bid <= 0 or ask <= 0:
                        bid = ask = last
                    if bid > 0 and ask > 0:
                        res[s] = {
                            "bid": bid,
                            "ask": ask,
                            "mid": round((bid + ask) / 2.0, 4),
                            "spread_pct": round(((ask - bid) / ask) * 100, 4)
                        }
    except Exception:
        pass
    return res

def scan_arbitrage(symbols: Optional[List[str]] = None) -> Dict[str, Any]:
    """Binance & Bybit 間のティッカーを取得し、アービトラージ機会を解析"""
    if not symbols:
        symbols = DEFAULT_SYMBOLS

    start_t = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f_binance = executor.submit(fetch_binance_tickers, symbols)
        f_bybit = executor.submit(fetch_bybit_tickers, symbols)
        binance_data = f_binance.result()
        bybit_data = f_bybit.result()

    elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)

    opportunities = []
    pair_reports = []

    for sym in symbols:
        b_info = binance_data.get(sym)
        y_info = bybit_data.get(sym)

        if not b_info or not y_info:
            continue

        # Strategy 1: Buy Binance Ask, Sell Bybit Bid
        gross_spread_1 = round(((y_info["bid"] - b_info["ask"]) / b_info["ask"]) * 100, 3)
        # Strategy 2: Buy Bybit Ask, Sell Binance Bid
        gross_spread_2 = round(((b_info["bid"] - y_info["ask"]) / y_info["ask"]) * 100, 3)

        best_spread = max(gross_spread_1, gross_spread_2)
        direction = ""
        buy_ex = ""
        sell_ex = ""
        buy_p = 0.0
        sell_p = 0.0

        if gross_spread_1 > gross_spread_2:
            direction = "Buy Binance -> Sell Bybit"
            buy_ex = "Binance"
            sell_ex = "Bybit"
            buy_p = b_info["ask"]
            sell_p = y_info["bid"]
        else:
            direction = "Buy Bybit -> Sell Binance"
            buy_ex = "Bybit"
            sell_ex = "Binance"
            buy_p = y_info["ask"]
            sell_p = b_info["bid"]

        report = {
            "symbol": sym,
            "binance_mid": b_info["mid"],
            "bybit_mid": y_info["mid"],
            "binance_spread_pct": b_info["spread_pct"],
            "bybit_spread_pct": y_info["spread_pct"],
            "arb_direction": direction,
            "best_spread_pct": best_spread,
            "buy_exchange": buy_ex,
            "buy_price": buy_p,
            "sell_exchange": sell_ex,
            "sell_price": sell_p
        }
        pair_reports.append(report)

        if best_spread > 0.05:  # 0.05%以上の価格乖離をチャンスとみなす
            opportunities.append(report)

    return {
        "status": "success",
        "timestamp": time.time(),
        "latency_ms": elapsed_ms,
        "pairs_scanned": len(pair_reports),
        "arbitrage_opportunities": opportunities,
        "details": pair_reports
    }

def main():
    if "--json" in sys.argv:
        res = scan_arbitrage()
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    print_banner()
    print(f"{C_CYAN}[*] Binance & Bybit オーダーブック・リアルタイム気配値を並行スキャン中...{RESET}\n")

    res = scan_arbitrage()
    if res["status"] != "success" or not res["details"]:
        print(f"{C_RED}❌ 気配値の取得に失敗しました。ネットワーク接続を確認してください。{RESET}")
        sys.exit(1)

    print(f"{C_WHITE}{BOLD}{'通貨ペア':<10} {'Binance (Mid)':<15} {'Bybit (Mid)':<15} {'最適ルート':<26} {'利鞘 (Gross)':<12}{RESET}")
    print(f"{C_MUTED}{'─'*80}{RESET}")

    for item in res["details"]:
        sym = item["symbol"]
        b_p = f"${item['binance_mid']:,.2f}" if item['binance_mid'] >= 1 else f"${item['binance_mid']:.5f}"
        y_p = f"${item['bybit_mid']:,.2f}" if item['bybit_mid'] >= 1 else f"${item['bybit_mid']:.5f}"
        spread = item["best_spread_pct"]

        if spread > 0.1:
            spread_str = f"{C_GREEN}{BOLD}+{spread:.3f}%{RESET}"
            dir_str = f"{C_GREEN}{item['arb_direction']}{RESET}"
        elif spread > 0.0:
            spread_str = f"{C_CYAN}+{spread:.3f}%{RESET}"
            dir_str = f"{C_WHITE}{item['arb_direction']}{RESET}"
        else:
            spread_str = f"{C_MUTED}{spread:.3f}%{RESET}"
            dir_str = f"{C_MUTED}{item['arb_direction']}{RESET}"

        print(f"{C_YELLOW}{BOLD}{sym:<10}{RESET} {b_p:<15} {y_p:<15} {dir_str:<35} {spread_str}")

    print(f"\n{C_YELLOW}{BOLD}[アービトラージ機会スナイプ判定]{RESET}")
    opps = res["arbitrage_opportunities"]
    if opps:
        for opp in opps:
            print(f"  {C_GREEN}⚡ [OPPORTUNITY] {opp['symbol']}: {opp['arb_direction']} | 予想利鞘: +{opp['best_spread_pct']}%{RESET}")
            print(f"     買値: {opp['buy_exchange']} ${opp['buy_price']}  →  売値: {opp['sell_exchange']} ${opp['sell_price']}")
    else:
        print(f"  {C_CYAN}ℹ️ 現在の主要ペア価格差は効率的均衡圏内（スプレッド < 0.05%）です。監視を継続します。{RESET}")

    print(f"\n{C_MUTED}スキャン完了: {res['pairs_scanned']}ペア | API通信レイテンシ: {res['latency_ms']} ms | Exit Code 0{RESET}")

if __name__ == "__main__":
    main()
