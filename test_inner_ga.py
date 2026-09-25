"""Static invariants + independent budget/elitism reference (not Nim execution)."""
import pathlib
import re
import unittest

CODE = (pathlib.Path(__file__).resolve().parent / 'at_jev.nim').read_text()


def get_proc(name: str, next_name: str) -> str:
    return CODE.split(f'proc {name}(', 1)[1].split(f'\nproc {next_name}(', 1)[0]


class InnerGATests(unittest.TestCase):
    def test_exact_budget_and_group_size(self):
        for part in (
            'const JEV_STEPS = 6400',
            'const JEV_INNER_POPULATION = 20',
            'const JEV_INNER_ELITES = 3',
            'const JEV_DEFAULT_MODELS = 64',
            'const JEV_MAX_MODELS = 64',
            'let pop_size = 450',
            'const JEV_GENERATION_INTERVAL = 20',
        ):
            with self.subTest(part=part): self.assertIn(part, CODE)
        self.assertEqual(20 + (6400 - 20), 6400)
        # The heavier Jev round is four times less frequent. Amortized local
        # generation work actually drops from 32,000 to 20,480 evaluations
        # per outer generation: 64*6400/20.
        self.assertEqual(6400 * 64, 409600)
        self.assertEqual((6400 * 64) // 20, 20480)

    def test_actual_evaluation_counter_is_not_elite_counter(self):
        p = get_proc('jevGenerate', 'jevGenerateById')
        self.assertEqual(len(re.findall(r'\binc result\.evaluations\b', p)), 2)
        self.assertIn('while result.evaluations < JEV_STEPS:', p)
        self.assertIn('while next.len < JEV_INNER_POPULATION and result.evaluations < JEV_STEPS:', p)
        self.assertIn('next.add(innerPop[i]) # immutable survivor; no scoreRaw call', p)
        self.assertIn('result.actualScoreCalls + result.cacheHits != JEV_STEPS', p)
        self.assertIn('inc actualScoreCalls', p)
        self.assertIn('inc cacheHits', p)
        self.assertIn('inc result.innerGenerations', p)

    def test_evolution_not_greedy_one_incumbent(self):
        p = get_proc('jevGenerate', 'jevGenerateById')
        for marker in ('jevInnerTournament(innerPop, rng)',
                       'for pos in left .. right:',
                       'let immigrantRate = if stagnation >= 32: 12',
                       'elif stagnation >= 24: upper = max(upper, 8)',
                       'jevInnerSort(next)',
                       'bestSuffix = cloneInts(child)',
                       'memo.hasKey(child)',
                       'for j in countdown(edits - 1, 0):'):
            with self.subTest(marker=marker): self.assertIn(marker, p)

    def test_reference_generational_budget_and_nonregression(self):
        initial = 20
        budget = 6400
        size = 20
        elites = 3
        scored = initial
        prev_best = 1.0
        generations = 0
        final_size = size
        while scored < budget:
            next_scores = [prev_best, prev_best - 0.1, prev_best - 0.2]
            while len(next_scores) < size and scored < budget:
                next_scores.append((scored % 23) / 20.0)
                scored += 1
            next_scores.sort(reverse=True)
            self.assertGreaterEqual(next_scores[0], prev_best)
            prev_best = next_scores[0]
            generations += 1
            final_size = len(next_scores)
        self.assertEqual(scored, 6400)
        self.assertEqual(generations, 376)
        self.assertEqual(final_size, 8)  # 3 elites + final 5 offspring

    def test_checkpoint_migrates_to_v23_and_jev_config_changes(self):
        self.assertIn('const CHECKPOINT_VERSION = 32', CODE)
        self.assertIn('validV22Embedding', CODE)
        self.assertIn('migrateWideEmbedding', CODE)
        self.assertIn('expandLoadedPopulation(population)', CODE)
        self.assertIn('"generation_algorithm": 7', CODE)
        self.assertIn('"internal_tokens": EMBEDDING_CODE_COUNT', CODE)
        self.assertIn('jevHall.setLen(0)', CODE)
        self.assertIn('previousJevProgressPath', CODE)
        self.assertIn('"quality_metric": "fresh_rank_linear_weighted_v2"', CODE)

    def test_objectives_are_separated(self):
        self.assertNotIn('JEV_GA_FITNESS_FLOOR', CODE)
        self.assertIn('no Jev value is ever written into `accs`', CODE)
        self.assertIn('fusionUpdateTrust(oldRepeat, newRepeat)', CODE)
        self.assertIn('writeFusion(fs)', CODE)
        self.assertIn('readFusion(fs, version, nextIter)', CODE)
        self.assertIn('fusionPendingSeen = 0', CODE)

    def test_rank_weighted_series_preserved(self):
        self.assertIn('rankWeightedSum += weight * qualityById[id]', CODE)
        self.assertIn('jevAverage(jevHistory, rankWeightedQuality)', CODE)
        self.assertIn('Jev fresh rank-weighted MA', CODE)
        self.assertIn('" local_evaluations=", jevResult.localEvaluations', CODE)
        self.assertIn('" actual_score_calls=", jevResult.actualScoreCalls', CODE)
        self.assertIn('" cache_hits=", jevResult.cacheHits', CODE)

    def test_worker_buffers_and_schedule_remain_shared(self):
        p = get_proc('jevGenerate', 'jevGenerateById')
        self.assertIn('getThreadEvalScratch(g.len)', p)
        self.assertIn('prepareScoreScratch(g, scratch)', p)
        self.assertIn('editUpperSchedule[][result.evaluations]', p)
        self.assertIn('var positions = newSeq[int](JEV_SUFFIX_LENGTH)', p)
        self.assertIn('var swapTargets = newSeq[int](JEV_SUFFIX_LENGTH)', p)
        self.assertIn('result.text = runeText(bestSuffix)', p)

if __name__ == '__main__':
    unittest.main()
