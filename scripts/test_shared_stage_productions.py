#!/usr/bin/env python3
"""Candidate-registry guards: technical site elements are not stage events."""
import unittest

from build_shared_stage_productions import valid_title, valid_source_url


class StageCandidateTitleTests(unittest.TestCase):
    def test_rejects_site_chrome_and_email_protection(self):
        for title in ("Friends Logo", "[email protected]"):
            with self.subTest(title=title):
                self.assertFalse(valid_title(title))

    def test_rejects_timetable_title_with_weekday(self):
        self.assertFalse(valid_title("05.11.26 יום חמישי 20:30 לאתר המכירה זוגיות AI אולם דיונה אשדוד"))
        self.assertFalse(valid_title("יום שבת 20:30 הופעה במרכז העיר"))

    def test_rejects_cloudflare_email_protection_urls(self):
        for url in (
            "https://www.friends.org.il/cdn-cgi/l/email-protection#abcd",
            "https://www.friends.org.il/cdn-cgi/l/email-protection/",
            "not-an-http-url",
        ):
            with self.subTest(url=url):
                self.assertFalse(valid_source_url(url))

    def test_keeps_real_source_detail_url(self):
        self.assertTrue(valid_source_url("https://www.friends.org.il/event/show-123"))

    def test_keeps_real_stage_production(self):
        self.assertTrue(valid_title("פאטמה הסטנדאפיסטית הבדואית"))


if __name__ == "__main__":
    unittest.main()
