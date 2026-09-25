# GP / Jev deep audit v35

This pass is deliberately conservative: preserve the FULL objective (6 cases x 20 observations), preserve the requested Jev 64-model / 6400-step / 20-generation setup, and remove correctness hazards or work that is provably redundant before changing more search semantics.

## Fixed in v35

### 1. Match-heavy no-op rules paid two full-state costs
`scoreRaw` previously materialized the rewritten state and then compared `bufB != state` after every matching rule. Detector/no-op rules are allowed to earn weight without changing state, so evolved genomes can become match-heavy and spend a large fraction of time rebuilding and comparing identical sequences.

v35 adds an `outputChanged` result to the compiled replacement path. Literal identity replacements are recognized before rebuilding the state; wildcard replacements determine change while the replacement span is emitted. `scoreRaw` swaps buffers only when the rewrite really changes the state. Matching and weight accumulation semantics are unchanged.

### 2. FAST scan-budget failures could survive too high in a depth-first race
A failed candidate was assigned `-Inf`, but the sequential race orders deeper measurement layers before shallower eliminated layers. Therefore a candidate that reached the 6-case layer and then exceeded its budget could still rank ahead of every candidate eliminated at 3/4/5 cases.

v35 quarantines every FAST budget-failed candidate and appends it after all valid race layers. Independent random FULL audit remains the only rescue path, so the anti-bloat cutoff cannot silently promote the very candidate it rejected.

### 3. FAST budget-failure rate used the wrong denominator
The base FAST job evaluates three cases in one spawned candidate job, but `exceededCases` increments once when that candidate job aborts. The old denominator counted three candidate-cases and could understate the failure rate by roughly 3x.

v35 measures the rate per evaluated candidate job: base jobs + actual jobs in each race stage.

### 4. FAST controller state was lost on resume
Stride, scan-work cap and last FAST/FULL correlation reset to conservative defaults after loading a checkpoint. A healthy long run therefore suffered a repeatable post-resume slowdown and temporarily changed screening behavior.

Checkpoint v32 persists and restores all three controller values. v31 checkpoints remain loadable and receive safe defaults.

### 5. Jev comparison had candidate-ID-dependent random noise
The inner TEXT GA seed used the outer population ID. Population IDs are not exchangeable: elites and other roles tend to occupy structured positions. This made Jev quality partly depend on which stochastic proposal stream happened to be attached to a slot.

v35 uses common random numbers within a Jev round: all outer genomes start from the same stochastic stream for that generation. Fitness-dependent tournament decisions still make searches diverge after scoring, but model-to-model comparisons start from paired stochastic conditions.

### 6. Jev duplicate repair was O(population x suffix length) and spent logical steps on old text
Each offspring was compared linearly against current and next inner populations. v35 uses the already-maintained memo table as the exact historical set. A bounded repair attempts to make a novel suffix; if it still collides, memoized scoring preserves exact 6400 logical-evaluation accounting.

### 7. A built-in budget self-test was a false positive for the clock guard
The old `forcedBudget` left `maxRuleVisits=0`, so it failed on the first rule visit rather than exercising the intended wall-clock branch. v35 tests the wall-clock and logical-visit limits independently.

### 8. Cache-growth diagnostics
The generation log now prints pattern and revision cache entry counts. If a later slowdown is memory/GC related instead of evaluator CPU related, it should become visible instead of being guessed from wall time.

## Intentionally unchanged

- FULL fitness is still exactly 6 cases x 20 observations = 120 rank observations.
- FULL temporal execution remains `ceil(2*sqrt(input.len))`; no FAST shortcut is allowed to redefine the final objective.
- Requested Jev constants remain: 64 models, 6400 logical inner evaluations, inner population 20, elites 3, tournament 3, crossover 45%, immigrants 3%, interval 20, survivor cap 8, MA window 10.
- A no-op match still contributes its rule weight. v35 only avoids redundant state reconstruction; it does not change this modeling choice.

## Remaining watchpoints (instrument first, do not blindly rewrite)

1. **Candidate-index maintenance.** A real state rewrite may rebuild/sort candidate lists. If `candidate_index_rebuilds` grows together with evaluator time, incremental or bucketed maintenance is the next target.
2. **Pattern/revision cache growth.** Watch the new cache-entry counters. If they grow monotonically with RSS/GC spikes, add bounded eviction/generation ownership; compile time is currently small enough that invasive cache work is not justified without evidence.
3. **Wildcard no-op materialization.** Literal identity rules now have a zero-copy path. A wildcard replacement that happens to reproduce its matched span still has to materialize output to prove equality. If profiling shows this family dominating, specialize common wildcard identity plans next.
4. **FAST budget is per trajectory, not cumulative per genome.** Quarantine is now correct and feedback is accurate, but a genome can be individually under budget on every trajectory while still being expensive in aggregate. If FAST tail latency remains high with near-zero budget-failure rate, add measured cumulative candidate work rather than arbitrarily shrinking the per-trajectory cap.
5. **Jev memo hashing.** The linear duplicate scans are gone, but `Table[seq[int], float]` still hashes 64-token suffixes. At a Jev generation, use `actual_score_calls`, `cache_hits`, `score_seconds`, and `max_score_seconds` to decide whether hashing or `scoreRaw` is dominant.
6. **FULL bloat.** FULL is intentionally authoritative and uncapped by FAST scan-work. If `full_eval` dominates while `fast_eval` is healthy, optimize the hot path / selection pressure; do not truncate FULL and quietly change the objective.

## Validation performed here

- Python/static/integration test suite: 80 tests passed.
- Package-level structural checks and source invariants passed.
- Nim is not installed in this execution environment, so the release Nim compilation and native self-tests cannot be run here. Use `verify_and_run.sh` on the target machine before a long run.

## Logs worth keeping for the next 3-5 generations

- `fast_eval`, `full_eval`, `repro_other`
- `screening fast/full spearman`
- `race_budget_rejected`, `fast_budget_failure_rate`
- `fast_scan_work_used`, `fast_scan_work_next`
- `pattern_cache_entries`, `revision_cache_entries`
- `champion_seconds`, `fastest_front_seconds`
- On a Jev generation: `actual_score_calls`, `cache_hits`, `score_seconds`, `max_score_seconds`, `budget_cutoffs`
