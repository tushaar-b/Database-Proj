# Trend-aware recommendation methodology

Method version: **`risk_momentum_v1`**. Comparator formula: **`risk_only_252_v1`**. These are transparent research heuristics, not evidence of improved investment performance.

## Investigation: why Titan was recommended

Read-only inspection of saved Titan recommendations found a pending batch created **23 October 2026 at 11:01:29 UTC**, plus a superseded batch from earlier that day. Their saved explanations identify the newer risk-aware engine: 252 returns, aggressive preference, a 0.25 risk penalty, inverse-volatility sizing, whole-share budgeting and a yfinance quotation. This was not the old fixed three-stock algorithm.

The saved explanation reported 25.6% annualized arithmetic average return, 23.5% annualized volatility, 3.14% one-day historical CVaR95 and zero saved exposure to its sector. Those statistical inputs came from `daily_market_quote`, whose Titan observations stopped on **19 October 2026**, while the quoted unit price came from yfinance on **23 October**.

The old score was `mean_daily_return − a × (daily_volatility + daily_CVaR95)`, with `a = 0.75 / 0.50 / 0.25` for conservative/moderate/aggressive preferences. Recent negative days could affect the arithmetic mean, sample volatility and loss tail **indirectly**, but there was no explicit recent-return or moving-average term. Annualized values appeared in prose; they were not mixed into the daily score. Sector exposure was the first sorting key, so a lower-exposure sector could take priority over a stronger score in a more exposed sector. One security per sector and at most three ideas were selected, subject to whole-share affordability.

Viewing the page returns saved rows. It does not regenerate the batch, so an earlier saved pending decision can remain visible after conditions change. The saved Titan explanation proves which engine and dated evidence it used. Its exact original relative position against every alternative cannot be reconstructed: older batches did not store their complete candidate universe.

A separate, genuine Yahoo observation inspection during this implementation found Titan completed prices through **23 October 2026**: R20 approximately **−11.8914%** from 23 September, R60 **−11.3409%** from 28 July, adjusted close **₹4,299.700195**, MA20 **₹4,513.830005**, MA50 **₹4,816.508008**. These current observations are not backfilled into the old decision. Under the defaults below they give five negative signals and Strong Negative Momentum. No recommendation was generated or accepted by the implementation inspection.

## Daily data and windows

- The shared yfinance service now supplies both ranking statistics and momentum from the **same completed adjusted-price series**. New ranking inputs no longer depend exclusively on the stale database window.
- Request bounded daily history (`auto_adjust=False`), exclude the developing current daily candle until the provider's session end plus 15 minutes, normalize dates, and keep the latest **253 adjusted closes**, yielding up to **252 simple daily returns**.
- Baseline eligibility requires at least **120 returns / 121 consistent adjusted closes**, positive finite prices and nonzero sample volatility. A missing/invalid adjustment within that ranking window is not substituted with raw Close or silently skipped. Such candidates receive an explicit data-exclusion reason in the batch snapshot.
- R20 requires 21 adjusted closes; R60 requires 61. MA20 requires 20, MA50 requires 50. The complete trend classification requires all five indicators, hence at least 61 valid completed adjusted observations.
- R20 = `P[t] / P[t−20] − 1`. R60 = `P[t] / P[t−60] − 1`. These are fractional returns internally and percentages in the UI.
- MA20 = arithmetic mean of the most recent 20 closes, including `P[t]`; MA50 uses 50. They are INR prices on the same adjusted basis.
- No intraday quotation is inserted into historical returns, moving averages or momentum. Current affordability still uses a separately timestamped latest quotation.
- Yahoo adjustment conventions are source-attributed, not independently guaranteed. Existing PostgreSQL prices, corporate-action records and portfolio-risk definitions are not rewritten.

## Freshness and missing data

The shared history cache is reused by Stock Intelligence and recommendations. Bounded network retrieval uses at most four provider workers; PostgreSQL connections are not shared across worker threads. Provider failures back off and retain genuine cached history, then dated database fallback. Crossing the provider's completed-session boundary refreshes an otherwise unexpired cache, so a newly completed daily bar is not hidden by the hourly TTL.

