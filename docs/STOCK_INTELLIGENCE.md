# IntelliVest Stock Intelligence — Yahoo Finance data

The application uses **yfinance as its only external price/history source**. React communicates through authenticated FastAPI endpoints. PostgreSQL risk/advisory data, user sessions, CSRF, ownership, holdings, cash and ledger records are preserved. No new SQL migration is required.

## 1. Original NTPC HTTP 500 and fix

The existing FastAPI process log identified this exact error while serializing the NTPC Stock Intelligence response:

```
TypeError: 'numpy.bool' object is not iterable
TypeError: vars() argument must have __dict__ attribute
ValueError: [TypeError("'numpy.bool' object is not iterable"), TypeError('vars() argument must have __dict__ attribute')]
```

The histogram expression `p05 is not None and edges[i] <= p05` produced a NumPy boolean. It was neither a missing credential nor an absent optional table. It now explicitly returns Python `bool`. `json_native()` also converts nested NumPy scalars to native Python values and nonfinite floats to `None` at the analytics/response boundary.

Ordinary provider failures are handled inside the shared service, preserving stock identity, cached/database prices and available historical metrics. Unexpected errors log sanitized exception types and source-code locations without account IDs, credential values or provider cookie payloads.

## 2. Obsolete integration removed

Removed the former REST/authentication client, account-token and display-gate configuration, instrument mapping, market-status/timing calls and provider-specific UI choices.

Removed exclusive files:

- `backend/data/upstox_instruments.json`
- `etl/sync_upstox_daily.py`
- `db/migrations/risk/004_provider_daily_candle.sql`

Before removal, a read-only PostgreSQL query returned `NULL` for `to_regclass('public.provider_daily_candle')`, confirming that the optional migration had not been applied. No table was dropped. No historical/CVaR migration or financial record was changed. There was no provider SDK dependency to uninstall.

## 3. Shared yfinance service

`backend/market_data.py` owns symbol validation, quotes, historical observations, caching, receipt/observation times, provider failures and portfolio valuation. Routers do not call Yahoo independently.

It reuses the installed yfinance dependency (version 1.7.0 at implementation). Supported `Ticker.history()` calls use `auto_adjust=False`, daily intervals, genuine source metadata and bounded timeouts. The installed version returns metadata as a `Mapping`, which is supported without assuming a concrete dictionary.

A proposed `.NS` symbol is accepted only after Yahoo metadata confirms the exact symbol, INR currency, NSE exchange and equity instrument type. No ambiguous company-name substitution is used. The 49 unambiguous local NSE candidates were validated with genuine Yahoo responses. The dated coverage record is `docs/yfinance-symbol-coverage.json`; it is documentation, not a production price source.

