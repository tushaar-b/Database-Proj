"""Render eight evidence-backed Markdown research reports; no favorable-result templates."""
import json
from pathlib import Path
import numpy as np,pandas as pd
from research.phase9.freeze import OUT,sha,verify

def table(frame,columns=None,percent=(),digits=3):
    f=frame.copy() if columns is None else frame[columns].copy()
    for c in f:
        if c in percent:f[c]=f[c]*100
        if pd.api.types.is_numeric_dtype(f[c]):f[c]=f[c].map(lambda v:'unavailable' if pd.isna(v) else f'{v:.{digits}f}')
        else:f[c]=f[c].fillna('unavailable').astype(str)
    return '| '+' | '.join(f.columns)+' |\n|'+'|'.join(['---']*len(f.columns))+'|\n'+'\n'.join('| '+' | '.join(row)+' |' for row in f.astype(str).values)+'\n'

def write(name,text):(OUT/name).write_text(text.strip()+'\n')

def main():
    S=pd.read_csv(OUT/'benchmark_summary.csv');s=S.set_index('policy');P=pd.read_csv(OUT/'all_investor_performance.csv');Q=pd.read_csv(OUT/'same_state_allocation_quality.csv');R=pd.read_csv(OUT/'controlled_algorithm_runtimes.csv');ST=pd.read_csv(OUT/'synchronized_temporal_intervals.csv');EX=pd.read_csv(OUT/'exposure_matched_comparisons.csv');AU=json.loads((OUT/'DATA_AUDIT.json').read_text());C=json.loads((OUT/'RUN_CONFIG.json').read_text())
    validation=json.loads((OUT/'VALIDATION.json').read_text())
    core=['V1','GREEDY_M','V3','MILP_M','EQUAL_M','SIP_M','ETF_M','GREEDY_C','V4','MILP_C','EQUAL_C','SIP_C','ETF_C','NEUTRAL_M','NEUTRAL_C']
    mainrows=s.loc[core].reset_index();percent=['authorized_budget_utilization','annualized_return','annualized_volatility','cvar95','maximum_drawdown','mean_cash_allocation']
    performance=table(mainrows,['policy','regime','authorized_budget_utilization','annualized_return','annualized_volatility','cvar95','maximum_drawdown','mean_hhi','mean_cash_allocation','median_defined_sharpe'],percent)
    trading=table(mainrows,['policy','cumulative_return','ending_equity','turnover','transaction_fees','slippage_cost','buy_trades','sell_trades'],['cumulative_return'])
    caveat='All findings are exploratory comparisons of nine synthetic profiles sharing historical market paths. Previously inspected observations, overlapping windows, surviving-security selection and current sector labels prevent independent-validation or population-level claims.'
    hashes='\n'.join(f'- `{p}`: `{h}`' for p,h in C['source_hashes'].items())
    write('PHASE9_DATA_AUDIT.md',f'''# Phase 9 data audit — 25 October 2026

{caveat}

## Frozen equity evidence

The required run03, diagnostic, Phase 8 and original conference-draft paths exist. Original data SHA256: `{C['dataset_sha256']}`. Source files and application files are recorded before experiments in PRESERVED_HASHES.json; {verify()} files are unchanged. Original V1 matches 36 accounts and V1/V3/V4 match all 108 Phase 8 account/window summaries at rtol 1e-10, atol 1e-8. Policies were imported unchanged.

The retained Yahoo/yfinance dataset has 57,400 rows, 40 securities, 1,435 common sessions, 1 January 2021–22 October 2026. Duplicate security/date keys: {AU['equity_duplicate_keys']}. Per-security identifier, sector, observation, dividend, split and provider first-trade metadata are exported in historical_universe_metadata.csv. Provider firstTradeDate is not an actual exchange listing certificate. No exchange-certified listing dates, delisting history or historical sector classifications were recovered. All retained securities have observed pre-decision history and cached eligibility requires at least 120 completed returns. Historical signals exclude later observations, conditional on this fixed surviving universe.

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

{hashes}
''')
    formulation=r'''
For investor $u$, decision $t$, eligible security $i$, let $h_i\in\mathbb Z_+$ be pre-trade holdings, $p_i>0$ observed nominal close, $q_i\in\mathbb Z_+$ new shares, $C_u$ actual brokerage cash, and $A_{u,t}$ unspent household authority. With fee $f$ and adverse slippage $\ell$, $c_i=p_i(1+\ell)(1+f)$ and purchase cost $K(q)=\sum_i c_iq_i$. The saved batch budget is

$$B_{u,t}=\lfloor100\rho_{u,t}\min(C_u,A_{u,t})\rfloor/100,$$

where $\rho$ is the frozen feedback multiplier. Hard financial constraints are $K(q)\le B_{u,t}$, $K(q)\le C_u$, $q_i=0$ for ineligible names, and no household reserve draw. No initial savings grant is created.

Set $v_i=h_ip_i$, $v'_i=(h_i+q_i)p_i$, $E=C_u+\sum_i v_i$, and $E'=C_u-K(q)+\sum_i v'_i$. Let $S$ be the sector incidence matrix. Frozen guarded methods impose

$$v'_i\le\max(0.20E',v_i),\quad (Sv')_s\le\max(0.35E',(Sv)_s),$$

$$H(v')=\sum_s[(Sv')_s/\sum_i v'_i]^2\le\max(0.25,H(v)),$$

when a prior equity sleeve exists. Empty-account bootstrap skips this HHI constraint and is explicitly recorded. Portfolio drift can retain a breach; these are not permanent guarantees of weights below the thresholds. With lagged 30-return covariance $\Sigma_t$,

$$\sigma(v'/E')\le\max(0.03,\sigma(v/E)),\qquad1.645\sigma(v'/E')\le\max(0.10,1.645\sigma(v/E)).$$

No hard CVaR threshold exists in the frozen implementation. Sector feedback blocks the largest sector when HHI is breached. Financial constraints, portfolio guards, candidate ranking and share integrality are separate mechanisms.

Monthly household buffer $F_u=\max(0,I_u-M_u-R_u)$ excludes protected reserve $R_u$. Tier capacity $a_u\in\{0.25,0.50,0.75\}$ produces a unique grant $G_{u,t}=\lfloor100a_uF_u\rfloor/100$. Regime M expires old authority at each monthly review. Regime C keeps FIFO approval lots until age in calendar months is at least 12; a reduction in household buffer revokes all outstanding carry before the new grant. Spending debits each grant once. Thus

$$A_{u,t}=\sum_{j:\mathrm{valid}}(G_{u,j}-\mathrm{spent}_{u,j}),\quad A=\mathrm{grants}-\mathrm{spending}-\mathrm{expiry}-\mathrm{revocation}.$$

V3 uses Regime M and V4 uses C with exactly the same constructor. Unique utilization is external-funded spending / unique external grants, including grants subsequently expired or revoked in the denominator. Repeated carry balances never count as new grants.

The reference utility is $U(q)=\sum_{i\in\mathcal E}p_iq_i(m-r_i+1)/m$, where $r_i$ is descending selection-score rank among the common eligible set, ties ticker-ascending. It is an ordinal score-utility per rupee objective, not a prediction of realized return. V3/V4 do not globally optimize it: they prioritize ascending current sector weight, descending score and ticker, seed one feasible share in at most three distinct sectors, approach inverse-volatility sizing targets, then fill feasible residual quantities among that basket. The targets use the frozen cached size_weight. Their soft preference differs from the reference objective.

The integer reference maximizes $U$ under budget, cash, nonnegative integrality, eligible set and conservative linear position/sector grandfathering constraints. If an existing position/sector is overweight it cannot be enlarged; otherwise its post-trade fraction must remain under the account cap. This is slightly more restrictive than the frozen max-with-existing-value guard near a fee-induced threshold crossing, where unchanged holdings can be grandfathered. It is an encoded conservative reference, not proof of an optimum over every basket accepted by the frozen guard. For prior HHI $H_0$, the constraint $\|Sv'\|_2\le\sqrt{\max(.25,H_0)}\mathbf1^Tv'$ and volatility norm constraint are handled by valid supporting-hyperplane outer approximations. SciPy receives only linear MILPs. Each solution is checked by the full frozen Guard; violated norm constraints add valid cuts. Solver-certified optimality applies to the encoded conservative formulation at numerical tolerance. Three-second / 80-cut limits are recorded; no time-limited or rejected solution is labelled an optimum.
'''
    pseudocode='''```text
Frozen V3 constructor(state, pool, approved authority):
  B = floor_cent(feedback_multiplier * min(cash, authority))
  remove forbidden holdings unless top-ups enabled; remove blocked sectors
  sort by (current sector weight, -selection score, ticker)
  for candidate in order:
    if sector not yet selected and one share passes combined guards:
      seed one share; remember sector
    stop seeding at three sectors
  increase selected quantities toward cached size-weight targets by binary search
  repeatedly increase selected quantities within residual budget and guards
  validate combined basket; cancel if final guards fail
  return integer quantities and feasibility witnesses
At next available session close:
  adjust requested quantities for actual splits
  fill in saved basket priority under saved budget, cash and remaining authority
  recheck combined guards using lagged decision covariance; cancel unsafe batch
  debit cash and FIFO authority for actual fee-inclusive purchases exactly once
V4: same constructor and fill; replace monthly reset ledger with C ledger
```
'''
    write('PHASE9_BENCHMARK_SPECIFICATION.md',f'''# Phase 9 benchmark specification

{caveat}

Protocol constants were fixed before benchmark outcomes: nine original profiles; four original windows; monthly first-available-session decisions; next common-session close fills; 10 bp fees, 5 bp adverse slippage; cash yield zero; risk-free input 4% with legacy daily 0.04/252 as primary. All methods receive the same contributions and tier grants; M versus C is explicit. Holdings start empty with INR100,000 cash that is not automatically approved for purchase. No sales, borrowing, taxation or live brokerage actions occur.

## Strategy definitions

- A1 V1: frozen rank-first original selector, original held-name exclusion and original sizing. Its original guards differ from later methods; do not attribute every V1/V3 difference to feasibility alone.
- V3/V4: exact frozen policy definitions; M/C respectively.
- A2 GREEDY_M/C: same cached score pool, top-ups, feedback restrictions, account limits and guards as V3/V4. Sort descending score then ticker. Repeatedly buy one share of the first candidate whose addition passes the full combined guards and fee-inclusive residual budget; stop only when no candidate permits a one-share addition. No three-name basket restriction. This deliberately preserves a useful broad greedy comparator. Guard-feasible multi-share combinations not reachable through successive feasible one-share additions can be missed.
- A3 MILP_M/C: score-utility integer reference, conservative grandfathering and norm outer approximation described below. It can use all eligible names; a three-name basket is an internal V3 choice, not a common portfolio hard limit. The full frozen Guard must admit the returned basket. It does not maximize future returns or universally maximize cash use.
- B1 ETF_M/C: NIFTYBEES whole units on the identical monthly calendar, current authority regime and cost model; quantities floor fee-inclusive authorized budget / signal close; next-session fills capped by actual cash and saved authority. Passive investing does not use predictive ranking or a stock-level three-position basket. Stock 20%/sector35% guards are not applied to a diversified fund unit; historical look-through exposure is unavailable. Exclude it from stock-allocation utility/constraint comparisons. No purchased index points. TRI market reference unavailable, not substituted.
- B2 EQUAL_M/C: all verified observed eligible names in the retained 40-security universe; no score ordering. Repeatedly buy one feasible share of the smallest existing-plus-proposed INR holding, ticker ties. Stop when no permitted share exists. These are monthly purchase-only equal-weight target reviews; no sale rebalancing. Whole-share prices, authority and guards prevent exact equal weights. Daily actual L1 deviation from equal weights across that date's eligible set is exported in equal_weight_deviation.csv. Stock count and sector restrictions can vary by date; it is not claimed to be an actual historical NIFTY universe.
- B3 SIP_M/C: no score ordering; the lexicographically first currently eligible ticker per sector forms a deterministic representative basket. Each calendar month cycles through three adjacent representatives in alphabetic sector order using year*12+month modulo basket length. Repeated score-free whole-share purchases prioritize that fixed month's order, subject to common guards and cash/authority. This is a constrained recurring rotating-basket strategy; it differs economically from full eligible equal-weight and single-fund passive investing. Feedback can alter the available representative sectors. It does not optimize predictive scores.
- Neutral M/C: frozen V3/V4 constructor with selection scores all zero and size weights all one. It removes ranking and inverse-volatility target sizing together, so it is a joint preference ablation, not a score-only causal experiment.
- RANK_GUARD_M: frozen rank-first, no top-ups, guarded; FEAS_NO_TOPUP_M adds feasibility; RANK_TOPUP_M adds top-ups to guarded rank-first; V3 combines feasibility and top-ups.

All stock benchmarks use the same historical cache and information dates. Reusing a cache and fixed current sector labels does not cure surviving-universe selection bias. ETF history is only available through 2025 and therefore has three windows; no 2026 ETF outputs are manufactured.

## Implemented mathematical problem

{formulation}

## Reproducible pseudocode

{pseudocode}

Greedy replaces the sector/basket/target loop by first-feasible score-priority one-share additions over all eligible names. Equal-weight replaces that priority by smallest current INR holding. SIP limits the priority order to the three calendar-selected sector representatives. MILP repeatedly solves its linear outer approximation and adds violated norm supporting cuts until a guard-feasible certified solution or a labelled resource limit.

## Complexity and timing scope

With n securities, s sectors, dense covariance guard evaluation costs O(n²+s*n); constructing it also stores O(n²). Sorting is O(n log n). Greedy and equal-weight can attempt O(Q*n) additions in the worst case, where Q is the authorized number of cheapest shares, so these simple implementations are pseudopolynomial in share count. V3 sorts, checks up to n seeds and uses bounded three-name binary quantity searches plus residual loops; an intentionally loose bound is O(n log n+n*G+Q*3*log(Q+1)*G), G=guard cost. No asymptotic superiority follows from a small-universe timing. Integer branch-and-bound has no claimed polynomial bound; outer approximations cap at 80 solves and 3 seconds. Runtime includes pool/witness/guard work but excludes cache generation, downloads and daily valuation. Hardware and versions are in RUN_CONFIG.json.
''')
    quality=Q.groupby('method').agg(states=('date','size'),mean_budget_fill=('budget_fill','mean'),mean_objective=('objective','mean'),valid_fraction=('common_constraint_valid','mean'),median_seconds=('seconds','median')).reset_index()
    pivot=Q.pivot(index=['scenario','date'],columns='method',values='objective');ratios=pivot.div(pivot.MILP_M.replace(0,np.nan),axis=0).mean();quality['mean_reference_utility_ratio']=quality.method.map(ratios)
    timing=R.groupby(['candidate_size','method']).seconds.agg(['median','min','max']).reset_index();timing[['median','min','max']]*=1000
    write('PHASE9_ALGORITHM_COMPARISON.md',f'''# Algorithmic comparison

{caveat}

## Separate path efficiency from common-state quality

The historical policy table uses each method's own evolving holdings and feedback. In addition, 432 original V3 decision states (9 profiles × 48 monthly decisions) are replayed through each allocator with exactly the same cash, authority, prices, pool and covariance. Every output passes the common eligibility/guard/budget check in these states. V1 still excludes held names by design; common-state comparisons therefore do not by themselves isolate top-ups. The guarded rank-with-top-ups arm provides the more tightly controlled selection contrast.

{table(quality,percent=['mean_budget_fill','valid_fraction','mean_reference_utility_ratio'],digits=4)}

Mean state-wise utility/reference utility is **99.39% for greedy** and **62.39% for V3/V4**. All 432 reference objectives are positive. The integer solver certifies its encoded conservative formulation in all 432 states; it is not a full-guard global optimum certificate because linear grandfathering can be more restrictive at fee-induced cap crossings. Mean utility in INR-score units is dominated by larger budgets; the normalized state-wise ratio is the primary descriptive allocation-quality comparison. No realized future returns enter the objective.

V3/V4 are **not superior under this score-only objective**. Greedy nearly matches the integer reference. V3 instead prioritizes sector balance and a three-sector basket. Their common-state quantities are identical when authority is held fixed. Neither score utility nor higher budget fill implies higher subsequent return. Across actual primary paths, MILP M deploys less authority than greedy M/V3 despite higher same-state utility, illustrating feedback, next-session cancellations, and state-path effects.

## Policy-path efficiency

{table(mainrows,['policy','authorized_budget_utilization','decision_purchase_efficiency','proposed_basket_execution_rate','feasible_but_unexecuted_total'],['authorized_budget_utilization','decision_purchase_efficiency','proposed_basket_execution_rate'])}

Execution feasibility is both the all-decision purchase fraction and the purchase fraction conditional on a nonzero proposal. Feasible-but-unexecuted counts use a compliant one-share witness at the signal date; some failures reflect next-session drift/guard cancellation and cannot all be attributed to signal design. No claim is made that a simultaneous multi-security basket cannot exist when no single-share witness passes.

## Runtime under matched states

{table(timing,digits=4)}

Units for median/min/max are milliseconds. Six historical states (first two monthly decisions for low-conservative, medium-moderate and high-aggressive), sizes 10/20/40 selected by ticker order, five repetitions per combination; 450 timed allocations. At n=40, median V3 is {R[(R.candidate_size==40)&(R.method=='V3')].seconds.median()*1000:.3f} ms, greedy {R[(R.candidate_size==40)&(R.method=='GREEDY_M')].seconds.median()*1000:.3f} ms and integer reference {R[(R.candidate_size==40)&(R.method=='MILP_M')].seconds.median()*1000:.3f} ms. These are shared-process CPU wall times on {C['hardware']['machine']} / {C['hardware']['system']} {C['hardware']['release']}; full hardware metadata is retained. Process caches, scheduling and only six states limit generalization. No extrapolation to thousands of securities or unconditional computational superiority is supported.

## Constraint interpretation

All executed guarded baskets are reconciled against pre-fill existing holdings, actual execution close and lagged decision covariance. Natural drift, bootstrap HHI exceptions and grandfathering remain visible; a nonzero breach duration is not automatically an illegal purchase. V1 is preserved with its original restrictions, not silently hardened. ETF is outside the common stock-utility experiment. Legacy and new algorithms remain isolated from application recommendation routes.
''')
    write('PHASE9_INVESTMENT_BENCHMARKS.md',f'''# Investment benchmark results

{caveat}

## Primary 2022–2025 comparison

All displayed rates are percent; HHI and Sharpe are unitless. Means are across the same nine profiles. Sharpe column is the median of defined investor ratios, using a 4%/252 daily benchmark. CVaR is daily historical 95% expected tail loss; maximum drawdown uses daily contribution-adjusted TWR. M and C are separate authority regimes. ETF is an executable NIFTYBEES proxy, not a purchased index or a TRI reference.

{performance}

NIFTY 50 TRI daily reference: **unavailable (official endpoint HTTP 401)**. NIFTYBEES M/C are executable and separately labelled; tracking error and fund look-through HHI are unavailable. Its market prices include fund tracking/expense effects. Baseline application fees and adverse slippage are applied to every purchase, in addition to these embedded effects. Three conventional strategies are economically distinct: one fund, all-name equal-weight target purchases, and calendar-rotating sector representatives.

V3 returns 8.61% with 6.30% volatility, versus ETF M 4.79% and 4.50%. Its daily CVaR is 0.899% versus 0.620%, and drawdown 10.11% versus 7.19%. V4 returns 9.03% with 6.49% volatility versus ETF C 4.88% and 4.57%; daily CVaR is 0.927% versus 0.631%, drawdown 10.48% versus 7.33%. These are additional realized returns accompanied by larger losses and different equity composition/exposure, not demonstrated market-wide superiority.

Equal-weight M uses 95.68% approved capital versus V3 95.13%, so near-complete monthly deployment is not unique to IntelliVest. Under C, both are near 100%. SIP and neutral-preference policies produce higher mean primary returns than V3/V4, alongside higher CVaR and drawdown. The frozen ranking is therefore not validated as superior stock selection by these data.

## Contributions, turnover and execution costs

{trading}

Ending equity in INR includes original savings and external contributions; it is not a return measure. Cumulative return is TWR. Turnover is total bought/sold execution notional / mean account equity over the entire window, not annualized turnover. All strategies are purchase-only and sales are zero. Fees/slippage are mean total INR per profile over four years, not portfolio-weighted pooled costs. Rebalance frequency is monthly purchase review; no actual sale equalization is performed. Equal-weight deviation and all daily holdings-derived metrics are exported.

## Coverage

Four stock windows: 2022–2025, 2022–2023, 2024–2025 and January–22 October 2026. ETF coverage ends 2025, so only the first three are compared. Overlapping windows are robustness descriptions, not independent replications. Per-profile, per-window return, contributions, ending value, HHI coverage/breach frequency/duration, purchases, sales, turnover, fees, slippage and Sharpe are in all_investor_performance.csv and portfolio_risk.csv.
''')
    ab=s.loc[['V1','RANK_GUARD_M','FEAS_NO_TOPUP_M','RANK_TOPUP_M','V3','V4','NEUTRAL_M','NEUTRAL_C']].reset_index()
    write('PHASE9_ABLATION_RESULTS.md',f'''# Controlled ablation results

{caveat}

All rates below are percent. Guard, feasibility and top-up arms use the frozen constructor switches and identical monthly authority; carry-forward changes only the ledger. These components interact, so marginal effects depend on the chosen control.

{table(ab,['policy','authorized_budget_utilization','decision_purchase_efficiency','feasible_but_unexecuted_total','annualized_return','cvar95','maximum_drawdown','mean_hhi','mean_cash_allocation'],percent+['decision_purchase_efficiency'])}

## A — Feasibility-aware selection

RANK_GUARD_M and V1 happen to give identical primary outcomes; this is an observed result, not a promise that guards are irrelevant elsewhere. With no top-ups, feasibility increases utilization from 14.52% to 29.83% (15.31 percentage points), and feasible non-execution falls from 218 to 1. The latter does not imply high deployment: held-name exclusion can remove all opportunities after initial purchases. With top-ups held enabled, replacing rank-first selection by V3 raises utilization from 35.29% to 95.13% (59.85 pp), and feasible non-executions fall from 176 to 3. Return and downside both rise along the changed holding paths. Same-state score utility is greater for V3 than rank-first, but less than greedy/reference.

## B — Existing-holding top-ups

FEAS_NO_TOPUP_M versus V3 isolates top-ups with feasible selection/guards/monthly authority fixed. Utilization rises 29.83% to 95.13% (+65.30 pp), purchase frequency 31.71% to 99.31%, and mean sector HHI falls 0.1329 to 0.1061. Annualized return rises 4.39% to 8.61%, daily CVaR 0.515% to 0.899% and maximum drawdown 5.11% to 10.11%. Top-ups contribute substantially to persistent execution, but their benefit includes added equity exposure. Candidate and holding counts are exported for every decision.

## C — Carry-forward

V3 versus V4 uses an identical constructor. Unique utilization rises 95.13% to 99.96% (+4.82 pp), average invested allocation increases 1.36 pp, annualized return increases 0.418 pp, daily CVaR increases 0.0278 pp and drawdown increases 0.377 pp. Turnover rises from 0.6116 to 0.6333 over four years, with mean fees rising INR968.47 to INR998.87. This is an authorization/deployment policy effect. At the same state and authority, V3 and V4 quantities/objectives are identical over all 432 states.

## D — Ranking/preferences

NEUTRAL_M/C zeroes score and replaces inverse-volatility weights by equal targets, keeping the allocator/eligible set/guards and regime fixed. Neutral M returns 9.03% versus V3 8.61%, but daily CVaR rises 0.899% to 1.012%, drawdown 10.11% to 12.05%, and volatility 6.30% to 7.06%. Neutral C returns 9.42% versus V4 9.03%, with CVaR 1.048% versus 0.927% and drawdown 12.37% versus 10.48%. The combined ranking/sizing preference is not supported as a return improvement. The design cannot separately attribute score ordering and volatility-weight targets; a score-only neutralization would be an additional ablation.

## Equal-weight and sector effects

V3's primary mean sector HHI (0.1061) is below greedy M (0.2523), while equal-weight M is 0.1323. These are endogenous composition differences. Same-state utility and exposure analyses expose this trade-off but do not supply a fixed-sector causal decomposition. Sector-neutral resampling, score-only neutralization and target-weight matching are not claimed as completed experiments.
''')
    st=ST[ST.window=='primary_2022_2025'][['contrast','profiles','mean_annualized_arithmetic_return_difference','ci95_low','ci95_high']]
    ex=EX[(EX.window=='primary_2022_2025')&(EX.matching=='same_date_same_bin')].groupby('contrast')[['coverage','gross_sleeve_cvar_a','gross_sleeve_cvar_b']].mean().reset_index()
    sharpe=table(mainrows,['policy','median_defined_sharpe','mean_defined_sharpe','min_defined_sharpe','max_defined_sharpe','undefined_sharpe_count','low_volatility_sharpe_count'])
    write('PHASE9_STATISTICAL_ANALYSIS.md',f'''# Statistical and exposure analysis

{caveat}

## Design and resampling

The experimental unit is a synthetic profile paired across strategies, conditional on a common historical path. There are nine designed profiles, not hundreds of independently sampled investors. Profile/window/replay counts are not independent sample sizes. No population p-values, optimal-parameter searches or multiplicity-adjusted significance claims are made.

Daily TWR follows E_t/(E_(t-1)+contribution_t)-1. Annualization uses 252 sessions. Sharpe uses mean daily excess return / sample daily standard deviation × sqrt(252), with primary rf=0.04/252; effective-geometric rf is a separate sensitivity. Historical VaR is negative empirical linear 5% return quantile truncated at zero; CVaR is the mean loss in observations at/below that quantile, at least VaR. Drawdown includes initial wealth=1 in the running peak. Cash-only/no-holding risk is unavailable at the account summary level where meaningful risk observations are absent; constant return Sharpe is undefined. Primary profiles all have defined but sometimes very unstable Sharpe ratios.

The existing deterministic circular moving-block procedure is retained: 20 observed-session blocks, 2,000 draws, seed 20261024. Paired daily return differences are resampled together. For the following mean-profile intervals, date blocks are synchronized across all nine profiles, preserving their shared market dependence. The statistic is the mean annualized **arithmetic daily-return difference**, not a confidence interval for the difference in geometric annualized returns. Per-profile intervals and geometric paired differences are separately exported. Intervals describe path uncertainty conditional on this exposed historical sample; they do not validate synthetic profiles as a human population.

{table(st,percent=['mean_annualized_arithmetic_return_difference','ci95_low','ci95_high'])}

Units are percentage points/year. V3/greedy and V4/greedy intervals include zero, as do equal-weight, SIP and neutral-preference comparisons. V3/ETF and V4/ETF temporal intervals are positive in this sample, but universe, exposure and retrospective-data caveats remain. The V4/V3 interval is positive under this resampling statistic; it does not prove that ledger complexity is worthwhile or that downside-adjusted utility improves.

## Investor-level Sharpe distribution

{sharpe}

The primary V1 ratio range includes -132.19 from very small risky exposure; its mean must not be presented without this distribution. V3 median 0.729, V4 median 0.761. Defined ratios can still be numerically or economically unstable. low_volatility_sharpe_count counts defined ratios with annualized volatility below 1%, using the diagnostic phase's unchanged threshold. Per-investor flags and distributions are retained. Four-percent frozen-trade cash yield and both risk-free conventions are exported in cash_yield_sharpe_sensitivity.csv. The interest overlay adds no new approval and does not change trades; it is not a reinvestment-policy experiment. It reduces the interpretation of idle cash as wasted economic capital.

## Exposure-aware comparison

Equity-sleeve daily gross return is account PnL plus explicitly simulated fees/slippage divided by opening equity holdings, conditional on positive opening holdings. It can include dividends and is undefined without an opening sleeve. It is a diagnostic return, not a separately self-financing investable strategy. No sleeve drawdown is chained over missing unmatched dates. Same-date matching uses fixed opening-exposure bins [0,5,25,50,75,100]%; bins are broad and do not exactly match exposures or composition.

{table(ex,percent=['coverage','gross_sleeve_cvar_a','gross_sleeve_cvar_b'])}

V3/V1 matching covers only 15.42% of sessions on average, while V4/V3 covers 96.15%. Sparse V1 matches cannot support a causal risk advantage. Even among comparable exposure bins, V3 has higher gross sleeve CVaR than greedy/ETF and lower than SIP/neutral. This reinforces composition and risk trade-offs. Mean conditional CVaRs in the table are not pooled return-tail estimates. Per-profile coverage, temporal intervals and full sleeve metrics are exported.

## Robustness

Original early, late and 2026 stock windows are rerun unchanged. window_robustness.csv and all_investor_performance.csv show means, medians and ranges. Cost sensitivities use zero versus 20bp fees+10bp slippage on low-conservative, medium-moderate, high-aggressive only; these selected-profile means must not be compared directly with nine-profile primary means. Reduced-universe sensitivity uses the first 20 ticker-sorted retained securities, chosen without future returns; it is not a reconstructed point-in-time market universe. Household deterioration sets buffer to zero January–March 2024 and revokes authority before the grant review. No independent dataset was found. No bootstrap addresses survivorship, historical sector error or researcher exposure to 2022–2025.
''')
    conclusions='''| Question | Finding | Assessment |
|---|---|---|
| RQ11 conventional benchmarks | V3/V4 exceed executable ETF and equal-weight mean primary returns but also incur larger CVaR/drawdown; SIP and neutral preferences return more with greater losses | Mixed exploratory evidence; universal superiority unsupported |
| RQ12 allocation efficiency | Large gain over original rank-first; monthly equal-weight slightly exceeds V3 utilization; greedy nearly matches reference utility and exceeds V3 utility | Original-baseline improvement supported; superiority to simple allocation unsupported |
| RQ13 incremental construction | Feasibility and top-ups materially interact; ledger changes authority; score/sizing preferences do not establish better returns | Construction/deployment contribution supported; ranking alpha unsupported |
| RQ14 risk-return | Additional returns accompany additional equity exposure/downside; sector concentration differs materially | Trade-off supported; unqualified risk-adjusted dominance unsupported |
| RQ15 V4 complexity | +4.82pp utilization, +0.418pp return, +0.0278pp daily CVaR, +0.377pp drawdown; same constructor at equal authority | Small deployment gain supported; deployment justification inconclusive |
| RQ16 generalizability | Profile/window/cost/cash/universe sensitivities executed; PIT membership and independent holdout unavailable | Restricted robustness only; external validity inconclusive |'''
    write('PHASE9_FINAL_REPORT.md',f'''# IntelliVest Phase 9 final research report

**Classification: 2 — exploratory benchmark research.** {caveat}

## What was executed

36 exact original V1 replays, followed by 108 V1/V3/V4 frozen-policy reproductions; 495 stock strategy/account/window simulations; 54 executable ETF simulations; 72 selected-profile sensitivity simulations; 432 common-state comparisons across six methods (2,592 allocations); and 450 controlled runtime calls. Validation adds deterministic and future-price-perturbation replays. Counts describe computations, not independent investors. Existing application/data/evidence hashes remain unchanged.

## Main evidence

{performance}

All rate columns are percent, with HHI and Sharpe unitless. NIFTY TRI is unavailable; ETF is the executable NIFTYBEES proxy. Daily CVaR and drawdown quantify the additional downside that accompanies returns. The observed original-baseline utilization gain survives comparison, but it is not unique to the proposed constructor: equal-weight monthly utilization is 95.68% versus V3 95.13%, and all C strategies approach full approved utilization.

At identical V3 states, score-greedy attains 99.39% of the integer reference's utility versus V3/V4 62.39%. V3/V4 are sector-balanced heuristics rather than global maximizers of that utility. V3's low HHI and different holdings help explain why realized returns do not follow the score-utility ranking. No future return was used in the objective. The reference solves a conservative encoded guard model, so ratios are reference comparisons rather than universal optimality gaps.

The neutral-preference and rotating recurring strategies have higher mean primary returns but larger CVaR/drawdown than V3/V4. Existing IntelliVest ranking is not established as return-enhancing. Feasible selection and controlled top-ups jointly explain much of the difference from rank-first; top-ups under feasible selection alone increase utilization by 65.30pp. Carry-forward adds 4.82pp utilization and 0.418pp annualized return while increasing risk. The same-state V3/V4 allocation equality establishes that V4's difference comes from authority, not a distinct allocation algorithm.

## Research questions and hypothesis assessment

{conclusions}

## Data integrity and fairness

Original adjusted equity dataset is unchanged (40 securities, 57,400 observations). Signals use prior/current observed history with next-session close execution. Point-in-time historical index membership remains unresolved: the official workbook ends July 2020. ETF history has six NSE close matches and one independently sourced missing-session repair, separately versioned. NIFTY TRI endpoints were inaccessible. Current sector classification, action reconstruction, ex-date dividend credit, survivorship and provider metadata listing dates remain limitations. The new benchmark is not an independent holdout.

M and C receive identical household contributions and unique approvals. Brokerage cash and approval authority are separately conserved; protected reserves stay outside the account. ETF fund-level exposure is not constrained by single-stock position caps and cannot establish superiority under common stock constraints. All comparisons label the applicable regime. Zero cash yield is primary; 4% is an explicitly frozen-trade overlay. No live database, application policy, account or order was changed.

## Interpretation for publication

A defensible contribution is an audited affordability/authority/execution architecture plus a transparent feasibility-aware sector-priority heuristic and experimental evidence of its effects. A claim of a new general allocation optimization algorithm, reliable alpha, universal risk dominance, statistical generalization to investors or independent external validation is unsupported. Simple greedy and equal-weight methods substantially weaken any claim that high approved-capital utilization is algorithmically unique. V4's small incremental deployment benefit must be weighed against bookkeeping, expiry/revocation burden and additional losses; this experiment does not justify production integration.

## Validation and remaining work

All {validation['focused_checks']} final focused checks passed. Independent reconciliation covered {validation['stock_account_daily_observations']:,} stock-account days and {validation['guarded_buy_batches']:,} guarded purchase batches, plus all 54 ETF accounts and 72 sensitivity ledgers. All 489 previously protected Phase 8 input files are also included in the 854-file unchanged manifest. VALIDATION.json and validation_final.log give the authoritative executed outcomes; no unresolved check failure remains. All earlier research files are hash-protected; protected-source manifests include application files. No frontend/browser/regression suite was run. Detailed report links, CSV schemas, figure captions, exact commands, hashes and source snapshots are in README.md and the run manifests. Real point-in-time membership, independently verified actions, historical ETF look-through exposures, a prospective frozen holdout, score-only ablation and a full-guard exact optimization certificate remain future research, not completed claims.
''')
    write('PHASE9_CONFERENCE_DRAFT.md',f'''# Affordability-Constrained, Feasibility-Aware and Risk-Aware Portfolio Construction for Retail Investors

IEEE-style research draft — Phase 9 exploratory evidence, 25 October 2026. Original conference manuscript is preserved.

## Abstract

Retail portfolio recommendations must distinguish household affordability, spending authorization and executable share quantities. We evaluate frozen IntelliVest constructors against original rank-first selection, score-priority greedy allocation, a conservative integer reference, equal-weight target purchases, recurring sector-basket investing and an executable NIFTY 50 ETF proxy. Nine synthetic profiles share a restricted 40-security historical universe. V3 and V4 use 95.13% and 99.96% of unique approved capital, versus 14.52% for the original baseline. Equal-weight monthly allocation uses 95.68%, while greedy attains 99.39% of reference score utility in common states versus 62.39% for V3/V4. V4 returns 9.03% annually with 0.927% daily CVaR95 and 10.48% drawdown; its extra deployment is not a free reduction in risk. No independent holdout or complete point-in-time universe is established. The evidence supports execution architecture and component effects, not novel general-purpose optimization or universal investment superiority.

## I. Research motivation

A useful stock ranking does not guarantee an affordable whole-share order. Recommendations can fail when initial candidate prices, held-name exclusions or sizing rules leave authorized capital unspent. Brokerage cash also includes capital not approved for purchase. We study whether a feasibility-aware constructor improves execution under household, cash, portfolio and integer constraints, independently of claims about stock-price prediction. Research questions RQ11–RQ16 address conventional benchmarks, allocation efficiency, component attribution, risk trade-offs, complexity and validity.

## II. Methodological context

Greedy whole-share allocation and mixed-integer budget optimization are established algorithmic families. This implementation makes no claim that score sorting, integer quantities, concentration caps or carry-forward bookkeeping alone constitute novel algorithms. The specific research object is the interaction of explicit household approval, guarded feasibility selection, permitted existing-holding top-ups and delayed execution. [SciPy documents mixed-integer linear optimization and solver termination status](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html); the reference uses that existing facility and valid norm supporting cuts. [NSE's total-return-index description](https://www.nseindia.com/static/products-services/indices-total-returns-index) distinguishes dividend-inclusive context from a price index. [The ETF issuer](https://mf.nipponindiaim.com/FundsAndPerformance/Pages/NipponIndia-ETF-Nifty-50-BeES.aspx) identifies the passive tracking objective and whole-unit exchange access. These are verified implementation/data references, not a fabricated literature review. A systematic peer-reviewed related-work survey is still required before submission.

## III. Mathematical problem formulation

{formulation}

## IV. Proposed implementation

{pseudocode}

The constructor is a guarded sector-priority heuristic, not an exact solution of U. Existing holdings enter every feasibility test. At execution, the next-session close can change quantities or cancel a basket. Covariance is lagged to the signal date. V4 differs from V3 only in the approval ledger. Full code hashes, dataset hashes and per-order evidence accompany the paper draft.

## V. Baselines

Original V1 selects the original basket before sizing and excludes held names. Greedy considers all eligible names by descending score and buys the first feasible next whole share until no such addition exists. The integer reference maximizes ordinal score-weighted nominal deployment under the documented conservative constraints. Equal-weight reviews monthly and prioritizes underweight INR holdings across all observed eligible names, without selling. Recurring investing rotates three deterministic sector representatives monthly, without scores. NIFTYBEES invests available approved capital in whole fund units, with next-session cost/cash caps. The ETF is not subject to a single-stock concentration cap; its historical sector look-through is unavailable and it is excluded from common stock-utility comparisons. Each benchmark is run under M and C where data permit.

## VI. Experimental setup

Nine synthetic profiles vary surplus level and risk tier, with empty initial holdings and INR100,000 brokerage cash. Monthly external household contributions are identical across methods; initial cash is not automatically granted spending authority. Primary period: 2022–2025. Additional overlapping windows: 2022–2023, 2024–2025 and January–22 October 2026 for stocks. Fees: 10bp; adverse slippage: 5bp; zero-interest cash; 4% annual risk-free input; daily TWR and 252-session annualization. The stock grid has 495 accounts, ETF grid 54. Seventy-two selected-profile sensitivities cover execution costs, reduced universe and household deterioration. All counts represent correlated simulation conditions.

## VII. Historical-data provenance

The original 57,400 adjusted observations across 40 retained securities derive from Yahoo/yfinance with split-reconstructed nominal execution prices, explicit shares/actions and ex-date dividend credit. Earlier sparse NSE checks cover 240 retained prices. Listing metadata and current sector labels do not establish historical point-in-time eligibility. Ten unreconciled securities remain excluded. NIFTYBEES has 1,236 provider rows, six independently matching exchange closes and one missing-session nominal-price correction sourced from the official exchange archive. Daily TRI retrieval returned HTTP401; no substitute index series is fabricated. The official constituent-event workbook ends in 2020 and cannot reconstruct the evaluation universe. All periods were exposed previously; the ETF is a benchmark, not an independent holdout.

## VIII. Main results

{performance}

Rates are percent; HHI and median investor Sharpe are unitless. V3/V4 exceed ETF primary mean return by 3.82/4.16pp but have greater volatility and CVaR. Equal-weight slightly exceeds V3 monthly utilization; SIP and neutral preferences exceed V3/V4 mean return with greater tail risk. Approved-capital utilization therefore cannot establish investment or allocation dominance.

## IX. Algorithmic comparison and ablation

Across 432 identical decision states, greedy reaches 99.39% of the encoded reference's score utility, V3/V4 62.39%. V3/V4 produce identical orders at equal authority. Five-repeat timing across six states and n=10/20/40 confirms actual computational costs; at n=40 medians are approximately 1.24ms for V3, 1.82ms greedy and 32.39ms reference in this environment. These are not asymptotic results. Feasibility without top-ups raises utilization 14.52% to 29.83%; enabling top-ups under feasibility raises it to 95.13%. With top-ups held fixed, feasibility raises utilization 35.29% to 95.13%. Interactions prevent additive attribution.

## X. Risk–return and statistical assessment

V4 minus V3 gives +4.82pp utilization, +0.418pp annualized geometric return, +0.0278pp daily CVaR and +0.377pp drawdown. Primary V3/V4 median Sharpe is 0.729/0.761; V1's -132.19 minimum illustrates why reporting only mean Sharpe is misleading. Circular 20-session paired blocks with 2,000 draws and seed20261024 provide descriptive temporal uncertainty; blocks are synchronized across profiles. Greedy/equal-weight/SIP/neutral return-difference intervals cross zero. These are conditional arithmetic-difference intervals, not population inference. Same-date exposure-bin coverage is only 15.42% for V3/V1; it is 96.15% for V4/V3. Sparse matching cannot identify causal selection advantage.

## XI. Threats to validity

Surviving-security admission, absent delisted names, unverified historical sectors, provider listing metadata, sparse action corroboration, ex-date dividend approximation, overlapping exposed periods, synthetic investor profiles and missing TRI/look-through data limit interpretation. The conservative reference's grandfathering differs at fee-induced threshold crossings and is not a certificate over the entire frozen Guard feasible set. One-share greedy can miss jointly feasible batches. Neutralization changes both scores and size targets. Cost/universe/shock sensitivities cover three representative profiles rather than all nine. Taxes, market impact, spread variation, withdrawals, liquidity limits and live execution are outside the model. None of these limitations is repaired by resampling historical returns.

## XII. Conclusion

The experiments establish that feasibility selection and controlled top-ups can transform previously approved capital into executable whole-share purchases within the studied system. Simple equal-weight and greedy methods capture much of the allocation efficiency, and the proposed heuristic does not maximize the reference score objective. Carry-forward mainly adds authorization and exposure, with modest incremental return and larger downside. The publication is exploratory benchmark research. Novel optimization, ranking alpha, universal risk-adjusted superiority and independent validation remain unproven.

## Reproducibility and figures

See README.md, PHASE9_BENCHMARK_SPECIFICATION.md, VALIDATION.json, source_snapshot/, CSV exports and figures/CAPTIONS.md. Nine figures are provided as 300dpi PNG and editable SVG. No original application, data, policy or manuscript is modified. Further literature review and independent prospective data are required before submission as validated comparative research.
''')
    write('README.md','''# Phase 9 executed research artifacts

Read PHASE9_FINAL_REPORT.md first. Rate CSV values are fractions, amounts INR, runtimes seconds, durations sessions. Reports explicitly convert displayed rates to percentages. Empty/undefined values are not zero risk. All paths below are relative to this repository root.

## Reproduction in a fresh output directory

The output is immutable after finalization. Preserve it and set INTELLIVEST_PHASE9_OUT to a fresh directory for another run; the main runner refuses an existing RUN_CONFIG.json. Read-only frozen source dependencies are under research/phase8, research/diagnostics and research/*.py. No database connection is needed. Do not rerun Phase 8's CLI against original output directories.

For a fresh run first set, for example, `export INTELLIVEST_PHASE9_OUT=research/results/phase9-reproduction-2026-10-25`. This environment variable controls all Phase 9 modules. Copy saved benchmark_sources into the fresh output to reuse exact raw inputs, or repeat acquisition and record the new hashes. The missing-session official zip must also be downloaded before audit.

Executed order:

```sh
.venv/bin/python -m research.phase9.freeze
.venv/bin/python -m research.phase9.reproduce
.venv/bin/python -m research.phase9.acquire
.venv/bin/python -m research.phase9.acquire_extra
# Official missing ETF bar: exact URL and hash in benchmark_sources/ETF_CORRECTION.json
PYTHONPATH=/private/tmp/intellivest-phase9-extra .venv/bin/python -m research.phase9.audit
.venv/bin/python -m research.phase9.runner
.venv/bin/python -m research.phase9.passive
.venv/bin/python -m research.phase9.same_state
.venv/bin/python -m research.phase9.sensitivity
.venv/bin/python -m research.phase9.analyze
.venv/bin/python -m research.phase9.validate
MPLCONFIGDIR=/private/tmp/intellivest-phase9-mpl PYTHONPATH=/private/tmp/intellivest-phase9-deps .venv/bin/python -m research.phase9.figures
.venv/bin/python -m research.phase9.reports
```

Acquisition needs authorized internet. Saved raw benchmark files can be reused without redownloading; analysis uses no network. The installed application environment already supplied NumPy, pandas, SciPy and yfinance. Matplotlib and xlrd were installed only in temporary directories, leaving repository dependency/environment files unchanged. Environment versions are in RUN_CONFIG.json and ENVIRONMENT.json. Future recreations should use a separate virtual environment and pinned recorded versions.

## Tables

- strategy_configuration.csv: frozen policy switches, name, carry regime.
- historical_universe_metadata.csv, DATA_AUDIT.json, etf_exchange_checks.csv: identifiers, dates, actions, source/verification limits.
- accounts/: per-window/profile/policy valuations, decisions, trades, authority events, fills, episodes and runtimes.
- benchmark_trades.csv and etf_accounts/trades.csv: every executed quantity, decision/execution date, fee/slippage and top-up flag.
- portfolio_valuations.csv and etf_accounts/valuations.csv: daily account cash/equity/returns and authority stocks.
- allocation_decisions.csv, allocation_utilization.csv: budgets, proposal/execution quantities, eligible/affordable counts and remaining authority.
- feasible_but_unexecuted.csv: compliant signal-date one-share witnesses without actual buys.
- cash_authority_accounting.csv: unique grants/spending/expiry/revocation, unused approved cash, other brokerage cash and protected-reserve distinction.
- investor_level_performance.csv, etf_investor_performance.csv, all_investor_performance.csv, portfolio_risk.csv: per-profile/window outcomes and risk coverage.
- benchmark_summary.csv: nine-profile primary descriptive means and Sharpe distribution.
- same_state_allocation_quality.csv: common-state objective/cost/quantities and solver status; no realized-return objective.
- algorithm_runtimes.csv: every main allocator invocation, including feedback counterfactual calls (override flag).
- controlled_algorithm_runtimes.csv: five repetitions, six historical states, sizes10/20/40; quantities verify timing repeatability.
- sensitivity_accounts/: complete raw cost/universe/shock replay ledgers.
- ablation_outcomes.csv, sensitivity_outcomes.csv, cash_yield_sharpe_sensitivity.csv: component, cost, universe, shock and frozen-trade cash-yield sensitivities.
- statistical_comparisons.csv, synchronized_temporal_intervals.csv: per-profile paired effects and shared-date temporal intervals.
- exposure_matched_comparisons.csv, equity_sleeve_metrics.csv: sleeve diagnostics, matching coverage and uncertainty.
- equal_weight_deviation.csv: daily actual equal-weight target deviation from independent holdings reconstruction.
- window_robustness.csv: means/medians/ranges across the original windows.

Important: algorithm_runtimes.csv's objective uses the full original pool rank and is only instrumentation. The common eligible-set objective for valid cross-method quality comparisons is computed explicitly in same_state_allocation_quality.csv. These score scales must not be mixed. Runtime call counts include feedback counterfactual evaluations; account counts do not.

## Integrity

PRESERVED_HASHES.json protects earlier evidence and application source; FROZEN_REPRODUCTION.json records numerical reproduction; RUN_CONFIG.json records inputs and primary code hashes; FINAL_SOURCE_HASHES.json and source_snapshot/ record all final Phase 9 code; OUTPUT_HASHES.json covers generated artifacts. VALIDATION.json and validation_final.log give the final focused executed checks; earlier validator development logs are superseded. GIT_STATUS_BEFORE.txt and GIT_STATUS_AFTER.txt are workspace-scoped. No files are staged or committed.

The original sensitivity draft had a literal-replacement ordering error caught during implementation review. The corrected placeholder-based cost adapter was executed to produce sensitivity_outcomes.csv; sensitivity_final.log is the final run. The primary grid never used the sensitivity adapter. No frozen V1/V3/V4 defect or modification was introduced.
''')
    print('Wrote eight required reports and README')
if __name__=='__main__':main()
