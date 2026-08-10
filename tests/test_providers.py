from __future__ import annotations

import os
import unittest

from or_select.pipeline import run_pipeline

_HAS_OPENAI = bool(os.environ.get("OPENAI_API_KEY"))
_HAS_GEMINI = bool(os.environ.get("GOOGLE_API_KEY"))


class ProviderIntegrationTest(unittest.TestCase):
    """Live-API tests. Skipped unless the relevant key is set in the environment."""

    @unittest.skipUnless(_HAS_OPENAI, "OPENAI_API_KEY not set")
    def test_openai_provider_end_to_end(self) -> None:
        result = run_pipeline("What is the capital of France?", n=3, provider="openai")
        self.assertTrue(result.winner_text)

    @unittest.skipUnless(_HAS_GEMINI, "GOOGLE_API_KEY not set")
    def test_gemini_provider_end_to_end(self) -> None:
        result = run_pipeline("What is the capital of France?", n=3, provider="gemini")
        self.assertTrue(result.winner_text)

    @unittest.skipUnless(_HAS_OPENAI and _HAS_GEMINI, "both API keys required")
    def test_both_providers_heterogeneous_end_to_end(self) -> None:
        result = run_pipeline("What is the capital of France?", n=4, provider="both")
        self.assertTrue(result.winner_text)
        source_models = {c.source_model for c in result.candidates}
        self.assertEqual(source_models, {"openai", "gemini"})


if __name__ == "__main__":
    unittest.main()
