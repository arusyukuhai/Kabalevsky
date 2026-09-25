from pathlib import Path
import re
import unittest

SRC = Path(__file__).with_name('at_jev.nim').read_text(encoding='utf-8')

class GPStabilizationStaticTests(unittest.TestCase):
    def value(self, name):
        m = re.search(rf'(?m)^\s*(?:const\s+)?{re.escape(name)}\s*=\s*([0-9_]+)', SRC)
        self.assertIsNotNone(m, name)
        return int(m.group(1).replace('_', ''))

    def test_spearman_case_size(self):
        self.assertEqual(self.value('CASES_PER_TIMESCALE'), 2)
        self.assertEqual(self.value('RETAINED_SAMPLES_PER_CASE'), 20)

    def test_raw_diffusion_stays_in_byte_domain(self):
        self.assertNotIn('min(256, old + delta)', SRC)
        self.assertNotIn('mod 257', SRC)
        self.assertIn('min(INPUT_BYTE_COUNT - 1, old + delta)', SRC)
        self.assertIn('mod INPUT_BYTE_COUNT', SRC)

    def test_local_and_exploration_mutation_lanes(self):
        self.assertEqual(self.value('LOCAL_MUTATION_MIN_RULES'), 12)
        self.assertEqual(self.value('LOCAL_MUTATION_MAX_RULES'), 48)
        self.assertIn('let mutationCap = if explorationLane: child.len else: localMutationCapGen', SRC)
        self.assertIn('pickMutationTargetsBudget', SRC)
        self.assertIn('if macroLane:', SRC)
        self.assertIn('sampleLogUniformMutationRange(1, upper)', SRC)

    def test_protected_elites_do_not_consume_merit_full_slots(self):
        self.assertIn('let fullCount = min(requestedFullTop, screeningOrder.len)', SRC)
        self.assertIn('FULL_EVAL_TOP_MIN', SRC)
        self.assertIn('FULL_EVAL_TOP_MAX', SRC)
        self.assertNotIn('FULL_EVAL_TOP - protectedCount', SRC)

    def test_crossover_only_path_exists(self):
        self.assertIn('let shouldMutate = (not didCrossover) or rand(99) < CROSSOVER_MUTATION_PERCENT', SRC)
        self.assertEqual(self.value('CROSSOVER_MUTATION_PERCENT'), 55)

    def test_fast_subset_rotates_without_changing_full_semantics(self):
        self.assertIn('phase: int = 0', SRC)
        self.assertIn('let fastPhase = iter mod max(1, adaptiveFastEvalStride)', SRC)
        self.assertIn('FAST_EVAL_ROUNDS = SCORE_ROUNDS', SRC)

    def test_crossover_has_explicit_local_and_macro_lanes(self):
        self.assertEqual(self.value('LOCAL_CROSSOVER_MAX_RULES'), 96)
        self.assertEqual(self.value('CROSSOVER_MACRO_PERCENT'), 12)
        self.assertIn('sampleCrossoverLength(n, LOCAL_CROSSOVER_MAX_RULES)', SRC)
        self.assertIn('sampleCrossoverLength(n, n)', SRC)

    def test_embedding_not_spliced_after_ordinary_crossover(self):
        reproduction = SRC[SRC.index('while new_population.len < pop_size:'):]
        self.assertNotIn('crossoverEmbedding(child, p2)', reproduction)
        self.assertIn('if macroLane:', SRC)

    def test_rank_resolution_retry_is_bounded(self):
        self.assertIn('while attempts < 4:', SRC)
        self.assertIn('if nextDamage != diffusionMass', SRC)

    def test_resume_keeps_stagnation_control_state(self):
        marker = 'bestEver = -Inf\n\n  let fast = buildFastEvalDataset'
        self.assertIn(marker, SRC)

if __name__ == '__main__':
    unittest.main()
