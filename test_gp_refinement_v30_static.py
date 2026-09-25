from pathlib import Path
import re

CODE = (Path(__file__).parent / "at_jev.nim").read_text()

def body(name, next_name):
    a = CODE.index(name)
    b = CODE.index(next_name, a)
    return CODE[a:b]

def test_v30_objective_and_checkpoint_version():
    assert "const CHECKPOINT_VERSION = 32" in CODE
    assert "const CHECKPOINT_OBJECTIVE_VERSION = 30" in CODE
    agg = body("proc rollingCaseBaseWeight", "proc rollingCaseMaturity")
    assert "1.0" in agg
    assert "result = 2.0" not in agg and "result = 3.0" not in agg

def test_hard_negatives_replace_and_do_not_append():
    mining = body("proc mineCorruptions(", "proc evaluateIndividualCases(")
    assert "xs[replaceAt] = cloneInts(state)" in mining
    assert "ys[replaceAt] = target" in mining
    assert "xs.add(" not in mining and "ys.add(" not in mining

def test_stagnation_reanchors_only_on_slow_refresh():
    generation = body("for iter in startIter ..< TARGET_GENERATIONS:", "if datasetChanged:")
    assert "if refreshedSlow:" in generation
    pos = generation.index("slowEpochInitialized = false")
    guard = generation.rfind("if refreshedSlow:", 0, pos)
    assert guard >= 0

def test_crossover_probes_are_matched_and_coordinate_safe():
    repro = body("# Matched crossover experiment", "var offspringBuckets")
    assert "let parent =" in repro and "let pId = survivorIds[parent]" in repro
    assert "for op in CrossoverOp:" in repro
    assert "sameMapDonors" in repro
    choose = body("proc chooseCrossoverOp(", "# Number of RULES touched")
    assert "allowTraceOperators" in choose
    assert "coTwoPoint" in choose and "coMacro" in choose

def test_rolling_scheduler_state_is_persisted():
    save = body("proc saveCheckpoint(", "proc loadCheckpoint(")
    assert "fs.write(rollingCaseAge[ci].int64)" in save
    assert "fs.write(rollingRefreshCredit[group].int64)" in save
    load = body("proc loadCheckpoint(", "proc loadCheckpointWithRecovery(")
    assert "if version >= 30:" in load
    assert "rollingCaseAge[ci] =" in load
    assert "rollingRefreshCredit[group] =" in load

def test_old_objective_forces_dataset_rebuild():
    migration = body("if loadedCheckpoint:", "else:\n  protectedPrefixCount = 0")
    assert "evalAggsX.setLen(0)" in migration
    assert "evalAggsY.setLen(0)" in migration
