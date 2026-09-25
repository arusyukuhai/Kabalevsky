# GP speed refinement v31

v31 keeps the **FULL objective exactly 6 cases × 20 observations**. It changes only how much work is spent before a candidate earns a FULL evaluation, plus two semantics-preserving hot-path optimizations.

## Why v30 was slow

The supplied gen=36 log showed:

- `fast_screened=400`
- FAST had `fast_points_next=[11,11,11,11,11,11]`
- `fast_eval=13.848s`
- `full_evaluated=120`
- `full_eval=8.171s`
- `trace_seconds=1.2925`

At stride 2, FAST therefore runs about `400 × 6 × 11 = 26,400` `scoreRaw` trajectories per generation. The measured FAST/FULL rank correlation was already `0.958`, so paying for six dense cases on every rejected child was excessive.

## v31 changes

### 1. FAST starts at 3 rotating cases, not 6

The six FULL cases are grouped by timescale as `{0,3}`, `{1,4}`, `{2,5}`. FAST always chooses one member from each group and alternates the member by generation. Thus every screening generation still sees FAST/MEDIUM/SLOW evidence, but only three cases are paid for initially.

At stride 3, each 20-point trajectory contributes exactly 8 FAST observations. With 400 screened candidates, the normal cost is therefore approximately:

`400 × 3 × 8 = 9,600 trajectories`

versus v30's observed:

`400 × 6 × 11 = 26,400 trajectories`.

That is a **63.6% reduction in FAST trajectory evaluations** before any lower-level speedup.

The case count adapts between 3 and 6 from measured FAST/FULL Spearman. If screening becomes unreliable or the rejection audit finds a serious miss, coverage expands automatically. Temporal execution itself is never truncated: `FAST_EVAL_ROUNDS == SCORE_ROUNDS` remains true.

### 2. No return to stride 2

v30's audit logic could force `stride=2`, which increased each case from ~8 to 11 observations and was the immediate reason the supplied generation became expensive. v31 uses stride 3 normally and permits stride 4 only after very strong measured agreement. Poor agreement restores stride 3 rather than 2.

### 3. Rejection audits are sparse

The independent rejection audit remains, but it is no longer eight FULL candidates every generation. Normally it evaluates four candidates every fourth generation. If the previous screening correlation is poor, it immediately falls back to an eight-candidate recovery audit.

### 4. Probe overhead is decimated

Mutation probes are four children every two generations instead of six every generation. Matched crossover probes run every four generations instead of every generation. Their EMA feedback remains intact but no longer consumes a large permanent fraction of the FULL budget.

### 5. FULL merit bandwidth is adaptive

The normal merit target remains 42. When the previous FAST/FULL correlation is strong it drops to 36; when screening is weak it expands to 48. Protected incumbents still do not consume these newcomer merit slots.

### 6. Removed an almost-always-miss hash table from `evaluateChunk`

Each 20-point diffusion trajectory is intentionally damage-distinct. v30 nevertheless created a `Table[seq[int], float]` for every genome/case and hashed each entire input sequence to look for exact duplicates. Exact duplicates are rare here, so this performed long sequence hashing almost every observation without a cache hit. v31 evaluates directly; an accidental duplicate is simply recomputed, which is semantically identical.

### 7. Crossover trace sample count 12 → 6

The supplied log spent 1.29s building crossover traces. v31 keeps one trace sample per rolling case instead of two, halving this input workload while retaining all six contexts.

## What must not change

- FULL selection fitness: exactly six equal-weight case Spearmans.
- 20 observations per FULL case.
- Full temporal `scoreRaw` semantics.
- Log-uniform mutation counts.
- FULL-only final ranking/parenthood.

## New log fields

`screening` now prints `fast_cases_used`, `fast_cases_next`, `fast_points_used`, `audit_due`, and `merit_full_target`. These are the first fields to inspect if runtime rises again.
