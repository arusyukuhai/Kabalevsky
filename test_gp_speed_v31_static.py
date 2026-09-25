from pathlib import Path

SRC = Path(__file__).with_name('at_jev.nim').read_text(encoding='utf-8')

def test_full_objective_remains_six_by_twenty():
    assert 'const CASES_PER_TIMESCALE = 2' in SRC
    assert 'const MULTI_CASE_COUNT = 3 * CASES_PER_TIMESCALE' in SRC
    assert 'const RETAINED_SAMPLES_PER_CASE = 20' in SRC
    assert 'const CHECKPOINT_OBJECTIVE_VERSION = 30 # v30: unbiased equal-case 6x20 objective' in SRC

def test_fast_does_not_hash_each_input_sequence():
    a = SRC.index('proc evaluateChunk(')
    b = SRC.index('var miningGenome', a)
    body = SRC[a:b]
    assert 'initTable[seq[int], float]' not in body
    assert 'memo.hasKey(input)' not in body

def test_probe_overhead_is_decimated():
    assert 'const MUTATION_PROBE_INTERVAL = 2' in SRC
    assert 'const CROSSOVER_PROBE_INTERVAL = 4' in SRC
    assert 'if iter mod MUTATION_PROBE_INTERVAL == 0:' in SRC
    assert 'if iter mod CROSSOVER_PROBE_INTERVAL == 0 and' in SRC

def test_trace_cost_is_halved_from_v30():
    assert 'const CROSSOVER_TRACE_SAMPLE_COUNT = 6' in SRC

def test_fast_screen_uses_subset_not_full_six_cases():
    a = SRC.index('# ---------------- v32 sequential FAST race ----------------')
    b = SRC.index('let tAfterFastEval = epochTime()', a)
    body = SRC[a:b]
    assert 'fastBaseCaseIds' in SRC
    assert 'parallelEvaluateCasesBatch(' in body
    assert 'raceStageCases' in body
    assert 'FAST_RACE_BASE_CASES' in SRC
