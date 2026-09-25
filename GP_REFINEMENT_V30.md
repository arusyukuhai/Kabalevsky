# GP refinement v30

v30 keeps the v29 representation, 450-individual population, 1500-rule genome, full temporal evaluator, local/macro mutation split, and rotating FAST subset. It changes the training-control semantics where v29 still had hidden bias or confounding.

## 1. Exact 6 x 20 objective

`mineCorruptions` no longer appends hard negatives. A mined hard negative replaces the interior trajectory observation with the nearest target rank, so every case remains exactly 20 observations and every generation remains exactly 120 training observations. This matters because the statistic being optimized is per-case Spearman; silently making medium/slow cases 21 points gave them different rank resolution.

## 2. Equal case weights

All six trajectories are draws from the same corpus objective. FAST/MEDIUM/SLOW describe refresh lifetime, not importance. v29 weighted them 1:2:3, which meant slow cases both survived longer and counted more in every aggregate score. v30 uses equal aggregate weight for all six cases. Fresh-case maturity remains only a lexicase-order heuristic.

## 3. Stagnation controller bug fix

Stagnation is measured on the two slow cases, but v29 reset `slowEpochInitialized` and decayed stagnation after *any* rolling refresh. Since FAST/MEDIUM/SLOW refresh events occur frequently, the controller rarely accumulated enough stagnation to widen local mutation or raise the macro lane. v30 re-anchors and decays stagnation only when a slow case actually changes.

This is the most important behavioral fix in v30: the adaptive exploration schedule can now actually reach the regimes it was designed to use.

## 4. Matched crossover experiments

Every eligible crossover operator is now probed on the same parent/donor pair. v29 used a different random pair for each operator, so paired FULL deltas still confounded operator quality with mating-pair quality. v30 removes that confound.

Trace-guided operators (`coHomologous`, `coModule`) are also excluded when the two embeddings differ. Previously they silently fell back to two-point crossover while the resulting gain was credited to the originally requested operator.

## 5. Exact resume dynamics

Checkpoint v30 serializes `rollingCaseAge` and `rollingRefreshCredit`. Older checkpoints reconstructed these approximately from the generation number, losing which member of each two-case timescale had actually refreshed most recently. v30 resumes the rolling scheduler exactly.

Because the objective itself changes (equal weights and exact hard-negative sample count), v28/v29 checkpoint genomes are retained but old objective-dependent scores, archive state, Jev trust and rolling dataset are rebuilt.

## Validation

The bundled Python/static suite passes 69 tests plus 33 subtests. The execution environment used to prepare this revision does not include a Nim compiler, so the final Nim compile/run still needs to be performed on the target machine with `verify_and_run.sh`.
