#!/usr/bin/env python3
"""
Price Action 数据预处理脚本 v2

用法:
  python preprocess.py "HK.800700"
  python preprocess.py "US.SPY"
  python preprocess.py "HK.800700" --full   # 输出全部80根bar

v2 变更:
  - 时区修复: 使用市场时区判定"今日"和交易时段
  - micro channel: 按Al Brooks原始定义 (bull=low>=prior low)
  - bar分类优先级: breakout > reversal > inside/outside
  - surprise检测: 统一overlap计算, 移除过严的gap条件
  - 新增三推检测 (swing point → three-push)
  - 新增swing_points输出
  - 紧凑输出: 默认输出今日bars + 足够引用已检测形态的前文
  - EMA20仅附加到今日bars
  - 信号形态/微通道/三推仅用今日K线，避免早盘跨隔夜误判
"""
import json
import sys
import os
import socket
import logging
from datetime import datetime, timedelta, timezone

logging.disable(logging.CRITICAL)

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

# ============================================================
# 市场配置
# ============================================================

_TZ_NAMES = {"US": "America/New_York", "HK": "Asia/Hong_Kong", "CN": "Asia/Shanghai"}
# Fallback: fixed UTC offsets (US uses EDT=-4; EST=-5 not auto-detected without zoneinfo)
_TZ_OFFSETS = {"US": -4, "HK": 8, "CN": 8}


def _market_tz(market):
    if ZoneInfo is not None:
        try:
            return ZoneInfo(_TZ_NAMES.get(market, "America/New_York"))
        except Exception:
            pass
    return timezone(timedelta(hours=_TZ_OFFSETS.get(market, 0)))


MARKET_CONFIG = {
    "US": {
        "open": "09:30", "close": "16:00", "lunch": None,
        "periods": [
            ("opening", "09:30", "10:00"),
            ("morning", "10:00", "11:30"),
            ("midday", "11:30", "13:00"),
            ("afternoon", "13:00", "15:30"),
            ("closing", "15:30", "16:00"),
        ],
    },
    "HK": {
        "open": "09:30", "close": "16:00", "lunch": ("12:00", "13:00"),
        "periods": [
            ("opening", "09:30", "10:00"),
            ("morning", "10:00", "12:00"),
            ("lunch", "12:00", "13:00"),
            ("afternoon_open", "13:00", "13:15"),
            ("afternoon", "13:15", "15:30"),
            ("closing", "15:30", "16:00"),
        ],
    },
    "CN": {
        "open": "09:30", "close": "15:00", "lunch": ("11:30", "13:00"),
        "periods": [
            ("opening", "09:30", "10:00"),
            ("morning", "10:00", "11:30"),
            ("lunch", "11:30", "13:00"),
            ("afternoon_open", "13:00", "13:15"),
            ("afternoon", "13:15", "14:30"),
            ("closing", "14:30", "15:00"),
        ],
    },
}

_CODE_PREFIX_TO_MARKET = {"US": "US", "HK": "HK", "SH": "CN", "SZ": "CN"}


def infer_market(code):
    prefix = code.split(".")[0].upper() if "." in code else ""
    return _CODE_PREFIX_TO_MARKET.get(prefix, "US")


# ============================================================
# 数据获取
# ============================================================

def fetch_klines(code, host, port):
    from futu import OpenQuoteContext, RET_OK, SubType, KLType, AuType

    KTYPE_SUB = [
        (KLType.K_5M, SubType.K_5M, 80),
        (KLType.K_DAY, SubType.K_DAY, 25),
    ]

    ctx = OpenQuoteContext(host=host, port=port)
    try:
        sub_types = [s for _, s, _ in KTYPE_SUB]
        ret, msg = ctx.subscribe([code], sub_types)
        if ret != RET_OK:
            return None, None, f"订阅失败: {msg}"

        results = {}
        for kl_type, _, num in KTYPE_SUB:
            ret, data = ctx.get_cur_kline(code, num, kl_type, AuType.QFQ)
            if ret != RET_OK:
                return None, None, f"获取K线失败 ({kl_type}): {data}"
            results[kl_type] = data

        return results[KLType.K_5M], results[KLType.K_DAY], None
    finally:
        ctx.close()


