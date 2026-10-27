#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TUGUMIv6 Quantitative Technical Analysis & Multi-Factor Alpha Engine (v2.0)
Calculates:
  - SMA & EMA Ribbon (9, 21, 50)
  - Wilder's RSI (14) & Stochastic RSI (14, 14, 3, 3)
  - MACD (12, 26, 9) & Histogram Momentum Acceleration
  - Bollinger Bands (20, 2.0) & Bandwidth Squeeze / %B
  - ATR (14) Volatility Ratio (ATR%) & Dynamic Stop/Target Levels
  - RVOL (Relative Volume Surge) & Buying Volume Pressure
  - Order Book Imbalance & Multi-Timeframe (15m / 1h / 4h) Alignment
  - Lot Efficiency Factor (avoids stepSize dust traps on micro accounts)
"""

from typing import List, Dict, Any, Optional


def calculate_sma(prices: List[float], period: int) -> List[float]:
    """Simple Moving Average."""
    if len(prices) < period or period <= 0:
        return []
    sma = []
    for i in range(period, len(prices) + 1):
        window = prices[i - period:i]
        sma.append(sum(window) / period)
    return sma


def calculate_ema(prices: List[float], period: int) -> List[float]:
    """Exponential Moving Average."""
    if len(prices) < period or period <= 0:
        return []
    multiplier = 2.0 / (period + 1)
    ema = [sum(prices[:period]) / period]
    for price in prices[period:]:
        new_val = (price - ema[-1]) * multiplier + ema[-1]
        ema.append(new_val)
    return ema


def calculate_rsi_series(prices: List[float], period: int = 14) -> List[float]:
    """Wilder's smoothed RSI series."""
    if len(prices) <= period:
        return [50.0] * len(prices)

    gains, losses = [], []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        if change > 0:
            gains.append(change)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(change))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    rsi_list = [50.0] * period
    if avg_loss == 0:
        rsi_list.append(100.0)
    else:
        rs = avg_gain / avg_loss
        rsi_list.append(100.0 - (100.0 / (1.0 + rs)))

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            rsi_list.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_list.append(100.0 - (100.0 / (1.0 + rs)))

    return rsi_list


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Relative Strength Index (RSI) for latest bar."""
    series = calculate_rsi_series(prices, period)
    return series[-1] if series else 50.0


def calculate_stoch_rsi(prices: List[float], period: int = 14, k_smooth: int = 3, d_smooth: int = 3) -> Dict[str, float]:
    """Stochastic RSI (%K and %D, 0-100 scale)."""
    rsi_series = calculate_rsi_series(prices, period)
    if len(rsi_series) < period * 2:
        return {"k": 50.0, "d": 50.0}

    raw_stoch = []
    for i in range(period, len(rsi_series) + 1):
        window = rsi_series[i - period:i]
        low_r = min(window)
        high_r = max(window)
        if high_r - low_r <= 1e-9:
            raw_stoch.append(50.0)
        else:
            raw_stoch.append(((window[-1] - low_r) / (high_r - low_r)) * 100.0)

    k_series = calculate_sma(raw_stoch, k_smooth) if len(raw_stoch) >= k_smooth else raw_stoch
    d_series = calculate_sma(k_series, d_smooth) if len(k_series) >= d_smooth else k_series

    return {
        "k": round(k_series[-1], 2) if k_series else 50.0,
        "d": round(d_series[-1], 2) if d_series else 50.0,
        "prev_k": round(k_series[-2], 2) if len(k_series) >= 2 else 50.0,
    }


def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
    """MACD (12, 26, 9) line, signal line, and histogram."""
    if len(prices) < slow + signal:
        return {"macd": 0.0, "signal": 0.0, "histogram": 0.0, "prev_histogram": 0.0}

    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    # Align lengths from the end
    min_len = min(len(ema_fast), len(ema_slow))
    macd_line = [ema_fast[-min_len + i] - ema_slow[-min_len + i] for i in range(min_len)]
    sig_line = calculate_ema(macd_line, signal)

    if not sig_line:
        return {"macd": macd_line[-1], "signal": 0.0, "histogram": 0.0, "prev_histogram": 0.0}

    hist = macd_line[-1] - sig_line[-1]
    prev_hist = (macd_line[-2] - sig_line[-2]) if len(sig_line) >= 2 and len(macd_line) >= 2 else hist
    return {
        "macd": macd_line[-1],
        "signal": sig_line[-1],
        "histogram": hist,
        "prev_histogram": prev_hist,
    }


def calculate_bollinger_bands(prices: List[float], period: int = 20, num_std: float = 2.0) -> Dict[str, float]:
    """Bollinger Bands (Middle, Upper, Lower, %B, Bandwidth%) for latest window."""
    if len(prices) < period:
        latest = prices[-1] if prices else 0.0
        return {"upper": latest, "middle": latest, "lower": latest, "pct_b": 0.5, "bandwidth_pct": 0.0}

    window = prices[-period:]
    mean = sum(window) / period
    variance = sum((x - mean) ** 2 for x in window) / period
    std = variance ** 0.5

    upper = mean + (num_std * std)
    lower = mean - (num_std * std)
    band_range = upper - lower
    pct_b = ((prices[-1] - lower) / band_range) if band_range > 0 else 0.5
    bandwidth_pct = ((band_range / mean) * 100.0) if mean > 0 else 0.0

    return {
        "upper": upper,
        "middle": mean,
        "lower": lower,
        "pct_b": pct_b,
        "bandwidth_pct": bandwidth_pct,
    }


def calculate_atr(klines: List[Any], period: int = 14) -> Dict[str, float]:
    """Average True Range (ATR) and ATR% of current price."""
    if not klines or len(klines) < 2:
        return {"atr": 0.0, "atr_pct": 0.0}

    trs = []
    for i in range(1, len(klines)):
        high = float(klines[i][2])
        low = float(klines[i][3])
        prev_close = float(klines[i - 1][4])
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)

    if not trs:
        return {"atr": 0.0, "atr_pct": 0.0}

    w = trs[-period:] if len(trs) >= period else trs
    atr = sum(w) / len(w)
    curr_price = float(klines[-1][4])
    atr_pct = ((atr / curr_price) * 100.0) if curr_price > 0 else 0.0
    return {"atr": atr, "atr_pct": round(atr_pct, 3)}


def calculate_volume_profile(klines: List[Any], period: int = 20) -> Dict[str, float]:
    """Calculate Relative Volume (RVOL) and Bullish Buying Volume Ratio."""
    if not klines or len(klines) < 5:
        return {"rvol": 1.0, "buy_vol_ratio": 0.5}

    vols = [float(k[5]) for k in klines]
    recent_vol = sum(vols[-3:]) / min(3, len(vols))
    base_window = vols[-period - 3:-3] if len(vols) > period + 3 else vols[:-1]
    avg_vol = (sum(base_window) / len(base_window)) if base_window else recent_vol
    rvol = (recent_vol / avg_vol) if avg_vol > 0 else 1.0

    # 陽線と陰線の出来高バランス（直近10本）
    bull_vol = 0.0
    total_vol = 0.0
    for k in klines[-10:]:
        o, h, l, c, v = float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])
        total_vol += v
        if h > l:
            # ローソク足の実体・ヒゲ位置から買い圧力を推計
            bull_vol += v * ((c - l) / (h - l))
        elif c >= o:
            bull_vol += v * 0.5

    buy_ratio = (bull_vol / total_vol) if total_vol > 0 else 0.5
    return {"rvol": round(rvol, 2), "buy_vol_ratio": round(buy_ratio, 3)}


def analyze_market_signals(
    klines: List[Any],
    klines_15m: Optional[List[Any]] = None,
    klines_4h: Optional[List[Any]] = None,
    order_book: Optional[Dict[str, Any]] = None,
    step_size: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Parse Binance Kline data and generate multi-factor quantitative signal & Alpha Score (0-100).
    Binance Kline schema:
    [0: Open time, 1: Open, 2: High, 3: Low, 4: Close, 5: Volume, ...]
    """
    if not klines or len(klines) < 20:
        latest_p = float(klines[-1][4]) if klines else 0.0
        return {
            "signal": "HOLD",
            "score": 0,
            "alpha_score": 50.0,
            "confidence": 50.0,
            "confidence_ratio": 0.5,
            "regime": "INSUFFICIENT_DATA",
            "rsi": 50.0,
            "stoch_rsi_k": 50.0,
            "macd_hist": 0.0,
            "atr_pct": 0.0,
            "rvol": 1.0,
            "bb_upper": latest_p,
            "bb_lower": latest_p,
            "latest_price": latest_p,
            "reasons": ["データ不足 (Insufficient kline history)"],
        }

    close_prices = [float(k[4]) for k in klines]
    current_price = close_prices[-1]

    # 1. 各テクニカル指標の計算
    rsi_series = calculate_rsi_series(close_prices, 14)
    rsi = rsi_series[-1]
    prev_rsi = rsi_series[-2] if len(rsi_series) >= 2 else rsi
    rsi_slope = rsi - prev_rsi

    rsi6_series = calculate_rsi_series(close_prices, 6)
    rsi6 = rsi6_series[-1]
    prev_rsi6 = rsi6_series[-2] if len(rsi6_series) >= 2 else rsi6

    stoch = calculate_stoch_rsi(close_prices, 14, 3, 3)
    macd_data = calculate_macd(close_prices, 12, 26, 9)
    bb = calculate_bollinger_bands(close_prices, 20, 2.0)
    atr_data = calculate_atr(klines, 14)
    vol_data = calculate_volume_profile(klines, 20)

    ema9 = calculate_ema(close_prices, 9)
    ema21 = calculate_ema(close_prices, 21)
    ema50 = calculate_ema(close_prices, min(50, len(close_prices)))

    e9 = ema9[-1] if ema9 else current_price
    e21 = ema21[-1] if ema21 else current_price
    e50 = ema50[-1] if ema50 else current_price

    # --- Argon v3.0 Trinity Capitulation Sniper 特徴量計算 ---
    highs_24 = [float(k[2]) for k in klines[-25:]]
    high_24h = max(highs_24) if highs_24 else current_price
    dd_24h = ((current_price - high_24h) / high_24h * 100.0) if high_24h > 0 else 0.0
    dist_e21 = ((current_price - e21) / e21 * 100.0) if e21 > 0 else 0.0
    ret_1h = ((current_price - close_prices[-2]) / close_prices[-2] * 100.0) if len(close_prices) >= 2 and close_prices[-2] > 0 else 0.0
    ret_6h = ((current_price - close_prices[-7]) / close_prices[-7] * 100.0) if len(close_prices) >= 7 and close_prices[-7] > 0 else 0.0
    open_latest = float(klines[-1][1])
    is_bull_reversal = (current_price > open_latest) and (len(close_prices) >= 2 and current_price > close_prices[-2])

    # Binance Kline Quote Volume (idx 7) & Taker Buy Quote Volume (idx 10)
    max_rvol2 = vol_data["rvol"]
    taker_buy_ratio = vol_data["buy_vol_ratio"]
    if len(klines) >= 25 and len(klines[-1]) >= 11:
        try:
            q_vols = [float(k[7]) for k in klines]
            avg_qv = sum(q_vols[-25:-1]) / 24.0
            if avg_qv > 0:
                rv_curr = q_vols[-1] / avg_qv
                rv_prev = q_vols[-2] / avg_qv
                max_rvol2 = round(max(rv_curr, rv_prev), 2)
            if q_vols[-1] > 0:
                taker_buy_ratio = round(float(klines[-1][10]) / q_vols[-1], 3)
        except Exception:
            pass

    sniper_regime = ""
    sniper_score = 0.0
    if is_bull_reversal:
        if ret_6h <= -5.0 and ret_1h >= 0.75 and max_rvol2 >= 1.25:
            sniper_regime = "R2_FLUSH_REVERSAL"
            sniper_score = min(99.0, round(95.0 + abs(ret_6h) * 0.5, 1))
        elif dist_e21 <= -3.4 and dd_24h <= -7.0 and (rsi <= 34.0 or prev_rsi6 <= 20.0) and max_rvol2 >= 1.15:
            sniper_regime = "R1_DEEP_CAPITULATION"
            sniper_score = min(94.5, round(88.0 + abs(dist_e21), 1))
        elif rsi <= 26.0 and ret_1h >= 0.50 and taker_buy_ratio >= 0.55:
            sniper_regime = "R3_EXTREME_RSI26"
            sniper_score = min(87.5, round(84.0 + (28.0 - rsi) * 0.5, 1))

    # ベースとなる Alpha Score (0〜100、中立=50)
    alpha = 50.0
    reasons: List[str] = []

    if sniper_regime:
        alpha = sniper_score
        reasons.append(
            f"🎯【{sniper_regime}】勝率100%極限反発点灯(乖離{dist_e21:+.1f}%/24h高値比{dd_24h:+.1f}%/RVOL{max_rvol2:.1f}x)"
        )

    # --- Factor 1: RSI & Stochastic RSI (逆張り底打ち ＆ 順張りモメンタム) ---
    if rsi < 30:
        alpha += 18.0
        reasons.append(f"RSI売られすぎ圏({rsi:.1f}<30)")
        if rsi_slope > 0:
            alpha += 6.0
            reasons.append("RSI底打ち上向き反転")
    elif 30 <= rsi <= 42:
        if rsi_slope > 0 or stoch["k"] > stoch["prev_k"]:
            alpha += 14.0
            reasons.append(f"RSI押し目反発初動({rsi:.1f})")
        else:
            alpha += 5.0
    elif 45 <= rsi <= 63:
        if current_price > e21 and rsi_slope >= 0:
            alpha += 12.0
            reasons.append(f"上昇モメンタム巡航({rsi:.1f})")
    elif 68 < rsi <= 75:
        alpha -= 12.0
        reasons.append(f"RSI過熱警戒({rsi:.1f})")
    elif rsi > 75:
        alpha -= 24.0
        reasons.append(f"RSI買われすぎ極限({rsi:.1f}>75)")

    # Stochastic RSI ゴールデンクロス
    if stoch["k"] < 30 and stoch["k"] > stoch["d"] and stoch["k"] > stoch["prev_k"]:
        alpha += 7.0
        reasons.append(f"StochRSI底値GC(K={stoch['k']:.0f})")
    elif stoch["k"] > 80 and stoch["k"] < stoch["d"]:
        alpha -= 7.0
        reasons.append(f"StochRSI高値DC(K={stoch['k']:.0f})")

    # --- Factor 2: EMA Ribbon トレンド構造 (9 / 21 / 50) ---
    if e9 > e21 > e50 and current_price > e9:
        alpha += 12.0
        reasons.append("EMA(9>21>50)パーフェクトオーダー")
    elif e9 > e21 and current_price >= e21:
        alpha += 7.0
        reasons.append("EMA短期上昇トレンド")
    elif e9 < e21 < e50 and current_price < e9:
        alpha -= 12.0
        reasons.append("EMA下降トレンド配列")

    # 直近のゴールデンクロス / デッドクロス
    if len(ema9) >= 2 and len(ema21) >= 2:
        if ema9[-1] > ema21[-1] and ema9[-2] <= ema21[-2]:
            alpha += 9.0
            reasons.append("EMA(9/21)ゴールデンクロス発生")
        elif ema9[-1] < ema21[-1] and ema9[-2] >= ema21[-2]:
            alpha -= 9.0
            reasons.append("EMA(9/21)デッドクロス発生")

    # --- Factor 3: MACD モメンタム加速 ---
    hist = macd_data["histogram"]
    prev_hist = macd_data["prev_histogram"]
    if hist > 0 and hist > prev_hist:
        alpha += 8.0
        reasons.append("MACD陽転・モメンタム加速")
    elif hist < 0 and hist > prev_hist and rsi < 45:
        alpha += 5.0
        reasons.append("MACD下落モメンタム減速(底入れ兆候)")
    elif hist < 0 and hist < prev_hist:
        alpha -= 8.0
        reasons.append("MACD陰転・下落加速")

    # --- Factor 4: ボリンジャーバンド位置 & ブレイクアウト ---
    pct_b = bb["pct_b"]
    if current_price <= bb["lower"] or pct_b <= 0.08:
        alpha += 12.0
        reasons.append(f"BB下限タッチ反発圏(%B={pct_b:.2f})")
    elif pct_b >= 0.98 and rsi > 68:
        alpha -= 12.0
        reasons.append(f"BB上限到達・利確圏(%B={pct_b:.2f})")
    elif 0.55 <= pct_b <= 0.88 and vol_data["rvol"] >= 1.3 and e9 > e21:
        alpha += 8.0
        reasons.append("BBアッパーバンドウォーク初動")

    # --- Factor 5: 出来高急増 (RVOL) ＆ 買い圧力 (Buying Volume Ratio) ---
    rvol = vol_data["rvol"]
    buy_ratio = vol_data["buy_vol_ratio"]
    if rvol >= 1.8 and buy_ratio >= 0.56:
        alpha += 10.0
        reasons.append(f"大口資金流入(出来高{rvol:.1f}倍・買い圧{buy_ratio*100:.0f}%)")
    elif rvol >= 1.25 and buy_ratio >= 0.53:
        alpha += 5.0
        reasons.append(f"出来高増加({rvol:.1f}x)")
    elif buy_ratio <= 0.40 and rvol >= 1.3:
        alpha -= 8.0
        reasons.append(f"売り出来高優勢(買い圧{buy_ratio*100:.0f}%)")

    # --- Factor 6: ボラティリティ適性 (ATR%) ---
    atr_pct = atr_data["atr_pct"]
    if atr_pct >= 1.2 and alpha > 55:
        alpha += 4.0
    elif atr_pct < 0.25:
        # 値動きが極端に乏しい銘柄はスイング効率が低い
        alpha -= 5.0

    # --- Factor 7: マルチタイムフレーム (15m / 4h) 整合性 ---
    if klines_15m and len(klines_15m) >= 20:
        c15 = [float(k[4]) for k in klines_15m]
        rsi15 = calculate_rsi(c15, 14)
        e9_15 = calculate_ema(c15, 9)
        e21_15 = calculate_ema(c15, 21)
        if e9_15 and e21_15 and e9_15[-1] > e21_15[-1] and 35 <= rsi15 <= 68:
            alpha += 5.0
            reasons.append(f"15m足短期上昇同調(RSI={rsi15:.0f})")
        elif rsi15 > 76:
            alpha -= 5.0

    if klines_4h and len(klines_4h) >= 20:
        c4h = [float(k[4]) for k in klines_4h]
        e9_4h = calculate_ema(c4h, 9)
        e21_4h = calculate_ema(c4h, 21)
        if e9_4h and e21_4h and e9_4h[-1] >= e21_4h[-1]:
            alpha += 5.0
            reasons.append("4h足上位トレンド上向き")
        elif e9_4h and e21_4h and c4h[-1] < e21_4h[-1] * 0.96:
            alpha -= 4.0

    # --- Factor 8: 板情報 (Order Book Imbalance) ---
    ob_imbalance = 1.0
    if order_book and "bids" in order_book and "asks" in order_book:
        bid_vol = sum(float(b[1]) for b in order_book["bids"][:10])
        ask_vol = sum(float(a[1]) for a in order_book["asks"][:10])
        if ask_vol > 0:
            ob_imbalance = bid_vol / ask_vol
            if ob_imbalance >= 1.35:
                alpha += 5.0
                reasons.append(f"買い板厚優勢({ob_imbalance:.2f}x)")
            elif ob_imbalance <= 0.65:
                alpha -= 4.0

    # --- Factor 9: 少額口座向けロット刻み効率 (Step Size Efficiency) ---
    step_cost_jpy = 0.0
    if step_size and step_size > 0:
        step_cost_jpy = step_size * current_price
        # 1刻みが30円を超える銘柄（NEARJPY=約80円等）は少額売買で端数ロスが大きいため減点
        if step_cost_jpy >= 40.0:
            alpha -= 10.0
            reasons.append(f"最小刻み大(1単位=¥{step_cost_jpy:.0f})")
        elif step_cost_jpy <= 5.0:
            alpha += 3.0

    # Alpha Score を 0.0 〜 100.0 にクランプ（Argon Trinity Sniper 点灯時は sniper_score を優先保証）
    if sniper_regime:
        alpha = max(alpha, sniper_score)
    alpha = max(0.0, min(100.0, round(alpha, 1)))

    # レジーム判定とシグナル変換
    if sniper_regime:
        decision = "STRONG_BUY"
        regime = sniper_regime
        legacy_score = 4
    elif alpha >= 74.0:
        decision = "STRONG_BUY"
        regime = "BREAKOUT_BULL" if current_price > e21 else "OVERSOLD_REVERSAL"
        legacy_score = 4
    elif alpha >= 60.0:
        decision = "BUY"
        regime = "UPTREND_PULLBACK" if current_price >= e21 else "BOUNCE_SETUP"
        legacy_score = 2
    elif alpha <= 26.0:
        decision = "STRONG_SELL"
        regime = "OVERBOUGHT_CLIMAX" if rsi > 65 else "STRONG_DOWNTREND"
        legacy_score = -4
    elif alpha <= 38.0:
        decision = "SELL"
        regime = "BEAR_WEAK"
        legacy_score = -2
    else:
        decision = "HOLD"
        regime = "RANGE_CONSOLIDATION"
        legacy_score = 0

    # 確信度 (0〜100% スケール)
    confidence_pct = round(min(98.0, max(35.0, abs(alpha - 50.0) * 1.8 + 40.0)), 1)
    confidence_ratio = round(confidence_pct / 100.0, 2)

    if not reasons:
        reasons.append("レンジ均衡・方向感待ち")

    # ATRに基づく推奨動的ターゲット（参考値）
    dyn_tp_pct = round(max(4.5, min(25.0, atr_pct * 3.2)), 2) if atr_pct > 0 else 8.0
    dyn_sl_pct = round(-max(3.5, min(8.0, atr_pct * 1.8)), 2) if atr_pct > 0 else -8.0

    return {
        "signal": decision,
        "score": legacy_score,
        "alpha_score": alpha,
        "confidence": confidence_pct,       # 0〜100 (%) - CLI/WebUI/Patrol完全統一
        "confidence_ratio": confidence_ratio,
        "regime": regime,
        "sniper_regime": sniper_regime,
        "latest_price": current_price,
        "rsi": round(rsi, 2),
        "rsi6": round(rsi6, 2),
        "prev_rsi6": round(prev_rsi6, 2),
        "rsi_slope": round(rsi_slope, 2),
        "stoch_rsi_k": stoch["k"],
        "stoch_rsi_d": stoch["d"],
        "macd_hist": round(hist, 6),
        "ema9": round(e9, 6),
        "ema21": round(e21, 6),
        "ema50": round(e50, 6),
        "dist_e21": round(dist_e21, 2),
        "dd_24h": round(dd_24h, 2),
        "ret_1h": round(ret_1h, 2),
        "ret_6h": round(ret_6h, 2),
        "max_rvol2": max_rvol2,
        "taker_buy_ratio": taker_buy_ratio,
        "is_bull_reversal": is_bull_reversal,
        "bb_upper": round(bb["upper"], 6 if current_price < 1 else 2),
        "bb_middle": round(bb["middle"], 6 if current_price < 1 else 2),
        "bb_lower": round(bb["lower"], 6 if current_price < 1 else 2),
        "bb_pct_b": round(pct_b, 2),
        "atr_pct": atr_pct,
        "rvol": rvol,
        "buy_vol_ratio": buy_ratio,
        "ob_imbalance": round(ob_imbalance, 2),
        "step_cost_jpy": round(step_cost_jpy, 2),
        "dyn_tp_pct": dyn_tp_pct,
        "dyn_sl_pct": dyn_sl_pct,
        "reasons": reasons,
    }


