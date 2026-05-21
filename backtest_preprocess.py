#!/usr/bin/env python3
"""
回测版预处理脚本 v2 — 复用 preprocess.py v2 的分析逻辑，支持历史日期。

用法:
  python backtest_preprocess.py --date 2026-05-18
  python backtest_preprocess.py --date 2026-05-18 --bar-limit 20  (模拟只看到前20根bar)
  python backtest_preprocess.py --all  (输出所有回测日的预处理结果)
  python backtest_preprocess.py --all --dates 2026-05-15,2026-05-18,2026-05-19,2026-05-20
"""
import json
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preprocess import (
    calc_ema,
    classify_bars,
    detect_patterns,
    detect_micro_channel,
    find_swing_points,
    detect_three_pushes,
)

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest_data")
DAILY_FILE = os.path.join(BASE, "spy_daily_v2.json")
FIVEMIN_FILE = os.path.join(BASE, "spy_5m_w5.json")

BACKTEST_DATES = ["2026-05-15", "2026-05-18", "2026-05-19", "2026-05-20"]


def load_data(daily_file=None, fivemin_file=None):
    df = daily_file or DAILY_FILE
    ff = fivemin_file or FIVEMIN_FILE
    with open(df, encoding="utf-8") as f:
        daily = json.load(f)["data"]
    with open(ff, encoding="utf-8") as f:
        fivemin = json.load(f)["data"]
    return daily, fivemin


def get_bars_for_date(bars, date_str):
    return [b for b in bars if b["time"][:10] == date_str]


def get_bars_before_date(bars, date_str):
    return [b for b in bars if b["time"][:10] < date_str]


def get_prior_trading_day(daily, date_str):
    prior = [d for d in daily if d["time"][:10] < date_str]
    return prior[-1] if prior else None