The legacy `TATAMOTORS` entry remains unresolved. [NSE's symbol-change circular](https://nsearchives.nseindia.com/content/circulars/FAOP70882.pdf) and the [company's demerger communication](https://links.sgx.com/FileOpen/NSEBSESHAREHOLDERINTIMATION.ashx?App=Announcement&FileID=863553) establish that the old listed entity became passenger-vehicle `TMPV`, while the commercial-vehicle business became a separately listed entity. Replacing a legacy holding/history with either business without corporate-action reconciliation would be misleading. No symbol, quantity, average cost or UUID was changed. Its dated database fallback remains viewable, and unresolved listings are excluded from newly generated purchase ideas.

## 4. Latest-price behavior and freshness

The normalized quote contains internal UUID, company/ticker/sector/exchange, INR price, valid previous daily close, change and percentage change, source, actual provider observation timestamp or daily date, receipt time, status and `fresh_enough_for_operation`.

Statuses:

- `latest_intraday_observation`: price paired with Yahoo's actual `regularMarketTime`; always labelled potentially delayed, never live.
- `last_market_close`: latest completed daily observation, with its actual trading date. No invented closing timestamp.
- `latest_daily_observation`: a developing daily bar without sufficient intraday timestamp evidence; labelled incomplete/delayed and not eligible for acceptance.
- `historical_fallback`: previous valid cached quotation after a failure/expiry, or PostgreSQL close with its real date and provenance warning.
- `unavailable`: no suitable price evidence.

Today's developing daily candle is excluded from statistical history. Completion uses Yahoo's reported regular-session end plus a 15-minute buffer, including provider-reported special schedules; no normal weekday-only holiday calendar is asserted.

Quotations are shared across investors and fetched only for the requested securities, in bounded groups of four workers. Quote cache/refresh defaults to five minutes; historical requests cache for an hour. Refresh buttons and existing visible-tab polling respect the same cache/backoff. Symbol failures are independent. Rate limiting backs off; network/empty/invalid data return dated fallback instead of zero or a page-wide provider HTTP 500.

Freshness for intent acceptance requires a provider-validated quote and:

- timestamped intraday evidence no older than the configured 30 minutes; or
- a daily close matching Yahoo's last trading date, outside the reported current session, no older than the configured seven calendar days.

This allows weekends/holidays without pretending that a closing price is an executable live price. Expired/failed retrievals lose acceptance eligibility. These limits are configurable and are local research safeguards, not trading guarantees. If provider session metadata is insufficient, the service stays conservative.

## 5. Historical observations and statistics

The default Stock Intelligence source is genuine yfinance completed daily history. Ranges remain 1M, 3M, 6M, 1Y and All (capped at ten years). Bounded provider requests are cached; the page does not download full history on every render.

Adjusted mode uses Yahoo `Adj Close` consistently over the selected window, with `auto_adjust=False`. If any selected adjusted observation is unavailable, the whole window uses raw `Close` with an explicit warning. Raw mode always uses `Close`. Adjusted and raw observations are never mixed row by row. Yahoo's corporate-action conventions are attributed, not independently guaranteed. Raw prices can retain source-specific corporate-action effects and are not represented as dividend-adjusted total returns.

If Yahoo history fails, use the last genuine cached history, then dated PostgreSQL history. Legacy database provenance remains explicitly provisional. No new market observations are written to PostgreSQL, and existing risk history is not silently rewritten or extended by an intraday observation.

Retained calculations: period return, close high/low, mean/median/best/worst daily return, positive/negative/flat days, sample daily/annualized volatility, historical 95% one-day VaR/CVaR, annualized Sharpe, maximum drawdown, downside deviation, 30-return rolling volatility and return histogram. Existing formulas are preserved. Tail metrics/Sharpe require 60 returns. Sharpe uses the configurable 4% annual risk-free assumption and 252-session convention. Constant/negligible volatility produces an unavailable Sharpe rather than division by zero. Empty, invalid, insufficient and missing-adjusted-price datasets have explicit statuses. Beta remains unavailable without a verified benchmark.

The portfolio PostgreSQL risk functions, historical ranking factors and original CVaR methodology remain unchanged.

## 6. UI and portfolio behavior

All five Stock Intelligence sections, existing charts/explanations, recommendation details drawer, workspace navigation and editorial design remain. The daily-series choice now selects adjusted or raw Yahoo observations. Prices show source and IST observation/date. API errors, provider fallback, unresolved symbols and insufficient history have distinct explanatory text.

Overview, Holdings, current allocation, Stock Intelligence and recommendations share the service. Position value = saved shares × latest valid price. Gain/loss = shares × (price − saved average cost), before fees/tax. Total portfolio value includes cash separately. Missing positions do not silently become zero; complete totals/weights become unavailable, with a labelled priced subtotal and incomplete status. Existing explicit imported/simulated transaction flows are preserved; a price refresh never records a transaction.

Hypothetical impact remains clearly labelled and includes saved proposed shares, current estimated cost, invested-value/sector/HHI changes, portfolio cash after and remaining evaluated cashflow investable buffer. Original recommendation context remains separate from current market conditions.

## 7. Recommendation safeguards retained

Historical return/downside ranking, volatility, holding exclusion, sector eligibility, risk preferences, inverse-volatility sizing, surplus policy, batch fingerprints/reuse, rejection history, superseding and closed-loop feedback remain in place. Prices now come from the shared yfinance service; no old deterministic three-stock algorithm was restored.

Fingerprint logic recognizes valid Yahoo intraday/closing evidence, price significance and whole-share affordability changes. Saved recommendation amounts, quantities and explanations do not change on quote refresh. Acceptance revalidates recent evidence, material price change and the total saved batch cost against the original budget/buffer. Unavailable/stale evidence produces a specific refresh/revalidation message. Acceptance still records intent only. It never executes a brokerage order.

## 8. Configuration

No account, token, secret or new database is required. `.env` and `.env.example` no longer contain the removed provider's settings. yfinance is the only supported external provider.

```
MARKET_DATA_PROVIDER=yfinance
MARKET_QUOTE_REFRESH_SECONDS=300
MARKET_QUOTE_STALE_SECONDS=1800
MARKET_CLOSE_MAX_AGE_DAYS=7
MARKET_HISTORY_CACHE_SECONDS=3600
MARKET_PROVIDER_BACKOFF_SECONDS=300
YFINANCE_TIMEOUT_SECONDS=8
```

Existing PostgreSQL connection/security settings and configurable recommendation significance/risk-free-rate assumptions remain.

[The yfinance documentation](https://ranaroussi.github.io/yfinance/) describes the library as unaffiliated with Yahoo, intended for research/education, and notes personal-use restrictions on Yahoo's data API. The application remains a local academic research demonstration, not an official exchange feed. Data can be delayed or unavailable, and caching does not grant redistribution rights.

## 9. Data retrieval and limitations

Genuine yfinance retrieval succeeded for NTPC and all 49 unambiguous local NSE candidates, with metadata-confirmed INR/equity identities and actual dated observations. NTPC also returned 495 completed daily observations from 23 October 2024 through 22 October 2026, all with adjusted closes; today’s developing bar was excluded. See the timestamped coverage record. This establishes provider retrieval, not an automated UI/application verification or a real-time feed guarantee.

Limitations: `TATAMOTORS` requires corporate-action reconciliation; Yahoo may throttle or fail; legacy historical provenance needs audit; no benchmark beta; in-memory caches are intended for the existing local single-process application; acceptance may require regeneration when old recommendations were sized at different historical prices. Existing public landing-page research data and its conservative dated labels are preserved.

## 10. Files modified in this replacement

- `backend/market_data.py` — yfinance-only service, validation, caches, quotes/history and valuations.
- `backend/config.py`, `.env`, `.env.example` — remove broker configuration; Yahoo freshness/cache settings. `.env` stays ignored and is not committed.
- `backend/stock_analytics.py` — actual NumPy serialization fix, response normalization, robust genuine-history calculations.
- `backend/routers/intelligence.py` — no optional-table dependency; adjusted/raw history and JSON-native responses.
- `backend/routers/recommendations.py` — provider-neutral freshness, unresolved-listing eligibility and batch-budget checks; newer ranking retained.
- `backend/routers/rebalance.py` — existing simulation uses Yahoo evidence safeguards.
- `frontend/src/StockIntelligence.jsx` — source choices/statuses and useful insufficient-history/API messages; all sections preserved.
- `docs/STOCK_INTELLIGENCE.md` — replaces obsolete provider instructions with this report.
- `docs/yfinance-symbol-coverage.json` — dated genuine symbol-coverage evidence, never loaded as application prices.

Removed the three exclusive files listed above. Other workspace files/features were preserved. No original CVaR migration or database record was modified.

## 11. Verification and Git

Application testing remains manual. No Pytest, Vitest, Playwright, browser automation, automated regression/E2E suite, fake observations or production price inserts were used. Permitted checks consist of source parsing, frontend production compilation, read-only schema inspection and genuine provider data retrieval. These checks are not represented as proof that the authenticated NTPC page has been manually verified.

Repository publication was authorized separately. Changes are published from an isolated checkout, preserving the destination history and excluding unrelated home-directory files. Commit title: `Restore Yahoo Finance market data`. See Git history for the final commit hash.
