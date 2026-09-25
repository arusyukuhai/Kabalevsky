# GP refinement v29

This pass keeps the v28 training objective: six rolling cases, 20 diffusion observations per base trajectory, identical FULL temporal semantics in FAST and FULL, and the same checkpoint/objective format. It changes *how candidates are generated and screened*, not what a FULL score means.

## Changes

- **Rank-resolution retry.** A trajectory step may retry the same bounded corruption kernel up to four times when the positional damage target did not move. This reduces adjacent target ties without inventing labels: every target is still recomputed from the actual corrupted state.
- **Rotating FAST subset.** FAST keeps endpoints but rotates the interior stride phase each generation. A lineage can no longer optimize indefinitely for one fixed 8-ish-point subset of each 20-point trajectory. FULL still uses all observations and all natural rewrite rounds.
- **One local mutation budget.** Structure, differential-weight, fine-weight, insurance, and sign mutations now spend from one per-child row budget. The old implementation could independently draw K rows for several operators and silently turn a nominal 32-row mutation into a much larger edit.
- **Adaptive local width.** The local cap rises smoothly from 12 to 48 rules with stagnation. Macro mutation remains a separate full 1..N log-uniform lane.
- **Adaptive macro frequency.** Full-range mutation starts at 5% of mutation events and rises toward 20% only on sustained plateaus. Asexual/local reproduction is correspondingly more common while progress is healthy.
- **Embedding edits are macro-only.** A mapping edit can affect the interpretation of many rules, so it no longer bypasses the local row budget. Ordinary donor rules are already recoded into the child mapping during transplant.
- **No post-crossover embedding splice.** Creating a third coordinate map after a rule crossover fragmented trace-guided homology. Embeddings still evolve through explicit macro mutation.
- **Local crossover vs macro crossover.** Homologous/module/two-point transfer is normally capped at 96 rules. A 12% segment-level macro route and the explicit `coMacro` operator preserve full-range exploration.
- **Crossover allocation uses evidence.** Because every crossover operator already receives a paired FULL probe each generation, blind uniform operator exploration is reduced from 40% to 20%; the remaining 80% follows the measured EMA.
- **Resume continuity.** Serialized stagnation is no longer unconditionally reset on an ordinary resume; the slow-case baseline is simply re-anchored.

## Expected log fields

Look for `variation: local_cap=... asexual%=... macro_mutation%=... crossover_macro%=...` plus the existing mutation/crossover paired probes. On healthy improvement, local caps and macro rates should remain low. During a genuine plateau, they widen gradually instead of jumping every child into a 1..1500 edit regime.
