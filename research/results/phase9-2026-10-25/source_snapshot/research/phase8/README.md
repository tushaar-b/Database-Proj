# IntelliVest Phase 8 research

Isolated portfolio-construction experiments; no database connections or live trading. All older evidence, application files and source are preserved by hashes. Every studied period was previously inspected; these are exploratory results, not independent holdouts. Read config/protocol.md and the five reports in `research/results/phase8-2026-10-24/`.

V1 retains the original monthly policy. V2 carries only valid unused tier-approved monthly quotas with no initial grant; V3 combines feasibility and safeguarded top-ups under monthly reset; V4 combines them; V5 adds purchase redirection. V5_SELL is a separate secondary corrective-selling arm. Construction ablations expose guard, feasibility and top-up interactions. A different grant design would be another policy; this version never silently treats all initial brokerage savings as approved authority.

The completed protocol executed 249 configured replays, plus original V1 reproduction and independent verification replays. Frozen sources, data hashes, settings, cost assumptions, random seed and protected-input manifest are retained in the run. The current commands target this already executed directory and refuse an existing RUN_CONFIG.json. To reproduce in a fresh directory, import the functions with a new Path after copying PRESERVED_HASHES.json; do not delete/overwrite an existing run:

```python
from pathlib import Path
import shutil
from research.phase8.experiments.reproduce_v1 import run as reproduce
from research.phase8.experiments.runner import main
from research.phase8.analysis.finalize import finalize
from research.phase8.experiments.verify import verify

out = Path('research/results/phase8-reproduction')
out.mkdir()
shutil.copyfile('research/results/phase8-2026-10-24/PRESERVED_HASHES.json', out/'PRESERVED_HASHES.json')
reproduce(out)
main(out)
finalize(out)
verify(out)
```

Use repository/research dependencies; exact environment can be recorded with package metadata. In this workspace, matplotlib and matching NumPy dependencies were loaded using `PYTHONPATH=/private/tmp/intellivest-research-deps` to preserve the application's environment. Financial metrics use original 252-session conventions, zero-interest cash as primary and cash-flow-aware daily TWR. Rates are fractions; monetary amounts are INR; durations are observed sessions. HHI excludes cash and is undefined without invested holdings. Guard bootstrap and drift-grandfathering are explicit exceptions, not hidden zero-risk claims.

`authorized_budget_utilization` counts unique external approvals once. `recurring_offered_budget_fill` is separately labelled and must not replace that denominator when authority carries. Recycled sale proceeds are tracked separately and never treated as household income. Current-month reference exceedance is reported even when old approvals validly fund a purchase. New household draw, reserve and authority violations are separate metrics. No brokerage withdrawal schedule is used in these experiments; the revocation primitive is verified, and real withdrawal flows would require explicit cash-flow events.

Future application integration, automatic selling, taxes and new policy tuning are outside this research implementation. No original paper or conference draft is overwritten.
