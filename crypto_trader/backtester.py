import asyncio
from typing import Dict, Any, List, Optional
from .binance_client import BinanceClient
from .analysis_engine import MarketAnalyzer


class QuantBacktester:
    """
    TUGUMIv6 Institutional Quant Backtester v2.0
    実ヒストリカルKlineデータ（1h / 15m）を用いて、
    - クオンツAlpha Scoreエントリー
    - 3重防護（スイング利確+25% / トレーリング+15%開始 / 最終損切-8%）
    - スマート・マイクロトレーリング（+4.0%起動 ➔ -1.8%反落またはRSI過熱反転で確実利確）
    - タイムストップ＆弱体化エグジット
    - Binance現物手数料（標準0.1% / BNB割引0.075%）
    を忠実に再現し、勝率・Profit Factor・最大ドローダウン・期待値を検証する。
    """

    def __init__(self, client: Optional[BinanceClient] = None):
        self.client = client or BinanceClient()
        self.analyzer = MarketAnalyzer()

    async def run_symbol_backtest(
        self,
        symbol: str = "SUIJPY",
        interval: str = "1h",
        limit: int = 240,
        initial_jpy: float = 10000.0,
        fee_rate: float = 0.00075,
        entry_alpha_threshold: float = 58.0,
        smart_trail_trigger_pct: float = 3.5,
        smart_trail_drop_pct: float = 1.5,
        hard_tp_pct: float = 25.0,
        hard_sl_pct: float = -6.5,
    ) -> Dict[str, Any]:
        klines = await self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
        if not klines or not isinstance(klines, list) or len(klines) < 60:
            return {
                "status": "ERROR",
                "symbol": symbol,
                "message": f"ヒストリカルデータ不足 ({len(klines) if isinstance(klines, list) else 0}本)",
            }

        closes = [float(k[4]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        timestamps = [int(k[0]) for k in klines]

        cash_jpy = initial_jpy
        position_qty = 0.0
        entry_price = 0.0
        highest_price = 0.0
        entry_index = 0
        trades: List[Dict[str, Any]] = []
        equity_curve: List[float] = []
        peak_equity = initial_jpy
        max_drawdown_pct = 0.0

        # ウォームアップ期間: 50本目からシミュレーション開始
        for idx in range(50, len(klines)):
            window = klines[max(0, idx - 80) : idx + 1]
            c_price = closes[idx]
            h_price = highs[idx]
            l_price = lows[idx]

            # 現在の評価額を記録
            current_equity = cash_jpy + (position_qty * c_price if position_qty > 0 else 0.0)
            equity_curve.append(current_equity)
            if current_equity > peak_equity:
                peak_equity = current_equity
            if peak_equity > 0:
                dd = (peak_equity - current_equity) / peak_equity * 100.0
                if dd > max_drawdown_pct:
                    max_drawdown_pct = dd

            # シグナル計算
            sig = self.analyzer.analyze_klines(window, symbol=symbol)
            alpha = float(sig.get("alpha_score", 50.0))
            ind = sig.get("indicators", {})
            rsi = float(ind.get("rsi", 50.0))
            stoch_k = float(ind.get("stoch_rsi_k", 50.0))
            macd_Rising = bool(ind.get("macd_hist_rising", False))

            if position_qty == 0.0:
                # エントリー判定: Alphaスコア基準クリア、または強い反発セットアップ
                is_strong_setup = (
                    alpha >= entry_alpha_threshold
                    or (rsi < 38.0 and stoch_k < 25.0 and macd_Rising)
                    or (alpha >= 54.0 and macd_Rising and 40.0 <= rsi <= 66.0)
                )
                if is_strong_setup and cash_jpy >= 100.0:
                    invest_jpy = cash_jpy
                    net_jpy = invest_jpy * (1.0 - fee_rate)
                    position_qty = net_jpy / c_price
                    cash_jpy = 0.0
                    entry_price = c_price
                    highest_price = c_price
                    entry_index = idx
            else:
                # ポジション保有中: 最高値更新チェック（高値ベース）
                if h_price > highest_price:
                    highest_price = h_price

                pnl_pct_close = (c_price - entry_price) / entry_price * 100.0
                pnl_pct_high = (highest_price - entry_price) / entry_price * 100.0
                pnl_pct_low = (l_price - entry_price) / entry_price * 100.0
                drop_from_high_pct = (c_price - highest_price) / highest_price * 100.0
                bars_held = idx - entry_index

                exit_reason = None
                exit_price = c_price

                # 1. ハード利確 (+25%)
                if pnl_pct_high >= hard_tp_pct:
                    exit_reason = f"HARD_TP (+{hard_tp_pct:.1f}%)"
                    exit_price = entry_price * (1.0 + hard_tp_pct / 100.0)
                # 2. 15%超えからの本格トレーリング (-3.5%反落)
                elif pnl_pct_high >= 15.0 and drop_from_high_pct <= -3.5:
                    exit_reason = f"TRAIL_15 (Peak +{pnl_pct_high:.1f}%)"
                    exit_price = c_price
                # 3. スマート・マイクロトレーリング (+3.5%以上到達後、ピークから-1.5%反落またはRSI過熱失速)
                elif pnl_pct_high >= smart_trail_trigger_pct and (
                    drop_from_high_pct <= -smart_trail_drop_pct
                    or (rsi >= 72.0 and not macd_Rising)
                ):
                    exit_reason = f"SMART_TRAIL (Peak +{pnl_pct_high:.1f}%)"
                    exit_price = c_price
                # 4. 短期モメンタム利確 (+2.2%以上かつストキャスティクス過熱デッドクロス)
                elif pnl_pct_close >= 2.2 and stoch_k >= 85.0 and not macd_Rising:
                    exit_reason = f"MOMENTUM_TP (+{pnl_pct_close:.2f}%)"
                    exit_price = c_price
                # 5. トレンド崩れ早期撤退 (保有18時間以上で含み損かつAlpha < 36)
                elif bars_held >= 18 and pnl_pct_close <= -2.2 and alpha < 36.0:
                    exit_reason = f"ALPHA_DECAY ({pnl_pct_close:.2f}%)"
                    exit_price = c_price
                # 6. ハード損切り (-6.5% 〜 -8.0%)
                elif pnl_pct_low <= hard_sl_pct:
                    exit_reason = f"STOP_LOSS ({hard_sl_pct:.1f}%)"
                    exit_price = entry_price * (1.0 + hard_sl_pct / 100.0)

                if exit_reason:
                    gross_jpy = position_qty * exit_price
                    net_jpy = gross_jpy * (1.0 - fee_rate)
                    trade_return_pct = (exit_price * (1.0 - fee_rate) - entry_price * (1.0 + fee_rate)) / (
                        entry_price * (1.0 + fee_rate)
                    ) * 100.0
                    trades.append(
                        {
                            "symbol": symbol,
                            "entry_price": round(entry_price, 6),
                            "exit_price": round(exit_price, 6),
                            "return_pct": round(trade_return_pct, 2),
                            "bars_held": bars_held,
                            "reason": exit_reason,
                            "timestamp": timestamps[idx],
                        }
                    )
                    cash_jpy = net_jpy
                    position_qty = 0.0
                    entry_price = 0.0
                    highest_price = 0.0

        # 最終バーで未決済ポジションがあれば時価評価
        final_equity = cash_jpy + (position_qty * closes[-1] * (1.0 - fee_rate) if position_qty > 0 else 0.0)
        total_return_pct = (final_equity - initial_jpy) / initial_jpy * 100.0
        buy_and_hold_pct = (closes[-1] - closes[50]) / closes[50] * 100.0 if closes[50] > 0 else 0.0

        wins = [t for t in trades if t["return_pct"] > 0]
        losses = [t for t in trades if t["return_pct"] <= 0]
        win_rate = (len(wins) / len(trades) * 100.0) if trades else 0.0
        gross_profit = sum(t["return_pct"] for t in wins)
        gross_loss = abs(sum(t["return_pct"] for t in losses))
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (99.9 if gross_profit > 0 else 0.0)

        return {
            "status": "SUCCESS",
            "symbol": symbol,
            "interval": interval,
            "bars_tested": len(klines) - 50,
            "initial_jpy": initial_jpy,
            "final_jpy": round(final_equity, 2),
            "total_return_pct": round(total_return_pct, 2),
            "buy_and_hold_pct": round(buy_and_hold_pct, 2),
            "outperformance_pct": round(total_return_pct - buy_and_hold_pct, 2),
            "total_trades": len(trades),
            "win_count": len(wins),
            "loss_count": len(losses),
            "win_rate_pct": round(win_rate, 1),
            "profit_factor": profit_factor,
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "open_position": position_qty > 0,
            "recent_trades": trades[-5:],
        }

    async def run_portfolio_backtest(
        self,
        symbols: Optional[List[str]] = None,
        interval: str = "1h",
        limit: int = 240,
    ) -> Dict[str, Any]:
        target_symbols = symbols or ["SUIJPY", "PEPEJPY", "SOLJPY", "XRPJPY", "DOGEJPY", "BTCJPY"]
        tasks = [self.run_symbol_backtest(sym, interval=interval, limit=limit) for sym in target_symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results = []
        for r in results:
            if isinstance(r, dict) and r.get("status") == "SUCCESS":
                valid_results.append(r)

        if not valid_results:
            return {"status": "ERROR", "message": "有効なバックテスト結果を取得できませんでした。"}

        avg_return = sum(r["total_return_pct"] for r in valid_results) / len(valid_results)
        avg_bh = sum(r["buy_and_hold_pct"] for r in valid_results) / len(valid_results)
        total_trades = sum(r["total_trades"] for r in valid_results)
        total_wins = sum(r["win_count"] for r in valid_results)
        overall_win_rate = (total_wins / total_trades * 100.0) if total_trades > 0 else 0.0
        max_dd = max(r["max_drawdown_pct"] for r in valid_results)

        valid_results.sort(key=lambda x: x["total_return_pct"], reverse=True)

        return {
            "status": "SUCCESS",
            "interval": interval,
            "bars_tested": limit - 50,
            "symbols_tested": len(valid_results),
            "avg_strategy_return_pct": round(avg_return, 2),
            "avg_buy_and_hold_pct": round(avg_bh, 2),
            "alpha_outperformance_pct": round(avg_return - avg_bh, 2),
            "total_trades": total_trades,
            "overall_win_rate_pct": round(overall_win_rate, 1),
            "worst_max_drawdown_pct": round(max_dd, 2),
            "symbol_results": valid_results,
        }