A momentum classification is usable only for a valid, available yfinance daily series. It is marked unavailable/stale when adjusted inputs are insufficient/invalid, normalization discarded rows, dates duplicate, the daily and provider last-trade dates disagree, observations are from a fallback, or the last observation is older than the configurable **4 calendar days**. An unexplained gap exceeding **7 calendar days** in recent observations requires review. These conservative age/gap checks are configurable and are not an authoritative exchange calendar; unusually long closures can be marked stale. Missing signals are `null`, never zero or neutral.

Dated numeric indicators can still be shown descriptively with their real observation date, but their current classification remains Unavailable. An explicit uncertainty charge below accounts for missing trend evidence; it is not represented as a measured negative return. If no sufficiently valid baseline window exists, the security is excluded for data insufficiency rather than given fabricated statistics.

## Classification criteria

Five votes describe:

1. R20 direction: positive above **+1%**, negative below **−1%**, otherwise approximately flat.
2. R60 direction: positive above **+2%**, negative below **−2%**, otherwise approximately flat.
3. Price / MA20 − 1.
4. Price / MA50 − 1.
5. MA20 / MA50 − 1.

The three moving-average ratios use a **±0.5% tolerance**. Positive means above, negative below, and the band means near the average. Ratios without sufficient data remain unavailable.

Categories, evaluated in this order:

- **Strong Negative Momentum:** R20 ≤ −8%; at least four negative votes; price below MA50 and MA20 below MA50 beyond tolerance.
- **Negative Momentum:** at least three negative votes, plus R20 below −1% or R60 below −2%.
- **Positive Momentum:** at least three positive votes, R20 above +1%, and R60 not below −2%.
- **Neutral or Mixed Momentum:** all required evidence exists, but the preceding conditions do not apply.
- **Unavailable:** freshness or sufficiency requirements fail. A descriptive observed classification, if possible, is kept separately from a usable current assessment.

The tolerance bands damp small descriptive reversals; the 8% threshold distinguishes a pronounced monthly decline from the 1% flat band and requires corroboration. These numbers are configurable research choices, not fitted or validated predictive thresholds. Vote counts, gap/age rules and penalty parameters are captured with every new batch.

## Scoring units and momentum penalty

Let `r` be simple daily returns over the same up-to-252-return window. Preserve:

```
mean = arithmetic mean(r)
sigma = sample standard deviation(r), using n−1
q05 = linear 5th percentile(r)
CVaR95 = max(0, −mean(r where r ≤ q05))
baseline = mean − a × (sigma + CVaR95)
```

VaR95 = `max(0, −q05)` is recorded for inspection. It does not introduce a new candidate-level hard limit; existing portfolio VaR/volatility/HHI feedback and sector restrictions remain unchanged. CVaR is a ranking factor where no separate candidate constraint is configured.

Convert negative momentum into **daily fractional-return equivalents**, not arbitrary percentage-point deductions:

```
d20 = max(0, −expm1(log(1 + R20) / 20))
d60 = max(0, −expm1(log(1 + R60) / 60))
d50 = max(0, −expm1(log(P / MA50) / 50))
z[i] = min(3, d[i] / sigma)
weighted_severity = 0.50*z20 + 0.30*z60 + 0.20*z50
agreement = 1 + 0.25 × negative_votes / 5
severity = weighted_severity × agreement
penalty = lambda[tier] × sigma × severity
updated_score = baseline − penalty
```

`d50` is a documented heuristic: distribute the price/50-session-average shortfall over a 50-session horizon. It is not an estimate of an actual future return. Normalize the three nonnegative weights to sum to one if configuration changes. Components are capped at three daily-volatility units before aggregation; the agreement multiplier can lift the aggregate above three.

This scale matches the original daily mean/risk score. The reported annualized average (`mean × 252`) never enters the daily ranking as a percentage. Recent-month decline has the greatest explicit weight; corroborating signals strengthen the penalty. Positive momentum receives no artificial bonus. A small negative move inside a classification flat band can still receive a small continuous penalty.

Default momentum `lambda`:

| Preference | Momentum weight | Original baseline risk aversion |
| --- | ---: | ---: |
| Conservative | 0.75 | 0.75 |
| Moderate | 0.50 | 0.50 |
| Aggressive | 0.25 | 0.25 |