def df_to_list(df):
    rows = []
    if df is None or not hasattr(df, "shape") or df.shape[0] == 0:
        return rows
    for i in range(len(df)):
        r = df.iloc[i]
        rows.append({
            "time": str(r.get("time_key", "")),
            "open": float(r.get("open", 0)),
            "high": float(r.get("high", 0)),
            "low": float(r.get("low", 0)),
            "close": float(r.get("close", 0)),
            "volume": int(r.get("volume", 0)),
            "turnover": float(r.get("turnover", 0)),
        })
    return rows


# ============================================================
# EMA 计算
# ============================================================

def calc_ema(values, span=20):
    import pandas as pd
    s = pd.Series(values)
    return s.ewm(span=span, adjust=False).mean().tolist()


# ============================================================
# Bar 分类 (v2: breakout/reversal优先于inside/outside)
# ============================================================

def classify_bars(bars, baseline_body):
    for i, b in enumerate(bars):
        o, h, l, c = b["open"], b["high"], b["low"], b["close"]
        bar_range = h - l
        body = abs(c - o)
        upper_tail = h - max(o, c)
        lower_tail = min(o, c) - l

        b["body"] = round(body, 4)
        b["upper_tail"] = round(upper_tail, 4)
        b["lower_tail"] = round(lower_tail, 4)

        if baseline_body > 0:
            b["body_strength"] = (
                "large" if body >= 1.5 * baseline_body
                else "small" if body <= 0.5 * baseline_body
                else "normal"
            )
        else:
            b["body_strength"] = "normal"

        if bar_range > 0:
            close_pct = round((c - l) / bar_range * 100, 1)
        else:
            close_pct = 50.0
        b["close_pct"] = close_pct

        prev = bars[i - 1] if i > 0 else None
        b["is_inside"] = (
            prev is not None and h <= prev["high"] and l >= prev["low"]
        )
        b["is_outside"] = (
            prev is not None and h > prev["high"] and l < prev["low"]
        )

        b["bar_type"] = _classify_single_bar(
            b, bar_range, body, baseline_body, upper_tail, lower_tail, close_pct
        )


def _classify_single_bar(b, bar_range, body, baseline_body, upper_tail, lower_tail, close_pct):
    if bar_range == 0:
        return "doji"

    if baseline_body > 0 and body <= 0.3 * baseline_body:
        if body == 0 or (upper_tail <= 2 * body and lower_tail <= 2 * body):
            return "doji"

    # Breakout: highest priority actionable type
    if baseline_body > 0 and body >= 1.5 * baseline_body:
        if upper_tail < 0.25 * bar_range and lower_tail < 0.25 * bar_range:
            if close_pct >= 90:
                return "bull_breakout"
            if close_pct <= 10:
                return "bear_breakout"

    # Reversal: higher priority than structural inside/outside
    if close_pct >= 75 and lower_tail >= 0.5 * bar_range:
        return "bull_reversal"
    if close_pct <= 25 and upper_tail >= 0.5 * bar_range:
        return "bear_reversal"

    if b["is_inside"]:
        return "inside"
    if b["is_outside"]:
        return "outside"

    if (upper_tail >= 0.33 * bar_range and lower_tail >= 0.33 * bar_range
            and 25 <= close_pct <= 75):
        return "tr_bar"

    return "bull" if b["close"] >= b["open"] else "bear"


# ============================================================
# Swing Point 检测
# ============================================================

