# Jev / Outer-GA fusion refinement v33

v33 retunes the Jev bridge around a 20-generation external-evaluation cadence and the requested 64-model, 6400-step inner TEXT-GA configuration. The goal is to keep Jev useful as an external selection signal without letting old Jev measurements dominate the much faster outer GP loop.

## Requested Jev configuration

- `JEV_MAX_MODELS = 64`
- `JEV_DEFAULT_MODELS = 64`
- `JEV_GENERATION_INTERVAL = 20`
- `JEV_STEPS = 6400`
- `JEV_SUFFIX_LENGTH = 64`
- inner population `20`, elites `3`, tournament `3`
- crossover `45%`, immigrants `3%`
- direct survivor slots `8`
- Jev moving-average window `10`

The expensive Jev round is 2.56x deeper than the previous 2500-step setting, but it runs only once every 20 outer generations instead of once every 5. The nominal amortized inner-search work therefore falls from `64*2500/5 = 32,000` to `64*6400/20 = 20,480` inner candidate evaluations per outer generation (36% lower).

## Main integration fixes

### 1. One cadence, not two conflicting clocks
`FUSION_INTERVAL` now aliases `JEV_GENERATION_INTERVAL`. Jev sampling, calibration, pending-child due dates, and external-signal aging all share the same 20-generation clock.

### 2. Separate Jev reliability from Jev freshness
`fusionReliability` measures repeat-ranking consistency; it no longer doubles as a time-since-measurement value. `fusionFreshness()` decays external evidence to zero across the 20-generation interval, and `fusionInfluence()` combines the two. A technically unavailable Jev call therefore makes the old evidence go stale naturally instead of incorrectly declaring the rubric unreliable.

### 3. Cadence-normalized donor pressure
The old 25% external donor pressure was appropriate only for a short cadence. v33 caps Jev-specific donor mating at 12% and multiplies it by reliability × freshness. Its integrated pressure over a 20-generation cycle is close to the old 25%-over-5-generations regime, but it cannot keep stale Jev evidence fully active for twenty generations.

### 4. `JEV_SURVIVOR_SLOTS=8` is now a real population cap
The fusion archive may retain up to 16 nondominated points for Pareto-shape memory, but only up to 8 can be directly injected as Jev survivors. Before Jev reliability is established, the direct quota is further restricted and decays with freshness.

### 5. Pending Jev children are a nursery, not pseudo-elites
Previously pending children could be injected repeatedly every generation while waiting for the next Jev round. With a 20-generation interval this would protect unmeasured children for far too long. v33 keeps them off-population and injects them only when their next Jev evaluation is actually due. The old hidden “exact pending genome gets FULL evaluation” privilege was removed as well.

### 6. Nursery reservoir sampling
The first eight Jev-mating children no longer freeze the pending nursery for the whole interval. Unique pending candidates are reservoir-sampled across all Jev-fusion births, so late high-quality/diverse children still have a fair chance to reach the next external cohort. The reservoir count is checkpointed.

### 7. Missing calibration is not negative evidence
Reliability is updated only when enough repeat pairs are available. API/bridge failure leaves reliability unchanged and lets freshness decay; it does not halve trust merely because the evaluator was unavailable.

### 8. Fixed-range G/J normalization for Pareto hypervolume
Pareto dominance still uses the original G/J scores, but hypervolume pruning now maps both axes to fixed known ranges before measuring area. This removes the old scale bias toward the wider G axis without introducing unstable cohort-dependent min/max normalization.

### 9. Balanced 64-model Jev cohort
A full Jev cohort now has explicit lanes rather than allowing historical repeats to crowd out exploration:

- up to 8 repeat anchors for calibration,
- up to 8 fresh nursery children,
- up to 8 prior-front repeats,
- 24 GA-merit candidates,
- the remainder from broad rank-stratified exploration.

With all repeat lanes populated, at least 16 of 64 positions remain broad exploration. If repeat lanes are sparse, the unused capacity goes to exploration.

### 10. Progress metric excludes historical-repeat contamination
Historical anchors/front repeats are still sent to Jev because they are useful for calibration and ranking context, but they are excluded from the plotted progress statistic. The primary metric is now `jev_fresh_rank_weighted_quality`, computed from fresh candidates only, with a 10-event moving average. This prevents deliberate reinjection of old known-good models from masquerading as current GP progress.

### 11. Stronger configuration fingerprint
The Jev configuration hash now includes cadence, 6400 steps, suffix/candidate count, all inner-GA parameters, survivor slots, MA window, algorithm revisions, internal token count, and the fresh-quality metric version. Material Jev changes therefore invalidate incompatible cached Hall/fusion/history state instead of silently mixing experiments.

### 12. Checkpoint compatibility
Checkpoint format is bumped to v31 to store the nursery reservoir count. v30 checkpoints remain loadable; genomes are preserved while incompatible Jev/fusion evaluation state is reinitialized when the objective/configuration fingerprint changes.

## New diagnostic output

Jev rounds print cohort lane counts such as:

```
jev-cohort: anchors=... pending_fresh=... front_repeat=... merit=... broad_explore=... fresh_metric=...
```

Between Jev rounds, fusion pressure is visible via:

```
jev-influence: trust=... freshness=... effective=... donor%=... survivor_cap=8 nursery_cap=...
```

The Jev quality line separates fresh progress from the all-cohort calibration context:

```
jev: fresh_quality_rank_weighted=... fresh_mean=... cohort_mean_all=... fresh_top8_quality=... rank_weighted_ma10=...
```

## Validation performed here

The package's Python/static suite passes (`91 passed, 33 subtests passed` under pytest; `70 tests OK` under unittest discovery). This environment does not include the Nim compiler, so a native Nim compile/run still needs to be performed on the target machine before a long experiment.
