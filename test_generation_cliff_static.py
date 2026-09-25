from pathlib import Path
import unittest

SRC = Path(__file__).with_name('at_jev.nim').read_text()

class GenerationCliffStaticTests(unittest.TestCase):
    def test_no_32768_global_memo_flush(self):
        self.assertNotIn('if memo.len >= 32768: memo.clear()', SRC)
        self.assertIn('GENERATION_MEMO_MAX_ENTRIES = 32768', SRC)
        self.assertIn('memoInsertRolling', SRC)
        self.assertIn('memo.del(oldKey)', SRC)

    def test_memo_has_byte_budget_for_long_strings(self):
        self.assertIn('GENERATION_MEMO_KEY_BYTE_BUDGET = 16 * 1024 * 1024', SRC)
        self.assertIn('memoKeyBytes + key.len > GENERATION_MEMO_KEY_BYTE_BUDGET', SRC)

    def test_generated_utf8_is_cached_per_individual(self):
        self.assertIn('key: string', SRC)
        self.assertIn('result.key = runeText(suffix)', SRC)
        self.assertIn('child.key notin seen', SRC)
        self.assertIn('seen.incl(child.key)', SRC)

    def test_generation_logs_the_real_length_cliff_inputs(self):
        self.assertIn('input_bytes=', SRC)
        self.assertIn('rounds=', SRC)
        self.assertIn('max_state=', SRC)
        self.assertIn('avg_exact_ms=', SRC)

    def test_existing_score_round_and_growth_rules_are_visible(self):
        self.assertIn('int(ceil(2 * sqrt(float(input.len))))', SRC)
        self.assertIn('max(1500 * (if embedded: EMBEDDING_WIDTH else: 1), encodedLen * 32)', SRC)

if __name__ == '__main__':
    unittest.main()