def find_swing_points(bars):
    """2-bar lookback, adaptive lookahead. Last bar uses lookback only."""
    n = len(bars)
    highs, lows = [], []

    for i in range(2, n):
        left_h = max(bars[i - 1]["high"], bars[i - 2]["high"])
        left_l = min(bars[i - 1]["low"], bars[i - 2]["low"])

        if i < n - 2:
            right_h = max(bars[i + 1]["high"], bars[i + 2]["high"])
            right_l = min(bars[i + 1]["low"], bars[i + 2]["low"])
        elif i < n - 1:
            right_h = bars[i + 1]["high"]
            right_l = bars[i + 1]["low"]
        else:
            right_h = bars[i]["high"]
            right_l = bars[i]["low"]

        if bars[i]["high"] >= left_h and bars[i]["high"] >= right_h:
            if not highs or i - highs[-1][0] >= 2:
                highs.append((i, bars[i]["high"]))
            elif bars[i]["high"] > highs[-1][1]:
                highs[-1] = (i, bars[i]["high"])

        if bars[i]["low"] <= left_l and bars[i]["low"] <= right_l:
            if not lows or i - lows[-1][0] >= 2:
                lows.append((i, bars[i]["low"]))
            elif bars[i]["low"] < lows[-1][1]:
                lows[-1] = (i, bars[i]["low"])

    return highs, lows


# ============================================================
# Pattern 检测 (v2: surprise overlap统一计算)
# ============================================================

def detect_patterns(bars, baseline_body):
    patterns = []
    n = len(bars)
    if n < 3:
        return patterns

    for i in range(1, n):
        if bars[i]["is_outside"] and bars[i - 1]["is_outside"]:
            patterns.append({"type": "oo_breakout", "bars": [i - 1, i]})

    for i in range(2, n):
        if bars[i - 2]["is_inside"] and bars[i - 1]["is_outside"] and bars[i]["is_inside"]:
            patterns.append({"type": "ioi", "bars": [i - 2, i - 1, i]})

    # Bull/Bear Surprise: unified overlap calculation
    for length in (3, 2):
        for i in range(length - 1, n):
            start = i - length + 1
            chunk = bars[start:i + 1]
            if baseline_body <= 0:
                break
            all_bull = all(
                b["close"] > b["open"] and b["close_pct"] >= 75
                and b["body"] >= baseline_body for b in chunk
            )
            all_bear = all(
                b["close"] < b["open"] and b["close_pct"] <= 25
                and b["body"] >= baseline_body for b in chunk
            )
            if not (all_bull or all_bear):
                continue
            minimal_overlap = True
            for j in range(1, len(chunk)):
                overlap = (min(chunk[j]["high"], chunk[j - 1]["high"])
                           - max(chunk[j]["low"], chunk[j - 1]["low"]))
                if overlap > 0:
                    max_body = max(chunk[j]["body"], chunk[j - 1]["body"])
                    if max_body > 0 and overlap > 0.5 * max_body:
                        minimal_overlap = False
                        break
            if minimal_overlap:
                direction = "bull_surprise" if all_bull else "bear_surprise"
                idx_list = list(range(start, i + 1))
                if not any(p["type"] == direction and set(p["bars"]) & set(idx_list)
                           for p in patterns):
                    patterns.append({"type": direction, "bars": idx_list})

    scan_start = max(0, n - 10)
    raw_dt, raw_db = [], []
    for i in range(scan_start, n):
        for j in range(i + 2, min(i + 5, n)):
            h_diff = abs(bars[i]["high"] - bars[j]["high"])
            if bars[i]["high"] > 0 and h_diff / bars[i]["high"] <= 0.001:
                raw_dt.append({
                    "type": "micro_double_top",
                    "bars": [i, j],
                    "level": round(max(bars[i]["high"], bars[j]["high"]), 4),
                })
            l_diff = abs(bars[i]["low"] - bars[j]["low"])
            if bars[i]["low"] > 0 and l_diff / bars[i]["low"] <= 0.001:
                raw_db.append({
                    "type": "micro_double_bottom",
                    "bars": [i, j],
                    "level": round(min(bars[i]["low"], bars[j]["low"]), 4),
                })

    # Deduplicate DT and DB independently
    kept_dt, kept_db = [], []
    for group, kept in ((raw_dt, kept_dt), (raw_db, kept_db)):
        for p in reversed(group):
            if not any(abs(p["level"] - k["level"]) / max(p["level"], 1) < 0.002
                       for k in kept):
                kept.append(p)
            if len(kept) >= 3:
                break

    # Suppress overlapping DT/DB (same bars → TR noise, not directional signal)
    dt_bar_sets = [frozenset(p["bars"]) for p in kept_dt]
    db_bar_sets = [frozenset(p["bars"]) for p in kept_db]
    for p in reversed(kept_dt):
        if not any(frozenset(p["bars"]) == bs for bs in db_bar_sets):
            patterns.append(p)
    for p in reversed(kept_db):
        if not any(frozenset(p["bars"]) == bs for bs in dt_bar_sets):
            patterns.append(p)

    return patterns