These default strengths align with the existing allocation-capacity complement, while remaining separately configurable. For the same asset, conservative investors receive a stronger momentum penalty. Falling prices are not assumed to create a buying opportunity.

When trend evidence is unavailable, set **measured momentum penalty unavailable** conceptually and apply a separately typed **data-quality uncertainty penalty**: `lambda × sigma × 0.25`. The stored `penalty_type` distinguishes this charge from measured momentum. Raw missing returns are never converted to zero. The UI and explanation disclose the missing evidence and the exact charge.

## Candidate ordering and financial safeguards

Sorting remains deterministic: sector weight ascending, then updated daily score descending, then ticker. Keep one security per sector and at most three selections. The penalty lowers a weak candidate's score against comparable alternatives, but **does not ban declines** and does not override the existing sector-priority rule.

Preserve held-security exclusion, blocked sectors, investor preference, investable surplus/reserve/capacity policy, inverse-volatility sizing, whole-share floors, total-budget checks and prior rejection/acceptance awareness. Current quotations remain separate from adjusted historical closes. No holdings, cash or transactions change when rankings refresh.

Legacy pending recommendations lack recorded momentum evidence and are labelled accordingly. Acceptance requests a new trend-aware batch first. New acceptance retains current-price significance/freshness and saved batch-budget revalidation, and also checks that the recorded adjusted history hash, trend-data status and policy are still reproducible. Changed completed history or changed policy requires Check for updates; original recorded amounts and explanations remain immutable. Acceptance records intent only.

## Fingerprints and research reproducibility

The methodology version, complete momentum policy, recent-return bands (default **0.5 percentage point**), moving-average relationships/classification, last observation date, history quality, baseline ranking inputs and exact completed-window price hash contribute to freshness. Quote polling timestamps/history fetch times are omitted. Existing price bands, whole-share affordability and risk-policy fingerprints remain. Polling does not generate batches; the explicit generation action reuses unchanged inputs.

A new completed daily observation, adjusted-history revision, meaningful signal change, policy/configuration change or methodology upgrade can invalidate a batch. Exact historical price revisions intentionally invalidate the research input hash even if a return band does not change. Intraday quote noise is still governed by the existing price-band/whole-share rules.

Nullable JSONB fields added by **only migration 008**:

- `recommendation_batch.ranking_snapshot`: frozen candidate universe, each candidate's exact adjusted dates/prices, metrics, pre/post scores, penalty components, policy, data exclusions, financial/sector context, selection order and actual recorded affordable recommendations/costs.
- `recommendation_log.ranking_evidence`: selected candidate's recorded trend, baseline/adjusted scores, penalty, risk tier, source/windows, quote basis, allocation budget and hash linking to the batch's frozen prices.

Old rows remain null; no backfill or rewriting of old decisions was performed. Apply `db/migrations/advisory/008_market_trend_evidence.sql` alone when deploying this change to another existing database. It was applied to this local advisory database with lock/statement timeouts. No risk-database migration or historical-price update was needed.

Owner-authenticated research endpoint: `GET /recommendations/{user_id}/batches/{batch_id}/evidence`. It filters by both authenticated user and batch ownership. Existing sessions/CSRF/ownership protections remain. New batch/record timestamps use PostgreSQL `clock_timestamp()` after data retrieval, so transaction-start timestamps cannot predate observations fetched during a long generation request. Captured runtime versions (Python, NumPy and yfinance) accompany the frozen inputs; existing record timestamps are not changed.

The comparator baseline is evaluated on the **same freshly captured adjusted series** for future paired research. It is not identical to a past batch that used an older database window. Snapshots preserve what was observed at the new decision time, avoiding later provider revisions silently changing its evidence. This is not a point-in-time historical backtesting archive: using today's retroactively adjusted Yahoo history to simulate older decisions would need separate look-ahead/corporate-action controls. No performance improvement, return forecast or loss reduction has been established.

## UI integration

