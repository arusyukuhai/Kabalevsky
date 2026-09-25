import pathlib, unittest
CODE = pathlib.Path(__file__).with_name("at_jev.nim").read_text()

class GenerationSpikeFixTests(unittest.TestCase):
    def test_generation_has_separate_budget(self):
        self.assertIn("TEXT_GENERATION_SCORE_MAX_SECONDS = 0.50", CODE)
        self.assertIn("TEXT_GENERATION_SCORE_MAX_RULE_VISITS = 250_000", CODE)
        self.assertIn("clockCheckVisits = TEXT_GENERATION_CLOCK_CHECK_VISITS", CODE)
        self.assertIn("except EvaluationBudgetExceeded:", CODE)

    def test_jev_avoids_string_roundtrip(self):
        block = CODE[CODE.index("proc jevGenerate("):CODE.index("proc jevGenerateById(")]
        self.assertIn("var memo = initTable[seq[int], float](JEV_STEPS)", block)
        self.assertIn("buildPromptSuffixBytes(promptBytes, suffix, scoreInput)", block)
        self.assertNotIn("let whole = prompt & runeText(suffix)", block)
        self.assertNotIn("textBytes(whole)", block)

    def test_generation_telemetry_and_worker_cap(self):
        self.assertIn('" budget_cutoffs=", result.budgetCutoffs', CODE)
        self.assertIn('" max_score_ms=", formatFloat(result.maxScoreSeconds', CODE)
        self.assertIn('" jev=", formatFloat(jevWallSeconds', CODE)
        self.assertIn("min(16, workerCount)", CODE)

if __name__ == "__main__":
    unittest.main()
