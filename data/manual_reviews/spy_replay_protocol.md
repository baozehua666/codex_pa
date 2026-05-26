# SPY Strict Replay Protocol

> Purpose: prevent lookahead bias when replaying historical SPY intraday price action as if it were live.

## Core Rule

Replay is not ordinary hindsight review. At each decision point, only bars that have already closed may be used. Future 5-minute bars, the final daily high/low/close, prior manual review notes, and Brad end-of-day commentary for that same date are not allowed during the simulated live decision.

## Five-Minute Decision Clock

- Use RTH 5-minute bars for price-action decisions.
- After each 5-minute bar closes, immediately analyze the chart using bars `1..N`.
- Any new trade plan created after bar `N` can only trigger from bar `N+1` onward.
- Do not batch several bars and then backfill an entry that appeared earlier inside that batch.
- Do not revise the original reason, stop, or target after seeing later bars.

Example:

```text
Bar 45 closes at 13:15.
Analyze using bars 1..45.
If a long stop is placed above bar 45, it can trigger during bar 46 or later.
If the next analysis is delayed until 13:25, the model may not claim an entry at 13:15.
```

## One-Minute Execution Path

Use 1-minute bars only as an execution-path verifier for trades planned from 5-minute bars:

- Did the next 5-minute bar trigger the entry?
- If entry, stop, and target are all inside the same 5-minute bar, did the 1-minute sequence hit stop or target first?
- If 1-minute data still cannot resolve sequence, use conservative accounting: assume the adverse outcome first or mark the result uncertain.

Do not use the 1-minute chart to create extra signals unless the user explicitly asks for a 1-minute strategy. The strategy logic remains 5-minute Al Brooks price action.

## Tick Data

Futu `get_rt_ticker` can provide recent real-time ticks after subscription, but it is not a reliable historical replay source for an arbitrary past time range. For historical replay, use 1-minute bars as the practical path-resolution layer.

## SPY 2026-05-21 Calibration

The 2026-05-21 replay exposed two important execution lessons:

- A 10:30 five-minute long plan around `738.61` triggered on 1-minute data, but the `737.40` stop was hit at 11:09 before any full target. Strict result: `-1R`.
- A 14:30 five-minute short plan around `743.23` triggered on 1-minute data, but the `743.65` stop was hit at 14:45 before the later drop to 742.08 at 14:49. Strict result: `-1R`.

Therefore, buy-climax reversal shorts and low-test reversal longs need stricter replay handling. Direction can be correct while the execution stop is still too tight or too early.

## Output Standard

For strict replay, each bar decision should include:

```text
Replay time:
Known bars:
Position:
Decision: observe / place long stop / place short stop / manage / exit
Entry:
Stop:
Target:
50-share risk:
Reason using only known data:
Invalidation:
Next bar execution rule:
```

After the next 5-minute bar closes, use 1-minute bars inside that interval to report whether the plan triggered, stopped, targeted, remained open, or was not triggered.
