#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TUGUMIv6 Real Binance Japan Live Order Executor (v2.0 Quant Edition)
Handles spot real orders via Binance REST API with Exact LOT_SIZE Quantization & Dust Sweep.
"""

import sys
from typing import Dict, Any, Optional, List

sys.path.insert(0, "/data/data/com.termux/files/home/TUGUMIv6/crypto_trader")
from binance_client import BinanceClient, quantize_lot_quantity


class LiveExecutor:
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://api.binance.com",
        client: Optional[BinanceClient] = None,
    ):
        self._owns_client = client is None
        self.client = client or BinanceClient(api_key=api_key, api_secret=api_secret, base_url=base_url)

    async def get_real_balances(self) -> Dict[str, Dict[str, float]]:
        """Fetch actual account balances (JPY, BTC, ETH, USDT, etc.)."""
        account = await self.client.get_account()
        balances: Dict[str, Dict[str, float]] = {}
        for b in account.get("balances", []):
            free = float(b.get("free", 0.0))
            locked = float(b.get("locked", 0.0))
            if free > 0 or locked > 0:
                balances[b["asset"]] = {"free": free, "locked": locked}
        return balances

    async def buy_market_jpy(self, symbol: str, jpy_amount: float) -> Dict[str, Any]:
        """
        Execute real MARKET BUY order using JPY quote amount.
        Minimum notional for JPY pairs is 100 JPY.
        """
        if jpy_amount < 100.0:
            raise ValueError(f"注文額（¥{jpy_amount:,.0f}）がバイナンスの最小取引額（¥100）を下回っています。")

        res = await self.client.create_order(
            symbol=symbol.upper(),
            side="BUY",
            order_type="MARKET",
            quote_order_qty=round(jpy_amount, 2),
        )
        return res

    async def sell_market(self, symbol: str, quantity: float, current_price: Optional[float] = None) -> Dict[str, Any]:
        """
        Execute real MARKET SELL order with exact LOT_SIZE stepSize quantization
        and minNotional pre-flight verification.
        """
        sym = symbol.upper()
        filters = await self.client.get_symbol_filters(sym)
        step_size = filters.get("stepSize", "0.01")
        min_notional = float(filters.get("minNotional", 100.0))

        q_float, q_str, dust_rem = quantize_lot_quantity(sym, quantity, step_size)
        if q_float <= 0:
            raise ValueError(
                f"{sym}: 保有数量({quantity})が最小取引単位(stepSize={step_size})未満のため通常売却できません。Dust BNB変換(/binance dust)をご利用ください。"
            )

        # 現在価格から想定約定代金を計算し minNotional (¥100) を満たすか検証
        try:
            curr_price = float(current_price) if current_price and current_price > 0 else await self.client.get_ticker_price(sym)
            est_notional = q_float * curr_price
            if est_notional < min_notional:
                raise ValueError(
                    f"{sym}: LOT_SIZE丸め後の売却数量({q_str}枚 ≒ ¥{est_notional:,.1f})がバイナンス最小注文額(¥{min_notional:,.0f})未満のため単体成行売却できません。"
                    f"（元数量: {quantity}枚, 端数: {dust_rem:.6f}枚）。Dust BNB変換(`/binance dust {sym.replace('JPY','')}`)で回収可能です。"
                )
        except ValueError:
            raise
        except Exception:
            pass

        res = await self.client.create_order(
            symbol=sym,
            side="SELL",
            order_type="MARKET",
            quantity=q_float,
        )
        res["_quantized_qty"] = q_float
        res["_dust_remainder"] = dust_rem
        return res

    async def sweep_dust_to_bnb(self, assets: List[str]) -> Dict[str, Any]:
        """Convert small/dust balances (< 100 JPY or un-sellable stepSize remainders) to BNB."""
        return await self.client.convert_dust_to_bnb(assets)

    async def close(self):
        if self.client:
            await self.client.close()
