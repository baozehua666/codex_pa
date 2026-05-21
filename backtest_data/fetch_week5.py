"""Fetch SPY data for week of May 15-21, 2026 via Futu OpenD."""
import json
import os
import sys

def fetch_and_save():
    from futu import OpenQuoteContext, RET_OK, KLType, AuType
    import pandas as pd

    base = os.path.dirname(os.path.abspath(__file__))
    ctx = OpenQuoteContext(host="127.0.0.1", port=11111)

    try:
        # Daily: re-fetch full range for context
        print("Fetching daily data (Apr 10 - May 21)...")
        all_daily = None
        page_key = None
        first = True
        while first or page_key is not None:
            first = False
            ret, data, page_key = ctx.request_history_kline(
                "US.SPY", start="2026-04-10", end="2026-05-21",
                ktype=KLType.K_DAY, autype=AuType.QFQ,
                max_count=1000, page_req_key=page_key,
            )
            if ret != RET_OK:
                print(f"Daily error: {data}")
                return
            all_daily = data if all_daily is None else pd.concat([all_daily, data], ignore_index=True)

        records = []
        for i in range(len(all_daily)):
            r = all_daily.iloc[i]
            records.append({
                "time": str(r.get("time_key", "")),
                "open": float(r.get("open", 0)),
                "high": float(r.get("high", 0)),
                "low": float(r.get("low", 0)),
                "close": float(r.get("close", 0)),
                "volume": int(r.get("volume", 0)),
                "turnover": float(r.get("turnover", 0)),
            })
        with open(os.path.join(base, "spy_daily_v2.json"), "w", encoding="utf-8") as f:
            json.dump({"code": "US.SPY", "ktype": "1d", "data": records}, f, ensure_ascii=False)
        print(f"  Saved {len(records)} daily bars")

        # 5-min: May 12-21 (need prior week for context)
        print("Fetching 5-min data (May 12 - May 21)...")
        all_5m = None
        page_key = None
        first = True
        while first or page_key is not None:
            first = False
            ret, data, page_key = ctx.request_history_kline(
                "US.SPY", start="2026-05-12", end="2026-05-21",
                ktype=KLType.K_5M, autype=AuType.QFQ,
                max_count=1000, page_req_key=page_key,
            )
            if ret != RET_OK:
                print(f"5m error: {data}")
                return
            all_5m = data if all_5m is None else pd.concat([all_5m, data], ignore_index=True)

        records = []
        for i in range(len(all_5m)):
            r = all_5m.iloc[i]
            records.append({
                "time": str(r.get("time_key", "")),
                "open": float(r.get("open", 0)),
                "high": float(r.get("high", 0)),
                "low": float(r.get("low", 0)),
                "close": float(r.get("close", 0)),
                "volume": int(r.get("volume", 0)),
                "turnover": float(r.get("turnover", 0)),
            })
        with open(os.path.join(base, "spy_5m_w5.json"), "w", encoding="utf-8") as f:
            json.dump({"code": "US.SPY", "ktype": "5m", "data": records}, f, ensure_ascii=False)
        print(f"  Saved {len(records)} 5-min bars")

    finally:
        ctx.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    fetch_and_save()
