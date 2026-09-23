from __future__ import annotations

import unittest

from or_select.generate import generate_candidates, generate_candidates_heterogeneous


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

    def test_each_seed_gets_its_own_retry_budget(self) -> None:
        # seed 0 needs two tries, seed 1 succeeds first try -- a failure on
        # one candidate must not consume or corrupt another's budget.
        calls: list[int] = []

        def generate_fn(query: str, seed: int) -> str:
            calls.append(seed)
            if seed == 0 and calls.count(0) == 1:
                return "garbage"
            return f"ANSWER: {seed}"

        candidates = generate_candidates(
            "q", generate_fn, n=2, validity_fn=lambda t: "ANSWER:" in t
        )
        self.assertEqual([c.text for c in candidates], ["ANSWER: 0", "ANSWER: 1"])

    def test_heterogeneous_backends_also_retry_on_invalid_text(self) -> None:
        responses = iter(["garbage", "ANSWER: B"])
        backends = [("model-a", lambda q, s: next(responses))]
        candidates = generate_candidates_heterogeneous(
            "q", backends, n=1, validity_fn=lambda t: "ANSWER:" in t
        )
        self.assertEqual(candidates[0].text, "ANSWER: B")


if __name__ == "__main__":
    unittest.main()
