# GP speed guard v34

v34 addresses a different bottleneck from v31/v32. The sequential race already
reduced the number of FAST observations, but evolved genomes can themselves
become much more expensive to execute. In the reported regression, FAST sample
count fell while wall time rose because the population's runtime roughly doubled
or tripled.

## Changes

- FULL scoring is unchanged: six cases x twenty observations and the same
  natural `ceil(2*sqrt(input.len))` temporal execution.
- FAST starts at stride 4 and may move to stride 5 after very strong FAST/FULL
  agreement; audit failures restore stride 3.
- FAST gains a deterministic `scanWork` budget. Every candidate-rule scan is
  charged by current state length, a proxy for the expensive replacement hot
  path. The default budget is 40M units per sample, min 20M, max 160M.
- The scan-work budget is FAST-only. A budget-exceeded candidate receives the
  ordinary FAST invalidation (-1 for that staged evaluation); FULL evaluation
  remains exact and uncapped by this new budget.
- The scan-work cap adapts: bad screening/audit evidence widens it aggressively;
  very strong agreement with few budget misses narrows it gradually.
- Sequential race pools become correlation-sensitive: 128/72/48 in recovery,
  112/64/44 in normal high-confidence operation, and 96/56/40 when correlation
  is >=0.985. The deepest 40 pool still exceeds the 36 merit FULL target used
  in that high-confidence regime.
- Runtime Pareto parent pressure is strengthened only inside the existing near-
  best fitness slack: time advantage threshold 1.6x -> 1.4x and Pareto-parent
  share 30% -> 40%. The absolute fitness champion is still always eligible.
- Logs now expose the race pool targets, scan-work budget used/next, and FAST
  budget-failure rate.

## Why this is needed

The v33 Jev changes do not run at generation 7 (`jev=0.000`) and do not alter
`scoreRaw`. The slowdown instead tracks computational bloat in the evolved
programs themselves. A race can reduce *how many* candidates are evaluated,
but it cannot bound a candidate whose replacement program has become several
times more expensive. v34 adds that missing cost control while preserving the
FULL objective.
