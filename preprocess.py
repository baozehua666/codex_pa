#!/usr/bin/env python3
"""
Price Action 数据预处理脚本

用法:
  python preprocess.py "HK.800700"
  python preprocess.py "US.SPY"

自动获取 80根5分钟 + 25根日线，输出富化 JSON:
  EMA20, bar类型, pattern, micro channel, ADR, gap, session
"""
import json
import sys
import os
import socket
import logging
from datetime import datetime, timedelta

logging.disable(logging.CRITICAL)

# ============================================================
# 市场配置
# ============================================================

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
# Bar 分类
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

        b["bar_type"] = _classify_single_bar(b, bar_range, body, baseline_body, upper_tail, lower_tail, close_pct)


def _classify_single_bar(b, bar_range, body, baseline_body, upper_tail, lower_tail, close_pct):
    if bar_range == 0:
        return "doji"

    if b["is_inside"]:
        return "inside"
    if b["is_outside"]:
        return "outside"

    # Doji: body ≤ 0.3× baseline, neither tail > 2× body
    if baseline_body > 0 and body <= 0.3 * baseline_body:
        if body == 0 or (upper_tail <= 2 * body and lower_tail <= 2 * body):
            return "doji"

    # Bull reversal: close in upper 25%, lower tail ≥ 50%
    if close_pct >= 75 and lower_tail >= 0.5 * bar_range:
        return "bull_reversal"

    # Bear reversal: close in lower 25%, upper tail ≥ 50%
    if close_pct <= 25 and upper_tail >= 0.5 * bar_range:
        return "bear_reversal"

    # Breakout: large body, close in extreme 10%, small tails
    if baseline_body > 0 and body >= 1.5 * baseline_body:
        if upper_tail < 0.25 * bar_range and lower_tail < 0.25 * bar_range:
            if close_pct >= 90:
                return "bull_breakout"
            if close_pct <= 10:
                return "bear_breakout"

    # Trading range bar: both tails ≥ 33%, close in middle 50%
    if (upper_tail >= 0.33 * bar_range and lower_tail >= 0.33 * bar_range
            and 25 <= close_pct <= 75):
        return "tr_bar"

    if b["close"] >= b["open"]:
        return "bull"
    return "bear"


# ============================================================
# Pattern 检测
# ============================================================

def detect_patterns(bars, baseline_body):
    patterns = []
    n = len(bars)
    if n < 3:
        return patterns

    # OO: two consecutive outside bars
    for i in range(1, n):
        if bars[i]["is_outside"] and bars[i - 1]["is_outside"]:
            patterns.append({"type": "oo_breakout", "bars": [i - 1, i]})

    # ioi: inside → outside → inside
    for i in range(2, n):
        if bars[i - 2]["is_inside"] and bars[i - 1]["is_outside"] and bars[i]["is_inside"]:
            patterns.append({"type": "ioi", "bars": [i - 2, i - 1, i]})

    # Bull/Bear Surprise: 2-3 consecutive trend bars, extreme close, minimal overlap, large body
    for length in (3, 2):
        for i in range(length - 1, n):
            start = i - length + 1
            chunk = bars[start:i + 1]
            if baseline_body <= 0:
                break
            all_bull = all(b["close"] > b["open"] and b["close_pct"] >= 75
                          and b["body"] >= baseline_body for b in chunk)
            all_bear = all(b["close"] < b["open"] and b["close_pct"] <= 25
                          and b["body"] >= baseline_body for b in chunk)
            if not (all_bull or all_bear):
                continue
            minimal_overlap = True
            for j in range(1, len(chunk)):
                if all_bull and chunk[j]["low"] > chunk[j - 1]["close"]:
                    pass
                elif all_bear and chunk[j]["high"] < chunk[j - 1]["close"]:
                    pass
                elif all_bull and chunk[j]["low"] <= chunk[j - 1]["high"]:
                    overlap = min(chunk[j]["high"], chunk[j - 1]["high"]) - max(chunk[j]["low"], chunk[j - 1]["low"])
                    if overlap > 0.5 * max(chunk[j]["body"], chunk[j - 1]["body"]):
                        minimal_overlap = False
                elif all_bear and chunk[j]["high"] >= chunk[j - 1]["low"]:
                    overlap = min(chunk[j]["high"], chunk[j - 1]["high"]) - max(chunk[j]["low"], chunk[j - 1]["low"])
                    if overlap > 0.5 * max(chunk[j]["body"], chunk[j - 1]["body"]):
                        minimal_overlap = False
            if minimal_overlap:
                direction = "bull_surprise" if all_bull else "bear_surprise"
                idx_list = list(range(start, i + 1))
                if not any(p["type"] == direction and set(p["bars"]) & set(idx_list) for p in patterns):
                    patterns.append({"type": direction, "bars": idx_list})

    # Micro Double Top/Bottom: two bars within 2-4 bars test same high/low (within 0.1%)
    # Only scan last 10 bars and deduplicate by level proximity
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

    # Deduplicate: keep only the most recent pair for each distinct level cluster
    for group in (raw_dt, raw_db):
        kept = []
        for p in reversed(group):
            if not any(abs(p["level"] - k["level"]) / max(p["level"], 1) < 0.002 for k in kept):
                kept.append(p)
            if len(kept) >= 3:
                break
        patterns.extend(reversed(kept))

    return patterns


