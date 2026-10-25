# Phase 9 data audit — 25 October 2026

All findings are exploratory comparisons of nine synthetic profiles sharing historical market paths. Previously inspected observations, overlapping windows, surviving-security selection and current sector labels prevent independent-validation or population-level claims.

## Frozen equity evidence

The required run03, diagnostic, Phase 8 and original conference-draft paths exist. Original data SHA256: `5d1564c142b835cba08675c89e4277486eb10cf7639fa586a643502a598a0102`. Source files and application files are recorded before experiments in PRESERVED_HASHES.json; 854 files are unchanged. Original V1 matches 36 accounts and V1/V3/V4 match all 108 Phase 8 account/window summaries at rtol 1e-10, atol 1e-8. Policies were imported unchanged.

The retained Yahoo/yfinance dataset has 57,400 rows, 40 securities, 1,435 common sessions, 1 January 2021–22 October 2026. Duplicate security/date keys: 0. Per-security identifier, sector, observation, dividend, split and provider first-trade metadata are exported in historical_universe_metadata.csv. Provider firstTradeDate is not an actual exchange listing certificate. No exchange-certified listing dates, delisting history or historical sector classifications were recovered. All retained securities have observed pre-decision history and cached eligibility requires at least 120 completed returns. Historical signals exclude later observations, conditional on this fixed surviving universe.

Adjusted close drives scores and covariance. Execution and account valuation use split-reconstructed nominal close, explicit split share changes, cash in lieu and dividends on ex-date rather than payment date. This inherits action and dividend-timing limitations. Earlier six-date NSE corroboration covers 240 retained stock observations; it does not independently verify every price, adjusted factor or corporate action. Repeated Yahoo downloads are not independent corroboration. No original data or PostgreSQL table was written.

Ten excluded symbols and exact reasons remain in research/data/2026-10-23/exclusions.json: TATAMOTORS, ITC, RELIANCE, BHARTIARTL, HDFCBANK, SHRIRAMFIN, BAJAJFINSV, BAJFINANCE, GRASIM and TRENT. These exclusions themselves can affect results; the retained universe is not historical NIFTY 50 membership.

## NIFTY benchmark acquisition

NIFTYBEES.NS history: 1,236 provider rows, 2021–2025, separately saved with raw hash `1a460cd650d0f152f694da87816330ea42275fff76c2a849ce2f9151d90c8160`. Six sampled closes match independent NSE bhavcopy records. No reported distributions or splits occur in this acquired interval; all nonmissing adjusted closes equal close. The provider had one missing OHLC bar on 24 October 2025. The actual NSE bar was acquired from the alternate official archive and inserted only into a new normalized benchmark file. ETF_CORRECTION.json retains the actual close, source URL and hash. No interpolation, forward-fill, invented action or synthetic market value is used. All required 2021–2025 common sessions now have positive finite executable closes. Validation checks and raw zip files are retained.

[Nippon India’s scheme documentation](https://mf.nipponindiaim.com/FundsAndPerformance/Pages/NipponIndia-ETF-Nifty-50-BeES.aspx) identifies this ETF as a NIFTY 50 TRI tracking fund and permits exchange trading in units. Fund expenses and historical tracking effects are embedded in market prices; simulated fees/slippage are additional. Market price can differ from NAV. Tracking error against TRI cannot be quantified without the daily TRI series. Provider-reported zero distributions is not an independent distribution audit. ETF look-through sector weights are unavailable and sector HHI is marked unavailable.

The official daily TRI endpoint returned HTTP 401 for both documented payload attempts; the historical-data page also timed out. Requests and raw responses are saved. No NIFTY price index was substituted and no index points were purchased. [NSE distinguishes dividends in TRI from price-index movements](https://www.nseindia.com/static/products-services/indices-total-returns-index). The non-executable TRI reference is therefore unavailable; the executable ETF is evaluated separately.

## Point-in-time membership investigation

Official source: https://archives.nseindia.com/content/indices/IndexInclExcl.xls . Download succeeded (820,736 bytes), SHA256 `8869bb7c4df67403131a494a8cc65509e80828f9438bc150b506cdbf55378046`. The parsed Nifty 50 sheet contains 196 inclusion/exclusion events, 18 September 1996–31 July 2020. It cannot establish 2022–2025 membership, missing initial constituents, renames or delisted histories. Raw workbook and parsed sheets are retained. A current list was not projected backward. Complete point-in-time reconstruction was not achieved; the stock experiments retain a clearly labelled restricted surviving universe.

## Independent evaluation

Not achieved. The 2022–2025 period and 2026 observations had already been examined. The new ETF history is a new benchmark instrument, not an independent equity holdout. A fresh download and an arbitrary split of these periods do not undo exposure. No future window after the 25 October 2026 freeze has elapsed. A later prospective study should preregister policy hashes, calendar, admissions and outcomes before collecting future data. This is a recommendation, not a completed external validation.

## Frozen policy source hashes

- `research/phase8/market.py`: `e186bbebccf82bed7fe1fffe311220e9e7b9a25c927c0ba4a4ab0eee4c95eb7f`
- `research/phase8/__init__.py`: `1be4936467a51b631da4b7663ff2cf5c4840fa654afb2ad2a3cd562ac8403510`
- `research/phase8/analysis/metrics.py`: `0e7335775e70fa770d7d6deb601bfb8c08145fdf3dd5b3e0d1f851039983a098`
- `research/phase8/analysis/finalize.py`: `104e456ac1393bafbbc889b44efa3a9d6156c6e3093d14c142ad1f84e2a58fa3`
- `research/phase8/analysis/report.py`: `84f46254a41d235d4a6a4f36d21693394785079fccdeacd51bec704673c757e2`
- `research/phase8/experiments/runner.py`: `727e096fccd06e016e3e931b0473f0bc19971f54b62862f83dc68bfceb125c1f`
- `research/phase8/experiments/validate.py`: `b38a28b615e7cceac0ff6de9d38db861ca6b8623040f6ac29f92f7a8f1873b58`
- `research/phase8/experiments/engine.py`: `cd68bdb0adddbe36c715694eae8cce1e1f8b2d165c757db246107f72ff057c34`
- `research/phase8/experiments/reproduce_v1.py`: `52d0e447ba87d1bfadf49bc21290907764e2d33f2ac79d7ef946f1c5586b52af`
- `research/phase8/experiments/verify.py`: `623df6160a497cc7b5235c9aef767e91c1e851f65542fc31fcf0dd1bfe221edb`
- `research/phase8/policies/construction.py`: `2f917c340f1facacf813948e58ea7af0b2a40a5e4bc2d3b64c5bec4253c09781`
- `research/phase8/policies/authority.py`: `f498fe399178b8bce241f74b79ba147f48a50160ab50a06513f654c2b029e686`
