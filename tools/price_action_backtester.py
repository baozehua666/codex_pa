#!/usr/bin/env python3
"""Reusable Al Brooks price-action backtester with an HTML report."""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from preprocess import (  # noqa: E402
    MARKET_CONFIG,
    calc_ema,
    classify_bars,
    detect_micro_channel,
    detect_patterns,
    detect_three_pushes,
    find_swing_points,
    infer_market,
)

TICK = 0.01


@dataclass
class PendingOrder:
    direction: str
    order_type: str
    signal_time: str
    signal_day_idx: int
    entry: float
    stop: float
    target: float
    risk: float
    structure: str
    confidence: str
    reason: str
    veto_line: str
    expires_day_idx: int


@dataclass
class Position:
    direction: str
    entry_time: str
    entry_day_idx: int
    entry: float
    initial_stop: float
    stop: float
    target: float
    risk: float
    structure: str
    confidence: str
    reason: str
    veto_line: str
    signal_time: str
    partial_taken: bool = False
    realized_r: float = 0.0
    size_left: float = 1.0


@dataclass
class Trade:
    date: str
    direction: str
    signal_time: str
    entry_time: str
    exit_time: str
    entry: float
    initial_stop: float
    target: float
    exit: float
    r: float
    outcome: str
    partial_taken: bool
    structure: str
    confidence: str
    reason: str
    veto_line: str


