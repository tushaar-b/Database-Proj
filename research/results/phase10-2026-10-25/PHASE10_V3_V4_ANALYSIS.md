# V3/V4 complexity–benefit analysis

Exploratory evidence from nine synthetic investor profiles and previously examined historical paths. No independent holdout, unbiased point-in-time universe or population-level investor inference is established.

## Financial and construction separation

All 432 matched V3/V4 quantities are identical at equal state/authority, in both F3 and Fwide. The 18 primary authority-instrumented accounts reproduce prior financial outcomes; six shock accounts and twelve targeted lifecycle checks were also executed. V4 is not a different share constructor.

| scenario | authorized_budget_utilization | mean_invested_allocation | annualized_return | annualized_volatility | cvar95 | maximum_drawdown | transaction_fees |
|---|---|---|---|---|---|---|---|
| high_aggressive | 2.585 | 1.921 | 0.664 | 0.325 | 0.049 | 0.800 | 92.951 |
| high_conservative | 3.308 | 0.560 | 0.149 | 0.051 | 0.007 | 0.097 | 39.652 |
| high_moderate | 2.417 | 1.266 | 0.298 | 0.194 | 0.028 | 0.164 | 57.960 |
| low_aggressive | 7.460 | 2.442 | 0.482 | 0.326 | 0.055 | 1.133 | 13.414 |
| low_conservative | 10.187 | 1.156 | 0.299 | 0.201 | 0.027 | 0.520 | 6.106 |
| low_moderate | 5.048 | 1.148 | 0.149 | 0.097 | 0.019 | -0.052 | 6.051 |
| medium_aggressive | 3.627 | 1.719 | 0.914 | 0.205 | 0.028 | 0.646 | 26.087 |
| medium_conservative | 4.473 | 0.660 | 0.125 | 0.093 | 0.011 | 0.112 | 10.723 |
| medium_moderate | 4.307 | 1.330 | 0.680 | 0.211 | 0.026 | -0.030 | 20.652 |


Rate differences are percentage points. Mean V4−V3 utilization +4.82pp, invested exposure +1.36pp, annualized return +0.418pp, daily CVaR +0.0278pp and drawdown +0.377pp. Mean transaction fees increase INR30.40 over four years. Profile effects vary; drawdown does not increase in every profile. These observations do not identify a universal household utility benefit.

## Measured operational state

| policy | instrumented_operations | max_outstanding_lots | max_approval_IDs | max_spend_IDs | median_transition_microseconds |
|---|---|---|---|---|---|
| V3 | 1652.000 | 1.000 | 48.000 | 143.000 | 7.917 |
| V4 | 1650.000 | 3.000 | 48.000 | 141.000 | 8.020 |


| policy | action | events | total_INR |
|---|---|---|---|
| V3 | approve | 432.000 | 9000000.000 |
| V3 | expire | 423.000 | 268883.106 |
| V3 | spend | 1220.000 | 8724958.231 |
| V4 | approve | 432.000 | 9000000.000 |
| V4 | spend | 1218.000 | 8998829.044 |


The first table counts method-entry month-review/spend operations; the second reports actual ledger events, including expiry. V4 can have fewer operations because its holding path yields different trade counts. Complexity is not measured by lines of code. V4 carries dated approval lots, FIFO balances, expiry/revocation reasons and spending identity state. The primary observed maximum is three outstanding lots versus one under V3; no-spend lifecycle tests reach twelve before expiry. Both versions retain approval and spending ID sets, whose growth is distinct from the bounded lot count.

Twelve actual checks cover no initial grant; duplicate approval; duplicate debit; overspend; 11/12-month boundary; reduced household capacity; FIFO crossing; monthly expiry; explicit revocation primitive; cash/authority mismatch; duplicate recycled proceeds; exact full spend. All passed. Shock inputs suspend buying January–March 2024 after capacity review. Explicit brokerage withdrawals and concurrent production persistence were not simulated.

## Operational risks and recommendation

Potential integration failures include lost/duplicated approvals after retries, cash reconciliation errors, incorrect calendar aging, FIFO double debits, failure to revoke carry, and concurrent or non-atomic cash/authority writes. The research primitives detect selected invalid operations but do not test database atomicity, persistence recovery, live withdrawals or tax handling. Additional production engineering would be necessary.

**Recommendation: B — optional extended policy.** V3 is the simpler research default. V4 may suit an explicit preference for approval carry-forward, but is not justified as the preferred default solely by higher deployment. Both remain research-isolated; this recommendation does not authorize deployment. Additional independent periods and operational persistence/withdrawal tests are needed before integration.
