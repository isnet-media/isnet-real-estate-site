#!/usr/bin/env python3
"""Candidate-registry guards: technical site elements are not stage events."""
import unittest

from build_shared_stage_productions import valid_title


class StageCandidateTitleTests(unittest.TestCase):
    def test_rejects_site_chrome_and_email_protection(self):
        for title in ("Friends Logo", "[email protected]"):
            with self.subTest(title=title):
                self.assertFalse(valid_title(title))

    def test_keeps_real_stage_production(self):
        self.assertTrue(valid_title("פאטמה הסטנדאפיסטית הבדואית"))


if __name__ == "__main__":
    unittest.main()
