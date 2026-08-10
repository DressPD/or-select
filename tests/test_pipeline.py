from __future__ import annotations

import unittest

from or_select.pipeline import run_pipeline


class PipelineTest(unittest.TestCase):
    def test_pipeline_smoke_run_with_placeholder_backends(self) -> None:
        result = run_pipeline("What is the capital of France?", n=5)
        self.assertTrue(result.winner_id)
        self.assertEqual(len(result.candidates), 5)
        self.assertIn(result.winner_id, result.scores)

    def test_pipeline_is_deterministic_given_placeholder_backends(self) -> None:
        first = run_pipeline("Same query", n=5)
        second = run_pipeline("Same query", n=5)
        self.assertEqual(first.winner_id, second.winner_id)
        self.assertEqual(first.winner_text, second.winner_text)


if __name__ == "__main__":
    unittest.main()
