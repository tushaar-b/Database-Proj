# Phase 9 benchmark specification

All findings are exploratory comparisons of nine synthetic profiles sharing historical market paths. Previously inspected observations, overlapping windows, surviving-security selection and current sector labels prevent independent-validation or population-level claims.

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


## Reproducible pseudocode

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


Greedy replaces the sector/basket/target loop by first-feasible score-priority one-share additions over all eligible names. Equal-weight replaces that priority by smallest current INR holding. SIP limits the priority order to the three calendar-selected sector representatives. MILP repeatedly solves its linear outer approximation and adds violated norm supporting cuts until a guard-feasible certified solution or a labelled resource limit.

## Complexity and timing scope

With n securities, s sectors, dense covariance guard evaluation costs O(n²+s*n); constructing it also stores O(n²). Sorting is O(n log n). Greedy and equal-weight can attempt O(Q*n) additions in the worst case, where Q is the authorized number of cheapest shares, so these simple implementations are pseudopolynomial in share count. V3 sorts, checks up to n seeds and uses bounded three-name binary quantity searches plus residual loops; an intentionally loose bound is O(n log n+n*G+Q*3*log(Q+1)*G), G=guard cost. No asymptotic superiority follows from a small-universe timing. Integer branch-and-bound has no claimed polynomial bound; outer approximations cap at 80 solves and 3 seconds. Runtime includes pool/witness/guard work but excludes cache generation, downloads and daily valuation. Hardware and versions are in RUN_CONFIG.json.
