# Al Brooks Price Action Trading Knowledge Base

> Synthesized from 17 course note files + 44 Brad daily Emini reviews (February 18 – May 13, 2026)

---

## I. Course Core Theory

### 1.1 Four Market Structures

| Structure | Definition | Core Characteristics | Trading Approach |
|-----------|-----------|---------------------|-----------------|
| **Breakout** | Price moves rapidly in one direction, escaping prior range | Consecutive strong trend bars, no pullback, large bodies with small tails | Trade with the trend, tight stops, first reversal attempt usually fails |
| **Tight Channel** | Breakout on a higher timeframe; pullbacks are shallow and brief | Minimal bar overlap, sustained single-direction movement, EMA acts as effective support/resistance | Trade only in the direction of the channel, never counter-trend |
| **Broad Channel** | A tilted trading range; can profit in both directions | Higher highs + higher lows (bull) or opposite; deep pullbacks | Can trade both directions, but with-trend has higher probability |
| **Trading Range** | Price oscillates within a horizontal range for ≥20 bars | Heavy bar overlap, most breakouts fail, no sustained direction | Buy low sell high, primarily limit orders |

**80% Inertia Rule**:
- In a trend: 80% of reversal attempts fail → first reversal signal is usually just a pullback
- In a trading range: 80% of breakout attempts fail → most breakouts get pulled back into range

**Market Cycle**: Breakout → Channel → Trading Range → New Breakout (repeats)

**Market Oscillation Model**:
```
+1 (Bull Trend) ↔ 0 (Trading Range) ↔ -1 (Bear Trend)
```
- The market cannot jump directly from +1 to -1 (or vice versa) — it must transition through 0 (TR) first
- After a trend ends, the most likely next phase is a trading range, not an immediate opposite trend
- This reinforces: "best case for the counter-trend side is a trading range"

### 1.2 Signal Bar Types

**Bar Size Baseline**: average body size (|close - open|) of the most recent 20 bars. Large body = ≥1.5× baseline; Small body = ≤0.5× baseline.

| Type | Quantified Characteristics | Meaning |
|------|---------------------------|---------|
| **Bull reversal bar** | Close in upper 25% of bar range, lower tail ≥ 50% of range | Buy signal |
| **Bear reversal bar** | Close in lower 25% of bar range, upper tail ≥ 50% of range | Sell signal |
| **Breakout bar** | Large body (≥1.5× baseline), close in top/bottom 10%, tails each <25% of range | Directional momentum, second leg likely |
| **Doji** | Body ≤ 0.3× baseline, neither tail > 2× body | Indecision, limit order market |
| **Inside bar** | H ≤ prior H AND L ≥ prior L | Range compression, breakout setup |
| **Outside bar** | H > prior H AND L < prior L | Both sides contesting, look at close direction |
| **Trading range bar** | Both tails ≥ 33% of range, close in middle 50% of range | Limit orders dominating, both sides trapped |

**Bar Combination Patterns** (multi-bar setups identifiable from K-line data):

