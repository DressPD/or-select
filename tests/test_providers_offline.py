from __future__ import annotations

import json
import time
import unittest
from unittest import mock

from or_select.providers import (
    StallTimeout,
    _call_with_stall_timeout,
    _is_retryable_error,
    _openai_client,
    _openrouter_client,
    _parse_score,
    _reset_clients_if_connection_error,
    _stable_seed,
    openrouter_heterogeneous_backends,
)


class ParseScoreTest(unittest.TestCase):
    def test_clean_number_parses(self) -> None:
        self.assertAlmostEqual(_parse_score("0.85"), 0.85)

    def test_takes_last_number_not_first(self) -> None:
        # A reasoning model restating a fact from the query (e.g. a year)
        # before giving its actual confidence must not have that fact
        # mistaken for the score.
        text = "The Berlin Wall fell in 1989, so I'd rate my confidence as 0.95"
        self.assertAlmostEqual(_parse_score(text), 0.95)

    def test_clamps_out_of_range_values(self) -> None:
        self.assertEqual(_parse_score("42"), 1.0)
        self.assertEqual(_parse_score("-3"), 0.0)

    def test_no_number_falls_back_to_midpoint(self) -> None:
        self.assertEqual(_parse_score("no numeric answer here"), 0.5)


class RetryableErrorTest(unittest.TestCase):
    def test_rate_limit_429_is_retryable(self) -> None:
        self.assertTrue(_is_retryable_error(Exception("Error code: 429 - too many requests")))

    def test_gemini_resource_exhausted_is_retryable(self) -> None:
        self.assertTrue(_is_retryable_error(Exception("429 RESOURCE_EXHAUSTED: quota exceeded")))

    def test_proxy_error_is_retryable(self) -> None:
        self.assertTrue(_is_retryable_error(Exception("407 Proxy Authentication Required")))

    def test_insufficient_quota_429_is_not_retryable(self) -> None:
        exc = Exception(
            "Error code: 429 - {'error': {'message': 'You have no credits remaining.', "
            "'type': 'insufficient_quota', 'code': 'credit_balance_exhausted'}}"
        )
        self.assertFalse(_is_retryable_error(exc))

    def test_openrouter_provider_returned_error_404_is_retryable(self) -> None:
        exc = Exception(
            "Error code: 404 - {'error': {'message': 'Provider returned error', 'code': 404, "
            "'metadata': {'raw': '', 'provider_name': 'Nvidia', 'is_byok': False}}}"
        )
        self.assertTrue(_is_retryable_error(exc))

    def test_bare_model_not_found_404_is_not_retryable(self) -> None:
        self.assertFalse(_is_retryable_error(Exception("Error code: 404 - model not found")))

    def test_unrelated_error_is_not_retryable(self) -> None:
        self.assertFalse(_is_retryable_error(Exception("model not found")))

    def test_openai_api_timeout_error_is_retryable(self) -> None:
        # openai.APITimeoutError's message is just "Request timed out." --
        # no text marker to match, so this must be caught by exception type
        # (a subclass of APIConnectionError), not text. Observed live: ~84
        # consecutive problems in the N=134 MATH Level 5 run failed with
        # zero retries during a sustained OpenRouter outage because this
        # case fell through to "not retryable" silently.
        import openai

        exc = openai.APITimeoutError(request=None)
        self.assertTrue(_is_retryable_error(exc))

    def test_truncated_json_response_is_retryable(self) -> None:
        # A malformed/truncated body under upstream saturation breaks the
        # SDK's own JSON parsing before any status code or error field is
        # visible -- observed live (line 967 into a response body). Its
        # message carries no provider-specific marker, so this must be
        # matched by exception type, not text.
        try:
            json.loads('{"choices": [{"message": {"content": "partial...')
        except json.JSONDecodeError as exc:
            self.assertTrue(_is_retryable_error(exc))
        else:
            self.fail("expected json.loads to raise JSONDecodeError on truncated input")


class OpenrouterHeterogeneousBackendsTest(unittest.TestCase):
    def test_each_backend_is_bound_to_its_own_model_not_the_last_one(self) -> None:
        # Classic late-binding-in-a-loop bug: without capturing model_id as
        # a default argument, every closure would share the loop variable
        # and all three backends would silently call the *last* model.
        models = ["model-a", "model-b", "model-c"]
        backends = openrouter_heterogeneous_backends(models)
        self.assertEqual([name for name, _ in backends], models)

        with mock.patch("or_select.providers._openrouter_complete", return_value="ok") as complete:
            for name, fn in backends:
                fn("query", 0)
            called_models = [call.kwargs.get("model") for call in complete.call_args_list]
        self.assertEqual(called_models, models)

    def test_empty_model_list_gives_empty_backends(self) -> None:
        # generate_candidates_heterogeneous is what actually raises on an
        # empty backend list; this function just builds the list.
        self.assertEqual(openrouter_heterogeneous_backends([]), [])


class ResetClientsOnConnectionErrorTest(unittest.TestCase):
    def test_api_connection_error_clears_both_client_caches(self) -> None:
        import openai

        with mock.patch.object(_openai_client, "cache_clear") as openai_clear, mock.patch.object(
            _openrouter_client, "cache_clear"
        ) as openrouter_clear:
            _reset_clients_if_connection_error(openai.APIConnectionError(request=None))
            openai_clear.assert_called_once()
            openrouter_clear.assert_called_once()

    def test_unrelated_error_does_not_clear_caches(self) -> None:
        with mock.patch.object(_openai_client, "cache_clear") as openai_clear, mock.patch.object(
            _openrouter_client, "cache_clear"
        ) as openrouter_clear:
            _reset_clients_if_connection_error(RuntimeError("some other failure"))
            openai_clear.assert_not_called()
            openrouter_clear.assert_not_called()


class StallTimeoutTest(unittest.TestCase):
    def test_fast_call_returns_normally(self) -> None:
        self.assertEqual(_call_with_stall_timeout(lambda: "ok", timeout=1.0), "ok")

    def test_slow_call_raises_stall_timeout_at_the_configured_deadline(self) -> None:
        def hangs():
            time.sleep(5.0)
            return "too late"

        start = time.perf_counter()
        with self.assertRaises(StallTimeout):
            _call_with_stall_timeout(hangs, timeout=0.2)
        elapsed = time.perf_counter() - start
        # Must return control near the budget, not wait for the underlying
        # call to actually finish (the whole point: an indefinitely hanging
        # network call must not block the caller).
        self.assertLess(elapsed, 1.0)

    def test_stall_timeout_is_retryable(self) -> None:
        self.assertTrue(_is_retryable_error(StallTimeout("no result after 120s")))

    def test_exception_raised_inside_the_call_propagates_unchanged(self) -> None:
        def raises():
            raise ValueError("boom")

        with self.assertRaises(ValueError):
            _call_with_stall_timeout(raises, timeout=1.0)


class StableSeedTest(unittest.TestCase):
    def test_same_prompt_same_seed(self) -> None:
        self.assertEqual(_stable_seed("hello"), _stable_seed("hello"))

    def test_different_prompt_different_seed(self) -> None:
        self.assertNotEqual(_stable_seed("hello"), _stable_seed("world"))


if __name__ == "__main__":
    unittest.main()