- Compact table badge: Recent weakness, Positive trend, Mixed trend, Trend data limited, or Trend not assessed for legacy rows. No long paragraph was added to rows.
- View Details: **Recent Market Trend**, actual recorded R20/R60/MA20/MA50/date/basis, relationship descriptions, baseline/penalty/adjusted score and expandable methodology. The saved full explanation remains verbatim.
- Stock Intelligence Overview/Historical Performance: current historical trend panel and a comparison with the selected-window statistics. Current trend is independent of chart range.
- Price charts: gold MA20 and dashed teal MA50, each with an accessible show/hide checkbox and hover values. Context preceding the visible range is included. Overlays follow the chart's displayed adjusted/raw basis; the trend assessment always uses adjusted closes and labels unavailable adjustments.
- Recommendation Reasoning: saved trend evidence and current trend assessment shown separately. Legacy rows never acquire a fabricated historical trend.
- No landing-page, intro, authentication, onboarding, portfolio-management or dashboard redesign.

## Files changed

- `backend/market_trends.py` (new): classification, normalized penalty, baseline metrics, evidence and explanations.
- `backend/config.py`, `.env.example`: configurable research policy.
- `backend/market_data.py`: shared completed-history batching, date/normalization quality, cache completion-boundary freshness.
- `backend/routers/recommendations.py`: latest adjusted ranking inputs, penalties/signatures, evidence persistence, acceptance revalidation and owner-scoped research read.
- `backend/stock_analytics.py`: adjusted trend panel data and moving-average chart series with preceding context.
- `backend/routers/intelligence.py`: recorded recommendation evidence and methodology-refresh warning.
- `db/migrations/advisory/008_market_trend_evidence.sql` (new): two additive nullable JSONB columns.
- `frontend/src/components/RecentMarketTrend.jsx`, `.css` (new): badges, accessible evidence panel and explanations.
- `frontend/src/components/RecommendationTable.jsx`: compact badge and recorded-trend detail section.
- `frontend/src/StockIntelligence.jsx`: current/saved panels and optional moving-average overlays.
- `frontend/src/WorkspaceApp.jsx`: methodology-upgrade notice and updated recommendation description.
- `docs/RECOMMENDATION_TRENDS.md`, `docs/STOCK_INTELLIGENCE.md`: methodology, investigation and manual checks.

## Manual verification and limitations

No recommendation generation/acceptance, application automated tests, browser automation, Pytest, Vitest, Playwright or regression suite was executed. Verification consists of source inspection, read-only saved-evidence/schema queries, genuine Titan daily-observation inspection, the isolated additive schema change, Python source parsing and frontend production compilation. These do not constitute manual application verification.

Suggested manual checks:

1. Open the existing Titan decision: it keeps its old explanation and displays Trend not assessed. Check for updates should create a versioned new batch rather than silently rewriting it.
2. Inspect Titan or any current declining stock: actual numeric indicators/date and classification should agree with completed daily chart observations. Do not expect a forced different stock list.
3. Open View Details: verify saved penalty, risk preference and original/current evidence separation. Compare Overview and Recommendation Reasoning in Analyse Stock.
4. Toggle MA20/MA50 at 1M/3M/1Y; curves should use prior context and follow the displayed price basis. Raw chart selection must not turn raw Close into adjusted momentum.
5. Recheck unchanged inputs: expect reuse. A new completed session, material price/share-affordability change or changed policy should permit a new batch, preserving accepted/rejected/superseded history.
6. Simulate provider unavailability through normal local configuration/network conditions: expect explicitly dated/unavailable trend evidence and the disclosed uncertainty charge, never neutral/zero missing momentum.
7. Verify available whole-share costs, budget, restrictions, owner isolation and acceptance intent-only behavior remain intact. Changed historical evidence should request regeneration.
8. Use the owner-scoped batch evidence endpoint to inspect frozen candidate prices, scores and configuration. Reproduction should use that snapshot rather than later Yahoo history.

Remaining limitations: heuristic thresholds/weights require sensitivity analysis and controlled research comparisons; sector priority can still prefer a weak stock in a less-exposed sector; calendar-age/gap limits are conservative; provider access/delay/adjustment conventions and legacy fallback provenance remain limitations; old batches cannot be fully reconstructed because they lack snapshots. No benchmark-based prediction or valuation model was introduced.

No commit created. Suggested commit title: `Improve recommendations with market trends`.