def process_day(daily, fivemin, target_date, bar_limit=None):
    today_5m = get_bars_for_date(fivemin, target_date)
    if bar_limit and bar_limit < len(today_5m):
        today_5m = today_5m[:bar_limit]

    prior_days_5m = get_bars_before_date(fivemin, target_date)
    context_5m = prior_days_5m[-80:] + today_5m if prior_days_5m else today_5m
    work_bars = context_5m[-80:]

    daily_up_to = [d for d in daily if d["time"][:10] <= target_date]
    daily_closes = [d["close"] for d in daily_up_to]
    daily_ema20 = calc_ema(daily_closes, 20) if daily_closes else []

    daily_ranges = [d["high"] - d["low"] for d in daily_up_to]
    adr = round(sum(daily_ranges[-20:]) / len(daily_ranges[-20:]), 4) if daily_ranges else 0

    prior_day_daily = get_prior_trading_day(daily, target_date)
    prior_day_info = None
    if prior_day_daily:
        d = prior_day_daily
        daily_baseline = 0
        prior_dailies = [dd for dd in daily if dd["time"][:10] < target_date]
        if len(prior_dailies) >= 2:
            bodies = [abs(dd["close"] - dd["open"]) for dd in prior_dailies[-20:]]
            daily_baseline = sum(bodies) / len(bodies) if bodies else 0
        classify_bars([d], daily_baseline)
        prior_day_info = {
            "date": d["time"][:10],
            "open": d["open"], "high": d["high"],
            "low": d["low"], "close": d["close"],
            "bar_type": d.get("bar_type", ""),
        }

    gap = {"size": 0, "pct_of_adr": 0, "classification": "none"}
    if today_5m and prior_day_info:
        gap_size = round(today_5m[0]["open"] - prior_day_info["close"], 4)
        gap["size"] = gap_size
        gap_pct = round(gap_size / adr * 100, 2) if adr > 0 else 0
        gap["pct_of_adr"] = gap_pct
        abs_pct = abs(gap_pct)
        gap["classification"] = (
            "large" if abs_pct > 50 else "medium" if abs_pct > 25 else "small" if abs_pct > 5 else "none"
        )

    closes_5m = [b["close"] for b in work_bars]
    ema20_5m = calc_ema(closes_5m, 20) if closes_5m else []

    recent_bodies = [abs(b["close"] - b["open"]) for b in work_bars[-20:]]
    baseline_body = round(sum(recent_bodies) / len(recent_bodies), 4) if recent_bodies else 0

    classify_bars(work_bars, baseline_body)

    today_bar_start_idx = len(work_bars) - len(today_5m)
    for i, b in enumerate(work_bars):
        if i >= today_bar_start_idx:
            b["ema20"] = round(ema20_5m[i], 4) if i < len(ema20_5m) else None
        else:
            b["ema20"] = None

    if today_5m:
        today_high = max(b["high"] for b in today_5m)
        today_low = min(b["low"] for b in today_5m)
    else:
        today_high = today_low = 0
    today_range_val = today_high - today_low
    adr_consumed_pct = round(today_range_val / adr * 100, 2) if adr > 0 else 0

    scan_bars = work_bars[-20:]
    offset = len(work_bars) - len(scan_bars)
    patterns = detect_patterns(scan_bars, baseline_body)
    for p in patterns:
        p["bars"] = [idx + offset for idx in p["bars"]]
        if "level" in p:
            p["level"] = round(p["level"], 4)

    micro_ch = detect_micro_channel(work_bars[-20:])
    if micro_ch.get("active") and "start_idx" in micro_ch:
        micro_ch["start_idx"] += offset

    # EMA metrics
    ema_crosses_today = 0
    if len(today_5m) >= 2:
        for i in range(today_bar_start_idx + 1, len(work_bars)):
            e_prev = work_bars[i - 1].get("ema20")
            e_curr = work_bars[i].get("ema20")
            if e_prev and e_curr:
                prev_above = work_bars[i - 1]["close"] > e_prev
                curr_above = work_bars[i]["close"] > e_curr
                if prev_above != curr_above:
                    ema_crosses_today += 1

    ema_slope = 0
    if ema20_5m and len(ema20_5m) >= 5:
        recent_ema = ema20_5m[-5:]
        ema_slope = round((recent_ema[-1] - recent_ema[0]) / max(abs(recent_ema[0]), 1) * 100, 4)

    ema_distance_pct = 0
    if ema20_5m and work_bars and adr > 0:
        ema_distance_pct = round((work_bars[-1]["close"] - ema20_5m[-1]) / adr * 100, 2)

    # Bar stats
    bar_balance = {"bull": 0, "bear": 0, "neutral": 0, "bias": "balanced"}
    bar_stats = {"inside_count": 0, "outside_count": 0, "outside_pct": 0}
    if today_5m:
        for b in today_5m:
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
        bar_stats["outside_pct"] = round(bar_stats["outside_count"] / len(today_5m) * 100, 1)

    swing_highs, swing_lows = find_swing_points(work_bars)
    swing_points = {
        "highs": [{"idx": idx, "price": round(price, 4)} for idx, price in swing_highs],
        "lows": [{"idx": idx, "price": round(price, 4)} for idx, price in swing_lows],
    }

    three_pushes = detect_three_pushes(work_bars)

    enriched = []
    for i, b in enumerate(work_bars):
        entry = {
            "idx": i,
            "time": b["time"],
            "o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"],
            "vol": b.get("volume", 0),
            "bar_type": b.get("bar_type", ""),
            "body_strength": b.get("body_strength", "normal"),
            "is_inside": b["is_inside"],
            "is_outside": b["is_outside"],
        }
        if b.get("ema20") is not None:
            entry["ema20"] = b["ema20"]
        enriched.append(entry)

    bars_today_count = len(today_5m)

    return {
        "code": "US.SPY",
        "market": "US",
        "target_date": target_date,
        "session": {
            "bars_today": bars_today_count,
            "today_bar_start_idx": today_bar_start_idx,
        },
        "daily": {
            "ema20": round(daily_ema20[-1], 4) if daily_ema20 else None,
            "adr": adr,
            "prior_day": prior_day_info,
            "gap": gap,
        },
        "intraday": {
            "baseline_body": baseline_body,
            "ema20_current": round(ema20_5m[-1], 4) if ema20_5m else None,
            "ema20_slope": ema_slope,
            "ema20_distance_pct": ema_distance_pct,
            "ema_crosses_today": ema_crosses_today,
            "today_range": {"high": round(today_high, 4), "low": round(today_low, 4)},
            "adr_consumed_pct": adr_consumed_pct,
            "bar_balance": bar_balance,
            "bar_stats": bar_stats,
            "micro_channel": micro_ch,
            "patterns": patterns,
            "swing_points": swing_points,
            "three_pushes": three_pushes,
            "bars": enriched,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="回测预处理 v2")
    parser.add_argument("--date", type=str, help="目标日期 YYYY-MM-DD")
    parser.add_argument("--bar-limit", type=int, default=None, help="限制当日bar数量（模拟盘中）")
    parser.add_argument("--all", action="store_true", help="输出所有回测日")
    parser.add_argument("--fivemin-file", type=str, default=None, help="5分钟数据文件路径")
    parser.add_argument("--daily-file", type=str, default=None, help="日线数据文件路径")
    parser.add_argument("--dates", type=str, default=None, help="回测日期列表(逗号分隔)")
    args = parser.parse_args()

    daily, fivemin = load_data(args.daily_file, args.fivemin_file)
    dates = args.dates.split(",") if args.dates else BACKTEST_DATES

    if args.all:
        results = {}
        for dt in dates:
            results[dt] = process_day(daily, fivemin, dt)
        print(json.dumps(results, ensure_ascii=False))
    elif args.date:
        result = process_day(daily, fivemin, args.date, args.bar_limit)
        print(json.dumps(result, ensure_ascii=False))
    else:
        print("Usage: --date YYYY-MM-DD or --all")
        sys.exit(1)


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    main()
