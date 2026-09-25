from pathlib import Path
import re
import unittest

SRC = Path(__file__).with_name('at_jev.nim').read_text(encoding='utf-8')

class SpeedGuardV34Tests(unittest.TestCase):
    def value(self, name):
        m = re.search(rf"(?m)^\s*(?:const\s+)?{re.escape(name)}\s*=\s*([0-9_]+)", SRC)
        self.assertIsNotNone(m, name)
        return int(m.group(1).replace('_', ''))

    def test_full_semantics_stay_exact(self):
        self.assertIn('const FAST_EVAL_ROUNDS = SCORE_ROUNDS', SRC)
        self.assertIn('maxScanWork: int64 = 0', SRC)
        self.assertIn('SCORE_ROUNDS, "FULL", addr freshTimings', SRC)

    def test_fast_has_deterministic_scan_work_guard(self):
        self.assertEqual(self.value('FAST_SCAN_WORK_DEFAULT'), 40_000_000)
        self.assertEqual(self.value('FAST_SCAN_WORK_MIN'), 20_000_000)
        self.assertGreaterEqual(self.value('FAST_SCAN_WORK_MAX'), self.value('FAST_SCAN_WORK_DEFAULT'))
        self.assertIn('chargeEvaluationScanWork(budget, state.len)', SRC)
        self.assertIn('adaptiveFastScanWork', SRC)
        self.assertIn('FAST_MAX_RULE_VISITS', SRC)

    def test_fast_budget_is_only_passed_to_fast_race(self):
        self.assertIn('"FAST_RACE_BASE", nil, addr fastBudgetFailures', SRC)
        self.assertIn('phaseName,\n      nil, addr fastBudgetFailures', SRC)
        self.assertNotIn('"FULL", addr freshTimings, addr fastBudgetFailures', SRC)

    def test_race_pools_shrink_only_when_correlation_supports_it(self):
        self.assertIn('proc adaptiveRacePoolTargets(correlation: float)', SRC)
        self.assertIn('if correlation >= 0.985:', SRC)
        self.assertIn('[96, 56, 40]', SRC)
        self.assertIn('[FAST_RACE_STAGE2_POOL, FAST_RACE_STAGE3_POOL, FAST_RACE_STAGE4_POOL]', SRC)

    def test_runtime_bloat_pressure_is_near_tie_only(self):
        self.assertIn('PARETO_FITNESS_SLACK = 0.012', SRC)
        self.assertIn('PARETO_FITNESS_NOISE = 0.002', SRC)
        self.assertIn('PARETO_TIME_ADVANTAGE = 1.40', SRC)
        self.assertIn('PARETO_PARENT_PERCENT = 40', SRC)

    def test_budget_feedback_widens_on_bad_screening(self):
        self.assertIn('if severeAuditMiss or screeningCorr < 0.88:', SRC)
        self.assertIn('(adaptiveFastScanWork * 3) div 2', SRC)
        self.assertIn('fastBudgetFailureRate > 0.08', SRC)
        self.assertIn('fastBudgetFailureRate < 0.02', SRC)

if __name__ == '__main__':
    unittest.main()
