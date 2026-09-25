"""Offline protocol regression tests: no Jev API calls or secrets required."""
import unittest
from unittest.mock import patch

import jev_bridge as bridge


class DummyClient:
    model = "jev-test"
    _resolved_model = None
    requests = 1
    cost = 0.0


def payload(first_id=0, text="abc", population_size=None):
    data = {
        "version": 1,
        "generation": 15,
        "prompt": "def ",
        "candidates": [{"id": first_id, "text": text},
                       {"id": first_id + 1, "text": "xyz"}],
    }
    if population_size is not None:
        data["population_size"] = population_size
    return data


class BridgeValidationTests(unittest.TestCase):
    def test_legacy_400_population_accepted(self):
        data = payload(398)
        with (patch.object(bridge, "score_candidates", return_value={398: 0.25, 399: 0.5}),
              patch.object(bridge, "kwiksort", return_value=([399, 398], 1))):
            result = bridge.evaluate(data, DummyClient(), 1, 2)
        self.assertEqual(result["ranked_ids"], [399, 398])
        self.assertAlmostEqual(result["mean_quality"], 0.375)

    def test_new_population_size_accepted(self):
        data = payload(498, population_size=500)
        with (patch.object(bridge, "score_candidates", return_value={498: 0.25, 499: 0.5}),
              patch.object(bridge, "kwiksort", return_value=([499, 498], 1))):
            result = bridge.evaluate(data, DummyClient(), 1, 2)
        self.assertEqual(result["ranked_ids"], [499, 498])

    def test_exactly_64_unicode_candidates(self):
        data = payload()
        data["candidates"] = [
            {"id": i, "text": "日本語" + ("あ" * 61) + str(i)}
            for i in range(64)
        ]
        scores = {i: 0.25 for i in range(64)}
        ranking = list(range(63, -1, -1))
        with (patch.object(bridge, "score_candidates", return_value=scores),
              patch.object(bridge, "kwiksort", return_value=(ranking, 64))):
            result = bridge.evaluate(data, DummyClient(), 1, 64)
        self.assertEqual(result["ranked_ids"], ranking)
        self.assertEqual(len(result["scores"]), 64)

    def test_legacy_out_of_range_is_diagnostic_and_fail_closed(self):
        with patch.object(bridge, "score_candidates", side_effect=AssertionError("called")):
            with self.assertRaisesRegex(bridge.JevError, r"ID must be integer in 0\.\.399"):
                bridge.evaluate(payload(400), DummyClient(), 1, 2)

    def test_empty_text_reports_length_without_content(self):
        with self.assertRaisesRegex(bridge.JevError, r"id=3: length=0"):
            bridge.evaluate(payload(3, text=""), DummyClient(), 1, 2)

    def test_oversize_text_reports_length(self):
        with self.assertRaisesRegex(bridge.JevError, r"length=4097"):
            bridge.evaluate(payload(3, text="x" * 4097), DummyClient(), 1, 2)

    def test_non_string_text_reports_type(self):
        with self.assertRaisesRegex(bridge.JevError, r"text is not a string"):
            bridge.evaluate(payload(3, text=None), DummyClient(), 1, 2)

    def test_boolean_id_rejected(self):
        data = payload()
        data["candidates"][0]["id"] = True
        with self.assertRaisesRegex(bridge.JevError, r"ID must be integer"):
            bridge.evaluate(data, DummyClient(), 1, 2)

    def test_invalid_population_size_rejected(self):
        data = payload()
        data["population_size"] = True
        with self.assertRaisesRegex(bridge.JevError, r"invalid Jev round header"):
            bridge.evaluate(data, DummyClient(), 1, 2)

    def test_duplicate_ids_rejected(self):
        data = payload()
        data["candidates"][1]["id"] = 0
        with self.assertRaisesRegex(bridge.JevError, r"duplicate Jev candidate IDs"):
            bridge.evaluate(data, DummyClient(), 1, 2)


if __name__ == "__main__":
    unittest.main()