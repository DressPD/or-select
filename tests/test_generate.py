from __future__ import annotations

import unittest

from or_select.generate import (
    TruncatedOutput,
    ValidityExhausted,
    generate_candidates,
    generate_candidates_heterogeneous,
)


class GenerateCandidatesValidityRetryTest(unittest.TestCase):
    # A call can return non-empty text and still be useless for the caller's
    # domain (e.g. GPQA text that never reaches an ANSWER:/\boxed{} marker).
    # Before this, that text was accepted as-is; validity_fn now gives the
    # same seed another chance before giving up, mirroring how
    # providers.py already retries an empty completion rather than
    # accepting it.

    def test_no_validity_fn_accepts_whatever_the_generator_returns(self) -> None:
        # Backward compatible: omitting validity_fn must not change behavior
        # for callers (e.g. MATH/AIME scripts not yet passing one).
        candidates = generate_candidates("q", lambda q, s: "garbage", n=2)
        self.assertEqual([c.text for c in candidates], ["garbage", "garbage"])

    def test_retries_until_a_valid_candidate_arrives(self) -> None:
        responses = iter(["garbage", "garbage", "ANSWER: A"])
        candidates = generate_candidates(
            "q", lambda q, s: next(responses), n=1, validity_fn=lambda t: "ANSWER:" in t
        )
        self.assertEqual(candidates[0].text, "ANSWER: A")

    def test_raises_after_exhausting_retries_on_a_persistently_invalid_seed(self) -> None:
        with self.assertRaises(RuntimeError):
            generate_candidates("q", lambda q, s: "garbage", n=1, validity_fn=lambda t: "ANSWER:" in t)

    def test_exhausted_exception_carries_the_last_response_text(self) -> None:
        # Previously only the length was recoverable; the full text is
        # needed to diagnose *why* extraction kept failing.
        with self.assertRaises(ValidityExhausted) as ctx:
            generate_candidates("q", lambda q, s: "garbage response", n=1, validity_fn=lambda t: "ANSWER:" in t)
        self.assertEqual(ctx.exception.last_response, "garbage response")
        self.assertEqual(ctx.exception.seed, 0)

    def test_truncated_output_fails_immediately_without_resampling(self) -> None:
        # Hitting the token cap is a property of the problem; re-sampling
        # would only spend two more full-length calls to truncate again.
        calls: list[int] = []

        def generate_fn(query: str, seed: int) -> str:
            calls.append(seed)
            raise TruncatedOutput("cut off mid-reasoning")

        with self.assertRaises(ValidityExhausted) as ctx:
            generate_candidates("q", generate_fn, n=1, validity_fn=lambda t: "ANSWER:" in t)
        self.assertEqual(len(calls), 1)
        self.assertTrue(ctx.exception.truncated)
        self.assertEqual(ctx.exception.last_response, "cut off mid-reasoning")
        self.assertIn("truncated", str(ctx.exception))

    def test_ordinary_invalid_text_is_not_flagged_truncated(self) -> None:
        with self.assertRaises(ValidityExhausted) as ctx:
            generate_candidates("q", lambda q, s: "garbage", n=1, validity_fn=lambda t: "ANSWER:" in t)
        self.assertFalse(ctx.exception.truncated)

    def test_each_seed_gets_its_own_retry_budget(self) -> None:
        # seed slot 0 needs two tries, seed slot 1 succeeds first try -- a
        # failure on one candidate must not consume or corrupt another's
        # budget. Retries vary the seed sent to generate_fn, so recover the
        # original slot via modulo rather than comparing the raw seed.
        calls: list[int] = []

        def generate_fn(query: str, seed: int) -> str:
            slot = seed % 10_000
            calls.append(slot)
            if slot == 0 and calls.count(0) == 1:
                return "garbage"
            return f"ANSWER: {slot}"

        candidates = generate_candidates(
            "q", generate_fn, n=2, validity_fn=lambda t: "ANSWER:" in t
        )
        self.assertEqual([c.text for c in candidates], ["ANSWER: 0", "ANSWER: 1"])

    def test_retries_vary_the_seed_instead_of_repeating_it(self) -> None:
        # A backend that honors `seed` for reproducibility must not be able
        # to force 3 identical, guaranteed-failing attempts out of this loop.
        seen_seeds: list[int] = []

        def generate_fn(query: str, seed: int) -> str:
            seen_seeds.append(seed)
            return "ANSWER: A" if len(seen_seeds) >= 3 else "garbage"

        generate_candidates("q", generate_fn, n=1, validity_fn=lambda t: "ANSWER:" in t)
        self.assertEqual(len(set(seen_seeds)), len(seen_seeds))

    def test_heterogeneous_backends_also_retry_on_invalid_text(self) -> None:
        responses = iter(["garbage", "ANSWER: B"])
        backends = [("model-a", lambda q, s: next(responses))]
        candidates = generate_candidates_heterogeneous(
            "q", backends, n=1, validity_fn=lambda t: "ANSWER:" in t
        )
        self.assertEqual(candidates[0].text, "ANSWER: B")


if __name__ == "__main__":
    unittest.main()
