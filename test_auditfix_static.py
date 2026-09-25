from pathlib import Path
import re
import unittest

SRC = Path(__file__).with_name('at_jev.nim').read_text(encoding='utf-8')

class AuditFixStaticTests(unittest.TestCase):
    def value(self, name):
        m = re.search(rf'(?m)^\s*(?:const\s+)?{re.escape(name)}\s*=\s*([0-9_]+)', SRC)
        self.assertIsNotNone(m, name)
        return int(m.group(1).replace('_',''))

    def test_stabilized_rolling_widths(self):
        # v28 uses two cases per timescale and refreshes one case per event.
        self.assertEqual(self.value('FAST_DATASET_REFRESH_INTERVAL'), 8)
        self.assertEqual(self.value('MEDIUM_DATASET_REFRESH_INTERVAL'), 16)
        self.assertEqual(self.value('SLOW_DATASET_REFRESH_INTERVAL'), 32)

    def test_collision_free_weighted_scheduler(self):
        self.assertIn('var rollingRefreshCredit: array[3, int]', SRC)
        self.assertIn('const refreshCreditAdd = [4, 2, 1]', SRC)
        self.assertIn('rollingRefreshCredit[chosenGroup] -= 16', SRC)
        # The code has one refreshDatasetGroup call inside the scheduler branch,
        # not three independent modulo refreshes that can collide.
        section = SRC.split('Rolling evaluation: two cases per timescale',1)[1]
        section = section.split('if datasetChanged:',1)[0]
        self.assertEqual(section.count('refreshDatasetGroup('), 1)

    def test_credit_scheduler_hits_requested_average_rates(self):
        credits = [0, 0, 0]
        adds = [4, 2, 1]  # FAST, MEDIUM, SLOW group events
        counts = [0, 0, 0]
        for _ in range(1600):
            credits = [credits[i] + adds[i] for i in range(3)]
            due = [i for i in range(3) if credits[i] >= 16]
            if due:
                chosen = max(due, key=lambda i: credits[i])
                credits[chosen] -= 16
                counts[chosen] += 1
        # Group events are 1/4, 1/8 and 1/16; two alternating cases therefore
        # see per-case lifetimes of roughly 8, 16 and 32 generations.
        self.assertLessEqual(abs(counts[0] - 400), 1)
        self.assertLessEqual(abs(counts[1] - 200), 1)
        self.assertLessEqual(abs(counts[2] - 100), 1)

    def test_no_rewrite_and_empty_candidate_cutoffs_present(self):
        self.assertIn('if terminated or not rewrote: break', SRC)
        self.assertIn('if evalScratch.candidateIds.len == 0:', SRC)

    def test_clock_watchdog_not_in_tight_128_visit_mode(self):
        self.assertEqual(self.value('EVAL_CLOCK_CHECK_VISITS'), 1024)
        self.assertNotIn('budget.ruleVisits - budget.lastClockCheck >= 128', SRC)

if __name__ == '__main__':
    unittest.main()
