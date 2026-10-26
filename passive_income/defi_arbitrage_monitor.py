# -*- coding: utf-8 -*-
"""
TUGUMIv6 DeFi & Crypto Cross-Exchange Arbitrage Monitor
- Compares real-time price spreads across multiple public exchange endpoints (Binance vs Bybit)
- Detects cross-market spatial arbitrage opportunities (Buy on ExA -> Sell on ExB)
- Zero-auth public REST APIs with high-resiliency timeout & error handling
"""

import urllib.request
import json
import time
from typing import Dict, Any, List, Optional

class DeFiArbitrageMonitor:
    """Real-Time Cross-Exchange Arbitrage Opportunity Scanner (Binance vs Bybit)"""
    def __init__(self):
        self.last_scan_time = 0.0

    def fetch_binance_tickers(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        """BinanceパブリックAPIから最良買値・売値を取得"""
        url = "https://api.binance.com/api/v3/ticker/bookTicker"
        req = urllib.request.Request(url, headers={"User-Agent": "Termux-TUGUMIv6/DeFi-Monitor"})
        with urllib.request.urlopen(req, timeout=30.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        ticker_map = {}
        for item in data:
            sym = item.get("symbol")
            if sym in symbols:
                ticker_map[sym] = {
                    "bid": float(item.get("bidPrice", 0.0)),
                    "ask": float(item.get("askPrice", 0.0))
                }
        return ticker_map

    def fetch_bybit_tickers(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        """BybitパブリックAPIから現物スポットの最良買値・売値を取得"""
        url = "https://api.bybit.com/v5/market/tickers?category=spot"
        req = urllib.request.Request(url, headers={"User-Agent": "Termux-TUGUMIv6/DeFi-Monitor"})
        with urllib.request.urlopen(req, timeout=30.0) as resp:
            raw = json.loads(resp.read().decode("utf-8"))

        items = raw.get("result", {}).get("list", [])
        ticker_map = {}
        for item in items:
            sym = item.get("symbol")
            if sym in symbols:
                bid = float(item.get("bid1Price") or item.get("lastPrice") or 0.0)
                ask = float(item.get("ask1Price") or item.get("lastPrice") or 0.0)
                ticker_map[sym] = {"bid": bid, "ask": ask}
        return ticker_map

    def scan_cross_exchange_spreads(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """BinanceとBybitの実勢価格を突合し、取引所間アービトラージ機会を算出"""
        target_symbols = symbols or ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        opportunities = []

        try:
            binance_tickers = self.fetch_binance_tickers(target_symbols)
        except Exception as e:
            binance_tickers = {}
            opportunities.append({"error": f"Binance fetch error: {e}"})

        try:
            bybit_tickers = self.fetch_bybit_tickers(target_symbols)
        except Exception as e:
            bybit_tickers = {}
            opportunities.append({"error": f"Bybit fetch error: {e}"})

        timestamp = time.time()

        for sym in target_symbols:
            b_data = binance_tickers.get(sym)
            by_data = bybit_tickers.get(sym)

            if not b_data or not by_data:
                continue

            b_bid = b_data["bid"]
            b_ask = b_data["ask"]
            by_bid = by_data["bid"]
            by_ask = by_data["ask"]

            # ルート1: Binanceで買い (ask) -> Bybitで売り (bid)
            spread_bin_to_by = ((by_bid - b_ask) / b_ask) * 100.0 if b_ask > 0 else 0.0

            # ルート2: Bybitで買い (ask) -> Binanceで売り (bid)
            spread_by_to_bin = ((b_bid - by_ask) / by_ask) * 100.0 if by_ask > 0 else 0.0

            # 最良ルート判定
            if spread_bin_to_by >= spread_by_to_bin:
                best_spread = spread_bin_to_by
                direction = "Binance (買) ➔ Bybit (売)"
                buy_ex, sell_ex = "Binance", "Bybit"
                buy_price, sell_price = b_ask, by_bid
            else:
                best_spread = spread_by_to_bin
                direction = "Bybit (買) ➔ Binance (売)"
                buy_ex, sell_ex = "Bybit", "Binance"
                buy_price, sell_price = by_ask, b_bid

            b_mid = (b_bid + b_ask) / 2.0
            by_mid = (by_bid + by_ask) / 2.0
            price_diff_pct = (abs(b_mid - by_mid) / min(b_mid, by_mid)) * 100.0 if min(b_mid, by_mid) > 0 else 0.0

            opportunities.append({
                "symbol": sym,
                # 下位互換用フィールド (CLI / WebUI 既存描画対応)
                "bid": b_bid,
                "ask": b_ask,
                "spread_pct": round(best_spread, 4),
                # 取引所間詳細フィールド
                "binance_price": round(b_mid, 2),
                "bybit_price": round(by_mid, 2),
                "binance_bid": b_bid,
                "binance_ask": b_ask,
                "bybit_bid": by_bid,
                "bybit_ask": by_ask,
                "cross_diff_pct": round(price_diff_pct, 4),
                "direction": direction,
                "buy_exchange": buy_ex,
                "sell_exchange": sell_ex,
                "buy_price": buy_price,
                "sell_price": sell_price,
                "is_profitable": best_spread > 0.0,
                "timestamp": timestamp
            })

        self.last_scan_time = timestamp
        return opportunities

    def scan_binance_ticker_spreads(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """既存インターフェース互換性ラッパー（内部で最新のBinance vs Bybit実取引所間スプレッドを返却）"""
        return self.scan_cross_exchange_spreads(symbols=symbols)

if __name__ == "__main__":
    monitor = DeFiArbitrageMonitor()
    print("\033[38;2;0;240;255m╔═══════════════════════════════════════════════════════════════╗\033[0m")
    print("\033[38;2;0;240;255m║   🎯 DeFi アービトラージ＆スプレッドスキャナー (TUGUMIv6)       ║\033[0m")
    print("\033[38;2;0;240;255m╚═══════════════════════════════════════════════════════════════╝\033[0m")
    print("  \033[1;36mスキャン対象:\033[0m Binance vs Bybit (Spot 最良買値・売値)\n")
    opps = monitor.scan_cross_exchange_spreads()
    for op in opps:
        sym = op["symbol"]
        b_p = op["binance_price"]
        by_p = op["bybit_price"]
        spread = op["spread_pct"]
        direction = op["direction"]
        color = "\033[38;5;82m" if spread > 0 else "\033[38;5;244m"
        print(f"  ● {sym:8} | Binance: {b_p:10} | Bybit: {by_p:10} | {color}Spread: {spread:+.4f}%\033[0m | 方向: {direction}")
    print(f"\n  \033[38;5;82m✔ DeFiスキャン完了 ({len(opps)}ペア取得)\033[0m")

