#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TUGUMIv6 Crypto Trader Master CLI - Zero Mock / Production Grade
Supports Real Binance Japan JPY Trading (BTCJPY, ETHJPY, etc.) with 1,000 JPY budget.
"""

import sys
import os
import json
import asyncio
import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

sys.path.insert(0, "/data/data/com.termux/files/home/TUGUMIv6/crypto_trader")
from binance_client import BinanceClient
from analysis_engine import analyze_market_signals
from live_executor import LiveExecutor
from trade_db import TradeDatabase

console = Console()
CONFIG_FILE = "/data/data/com.termux/files/home/TUGUMIv6/crypto_trader/config.json"


SECRETS_FILE = "/data/data/com.termux/files/home/.agents/binance/secrets.json"


def load_config():
    cfg = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}

    # 安全な環境変数またはパーミッション制限されたシークレットファイルからの透過ロード
    api_k = cfg.get("api_key") or os.environ.get("BINANCE_API_KEY")
    api_s = cfg.get("api_secret") or os.environ.get("BINANCE_API_SECRET")

    if (not api_k or not api_s) and os.path.exists(SECRETS_FILE):
        try:
            with open(SECRETS_FILE, "r", encoding="utf-8") as sf:
                s_data = json.load(sf)
                api_k = api_k or s_data.get("api_key")
                api_s = api_s or s_data.get("api_secret")
        except Exception:
            pass

    cfg["api_key"] = api_k or ""
    cfg["api_secret"] = api_s or ""
    return cfg


async def run_scan_command():
    """Scan JPY market pairs and print quantitative signals."""
    config = load_config()
    client = BinanceClient(base_url=config.get("base_url", "https://api.binance.com"))
    db = TradeDatabase()
    symbols = config.get("symbols_to_monitor", ["BTCJPY", "ETHJPY", "BNBJPY", "SOLJPY"])

    console.print(Panel.fit("[bold cyan]TUGUMIv6 Binance Japan JPY市場スキャナー (実データ即時解析)[/bold cyan]"))

    table = Table(title="リアルタイム市場分析 & AI売買シグナル (日本円建て)")
    table.add_column("銘柄 (Symbol)", style="cyan", justify="left")
    table.add_column("現在価格 (JPY)", style="white", justify="right")
    table.add_column("RSI (14)", justify="right")
    table.add_column("ボリンジャーバンド (下限/上限)", justify="center")
    table.add_column("AI判定シグナル", justify="center")
    table.add_column("信頼度", justify="right")
    table.add_column("主因 / 根拠", style="dim")

    for symbol in symbols:
        try:
            klines = await client.get_klines(symbol, interval="1h", limit=50)
            res = analyze_market_signals(klines)
            db.record_market_snapshot(
                symbol=symbol,
                price=res["latest_price"],
                rsi=res["rsi"],
                signal=res["signal"],
                confidence=res["confidence"],
            )

            price_str = f"¥{res['latest_price']:,.0f}"
            rsi_str = f"{res['rsi']:.1f}"
            rsi_color = "[bold green]" if res["rsi"] < 30 else "[bold red]" if res["rsi"] > 70 else "[yellow]"
            rsi_formatted = f"{rsi_color}{rsi_str}[/]"

            bb_range = f"¥{res['bb_lower']:,.0f} ~ ¥{res['bb_upper']:,.0f}"

            sig = res["signal"]
            if "BUY" in sig:
                sig_disp = f"[bold green]{sig}[/bold green]"
            elif "SELL" in sig:
                sig_disp = f"[bold red]{sig}[/bold red]"
            else:
                sig_disp = "[dim white]HOLD[/dim white]"

            conf_str = f"{int(res['confidence'] * 100)}%"
            reason_str = " | ".join(res["reasons"])[:40]

            table.add_row(symbol, price_str, rsi_formatted, bb_range, sig_disp, conf_str, reason_str)
        except Exception as e:
            table.add_row(symbol, "ERROR", "-", "-", "[red]通信失敗[/red]", "-", str(e)[:30])

    console.print(table)
    await client.close()


async def run_balance_command():
    """Fetch and display real Binance account balances."""
    config = load_config()
    api_key = config.get("api_key")
    api_secret = config.get("api_secret")

    if not api_key or not api_secret:
        console.print(Panel("[bold yellow]⚠️ Binance APIキーが未設定です。[/bold yellow]\n"
                            "実口座の残高確認・発注を行うには、config.json に APIキーを設定してください。\n"
                            f"設定先ファイル: [cyan]{CONFIG_FILE}[/cyan]", title="API設定ステータス"))
        return

    executor = LiveExecutor(api_key, api_secret, config.get("base_url", "https://api.binance.com"))
    try:
        balances = await executor.get_real_balances()
        table = Table(title="Binance 実口座残高")
        table.add_column("資産 (Asset)", style="cyan")
        table.add_column("利用可能残高 (Free)", justify="right", style="green")
        table.add_column("注文中拘束 (Locked)", justify="right", style="dim")

        if not balances:
            console.print("[yellow]ℹ️ 現在、口座内の保有残高（JPY / 暗号資産）は 0 です（未入金状態）。[/yellow]\n"
                          "[dim]※PayPayマネー等からバイナンス口座へ日本円を入金すると、ここに即座に反映されます。[/dim]")
        else:
            for asset, data in sorted(balances.items()):
                table.add_row(asset, f"{data['free']:.6f}", f"{data['locked']:.6f}")
            console.print(table)
    except Exception as e:
        console.print(f"[bold red]❌ 口座情報取得失敗: {e}[/bold red]")
    finally:
        await executor.close()


async def run_live_trade(symbol: str, action: str = "auto", amount_jpy: float = 1000.0):
    """Execute real trade on Binance Japan."""
    config = load_config()
    api_key = config.get("api_key")
    api_secret = config.get("api_secret")

    if not api_key or not api_secret:
        console.print(Panel(
            "[bold red]❌ 本番取引エラー: APIキーが設定されていません[/bold red]\n"
            f"1. バイナンスアプリ／WEBで「API管理」を開く\n"
            f"2. 「読み取り」および「現物・マージン取引」のみを有効化（※出金権限は絶対にOFF）\n"
            f"3. {CONFIG_FILE} に APIキーとシークレットを記載してください。",
            title="本番APIキー未登録"
        ))
        return

    executor = LiveExecutor(api_key, api_secret, config.get("base_url", "https://api.binance.com"))
    client = BinanceClient(base_url=config.get("base_url", "https://api.binance.com"))

    try:
        klines = await client.get_klines(symbol, interval="1h", limit=50)
        analysis = analyze_market_signals(klines)
        price = analysis["latest_price"]
        sig = analysis["signal"]

        console.print(f"📊 [bold cyan]{symbol}[/bold cyan] 現在価格: ¥{price:,.0f} | RSI: {analysis['rsi']} | AI判定: [bold yellow]{sig}[/bold yellow]")

        should_buy = (action == "buy") or (action == "auto" and sig in ["BUY", "STRONG_BUY"])
        should_sell = (action == "sell") or (action == "auto" and sig in ["SELL", "STRONG_SELL"])

        if should_buy:
            console.print(f"[bold green]🚀 本番買い注文を発行します: 金額 ¥{amount_jpy:,.0f} ({symbol})[/bold green]")
            order_res = await executor.buy_market_jpy(symbol, amount_jpy)
            console.print(Panel(f"約定完了 ID: {order_res.get('orderId')}\nステータス: {order_res.get('status')}\n約定数量: {order_res.get('executedQty')}", title="実発注リザルト", style="green"))
        elif should_sell:
            console.print("[bold yellow]⚠️ 売りシグナル検知: 手動売却またはポジションクローズ対象です[/bold yellow]")
        else:
            console.print("[dim]⏸️ シグナルが中立（HOLD）のため見送りました。[/dim]")

    except Exception as e:
        console.print(f"[bold red]❌ 取引実行エラー: {e}[/bold red]")
    finally:
        await client.close()
        await executor.close()


def main():
    parser = argparse.ArgumentParser(description="TUGUMIv6 Real Binance Japan Crypto Trader")
    parser.add_argument("command", choices=["scan", "balance", "trade", "daemon"], help="実行コマンド")
    parser.add_argument("--symbol", default="BTCJPY", help="対象通貨ペア (デフォルト: BTCJPY)")
    parser.add_argument("--action", choices=["auto", "buy", "sell"], default="auto", help="売買種別 (auto/buy/sell)")
    parser.add_argument("--amount", type=float, default=1000.0, help="購入予算 (日本円, デフォルト: 1000円)")

    args = parser.parse_args()

    if args.command == "scan":
        asyncio.run(run_scan_command())
    elif args.command == "balance":
        asyncio.run(run_balance_command())
    elif args.command == "trade":
        asyncio.run(run_live_trade(args.symbol, args.action, args.amount))
    elif args.command == "daemon":
        console.print(f"[bold yellow]⚡ Binance Japan リアルタイム自律監視モード稼働中 (対象: {args.symbol})[/bold yellow]")
        async def loop():
            while True:
                await run_live_trade(args.symbol, "auto", args.amount)
                await asyncio.sleep(60)
        asyncio.run(loop())


if __name__ == "__main__":
    main()
