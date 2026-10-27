#!/data/data/com.termux/files/usr/bin/python3
# -*- coding: utf-8 -*-
"""
TUGUMIv6 Tools - Binance Crypto Tools v2.0 (Institutional Quant Edition)
統合バイナンスAI運用ツール（CLI / Web UI / 自律パトロール / エージェント 共通）
Author: つぐみ (TUGUMI) for 拓磨様
"""

import os
import sys
import json
import asyncio
import sqlite3
from typing import Dict, Any, List, Optional

TUGUMI_ROOT = "/data/data/com.termux/files/home/TUGUMIv6"
if TUGUMI_ROOT not in sys.path:
    sys.path.insert(0, TUGUMI_ROOT)

from crypto_trader.binance_client import (
    BinanceClient,
    quantize_lot_quantity,
    ALL_VALID_JPY_SYMBOLS,
)
from crypto_trader.analysis_engine import MarketAnalyzer
from crypto_trader.live_executor import LiveExecutor
from crypto_trader.backtester import QuantBacktester

CONFIG_PATH = os.path.join(TUGUMI_ROOT, "crypto_trader", "config.json")
DB_PATH = os.path.join(TUGUMI_ROOT, "crypto_trader", "trader_history.db")
POSITIONS_FILE = "/data/data/com.termux/files/home/.agents/binance/positions_state.json"


