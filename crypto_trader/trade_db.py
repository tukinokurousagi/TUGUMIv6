#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TUGUMIv6 Crypto Trader - SQLite Trade Logger and Paper Trading Portfolio
Persists trade signals, virtual balance, and real execution logs.
"""

import sqlite3
import os
import json
import time
from typing import Dict, Any, List

DB_PATH = "/data/data/com.termux/files/home/TUGUMIv6/crypto_trader/trader_history.db"


class TradeDatabase:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._get_conn() as conn:
            # Paper trading balances
            conn.execute("""
            CREATE TABLE IF NOT EXISTS virtual_portfolio (
                asset TEXT PRIMARY KEY,
                free_balance REAL NOT NULL,
                locked_balance REAL NOT NULL DEFAULT 0.0,
                updated_at REAL NOT NULL
            );
            """)

            # Trade orders log
            conn.execute("""
            CREATE TABLE IF NOT EXISTS trade_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                symbol TEXT NOT NULL,
                mode TEXT NOT NULL, -- 'PAPER' or 'LIVE'
                side TEXT NOT NULL, -- 'BUY' or 'SELL'
                price REAL NOT NULL,
                quantity REAL NOT NULL,
                cost REAL NOT NULL,
                status TEXT NOT NULL,
                signal_info TEXT
            );
            """)

            # Market snapshots
            conn.execute("""
            CREATE TABLE IF NOT EXISTS market_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                rsi REAL,
                signal TEXT,
                confidence REAL
            );
            """)

            # Seed virtual portfolio with 100,000 JPY / USDT if empty
            cur = conn.execute("SELECT count(*) FROM virtual_portfolio;")
            if cur.fetchone()[0] == 0:
                conn.execute(
                    "INSERT INTO virtual_portfolio (asset, free_balance, updated_at) VALUES ('USDT', 1000.0, ?);",
                    (time.time(),)
                )
                conn.execute(
                    "INSERT INTO virtual_portfolio (asset, free_balance, updated_at) VALUES ('JPY', 100000.0, ?);",
                    (time.time(),)
                )
            conn.commit()

    def get_portfolio(self) -> Dict[str, float]:
        with self._get_conn() as conn:
            cur = conn.execute("SELECT asset, free_balance FROM virtual_portfolio;")
            return {row["asset"]: row["free_balance"] for row in cur.fetchall()}

    def record_market_snapshot(self, symbol: str, price: float, rsi: float, signal: str, confidence: float):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO market_snapshots (timestamp, symbol, price, rsi, signal, confidence) VALUES (?, ?, ?, ?, ?, ?);",
                (time.time(), symbol, price, rsi, signal, confidence),
            )
            conn.commit()

    def record_paper_trade(self, symbol: str, side: str, price: float, quantity: float, signal_data: Dict[str, Any]) -> bool:
        """Execute and record virtual trade, updating portfolio."""
        cost = price * quantity
        base_asset = symbol.replace("USDT", "").replace("JPY", "")
        quote_asset = "JPY" if "JPY" in symbol else "USDT"

        with self._get_conn() as conn:
            portfolio = self.get_portfolio()
            quote_balance = portfolio.get(quote_asset, 0.0)
            base_balance = portfolio.get(base_asset, 0.0)

            if side == "BUY":
                if quote_balance < cost:
                    return False  # Insufficient funds
                new_quote = quote_balance - cost
                new_base = base_balance + quantity
            else:  # SELL
                if base_balance < quantity:
                    return False  # Insufficient coins
                new_quote = quote_balance + cost
                new_base = base_balance - quantity

            conn.execute(
                "INSERT OR REPLACE INTO virtual_portfolio (asset, free_balance, updated_at) VALUES (?, ?, ?);",
                (quote_asset, new_quote, time.time()),
            )
            conn.execute(
                "INSERT OR REPLACE INTO virtual_portfolio (asset, free_balance, updated_at) VALUES (?, ?, ?);",
                (base_asset, new_base, time.time()),
            )

            conn.execute(
                """INSERT INTO trade_orders
                (timestamp, symbol, mode, side, price, quantity, cost, status, signal_info)
                VALUES (?, ?, 'PAPER', ?, ?, ?, ?, 'FILLED', ?);""",
                (time.time(), symbol, side, price, quantity, cost, json.dumps(signal_data, ensure_ascii=False)),
            )
            conn.commit()
            return True

    def get_recent_orders(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.execute(
                "SELECT * FROM trade_orders ORDER BY id DESC LIMIT ?;", (limit,)
            )
            return [dict(row) for row in cur.fetchall()]