# ============================================================
# Micro Channel 检测
# ============================================================

def detect_micro_channel(bars):
    n = len(bars)
    if n < 3:
        return {"active": False}

    best = {"active": False}

    # Scan from end backwards for the most recent channel
    for start in range(max(0, n - 20), n - 2):
        direction = None
        length = 0

        for i in range(start + 1, n):
            if bars[i]["high"] > bars[i - 1]["high"] and bars[i]["low"] >= bars[i - 1]["low"]:
                if direction is None:
                    direction = "bull"
                if direction == "bull":
                    length += 1
                else:
                    break
            elif bars[i]["low"] < bars[i - 1]["low"] and bars[i]["high"] <= bars[i - 1]["high"]:
                if direction is None:
                    direction = "bear"
                if direction == "bear":
                    length += 1
                else:
                    break
            else:
                break

        if length >= 3 and direction is not None:
            end_idx = start + length
            if end_idx == n - 1:
                best = {
                    "active": True,
                    "direction": direction,
                    "start_idx": start,
                    "length": length + 1,
                }

    if not best["active"]:
        # Relaxed check: consecutive higher-highs or lower-lows (allowing 1 exception)
        for look_back in range(min(15, n), 2, -1):
            start = n - look_back
            higher = sum(1 for i in range(start + 1, n) if bars[i]["high"] > bars[i - 1]["high"])
            lower = sum(1 for i in range(start + 1, n) if bars[i]["low"] < bars[i - 1]["low"])
            total = look_back - 1
            if higher >= total * 0.75:
                best = {"active": True, "direction": "bull", "start_idx": start, "length": look_back}
                break
            if lower >= total * 0.75:
                best = {"active": True, "direction": "bear", "start_idx": start, "length": look_back}
                break

    return best


# ============================================================
# Session 检测
# ============================================================

def detect_session(market, bars_today_count):
    cfg = MARKET_CONFIG.get(market, MARKET_CONFIG["US"])
    now = datetime.now()

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
# 主处理流程
# ============================================================

