import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import usc_baseline as usc  # noqa: E402


class UscParsingTests(unittest.TestCase):
    def test_parse_valid_choice(self):
        self.assertEqual(usc.parse_choice("The most consistent response is Response 2.", 3), 2)
        self.assertEqual(usc.parse_choice("Response 0", 3), 0)

    def test_parse_rejects_out_of_range_or_missing(self):
        self.assertIsNone(usc.parse_choice("The most consistent response is Response 5", 3))
        self.assertIsNone(usc.parse_choice("I cannot decide", 3))

    def test_prompt_lists_every_response_zero_indexed(self):
        prompt = usc.build_prompt("What is 2+2?", ["four", "five"])
        self.assertIn("Response 0: four", prompt)
        self.assertIn("Response 1: five", prompt)
        self.assertIn("What is 2+2?", prompt)


if __name__ == "__main__":
    unittest.main()
