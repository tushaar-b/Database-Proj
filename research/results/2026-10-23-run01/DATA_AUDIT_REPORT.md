# Historical dataset audit

Audit time: 2026-10-23T18:12:45.515006+00:00

## Existing database (read-only snapshot)

61,850 observations, 50 securities, ['2021-10-19', '2026-10-19'].
0 rows match the synthetic generator's rounded 0.98 adjustment formula. This is a diagnostic fingerprint, not proof of provenance. The schema stores neither source nor ingestion time; no listing/delisting history exists. Full per-security checks are in `legacy_quality_by_security.csv`. Union-date gaps are diagnostics, not an exchange calendar. No historical rows were changed.

## Independent acquisition

70,315 provider observations across 49 securities. Status: **provider_data_available_requires_validation**. See `acquisition_log.json` for every download failure and exclusion. Synthetic fallback is disabled. Legacy observations are quarantined from financial simulation, regardless of plausibility.

## Adjustment and eligibility

Provider Adj Close for return/ranking; split-reconstructed nominal OHLC for execution; cash dividends credited on ex-date (pay-date approximation). Raw responses and hashes are retained when available. Symbols are never silently substituted; TATAMOTORS is excluded because the implemented application flags unreconciled identity/corporate actions. Initial eligibility requires at least 120 completed adjusted returns and a contemporaneous bar; a first provider observation is not a verified listing date. Current sector labels and a surviving universe limit generalization. Historical index membership and delisted stocks cannot be reconstructed from these tables. Any replay is a restricted-universe exploratory study, not an unbiased market-wide evaluation.

## Scientific gate

If fresh adjusted history is absent, historical financial comparisons, return curves, p-values, and superiority claims are unavailable. Policy arithmetic and synthetic engine checks can still be executed, explicitly as implementation diagnostics. Provider data, when acquired, must additionally pass identity, action and calendar checks before replay.

## Source documentation