def process(code):
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

    # --- Daily processing ---
    daily_closes = [b["close"] for b in bars_daily]
    daily_ema20 = calc_ema(daily_closes, 20) if len(daily_closes) >= 1 else []

    daily_ranges = [b["high"] - b["low"] for b in bars_daily]
    adr = round(sum(daily_ranges[-20:]) / len(daily_ranges[-20:]), 4) if daily_ranges else 0

    prior_day = None
    daily_baseline = 0
    if len(bars_daily) >= 2:
        d = bars_daily[-2]
        daily_baseline = sum(abs(b["close"] - b["open"]) for b in bars_daily[-22:-2]) / max(1, len(bars_daily[-22:-2])) if len(bars_daily) > 2 else abs(d["close"] - d["open"])
        classify_bars([d], daily_baseline)
        prior_day = {
            "high": d["high"], "low": d["low"], "close": d["close"],
            "open": d["open"], "bar_type": d.get("bar_type", ""),
        }

    # Gap: today's first 5m open vs prior day close
    gap = {"size": 0, "pct_of_adr": 0}
    if bars_5m and prior_day:
        today_bars = _get_today_bars(bars_5m)
        if today_bars:
            gap_size = round(today_bars[0]["open"] - prior_day["close"], 4)
            gap["size"] = gap_size
            gap["pct_of_adr"] = round(gap_size / adr * 100, 2) if adr > 0 else 0

    daily_section = {
        "ema20": round(daily_ema20[-1], 4) if daily_ema20 else None,
        "adr": adr,
        "prior_day": prior_day,
        "gap": gap,
    }

    # --- Intraday processing ---
    today_bars = _get_today_bars(bars_5m)
    work_bars = today_bars if len(today_bars) >= 3 else bars_5m[-30:] if bars_5m else []

    closes_5m = [b["close"] for b in bars_5m]
    ema20_5m = calc_ema(closes_5m, 20) if len(closes_5m) >= 1 else []

    recent_bodies = [abs(b["close"] - b["open"]) for b in bars_5m[-20:]] if bars_5m else []
    baseline_body = round(sum(recent_bodies) / len(recent_bodies), 4) if recent_bodies else 0

    classify_bars(bars_5m, baseline_body)

    # Attach EMA20 to each bar
    for i, b in enumerate(bars_5m):
        b["ema20"] = round(ema20_5m[i], 4) if i < len(ema20_5m) else None

    # Today's range
    if today_bars:
        today_high = max(b["high"] for b in today_bars)
        today_low = min(b["low"] for b in today_bars)
    else:
        today_high = today_low = 0
    today_range_val = today_high - today_low
    adr_consumed_pct = round(today_range_val / adr * 100, 2) if adr > 0 else 0

    # Patterns (scan last 20 bars)
    scan_bars = bars_5m[-20:] if len(bars_5m) >= 20 else bars_5m
    patterns = detect_patterns(scan_bars, baseline_body)
    # Remap pattern bar indices to global indices
    offset = len(bars_5m) - len(scan_bars)
    for p in patterns:
        p["bars"] = [idx + offset for idx in p["bars"]]
        if "level" in p:
            p["level"] = round(p["level"], 4)

    micro_ch = detect_micro_channel(bars_5m[-20:] if len(bars_5m) >= 20 else bars_5m)
    if micro_ch.get("active") and "start_idx" in micro_ch:
        micro_ch["start_idx"] += offset

    # Build enriched bar output (last 80 bars with all computed fields)
    enriched_bars = []
    for i, b in enumerate(bars_5m):
        enriched_bars.append({
            "idx": i,
            "time": b["time"],
            "o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"],
            "volume": b["volume"],
            "ema20": b.get("ema20"),
            "body": b["body"],
            "body_strength": b.get("body_strength", "normal"),
            "bar_type": b.get("bar_type", ""),
            "upper_tail": b["upper_tail"],
            "lower_tail": b["lower_tail"],
            "close_pct": b["close_pct"],
            "is_inside": b["is_inside"],
            "is_outside": b["is_outside"],
        })

    session = detect_session(market, len(today_bars))

    return {
        "code": code,
        "market": market,
        "session": session,
        "daily": daily_section,
        "intraday": {
            "baseline_body": baseline_body,
            "ema20_current": round(ema20_5m[-1], 4) if ema20_5m else None,
            "today_range": {"high": round(today_high, 4), "low": round(today_low, 4)},
            "adr_consumed_pct": adr_consumed_pct,
            "micro_channel": micro_ch,
            "patterns": patterns,
            "bars": enriched_bars,
        },
    }


def _get_today_bars(bars):
    if not bars:
        return []
    today_str = datetime.now().strftime("%Y-%m-%d")
    return [b for b in bars if b["time"].startswith(today_str)]


# ============================================================
# 入口
# ============================================================

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "用法: preprocess.py CODE"}, ensure_ascii=False))
        sys.exit(1)

    code = sys.argv[1]
    result = process(code)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    main()
