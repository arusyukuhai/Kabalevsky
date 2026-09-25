# GP FAST sequential race — v32

v32 keeps the exact FULL objective at 6 independent cases × 20 observations (120 ranks), but changes only the cheap screening path.

## Race schedule

Optional offspring are screened in four nested stages:

- Base: every optional offspring gets 3 FAST cases, one from each rolling timescale.
- Stage 2: only the best 128 receive a fourth case.
- Stage 3: only the best 72 receive a fifth case.
- Stage 4: only the best 48 receive the sixth case.

The final FAST race pool is intentionally 48, equal to `FULL_EVAL_TOP_MAX`, so every merit candidate that can be promoted to FULL has six-case FAST evidence. Tail candidates never pay for the extra cases.

The FAST evaluator still runs the exact same temporal program as FULL (`FAST_EVAL_ROUNDS = SCORE_ROUNDS`); only the number of observations per case is thinned by stride 3/4.

## Why eliminated layers are not directly cross-compared

A 3-case estimate and a 6-case estimate have different uncertainty. v32 therefore freezes each elimination layer at the stage where it lost. Final ordering is:

1. six-case race survivors,
2. five-case eliminated layer,
3. four-case eliminated layer,
4. three-case eliminated layer.

Within each layer every candidate has identical measurement coverage.

## Specialist rescue

Case-specialist rescue uses only the three common base cases, because every optional candidate was measured there. This avoids biasing specialist rescue toward candidates that already survived a race stage.

## Reliability controls retained

- independent random rejection audit remains sparse (every 4 generations normally),
- severe misses restore stride 3,
- very high FAST/FULL agreement may use stride 4,
- FULL selection remains the only fitness used for survival and parenthood.

## New diagnostics

The generation log now reports:

- `sequential_race=true`
- `race_case_order`
- `race_stage_cases`
- `race_stage_sizes`
- `fast_candidate_case_evals`
- `fast_sample_evals`
- `fast_points_per_case`

For ~406 optional offspring, the nominal candidate-case count is about
`406*3 + 128 + 72 + 48 = 1466`, instead of `406*5 = 2030` when five FAST cases are applied uniformly. With stride 4, the sample-level reduction is similar while the top 48 still receive all six FAST cases.
