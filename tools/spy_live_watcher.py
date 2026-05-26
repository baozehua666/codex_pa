#!/usr/bin/env python3
"""
Low-latency Futu 5-minute watcher for price-action analysis.

This script only fetches and shapes market data. It does not make trade
decisions. The agent still applies the price-action skill manually.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from preprocess import (  # noqa: E402
    MARKET_CONFIG,
    _market_tz,
    _today_start_idx,
    calc_ema,
    classify_bars,
    detect_micro_channel,
    detect_patterns,
    detect_session,
    detect_three_pushes,
    df_to_list,
    find_swing_points,
    infer_market,
)


def market_now(market: str) -> datetime:
    return datetime.now(_market_tz(market))


def parse_market_time(value: str, market: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=_market_tz(market))


def floor_5m(ts: datetime) -> datetime:
    minute = ts.minute - (ts.minute % 5)
    return ts.replace(minute=minute, second=0, microsecond=0)


def next_5m_close(ts: datetime) -> datetime:
    floor = floor_5m(ts)
    if ts == floor:
        return floor
    return floor + timedelta(minutes=5)


def sleep_until(target: datetime, market: str) -> None:
    while True:
        remaining = (target - market_now(market)).total_seconds()
        if remaining <= 0:
            return
        time.sleep(min(remaining, 0.2))


def filter_closed_5m(bars_5m: list[dict], market: str, now: datetime | None = None):
    now = now or market_now(market)
    cutoff = floor_5m(now)
    closed = []
    open_bar = None
    for bar in bars_5m:
        bar_time = parse_market_time(bar["time"], market)
        if bar_time <= cutoff:
            closed.append(bar)
        elif open_bar is None:
            open_bar = bar
    return closed, open_bar, cutoff


def opening_range(today_bars: list[dict], close: float, first_n: int):
    if len(today_bars) < first_n:
        return {"complete": False}
    chunk = today_bars[:first_n]
    high = max(b["high"] for b in chunk)
    low = min(b["low"] for b in chunk)
    width = high - low
    if close > high:
        state = "above"
    elif close < low:
        state = "below"
    else:
        state = "inside"
    return {
        "complete": True,
        "high": round(high, 4),
        "low": round(low, 4),
        "width": round(width, 4),
        "position": round((close - low) / width, 3) if width > 0 else None,
        "state": state,
    }


def build_context(
    code: str,
    bars_5m: list[dict],
    bars_daily: list[dict],
    *,
    output_bars: int = 40,
) -> dict:
    market = infer_market(code)
    if not bars_5m:
        return {"code": code, "market": market, "error": "no closed 5m bars"}

    bars_5m = [dict(b) for b in bars_5m]
    bars_daily = [dict(b) for b in bars_daily]

    daily_closes = [b["close"] for b in bars_daily]
    daily_ema20 = calc_ema(daily_closes, 20) if daily_closes else []
    daily_ranges = [b["high"] - b["low"] for b in bars_daily]
    adr = round(sum(daily_ranges[-20:]) / len(daily_ranges[-20:]), 4) if daily_ranges else 0

    t_start = _today_start_idx(bars_5m, market)
    today_count = len(bars_5m) - t_start
    today_bars = bars_5m[t_start:] if today_count > 0 else []
    today_date = today_bars[0]["time"][:10] if today_bars else None

    prior_day = None
    if bars_daily:
        latest_daily_is_today = bool(today_date and bars_daily[-1]["time"].startswith(today_date))
        prior_idx = -2 if latest_daily_is_today and len(bars_daily) >= 2 else -1
        daily_bar = dict(bars_daily[prior_idx])
        baseline_end = len(bars_daily) + prior_idx
        baseline_slice = bars_daily[max(0, baseline_end - 20):baseline_end]
        daily_baseline = (
            sum(abs(b["close"] - b["open"]) for b in baseline_slice) / len(baseline_slice)
            if baseline_slice
            else abs(daily_bar["close"] - daily_bar["open"])
        )
        classify_bars([daily_bar], daily_baseline)
        prior_day = {
            "high": daily_bar["high"],
            "low": daily_bar["low"],
            "close": daily_bar["close"],
            "open": daily_bar["open"],
            "bar_type": daily_bar.get("bar_type", ""),
        }

    gap = {"size": 0, "pct_of_adr": 0, "classification": "none"}
    if prior_day and today_bars:
        gap_size = round(today_bars[0]["open"] - prior_day["close"], 4)
        gap_pct = round(gap_size / adr * 100, 2) if adr else 0
        abs_pct = abs(gap_pct)
        gap = {
            "size": gap_size,
            "pct_of_adr": gap_pct,
            "classification": (
                "large" if abs_pct > 50 else
                "medium" if abs_pct > 25 else
                "small" if abs_pct > 5 else
                "none"
            ),
        }

    closes_5m = [b["close"] for b in bars_5m]
    ema20_5m = calc_ema(closes_5m, 20) if closes_5m else []
    recent_bodies = [abs(b["close"] - b["open"]) for b in bars_5m[-20:]]
    baseline_body = round(sum(recent_bodies) / len(recent_bodies), 4) if recent_bodies else 0

    classify_bars(bars_5m, baseline_body)
    for idx, bar in enumerate(bars_5m):
        bar["ema20"] = round(ema20_5m[idx], 4) if idx < len(ema20_5m) else None

    today_bars = bars_5m[t_start:] if today_count > 0 else []
    if today_bars:
        today_high = max(b["high"] for b in today_bars)
        today_low = min(b["low"] for b in today_bars)
    else:
        today_high = today_low = 0
    today_range = today_high - today_low
    last_close = bars_5m[-1]["close"]
    range_position = round((last_close - today_low) / today_range, 3) if today_range > 0 else None
    adr_consumed_pct = round(today_range / adr * 100, 2) if adr else 0

    scan_n = min(20, len(today_bars))
    scan_offset = t_start + len(today_bars) - scan_n if scan_n else len(bars_5m)
    patterns = detect_patterns(today_bars[-scan_n:], baseline_body) if scan_n >= 3 else []
    for pattern in patterns:
        pattern["bars"] = [idx + scan_offset for idx in pattern["bars"]]

    mc_n = min(20, len(today_bars))
    mc_offset = t_start + len(today_bars) - mc_n if mc_n else len(bars_5m)
    micro_channel = detect_micro_channel(today_bars[-mc_n:]) if mc_n >= 3 else {"active": False}
    if micro_channel.get("active") and "start_idx" in micro_channel:
        micro_channel["start_idx"] += mc_offset

    if today_count >= 10:
        three_pushes = detect_three_pushes(today_bars)
        for push in three_pushes:
            push["pushes"] = [idx + t_start for idx in push["pushes"]]
    else:
        three_pushes = []

    sp_slice = today_bars if today_count >= 5 else bars_5m[-min(30, len(bars_5m)):]
    sp_offset = t_start if today_count >= 5 else len(bars_5m) - len(sp_slice)
    swing_highs, swing_lows = find_swing_points(sp_slice)
    swing_points = {
        "highs": [{"idx": idx + sp_offset, "level": round(value, 4)} for idx, value in swing_highs],
        "lows": [{"idx": idx + sp_offset, "level": round(value, 4)} for idx, value in swing_lows],
    }

    ema_crosses_today = 0
    for idx in range(t_start + 1, len(bars_5m)):
        prev_ema = bars_5m[idx - 1].get("ema20")
        curr_ema = bars_5m[idx].get("ema20")
        if prev_ema and curr_ema:
            prev_above = bars_5m[idx - 1]["close"] > prev_ema
            curr_above = bars_5m[idx]["close"] > curr_ema
            if prev_above != curr_above:
                ema_crosses_today += 1

    ema_slope = 0
    if len(ema20_5m) >= 5:
        recent_ema = ema20_5m[-5:]
        ema_slope = round((recent_ema[-1] - recent_ema[0]) / max(abs(recent_ema[0]), 1) * 100, 4)

    ema_distance_pct = 0
    if ema20_5m and adr > 0:
        ema_distance_pct = round((last_close - ema20_5m[-1]) / adr * 100, 2)

    bar_balance = {"bull": 0, "bear": 0, "neutral": 0, "bias": "balanced"}
    bar_stats = {"inside_count": 0, "outside_count": 0, "outside_pct": 0}
    for bar in today_bars:
        bar_type = bar.get("bar_type", "")
        if "bull" in bar_type:
            bar_balance["bull"] += 1
        elif "bear" in bar_type:
            bar_balance["bear"] += 1
        else:
            bar_balance["neutral"] += 1
        if bar.get("is_inside"):
            bar_stats["inside_count"] += 1
        if bar.get("is_outside"):
            bar_stats["outside_count"] += 1
    total_directional = bar_balance["bull"] + bar_balance["bear"]
    if total_directional > 0:
        bull_pct = bar_balance["bull"] / total_directional
        bar_balance["bias"] = "bull" if bull_pct > 0.6 else "bear" if bull_pct < 0.4 else "balanced"
    if today_count > 0:
        bar_stats["outside_pct"] = round(bar_stats["outside_count"] / today_count * 100, 1)

    enriched = []
    out_start = max(0, len(bars_5m) - output_bars)
    for idx in range(out_start, len(bars_5m)):
        bar = bars_5m[idx]
        entry = {
            "idx": idx,
            "time": bar["time"],
            "o": bar["open"],
            "h": bar["high"],
            "l": bar["low"],
            "c": bar["close"],
            "volume": bar["volume"],
            "body": bar["body"],
            "body_strength": bar.get("body_strength", "normal"),
            "bar_type": bar.get("bar_type", ""),
            "upper_tail": bar["upper_tail"],
            "lower_tail": bar["lower_tail"],
            "close_pct": bar["close_pct"],
            "is_inside": bar["is_inside"],
            "is_outside": bar["is_outside"],
        }
        if idx >= t_start:
            entry["ema20"] = bar.get("ema20")
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
                "first_30m": opening_range(today_bars, last_close, 6),
                "first_90m": opening_range(today_bars, last_close, 18),
            },
            "adr_consumed_pct": adr_consumed_pct,
            "bar_balance": bar_balance,
            "bar_stats": bar_stats,
            "micro_channel": micro_channel,
            "patterns": patterns,
            "three_pushes": three_pushes,
            "swing_points": swing_points,
            "bars": enriched,
        },
    }


class FutuWatcher:
    def __init__(self, code: str, host: str, port: int, count_5m: int, count_daily: int):
        from futu import OpenQuoteContext, SubType

        self.code = code
        self.host = host
        self.port = port
        self.count_5m = count_5m
        self.count_daily = count_daily
        self.ctx = OpenQuoteContext(host=host, port=port)
        ret, msg = self.ctx.subscribe([code], [SubType.K_5M, SubType.K_DAY])
        if ret != 0:
            self.ctx.close()
            raise RuntimeError(f"subscribe failed: {msg}")

    def close(self) -> None:
        self.ctx.close()

    def fetch(self):
        from futu import AuType, KLType

        start = time.perf_counter()
        ret_5m, data_5m = self.ctx.get_cur_kline(self.code, self.count_5m, KLType.K_5M, AuType.QFQ)
        ret_day, data_day = self.ctx.get_cur_kline(self.code, self.count_daily, KLType.K_DAY, AuType.QFQ)
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        if ret_5m != 0:
            raise RuntimeError(f"get 5m kline failed: {data_5m}")
        if ret_day != 0:
            raise RuntimeError(f"get daily kline failed: {data_day}")
        return df_to_list(data_5m), df_to_list(data_day), latency_ms


def snapshot(watcher: FutuWatcher, output_bars: int) -> dict:
    market = infer_market(watcher.code)
    now = market_now(market)
    raw_5m, daily, latency_ms = watcher.fetch()
    closed_5m, open_bar, cutoff = filter_closed_5m(raw_5m, market, now)
    context = build_context(watcher.code, closed_5m, daily, output_bars=output_bars)
    context["timing"] = {
        "market_now": now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "closed_cutoff": cutoff.strftime("%Y-%m-%d %H:%M:%S"),
        "latest_closed_bar": closed_5m[-1]["time"] if closed_5m else None,
        "ignored_open_bar": open_bar["time"] if open_bar else None,
        "fetch_latency_ms": latency_ms,
        "closed_bar_delay_sec": (
            round((now - parse_market_time(closed_5m[-1]["time"], market)).total_seconds(), 3)
            if closed_5m
            else None
        ),
    }
    return context


def compact_payload(payload: dict) -> dict:
    if payload.get("event") in {"ready", "data_delay"}:
        return payload

    intraday = payload.get("intraday", {})
    bars = intraday.get("bars", [])
    latest_bar = bars[-1] if bars else None
    recent_bars = [
        {
            "time": bar.get("time"),
            "o": bar.get("o"),
            "h": bar.get("h"),
            "l": bar.get("l"),
            "c": bar.get("c"),
            "type": bar.get("bar_type"),
            "close_pct": bar.get("close_pct"),
            "ema20": bar.get("ema20"),
        }
        for bar in bars
    ]
    swing_points = intraday.get("swing_points", {})
    return {
        "event": payload.get("event"),
        "code": payload.get("code"),
        "market": payload.get("market"),
        "timing": payload.get("timing"),
        "session": payload.get("session"),
        "daily": {
            "adr": payload.get("daily", {}).get("adr"),
            "prior_day": payload.get("daily", {}).get("prior_day"),
            "gap": payload.get("daily", {}).get("gap"),
        },
        "intraday": {
            "ema20": intraday.get("ema20_current"),
            "ema20_slope": intraday.get("ema20_slope"),
            "ema20_distance_pct": intraday.get("ema20_distance_pct"),
            "ema_crosses_today": intraday.get("ema_crosses_today"),
            "today_range": intraday.get("today_range"),
            "range_position": intraday.get("range_position"),
            "opening_range": intraday.get("opening_range"),
            "adr_consumed_pct": intraday.get("adr_consumed_pct"),
            "bar_balance": intraday.get("bar_balance"),
            "micro_channel": intraday.get("micro_channel"),
            "patterns": intraday.get("patterns"),
            "swing_highs": swing_points.get("highs", [])[-4:],
            "swing_lows": swing_points.get("lows", [])[-4:],
            "latest_bar": latest_bar,
            "recent_bars": recent_bars,
        },
    }


def print_json(payload: dict, pretty: bool) -> None:
    if pretty:
        print(json.dumps(payload, ensure_ascii=False, indent=2), flush=True)
    else:
        print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), flush=True)


def emit(payload: dict, args) -> None:
    print_json(compact_payload(payload) if args.compact else payload, args.pretty)


def run_loop(args) -> None:
    market = infer_market(args.code)
    watcher = FutuWatcher(args.code, args.host, args.port, args.count_5m, args.count_daily)
    emitted_bar = None
    emitted_count = 0
    try:
        # Warm the connection before the first decision boundary.
        watcher.fetch()
        ready = {
            "event": "ready",
            "code": args.code,
            "market": market,
            "market_now": market_now(market).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "poll_interval_sec": args.poll_interval,
            "max_wait_sec": args.max_wait,
        }
        emit(ready, args)

        while True:
            now = market_now(market)
            target = next_5m_close(now)
            if target <= now:
                target += timedelta(minutes=5)
            sleep_until(target, market)
            deadline = target + timedelta(seconds=args.max_wait)
            target_key = target.strftime("%Y-%m-%d %H:%M:%S")

            while market_now(market) <= deadline:
                payload = snapshot(watcher, args.output_bars)
                latest = payload.get("timing", {}).get("latest_closed_bar")
                if latest == target_key and latest != emitted_bar:
                    payload["event"] = "bar_closed"
                    payload["timing"]["target_bar"] = target_key
                    payload["timing"]["emit_delay_sec"] = round(
                        (market_now(market) - target).total_seconds(), 3
                    )
                    emit(payload, args)
                    emitted_bar = latest
                    emitted_count += 1
                    if args.max_events and emitted_count >= args.max_events:
                        return
                    break
                time.sleep(args.poll_interval)
            else:
                emit({
                    "event": "data_delay",
                    "code": args.code,
                    "target_bar": target_key,
                    "market_now": market_now(market).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                    "max_wait_sec": args.max_wait,
                }, args)
    finally:
        watcher.close()


def parse_args():
    parser = argparse.ArgumentParser(description="Low-latency Futu 5m watcher for price-action analysis.")
    parser.add_argument("--code", default="US.SPY")
    parser.add_argument("--host", default=os.getenv("FUTU_OPEND_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("FUTU_OPEND_PORT", "11111")))
    parser.add_argument("--once", action="store_true", help="Print one latest closed-bar snapshot and exit.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON instead of JSONL.")
    parser.add_argument("--compact", action="store_true", help="Emit compact analysis context instead of full payload.")
    parser.add_argument("--poll-interval", type=float, default=0.12)
    parser.add_argument("--max-wait", type=float, default=2.0)
    parser.add_argument("--max-events", type=int, default=0, help="Stop after N closed-bar events; 0 means run forever.")
    parser.add_argument("--count-5m", type=int, default=100)
    parser.add_argument("--count-daily", type=int, default=25)
    parser.add_argument("--output-bars", type=int, default=16)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    watcher = None
    try:
        if args.once:
            watcher = FutuWatcher(args.code, args.host, args.port, args.count_5m, args.count_daily)
            watcher.fetch()  # warm request
            emit(snapshot(watcher, args.output_bars), args)
            return 0

        run_loop(args)
        return 0
    finally:
        if watcher is not None:
            watcher.close()


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    raise SystemExit(main())
