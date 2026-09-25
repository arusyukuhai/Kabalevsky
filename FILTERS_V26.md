# Capture filters and genetic-operation refinement (2026-09-25)

Base: jev_embedding256_optimized_audited_20260924.zip, Library version 4.
This is the latest available continuation of the adaptive-fusion package.
It has 256 internal tokens, 450 genomes, 1500 rules, and Jev 64×2500 every 5 generations.
Those settings and the adaptive-fusion selection policy are preserved.

## Added replacement filters

Each instruction acts on the entire captured sequence `$n`, keeps its length,
and emits nothing for an empty capture. Banks each support captures 1..16.
Old opcode meanings have not changed.

| Opcodes | Operation |
|---|---|
| -112..-127 | `(-x) mod EMBEDDING_CODE_COUNT` for each internal token |
| -128..-143 | Fill every element with `floor(sum(x)/length)` |
| -144..-159 | Fill every element with the median; for even lengths use the floor of the average of both middle elements |
| -160..-175 | `floor(mean + (x-mean)/2)` for each element, using the exact mean before final rounding |

In the current 256-token space, modular negation equals `(512-x) mod 256`.
This does NOT change the vocabulary to 512. Like existing modular +1/-1/*2,
negation preserves the OOV sentinel 256. Mean/median fill are unconditional,
including OOV positions; their statistics include every captured value.
Contraction also includes every value, without a threshold or conditional mask.
Statistics use numeric encoded token IDs, not decoded characters or circular means.

Examples (all are capture-wide):

- `[0,1,255]` negated -> `[0,255,1]`.
- `[0,1,8]` mean fill -> `[3,3,3]`; median fill -> `[1,1,1]`.
- `[0,1,8]` contracted -> `[1,2,5]`.
- `[0,3]` contracted -> `[0,2]`: the mean is not prematurely rounded to 1.

Sum/contraction use int64 integer arithmetic. Median reuses the worker-local
sort buffer; its cost is O(n log n), while the other three new filters are O(n).
Existing opcode execution paths retain their original behavior.

## Genetic changes

- 35% of triggered pattern/replacement edits are now replacement-only.
  This makes it possible to explore a filter without first destroying its matcher.
- In that branch, when a capture reference exists, 70% of edits change only
  its operator family, preserving the capture number. The old family is excluded;
  capture 16 cannot accidentally become the nonexistent legacy direct `$16`.
- All ten filter families are available to both initialization and mutation.
  Random replacement-opcode sampling retains 50% direct references and assigns
  the remaining 50% uniformly to the ten function families.
- Mutation target counts retain the existing full-range logarithmic sampling.
- The common two-point crossover skips a redundant coordinate-transplant-table
  preparation. The resulting crossover semantics and random draws are unchanged.
- Block relocation/duplication now always picks a different destination when the
  initial destination equals the source. The old fallback could pick the source again.
- Generation offspring's forced-novelty fallback now excludes the actual current
  token, rather than always excluding alphabet index zero.

These changes expand reachable variations and remove specific wasted operations.
They do not establish a learning-quality or whole-program speed improvement.

## Persistence and execution

Checkpoint writer: v26. Energy model writer: V11.
The checkpoint objective version stays 25: adding new reachable instructions does
not change the meaning of an existing valid v25 genome or invalidate its scores.
v25 checkpoints and V10 models remain readable; histories are preserved on v25 load.
Older migrations remain as before. New saves should not be loaded with old executables.
V1 header collisions at rule counts 48/49/304/305 are explicitly tested.

Run:

```bash
bash verify_and_run.sh --load
```

The runner includes the new `--filter-test`, existing regression tests, and
backup-before-training behavior. Full compilation in this environment uses
Nim 2.2.4/release/ORC/threads:on, with a no-op progress module ONLY in the test
search path. The distributed source still imports the normal progress dependency.

Validation logs for this revision are in `validation/v26`; the other validation
logs describe the preceding version and must not be attributed to this revision.
External Jev service and real production checkpoint training are not exercised.

## Completed validation

- Nim 2.2.4 release/ORC/threads:on build succeeds.
- New filter test: 4000 randomized comparisons, captures 1..16, empty inputs,
  negative rounding, OOV inclusion, invalid bounds and output limits.
- 2000 mutation trials check parent immutability, valid opcodes, new-family
  reachability and replacement-only edits. All four crossovers are exercised.
- V10/V11 model roundtrips and V1 header-collision regression succeed.
- Existing bottleneck/refinement/fusion/generation-index/regression/self tests pass.
- Existing Python suite: 52 tests pass (format expectations updated to v26/V11).
- 450-genome / 16-rule offline fixture: 16 generations, three 64×2500 Jev cohorts.
  Per-generation parent accounting, parent immutability, elite retention, embedding
  validity and no unresolved exact duplicates all pass. Jev uses an explicit local mock.
- v26 checkpoint resume preserves generation 16, 20 archive entries and 16 graph points.
- A checkpoint actually produced by the preceding v25 source is loaded by v26 at
  generation 4, preserving four archive entries and four graph points; learning
  continues to generation 16 and saves in the new format.

These are implementation checks, not evidence of production learning improvement.
The 16-rule fixture does not measure full 1500-rule long-run performance.
