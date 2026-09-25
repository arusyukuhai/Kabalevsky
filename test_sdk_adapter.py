"""Offline tests: replace the official SDK module with a tiny test double.
No live requests, credentials or Python package installation needed.
"""
import sys
import types
import unittest
from unittest.mock import patch

import jev_bridge as bridge


class FakeScore:
    def __init__(self, instructions, criteria):
        self.instructions = instructions
        self.criteria = criteria


class FakeChoice(FakeScore):
    pass


class FakeRetry:
    def __init__(self, max_retries):
        self.max_retries = max_retries


class FakeSDK:
    latest = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.calls = []
        self.closed = False
        FakeSDK.latest = self

    def system_one(self, *, state, questions):
        self.calls.append((state, questions))
        answers = {}
        for key, value in questions.items():
            if isinstance(value, FakeScore) and not isinstance(value, FakeChoice):
                answers[key] = types.SimpleNamespace(score=2.5)
            else:
                answers[key] = types.SimpleNamespace(choice='a',
                    probabilities={'a': 0.8, 'b': 0.2})
        return types.SimpleNamespace(answers=answers, model='jev-1.13.0',
            usage=types.SimpleNamespace(input_tokens=42, output_tokens=1))

    def close(self):
        self.closed = True


fake_sdk = types.ModuleType('typesafe_sdk')
fake_sdk.Score = FakeScore
fake_sdk.Choice = FakeChoice
fake_sdk.RetryPolicy = FakeRetry
fake_sdk.TypeSafeClient = FakeSDK


class SDKAdapterTests(unittest.TestCase):
    def setUp(self):
        self.patch_sdk = patch.dict(sys.modules, {'typesafe_sdk': fake_sdk})
        self.patch_sdk.start()
        self.addCleanup(self.patch_sdk.stop)

    def test_explicit_key_model_and_no_retries(self):
        client = bridge.JevClient('test-token-secret', 'jev-1.13.0')
        self.assertEqual(FakeSDK.latest.kwargs['api_key'], 'test-token-secret')
        self.assertEqual(FakeSDK.latest.kwargs['model'], 'jev-1.13.0')
        self.assertEqual(FakeSDK.latest.kwargs['retry'].max_retries, 0)
        client.close()
        self.assertTrue(FakeSDK.latest.closed)

    def test_both_question_types_and_no_extra_calls(self):
        client = bridge.JevClient('test-key', 'jev-1.13.0')
        output = client.decide({'fixed_prompt': 'def '}, {
            'quality': {'type': 'score', 'instructions': 'test', 'criteria': bridge.RUBRIC},
            'pair_0': {'type': 'choice', 'instructions': 'pair test',
                       'criteria': {'a': 'first', 'b': 'second'}},
        })
        self.assertEqual(len(FakeSDK.latest.calls), 1)
        self.assertIsInstance(FakeSDK.latest.calls[0][1]['quality'], FakeScore)
        self.assertIsInstance(FakeSDK.latest.calls[0][1]['pair_0'], FakeChoice)
        self.assertEqual(output['quality'], {'type': 'score', 'score': 2.5})
        self.assertEqual(output['pair_0']['probabilities'], {'a': 0.8, 'b': 0.2})
        self.assertEqual(client.requests, 1)
        self.assertEqual(client.cost, 0.0)
        client.close()

    def test_unsupported_question_fails_before_network(self):
        client = bridge.JevClient('test-key', 'jev-1.13.0')
        with self.assertRaisesRegex(bridge.JevError, 'unsupported'):
            client.decide('x', {'bad': {'type': 'noul'}})
        self.assertEqual(len(FakeSDK.latest.calls), 0)
        client.close()

    def test_403_fails_closed_and_does_not_log_body(self):
        class PermissionDeniedError(Exception):
            status = 403
            request_id = 'req_safe123'
        def deny(*, state, questions):
            raise PermissionDeniedError('SECRET_TOKEN response body')
        client = bridge.JevClient('test-key', 'jev-1.13.0')
        FakeSDK.latest.system_one = deny
        with self.assertRaises(bridge.JevError) as caught:
            client.decide('x', {'quality': {'type': 'score', 'instructions': 'rate',
                                           'criteria': bridge.RUBRIC}})
        self.assertIn('HTTP 403', str(caught.exception))
        self.assertIn('req_safe123', str(caught.exception))
        self.assertNotIn('SECRET_TOKEN', str(caught.exception))
        self.assertEqual(client.requests, 0)
        client.close()

    def test_mismatched_answers_fail_closed(self):
        client = bridge.JevClient('test-key', 'jev-1.13.0')
        FakeSDK.latest.system_one = lambda **kwargs: types.SimpleNamespace(
            answers={}, model='jev-1.13.0')
        with self.assertRaisesRegex(bridge.JevError, 'missing/extra'):
            client.decide('x', {'quality': {'type': 'score', 'instructions': 'rate',
                                           'criteria': bridge.RUBRIC}})
        self.assertEqual(client.requests, 0)
        client.close()

    def test_automatic_retry_argument_refused(self):
        with self.assertRaisesRegex(bridge.JevError, 'forbids'):
            bridge.JevClient('test-key', 'jev-1.13.0', attempts=2)


if __name__ == '__main__':
    unittest.main()