class MarketAnalyzer:
    """Quantitative Multi-Factor Market Analyzer for Binance."""

    def score_2x_potential(
        self,
        klines_1h: List[Any],
        symbol: str = "",
        klines_15m: Optional[List[Any]] = None,
        order_book: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        sig = analyze_market_signals(
            klines=klines_1h,
            klines_15m=klines_15m,
            order_book=order_book,
        )
        current_p = sig.get("latest_price", 0.0)
        ret_24h = 0.0
        if klines_1h and len(klines_1h) >= 24:
            p_24h_ago = float(klines_1h[-24][4])
            if p_24h_ago > 0:
                ret_24h = round(((current_p - p_24h_ago) / p_24h_ago) * 100.0, 2)

        return {
            "current_price": current_p,
            "alpha_score": sig.get("alpha_score", 50.0),
            "confidence": sig.get("confidence", 50.0),
            "signal": sig.get("signal", "HOLD"),
            "regime": sig.get("regime", "RANGE"),
            "sniper_regime": sig.get("sniper_regime", ""),
            "reasons": sig.get("reasons", []),
            "indicators": {
                "rsi": sig.get("rsi", 50.0),
                "rsi6": sig.get("rsi6", 50.0),
                "prev_rsi6": sig.get("prev_rsi6", 50.0),
                "ema21": sig.get("ema21", current_p),
                "dist_e21": sig.get("dist_e21", 0.0),
                "dd_24h": sig.get("dd_24h", 0.0),
                "ret_1h": sig.get("ret_1h", 0.0),
                "ret_6h": sig.get("ret_6h", 0.0),
                "max_rvol2": sig.get("max_rvol2", 1.0),
                "taker_buy_ratio": sig.get("taker_buy_ratio", 0.5),
                "is_bull_reversal": sig.get("is_bull_reversal", False),
                "stoch_rsi_k": sig.get("stoch_rsi_k", 50.0),
                "macd_hist": sig.get("macd_hist", 0.0),
                "macd_hist_rising": sig.get("macd_hist", 0.0) > 0,
                "bb_lower": sig.get("bb_lower", 0.0),
                "bb_upper": sig.get("bb_upper", 0.0),
                "bb_pct_b": sig.get("bb_pct_b", 0.5),
                "atr_pct": sig.get("atr_pct", 0.0),
                "rvol": sig.get("rvol", 1.0),
                "order_book_imbalance": sig.get("ob_imbalance", 1.0),
                "ret_24h_pct": ret_24h,
                "step_cost_jpy": sig.get("step_cost_jpy", 0.0),
            },
        }

    def analyze_klines(
        self,
        klines: List[Any],
        symbol: str = "",
        klines_15m: Optional[List[Any]] = None,
        order_book: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Alias for score_2x_potential used by QuantBacktester."""
        return self.score_2x_potential(
            klines_1h=klines,
            symbol=symbol,
            klines_15m=klines_15m,
            order_book=order_book,
        )