class BinanceCryptoTools:
    """TUGUMIv6 CLI・WebUI・自律パトロールから利用可能なバイナンスクオンツ自動運用ツールセット v2.0"""

    def __init__(self, config_path: str = CONFIG_PATH):
        self.config_path = config_path
        self.config = self._load_config()
        self.api_key = self.config.get("api_key", "")
        self.api_secret = self.config.get("api_secret", "")
        self.base_url = self.config.get("base_url", "https://api.binance.com")
        self.initial_capital_jpy = float(self.config.get("initial_capital_jpy", 887.0))

    def _get_clients(self):
        client = BinanceClient(api_key=self.api_key, api_secret=self.api_secret, base_url=self.base_url)
        executor = LiveExecutor(
            api_key=self.api_key,
            api_secret=self.api_secret,
            base_url=self.base_url,
            client=client,
        )
        return client, executor

    def _load_config(self) -> Dict[str, Any]:
        cfg = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            except Exception:
                cfg = {}

        api_k = cfg.get("api_key") or os.environ.get("BINANCE_API_KEY")
        api_s = cfg.get("api_secret") or os.environ.get("BINANCE_API_SECRET")
        secrets_file = "/data/data/com.termux/files/home/.agents/binance/secrets.json"
        if (not api_k or not api_s) and os.path.exists(secrets_file):
            try:
                with open(secrets_file, "r", encoding="utf-8") as sf:
                    s_data = json.load(sf)
                    api_k = api_k or s_data.get("api_key")
                    api_s = api_s or s_data.get("api_secret")
            except Exception:
                pass

        cfg["api_key"] = api_k or ""
        cfg["api_secret"] = api_s or ""
        return cfg

    def _load_positions_state(self) -> Dict[str, Any]:
        state: Dict[str, Any] = {}
        if os.path.exists(POSITIONS_FILE):
            try:
                with open(POSITIONS_FILE, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except Exception:
                state = {}

        # DBの直近BUY履歴から未登録銘柄の取得単価も補完
        if os.path.exists(DB_PATH):
            try:
                with sqlite3.connect(DB_PATH, timeout=15.0) as conn:
                    c = conn.cursor()
                    c.execute(
                        "SELECT symbol, price FROM live_trades WHERE side = 'BUY' ORDER BY id ASC"
                    )
                    for sym, price in c.fetchall():
                        if sym and float(price) > 0:
                            if sym not in state or float(state[sym].get("entry_price", 0.0)) <= 0:
                                state[sym] = {
                                    "entry_price": float(price),
                                    "highest_price": float(price),
                                }
            except Exception:
                pass
        return state

    async def get_balance(self) -> Dict[str, Any]:
        """実口座残高＋時価評価＋LOT_SIZE売却可否・端数（Dust）精密診断"""
        client, executor = self._get_clients()
        try:
            balances_dict = await executor.get_real_balances()
            jpy_prices = await client.get_all_jpy_prices()
            pos_state = self._load_positions_state()

            formatted_list = []
            total_jpy_value = 0.0
            cash_jpy = 0.0
            bnb_jpy = 0.0
            sellable_positions = []
            locked_dust_positions = []

            for asset, b in balances_dict.items():
                free = float(b.get("free", 0.0))
                locked = float(b.get("locked", 0.0))
                total = free + locked

                if asset == "JPY":
                    price_jpy = 1.0
                    val_jpy = total
                    cash_jpy = free
                    sellable_qty = free
                    sellable_jpy = free
                    dust_qty = 0.0
                    dust_jpy = 0.0
                    can_sell = True
                    entry_price = 1.0
                    highest_price = 1.0
                    pnl_pct = 0.0
                else:
                    sym = f"{asset}JPY"
                    price_jpy = float(jpy_prices.get(sym, 0.0))
                    val_jpy = total * price_jpy
                    if asset == "BNB":
                        bnb_jpy = val_jpy

                    q_info = quantize_lot_quantity(sym, free, price_jpy)
                    sellable_qty = float(q_info["sellable_qty"])
                    sellable_jpy = float(q_info["notional_jpy"])
                    dust_qty = float(q_info["dust_qty"])
                    dust_jpy = dust_qty * price_jpy
                    can_sell = bool(q_info["can_market_sell"])

                    st = pos_state.get(sym, {})
                    entry_price = float(st.get("entry_price", price_jpy))
                    highest_price = float(st.get("highest_price", max(entry_price, price_jpy)))
                    pnl_pct = ((price_jpy - entry_price) / entry_price * 100.0) if entry_price > 0 else 0.0

                total_jpy_value += val_jpy

                item = {
                    "asset": asset,
                    "symbol": f"{asset}JPY" if asset != "JPY" else "JPY",
                    "free": free,
                    "locked": locked,
                    "total": total,
                    "price_jpy": price_jpy,
                    "value_jpy": round(val_jpy, 2),
                    "sellable_qty": sellable_qty,
                    "sellable_jpy": round(sellable_jpy, 2),
                    "dust_qty": dust_qty,
                    "dust_jpy": round(dust_jpy, 2),
                    "can_market_sell": can_sell,
                    "entry_price": entry_price,
                    "highest_price": highest_price,
                    "pnl_pct": round(pnl_pct, 2),
                }
                formatted_list.append(item)

                if asset not in ("JPY", "BNB") and val_jpy >= 1.0:
                    if can_sell:
                        sellable_positions.append(item)
                    else:
                        locked_dust_positions.append(item)

            formatted_list.sort(key=lambda x: x["value_jpy"], reverse=True)
            total_pnl_jpy = total_jpy_value - self.initial_capital_jpy
            total_pnl_pct = (total_pnl_jpy / self.initial_capital_jpy * 100.0) if self.initial_capital_jpy > 0 else 0.0

            return {
                "success": True,
                "balances": formatted_list,
                "balances_dict": balances_dict,
                "total_jpy_value": round(total_jpy_value, 2),
                "cash_jpy": round(cash_jpy, 2),
                "bnb_reserve_jpy": round(bnb_jpy, 2),
                "initial_capital_jpy": self.initial_capital_jpy,
                "target_goal_jpy": round(self.initial_capital_jpy * 2.0, 2),
                "progress_pct": round(min(100.0, (total_jpy_value / (self.initial_capital_jpy * 2.0)) * 100.0), 1) if self.initial_capital_jpy > 0 else 0.0,
                "remaining_to_goal_jpy": round(max(0.0, (self.initial_capital_jpy * 2.0) - total_jpy_value), 2),
                "total_pnl_jpy": round(total_pnl_jpy, 2),
                "total_pnl_pct": round(total_pnl_pct, 2),
                "sellable_count": len(sellable_positions),
                "locked_dust_count": len(locked_dust_positions),
                "sellable_positions": sellable_positions,
                "locked_dust_positions": locked_dust_positions,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "balances": []}
        finally:
            await executor.close()

    async def scan_market(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """監視銘柄のリアルタイムマルチタイムフレーム・クオンツAlphaスキャン (v2.0)"""
        if not symbols:
            symbols = self.config.get("symbols_to_monitor", ALL_VALID_JPY_SYMBOLS[:15])

        # 廃止ペア(MATICJPY/NEIROJPY)を自動浄化
        clean_symbols = []
        for s in symbols:
            sym = s.upper()
            if not sym.endswith("JPY") and not sym.endswith("USDT"):
                sym += "JPY"
            if sym == "MATICJPY":
                sym = "POLJPY"
            if sym in ("NEIROJPY",):
                continue
            if sym not in clean_symbols:
                clean_symbols.append(sym)

        client, executor = self._get_clients()
        analyzer = MarketAnalyzer()

        async def _analyze_one(sym: str) -> Dict[str, Any]:
            try:
                klines_1h, klines_15m, depth = await asyncio.gather(
                    client.get_klines(sym, interval="1h", limit=100),
                    client.get_klines(sym, interval="15m", limit=60),
                    client.get_order_book(sym, limit=20),
                )
                if not klines_1h or not isinstance(klines_1h, list):
                    return {"symbol": sym, "error": "Kline取得失敗"}

                scored = analyzer.score_2x_potential(
                    klines_1h=klines_1h,
                    symbol=sym,
                    klines_15m=klines_15m if isinstance(klines_15m, list) else None,
                    order_book=depth if isinstance(depth, dict) else None,
                )
                ind = scored.get("indicators", {})
                return {
                    "symbol": sym,
                    "price": scored.get("current_price", 0.0),
                    "alpha_score": scored.get("alpha_score", 0.0),
                    "confidence": scored.get("confidence", 0.0),
                    "signal": scored.get("signal", "HOLD"),
                    "regime": scored.get("regime", "RANGE"),
                    "sniper_regime": scored.get("sniper_regime", ""),
                    "rsi": ind.get("rsi", 50.0),
                    "rsi6": ind.get("rsi6", 50.0),
                    "ema21": ind.get("ema21", scored.get("current_price", 0.0)),
                    "dist_e21": ind.get("dist_e21", 0.0),
                    "dd_24h": ind.get("dd_24h", 0.0),
                    "ret_1h": ind.get("ret_1h", 0.0),
                    "ret_6h": ind.get("ret_6h", 0.0),
                    "max_rvol2": ind.get("max_rvol2", 1.0),
                    "taker_buy_ratio": ind.get("taker_buy_ratio", 0.5),
                    "stoch_rsi_k": ind.get("stoch_rsi_k", 50.0),
                    "macd_hist": ind.get("macd_hist", 0.0),
                    "macd_rising": ind.get("macd_hist_rising", False),
                    "bb_lower": ind.get("bb_lower", 0.0),
                    "bb_upper": ind.get("bb_upper", 0.0),
                    "bb_pct_b": ind.get("bb_pct_b", 0.5),
                    "atr_pct": ind.get("atr_pct", 0.0),
                    "rvol": ind.get("rvol", 1.0),
                    "obi": ind.get("order_book_imbalance", 0.0),
                    "ret_24h_pct": ind.get("ret_24h_pct", 0.0),
                    "step_cost_jpy": ind.get("step_cost_jpy", 0.0),
                    "reasons": scored.get("reasons", []),
                }
            except Exception as e:
                return {"symbol": sym, "error": str(e)}

        try:
            raw_results = await asyncio.gather(*[_analyze_one(s) for s in clean_symbols])
            valid = [r for r in raw_results if "error" not in r]
            errors = [r for r in raw_results if "error" in r]
            valid.sort(key=lambda x: x.get("alpha_score", 0.0), reverse=True)
            return {
                "success": True,
                "scan_results": valid + errors,
                "top_pick": valid[0] if valid else None,
            }
        finally:
            await executor.close()

    async def execute_trade(self, symbol: str, action: str, amount_jpy: float = 115.0) -> Dict[str, Any]:
        """実口座売買の執行 (成行買い quoteOrderQty / LOT_SIZE自動丸め成行売り quantity)"""
        sym = symbol.upper()
        if not sym.endswith("JPY") and not sym.endswith("USDT"):
            sym += "JPY"
        act = action.upper()

        client, executor = self._get_clients()
        try:
            current_price = await client.get_ticker_price(sym)
            if act == "BUY":
                if amount_jpy < 100.0:
                    return {"success": False, "error": f"最小注文額は100円です (指定額: {amount_jpy}円)"}

                order = await executor.buy_market_jpy(sym, amount_jpy)
                executed_qty = float(order.get("executedQty", 0.0))
                cum_quote = float(order.get("cummulativeQuoteQty", amount_jpy))
                exec_price = (cum_quote / executed_qty) if executed_qty > 0 else current_price

                self._log_trade_to_db(
                    sym, "BUY", exec_price, executed_qty, cum_quote, f"成行買い約定 (指定:{amount_jpy:.0f}円)"
                )

                return {
                    "success": True,
                    "action": "BUY",
                    "symbol": sym,
                    "order_id": order.get("orderId"),
                    "price": exec_price,
                    "executed_qty": executed_qty,
                    "cummulative_quote": cum_quote,
                    "status": order.get("status"),
                }

            elif act == "SELL":
                base_asset = sym.replace("JPY", "").replace("USDT", "")
                balances = await executor.get_real_balances()
                asset_info = balances.get(base_asset, {})
                free_qty = float(asset_info.get("free", 0.0))

                if free_qty <= 1e-8:
                    return {
                        "success": False,
                        "error": f"売却対象の資産({base_asset})を保有していません (保有量: {free_qty})",
                    }

                q_info = quantize_lot_quantity(sym, free_qty, current_price)
                if not q_info["can_market_sell"]:
                    return {
                        "success": False,
                        "error": (
                            f"{sym} はLOT_SIZE丸め後の売却可能額が ¥{q_info['notional_jpy']:.1f} となり、"
                            f"最小注文額 ¥100 未満のため単体成行売却できません "
                            f"(保有:{free_qty}, stepSize:{q_info['step_size']}, 丸め後:{q_info['sellable_qty']})。"
                            f"`dust` (BNB変換) または追加購入による合算売却をご利用ください。"
                        ),
                        "quantize_info": q_info,
                    }

                order = await executor.sell_market(sym, free_qty, current_price=current_price)
                executed_qty = float(order.get("executedQty", q_info["sellable_qty"]))
                cum_quote = float(order.get("cummulativeQuoteQty", 0.0))
                exec_price = (cum_quote / executed_qty) if executed_qty > 0 else current_price

                self._log_trade_to_db(
                    sym,
                    "SELL",
                    exec_price,
                    executed_qty,
                    cum_quote,
                    f"{base_asset} LOT_SIZE最適化売却 (残端数:{q_info['dust_qty']:.6f})",
                )

                return {
                    "success": True,
                    "action": "SELL",
                    "symbol": sym,
                    "order_id": order.get("orderId"),
                    "price": exec_price,
                    "executed_qty": executed_qty,
                    "cummulative_quote": cum_quote,
                    "remaining_dust_qty": q_info["dust_qty"],
                    "status": order.get("status"),
                }
            else:
                return {"success": False, "error": f"無効なアクション: {action} (BUY または SELL)"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            await executor.close()

    async def close_all_positions(self) -> Dict[str, Any]:
        """成行売却可能な全保有ポジションを一括で日本円へ決済する"""
        bal_res = await self.get_balance()
        if not bal_res.get("success"):
            return bal_res
        sellable = bal_res.get("sellable_positions", [])
        if not sellable:
            return {
                "success": True,
                "closed_count": 0,
                "results": [],
                "message": "現在、単体成行売却可能な保有ポジション（¥100以上）はありません。",
            }
        results = []
        total_received_jpy = 0.0
        for pos in sellable:
            sym = pos["symbol"]
            r = await self.execute_trade(sym, "SELL")
            results.append(r)
            if r.get("success"):
                total_received_jpy += float(r.get("cummulative_quote", 0.0))
        closed_ok = [r for r in results if r.get("success")]
        return {
            "success": True,
            "closed_count": len(closed_ok),
            "total_received_jpy": round(total_received_jpy, 2),
            "results": results,
            "message": f"{len(closed_ok)}銘柄を一括成行決済しました（獲得合計: ¥{total_received_jpy:,.2f}）",
        }

    async def unlock_surplus_bnb(self, retain_bnb: float = 0.0020) -> Dict[str, Any]:
        """余剰BNBを成行売却してJPY現金に還元し、小資金運用の流動性を最大化する"""
        client, executor = self._get_clients()
        try:
            balances = await executor.get_real_balances()
            bnb_info = balances.get("BNB", {})
            free_bnb = float(bnb_info.get("free", 0.0))
            surplus = free_bnb - retain_bnb
            if surplus <= 0.0005:
                return {
                    "success": True,
                    "message": f"余剰BNBはありません (保有: {free_bnb:.6f}, 保持目安: {retain_bnb:.6f})",
                    "sold": False,
                }

            price = await client.get_ticker_price("BNBJPY")
            q_info = quantize_lot_quantity("BNBJPY", surplus, price)
            if not q_info["can_market_sell"] or q_info["sellable_qty"] <= 0:
                return {
                    "success": False,
                    "error": f"余剰BNB売却可能額(¥{q_info['notional_jpy']:.1f})が最小取引単位未満です",
                    "sold": False,
                }

            order = await client.create_order(
                symbol="BNBJPY",
                side="SELL",
                quantity=q_info["sellable_qty"],
            )
            executed_qty = float(order.get("executedQty", q_info["sellable_qty"]))
            cum_quote = float(order.get("cummulativeQuoteQty", 0.0))
            exec_price = (cum_quote / executed_qty) if executed_qty > 0 else price

            self._log_trade_to_db(
                "BNBJPY",
                "SELL",
                exec_price,
                executed_qty,
                cum_quote,
                f"BNB余剰燃料アンロック売却 (保持残:{free_bnb - executed_qty:.6f})",
            )
            return {
                "success": True,
                "sold": True,
                "executed_qty": executed_qty,
                "cummulative_quote": cum_quote,
                "exec_price": exec_price,
                "remaining_bnb": free_bnb - executed_qty,
                "message": f"余剰BNB {executed_qty:.4f} を成行売却し、現金 ¥{cum_quote:,.1f} を回収しました (残燃料: {free_bnb - executed_qty:.6f} BNB)",
            }
        except Exception as e:
            return {"success": False, "error": str(e), "sold": False}
        finally:
            await executor.close()

    async def sweep_dust_to_bnb(self, target_assets: Optional[List[str]] = None, include_locked_under_100: bool = False) -> Dict[str, Any]:
        """
        端数資産（LOT_SIZE未満の端数、または指定時は100円未満ロック銘柄）をBNBへ一括変換し、
        手数料25%割引（spotBNBBurn）および購入時の端数欠け防止燃料を確保する。
        """
        client, executor = self._get_clients()
        try:
            if not target_assets:
                bal_res = await self.get_balance()
                if not bal_res.get("success"):
                    return bal_res
                candidates = []
                for item in bal_res.get("balances", []):
                    asset = item["asset"]
                    if asset in ("JPY", "BNB"):
                        continue
                    # 売却後残った純粋な端数（評価額1円〜99円かつ成行売却不可）
                    if not item["can_market_sell"] and item["value_jpy"] > 0.5:
                        if include_locked_under_100 or item["value_jpy"] < 40.0:
                            candidates.append(asset)
                target_assets = candidates

            if not target_assets:
                return {
                    "success": True,
                    "converted": [],
                    "message": "変換対象の端数資産（Dust）はありませんでした。",
                }

            res = await client.convert_dust_to_bnb(target_assets)
            return {
                "success": True,
                "requested_assets": target_assets,
                "total_transfered_bnb": res.get("totalTransfered", "0"),
                "total_service_charge_bnb": res.get("totalServiceCharge", "0"),
                "transfer_result": res.get("transferResult", []),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            await executor.close()

    async def run_backtest(
        self,
        symbols: Optional[List[str]] = None,
        interval: str = "1h",
        limit: int = 240,
    ) -> Dict[str, Any]:
        """実ヒストリカルKlineデータを用いたクオンツv2.0戦略バックテスト"""
        client, executor = self._get_clients()
        try:
            bt = QuantBacktester(client=client)
            if symbols and len(symbols) == 1 and symbols[0]:
                sym = symbols[0].upper()
                if not sym.endswith("JPY"):
                    sym += "JPY"
                return await bt.run_symbol_backtest(symbol=sym, interval=interval, limit=limit)
            return await bt.run_portfolio_backtest(symbols=symbols, interval=interval, limit=limit)
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
        finally:
            await executor.close()

    def get_trade_history(self, limit: int = 25) -> List[Dict[str, Any]]:
        """SQLite (live_trades) から実口座の直近約定履歴を取得"""
        trades: List[Dict[str, Any]] = []
        if not os.path.exists(DB_PATH):
            return trades
        try:
            with sqlite3.connect(DB_PATH, timeout=15.0) as conn:
                c = conn.cursor()
                c.execute(
                    """
                    SELECT id, timestamp, symbol, side, price, quantity, cost, rationale
                    FROM live_trades
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
                for row in c.fetchall():
                    trades.append(
                        {
                            "id": row[0],
                            "timestamp": row[1],
                            "symbol": row[2],
                            "side": row[3],
                            "price": float(row[4] or 0.0),
                            "quantity": float(row[5] or 0.0),
                            "cost": round(float(row[6] or 0.0), 2),
                            "rationale": row[7] or "",
                        }
                    )
        except Exception:
            pass
        return trades

    def get_patrol_status(self) -> Dict[str, Any]:
        """自律クオンツパトロール (crontab / 4層防護設定 / 直近ログ) のステータスを取得"""
        import subprocess

        cron_tag = "# TUGUMI_BINANCE_AI_PATROL"
        cron_active = False
        cron_line = ""
        try:
            proc = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
            for line in proc.stdout.splitlines():
                if cron_tag in line:
                    cron_active = True
                    cron_line = line.replace(cron_tag, "").strip()
                    break
        except Exception:
            pass

        patrol_log_path = os.path.expanduser("~/.agents/binance/patrol.log")
        recent_log = ""
        if os.path.exists(patrol_log_path):
            try:
                with open(patrol_log_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                    recent_log = "".join(lines[-35:]).strip()
            except Exception:
                pass

        q_cfg = self.config.get("quant_strategy", {})
        return {
            "cron_active": cron_active,
            "cron_line": cron_line,
            "strategy_tiers": {
                "tier1_tp_pct": round(float(q_cfg.get("hard_take_profit_pct", 0.25)) * 100, 1),
                "tier1_trail_start_pct": round(float(q_cfg.get("hard_trailing_trigger_pct", 0.15)) * 100, 1),
                "tier1_trail_drop_pct": round(float(q_cfg.get("hard_trailing_drop_pct", 0.04)) * 100, 1),
                "tier1_sl_pct": round(float(q_cfg.get("hard_stop_loss_pct", -0.08)) * 100, 1),
                "tier2_smart_start_pct": round(float(q_cfg.get("smart_trail_trigger_pct", 0.04)) * 100, 1),
                "tier2_smart_drop_pct": round(float(q_cfg.get("smart_trail_drop_pct", 0.018)) * 100, 1),
                "tier3_entry_alpha": float(q_cfg.get("entry_alpha_threshold", 55.0)),
                "tier3_rotation_alpha": float(q_cfg.get("rotation_target_alpha", 62.0)),
                "tier3_weak_alpha": float(q_cfg.get("rotation_weak_alpha", 40.0)),
            },
            "recent_log": recent_log,
        }

    def control_patrol(self, action: str = "status", interval: int = 1) -> Dict[str, Any]:
        """自律クオンツパトロールの開始・停止・即時実行・ステータス確認"""
        import subprocess

        act = (action or "status").lower()
        patrol_script = os.path.expanduser("~/.agents/binance/autonomous_wealth_patrol.py")
        cron_tag = "# TUGUMI_BINANCE_AI_PATROL"

        if act == "run":
            try:
                proc = subprocess.run(
                    [sys.executable, patrol_script],
                    capture_output=True,
                    text=True,
                    timeout=90,
                )
                status_info = self.get_patrol_status()
                return {
                    "success": proc.returncode == 0,
                    "action": "run",
                    "output": (proc.stdout + "\n" + proc.stderr).strip(),
                    "patrol_status": status_info,
                }
            except Exception as e:
                return {"success": False, "action": "run", "error": str(e)}

        elif act == "start":
            try:
                proc = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
                lines = [l for l in proc.stdout.splitlines() if cron_tag not in l and l.strip()]
                iv = max(1, min(24, int(interval or 1)))
                cron_expr = "0 * * * *" if iv <= 1 else f"0 */{iv} * * *"
                log_p = "/data/data/com.termux/files/home/.agents/binance/patrol.log"
                cron_cmd = f"{cron_expr} {sys.executable} {patrol_script} >> {log_p} 2>&1 {cron_tag}"
                lines.append(cron_cmd)
                new_cron = "\n".join(lines) + "\n"
                p_write = subprocess.run(["crontab", "-"], input=new_cron, text=True, timeout=5)
                status_info = self.get_patrol_status()
                return {
                    "success": p_write.returncode == 0,
                    "action": "start",
                    "interval_hours": iv,
                    "cron_expr": cron_expr,
                    "message": f"自律クオンツパトロールを開始しました（{iv}時間ごと: {cron_expr}）",
                    "patrol_status": status_info,
                }
            except Exception as e:
                return {"success": False, "action": "start", "error": str(e)}

        elif act == "stop":
            try:
                proc = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
                lines = [l for l in proc.stdout.splitlines() if cron_tag not in l and l.strip()]
                new_cron = "\n".join(lines) + "\n" if lines else ""
                if new_cron:
                    subprocess.run(["crontab", "-"], input=new_cron, text=True, timeout=5)
                else:
                    subprocess.run(["crontab", "-r"], timeout=5)
                status_info = self.get_patrol_status()
                return {
                    "success": True,
                    "action": "stop",
                    "message": "自律クオンツパトロールの定期実行を停止しました。",
                    "patrol_status": status_info,
                }
            except Exception as e:
                return {"success": False, "action": "stop", "error": str(e)}

        else:
            status_info = self.get_patrol_status()
            return {
                "success": True,
                "action": "status",
                "patrol_status": status_info,
            }

    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """Web UI『収益・Binance』タブ用の統合リアルタイムダッシュボードデータを一括取得"""
        bal_res = await self.get_balance()
        patrol_info = self.get_patrol_status()
        recent_trades = self.get_trade_history(limit=20)
        return {
            **bal_res,
            "patrol_status": patrol_info,
            "recent_trades": recent_trades,
            "monitored_symbols": self.config.get("symbols_to_monitor", ALL_VALID_JPY_SYMBOLS[:18]),
            "all_jpy_symbols": ALL_VALID_JPY_SYMBOLS,
            "default_order_jpy": float(self.config.get("order_budget_jpy", 115.0)),
        }

    def _log_trade_to_db(self, symbol: str, side: str, price: float, quantity: float, cost: float, rationale: str):
        try:
            with sqlite3.connect(DB_PATH, timeout=30.0) as conn:
                c = conn.cursor()
                c.execute(
                    """
                    CREATE TABLE IF NOT EXISTS live_trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        symbol TEXT,
                        side TEXT,
                        price REAL,
                        quantity REAL,
                        cost REAL,
                        rationale TEXT
                    )
                """
                )
                c.execute(
                    """
                    INSERT INTO live_trades (symbol, side, price, quantity, cost, rationale)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (symbol, side, price, quantity, cost, rationale),
                )
                conn.commit()
        except Exception:
            pass

    def _safe_run(self, coro):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return asyncio.run(coro)

    def get_balance_sync(self) -> Dict[str, Any]:
        return self._safe_run(self.get_balance())

    def get_dashboard_summary_sync(self) -> Dict[str, Any]:
        return self._safe_run(self.get_dashboard_summary())

    def scan_market_sync(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        return self._safe_run(self.scan_market(symbols))

    def execute_trade_sync(self, symbol: str, action: str, amount_jpy: float = 115.0) -> Dict[str, Any]:
        return self._safe_run(self.execute_trade(symbol, action, amount_jpy))

    def close_all_positions_sync(self) -> Dict[str, Any]:
        return self._safe_run(self.close_all_positions())

    def sweep_dust_sync(self, target_assets: Optional[List[str]] = None, include_locked_under_100: bool = False) -> Dict[str, Any]:
        return self._safe_run(self.sweep_dust_to_bnb(target_assets=target_assets, include_locked_under_100=include_locked_under_100))

    def run_backtest_sync(self, symbols: Optional[List[str]] = None, interval: str = "1h", limit: int = 240) -> Dict[str, Any]:
        return self._safe_run(self.run_backtest(symbols=symbols, interval=interval, limit=limit))

    def unlock_surplus_bnb_sync(self, retain_bnb: float = 0.0020) -> Dict[str, Any]:
        return self._safe_run(self.unlock_surplus_bnb(retain_bnb=retain_bnb))

