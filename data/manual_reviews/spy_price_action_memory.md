# SPY Price Action Memory

> Purpose: persistent local memory for the SPY Al Brooks price-action workflow. This file records the user's execution model, manual-review preference, validated rules, and review outputs so future sessions can continue without re-deriving the same context.

## User Execution Model

- Instrument: SPY.
- Position size: fixed 50 shares.
- Execution: whole-position entry and whole-position exit.
- Do not use half exits, partial runners, scale-ins, or a second 50-share add-on unless the user explicitly changes the model.
- Maximum preferred initial risk: about 75 USD per trade.
- At most 1-2 completed A-grade trades per day.
- Stable weekly opportunity count matters more than trading every day.

## Analysis Preference

- For manual reviews, do not use Python scripts or batch backtest output as a substitute for judgment.
- Read cached 5-minute bars one day at a time.
- Use Brad daily transcripts and course notes only as targeted context.
- Write the reasoning manually: structure, location, trapped traders, signal, stop, target, and why non-A signals are rejected.
- Batch tools may be used only to list/extract local data, not to decide trades.
- For strict replay, analyze immediately after each 5-minute bar closes. Use only bars already closed. Any new order can trigger only from the next 5-minute bar onward.
- Do not batch several 5-minute bars and then backfill an entry that appeared earlier inside the batch.
- Use 1-minute bars only to verify intrabar execution order after a 5-minute trade plan exists. Do not create new 1-minute signals unless the user explicitly asks for a 1-minute strategy.

## Current Skill State

- Skill file in repo: `F:/个人知识库/codex_pa/SKILL.md`.
- Installed Codex skill file: `C:/Users/22971/.codex/skills/price-action/SKILL.md`.
- Both currently include the fixed 50-share SPY profile and manual-review rules validated on SPY 2026-03-02 through 2026-05-22.
- Both currently include the strict replay rule: no lookahead, 5-minute bar-close decisions, next-bar triggering, and 1-minute execution-path verification.
- Both currently include the strict real-time trading logic: 5-minute closed-bar decisions, context -> structure -> Always In -> location -> veto -> signal -> 50-share risk, next-bar triggering only, and 1-minute execution-path verification only after a 5-minute plan exists.
- Manual-review rules now explicitly include:
  - no chasing first large OR/gap bars;
  - A trades require location + trapped traders + second leg/pullback + normal risk;
  - trading-range middle entries are not A;
  - high-volatility/wide OR days require risk compression;
  - zero-A days are valid;
  - first lower high after an early selloff inside a wide OR is not automatically A;
  - do not replace a wide structural stop with a tight signal-bar stop just to pass the risk cap.

## Strict Replay Files

- Protocol: `data/manual_reviews/spy_replay_protocol.md`.
- Cached 1-minute calibration data: `backtest_cache/US_SPY_1m_2026-05-21_2026-05-21.json`.
- Futu 1-minute historical data worked for SPY 2026-05-21 and returned 390 RTH bars.
- Futu `get_rt_ticker` worked for recent ticks after subscription, but it is not a reliable arbitrary historical tick source. Use 1-minute bars for historical path verification.
- SPY 2026-05-21 strict replay calibration:
  - 10:30 five-minute long plan around `738.61` triggered, then stopped at `737.40` before target: strict `-1R`.
  - 14:30 five-minute short plan around `743.23` triggered, then stopped at `743.65` before the later drop: strict `-1R`.
  - Lesson: a directionally correct setup can still fail under strict execution; do not tighten stops simply to fit the risk cap.

## Completed Manual Reviews

| Period | File | Trading days | A trades | Manual R | 50-share estimate |
|---|---|---:|---:|---:|---:|
| 2026-03-02 to 2026-03-31 | `data/manual_reviews/spy_2026_03_manual_review.md` | 22 | 32 | +57.5R | about +3,100 to +3,500 USD |
| 2026-04-01 to 2026-04-30 | `data/manual_reviews/spy_2026_04_manual_review.md` | 21 | 39 | +72R | about +1,980 to +2,300 USD |
| 2026-05-01 to 2026-05-22 | `data/manual_reviews/spy_2026_05_manual_review.md` | 16 | about 28 | about +37R to +43R under old partial-management notes | needs full 50-share normalization if used for strict comparison |

Notes:

- March and April are already written in the current fixed 50-share whole-position model.
- May was reviewed before the no-half-position rule was fully enforced and still contains partial-management wording. Use it for structure learning, but normalize it before strict PnL comparison.
- The historical manual-review win rate is a hindsight study statistic, not a live-trading expectation.

## Important Learned Rules

1. Direction is not enough. A trade must have an honest structural stop that fits the 50-share risk cap.
2. Big breakout or reversal bars usually confirm direction; the executable entry often comes on the pullback, second entry, or failed breakout.
3. Wide trading ranges are edge-only markets. Middle stop-order signals are B/C even if they later work.
4. Strong trend days favor first pullback or trend-resumption entries; countertrend wedges are usually exit/management cues until there is a real break and follow-through.
5. Same-day direction flips require structure change: trend-line break, retest, second signal, and trapped-trader fuel.
6. After one good A trade captures the day's main premise, later same-direction signals are usually management, not new risk.
7. If no A-grade setup appears, record 0 trades for the day.

## Real-Time Output Standard

Use this format for live SPY checks:

```text
SPY [time]

Conclusion: observe / A long / A short / manage existing trade
Structure:
Always In:
Location:
Veto score:
50-share plan:
Entry:
Stop:
Target:
Initial risk:
Reason:
Invalidation:
```

Default to observe when structure, location, signal, or risk is unclear.

## Next Useful Work

- Normalize the May 2026 review into the strict whole-position 50-share model if the user asks for exact combined statistics.
- Continue earlier months only one day at a time.
- If building live monitoring, run Futu data refresh per 5-minute bar and use the skill as a decision filter, not as an automatic order system.
- For replay requests, prefer the strict protocol file and fetch 1-minute bars for the target date before judging ambiguous fills.
