from pathlib import Path
import unittest

CODE = Path(__file__).with_name("at_jev.nim").read_text()


class GPAuditV35StaticTests(unittest.TestCase):
    def test_literal_identity_fast_path_and_no_whole_state_compare(self):
        self.assertIn("outputChanged: ptr bool = nil", CODE)
        self.assertIn("if sameLiteral:", CODE)
        self.assertIn("addr stateChangedByRule", CODE)
        self.assertIn("if stateChangedByRule:", CODE)
        score = CODE.split("proc scoreRaw(", 1)[1].split("proc evaluateChunk(", 1)[0]
        self.assertNotIn("evalScratch.bufB != state", score)

    def test_fast_budget_failure_is_candidate_global_and_rate_is_job_based(self):
        self.assertIn("budgetFailed: ptr seq[bool] = nil", CODE)
        self.assertIn("var fastInvalid = newSeq[bool](pop_size)", CODE)
        self.assertIn("fastInvalid[id] = true", CODE)
        self.assertIn("fastInvalid[jp] = true", CODE)
        self.assertIn("var raceBudgetRejected: seq[int] = @[]", CODE)
        self.assertIn("screeningOrder.add(raceBudgetRejected)", CODE)
        self.assertIn("scores[i] = if fastInvalid[jp]: -Inf", CODE)
        self.assertIn("var fastBudgetDenom = fastIds.len", CODE)
        self.assertNotIn("var fastBudgetDenom = fastIds.len * fastBaseCaseCount", CODE)

    def test_fast_controller_persists_across_checkpoint(self):
        self.assertIn("const CHECKPOINT_VERSION = 32", CODE)
        self.assertIn("fs.write(adaptiveFastEvalStride.int64)", CODE)
        self.assertIn("fs.write(adaptiveFastScanWork)", CODE)
        self.assertIn("fs.write(lastScreeningCorrelation)", CODE)
        self.assertIn("if version >= 32:", CODE)
        self.assertIn("31, CHECKPOINT_VERSION", CODE)

    def test_jev_uses_common_random_numbers_and_memo_duplicate_repair(self):
        gen = CODE.split("proc jevGenerate(", 1)[1].split("proc jevGenerateById", 1)[0]
        self.assertNotIn("int64(id + 1) * 7_919", gen)
        self.assertIn("Common random numbers", gen)
        self.assertIn("memo.hasKey(child)", gen)
        self.assertNotIn("for item in next:", gen)
        self.assertNotIn("for item in innerPop:", gen)


if __name__ == "__main__":
    unittest.main()