# ============================================================
# Micro Channel 检测 (v2: Al Brooks原始定义)
# ============================================================

def detect_micro_channel(bars):
    """
    Bull: each bar's low >= prior bar's low (no pullback dips below prior bar)
    Bear: each bar's high <= prior bar's high (no bounce exceeds prior bar)
    """
    n = len(bars)
    if n < 3:
        return {"active": False}

    bull_pairs = 0
    for i in range(n - 1, 0, -1):
        if bars[i]["low"] >= bars[i - 1]["low"]:
            bull_pairs += 1
        else:
            break

    bear_pairs = 0
    for i in range(n - 1, 0, -1):
        if bars[i]["high"] <= bars[i - 1]["high"]:
            bear_pairs += 1
        else:
            break

    min_pairs = 2  # 3 bars in sequence.
    if bull_pairs >= min_pairs or bear_pairs >= min_pairs:
        if bull_pairs >= bear_pairs:
            return {
                "active": True, "direction": "bull",
                "start_idx": n - 1 - bull_pairs, "length": bull_pairs + 1,
            }
        return {
            "active": True, "direction": "bear",
            "start_idx": n - 1 - bear_pairs, "length": bear_pairs + 1,
        }

    return {"active": False}


# ============================================================
# Three-Push 检测 (v2 新增)
# ============================================================

def detect_three_pushes(bars):
    n = len(bars)
    if n < 10:
        return []

    swing_highs, swing_lows = find_swing_points(bars)
    results = []

    for i in range(len(swing_lows) - 2):
        l1, l2, l3 = swing_lows[i], swing_lows[i + 1], swing_lows[i + 2]
        if l1[1] > l2[1] > l3[1]:
            if (any(h[0] > l1[0] and h[0] < l2[0] for h in swing_highs)
                    and any(h[0] > l2[0] and h[0] < l3[0] for h in swing_highs)):
                results.append({
                    "type": "bear_three_push",
                    "pushes": [l1[0], l2[0], l3[0]],
                    "levels": [round(l1[1], 4), round(l2[1], 4), round(l3[1], 4)],
                    "complete": l3[0] <= n - 3,
                })

    for i in range(len(swing_highs) - 2):
        h1, h2, h3 = swing_highs[i], swing_highs[i + 1], swing_highs[i + 2]
        if h1[1] < h2[1] < h3[1]:
            if (any(l[0] > h1[0] and l[0] < h2[0] for l in swing_lows)
                    and any(l[0] > h2[0] and l[0] < h3[0] for l in swing_lows)):
                results.append({
                    "type": "bull_three_push",
                    "pushes": [h1[0], h2[0], h3[0]],
                    "levels": [round(h1[1], 4), round(h2[1], 4), round(h3[1], 4)],
                    "complete": h3[0] <= n - 3,
                })

    bear = [r for r in results if r["type"] == "bear_three_push"]
    bull = [r for r in results if r["type"] == "bull_three_push"]
    final = []
    if bear:
        final.append(bear[-1])
    if bull:
        final.append(bull[-1])
    return final


# ============================================================
# Session 检测 (v2: 使用市场时区)
# ============================================================