- [yfinance history implementation](https://github.com/ranaroussi/yfinance/blob/main/yfinance/scrapers/history.py): OHLC, adjustment and action options.
- [NSE historical reports](https://www.nseindia.com/static/resources/historical-reports-capital-market-daily-monthly-archives): exchange comparison source.

No claim of exchange corroboration is made merely because a provider responded.

## Completed admission checks

{
  "status": "exploratory_restricted_universe",
  "securities": 43,
  "observations": 61705,
  "range": [
    "2021-01-01",
    "2026-10-22"
  ],
  "source_dataset_sha256": "dff4cd2d33ed5be783623472f210eb1d4a4f17a1db8f6bd66f442acac37e27dc",
  "research_dataset_sha256": "ebdeb0ca4bfca93016a28f0d09349ba9359b4cfa6c6d67e6cd49e467739f2872",
  "exclusions": {
    "TATAMOTORS": "unreconciled demerger and renamed identity",
    "ITC": "exchange sampled nominal-close disagreement",
    "RELIANCE": "2023 Jio Financial demerger; no entitlement valuation ledger",
    "BHARTIARTL": "rights/partly paid security history not reconciled",
    "HDFCBANK": "2023 merger identity/action reconciliation not independently established",
    "LTIM": "2022 merger/symbol history not independently reconciled",
    "BAJFINANCE": "exchange sampled nominal-close disagreement",
    "TRENT": "exchange sampled nominal-close disagreement"
  },
  "calendar_removed": [],
  "calendar_removed_observations": 0,
  "exchange_comparisons": 98,
  "exchange_matches": 94,
  "universe": [
    "ADANIENT",
    "ADANIPORTS",
    "APOLLOHOSP",
    "ASIANPAINT",
    "AXISBANK",
    "BAJAJ-AUTO",
    "BAJAJFINSV",
    "BEL",
    "BPCL",
    "BRITANNIA",
    "CIPLA",
    "COALINDIA",
    "DIVISLAB",
    "DRREDDY",
    "EICHERMOT",
    "GRASIM",
    "HCLTECH",
    "HEROMOTOCO",
    "HINDALCO",
    "HINDUNILVR",
    "ICICIBANK",
    "INDUSINDBK",
    "INFY",
    "JSWSTEEL",
    "KOTAKBANK",
    "LT",
    "M&M",
    "MARUTI",
    "NESTLEIND",
    "NTPC",
    "ONGC",
    "POWERGRID",
    "SBILIFE",
    "SBIN",
    "SHRIRAMFIN",
    "SUNPHARMA",
    "TATACONSUM",
    "TATASTEEL",
    "TCS",
    "TECHM",
    "TITAN",
    "ULTRACEMCO",
    "WIPRO"
  ],
  "listing_dates": "not independently established; minimum 120 observed returns and contemporaneous bar required",
  "adjustment_provenance": "Yahoo adjusted close plus explicit dividends/splits; nominal reconstruction sampled against NSE",
  "publication_claims_supported": false
}

Exchange checks are sparse price/date corroboration, not certification of every adjusted observation or dividend. A complete historical listing/index/delisting universe is unavailable. Financial comparisons, if admitted, are exploratory only.

## Completed admission checks

{
  "status": "exploratory_restricted_universe",
  "securities": 41,
  "observations": 58835,
  "range": [
    "2021-01-01",
    "2026-10-22"
  ],
  "source_dataset_sha256": "dff4cd2d33ed5be783623472f210eb1d4a4f17a1db8f6bd66f442acac37e27dc",
  "research_dataset_sha256": "2f0b92f3549b3b58723befc9a704e5b8c5c1ae6a98db4bf89d94b45eb3c996a4",
  "exclusions": {
    "TATAMOTORS": "unreconciled demerger and renamed identity",
    "ITC": "exchange sampled nominal-close disagreement",
    "RELIANCE": "exchange sampled nominal-close disagreement",
    "BHARTIARTL": "rights/partly paid security history not reconciled",
    "HDFCBANK": "2023 merger identity/action reconciliation not independently established",
    "LTIM": "2022 merger/symbol history not independently reconciled",
    "BAJAJFINSV": "exchange sampled nominal-close disagreement",
    "BAJFINANCE": "exchange sampled nominal-close disagreement",
    "GRASIM": "exchange sampled nominal-close disagreement",
    "TRENT": "exchange sampled nominal-close disagreement"
  },
  "calendar_removed": [],
  "calendar_removed_observations": 0,
  "exchange_comparisons": 293,
  "exchange_matches": 271,
  "universe": [
    "ADANIENT",
    "ADANIPORTS",
    "APOLLOHOSP",
    "ASIANPAINT",
    "AXISBANK",
    "BAJAJ-AUTO",
    "BEL",
    "BPCL",
    "BRITANNIA",
    "CIPLA",
    "COALINDIA",
    "DIVISLAB",
    "DRREDDY",
    "EICHERMOT",
    "HCLTECH",
    "HEROMOTOCO",
    "HINDALCO",
    "HINDUNILVR",
    "ICICIBANK",
    "INDUSINDBK",
    "INFY",
    "JSWSTEEL",
    "KOTAKBANK",
    "LT",
    "M&M",
    "MARUTI",
    "NESTLEIND",
    "NTPC",
    "ONGC",
    "POWERGRID",
    "SBILIFE",
    "SBIN",
    "SHRIRAMFIN",
    "SUNPHARMA",
    "TATACONSUM",
    "TATASTEEL",
    "TCS",
    "TECHM",
    "TITAN",
    "ULTRACEMCO",
    "WIPRO"
  ],
  "listing_dates": "not independently established; minimum 120 observed returns and contemporaneous bar required",
  "adjustment_provenance": "Yahoo adjusted close plus explicit dividends/splits; nominal reconstruction sampled against NSE",
  "publication_claims_supported": false
}

Exchange checks are sparse price/date corroboration, not certification of every adjusted observation or dividend. A complete historical listing/index/delisting universe is unavailable. Financial comparisons, if admitted, are exploratory only.
