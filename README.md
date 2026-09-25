
## v34 runtime-bloat guard

`at_jev.nim` now includes the v34 FAST scan-work guard, adaptive stride up to 5,
correlation-sized sequential race pools, and stronger near-tie runtime Pareto
pressure. See `GP_SPEED_GUARD_V34.md`. FULL 6x20 scoring and Jev v33 fusion are
unchanged.

# Jev：512トークン GP洗練版 v31（2026-09-25）

- `EMBEDDING_SIZE = 512`。256バイトを512個の内部トークンへ一対一に割り当てます。
- 個体数450・1500ルール・Jev 64モデル×2500ステップ・5世代間隔を維持。
- フィルタ4種と、前版の交叉・突然変異改良を継承。
- FULL学習評価は厳密に 6ケース×20点。hard negativeも追加ではなく20点内の置換で、各Spearmanの標本数を固定。
- FASTは3ケース×8点程度から始め、実測FAST/FULL相関と監査結果に応じて3〜6ケースへ自動拡張。FULLの6×20は削らない。
- 通常突然変異は停滞度に応じた局所上限内の対数一様、探索laneのみ1..Nの対数一様。
- 詳細は `GP_STABILIZATION_V28.md` と `REFINEMENT_512.md`。

```bash
# 新規学習
bash verify_and_run.sh

# 既存checkpointから再開する場合
bash verify_and_run.sh --load
```

512化で演算の意味が変わるため、256版のスコア履歴・アーカイブ・Jev信頼度は
リセットして再評価します。保存形式はcheckpoint v30 / model V12です。v28以前のcheckpointはgenomeを保持しつつ、v30の等重み・厳密6×20 objectiveへ再評価します。

`FILTERS_V26.md` と `validation/v26/`、それ以前のログ・差分は前版の記録です。
今回の設定・検証結果とは区別してください。

## v29 refinement

`at_jev.nim` now keeps the v28 6 x 20 FULL objective, while making variation and screening more local and less exploitable. FAST observations rotate by phase each generation; local mutation operators share one total row budget; embedding mutation is macro-lane-only; ordinary crossovers transfer at most 96 rules except for an explicit macro route; and macro mutation pressure grows with measured stagnation instead of being fixed at 20%. Checkpoint/objective format remains v28-compatible.

See `GP_REFINEMENT_V29.md` for the rationale and expected log fields.

## v30 refinement

v30 fixes a control-loop bug that prevented stagnation pressure from growing: the slow-case baseline is now re-anchored only when a slow case actually refreshes, not on every fast/medium refresh. The six rolling cases now have equal aggregate weight (refresh lifetime controls variance, not importance), hard-negative mining preserves exactly 20 observations per case, crossover operators are compared on the same parent/donor pair, incompatible trace operators are not falsely credited as two-point crossover, and rolling case ages/refresh credits are serialized so resume is dynamically exact.

See `GP_REFINEMENT_V30.md`.


## v31 speed refinement

v31 targets the measured `fast_eval=13.848s` / `full_eval=8.171s` bottleneck without changing the 6×20 FULL objective. FAST starts from one rotating case per timescale (3 cases total), stride 2 is removed, audits and variation probes are decimated, the merit FULL budget adapts from 36–48, per-sample sequence-hash memoization is removed from the hot path, and crossover trace inputs are cut from 12 to 6.

See `GP_SPEED_V31.md`.

## v33 Jev fusion

The current `at_jev.nim` is v33. It is normalized for the 64-model / 6400-step Jev configuration with a 20-generation cadence. See `JEV_FUSION_V33.md` for the external-signal freshness, survivor/nursery, cohort-composition, metric, and checkpoint changes.

## v35 audit/hardening (2026-09-25)
For the latest evaluator/race/Jev correctness and bottleneck audit, see `GP_AUDIT_V35.md` and `v34_to_v35_audit.diff`. FULL remains 6x20; requested Jev 64x6400/20-generation settings are unchanged.
