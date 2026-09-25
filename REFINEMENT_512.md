# 512-token refinement

## Current configuration

EMBEDDING_SIZE=512, EMBEDDING_ENTRY_COUNT=256, OOV=512. Mapping destinations
are unique, but may be any 256 of the 512 token IDs. The other coordinates are latent.
Population 450, rules 1500, Jev 64×2500 every five generations remain unchanged.

All added filters from v26 are retained, with the same opcode banks:

| Bank | Definition |
|---|---|
| -112..-127 | `(512-x) mod 512`; OOV preserved |
| -128..-143 | Fill every captured position with floor(mean) |
| -144..-159 | Fill every position with floor(median); even lengths average both middle values |
| -160..-175 | `floor(mean + (x-mean)/2)` |

Each bank addresses captures 1..16, preserves length, and emits nothing on an
empty capture. Mean and median include all captured values, including OOV.

## Improvements

1. Embedding mutation can move a byte into a uniformly chosen unused coordinate.
   A free-coordinate array is built once per embedding-mutation event, then updated
   with swaps. It does not repeatedly scan 512 slots per mutation step.
2. Transplant/recode computes a complete bijection over all 512 coordinates.
   Byte correspondences are fixed first, unused identity correspondences are kept,
   and remaining sources/targets are paired in order. Latent symbols cannot collide
   with byte symbols. Reversing the two maps yields the inverse translation.
3. Median for length >=128 uses an exact 513-bin histogram for tokens 0..512.
   Short sequences or any out-of-domain token use the existing exact sort fallback.
   Long ordinary captures therefore cost O(n+513), instead of O(n log n).
4. Mean-centred contraction removes division by a variable denominator per element.
   For integer x and real m, `floor((x+m)/2) = floor((x+floor(m))/2)`.
   The fractional part of m contributes less than one half and cannot cross an
   integer boundary. This remains exact for negative values; it is not an approximation.
5. Operator-only mutation selects a capture position by count and ordinal scan,
   eliminating its temporary sequence while preserving uniform selection and RNG draws.

Target-count distributions remain logarithmic. Adaptive-fusion policy is unchanged.
No claim is made that these changes improve learning quality on the real corpus.

## Persistence

Checkpoint v27 and energy model V12 prevent old executables silently accepting
new semantics. Existing read paths remain. 256-token checkpoints retain genomes
and move OOV 256 to 512, but old scores, elite archive and Jev reliability are reset.
Normal 512-to-512 resume retains state. Checkpoint migration is not the focus of this revision.

## Verification and measurements

Nim 2.2.4, release, ORC, threads:on. The test build uses a no-op progress module
only in an external test search path; the distributed source imports normal progress.
New filters are checked against independent formulas on 4000 cases with lengths
0..2048, signed/out-of-domain values and OOV. All 16 capture indices and bounds
are checked. 100 random pairs of 512-space maps are tested for bijection and inverse
roundtrip; mutation is checked to actually reach the upper half of the vocabulary.

A synthetic isolated-filter benchmark uses identical inputs and 3000 iterations.
At length 128/512/4096, histogram median was approximately 9.4×/18.4×/34.8× faster;
contraction approximately 1.15×/1.28×/1.11×. Short captures show no clear gain.
These are single-run component measurements, not overall training speedups.
The exact timings are in `validation/v27/bench512.log`.

External Jev API and production long-running 1500-rule training are not measured.

Final checks: all seven Nim test modes (filter, regression, self, bottleneck,
refinement, fusion, generation-index) pass; Python 52 tests pass. Offline
450-genome / 16-rule integration passes 16 generations and three 64×2500 Jev
cohorts with parent immutability, accounting, elite retention and embedding
invariants asserted. The Jev service is replaced by an explicit local mock.


## v28 training stabilization

The 512-token representation and model V12 inference semantics are retained. Training/checkpoint objective is v28; see `GP_STABILIZATION_V28.md` for the 6×20 rolling objective, exact FAST temporal semantics, bounded local log-uniform mutation, archive bandwidth changes, diffusion-byte fix and crossover-trace widening.