def detect_session(market, bars_today_count):
    cfg = MARKET_CONFIG.get(market, MARKET_CONFIG["US"])
    tz = _market_tz(market)
    now = datetime.now(tz)

    if now.weekday() >= 5:
        return {
            "current_period": "closed",
            "bars_today": bars_today_count,
            "is_lunch": False,
            "minutes_to_close": 0,
        }

    close_h, close_m = map(int, cfg["close"].split(":"))
    close_time = now.replace(hour=close_h, minute=close_m, second=0, microsecond=0)
    minutes_to_close = max(0, int((close_time - now).total_seconds() / 60))

    current_period = "closed"
    now_str = now.strftime("%H:%M")
    for name, start, end in cfg["periods"]:
        if start <= now_str < end:
            current_period = name
            break

    if now_str >= cfg["close"] or now_str < cfg["open"]:
        current_period = "closed"

    is_lunch = False
    if cfg["lunch"]:
        lunch_start, lunch_end = cfg["lunch"]
        if lunch_start <= now_str < lunch_end:
            is_lunch = True

    return {
        "current_period": current_period,
        "bars_today": bars_today_count,
        "is_lunch": is_lunch,
        "minutes_to_close": minutes_to_close,
    }


# ============================================================
# Today判定 (v2: 使用市场时区)
# ============================================================

def _today_start_idx(bars, market):
    if not bars:
        return 0
    tz = _market_tz(market)
    today_str = datetime.now(tz).strftime("%Y-%m-%d")
    for i, b in enumerate(bars):
        if b["time"].startswith(today_str):
            return i
    return len(bars)


# ============================================================
# 主处理流程
# ============================================================

