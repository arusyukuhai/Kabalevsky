from pathlib import Path

CODE = (Path(__file__).parent / "at_jev.nim").read_text()


def body(start, end):
    a = CODE.index(start)
    b = CODE.index(end, a)
    return CODE[a:b]


def test_requested_jev_budget_and_cadence():
    for marker in (
        "const JEV_MAX_MODELS = 64",
        "const JEV_DEFAULT_MODELS = 64",
        "const JEV_GENERATION_INTERVAL = 20",
        "const JEV_STEPS = 6400",
        "const JEV_SUFFIX_LENGTH = 64",
        "const JEV_INNER_POPULATION = 20",
        "const JEV_INNER_ELITES = 3",
        "const JEV_INNER_TOURNAMENT = 3",
        "const JEV_INNER_CROSSOVER_PERCENT = 45",
        "const JEV_INNER_IMMIGRANT_PERCENT = 3",
        "const JEV_SURVIVOR_SLOTS = 8",
        "const JEV_MA_WINDOW = 10",
    ):
        assert marker in CODE
    assert "const FUSION_INTERVAL = JEV_GENERATION_INTERVAL" in CODE


def test_external_influence_is_reliability_times_freshness():
    f = body("proc fusionLatestGeneration()", "proc bestArchiveEntry()")
    assert "fusionReliability * fusionFreshness(iter)" in f
    assert "JEV_MAX_DONOR_PERCENT = 12" in CODE
    assert "float(JEV_MAX_DONOR_PERCENT) * jevInfluence" in CODE
    assert "25.0 * fusionReliability" not in CODE


def test_pending_children_are_due_only_and_reservoir_sampled():
    f = body("proc fusionInject(", "proc bestArchiveEntry()")
    assert "if generation == pending.due:" in f
    assert "if generation <= pending.due" not in f
    repro = body("if fusionMating and nurseryCap > 0:", "offspringBuckets.mgetOrPut")
    assert "inc fusionPendingSeen" in repro
    assert "let reservoirIndex = rand(fusionPendingSeen - 1)" in repro
    assert "fusionPending[reservoirIndex] = candidate" in repro


def test_jev_snapshots_do_not_get_hidden_full_privilege():
    screening = body("let protectedCount = min(protectedPrefixCount, pop_size)",
                     "var fastIds: seq[int] = @[]")
    assert "fusionMatch(population[jp], fusionArchive)" not in screening
    assert "pending.due" not in screening


def test_cohort_keeps_calibration_merit_and_exploration_separate():
    c = body("let target = min(jevModelCount, fullOrder.len)", "let jevStarted = epochTime()")
    assert "anchorAdded" in c and "pendingAdded" in c and "frontRepeatAdded" in c
    assert "let meritQuota = max(1, (target * 3) div 8)" in c
    assert "broad_explore" in c
    assert "repeatIds" in c


def test_progress_metric_excludes_historical_repeats():
    m = body("var freshRanked: seq[int] = @[]", "comparisons=\", jevResult.pairComparisons")
    assert "if id notin repeatIds: freshRanked.add(id)" in m
    assert "fresh_quality_rank_weighted" in m
    assert "rank_weighted_ma\", JEV_MA_WINDOW" in m
    assert "fresh_rank_linear_weighted_v2" in CODE


def test_pareto_hypervolume_uses_fixed_known_range_normalization():
    f = body("proc fusionFront(", "proc fusionLatestGeneration()")
    assert "(points[id].g + 1.01) / 2.02" in f
    assert "(points[id].j + 0.01) / 1.02" in f
    assert "points[id].g + 1.01) *" not in f


def test_missing_or_failed_jev_is_not_negative_reliability_evidence():
    u = body("proc fusionUpdateTrust(", "proc fusionFront(")
    assert "if a.len < 6 or a.len != b.len: return" in u
    failure = body("else:\n      # Availability failure", "# Exact telescoping decomposition")
    assert "fusionReliability *= 0.5" not in failure
    assert "trust unchanged" in failure


def test_checkpoint_tracks_nursery_reservoir_and_accepts_v30():
    assert "const CHECKPOINT_VERSION = 32" in CODE
    w = body("proc writeFusion(", "proc readFusion(")
    r = body("proc readFusion(", "proc writeDataset(")
    assert "s.write(fusionPendingSeen.int64)" in w
    assert "if version >= 31:" in r
    assert "fusionPendingSeen = int(s.readInt64())" in r
    assert "28, 30, CHECKPOINT_VERSION" in CODE


def test_config_fingerprints_all_material_jev_settings():
    c = body("let jevConfig =", "# v20 checkpoints")
    for marker in (
        '"interval": JEV_GENERATION_INTERVAL',
        '"inner_population": JEV_INNER_POPULATION',
        '"inner_elites": JEV_INNER_ELITES',
        '"inner_tournament": JEV_INNER_TOURNAMENT',
        '"survivor_slots": JEV_SURVIVOR_SLOTS',
        '"ma_window": JEV_MA_WINDOW',
        '"fusion_algorithm": 3',
    ):
        assert marker in c
