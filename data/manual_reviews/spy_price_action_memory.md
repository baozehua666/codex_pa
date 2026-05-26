# SPY Price Action Memory

Purpose: persistent local memory for the SPY Al Brooks workflow.

## User Model

- Instrument: SPY.
- Size: fixed 50 shares.
- Entry/exit: whole position only.
- Do not use half exits, runners, scale-ins, or add-ons unless the user explicitly changes the model.
- Preferred initial risk: about `$75` or less per trade.
- Typical limit: 1-2 completed A-grade trades per day.
- Stable weekly opportunity count matters more than trading every day.

## Analysis Preference

- Manual review is one day at a time.
- Do not use Python scripts or batch backtest output as a substitute for judgment.
- Tools may fetch/list/extract bars; decisions must be reasoned manually.
- Strict replay follows `data/manual_reviews/spy_replay_protocol.md`.
- 1-minute bars verify execution path only after a 5-minute trade plan exists.

## Review Index

| Period | File | Note |
|---|---|---|
| 2026-03-02 to 2026-03-31 | `data/manual_reviews/spy_2026_03_manual_review.md` | fixed 50-share model |
| 2026-04-01 to 2026-04-30 | `data/manual_reviews/spy_2026_04_manual_review.md` | fixed 50-share model |
| 2026-05-01 to 2026-05-22 | `data/manual_reviews/spy_2026_05_manual_review.md` | older notes include partial-management wording; normalize before exact comparison |

## Strict Replay Calibrations

- 2026-05-21 long around `738.61`: triggered, then stopped at `737.40` before full target. Strict result: `-1R`.
- 2026-05-21 short around `743.23`: triggered, then stopped at `743.65` before later drop. Strict result: `-1R`.
- Lesson: direction can be correct while execution is still too early or the stop is invalid.

## Validated Rules

1. Direction is not enough; the structural stop must fit the 50-share risk model.
2. Big bars often confirm direction; the executable entry usually comes on the pullback, second entry, or failed breakout.
3. Wide trading ranges are edge-only markets. Middle stop-order entries are not A.
4. Strong trend days favor first pullback or trend-resumption entries.
5. Same-day direction flips require break, retest, second signal, and trapped-trader fuel.
6. After one good A trade captures the day's premise, later same-direction signals are usually management.
7. Zero-A days are valid.
8. Do not tighten a wide structural stop just to pass the risk cap.

## Maintenance

- Source skill file: `F:/个人知识库/codex_pa/SKILL.md`.
- Installed skill file: `C:/Users/22971/.codex/skills/price-action/SKILL.md`.
- Keep installed skill as a copy of the source `SKILL.md`; do not rely on stale installed helper scripts.
