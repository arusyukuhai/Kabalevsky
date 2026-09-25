from pathlib import Path
import unittest

SRC = Path(__file__).with_name('at_jev.nim').read_text(encoding='utf-8')

class GpRaceV32StaticTests(unittest.TestCase):
    def test_every_candidate_gets_only_base_batch_initially(self):
        self.assertIn('population, compiledPopulation, candidatePopulation, fastIds,', SRC)
        self.assertIn('"FAST_RACE_BASE"', SRC)
        self.assertIn('let fastBaseCaseIds = fastRaceCaseOrder[0 ..< fastBaseCaseCount]', SRC)

    def test_extra_cases_only_go_to_survivors(self):
        self.assertIn('raceActive.setLen(keep)', SRC)
        self.assertIn('evaluateFastCaseFor(raceActive, caseId', SRC)
        self.assertIn('raceEliminated.add', SRC)

    def test_elimination_layers_are_not_cross_compared(self):
        self.assertIn('for layer in countdown(raceEliminated.high, 0):', SRC)
        self.assertIn('screeningOrder.add(raceEliminated[layer])', SRC)

    def test_specialist_rescue_uses_common_base_cases(self):
        self.assertIn('for actualCi in fastBaseCaseIds:', SRC)
        self.assertIn('fastCaseScores[jp][actualCi]', SRC)

    def test_full_correlation_uses_actual_observed_depth(self):
        self.assertIn('fastObservedCount(id) > 0', SRC)
        self.assertIn('fastValues.add(fastObservedAggregate(id))', SRC)

if __name__ == '__main__':
    unittest.main()
