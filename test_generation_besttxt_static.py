from pathlib import Path
import unittest

SRC = Path(__file__).with_name('at_jev.nim').read_text()

class BestTextPersistenceTests(unittest.TestCase):
    def test_initial_best_written(self):
        needle = 'let initialBest = bestEnergy'
        i = SRC.index(needle)
        j = SRC.index('var localStagnation', i)
        block = SRC[i:j]
        self.assertIn('writeFile(outputPath, prompt & runeText(bestSuffix))', block)

    def test_best_written_inside_generation_loop(self):
        loop = SRC.index('while attempted < steps:')
        log = SRC.index('if generation mod 5 == 0 or attempted >= steps:', loop)
        block = SRC[loop:log]
        self.assertIn('Persist the current global champion after EVERY text-GA generation.', block)
        self.assertIn('writeFile(outputPath, prompt & runeText(bestSuffix))', block)

    def test_no_candidate_file_dump(self):
        # Persistence is outside the per-proposal while loop; only one champion
        # write happens after all islands for that generation have been processed.
        loop = SRC.index('while attempted < steps:')
        candidate_loop = SRC.index('while next.len < target and attempted < steps:', loop)
        persist = SRC.index('Persist the current global champion after EVERY text-GA generation.', candidate_loop)
        self.assertNotIn('writeFile(outputPath', SRC[candidate_loop:persist])

if __name__ == '__main__':
    unittest.main()
