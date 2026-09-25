# GP stabilization v28

This revision targets the late-stage plateau visible around generations 3000–6000: training Spearman stays high while the external Jev quality oscillates instead of improving consistently.

## Objective / rolling dataset

- Six independent rolling trajectories: `CASES_PER_TIMESCALE=2`, `MULTI_CASE_COUNT=6`.
- Twenty rank points per trajectory: `RETAINED_SAMPLES_PER_CASE=20`.
- Total FULL observations remain 120, but there are now six independent base chunks rather than three.
- FAST/MEDIUM/SLOW per-case lifetimes are approximately 8/16/32 generations.
- A credit scheduler refreshes at most one case per generation. Each group event refreshes only the oldest of its two cases, so both members are not replaced together.
- Stable cases receive more aggregate weight: FAST/MEDIUM/SLOW = 1/2/3.

The 6×20 layout was chosen instead of fragmenting the same budget into many very short trajectories, because Spearman becomes too discrete/noisy at small sample counts.

## FAST evaluation

FAST and FULL now execute the same temporal program (`FAST_EVAL_ROUNDS = SCORE_ROUNDS`). FAST saves work only by sampling fewer observations. This removes the previous phenotype mismatch where a program requiring more than 12–16 replacement rounds could be rejected before FULL evaluation.

FAST stride starts at 3 and adapts between 2 and 4 on the 20-point trajectories.

## Mutation locality

Mutation counts remain log-uniform, but exploitation and exploration have different valid ranges:

- exploitation: log-uniform in `1..32` affected rules;
- exploration: log-uniform in `1..genome.len`.

The same cap is passed to embedding mutation. This preserves the project's rule that count-bearing mutations are logarithmically sampled, while making genuine local refinement possible near convergence.

Variation is split into three paths: mutation-only, crossover-only, and crossover+mutation. A crossover child is no longer unconditionally mutated.

## Selection bandwidth / archive

- `ARCHIVE_INJECT_COUNT`: 40 -> 8.
- `ARCHIVE_INJECT_INTERVAL`: 1 -> 4.
- The 42 merit FULL evaluations are now additive to protected incumbents instead of being reduced by the protected prefix.

This prevents historical elites from consuming most of the new-offspring FULL-evaluation bandwidth.

## Crossover traces

Homologous/module crossover traces use up to 12 observations (two from each of the six trajectories) instead of only two total observations.

## 512-token latent access

Literal mutation has a small direct route to any normal 0..511 internal token. Previously ordinary literals were generated only through the 256 byte-mapped coordinates, making the other latent coordinates difficult to address directly.

## Diffusion bug fix

Raw corruption is now strictly byte-domain 0..255:

- local clamp upper bound: 256 -> 255;
- alphabet fallback: `mod 257` -> `mod 256`.

This prevents training corruption from accidentally manufacturing raw value 256, which the embedding layer interprets as OOV 512 and could become a shortcut cue for damage.

## Guided credit

`CREDIT_REFRESH_INTERVAL` is reduced from 64 to 16 generations so rule guidance does not remain stale across many rolling-case changes.

## Persistence

Checkpoint/objective version is v28. v27 checkpoints remain readable; genomes are retained, while old objective-dependent fitness/archive state is reset and the six 20-point rolling cases are rebuilt.

## Validation in this package

The Python/static test suite passes (53 tests). The current execution environment does not contain the Nim compiler, so the Nim release build and embedded Nim test modes could not be executed here. Run `bash verify_and_run.sh` on the development machine before a long production training run.
