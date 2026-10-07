from __future__ import annotations

import json
import os
import time
import unittest
from unittest import mock

from or_select.generate import TruncatedOutput
from or_select.providers import (
    MAX_OUTPUT_TOKENS,
    MAX_SHORT_ANSWER_TOKENS,
    SHORT_ANSWER_ATTEMPTS,
    StallTimeout,
    _call_with_stall_timeout,
    _is_retryable_error,
    _openai_client,
    _openrouter_client,
    _openrouter_complete,
    _parse_score,
    _reset_clients_if_connection_error,
    _stable_seed,
    openrouter_generate,
    openrouter_heterogeneous_backends,
    openrouter_judge,
    openrouter_score,
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


def _fake_response(content: str | None):
    message = mock.Mock(content=content)
    choice = mock.Mock(message=message)
    return mock.Mock(choices=[choice])


class EmptyCompletionRetriesTest(unittest.TestCase):
    # Empty content used to be accepted as a "successful" candidate -- a
    # winner_text could end up literally "" (extract_choice("") -> None)
    # even though the API call raised no exception, silently mixing
    # unusable output into what n_valid otherwise implies is real model
    # output. An empty/whitespace-only body is the same class of failure as
    # StallTimeout (severe upstream saturation producing degenerate
    # responses), so it must burn a retry attempt instead of returning "".

    def _client_returning(self, *contents):
        client = mock.Mock()
        client.chat.completions.create.side_effect = [_fake_response(c) for c in contents]
        return client

    def test_empty_content_is_retried_until_a_real_answer_arrives(self) -> None:
        client = self._client_returning("", "   ", "the real answer")
        with mock.patch("or_select.providers._openrouter_client", return_value=client), mock.patch(
            "or_select.providers.time.sleep"
        ):
            result = _openrouter_complete("query", seed=0)
        self.assertEqual(result, "the real answer")
        self.assertEqual(client.chat.completions.create.call_count, 3)

    def test_empty_content_exhausting_all_retries_raises_stall_timeout(self) -> None:
        client = self._client_returning(*([""] * 9))  # matches max_attempts=9
        with mock.patch("or_select.providers._openrouter_client", return_value=client), mock.patch(
            "or_select.providers.time.sleep"
        ):
            with self.assertRaises(StallTimeout):
                _openrouter_complete("query", seed=0)


class MaxOutputTokensTest(unittest.TestCase):
    # A "successful" (non-empty, non-timed-out) completion could still
    # degenerate into unbounded rambling with nothing to stop it -- verified
    # live this session as candidates up to ~100,000 characters that never
    # reached an ANSWER:/\boxed{} line, corrupting self-consistency majority
    # votes and fooling exact Kemeny-Young pairwise judging. max_tokens caps
    # that tail; this locks in that every call actually requests the cap
    # rather than silently dropping it in a future edit.

    def test_openrouter_call_requests_the_output_token_cap(self) -> None:
        client = mock.Mock()
        client.chat.completions.create.return_value = _fake_response("ANSWER: A")
        with mock.patch("or_select.providers._openrouter_client", return_value=client):
            _openrouter_complete("query", seed=0)
        _, kwargs = client.chat.completions.create.call_args
        self.assertEqual(kwargs.get("max_tokens"), MAX_OUTPUT_TOKENS)


class TruncationTest(unittest.TestCase):
    # finish_reason == "length" means the model was cut off at the cap, so
    # the text is a fragment. Generation must surface that explicitly; the
    # judge path (short outputs, last-number parsing) keeps returning text.

    def _truncated_client(self):
        response = _fake_response("long reasoning with no final answer")
        response.choices[0].finish_reason = "length"
        client = mock.Mock()
        client.chat.completions.create.return_value = response
        return client

    def test_generation_raises_truncated_output_on_length_stop(self) -> None:
        with mock.patch("or_select.providers._openrouter_client", return_value=self._truncated_client()):
            with self.assertRaises(TruncatedOutput) as ctx:
                openrouter_generate("query", 0)
        self.assertEqual(ctx.exception.text, "long reasoning with no final answer")

    def test_truncation_is_not_retried_by_the_transport_layer(self) -> None:
        client = self._truncated_client()
        with mock.patch("or_select.providers._openrouter_client", return_value=client), mock.patch(
            "or_select.providers.time.sleep"
        ):
            with self.assertRaises(TruncatedOutput):
                openrouter_generate("query", 0)
        self.assertEqual(client.chat.completions.create.call_count, 1)

    def test_truncation_is_never_retryable_even_if_its_char_count_looks_like_a_status_code(self) -> None:
        # "(24291 chars)" and "(4295 chars)" contain the "429" rate-limit marker.
        for size in (24291, 4295, 40712, 15040):
            self.assertFalse(_is_retryable_error(TruncatedOutput("x" * size)), size)

    def test_default_path_still_returns_truncated_text(self) -> None:
        with mock.patch("or_select.providers._openrouter_client", return_value=self._truncated_client()):
            self.assertEqual(_openrouter_complete("query", seed=0), "long reasoning with no final answer")

    def test_reasoning_effort_is_opt_in(self) -> None:
        client = mock.Mock()
        client.chat.completions.create.return_value = _fake_response("ANSWER: A")
        with mock.patch("or_select.providers._openrouter_client", return_value=client), mock.patch.dict(
            "os.environ", {}, clear=False
        ):
            os.environ.pop("OPENROUTER_REASONING_EFFORT", None)
            _openrouter_complete("query", seed=0)
            self.assertNotIn("extra_body", client.chat.completions.create.call_args.kwargs)
            os.environ["OPENROUTER_REASONING_EFFORT"] = "low"
            _openrouter_complete("query", seed=0)
        self.assertEqual(
            client.chat.completions.create.call_args.kwargs["extra_body"], {"reasoning": {"effort": "low"}}
        )

    def _client_returning_choice(self, content: str, finish: str):
        response = _fake_response(content)
        response.choices[0].finish_reason = finish
        client = mock.Mock()
        client.chat.completions.create.return_value = response
        return client

    def test_judge_turns_reasoning_off_and_uses_the_small_cap(self) -> None:
        # Measured: with reasoning on, 6/10 real judge calls were cut off at
        # 8192 tokens "thinking" and the score was read from that fragment.
        client = self._client_returning_choice("0.8", "stop")
        with mock.patch("or_select.providers._openrouter_client", return_value=client):
            self.assertEqual(openrouter_judge("q", "a", "b"), 0.8)
        kwargs = client.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs["extra_body"], {"reasoning": {"enabled": False}})
        self.assertEqual(kwargs["max_tokens"], MAX_SHORT_ANSWER_TOKENS)

    def test_score_also_uses_short_answer_mode(self) -> None:
        client = self._client_returning_choice("0.6", "stop")
        with mock.patch("or_select.providers._openrouter_client", return_value=client):
            self.assertEqual(openrouter_score("q", "text"), 0.6)
        kwargs = client.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs["extra_body"], {"reasoning": {"enabled": False}})

    def test_truncated_judge_reply_raises_instead_of_parsing_the_fragment(self) -> None:
        # A cut-off reply that happens to contain a number must not become a score.
        client = self._client_returning_choice("thinking... maybe 0.9 or 0.1 but", "length")
        with mock.patch("or_select.providers._openrouter_client", return_value=client):
            with self.assertRaises(TruncatedOutput):
                openrouter_judge("q", "a", "b")
        # Re-sampled a bounded number of times first, never parsed.
        self.assertEqual(client.chat.completions.create.call_count, SHORT_ANSWER_ATTEMPTS)

    def test_truncated_judge_reply_is_resampled_with_a_different_seed_and_can_recover(self) -> None:
        cut = _fake_response("0")
        cut.choices[0].finish_reason = "length"
        good = _fake_response("0.8")
        good.choices[0].finish_reason = "stop"
        client = mock.Mock()
        client.chat.completions.create.side_effect = [cut, good]
        with mock.patch("or_select.providers._openrouter_client", return_value=client):
            self.assertEqual(openrouter_judge("q", "a", "b"), 0.8)
        first, second = client.chat.completions.create.call_args_list
        self.assertNotEqual(first.kwargs["seed"], second.kwargs["seed"])

    def test_judge_falls_back_when_the_model_makes_reasoning_mandatory(self) -> None:
        ok = _fake_response("0.7")
        ok.choices[0].finish_reason = "stop"
        client = mock.Mock()
        client.chat.completions.create.side_effect = [
            Exception("Error code: 400 - Reasoning is mandatory for this endpoint"),
            ok,
        ]
        with mock.patch("or_select.providers._openrouter_client", return_value=client):
            self.assertEqual(openrouter_judge("q", "a", "b", model="liquid/lfm-2.5-2.6b:free"), 0.7)
        first, second = client.chat.completions.create.call_args_list
        self.assertIn("extra_body", first.kwargs)
        self.assertNotIn("extra_body", second.kwargs)
        self.assertEqual(second.kwargs["max_tokens"], MAX_OUTPUT_TOKENS)

    def test_other_errors_are_not_swallowed_by_the_fallback(self) -> None:
        client = mock.Mock()
        client.chat.completions.create.side_effect = ValueError("something else")
        with mock.patch("or_select.providers._openrouter_client", return_value=client):
            with self.assertRaises(ValueError):
                openrouter_judge("q", "a", "b")
        self.assertEqual(client.chat.completions.create.call_count, 1)

    def test_generation_keeps_reasoning_on_and_the_large_cap(self) -> None:
        client = self._client_returning_choice("ANSWER: A", "stop")
        with mock.patch("or_select.providers._openrouter_client", return_value=client), mock.patch.dict(
            "os.environ", {}, clear=False
        ):
            os.environ.pop("OPENROUTER_REASONING_EFFORT", None)
            openrouter_generate("query", 0)
        kwargs = client.chat.completions.create.call_args.kwargs
        self.assertNotIn("extra_body", kwargs)
        self.assertEqual(kwargs["max_tokens"], MAX_OUTPUT_TOKENS)

    def test_normal_stop_is_not_truncation(self) -> None:
        response = _fake_response("ANSWER: A")
        response.choices[0].finish_reason = "stop"
        client = mock.Mock()
        client.chat.completions.create.return_value = response
        with mock.patch("or_select.providers._openrouter_client", return_value=client):
            self.assertEqual(openrouter_generate("query", 0), "ANSWER: A")


class StableSeedTest(unittest.TestCase):
    def test_same_prompt_same_seed(self) -> None:
        self.assertEqual(_stable_seed("hello"), _stable_seed("hello"))

    def test_different_prompt_different_seed(self) -> None:
        self.assertNotEqual(_stable_seed("hello"), _stable_seed("world"))


if __name__ == "__main__":
    unittest.main()