def parse_args():
    parser = argparse.ArgumentParser(
        description="Price-action time-forward backtester",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python tools/price_action_backtester.py --code US.SPY --start 2026-05-18 --end 2026-05-22
  python tools/price_action_backtester.py --code HK.800000 --start 2026-05-18 --end 2026-05-22 --refresh
  python tools/price_action_backtester.py --code US.QQQ --start 2026-05-01 --end 2026-05-22 --output reports/qqq.html
""",
    )
    parser.add_argument("--code", default="US.SPY", help="Futu code, e.g. US.SPY, HK.800000")
    parser.add_argument("--start", default="2026-05-18", help="Backtest start date YYYY-MM-DD")
    parser.add_argument("--end", default="2026-05-22", help="Backtest end date YYYY-MM-DD")
    parser.add_argument("--data-start", default=None, help="5m context start date; default start-10 calendar days")
    parser.add_argument("--daily-start", default=None, help="Daily context start date; default start-60 calendar days")
    parser.add_argument("--output", default=None, help="HTML output path")
    parser.add_argument("--cache-dir", default="backtest_cache", help="K-line cache directory")
    parser.add_argument("--refresh", action="store_true", help="Ignore cache and fetch from Futu OpenD")
    parser.add_argument("--host", default=os.getenv("FUTU_OPEND_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("FUTU_OPEND_PORT", "11111")))
    return parser.parse_args()


def date_range(start, end):
    cur = datetime.strptime(start, "%Y-%m-%d").date()
    last = datetime.strptime(end, "%Y-%m-%d").date()
    while cur <= last:
        if cur.weekday() < 5:
            yield cur.isoformat()
        cur += timedelta(days=1)


def default_context_start(date_str, days):
    d = datetime.strptime(date_str, "%Y-%m-%d").date() - timedelta(days=days)
    return d.isoformat()


def load_or_fetch(args):
    data_start = args.data_start or default_context_start(args.start, 10)
    daily_start = args.daily_start or default_context_start(args.start, 60)
    cache_dir = ROOT / args.cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)

    safe_code = args.code.replace(".", "_")
    daily_file = cache_dir / f"{safe_code}_daily_{daily_start}_{args.end}.json"
    five_file = cache_dir / f"{safe_code}_5m_{data_start}_{args.end}.json"

    if not args.refresh and daily_file.exists() and five_file.exists():
        daily = json.loads(daily_file.read_text(encoding="utf-8"))["data"]
        five = json.loads(five_file.read_text(encoding="utf-8"))["data"]
        return daily, five, {"source": "cache", "daily_file": str(daily_file), "five_file": str(five_file)}

    daily, five = fetch_history(args.code, daily_start, data_start, args.end, args.host, args.port)
    daily_file.write_text(json.dumps({"code": args.code, "data": daily}, ensure_ascii=False), encoding="utf-8")
    five_file.write_text(json.dumps({"code": args.code, "data": five}, ensure_ascii=False), encoding="utf-8")
    return daily, five, {"source": "futu", "daily_file": str(daily_file), "five_file": str(five_file)}


def fetch_history(code, daily_start, five_start, end, host, port):
    from futu import AuType, KLType, OpenQuoteContext, RET_OK
    import pandas as pd

    ctx = OpenQuoteContext(host=host, port=port)
    try:
        daily_df = fetch_klines(ctx, code, daily_start, end, KLType.K_DAY, AuType.QFQ, RET_OK, pd)
        five_df = fetch_klines(ctx, code, five_start, end, KLType.K_5M, AuType.QFQ, RET_OK, pd)
    finally:
        ctx.close()
    return rows_from_df(daily_df), rows_from_df(five_df)


def fetch_klines(ctx, code, start, end, ktype, autype, ret_ok, pd):
    chunks = []
    page_key = None
    first = True
    while first or page_key is not None:
        first = False
        ret, data, page_key = ctx.request_history_kline(
            code,
            start=start,
            end=end,
            ktype=ktype,
            autype=autype,
            max_count=1000,
            page_req_key=page_key,
        )
        if ret != ret_ok:
            raise RuntimeError(f"Futu request failed for {code} {ktype}: {data}")
        chunks.append(data)
    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()


def rows_from_df(df):
    rows = []
    for i in range(len(df)):
        r = df.iloc[i]
        rows.append(
            {
                "time": str(r.get("time_key", "")),
                "open": float(r.get("open", 0)),
                "high": float(r.get("high", 0)),
                "low": float(r.get("low", 0)),
                "close": float(r.get("close", 0)),
                "volume": int(r.get("volume", 0)),
                "turnover": float(r.get("turnover", 0)),
            }
        )
    return rows


def bars_for_date(bars, date):
    return [b for b in bars if b["time"].startswith(date)]


def bars_before_date(bars, date):
    return [b for b in bars if b["time"][:10] < date]


def process_snapshot(code, daily, five, date, bar_limit):
    today_raw = bars_for_date(five, date)[:bar_limit]
    if not today_raw:
        return None

    market = infer_market(code)
    prior_daily = [d for d in daily if d["time"][:10] < date]
    if len(prior_daily) < 20:
        return None

    prior_5m = bars_before_date(five, date)
    work = [dict(b) for b in (prior_5m[-80:] + today_raw)[-80:]]
    today_start = len(work) - len(today_raw)

    daily_closes = [d["close"] for d in prior_daily]
    daily_ema = calc_ema(daily_closes, 20)
    daily_ranges = [d["high"] - d["low"] for d in prior_daily]
    adr = round(sum(daily_ranges[-20:]) / 20, 4)
    prior_day = prior_daily[-1]
    gap_size = round(today_raw[0]["open"] - prior_day["close"], 4)
    gap_pct = round(gap_size / adr * 100, 2) if adr else 0
    abs_gap = abs(gap_pct)
    gap_class = "large" if abs_gap > 50 else "medium" if abs_gap > 25 else "small" if abs_gap > 5 else "none"

    closes = [b["close"] for b in work]
    ema = calc_ema(closes, 20)
    baseline = round(sum(abs(b["close"] - b["open"]) for b in work[-20:]) / min(20, len(work)), 4)
    classify_bars(work, baseline)
    for i, b in enumerate(work):
        b["ema20"] = round(ema[i], 4)

    today = work[today_start:]
    today_high = max(b["high"] for b in today)
    today_low = min(b["low"] for b in today)
    day_range = max(today_high - today_low, TICK)
    adr_consumed = round(day_range / adr * 100, 2) if adr else 0

    def opening_range(first_n):
        if len(today) < first_n:
            return {"complete": False}
        chunk = today[:first_n]
        hi = max(b["high"] for b in chunk)
        lo = min(b["low"] for b in chunk)
        width = hi - lo
        close = work[-1]["close"]
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

    ema_crosses = 0
    for i in range(today_start + 1, len(work)):
        if (work[i - 1]["close"] > work[i - 1]["ema20"]) != (work[i]["close"] > work[i]["ema20"]):
            ema_crosses += 1
    ema_slope = round((ema[-1] - ema[-5]) / max(abs(ema[-5]), 1) * 100, 4) if len(ema) >= 5 else 0
    ema_distance_pct = round((work[-1]["close"] - ema[-1]) / adr * 100, 2) if adr else 0

    pattern_source = today[-20:]
    scan_offset = today_start + len(today) - len(pattern_source)
    patterns = detect_patterns(pattern_source, baseline)
    for p in patterns:
        p["bars"] = [idx + scan_offset for idx in p["bars"]]

    micro_source = today[-20:]
    micro = detect_micro_channel(micro_source) if len(micro_source) >= 3 else {"active": False}
    if micro.get("active") and "start_idx" in micro:
        micro["start_idx"] += today_start + len(today) - len(micro_source)

    swing_slice = today if len(today) >= 5 else work[-30:]
    swing_offset = today_start if len(today) >= 5 else len(work) - min(30, len(work))
    swing_highs, swing_lows = find_swing_points(swing_slice)
    swing_points = {
        "highs": [{"idx": idx + swing_offset, "level": round(v, 4)} for idx, v in swing_highs],
        "lows": [{"idx": idx + swing_offset, "level": round(v, 4)} for idx, v in swing_lows],
    }
    three_pushes = detect_three_pushes(today) if len(today) >= 10 else []

    bull = sum(1 for b in today if "bull" in b.get("bar_type", ""))
    bear = sum(1 for b in today if "bear" in b.get("bar_type", ""))
    neutral = len(today) - bull - bear
    total_dir = bull + bear
    bias = "balanced"
    if total_dir:
        bull_pct = bull / total_dir
        bias = "bull" if bull_pct > 0.6 else "bear" if bull_pct < 0.4 else "balanced"

    bars = [
        {
            "idx": i,
            "day_idx": i - today_start + 1 if i >= today_start else None,
            "time": b["time"],
            "o": b["open"],
            "h": b["high"],
            "l": b["low"],
            "c": b["close"],
            "volume": b["volume"],
            "body": b["body"],
            "body_strength": b["body_strength"],
            "bar_type": b["bar_type"],
            "upper_tail": b["upper_tail"],
            "lower_tail": b["lower_tail"],
            "close_pct": b["close_pct"],
            "is_inside": b["is_inside"],
            "is_outside": b["is_outside"],
            "ema20": b["ema20"],
        }
        for i, b in enumerate(work)
    ]

    return {
        "code": code,
        "market": market,
        "target_date": date,
        "session": {
            "current_period": period_for_time(work[-1]["time"], market),
            "bars_today": len(today),
            "minutes_to_close": minutes_to_close(work[-1]["time"], market),
            "is_lunch": period_for_time(work[-1]["time"], market) == "lunch",
        },
        "daily": {
            "ema20": round(daily_ema[-1], 4),
            "adr": adr,
            "prior_day": {
                "date": prior_day["time"][:10],
                "open": prior_day["open"],
                "high": prior_day["high"],
                "low": prior_day["low"],
                "close": prior_day["close"],
            },
            "gap": {"size": gap_size, "pct_of_adr": gap_pct, "classification": gap_class},
        },
        "intraday": {
            "baseline_body": baseline,
            "ema20_current": round(ema[-1], 4),
            "ema20_slope": ema_slope,
            "ema20_distance_pct": ema_distance_pct,
            "ema_crosses_today": ema_crosses,
            "today_range": {"high": round(today_high, 4), "low": round(today_low, 4)},
            "range_position": round((work[-1]["close"] - today_low) / day_range, 3),
            "opening_range": {
                "first_30m": opening_range(6),
                "first_90m": opening_range(18),
            },
            "adr_consumed_pct": adr_consumed,
            "bar_balance": {"bull": bull, "bear": bear, "neutral": neutral, "bias": bias},
            "bar_stats": {
                "inside_count": sum(1 for b in today if b.get("is_inside")),
                "outside_count": sum(1 for b in today if b.get("is_outside")),
                "outside_pct": round(sum(1 for b in today if b.get("is_outside")) / len(today) * 100, 1),
            },
            "micro_channel": micro,
            "patterns": patterns,
            "three_pushes": three_pushes,
            "swing_points": swing_points,
            "bars": bars,
            "today_start_idx": today_start,
        },
    }


def period_for_time(time_key, market="US"):
    hhmm = time_key[11:16]
    config = MARKET_CONFIG.get(market, MARKET_CONFIG["US"])
    for name, start, end in config["periods"]:
        if start <= hhmm < end:
            return name
    return "closed"


def minutes_to_close(time_key, market="US"):
    dt = datetime.strptime(time_key, "%Y-%m-%d %H:%M:%S")
    close_hhmm = MARKET_CONFIG.get(market, MARKET_CONFIG["US"])["close"]
    hour, minute = [int(part) for part in close_hhmm.split(":")]
    close = dt.replace(hour=hour, minute=minute, second=0)
    return max(0, int((close - dt).total_seconds() // 60))


def opening_label(snap, key):
    info = snap["intraday"].get("opening_range", {}).get(key, {})
    if not info.get("complete"):
        return "未形成"
    pos = info.get("position")
    state = {"above": "上方", "below": "下方", "inside": "内部"}.get(info.get("state"), info.get("state", ""))
    return f"{state} {pos:.2f}" if pos is not None else state


def analyze_snapshot(snap):
    bars = snap["intraday"]["bars"]
    cur = bars[-1]
    n = snap["session"]["bars_today"]
    if n < 3:
        return watch(snap, "数据不足", "N0✗", "今日少于3根5分钟K线")
    if snap["session"]["is_lunch"]:
        return watch(snap, "午休", "N0✗", "午休时段不产生入场信号")

    structure, structure_reason = classify_structure(snap)
    if structure == "不明确":
        return watch(snap, "结构不明", "N1✗", structure_reason)

    direction, direction_reason = always_in_direction(snap)
    if direction == "none":
        return watch(snap, structure, "N4✗", direction_reason)

    signal = signal_for_direction(snap, direction, structure)
    vetoes = score_vetoes(snap, structure, direction, signal)
    score = sum(v[1] for v in vetoes)
    veto_line = format_veto(vetoes, score)
    if score >= 5:
        return watch(snap, structure, "V✗", "否决分数达到强烈观望", veto_line, direction)
    if score >= 3:
        return watch(snap, structure, "V✗", "否决分数达到观望", veto_line, direction)

    if not signal["valid"]:
        return watch(snap, structure, "S2✗", signal["reason"], veto_line, direction)
    if not trapped_fuel(snap, direction, structure, signal):
        return watch(snap, structure, "S1✗", "被套交易者燃料不足", veto_line, direction)

    order = build_order(snap, structure, direction, signal, veto_line, score)
    if not order:
        return watch(snap, structure, "R1✗", "盈亏比或止损条件不足", veto_line, direction)

    confidence = "中" if score == 0 else "弱"
    order.confidence = confidence
    return {
        "time": cur["time"],
        "close": cur["c"],
        "structure": structure,
        "direction": "做多" if direction == "long" else "做空",
        "advice": "做多" if direction == "long" else "做空",
        "confidence": confidence,
        "path": "N0✓ -> N1✓ -> N4✓ -> V✓ -> S✓ -> R✓",
        "reason": signal["reason"],
        "veto_line": veto_line,
        "order": order,
        "bar_type": cur["bar_type"],
        "adr": snap["intraday"]["adr_consumed_pct"],
        "range_position": snap["intraday"]["range_position"],
        "opening_30m": opening_label(snap, "first_30m"),
        "opening_90m": opening_label(snap, "first_90m"),
    }


def classify_structure(snap):
    intr = snap["intraday"]
    bars = intr["bars"]
    today = bars[intr["today_start_idx"] :]
    cur = bars[-1]
    n = len(today)
    if n < 5:
        return "不明确", "开盘前几根K线，结构还没有形成"

    prev = today[:-2]
    if len(prev) >= 15:
        range_high = max(b["h"] for b in prev)
        range_low = min(b["l"] for b in prev)
        last2 = today[-2:]
        bull_break = all(b["bar_type"] in ("bull_breakout", "bull") and b["c"] > b["o"] for b in last2)
        bear_break = all(b["bar_type"] in ("bear_breakout", "bear") and b["c"] < b["o"] for b in last2)
        if bull_break and cur["c"] > range_high:
            return "震荡突破", "区间上沿被连续趋势K线突破"
        if bear_break and cur["c"] < range_low:
            return "震荡突破", "区间下沿被连续趋势K线突破"

    micro = intr["micro_channel"]
    balance = intr["bar_balance"]["bias"]
    outside_pct = intr["bar_stats"]["outside_pct"]
    ema_crosses = intr["ema_crosses_today"]
    slope = intr["ema20_slope"]

    sustained = False
    if micro.get("active") and micro.get("length", 0) >= 4:
        sustained = True
    if abs(slope) >= 0.03 and ema_crosses <= 2 and balance in ("bull", "bear"):
        sustained = True
    if len(today) >= 3:
        last3 = today[-3:]
        above = all(b["c"] > b["ema20"] for b in last3)
        below = all(b["c"] < b["ema20"] for b in last3)
        if (above or below) and balance in ("bull", "bear"):
            sustained = True

    if not sustained or outside_pct > 18 or (ema_crosses >= 5 and n >= 15):
        return "震荡区间", "重叠/外包或均线反复穿越，限价单市场特征"
    if micro.get("active") and micro.get("length", 0) >= 5 and ema_crosses <= 1:
        return "突破/窄通道", "微通道延续且均线穿越少"
    return "宽通道", "有方向但回撤和重叠仍较多"


def always_in_direction(snap):
    intr = snap["intraday"]
    bars = intr["bars"]
    today = bars[intr["today_start_idx"] :]
    cur = today[-1]
    score = 0
    reasons = []

    for b in reversed(today[-8:]):
        if b["bar_type"] == "bull_breakout":
            score += 2
            reasons.append("最近强多头突破")
            break
        if b["bar_type"] == "bear_breakout":
            score -= 2
            reasons.append("最近强空头突破")
            break

    micro = intr["micro_channel"]
    if micro.get("active"):
        if micro.get("direction") == "bull":
            score += 1
            reasons.append("多头微通道")
        else:
            score -= 1
            reasons.append("空头微通道")

    if intr["ema_crosses_today"] < 5 and abs(intr["ema20_slope"]) >= 0.01:
        if cur["c"] > intr["ema20_current"]:
            score += 1
            reasons.append("价格在均线上方")
        elif cur["c"] < intr["ema20_current"]:
            score -= 1
            reasons.append("价格在均线下方")

    bias = intr["bar_balance"]["bias"]
    if bias == "bull":
        score += 1
        reasons.append("多头K线占优")
    elif bias == "bear":
        score -= 1
        reasons.append("空头K线占优")

    if score >= 2:
        return "long", "、".join(reasons)
    if score <= -2:
        return "short", "、".join(reasons)
    return "none", "持仓方向证据不足或互相冲突"


def signal_for_direction(snap, direction, structure):
    intr = snap["intraday"]
    bars = intr["bars"]
    cur = bars[-1]
    pos = intr["range_position"]
    recent_patterns = [p for p in intr["patterns"] if max(p["bars"]) >= cur["idx"] - 1]
    pattern_types = {p["type"] for p in recent_patterns}

    at_long_area = pos <= 0.40 if structure == "震荡区间" else pos <= 0.82
    at_short_area = pos >= 0.60 if structure == "震荡区间" else pos >= 0.18

    bull_confirm = cur["c"] > cur["o"] and cur["close_pct"] >= 60
    bear_confirm = cur["c"] < cur["o"] and cur["close_pct"] <= 40

    if direction == "long":
        if structure == "震荡区间" and not at_long_area:
            return {"valid": False, "reason": "震荡区间未在下沿，不追多"}
        if cur["bar_type"] in ("bull_reversal", "bull_breakout") and bull_confirm:
            return {"valid": True, "reason": f"{cur['bar_type']} 信号K线"}
        if ("micro_double_bottom" in pattern_types or "bull_surprise" in pattern_types) and bull_confirm:
            return {"valid": True, "reason": "微型双底/多头意外强势并收阳确认"}
        if structure != "震荡区间" and bull_confirm and cur["l"] <= cur["ema20"] <= cur["h"]:
            return {"valid": True, "reason": "回撤均线后收阳"}
    else:
        if structure == "震荡区间" and not at_short_area:
            return {"valid": False, "reason": "震荡区间未在上沿，不追空"}
        if cur["bar_type"] in ("bear_reversal", "bear_breakout") and bear_confirm:
            return {"valid": True, "reason": f"{cur['bar_type']} 信号K线"}
        if ("micro_double_top" in pattern_types or "bear_surprise" in pattern_types) and bear_confirm:
            return {"valid": True, "reason": "微型双顶/空头意外强势并收阴确认"}
        if structure != "震荡区间" and bear_confirm and cur["l"] <= cur["ema20"] <= cur["h"]:
            return {"valid": True, "reason": "回撤均线后收阴"}

    return {"valid": False, "reason": "当前K线缺少方向确认"}


def trapped_fuel(snap, direction, structure, signal):
    intr = snap["intraday"]
    bars = intr["bars"]
    cur = bars[-1]
    pos = intr["range_position"]
    recent = bars[-8:]

    if structure == "震荡区间":
        if direction == "long" and pos <= 0.40 and ("双底" in signal["reason"] or cur["bar_type"] == "bull_reversal"):
            return True
        if direction == "short" and pos >= 0.60 and ("双顶" in signal["reason"] or cur["bar_type"] == "bear_reversal"):
            return True
        return False

    if any(b["bar_type"] == ("bull_breakout" if direction == "long" else "bear_breakout") for b in recent):
        return True
    micro = intr["micro_channel"]
    if micro.get("active") and ((direction == "long" and micro.get("direction") == "bull") or (direction == "short" and micro.get("direction") == "bear")):
        return True
    if "意外强势" in signal["reason"]:
        return True
    return False


def score_vetoes(snap, structure, direction, signal):
    intr = snap["intraday"]
    bars = intr["bars"]
    cur = bars[-1]
    today = bars[intr["today_start_idx"] :]
    pos = intr["range_position"]
    reason = signal.get("reason", "")
    vetoes = []

    if structure == "突破/窄通道":
        micro_dir = intr["micro_channel"].get("direction")
        if (direction == "long" and micro_dir == "bear") or (direction == "short" and micro_dir == "bull"):
            vetoes.append(("V1", 5, "逆窄通道"))

    if structure == "震荡区间":
        if direction == "long" and pos > 0.40:
            vetoes.append(("V2", 5, "区间中部"))
        if direction == "short" and pos < 0.60:
            vetoes.append(("V2", 5, "区间中部"))

    if structure == "宽通道":
        if direction == "long" and pos > 0.70:
            vetoes.append(("V3", 3, "宽通道买在高位"))
        if direction == "short" and pos < 0.40:
            vetoes.append(("V3", 3, "宽通道卖在低位"))
        if signal.get("valid"):
            if direction == "long" and "微型双底" in reason and pos > 0.45:
                vetoes.append(("V14", 3, "宽通道非下沿微型双底"))
            if direction == "short" and "微型双顶" in reason and pos < 0.55:
                vetoes.append(("V14", 3, "宽通道非上沿微型双顶"))
    else:
        if direction == "long" and pos > 0.82:
            vetoes.append(("V3", 3, "买在阻力"))
        if direction == "short" and pos < 0.18:
            vetoes.append(("V3", 3, "卖在支撑"))

    stop_dist = cur["h"] - cur["l"]
    if stop_dist > 0.30 * snap["daily"]["adr"]:
        vetoes.append(("V4", 3, "止损过大"))

    if cur["body_strength"] == "large" and signal["valid"] and "breakout" in cur["bar_type"]:
        vetoes.append(("V5", 3, "追大K线"))

    if signal.get("valid"):
        if "微型双" in reason and cur["bar_type"] == "tr_bar":
            vetoes.append(("V14", 3, "微型双信号是交易区间K线"))
        if "回撤均线" in reason and cur.get("is_outside"):
            vetoes.append(("V14", 3, "外包K线回撤信号"))

    micro = intr["micro_channel"]
    if micro.get("active"):
        if (direction == "long" and micro.get("direction") == "bear") or (direction == "short" and micro.get("direction") == "bull"):
            vetoes.append(("V6", 3, "微通道首次反转"))
        if micro.get("length", 0) >= 9 and ((direction == "long" and micro.get("direction") == "bull") or (direction == "short" and micro.get("direction") == "bear")):
            vetoes.append(("V11", 1, "微通道过长"))

    if recent_three_push_complete(intr["three_pushes"], len(today)):
        vetoes.append(("V7", 2, "三推后第四段"))

    if abs(intr["ema20_distance_pct"]) > 30:
        if (direction == "long" and cur["c"] < intr["ema20_current"]) or (direction == "short" and cur["c"] > intr["ema20_current"]):
            vetoes.append(("V8", 3, "远离均线逆势"))

    adr_used = intr["adr_consumed_pct"]
    if adr_used > 100:
        vetoes.append(("V9", 3, "日振幅>100%"))
    elif adr_used > 90:
        vetoes.append(("V9", 2, "日振幅>90%"))
    elif adr_used > 80:
        vetoes.append(("V9", 1, "日振幅>80%"))

    if snap["session"]["current_period"] in ("opening", "closing"):
        vetoes.append(("V12", 1, "时段"))

    last2 = bars[-2:]
    if len(last2) == 2 and (all(b["bar_type"] == "bull_breakout" for b in last2) or all(b["bar_type"] == "bear_breakout" for b in last2)):
        vetoes.append(("V13", 2, "连续突破高潮"))

    return vetoes


def recent_three_push_complete(three_pushes, bars_today):
    for tp in three_pushes:
        pushes = tp.get("pushes") or []
        if not (tp.get("complete") and pushes):
            continue
        bars_since_last_push = bars_today - (pushes[-1] + 1)
        if 0 <= bars_since_last_push <= 8:
            return True
    return False


def build_order(snap, structure, direction, signal, veto_line, score):
    cur = snap["intraday"]["bars"][-1]
    adr = snap["daily"]["adr"]
    order_type = "market_next_open" if structure == "震荡区间" else "stop"

    if direction == "long":
        entry = cur["c"] if order_type == "market_next_open" else round(cur["h"] + TICK, 2)
        stop = round(cur["l"] - TICK, 2)
        risk = round(entry - stop, 4)
        magnets = [
            snap["intraday"]["today_range"]["high"],
            snap["daily"]["prior_day"]["high"],
            snap["intraday"]["ema20_current"],
            entry + 2 * risk,
        ]
        candidates = [m for m in magnets if m > entry + 1.5 * risk]
        target = round(min(candidates) if candidates else entry + 1.5 * risk, 2)
    else:
        entry = cur["c"] if order_type == "market_next_open" else round(cur["l"] - TICK, 2)
        stop = round(cur["h"] + TICK, 2)
        risk = round(stop - entry, 4)
        magnets = [
            snap["intraday"]["today_range"]["low"],
            snap["daily"]["prior_day"]["low"],
            snap["intraday"]["ema20_current"],
            entry - 2 * risk,
        ]
        candidates = [m for m in magnets if m < entry - 1.5 * risk]
        target = round(max(candidates) if candidates else entry - 1.5 * risk, 2)

    if risk <= 0 or risk > 0.30 * adr:
        return None
    if abs(target - entry) / risk < 1.49:
        return None

    return PendingOrder(
        direction=direction,
        order_type=order_type,
        signal_time=cur["time"],
        signal_day_idx=snap["session"]["bars_today"],
        entry=round(entry, 2),
        stop=round(stop, 2),
        target=round(target, 2),
        risk=round(risk, 4),
        structure=structure,
        confidence="中" if score == 0 else "弱",
        reason=signal["reason"],
        veto_line=veto_line,
        expires_day_idx=snap["session"]["bars_today"] + 3,
    )


def watch(snap, structure, path, reason, veto_line=None, direction="none"):
    cur = snap["intraday"]["bars"][-1]
    if veto_line is None:
        veto_line = "> 否决评分: 0分 -> 全部通过"
    return {
        "time": cur["time"],
        "close": cur["c"],
        "structure": structure,
        "direction": "不明确" if direction == "none" else "做多" if direction == "long" else "做空",
        "advice": "观望",
        "confidence": "弱",
        "path": path,
        "reason": reason,
        "veto_line": veto_line,
        "order": None,
        "bar_type": cur["bar_type"],
        "adr": snap["intraday"]["adr_consumed_pct"],
        "range_position": snap["intraday"].get("range_position", 0),
        "opening_30m": opening_label(snap, "first_30m"),
        "opening_90m": opening_label(snap, "first_90m"),
    }


def cooldown_watch(decision, cooldown_until):
    blocked = {**decision}
    blocked["advice"] = "观望"
    blocked["confidence"] = "弱"
    blocked["path"] = "M1✗"
    blocked["reason"] = f"止损后冷却，等待第{cooldown_until + 1}根K线后再评估"
    blocked["veto_line"] = "> 管理规则: 止损后两根K线内不反手 -> 观望"
    blocked["order"] = None
    return blocked


def format_veto(vetoes, score):
    if not vetoes:
        return "> 否决评分: 0分 -> 全部通过"
    parts = [f"{code}({reason})+{points}" for code, points, reason in vetoes]
    result = "强烈观望" if score >= 5 else "观望" if score >= 3 else "信心降级，继续评估"
    return f"> 否决评分: {', '.join(parts)} = {score}分 -> {result}"


def run_backtest(args, daily, five):
    dates = list(date_range(args.start, args.end))
    monitor = []
    trades = []
    day_stats = {}

    for date in dates:
        day_bars = bars_for_date(five, date)
        if not day_bars:
            continue
        day_stats[date] = {"bars": len(day_bars), "signals": 0, "trades": 0, "r": 0.0}
        pending = None
        position = None
        cooldown_until = 0

        for day_idx, _ in enumerate(day_bars, start=1):
            snap = process_snapshot(args.code, daily, five, date, day_idx)
            if not snap:
                continue
            cur = snap["intraday"]["bars"][-1]
            event = ""

            if pending:
                if day_idx > pending.expires_day_idx:
                    event = "挂单过期"
                    pending = None
                elif not position and day_idx > pending.signal_day_idx:
                    fill = fill_pending(pending, cur, day_idx)
                    if fill:
                        position = fill
                        event = f"入场 {position.direction} {position.entry:.2f}"
                        pending = None

            if position:
                exit_info = manage_position(position, cur, day_idx)
                if exit_info:
                    trade = make_trade(date, position, exit_info)
                    trades.append(trade)
                    day_stats[date]["trades"] += 1
                    day_stats[date]["r"] += trade.r
                    event = f"出场 {trade.outcome} {trade.r:.2f}R"
                    if "止损" in trade.outcome:
                        cooldown_until = day_idx + 2
                    position = None

            decision = analyze_snapshot(snap)
            if decision["order"] and not pending and not position:
                if day_idx <= cooldown_until:
                    decision = cooldown_watch(decision, cooldown_until)
                    event = event or "止损后冷却"
                else:
                    pending = decision["order"]
                    day_stats[date]["signals"] += 1
                    event = event or "发出挂单"
            monitor.append({**decision, "event": event, "date": date})

        if position:
            last = day_bars[-1]
            trade = make_trade(date, position, {"time": last["time"], "price": last["close"], "outcome": "收盘平仓"})
            trades.append(trade)
            day_stats[date]["trades"] += 1
            day_stats[date]["r"] += trade.r

    return monitor, trades, day_stats


def fill_pending(order, bar, day_idx):
    if order.order_type == "market_next_open":
        entry = bar["o"]
    elif order.direction == "long":
        if bar["h"] < order.entry:
            return None
        entry = max(order.entry, bar["o"]) if bar["o"] > order.entry else order.entry
    else:
        if bar["l"] > order.entry:
            return None
        entry = min(order.entry, bar["o"]) if bar["o"] < order.entry else order.entry

    if order.direction == "long":
        risk = entry - order.stop
        reward = order.target - entry
    else:
        risk = order.stop - entry
        reward = entry - order.target
    if risk <= 0:
        return None
    if risk > order.risk * 1.25:
        return None
    if reward <= 0 or reward / risk < 1.49:
        return None
    return Position(
        direction=order.direction,
        entry_time=bar["time"],
        entry_day_idx=day_idx,
        entry=round(entry, 2),
        initial_stop=order.stop,
        stop=order.stop,
        target=order.target,
        risk=round(risk, 4),
        structure=order.structure,
        confidence=order.confidence,
        reason=order.reason,
        veto_line=order.veto_line,
        signal_time=order.signal_time,
    )


def manage_position(pos, bar, day_idx):
    if pos.direction == "long":
        hit_stop = bar["l"] <= pos.stop
        hit_one_r = bar["h"] >= pos.entry + pos.risk
        hit_target = bar["h"] >= pos.target
        close_r = (bar["c"] - pos.entry) / pos.risk
    else:
        hit_stop = bar["h"] >= pos.stop
        hit_one_r = bar["l"] <= pos.entry - pos.risk
        hit_target = bar["l"] <= pos.target
        close_r = (pos.entry - bar["c"]) / pos.risk

    if hit_stop:
        stop_r = (pos.stop - pos.entry) / pos.risk if pos.direction == "long" else (pos.entry - pos.stop) / pos.risk
        total_r = pos.realized_r + pos.size_left * stop_r
        return {"time": bar["time"], "price": pos.stop, "outcome": "保本/止损" if pos.partial_taken else "止损", "r": total_r}

    if not pos.partial_taken and hit_one_r:
        pos.partial_taken = True
        pos.realized_r += 0.5
        pos.size_left = 0.5
        pos.stop = pos.entry

    if hit_target:
        target_r = abs(pos.target - pos.entry) / pos.risk
        total_r = pos.realized_r + pos.size_left * target_r
        return {"time": bar["time"], "price": pos.target, "outcome": "目标", "r": total_r}

    if pos.partial_taken:
        if pos.direction == "long" and bar["l"] <= pos.stop:
            return {"time": bar["time"], "price": pos.stop, "outcome": "保本", "r": pos.realized_r}
        if pos.direction == "short" and bar["h"] >= pos.stop:
            return {"time": bar["time"], "price": pos.stop, "outcome": "保本", "r": pos.realized_r}

    if bar["time"][11:16] >= "15:55":
        total_r = pos.realized_r + pos.size_left * close_r
        return {"time": bar["time"], "price": bar["c"], "outcome": "收盘平仓", "r": total_r}

    return None


def make_trade(date, pos, exit_info):
    return Trade(
        date=date,
        direction="做多" if pos.direction == "long" else "做空",
        signal_time=pos.signal_time,
        entry_time=pos.entry_time,
        exit_time=exit_info["time"],
        entry=round(pos.entry, 2),
        initial_stop=round(pos.initial_stop, 2),
        target=round(pos.target, 2),
        exit=round(exit_info["price"], 2),
        r=round(exit_info.get("r", 0.0), 2),
        outcome=exit_info["outcome"],
        partial_taken=pos.partial_taken,
        structure=pos.structure,
        confidence=pos.confidence,
        reason=pos.reason,
        veto_line=pos.veto_line,
    )


def render_html(args, metadata, daily, five, monitor, trades, day_stats, out_path):
    dates = list(day_stats)
    total_r = round(sum(t.r for t in trades), 2)
    wins = sum(1 for t in trades if t.r > 0)
    losses = sum(1 for t in trades if t.r < 0)
    win_rate = round(wins / len(trades) * 100, 1) if trades else 0
    max_dd = max_drawdown([t.r for t in trades])
    watch_count = sum(1 for r in monitor if r["advice"] == "观望")
    watch_pct = round(watch_count / len(monitor) * 100, 1) if monitor else 0

    trade_rows = "\n".join(
        f"<tr><td>{t.date}</td><td>{t.direction}</td><td>{t.signal_time[11:16]}</td><td>{t.entry_time[11:16]}</td>"
        f"<td>{t.exit_time[11:16]}</td><td>{t.entry:.2f}</td><td>{t.initial_stop:.2f}</td><td>{t.target:.2f}</td>"
        f"<td>{t.exit:.2f}</td><td>{'是' if t.partial_taken else '否'}</td><td class='{ 'win' if t.r > 0 else 'loss' if t.r < 0 else ''}'>{t.r:.2f}</td>"
        f"<td>{escape(t.outcome)}</td><td>{escape(t.structure)}</td><td>{escape(t.reason)}</td></tr>"
        for t in trades
    )

    day_sections = []
    for date in dates:
        rows = [r for r in monitor if r["date"] == date]
        day_trades = [t for t in trades if t.date == date]
        chart = render_day_svg(date, bars_for_date(five, date), day_trades)
        table_rows = "\n".join(
            f"<tr><td>{r['time'][11:16]}</td><td>{r['close']:.2f}</td><td>{escape(r['structure'])}</td><td>{escape(r['direction'])}</td>"
            f"<td>{escape(r['advice'])}</td><td>{escape(r['confidence'])}</td><td>{r['range_position']:.2f}</td><td>{r['adr']:.1f}%</td>"
            f"<td>{escape(r.get('opening_30m', ''))}</td><td>{escape(r.get('opening_90m', ''))}</td>"
            f"<td>{escape(r['bar_type'])}</td><td>{escape(r['reason'])}</td><td>{escape(r['veto_line'].replace('> ', ''))}</td><td>{escape(r['event'])}</td></tr>"
            for r in rows
        )
        day_sections.append(
            f"""
            <section>
              <h2>{date}</h2>
              <div class="day-grid">
                <div>{chart}</div>
                <div class="mini">
                  <p><b>Bars</b>: {day_stats[date]['bars']}</p>
                  <p><b>Signals</b>: {day_stats[date]['signals']}</p>
                  <p><b>Trades</b>: {day_stats[date]['trades']}</p>
                  <p><b>R</b>: {day_stats[date]['r']:.2f}</p>
                </div>
              </div>
              <details>
                <summary>实时监控记录 ({len(rows)} 条)</summary>
                <table>
                  <thead><tr><th>时间</th><th>收盘</th><th>结构</th><th>方向</th><th>建议</th><th>信心</th><th>区间位置</th><th>ADR</th><th>OR30</th><th>OR90</th><th>K线</th><th>原因</th><th>否决</th><th>事件</th></tr></thead>
                  <tbody>{table_rows}</tbody>
                </table>
              </details>
            </section>
            """
        )

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "code": args.code,
        "start": args.start,
        "end": args.end,
        "metadata": metadata,
        "summary": {
            "trades": len(trades),
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "total_r": total_r,
            "max_drawdown_r": max_dd,
            "watch_pct": watch_pct,
        },
        "trades": [asdict(t) for t in trades],
    }

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(args.code)} Price Action 回测报告</title>
  <style>
    body {{ margin: 0; font-family: Segoe UI, Arial, sans-serif; color: #202124; background: #f6f7f9; }}
    header {{ padding: 28px 36px; background: #111827; color: #fff; }}
    h1 {{ margin: 0 0 8px; font-size: 24px; }}
    main {{ padding: 24px 36px 48px; }}
    .cards {{ display: grid; grid-template-columns: repeat(6, minmax(120px, 1fr)); gap: 12px; margin-bottom: 18px; }}
    .card, section {{ background: #fff; border: 1px solid #d9dde5; border-radius: 8px; }}
    .card {{ padding: 14px; }}
    .label {{ color: #667085; font-size: 12px; }}
    .value {{ font-size: 22px; font-weight: 700; margin-top: 6px; }}
    section {{ padding: 18px; margin: 18px 0; }}
    .day-grid {{ display: grid; grid-template-columns: minmax(360px, 1fr) 180px; gap: 16px; align-items: start; }}
    .mini {{ background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 6px; padding: 10px 14px; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 12px; background: #fff; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 7px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f1f5f9; position: sticky; top: 0; }}
    details {{ margin-top: 12px; }}
    summary {{ cursor: pointer; color: #1f2937; font-weight: 600; }}
    .win {{ color: #047857; font-weight: 700; }}
    .loss {{ color: #b42318; font-weight: 700; }}
    .note {{ color: #475467; line-height: 1.55; }}
    svg {{ width: 100%; height: auto; background: #fbfdff; border: 1px solid #e5e7eb; border-radius: 6px; }}
  </style>
</head>
<body>
  <header>
    <h1>{escape(args.code)} Price Action 回测报告</h1>
    <div>区间：{escape(args.start)} 至 {escape(args.end)} · 数据源：{escape(metadata['source'])} · 模式：5分钟收盘后逐根模拟</div>
  </header>
  <main>
    <div class="cards">
      <div class="card"><div class="label">交易数</div><div class="value">{len(trades)}</div></div>
      <div class="card"><div class="label">胜率</div><div class="value">{win_rate}%</div></div>
      <div class="card"><div class="label">总R</div><div class="value">{total_r:.2f}</div></div>
      <div class="card"><div class="label">最大回撤R</div><div class="value">{max_dd:.2f}</div></div>
      <div class="card"><div class="label">观望比例</div><div class="value">{watch_pct}%</div></div>
      <div class="card"><div class="label">监控点</div><div class="value">{len(monitor)}</div></div>
    </div>
    <section>
      <h2>修正版规则</h2>
      <p class="note">震荡区间只在上下沿做反转，不在中部追突破；宽通道避免在高位追多或低位追空，非正确边缘的微型双顶/双底必须有清晰支撑阻力或放弃；TR bar 微型双和外包K线回撤不作为普通 stop entry；止损后至少冷却两根K线；微型双顶/双底和意外强势必须由当前K线方向确认；趋势/通道用顺势 stop entry；成交后按实际入场价重新校验风险和盈亏比；到 +1R 后半仓止盈并把剩余仓位止损移到保本；同根K线止损与目标同时出现时按保守顺序处理；不隔夜。</p>
    </section>
    <section>
      <h2>交易明细</h2>
      <table>
        <thead><tr><th>日期</th><th>方向</th><th>信号</th><th>入场</th><th>出场</th><th>入场价</th><th>初始止损</th><th>目标</th><th>出场价</th><th>1R减仓</th><th>R</th><th>结果</th><th>结构</th><th>原因</th></tr></thead>
        <tbody>{trade_rows}</tbody>
      </table>
    </section>
    {''.join(day_sections)}
    <script type="application/json" id="payload">{escape(json.dumps(payload, ensure_ascii=False))}</script>
  </main>
</body>
</html>"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")


def render_day_svg(date, bars, trades):
    if not bars:
        return "<svg viewBox='0 0 800 260'></svg>"
    w, h, pad = 800, 260, 28
    prices = [p for b in bars for p in (b["high"], b["low"])]
    lo, hi = min(prices), max(prices)
    span = max(hi - lo, TICK)

    def x(i):
        return pad + (w - 2 * pad) * i / max(len(bars) - 1, 1)

    def y(price):
        return h - pad - (h - 2 * pad) * (price - lo) / span

    points = " ".join(f"{x(i):.1f},{y(b['close']):.1f}" for i, b in enumerate(bars))
    time_to_idx = {b["time"]: i for i, b in enumerate(bars)}
    marks = []
    for t in trades:
        ei = time_to_idx.get(t.entry_time)
        xi = time_to_idx.get(t.exit_time)
        if ei is not None:
            color = "#047857" if t.direction == "做多" else "#b42318"
            marks.append(f"<circle cx='{x(ei):.1f}' cy='{y(t.entry):.1f}' r='4' fill='{color}'><title>{t.direction} entry {t.entry}</title></circle>")
        if xi is not None:
            color = "#047857" if t.r > 0 else "#b42318"
            marks.append(f"<rect x='{x(xi)-3:.1f}' y='{y(t.exit)-3:.1f}' width='6' height='6' fill='{color}'><title>exit {t.exit} {t.r}R</title></rect>")
    return f"""
    <svg viewBox="0 0 {w} {h}" role="img" aria-label="{date} price path">
      <text x="{pad}" y="18" font-size="13" fill="#344054">{date}</text>
      <line x1="{pad}" y1="{y(hi):.1f}" x2="{w-pad}" y2="{y(hi):.1f}" stroke="#e5e7eb" />
      <line x1="{pad}" y1="{y(lo):.1f}" x2="{w-pad}" y2="{y(lo):.1f}" stroke="#e5e7eb" />
      <text x="{w-pad-56}" y="{y(hi)+4:.1f}" font-size="11" fill="#667085">{hi:.2f}</text>
      <text x="{w-pad-56}" y="{y(lo)+4:.1f}" font-size="11" fill="#667085">{lo:.2f}</text>
      <polyline points="{points}" fill="none" stroke="#2563eb" stroke-width="2" />
      {''.join(marks)}
    </svg>
    """


def max_drawdown(rs):
    equity = peak = dd = 0
    for r in rs:
        equity += r
        peak = max(peak, equity)
        dd = min(dd, equity - peak)
    return round(dd, 2)


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    args = parse_args()
    daily, five, metadata = load_or_fetch(args)
    monitor, trades, day_stats = run_backtest(args, daily, five)
    if args.output:
        out = Path(args.output)
    else:
        safe_code = args.code.replace(".", "_")
        out = ROOT / "reports" / f"{safe_code}_{args.start}_{args.end}_price_action_backtest.html"
    render_html(args, metadata, daily, five, monitor, trades, day_stats, out)
    print(
        json.dumps(
            {
                "report": str(out),
                "source": metadata["source"],
                "monitor_records": len(monitor),
                "trades": len(trades),
                "total_r": round(sum(t.r for t in trades), 2),
                "win_rate": round(sum(1 for t in trades if t.r > 0) / len(trades) * 100, 1) if trades else 0,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
