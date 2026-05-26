# SPY Strict Replay Protocol

Purpose: replay historical SPY intraday price action as if it were live, without lookahead.

## Clock

- Use RTH 5-minute bars as the only signal clock.
- After bar `N` closes, analyze immediately using only bars `1..N`.
- A plan created from bar `N` can trigger only from bar `N+1`.
- Never batch several bars and then claim an earlier entry.
- Never revise the original entry, stop, target, or reason after seeing later bars.

## Execution Path

Use 1-minute bars only after a 5-minute plan exists:

- Did the next bar trigger the entry?
- If triggered, did stop or target happen first?
- If the sequence is still ambiguous, assume the adverse result first or mark it uncertain.

Do not use 1-minute bars to create signals unless the user explicitly asks for a 1-minute strategy.

## Blindness Label

- If only past bars are loaded as the replay advances: label as `strict blind replay`.
- If full-day bars were loaded before decisions: label as `rules-strict replay, not fully blind`.
- If hindsight notes or same-day Brad commentary are used before decisions: label as `review`, not replay.

## Required Bar Decision Format

```text
Replay time:
Known bars:
Position:
Decision:
Entry:
Stop:
Target:
50-share risk:
Reason using only known data:
Invalidation:
Next bar execution rule:
```

## Required Day Summary

```text
Trades:
Wins/losses:
Net R:
Approx 50-share PnL:
Best avoided mistake:
Skill lesson:
```
