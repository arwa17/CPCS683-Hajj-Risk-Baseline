import unittest
from unittest.mock import patch

import resume_with_retries as retry
from hajj_baseline.providers import ProviderError


class TestNetworkRetries(unittest.TestCase):
    def run_with_responses(self, responses):
        with patch.object(retry, '_original_generate', side_effect=responses) as generate, \
             patch.object(retry.time, 'sleep') as sleep, \
             patch.object(retry.random, 'uniform', return_value=0):
            output = retry.generate_with_retries(object(), 'system', 'user')
            return output, generate.call_count, sleep.call_count

    def test_remote_end_closed_retries_and_recovers(self):
        result = ('{}', {'input_tokens': 1, 'output_tokens': 1})
        output, calls, waits = self.run_with_responses([
            ProviderError('Cannot reach Gemini: Remote end closed connection without response'), result
        ])
        self.assertEqual(output, result)
        self.assertEqual((calls, waits), (2, 1))

    def test_read_timeout_retries_and_recovers(self):
        result = ('{}', {})
        output, calls, waits = self.run_with_responses([
            ProviderError('Cannot reach Gemini: The read operation timed out'), result
        ])
        self.assertEqual(output, result)
        self.assertEqual((calls, waits), (2, 1))

    def test_http_503_still_retries(self):
        result = ('{}', {})
        output, calls, waits = self.run_with_responses([
            ProviderError('Gemini returned HTTP 503: unavailable'), result
        ])
        self.assertEqual(output, result)
        self.assertEqual((calls, waits), (2, 1))

    def test_dns_name_resolution_retries_and_recovers(self):
        result = ('{}', {})
        output, calls, waits = self.run_with_responses([
            ProviderError('Cannot reach Gemini: <urlopen error [Errno 8] nodename nor servname provided, or not known>'), result
        ])
        self.assertEqual(output, result)
        self.assertEqual((calls, waits), (2, 1))

    def test_dns_error_retries_are_bounded(self):
        failure = ProviderError('Cannot reach Gemini: <urlopen error [Errno 8] nodename nor servname provided, or not known>')
        with patch.object(retry, '_original_generate', side_effect=failure) as generate, \
             patch.object(retry.time, 'sleep') as sleep, \
             patch.object(retry.random, 'uniform', return_value=0):
            with self.assertRaises(ProviderError):
                retry.generate_with_retries(object(), 'system', 'user')
            self.assertEqual(generate.call_count, 5)
            self.assertEqual(sleep.call_count, 4)

    def test_unauthorized_does_not_retry(self):
        with patch.object(retry, '_original_generate', side_effect=ProviderError('Gemini returned HTTP 401: unauthorized')) as generate, \
             patch.object(retry.time, 'sleep') as sleep:
            with self.assertRaises(ProviderError):
                retry.generate_with_retries(object(), 'system', 'user')
            self.assertEqual(generate.call_count, 1)
            self.assertEqual(sleep.call_count, 0)

    def test_connection_failures_stop_after_bounded_retries(self):
        failure = ProviderError('Cannot reach Gemini: Remote end closed connection without response')
        with patch.object(retry, '_original_generate', side_effect=failure) as generate, \
             patch.object(retry.time, 'sleep') as sleep, \
             patch.object(retry.random, 'uniform', return_value=0):
            with self.assertRaises(ProviderError):
                retry.generate_with_retries(object(), 'system', 'user')
            self.assertEqual(generate.call_count, 5)
            self.assertEqual(sleep.call_count, 4)


if __name__ == '__main__':
    unittest.main()