| Pattern | Detection Rule | Meaning |
|---------|---------------|---------|
| **OO (Outside-Outside) BreakOut Mode** | Two consecutive outside bars (each bar's H > prior H AND L < prior L) | Extreme bull-bear contest; trade the breakout direction — buy above OO high, sell below OO low |
| **ioi (Inside-Outside-Inside)** | Inside bar → outside bar → inside bar | Compression → expansion → compression = energy building; breakout of the final inside bar is the entry |
| **Bull Surprise** | 2-3 consecutive bull bars, each closing in upper 25%, minimal overlap between bars, bodies ≥ 1× baseline | Unexpected strength; >80% chance of follow-through and a second leg up |
| **Bear Surprise** | 2-3 consecutive bear bars, each closing in lower 25%, minimal overlap between bars, bodies ≥ 1× baseline | Unexpected weakness; >80% chance of follow-through and a second leg down |
| **Micro Double Top** | Two bars within 2-4 bars of each other test the same high (within 0.1% tolerance) | Short-term resistance confirmed; sell below subsequent bear bar |
| **Micro Double Bottom** | Two bars within 2-4 bars of each other test the same low (within 0.1% tolerance) | Short-term support confirmed; buy above subsequent bull bar |

**Give Up Bar**:
- A bar where trapped traders collectively abandon their positions
- Characteristics: large body in the direction opposite to their position, often with increased volume
- Produces a climactic signal — the move may pause or reverse after the give up bar
- Key insight: the give up bar is both an exit signal for the trapped side and a potential entry signal for the winning side

**Brad's Signal Bar Assessment in Practice**:
- "Bad stop order buy/sell" = poor signal bar quality → opposite side entry is better
- Small bar = good risk/reward + low probability (Brad emphasizes repeatedly)
- Big bar = distant stop, large risk, but potentially higher probability

### 1.3 Entry Patterns

#### 1.3.1 Pullback-Count Entries

| Pattern | Definition | When to Use |
|---------|-----------|-------------|
| **H1 (High 1)** | Buy after first pullback in bull trend | First pullback in a strong trend |
| **H2 (High 2)** | Buy after second pullback in bull trend | Higher probability with-trend entry |
| **L1 (Low 1)** | Sell after first bounce in bear trend | First bounce in a strong decline |
| **L2 (Low 2)** | Sell after second bounce in bear trend | Higher probability with-trend sell |

#### 1.3.2 Pattern-Based Entries

| Pattern | Definition | Key Rules |
|---------|-----------|-----------|
| **Wedge** | Three-push pattern at end of channel | Requires trend line break for confirmation; good vs. bad wedge depends on context |
| **Double Top / Bottom** | Two tests of the same level followed by reversal | Micro double tops/bottoms are extremely common on 5-min charts |
| **Second Entry** | Same-direction re-entry after first entry fails | One of Brad's most recommended entry timings |
| **MTR (Major Trend Reversal)** | Trend line break → retest of extreme → reversal | Four steps: ①Bull trend ②Trend line break ③Retest of high ④Lower high / double top / higher high reversal; probability: only ~40% produce a swing; minimum confirmation: TBTL (Ten Bars Two Legs = at least 10 bars and 2 legs in the reversal direction) |
| **Spike and Channel** | Strong breakout followed by weaker channel | Channel eventually evolves into trading range; channel end tests channel start; nested structure: Spike = Leg 1, Channel = extended pullback + Leg 2; the channel itself can be measured with Leg1=Leg2 internally |
| **Micro Channel** | Each bar's low ≥ prior bar's low (bull) | First reversal usually fails; breakout side waits for second leg |
| **Breakout Pullback** | Pullback to test the breakout point | Trapped traders at breakout point create support/resistance |
| **Stairs Pattern** | Breakout to new low/high with deep pullback covering breakout point | Limit order traders take profits at breakout point → not a strong trend signal |
| **Triangle** | Converging pattern, breakout setup | Wait for breakout direction |
| **Expanding Triangle** | Higher highs + lower lows, expanding range | Two-way trap: longs trapped above, shorts trapped below; usually appears within a TR representing extreme contention; often resolves into a tighter TR or a genuine breakout |
| **Final Flag** | Last pullback in a trend that looks like a continuation flag but becomes the start of a reversal | Appears after an extended trend (often after 3+ pushes); traders expect continuation → wrong side gets trapped; the flag breaks opposite to the trend → becomes the first leg of a reversal; probability: ~40% produces a swing (same as MTR); minimum target: TBTL (Ten Bars Two Legs) |
| **Opening Reversal** | Fast move to a magnet level in the first 60–90 minutes, then reversal | Most common intraday pattern; gap + fast trend to prior day H/L or key S/R → exhaustion → reversal; the initial move traps chasers (Group 2) → their panic fuels the reversal; often produces a two-legged correction lasting into midday |

#### 1.3.3 Key Entry Principles

1. **Trapped Trader Logic** (Brad's core): Breakout traps traders → trapped traders produce second leg → second leg is the primary trading signal
2. **Three Groups of Trapped Traders**:
   - **Group 1 — Wrong direction**: Entered opposite to the move (e.g., bought at the high) → forced to stop out → creates opposite pressure
   - **Group 2 — Right direction, too late**: Chased the move and entered at a poor price → panics on any pullback → accelerates reversals
   - **Group 3 — Right direction, exited too early**: Took profits prematurely → may re-enter at a worse price → creates secondary demand/supply
3. **Second Leg Rule**: Any breakout/micro channel "will probably get a second leg" (Brad's most frequently used phrase in daily reviews)
4. **Always In Direction**: Determine market direction based on most recent evidence — long or short
5. **Pattern Confluence**: When multiple patterns align at the same price point (e.g., Wedge + Double Top + Micro Double Top), the setup has higher probability. Each additional overlapping pattern increases confidence. In practice: if ≥2 independent patterns point to the same entry, upgrade confidence one level

### 1.4 Stop Rules

#### Three Stop Types

| Type | Definition | When to Use |
|------|-----------|-------------|
| **Price Action Stop (PA Stop)** | Based on signal bar extreme or key structural point | Most common; beyond the signal bar |
| **Money Stop** | Fixed dollar amount or tick count | Caps maximum risk per trade |
| **Measured Move Stop (MM Stop)** | Based on prior leg's measured distance | Used alongside measured move targets |

#### Stop Rules by Market State

- **In a trend**: Initial stop beyond signal bar; trail stop with trend (follow EMA or pullback lows)
- **In a trading range**: Stop beyond range boundary; use wide stop + scale-in
- **Reversal trade**: Stop beyond trend extreme; requires TBTL (Ten Bars Two Legs) confirmation

#### Brad's Practical Stop Guidance

- Small bar signal → stop beyond bar, but warns "good risk/reward = low probability"
- Entry after micro channel → don't place stop at the immediate high/low of signal bar (that level is resistance/support — placing a counter-trend entry there is illogical)
- Wide stop + scale-in → 80% probability of at least breaking even

### 1.5 Target Setting

#### Measured Move — Three Methods

| Method | Calculation | When to Use |
|--------|------------|-------------|
| **Leg1 = Leg2** | Project first leg's length for second leg | Most common; Brad uses this almost daily |
| **Trading Range Height Projection** | Project TR height from breakout point | Target after breaking out of a TR |
| **Breakout Bar Body Projection** | Project breakout bar's body height | Short-term target after strong breakout bar |

#### Actual Risk Targets

- **1x Actual Risk**: 1× the maximum adverse excursion since entry → basic scalp target
- **2x Actual Risk**: 2× the maximum adverse excursion → minimum swing trade target

#### Magnets (Price Attraction Levels)

Magnets are price levels that attract price toward them — a "vacuum" effect where price accelerates as it nears the level. Once reached, magnets often trigger a reversal or pause.

**Magnet hierarchy (strongest → weakest):**

| Priority | Magnet | Why It Works |
|----------|--------|-------------|
| 1 | Prior day's high / low | Most-watched intraday levels; stops cluster there |
| 2 | Measured move target (Leg1=Leg2) | Institutional algorithms target this |
| 3 | Key S/R from higher timeframe | Swing highs/lows, weekly levels |
| 4 | EMA (20-period) | Mean reversion target in pullbacks |
| 5 | 50% pullback level | Natural equilibrium point |
| 6 | Breakout point (origin) | Trapped traders create S/R there |
| 7 | Channel line / trend line | Geometric boundary of the move |
| 8 | Round numbers | Psychological; options strikes cluster there |

**Vacuum dynamics**: When price is within ~30% of the distance to a magnet, it often accelerates — sellers/buyers thin out between current price and the magnet, creating a vacuum. This acceleration is itself a signal: it looks like a breakout but is often climactic → reversal at the magnet.

**Dual role**: A magnet is both a target (price heads toward it) and a reversal zone (price often reverses once it gets there). Use magnets for:
- Setting realistic targets in R1 (nearest magnet = likely first resistance/support)
- Anticipating reversals at magnet levels (especially Opening Reversals)

#### ADR (Average Daily Range) as Sustainability Tool

- ADR = average distance between the daily high and low over recent sessions
- Measures how much of the "typical day" the market has already traveled
- When >80% of ADR has been consumed → remaining directional room is limited → do not chase
- Combine opening range + ADR to estimate the day's probable boundaries
- Useful for filtering late entries: if the move has already used most of the ADR, the reward/risk of chasing is poor

#### Actual Risk vs. Initial Risk

- **Initial risk**: distance from entry to protective stop at time of entry
- **Actual risk**: maximum adverse excursion since entry (the deepest the trade went against you)
- Actual risk is often smaller than initial risk → use 1x and 2x actual risk for profit-taking targets
- Brad emphasizes: "Actual risk is what matters for your targets, not the initial risk"

### 1.6 Trade Management Principles

#### Swing Trade vs. Scalp

| Dimension | Swing Trade | Scalp |
|-----------|-------------|-------|
| Target | ≥2R | <2R |
| Minimum Win Rate | 40% | 60% |
| When to Use | Trend is clear | Trading range or uncertain |
| **No Conversion** | Losing scalp → do not convert to swing | Winning swing → do not shorten to scalp |

#### Scale-In Rules

- Total risk must not exceed normal single-trade risk
- Scale-in improves average entry → break even near original entry price
- Brad's common scale-in scenarios: buy low / sell high in TR, with-trend additions in trend

#### Partial Exit

- Take partial profit at 1x risk
- Protect remainder with trailing stop
- Big bars (especially channel line breakouts) are profit-taking signals

---

## II. Brad Daily Review Practical Extraction

### 2.1 Top 10 Most Frequently Identified Patterns

Based on frequency analysis across 44 reviews:

| Rank | Pattern / Concept | Frequency | Brad's Typical Phrasing |
|------|-------------------|-----------|------------------------|
| 1 | **Micro Channel + Second Leg** | Nearly every bar | "micro channel, second leg up/down likely" |
| 2 | **Trapped Traders** | Every review | "traders buying/selling here are trapped, and that creates support/resistance" |
| 3 | **Breakout Point as Support/Resistance** | Every review | "breakout point, traders selling here got trapped on the breakout" |
| 4 | **Limit Order Market** | ~80% of reviews | "limit order market, probably sellers above and buyers below" |
| 5 | **Always In Direction Determination** | ~75% of reviews | "it's always in long/short" |
| 6 | **Channel Evolving into Trading Range** | ~70% of reviews | "spike and channel, the channel will probably evolve into a trading range" |
| 7 | **"Small Bar = Good Risk/Reward but Low Probability"** | ~65% of reviews | "small bar, good risk reward, but low probability" |
| 8 | **Stairs Pattern** | ~50% of reviews | "stairs pattern, traders buying at the low made money" |
| 9 | **50% Pullback Level** | ~50% of reviews | "50% pullback is a common resistance/support area" |
| 10 | **Measured Move (Leg1=Leg2)** | ~50% of reviews | "leg one, pullback, leg two measured move target reached" |
| 11 | **Support/Resistance Flip** | ~60% of reviews | "once support is broken, it becomes resistance" |
| 12 | **ADR Range Sustainability** | ~40% of reviews | "the market has already covered most of its ADR" |
| 13 | **Give Up Bar** | ~20% of reviews | "that's a give up bar, trapped traders are exiting" |

### 2.2 Brad's Decision Narrative Pattern

Brad's analysis follows an extremely consistent logic chain:

#### Core Decision Framework

```
1. Higher timeframe context → "Daily chart, market is in a [structure]"
2. Opening gap / price location → "Gap up/down, it's a bull/bear breakout"
3. Bar-by-bar: Who is trapped? → "Traders buying/selling here are trapped"
4. What is the dominant feature? → "Micro channel / breakout / trading range"
5. Is selling/buying pressure strong or weak? → "The selling pressure is/is not strong enough"
6. Is a second leg likely? → "Second leg up/down likely"
7. Always In direction? → "It's always in long/short"
8. Trade or not? → "Reasonable to buy/sell" or "Really not ideal"
```

#### Brad's Signature Reasoning Phrases

**Assessing buyer/seller presence**:
- "Probably buyers below [bar X]" — highest frequency phrase
- "Probably sellers above [bar X]" — highest frequency phrase
- "There might be more traders buying/selling here"

**Assessing whether an action is reasonable**:
- "Reasonable to buy/sell [bar X]" = actionable
- "Really not ideal" = not recommended
- "Low probability sell/buy" = low win rate
- "Better if you can [scale in / use wider stop / sell higher]" = there's a better approach

**Assessing reversal character**:
- "Minor reversal, probably just a pullback" = not enough to change direction
- "First reversal attempt is probably going to be minor" = first reversal usually fails
- "For a major reversal, you need consecutive big bear/bull bars breaking a significant trend line" = standard for major reversal

**Assessing traps**:
- "Traders [action] getting trapped" = core logic
- "Disappointed with their entry bar" = immediately adverse after entry
- "May use [bar X] to exit" = trapped traders will exit on retest
- "Three groups of trapped traders" = wrong direction / chased too late / exited too early

**Assessing day structure and sustainability**:
- "The market has already covered X% of its ADR" = range consumption assessment
- "No breakout until there's a breakout" = do not anticipate breakouts
- "Support became resistance" / "Resistance became support" = support/resistance flip
- "Actual risk is [X], not the initial risk" = actual vs. initial risk distinction
- "The second leg often takes longer than the first" = patience with second legs

### 2.3 Brad's Explicit "Do Not Trade" Scenarios

Based on 44 reviews, scenarios where Brad explicitly says "not ideal" / "would not" / "low probability":

| Do Not Trade Scenario | Brad's Logic | Frequency |
|-----------------------|-------------|-----------|
| **Counter-trend in a tight channel** | "selling a tight bull channel, low probability" | Very high |
| **Entering in the middle of a trading range** | "forcing you to enter in the middle of the range, not ideal" | Very high |
| **Selling at support / buying at resistance** | "selling at support / buying at resistance, not ideal" | Very high |
| **First reversal of a micro channel** | "micro channel, first reversal likely minor" | Very high |
| **Counter-trend when far from EMA** | "far below/above the EMA, not ideal to buy/sell" | High |
| **Chasing immediately after a big bar** | "big bar, forcing big risk, may attract profit-taking" | High |
| **Fourth leg after three pushes** | "three legs up/down, probably sellers/buyers above/below" | High |
| **"Bad" stop order signals** | "bad stop order buy/sell, probably [opposite] below/above" | High |
| **Stop orders in a tight trading range** | "stop order entry in the middle of a tight TR, not ideal" | Medium |
| **Accelerating late-stage channel legs** | "late leg, breaking below channel line, climactic, unsustainable" | Medium |
| **Chasing after >80% of ADR consumed** | "already covered most of the average daily range, limited room left" | Medium |
| **Treating deep pullback (>75%) as continuation** | "pullback is too deep, more like a TR forming than a pullback" | Medium |
| **Counter-trend after micro channel of 9+ bars** | "micro channel this long is very rare, pullback is coming, but first reversal still minor" | Medium |
| **Directional trade with only 1-2 bars today** | "not enough data to determine direction" | High |

### 2.4 Market Structure Vocabulary Patterns

Brad uses an extremely stable set of market structure classification language:

**Trend Assessment**:
- "Always in long/short" — ultimate directional statement
- "Tight bull/bear channel" = breakout on higher timeframe
- "Small pullback trending behavior" = very strong trend, can buy for any reason
- "The selling/buying pressure is weak/strong" — used multiple times daily

**Trading Range Assessment**:
- "Limit order market, sellers above, buyers below" — signature phrase
- "Big up, big down, probably a trading range" — big up big down = TR
- "It's forcing you to buy/sell in the middle of the range" — rejects middle-of-range entries

**Channel Assessment**:
- "Spike and channel, the channel will evolve into a trading range"
- "Broad bear/bull channel is basically a trading range tilted [down/up]"
- "Breaking above/below the channel line, climactic, probably profit-taking"

**Reversal Assessment**:
- "Minor reversal" vs "Major reversal" — the most critical distinction in daily reviews
- "For a major reversal: consecutive big trend bars + break of significant trend line"
- "Not enough selling/buying pressure for a major reversal"
- "Best case scenario for the bears/bulls is a trading range" — best outcome for counter-trend side

**Limit Order vs. Stop Order Market Identification**:
- Limit order market: overlapping bars, long tails, frequent reversals, dojis, "sellers above and buyers below"
- Stop order market: trend bars with small tails, breakouts, momentum, sustained direction
- The distinction determines entry method: limit orders in TR, stop orders in trends

**Probability Assessment**:
- "75% of the time" — probability of channel breaking opposite direction
- "About 25% chance" — probability of channel accelerating through
- "About 5 bars" — reversal window after channel line breakout
- "Small risk, big reward = low probability" — inverse relationship of risk/reward and probability

---

## III. Theory vs. Practice Cross-Reference

### 3.1 Concepts Appearing at High Frequency in Both Theory and Practice

These concepts appear at **high frequency in both** course theory and Brad's daily reviews:

| Concept | Theory Frequency | Practice Frequency | Cross-Reference Level |
|---------|-----------------|-------------------|----------------------|
| Second Leg | Core | Nearly every bar | **Very High** |
| Micro Channel | Core | Nearly every bar | **Very High** |
| Trapped Traders | Core | Nearly every bar | **Very High** |
| Always In Direction | Core | Daily | **Very High** |
| Breakout Point = Support/Resistance | Core | Daily | **Very High** |
| 80% Inertia Rule | Core | Daily (implicit) | **High** |
| Channel → Trading Range Evolution | Core | Daily | **High** |
| Measured Move (Leg1=Leg2) | Core | ~50% | **Medium-High** |
| EMA as Support/Resistance | Core | ~60% | **Medium-High** |
| Prior Day High/Low Magnet | Important | ~70% | **Medium-High** |

### 3.2 Concepts Important in Theory but Less Frequent in Practice

| Concept | Theory Status | Brad's Practical Use | Likely Reason |
|---------|-------------|---------------------|---------------|
| TBTL (Ten Bars Two Legs) | Reversal confirmation standard | Rarely mentioned directly | Brad uses "second leg" as substitute |
| 70% Channel Boundary Reversal Rule | Important probability | Occasionally mentioned | Absorbed into "channel line breakout reversal" phrasing |
| 75%/25% Channel Breakout Direction | Important probability | Occasionally mentioned | Absorbed into "most channels evolve into TR" |
| 40% MTR Success Rate | Important expectation management | Rarely cites specific number | Brad prefers describing "what the bears/bulls need" |
| Actual Risk Concept | Profit-taking framework | Occasionally mentions "one R" | Brad more commonly uses measured move |
| Gap = Breakout | Definitional concept | Mentioned every gap opening | Fully internalized as standard analytical language |
| Z-score | Supplementary tool | Mentioned once | Not a core price action concept |

### 3.3 Concepts Frequent in Brad's Practice but Not Systematized in Course Notes

| Concept | Brad's Usage Frequency | Notes |
|---------|----------------------|-------|
| "Probably buyers/sellers below/above" | Nearly every bar | Brad's real-time supply/demand assessment framework |
| "Bad stop order" = "Good limit order" | Very high | Poor stop order quality = good limit order opportunity |
| "Disappointed traders" | Very high | Immediately adverse after entry → creates opposite pressure |
| "The stop is far / big risk" | High | Brad's concrete risk-awareness phrasing |
| Buy/Sell Vacuum / Magnets | Medium-high | Price races quickly toward a magnet level; systematized magnet hierarchy in Section 1.5 |
| Opening Reversal | Medium | Fast move to a magnet in first 60–90 min → reversal; one of the most common intraday patterns |
| Final Flag | Low-medium | Pullback that looks like continuation but becomes start of reversal; appears after extended trends |
| Support/Resistance Flip | Very high | "Once support is broken, it becomes resistance" — traders who bought now looking to exit |
| ADR as sustainability check | Medium-high | Assesses how much of the day's range has been consumed |
| "No breakout until there's a breakout" | High | Do not anticipate — wait for actual confirmation |
| Give Up Bar | Medium | Climactic exit by trapped traders, often precedes a pause or reversal |
| Three Groups of Trapped Traders | Medium | Systematizes who is trapped and how they react |
| Nested Leg Counting | Medium | Counting legs within legs across multiple timeframes simultaneously |
| OO BreakOut Mode | Low | Consecutive outside bars; Al Brooks names this explicitly as a breakout mode pattern |
| ioi Pattern | Low | Inside-outside-inside sequence; compression-expansion-compression before breakout |
| Bull/Bear Surprise | Medium | Brad describes the effect ("surprisingly strong rally") without using the formal name |
| Pattern Confluence | High (implicit) | Brad routinely notes multiple patterns at one point ("Wedge and a Double Top") but doesn't name it as a rule |

---

## IV. Binary Decision Tree — Al Brooks Practical Framework

**Traverse from root to leaf. At each node, answer Yes or No. Do not skip nodes. Do not look ahead at signals before determining structure.**

### Layer 1: Data Gate

```
N0: Are there ≥3 bars on today's 5-minute chart?
├─ NO → ⚪ WATCH: Insufficient data. Provide daily chart context only.
│        "Only 1-2 bars today, structural information is extremely limited."
└─ YES → proceed to N1
```

### Layer 2: Structure Classification

```
N1: Is the market structure identifiable?
│   (Can you classify it as trend/channel/TR based on current evidence?)
├─ NO → ⚪ WATCH: "Structure is unclear, not suitable for trading."
└─ YES → proceed to N2

N2: Is there sustained directional movement?
│   (Consecutive trend bars + EMA acting as effective support/resistance?)
├─ NO → STRUCTURE = Trading Range (≥20 bars oscillating, heavy overlap)
│        → proceed to N4
└─ YES → proceed to N3

N3: Are pullbacks shallow?
│   (≤3 bars AND retracement <33% of the move?)
├─ YES → STRUCTURE = Tight Channel / Breakout
│         "Trade only with trend. Counter-trend is low probability."
└─ NO  → STRUCTURE = Broad Channel
│         "Primarily with trend. Can scalp counter-trend at extremes."

         → all paths converge at N4
```

### Layer 3: Always In Direction

```
N4: Is the Always In direction clear?
│   Check three factors:
│     ① Direction of most recent strong breakout
│     ② Direction of most recent micro channel
│     ③ Price above or below EMA
│   (Are at least 2 of 3 in agreement?)
├─ NO → ⚪ WATCH: "Direction is unclear. Wait for clarity."
└─ YES → Record direction (LONG or SHORT) → proceed to Veto Chain
```

### Layer 4: Veto Chain (any YES → immediate Watch)

```
V1: Is this trade counter-trend in a tight channel?
│   "Selling a tight bull channel is low probability."
├─ YES → ⚪ WATCH (counter-trend in tight channel)
└─ NO → V2

V2: Is price in the middle of a trading range?
│   (Not within the upper or lower 25% of the range?)
├─ YES → ⚪ WATCH (middle of range, no edge)
└─ NO → V3

V3: Is this selling at support or buying at resistance?
│   "Selling at support / buying at resistance, not ideal."
├─ YES → ⚪ WATCH (against support/resistance)
└─ NO → V4

V4: Is the stop distance too large?
│   (>30% of the current day's ATR?)
├─ YES → ⚪ WATCH (risk too large)
└─ NO → V5

V5: Is this chasing after a big bar or big gap?
│   (Entering immediately after a large-body bar with no pullback?)
├─ YES → ⚪ WATCH (chasing, wait for pullback)
└─ NO → V6

V6: Is this the first reversal of a micro channel?
│   "Micro channel, first reversal likely minor."
├─ YES → ⚪ WATCH (first reversal usually fails)
└─ NO → V7

V7: Have three pushes completed and this is a 4th leg entry?
│   "Three legs up/down, correction likely."
│   Also check for Final Flag: if a pullback here looks like a continuation flag
│   but breaks opposite → counter-trend entry with ~40% swing probability (TBTL target).
├─ YES → ⚪ WATCH (correction expected after 3 pushes; check for Final Flag reversal)
└─ NO → V8

V8: Is price far from EMA and this is a counter-trend trade?
│   "Far from the EMA, counter-trend is not ideal."
├─ YES → ⚪ WATCH (far from EMA, counter-trend)
└─ NO → V9

V9: Has >80% of the ADR been consumed today?
│   "Market has already covered most of its average daily range."
├─ YES → ⚪ WATCH (limited remaining room)
└─ NO → V10

V10: Is the breakout pullback depth >75%?
│    "Pullback is too deep — more like a TR forming, not continuation."
├─ YES → ⚪ WATCH (deep pullback negates breakout)
└─ NO → V11

V11: Is this chasing a micro channel that has lasted ≥9 bars?
│    "9-10+ consecutive micro channel bars is extremely rare."
├─ YES → ⚪ WATCH (micro channel at limit, pullback imminent)
└─ NO → V12

V12: Is the current period unfavorable?
│    (Within first 5 minutes after open OR last 30 minutes before close?)
├─ YES → FLAG: Period risk. (Does not terminate — downgrades confidence.)
└─ NO → proceed to Signal Quality
```

### Layer 5: Signal Quality Gates

```
S1: Are there trapped traders providing fuel for a second leg?
│   Three groups to check:
│     ① Wrong direction — will stop out, creating opposite pressure
│     ② Right direction but chased too late — will panic on pullback
│     ③ Right direction but exited too early — may re-enter at worse price
│   (Is at least one group clearly identifiable?)
├─ NO → ⚪ WATCH (no trapped trader fuel)
└─ YES → S2

S2: Is there a valid signal bar?
│   (Bull/bear reversal bar, breakout bar, or second entry signal?)
├─ NO → ⚪ WATCH (no valid signal)
└─ YES → S3

S3: Is the signal in the same direction as Always In?
├─ NO → ⚪ WATCH (signal contradicts direction)
└─ YES → proceed to Risk Assessment
```

### Layer 6: Risk Assessment & Trade Routing

```
R1: Is the reward-to-risk ratio ≥ 1.5:1?
│   (Target distance ÷ stop distance ≥ 1.5?)
├─ NO → ⚪ WATCH (insufficient reward/risk)
└─ YES → R2

R2: Is the structure Tight Channel / Breakout?
├─ YES → 🟩 ENTRY: Swing Trade Plan
│         ├─ Hold swing position
│         ├─ Scale out partial at 1× actual risk
│         ├─ Trail stop with trend (follow EMA or pullback lows/highs)
│         └─ Target: measured move (Leg1=Leg2) or prior day high/low
└─ NO → R3

R3: Is price at the upper/lower boundary of a trading range?
├─ YES → 🟨 ENTRY: Scalp Plan
│         ├─ Scalp to opposite boundary
│         ├─ Exit at 1× risk or opposite range boundary
│         └─ Target: opposite side of range
└─ NO  → 🟨 ENTRY: Reduced Size Plan
           ├─ Light position, exit entirely at 1× actual risk
           ├─ Do not add to position
           └─ Target: nearest measured move or EMA
```

### Scale-In Rules (when trapped after entry)

```
T1: Are you trapped in a trading range? (price went against you within a range)
├─ YES → Wide stop + scale-in → 80% chance of at least breaking even
│         ├─ Only scale in the original direction
│         ├─ Total risk after scale-in ≤ normal single-trade risk
│         └─ After scale-in, break even near original entry
└─ NO → (Trapped in a trend) → Stop out immediately. Do not scale in.
```

### Daily Structural Checklist (Pre-Tree Context Gathering)

```
Pre-market:
□ Daily chart structure? Trend / TR / Channel?
□ How far from EMA? Too far = likely pullback
□ Prior day bar type? Reversal / Breakout / TR?
□ Key support/resistance levels for today?

After open (first 30 minutes):
□ Gap direction and size? → Gap = breakout
□ Is the first bar a breakout or TR bar?
□ Has the opening range formed?
□ Bar 1 is NOT the day's high or low ~80% of the time

During session:
□ Current micro channel direction?
□ Which side has trapped traders?
□ Selling/buying pressure strength?
□ Have three pushes completed?

Before close (last 30 minutes):
□ Still in a trading range → most likely continues as TR
□ Around Bar 72 is the last reasonable entry
□ Huge bars near close = profit-taking signal
```

---

## V. Core Probability Reference Table

| Rule | Probability | Application |
|------|------------|-------------|
| First reversal in a trend fails | ~80% | Do not trade first counter-trend reversal |
| Breakout in a trading range fails | ~80% | Do not chase breakout, wait for failure then reverse |
| Channel breaks opposite direction (not accelerating) | ~75% | Bull channel most likely breaks downward |
| Channel breaks same direction (accelerating) | ~25% | Rare, do not bet on channel acceleration |
| Reversal within 5 bars after channel line breakout | ~75% | Channel line breakout = profit-taking signal |
| Good wedge reversal produces a swing trade | ~40% | Even good setups don't warrant full position |
| Wide stop + scale-in at least breaks even | ~80% | Management plan when trapped in a TR |
| Strong breakout gets a second leg | >80% | Brad's most core trading logic |
| Tight channel is a higher TF breakout | ~100% | Never counter-trend, only look for with-trend |
| Intraday Bar 1 is not the high/low of day | ~80% | Do not draw directional conclusions from Bar 1 |
| Big gap down → day type distribution | ~60% TR / ~20% continuation / ~20% reversal | Do not assume trend after a big gap; most likely outcome is a trading range |
| Micro channel 9-10+ bars must pull back | ~90%+ | Extremely rare for micro channel to extend beyond 9-10 bars without correction |
| Breakout pullback >66-75% of breakout → probably TR or reversal | ~70% | Deep pullback negates breakout; treat as TR formation, not continuation |
| Wedge correction duration ≈ half the wedge's bar count | Rule of thumb | After a wedge reversal, expect the correction to last about half as many bars as the wedge itself |
| Second leg takes more time/bars than first leg | Common | Be patient — the second leg often develops more slowly than the first |
| MTR / Final Flag produces a swing trade | ~40% | Even well-formed MTRs only produce a swing ~40% of the time; minimum confirmation is TBTL (Ten Bars Two Legs) |
| Opening Reversal after fast move to magnet | Very common | One of the most frequent intraday patterns; fast move to prior day H/L in first 60–90 min → exhaustion → two-legged correction |

---

## VI. Brad's Key Quotes and Core Beliefs

> **On trapped traders**:
> "The dynamic of trapped traders is what produces second legs."

> **On risk/reward**:
> "Whenever you have good risk reward, the opposite side of your trade has high probability."
> "There's no such thing as a perfect trade. You don't get small risk, big reward, AND high probability."

> **On tight channels**:
> "A tight channel is a breakout on a higher time frame. It's better to trade only in the direction of the breakout."

> **On trading ranges**:
> "Limit order market. Sellers above and buyers below."

> **On reversals**:
> "For a major reversal, you need consecutive big trend bars breaking a significant trend line."
> "Best case scenario for [the counter-trend side] is a trading range, not an opposite trend."

> **On strong trends**:
> "When it's a strong trend, you can buy for any reason. Most important thing is not to sell."
> "Counting legs in the direction of the major trend is less important than counting legs in a trading range."

> **On channel evolution**:
> "Spike and channel — the channel will probably evolve into a trading range, then test the start of the channel."

> **On stops**:
> "If your protective stop is at an area of resistance, it doesn't make sense — you want to sell at resistance, not buy."

> **On market oscillation**:
> "The market goes from +1 to 0 to -1. It can't go from +1 directly to -1 — it has to go through 0 first."

> **On patience with second legs**:
> "The second leg will probably take longer than the first. Be patient."

> **On breakout anticipation**:
> "No breakout until there's a breakout."

> **On ADR and sustainability**:
> "The market has already covered most of its average daily range — there's not much room left."

> **On position sizing (High Dive Analogy)**:
> "It's like a high dive — you can do a cannonball or you can do a dive. The pool doesn't care."

> **On support/resistance flip**:
> "Once support is broken, it becomes resistance. Traders who bought there are now looking to get out."
