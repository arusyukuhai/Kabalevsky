from pathlib import Path
import re
import unittest

SRC = Path(__file__).with_name('at_jev.nim').read_text(encoding='utf-8')

class FastStrideStaticTests(unittest.TestCase):
    def value(self, name):
        m = re.search(rf'(?m)^\s*(?:const\s+)?{re.escape(name)}\s*=\s*([0-9_]+)', SRC)
        self.assertIsNotNone(m, name)
        return int(m.group(1).replace('_',''))

    def test_stride_never_returns_to_dense_v30_mode(self):
        self.assertEqual(self.value('FAST_EVAL_STRIDE'), 4)
        self.assertEqual(self.value('FAST_EVAL_STRIDE_MIN'), 3)
        self.assertEqual(self.value('FAST_EVAL_STRIDE_MAX'), 5)

    def test_fast_keeps_full_temporal_semantics(self):
        self.assertIn('const FAST_EVAL_ROUNDS = SCORE_ROUNDS', SRC)
        self.assertNotIn('adaptiveFastEvalRounds', SRC)

    def test_fast_uses_sequential_race(self):
        self.assertEqual(self.value('FAST_RACE_BASE_CASES'), 3)
        self.assertEqual(self.value('FAST_RACE_STAGE2_POOL'), 128)
        self.assertEqual(self.value('FAST_RACE_STAGE3_POOL'), 72)
        self.assertEqual(self.value('FAST_RACE_STAGE4_POOL'), 48)
        self.assertIn('fastRaceCaseOrder', SRC)
        self.assertIn('FAST_RACE_BASE', SRC)
        self.assertIn('evaluateFastCaseFor(raceActive', SRC)
        self.assertNotIn('adaptiveFastCaseCount', SRC)

    def test_final_race_pool_covers_max_merit_band(self):
        self.assertGreaterEqual(self.value('FAST_RACE_STAGE4_POOL'), self.value('FULL_EVAL_TOP_MAX'))

    def test_bad_screening_restores_observation_density(self):
        self.assertIn('if severeAuditMiss or screeningCorr < 0.76:', SRC)
        self.assertIn('adaptiveFastEvalStride = FAST_EVAL_STRIDE_MIN', SRC)

    def test_high_correlation_can_reduce_cost(self):
        self.assertIn('elif screeningCorr > 0.985 and auditMissedMerit == 0:', SRC)
        self.assertIn('adaptiveFastEvalStride = min(FAST_EVAL_STRIDE_MAX, adaptiveFastEvalStride + 1)', SRC)

    def test_audit_is_sparse_but_recovery_can_be_dense(self):
        self.assertEqual(self.value('FAST_AUDIT_INTERVAL'), 4)
        self.assertEqual(self.value('FAST_AUDIT_COUNT_NORMAL'), 4)
        self.assertEqual(self.value('FAST_AUDIT_COUNT_RECOVERY'), 8)
        self.assertIn('let auditDue = (iter mod FAST_AUDIT_INTERVAL == 0)', SRC)
        self.assertIn('lastScreeningCorrelation < 0.82', SRC)

    def test_log_reports_actual_race_work(self):
        self.assertIn('sequential_race=true', SRC)
        self.assertIn('race_case_order=', SRC)
        self.assertIn('race_stage_sizes=', SRC)
        self.assertIn('fast_candidate_case_evals=', SRC)
        self.assertIn('fast_sample_evals=', SRC)
        self.assertIn('fast_scan_work_used=', SRC)
        self.assertIn('fast_scan_work_next=', SRC)
        self.assertIn('race_pool_targets=', SRC)
        self.assertIn('fast_budget_failures=', SRC)
        self.assertIn('fast_budget_failure_rate=', SRC)
        self.assertIn('fast_points_per_case=', SRC)
        self.assertIn('audit_due=', SRC)
        self.assertIn('merit_full_target=', SRC)

if __name__ == '__main__':
    unittest.main()
