# Affordability-Constrained, Feasibility-Aware and Risk-Aware Portfolio Construction for Retail Investors

IEEE-style research draft — Phase 9 exploratory evidence, 25 October 2026. Original conference manuscript is preserved.

## Abstract

Retail portfolio recommendations must distinguish household affordability, spending authorization and executable share quantities. We evaluate frozen IntelliVest constructors against original rank-first selection, score-priority greedy allocation, a conservative integer reference, equal-weight target purchases, recurring sector-basket investing and an executable NIFTY 50 ETF proxy. Nine synthetic profiles share a restricted 40-security historical universe. V3 and V4 use 95.13% and 99.96% of unique approved capital, versus 14.52% for the original baseline. Equal-weight monthly allocation uses 95.68%, while greedy attains 99.39% of reference score utility in common states versus 62.39% for V3/V4. V4 returns 9.03% annually with 0.927% daily CVaR95 and 10.48% drawdown; its extra deployment is not a free reduction in risk. No independent holdout or complete point-in-time universe is established. The evidence supports execution architecture and component effects, not novel general-purpose optimization or universal investment superiority.

## I. Research motivation

A useful stock ranking does not guarantee an affordable whole-share order. Recommendations can fail when initial candidate prices, held-name exclusions or sizing rules leave authorized capital unspent. Brokerage cash also includes capital not approved for purchase. We study whether a feasibility-aware constructor improves execution under household, cash, portfolio and integer constraints, independently of claims about stock-price prediction. Research questions RQ11–RQ16 address conventional benchmarks, allocation efficiency, component attribution, risk trade-offs, complexity and validity.

## II. Methodological context

Greedy whole-share allocation and mixed-integer budget optimization are established algorithmic families. This implementation makes no claim that score sorting, integer quantities, concentration caps or carry-forward bookkeeping alone constitute novel algorithms. The specific research object is the interaction of explicit household approval, guarded feasibility selection, permitted existing-holding top-ups and delayed execution. [SciPy documents mixed-integer linear optimization and solver termination status](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html); the reference uses that existing facility and valid norm supporting cuts. [NSE's total-return-index description](https://www.nseindia.com/static/products-services/indices-total-returns-index) distinguishes dividend-inclusive context from a price index. [The ETF issuer](https://mf.nipponindiaim.com/FundsAndPerformance/Pages/NipponIndia-ETF-Nifty-50-BeES.aspx) identifies the passive tracking objective and whole-unit exchange access. These are verified implementation/data references, not a fabricated literature review. A systematic peer-reviewed related-work survey is still required before submission.

## III. Mathematical problem formulation


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


## IV. Proposed implementation

```text
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


The constructor is a guarded sector-priority heuristic, not an exact solution of U. Existing holdings enter every feasibility test. At execution, the next-session close can change quantities or cancel a basket. Covariance is lagged to the signal date. V4 differs from V3 only in the approval ledger. Full code hashes, dataset hashes and per-order evidence accompany the paper draft.

## V. Baselines

Original V1 selects the original basket before sizing and excludes held names. Greedy considers all eligible names by descending score and buys the first feasible next whole share until no such addition exists. The integer reference maximizes ordinal score-weighted nominal deployment under the documented conservative constraints. Equal-weight reviews monthly and prioritizes underweight INR holdings across all observed eligible names, without selling. Recurring investing rotates three deterministic sector representatives monthly, without scores. NIFTYBEES invests available approved capital in whole fund units, with next-session cost/cash caps. The ETF is not subject to a single-stock concentration cap; its historical sector look-through is unavailable and it is excluded from common stock-utility comparisons. Each benchmark is run under M and C where data permit.

## VI. Experimental setup

Nine synthetic profiles vary surplus level and risk tier, with empty initial holdings and INR100,000 brokerage cash. Monthly external household contributions are identical across methods; initial cash is not automatically granted spending authority. Primary period: 2022–2025. Additional overlapping windows: 2022–2023, 2024–2025 and January–22 October 2026 for stocks. Fees: 10bp; adverse slippage: 5bp; zero-interest cash; 4% annual risk-free input; daily TWR and 252-session annualization. The stock grid has 495 accounts, ETF grid 54. Seventy-two selected-profile sensitivities cover execution costs, reduced universe and household deterioration. All counts represent correlated simulation conditions.

## VII. Historical-data provenance

The original 57,400 adjusted observations across 40 retained securities derive from Yahoo/yfinance with split-reconstructed nominal execution prices, explicit shares/actions and ex-date dividend credit. Earlier sparse NSE checks cover 240 retained prices. Listing metadata and current sector labels do not establish historical point-in-time eligibility. Ten unreconciled securities remain excluded. NIFTYBEES has 1,236 provider rows, six independently matching exchange closes and one missing-session nominal-price correction sourced from the official exchange archive. Daily TRI retrieval returned HTTP401; no substitute index series is fabricated. The official constituent-event workbook ends in 2020 and cannot reconstruct the evaluation universe. All periods were exposed previously; the ETF is a benchmark, not an independent holdout.

## VIII. Main results

| policy | regime | authorized_budget_utilization | annualized_return | annualized_volatility | cvar95 | maximum_drawdown | mean_hhi | mean_cash_allocation | median_defined_sharpe |
|---|---|---|---|---|---|---|---|---|---|
| V1 | M | 14.523 | 2.635 | 2.107 | 0.310 | 2.882 | 0.348 | 85.621 | -1.934 |
| GREEDY_M | M | 94.255 | 5.749 | 5.126 | 0.723 | 9.963 | 0.252 | 62.439 | 0.341 |
| V3 | M | 95.134 | 8.614 | 6.302 | 0.899 | 10.106 | 0.106 | 60.492 | 0.729 |
| MILP_M | M | 92.013 | 5.389 | 4.877 | 0.682 | 9.589 | 0.257 | 63.629 | 0.349 |
| EQUAL_M | M | 95.684 | 7.030 | 5.284 | 0.763 | 9.029 | 0.132 | 61.431 | 0.502 |
| SIP_M | M | 94.074 | 9.404 | 7.852 | 1.142 | 12.592 | 0.163 | 60.274 | 0.671 |
| ETF_M | M | 97.085 | 4.792 | 4.496 | 0.620 | 7.195 | unavailable | 61.503 | 0.246 |
| GREEDY_C | C | 99.683 | 6.094 | 5.295 | 0.746 | 10.554 | 0.257 | 60.907 | 0.339 |
| V4 | C | 99.958 | 9.031 | 6.492 | 0.927 | 10.483 | 0.106 | 59.136 | 0.761 |
| MILP_C | C | 99.802 | 5.981 | 5.277 | 0.741 | 10.633 | 0.256 | 60.557 | 0.363 |
| EQUAL_C | C | 99.974 | 7.256 | 5.416 | 0.780 | 9.246 | 0.133 | 60.117 | 0.629 |
| SIP_C | C | 99.882 | 9.756 | 8.165 | 1.191 | 12.973 | 0.159 | 58.618 | 0.679 |
| ETF_C | C | 99.930 | 4.876 | 4.573 | 0.631 | 7.328 | unavailable | 60.851 | 0.261 |
| NEUTRAL_M | M | 94.760 | 9.029 | 7.058 | 1.012 | 12.050 | 0.105 | 60.328 | 0.681 |
| NEUTRAL_C | C | 99.938 | 9.417 | 7.307 | 1.048 | 12.365 | 0.104 | 58.714 | 0.719 |


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
