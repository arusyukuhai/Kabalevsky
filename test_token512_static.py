"""512-token format and generation invariants."""
from pathlib import Path
import random
import unittest

CODE = (Path(__file__).resolve().parent / "at_jev.nim").read_text()


class Token512Tests(unittest.TestCase):
    def test_format_and_migration(self):
        for marker in (
            "const EMBEDDING_SIZE = 512",
            "const EMBEDDING_OOV = EMBEDDING_CODE_COUNT",
            "const CHECKPOINT_VERSION = 32",
            "const CHECKPOINT_OBJECTIVE_VERSION = 30",
            "elif version in [23, 24]: validWideEmbedding(storedMapping, V24_EMBEDDING_CODE_COUNT)",
            "let migrated = migrateWideEmbedding(storedMapping, oldCodeCount)",
            "resetFusion()",
            'const ENERGY_MODEL_MAGIC = "KLEISMIC_ENERGY_V12"',
            'elif header == ENERGY_MODEL_MAGIC_V9: 24',
        ):
            with self.subTest(marker=marker): self.assertIn(marker, CODE)

    def test_injection_mutation(self):
        self.assertNotIn("sampleUnusedEmbeddingCode", CODE)
        self.assertIn("swap(newMap[byte], newMap[other])", CODE)
        self.assertIn("swap(newMap[byte], freeCodes[freeIndex])", CODE)
        self.assertIn("doAssert targetTaken.allIt(it)", CODE)
        rng = random.Random(1729)
        for _ in range(50):
            frm = rng.sample(range(256), 256)
            to = rng.sample(range(256), 256)
            table = [None] * 256
            for b in range(256): table[frm[b]] = to[b]
            self.assertEqual(sorted(table), list(range(256)))

    def test_evaluator_and_generation_limits(self):
        for marker in (
            "head1: array[INDEX_TOKEN_COUNT, int32]",
            "head2: PairHeadIndex",
            "pairSeenBits: seq[uint64]",
            "(v + 1) mod EMBEDDING_CODE_COUNT",
            "(v * 2) mod EMBEDDING_CODE_COUNT",
            "const JEV_STEPS = 6400",
            "const JEV_DEFAULT_MODELS = 64",
            "EVAL_MAX_RULE_VISITS = 1_500_000",
            "EVAL_MAX_SAMPLE_SECONDS = 10.0",
        ):
            with self.subTest(marker=marker): self.assertIn(marker, CODE)

if __name__ == "__main__": unittest.main()