def process(code, full_output=False):
    market = infer_market(code)

    host = os.getenv("FUTU_OPEND_HOST", "127.0.0.1")
    port = int(os.getenv("FUTU_OPEND_PORT", "11111"))

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        sock.connect((host, port))
    except (ConnectionRefusedError, OSError) as e:
        return {"error": f"无法连接OpenD ({host}:{port}): {e}"}
    finally:
        sock.close()

    df_5m, df_daily, err = fetch_klines(code, host, port)
    if err:
        return {"error": err}

    bars_5m = df_to_list(df_5m)
    bars_daily = df_to_list(df_daily)

    if not bars_5m and not bars_daily:
        return {"error": "未获取到任何K线数据"}

    # --- Daily ---
    daily_closes = [b["close"] for b in bars_daily]
    daily_ema20 = calc_ema(daily_closes, 20) if daily_closes else []

    daily_ranges = [b["high"] - b["low"] for b in bars_daily]
    adr = round(sum(daily_ranges[-20:]) / len(daily_ranges[-20:]), 4) if daily_ranges else 0

    # Today bars (market-timezone aware)
    t_start = _today_start_idx(bars_5m, market)
    today_count = len(bars_5m) - t_start
    today_date = bars_5m[t_start]["time"][:10] if today_count > 0 else None

    prior_day = None
    if bars_daily:
        latest_daily_is_today = bool(today_date and bars_daily[-1]["time"].startswith(today_date))
        prior_idx = -2 if latest_daily_is_today and len(bars_daily) >= 2 else -1
        d = bars_daily[prior_idx]
        baseline_end = len(bars_daily) + prior_idx
        baseline_slice = bars_daily[max(0, baseline_end - 20):baseline_end]
        d_baseline = (
            sum(abs(b["close"] - b["open"]) for b in baseline_slice) / len(baseline_slice)
        ) if baseline_slice else abs(d["close"] - d["open"])
        classify_bars([d], d_baseline)
        prior_day = {
            "high": d["high"], "low": d["low"], "close": d["close"],
            "open": d["open"], "bar_type": d.get("bar_type", ""),
        }

    # Gap
    gap = {"size": 0, "pct_of_adr": 0, "classification": "none"}
    if prior_day and today_count > 0:
        gap_size = round(bars_5m[t_start]["open"] - prior_day["close"], 4)
        gap["size"] = gap_size
        gap_pct = round(gap_size / adr * 100, 2) if adr else 0
        gap["pct_of_adr"] = gap_pct
        abs_pct = abs(gap_pct)
        gap["classification"] = (
            "large" if abs_pct > 50 else "medium" if abs_pct > 25 else "small" if abs_pct > 5 else "none"
        )

    # --- Intraday ---
    closes_5m = [b["close"] for b in bars_5m]
    ema20_5m = calc_ema(closes_5m, 20) if closes_5m else []

    recent_bodies = [abs(b["close"] - b["open"]) for b in bars_5m[-20:]] if bars_5m else []
    baseline_body = round(sum(recent_bodies) / len(recent_bodies), 4) if recent_bodies else 0

    classify_bars(bars_5m, baseline_body)

    for i, b in enumerate(bars_5m):
        b["ema20"] = round(ema20_5m[i], 4) if i < len(ema20_5m) else None

    # Today range
    if today_count > 0:
        today_bars = bars_5m[t_start:]
        today_high = max(b["high"] for b in today_bars)
        today_low = min(b["low"] for b in today_bars)
    else:
        today_bars = []
        today_high = today_low = 0
    today_range = today_high - today_low
    range_position = (
        round((bars_5m[-1]["close"] - today_low) / today_range, 3)
        if today_count > 0 and today_range > 0
        else None
    )
    adr_consumed_pct = round((today_high - today_low) / adr * 100, 2) if adr else 0

    # Signal patterns: today's bars only. Prior-day bars are context, not live signals.
    scan_n = min(20, len(today_bars))
    scan_offset = t_start + len(today_bars) - scan_n if scan_n else len(bars_5m)
    patterns = detect_patterns(today_bars[-scan_n:], baseline_body) if scan_n >= 3 else []
    for p in patterns:
        p["bars"] = [idx + scan_offset for idx in p["bars"]]

    # Micro channel: today's bars only, otherwise early-session output can inherit yesterday.
    mc_n = min(20, len(today_bars))
    mc_offset = t_start + len(today_bars) - mc_n if mc_n else len(bars_5m)
    micro_ch = detect_micro_channel(today_bars[-mc_n:]) if mc_n >= 3 else {"active": False}
    if micro_ch.get("active") and "start_idx" in micro_ch:
        micro_ch["start_idx"] += mc_offset

    # Three-push: do not bridge overnight.
    if today_count >= 10:
        tp_slice = today_bars
        tp_offset = t_start
        three_pushes = detect_three_pushes(tp_slice)
    else:
        tp_offset = t_start if today_count > 0 else len(bars_5m)
        three_pushes = []
    for tp in three_pushes:
        tp["pushes"] = [idx + tp_offset for idx in tp["pushes"]]

    def opening_range(first_n):
        if today_count < first_n:
            return {"complete": False}
        chunk = today_bars[:first_n]
        hi = max(b["high"] for b in chunk)
        lo = min(b["low"] for b in chunk)
        width = hi - lo
        close = bars_5m[-1]["close"]
        if close > hi:
            state = "above"
        elif close < lo:
            state = "below"
        else:
            state = "inside"
        return {
            "complete": True,
            "high": round(hi, 4),
            "low": round(lo, 4),
            "width": round(width, 4),
            "position": round((close - lo) / width, 3) if width > 0 else None,
            "state": state,
        }

    # Swing points (today's bars if sufficient, else last 30)
    if today_count >= 5:
        sp_slice = bars_5m[t_start:]
        sp_offset = t_start
    else:
        sp_n = min(30, len(bars_5m))
        sp_slice = bars_5m[-sp_n:]
        sp_offset = len(bars_5m) - sp_n
    sp_highs, sp_lows = find_swing_points(sp_slice)
    swing_points = {
        "highs": [{"idx": idx + sp_offset, "level": round(v, 4)} for idx, v in sp_highs],
        "lows": [{"idx": idx + sp_offset, "level": round(v, 4)} for idx, v in sp_lows],
    }

    # --- EMA metrics (today's bars only) ---
    ema_crosses_today = 0
    if today_count >= 2:
        for i in range(t_start + 1, len(bars_5m)):
            e_prev = bars_5m[i - 1].get("ema20")
            e_curr = bars_5m[i].get("ema20")
            if e_prev and e_curr:
                prev_above = bars_5m[i - 1]["close"] > e_prev
                curr_above = bars_5m[i]["close"] > e_curr
                if prev_above != curr_above:
                    ema_crosses_today += 1

    ema_slope = 0
    if ema20_5m and len(ema20_5m) >= 5:
        recent_ema = ema20_5m[-5:]
        ema_slope = round((recent_ema[-1] - recent_ema[0]) / max(abs(recent_ema[0]), 1) * 100, 4)

    ema_distance_pct = 0
    if ema20_5m and bars_5m and adr > 0:
        ema_distance_pct = round((bars_5m[-1]["close"] - ema20_5m[-1]) / adr * 100, 2)

    # --- Bar stats (today only) ---
    bar_balance = {"bull": 0, "bear": 0, "neutral": 0, "bias": "balanced"}
    bar_stats = {"inside_count": 0, "outside_count": 0, "outside_pct": 0}
    if today_count > 0:
        today_bars = bars_5m[t_start:]
        for b in today_bars:
            bt = b.get("bar_type", "")
            if "bull" in bt:
                bar_balance["bull"] += 1
            elif "bear" in bt:
                bar_balance["bear"] += 1
            else:
                bar_balance["neutral"] += 1
            if b.get("is_inside"):
                bar_stats["inside_count"] += 1
            if b.get("is_outside"):
                bar_stats["outside_count"] += 1

        total = bar_balance["bull"] + bar_balance["bear"]
        if total > 0:
            bull_pct = bar_balance["bull"] / total
            bar_balance["bias"] = "bull" if bull_pct > 0.6 else "bear" if bull_pct < 0.4 else "balanced"

        bar_stats["outside_pct"] = round(bar_stats["outside_count"] / today_count * 100, 1)

    # --- Build output bars (compact by default) ---
    if full_output:
        out_start = 0
    else:
        referenced_starts = [max(0, t_start - 5), scan_offset, mc_offset, tp_offset, sp_offset]
        out_start = max(0, min(referenced_starts))

    enriched = []
    for i in range(out_start, len(bars_5m)):
        b = bars_5m[i]
        entry = {
            "idx": i,
            "time": b["time"],
            "o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"],
            "volume": b["volume"],
            "body": b["body"],
            "body_strength": b.get("body_strength", "normal"),
            "bar_type": b.get("bar_type", ""),
            "upper_tail": b["upper_tail"],
            "lower_tail": b["lower_tail"],
            "close_pct": b["close_pct"],
            "is_inside": b["is_inside"],
            "is_outside": b["is_outside"],
        }
        if i >= t_start:
            entry["ema20"] = b.get("ema20")
        enriched.append(entry)

    session = detect_session(market, today_count)

    return {
        "code": code,
        "market": market,
        "session": session,
        "daily": {
            "ema20": round(daily_ema20[-1], 4) if daily_ema20 else None,
            "adr": adr,
            "prior_day": prior_day,
            "gap": gap,
        },
        "intraday": {
            "baseline_body": baseline_body,
            "ema20_current": round(ema20_5m[-1], 4) if ema20_5m else None,
            "ema20_slope": ema_slope,
            "ema20_distance_pct": ema_distance_pct,
            "ema_crosses_today": ema_crosses_today,
            "today_range": {"high": round(today_high, 4), "low": round(today_low, 4)},
            "range_position": range_position,
            "opening_range": {
                "first_30m": opening_range(6),
                "first_90m": opening_range(18),
            },
            "adr_consumed_pct": adr_consumed_pct,
            "bar_balance": bar_balance,
            "bar_stats": bar_stats,
            "micro_channel": micro_ch,
            "patterns": patterns,
            "three_pushes": three_pushes,
            "swing_points": swing_points,
            "bars": enriched,
        },
    }


# ============================================================
# 入口
# ============================================================

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "用法: preprocess.py CODE [--full]"}, ensure_ascii=False))
        sys.exit(1)

    code = sys.argv[1]
    full = "--full" in sys.argv
    result = process(code, full_output=full)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    main()
