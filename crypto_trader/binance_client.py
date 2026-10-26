#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TUGUMIv6 Crypto Trader - Binance Japan Public & Private API Client (v2.0 Quant Edition)
Pure Python asyncio / aiohttp implementation with Exact LOT_SIZE Quantizer & Dust Sweep API.
"""

import time
import hmac
import hashlib
import urllib.parse
from decimal import Decimal
from typing import Dict, Any, Optional, List
import aiohttp


# Binance Japan 全27種 JPYペアの確定フィルタ定義 (フォールバック＆高速参照用)
DEFAULT_JPY_FILTERS: Dict[str, Dict[str, Any]] = {
    "ADAJPY": {"minQty": "0.10000000", "stepSize": "0.10000000", "minNotional": 100.0},
    "APTJPY": {"minQty": "0.01000000", "stepSize": "0.01000000", "minNotional": 100.0},
    "BCHJPY": {"minQty": "0.00010000", "stepSize": "0.00010000", "minNotional": 100.0},
    "BNBJPY": {"minQty": "0.00010000", "stepSize": "0.00010000", "minNotional": 100.0},
    "BTCJPY": {"minQty": "0.00000100", "stepSize": "0.00000100", "minNotional": 100.0},
    "DOGEJPY": {"minQty": "1.00000000", "stepSize": "1.00000000", "minNotional": 100.0},
    "ETHJPY": {"minQty": "0.00001000", "stepSize": "0.00001000", "minNotional": 100.0},
    "FETJPY": {"minQty": "0.01000000", "stepSize": "0.01000000", "minNotional": 100.0},
    "GIGGLEJPY": {"minQty": "0.00010000", "stepSize": "0.00010000", "minNotional": 100.0},
    "IOTXJPY": {"minQty": "1.00000000", "stepSize": "1.00000000", "minNotional": 100.0},
    "LINKJPY": {"minQty": "0.01000000", "stepSize": "0.01000000", "minNotional": 100.0},
    "LPTJPY": {"minQty": "0.01000000", "stepSize": "0.01000000", "minNotional": 100.0},
    "LTCJPY": {"minQty": "0.00100000", "stepSize": "0.00100000", "minNotional": 100.0},
    "MEMEJPY": {"minQty": "1.00000000", "stepSize": "1.00000000", "minNotional": 100.0},
    "NEARJPY": {"minQty": "0.10000000", "stepSize": "0.10000000", "minNotional": 100.0},
    "PEPEJPY": {"minQty": "1.00", "stepSize": "1.00", "minNotional": 100.0},
    "POLJPY": {"minQty": "0.10000000", "stepSize": "0.10000000", "minNotional": 100.0},
    "SEIJPY": {"minQty": "1.00000000", "stepSize": "1.00000000", "minNotional": 100.0},
    "SHIBJPY": {"minQty": "1.00", "stepSize": "1.00", "minNotional": 100.0},
    "SOLJPY": {"minQty": "0.00100000", "stepSize": "0.00100000", "minNotional": 100.0},
    "SUIJPY": {"minQty": "0.01000000", "stepSize": "0.01000000", "minNotional": 100.0},
    "TAOJPY": {"minQty": "0.00001000", "stepSize": "0.00001000", "minNotional": 100.0},
    "TRBJPY": {"minQty": "0.00010000", "stepSize": "0.00010000", "minNotional": 100.0},
    "TRUMPJPY": {"minQty": "0.00010000", "stepSize": "0.00010000", "minNotional": 100.0},
    "TRXJPY": {"minQty": "0.01000000", "stepSize": "0.01000000", "minNotional": 100.0},
    "XLMJPY": {"minQty": "0.10000000", "stepSize": "0.10000000", "minNotional": 100.0},
    "XRPJPY": {"minQty": "0.10000000", "stepSize": "0.10000000", "minNotional": 100.0},
}

ALL_VALID_JPY_SYMBOLS: List[str] = list(DEFAULT_JPY_FILTERS.keys())


class LotQuantizeResult(dict):
    """Hybrid dict and 3-tuple (sellable_qty, sellable_str, dust_qty) for LOT_SIZE quantization."""

    def __iter__(self):
        yield self["sellable_qty"]
        yield self["sellable_str"]
        yield self["dust_qty"]


def quantize_lot_quantity(
    symbol: str,
    raw_quantity: float,
    step_or_price: Optional[Any] = None,
    price_jpy: float = 0.0,
) -> LotQuantizeResult:
    """
    Binance LOT_SIZE フィルタに完全準拠するよう数量を切り捨て（ROUND_DOWN）量子化する。
    3要素タプルアンパック `(q_float, q_str, dust_rem)` と辞書キーアクセスの両方に100%対応。
    """
    sym = symbol.upper()
    info = DEFAULT_JPY_FILTERS.get(sym, {})
    step_size_str = info.get("stepSize", "0.00010000")
    min_notional = float(info.get("minNotional", 100.0))

    if isinstance(step_or_price, str) and step_or_price:
        step_size_str = step_or_price
    elif isinstance(step_or_price, (int, float)):
        price_jpy = float(step_or_price)

    d_qty = Decimal(str(max(0.0, float(raw_quantity))))
    d_step = Decimal(str(step_size_str)).normalize()

    if d_step <= 0:
        q_float = float(raw_quantity)
        q_str = str(raw_quantity)
        dust_float = 0.0
    else:
        steps = d_qty // d_step
        d_quantized = steps * d_step
        d_dust = max(Decimal("0"), d_qty - d_quantized)
        q_norm = d_quantized.normalize()
        q_str = format(q_norm, "f")
        if "." in q_str:
            q_str = q_str.rstrip("0").rstrip(".") or "0"
        q_float = float(d_quantized)
        dust_float = float(d_dust)

    notional_jpy = q_float * price_jpy if price_jpy > 0 else 0.0
    can_market_sell = (q_float > 0) and (notional_jpy >= min_notional if price_jpy > 0 else True)

    return LotQuantizeResult(
        sellable_qty=q_float,
        sellable_str=q_str,
        dust_qty=dust_float,
        notional_jpy=notional_jpy,
        can_market_sell=can_market_sell,
        step_size=step_size_str,
        min_notional=min_notional,
    )


def get_symbol_filter(symbol: str) -> Dict[str, Any]:
    """Get fallback LOT_SIZE and MIN_NOTIONAL filter for a symbol."""
    sym = symbol.upper()
    return DEFAULT_JPY_FILTERS.get(sym, {"minQty": "0.0001", "stepSize": "0.0001", "minNotional": 100.0})


class BinanceClient:
    """Binance REST API Client (Compatible with Binance Japan & Global endpoints)."""

    _exchange_filters_cache: Dict[str, Dict[str, Any]] = dict(DEFAULT_JPY_FILTERS)
    _cache_timestamp: float = 0.0

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        base_url: str = "https://api.binance.com",
    ):
        self.api_key = api_key or ""
        self.api_secret = api_secret or ""
        self.base_url = base_url.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=90)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    def _sign_params(self, params: Dict[str, Any]) -> str:
        """Generate HMAC SHA256 signature for signed endpoints (supports list values via doseq=True)."""
        params["timestamp"] = int(time.time() * 1000)
        query_string = urllib.parse.urlencode(sorted(params.items()), doseq=True)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return f"{query_string}&signature={signature}"

    async def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Any:
        """Send asynchronous HTTP request to Binance API."""
        session = await self._get_session()
        url = f"{self.base_url}{path}"
        headers = {
            "Accept": "application/json",
            "User-Agent": "TUGUMI-CryptoTrader/2.0",
        }

        if self.api_key:
            headers["X-MBX-APIKEY"] = self.api_key

        params = params.copy() if params else {}

        if signed:
            if not self.api_secret or not self.api_key:
                raise ValueError("API Key and Secret are required for signed endpoints")
            query = self._sign_params(params)
            url = f"{url}?{query}"
            req_params = None
        else:
            req_params = params if params else None

        async with session.request(method, url, params=req_params, headers=headers) as response:
            data = await response.json(content_type=None)
            if response.status >= 400:
                code = data.get("code", response.status) if isinstance(data, dict) else response.status
                msg = data.get("msg", str(data)) if isinstance(data, dict) else str(data)
                raise RuntimeError(f"Binance API Error [{code}]: {msg} (Status: {response.status})")
            return data

    async def close(self):
        """Close active http session."""
        if self.session and not self.session.closed:
            await self.session.close()

    # --- Public Market Data Endpoints ---

    async def ping(self) -> bool:
        """Test API connectivity."""
        res = await self.request("GET", "/api/v3/ping")
        return res == {}

    async def get_server_time(self) -> int:
        """Fetch server timestamp."""
        res = await self.request("GET", "/api/v3/time")
        return res.get("serverTime", 0)

    async def get_symbol_filters(self, symbol: str) -> Dict[str, Any]:
        """Get LOT_SIZE and MIN_NOTIONAL filters for a symbol."""
        sym = symbol.upper()
        if sym in self._exchange_filters_cache:
            return self._exchange_filters_cache[sym]

        try:
            res = await self.request("GET", "/api/v3/exchangeInfo", {"symbol": sym})
            for s in res.get("symbols", []):
                if s["symbol"] == sym:
                    lot = next((f for f in s.get("filters", []) if f["filterType"] == "LOT_SIZE"), {})
                    notional = next((f for f in s.get("filters", []) if f["filterType"] in ("NOTIONAL", "MIN_NOTIONAL")), {})
                    f_data = {
                        "minQty": lot.get("minQty", "0.01"),
                        "stepSize": lot.get("stepSize", "0.01"),
                        "minNotional": float(notional.get("minNotional", 100.0)),
                    }
                    self._exchange_filters_cache[sym] = f_data
                    return f_data
        except Exception:
            pass

        return {"minQty": "0.01", "stepSize": "0.01", "minNotional": 100.0}

    async def get_ticker_price(self, symbol: str) -> float:
        """Fetch latest price for a symbol (e.g. BTCUSDT, BTCJPY)."""
        res = await self.request("GET", "/api/v3/ticker/price", {"symbol": symbol.upper()})
        return float(res["price"])

    async def get_all_jpy_prices(self) -> Dict[str, float]:
        """Fetch latest prices for all JPY trading pairs in a single API call."""
        res = await self.request("GET", "/api/v3/ticker/price")
        prices: Dict[str, float] = {}
        if isinstance(res, list):
            for item in res:
                sym = item.get("symbol", "")
                if sym.endswith("JPY"):
                    try:
                        prices[sym] = float(item.get("price", 0.0))
                    except Exception:
                        pass
        return prices

    async def get_24hr_ticker(self, symbol: Optional[str] = None) -> Any:
        """Fetch 24hr ticker statistics for one or all symbols."""
        params = {"symbol": symbol.upper()} if symbol else {}
        return await self.request("GET", "/api/v3/ticker/24hr", params)

    async def get_klines(
        self, symbol: str, interval: str = "1h", limit: int = 100
    ) -> list:
        """Fetch Kline/candlestick bars.
        intervals: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
        """
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit,
        }
        return await self.request("GET", "/api/v3/klines", params)

    async def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """Fetch depth order book."""
        params = {"symbol": symbol.upper(), "limit": limit}
        return await self.request("GET", "/api/v3/depth", params)

    # --- Private Account Endpoints (Signed) ---

    async def get_account(self) -> Dict[str, Any]:
        """Fetch account balances and permissions."""
        return await self.request("GET", "/api/v3/account", signed=True)

    async def get_my_trades(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch actual executed trades for a symbol from Binance account."""
        params = {"symbol": symbol.upper(), "limit": limit}
        return await self.request("GET", "/api/v3/myTrades", params=params, signed=True)

    async def get_bnb_burn_status(self) -> Dict[str, Any]:
        """Check if spotBNBBurn (25% fee discount via BNB) is enabled."""
        return await self.request("GET", "/sapi/v1/bnbBurn", signed=True)

    async def get_dust_eligible_assets(self) -> Dict[str, Any]:
        """Fetch small balances eligible for conversion to BNB."""
        return await self.request("POST", "/sapi/v1/asset/dust-btc", signed=True)

    async def convert_dust_to_bnb(self, assets: List[str]) -> Dict[str, Any]:
        """Convert specified small/dust assets to BNB via /sapi/v1/asset/dust."""
        if not assets:
            raise ValueError("No assets specified for dust conversion")
        clean_assets = [a.upper().replace("JPY", "").replace("USDT", "") for a in assets]
        return await self.request("POST", "/sapi/v1/asset/dust", params={"asset": clean_assets}, signed=True)

    async def create_order(
        self,
        symbol: str,
        side: str,  # BUY or SELL
        order_type: str = "MARKET",  # MARKET or LIMIT
        quantity: Optional[float] = None,
        quote_order_qty: Optional[float] = None,
        price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Place spot order with automatic LOT_SIZE stepSize quantization."""
        sym = symbol.upper()
        params: Dict[str, Any] = {
            "symbol": sym,
            "side": side.upper(),
            "type": order_type.upper(),
        }
        if quantity is not None:
            filters = await self.get_symbol_filters(sym)
            q_float, q_str, _ = quantize_lot_quantity(sym, quantity, filters.get("stepSize"))
            if q_float <= 0:
                raise ValueError(f"{sym}: 注文数量({quantity})が最小取引単位(stepSize={filters.get('stepSize')})未満です。")
            params["quantity"] = q_str
        elif quote_order_qty is not None:
            params["quoteOrderQty"] = round(float(quote_order_qty), 2)

        if order_type.upper() == "LIMIT":
            if price is None:
                raise ValueError("Price is required for LIMIT order")
            params["price"] = price
            params["timeInForce"] = "GTC"

        return await self.request("POST", "/api/v3/order", params=params, signed=True)
