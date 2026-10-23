#!/usr/bin/env python3
"""Fail-closed regression checks for ticketing-site technical logos.

All fixture cleanup executes in a temporary copy, not the live event dataset.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_media_bank
import recover_event_listing_images


class SmarticketLogoSafetyTests(unittest.TestCase):
    LOGOS = (
        "https://ashdod.smarticket.co.il/images/logo.png",
        "https://mishkan-ashdod.smarticket.co.il/logo.jpg?v=3",
        "https://smarticket.co.il/images/logo.webp",
        "https://yama.smarticket.co.il/logo.svg",
    )

    def test_media_bank_rejects_ticket_site_logos(self):
        for url in self.LOGOS:
            with self.subTest(url=url):
                self.assertEqual(build_media_bank.bad_reason(url), "technical_asset:smarticket_logo")
                self.assertFalse(build_media_bank.reusable({
                    "status": "rejected", "publishable": False, "reuse_risk": "low"
                }))

    def test_listing_recovery_rejects_logo_candidates(self):
        for url in self.LOGOS:
            with self.subTest(url=url):
                self.assertTrue(recover_event_listing_images.bad(url))
        self.assertFalse(recover_event_listing_images.bad(
            "https://ashdod.smarticket.co.il/images/live/show_123.jpg"
        ))

    def test_cleanup_removes_logos_even_from_authoritative_records(self):
        with tempfile.TemporaryDirectory(prefix="isnet-logo-fixture-") as tmp:
            base = Path(tmp)
            scripts = base / "scripts"
            data_dir = base / "events-preview" / "ashdod" / "data"
            scripts.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            shutil.copyfile(ROOT / "scripts" / "clean_event_image_placeholders_v2.py",
                            scripts / "clean_event_image_placeholders_v2.py")
            fixture = {"events": [
                {"event_id": "unsafe_authoritative", "title": "Fixture one",
                 "source_content_authoritative": True,
                 "image_url": self.LOGOS[0], "image_origin_url": self.LOGOS[0],
                 "thumbnail_url": self.LOGOS[0], "thumbnail_ready": True,
                 "image_publishable": True, "image_verified": True,
                 "image_source": "https://ashdod.smarticket.co.il/example"},
                {"event_id": "safe_authoritative", "title": "Fixture two",
                 "source_content_authoritative": True,
                 "image_url": "https://ashdod.smarticket.co.il/images/live/show_123.jpg",
                 "image_publishable": True, "image_verified": True},
                {"event_id": "unsafe_other", "title": "Fixture three",
                 "image_url": self.LOGOS[1],
                 "image_publishable": True, "image_verified": True},
            ]}
            path = data_dir / "events.json"
            path.write_text(json.dumps(fixture), encoding="utf-8")
            subprocess.run([sys.executable, str(scripts / "clean_event_image_placeholders_v2.py")],
                           check=True, text=True, capture_output=True, timeout=15)
            saved = json.loads(path.read_text(encoding="utf-8"))["events"]
            report = json.loads((data_dir / "image-enrichment-report.json").read_text(encoding="utf-8"))
            for event in (saved[0], saved[2]):
                self.assertIsNone(event["image_url"])
                self.assertIs(event["image_publishable"], False)
                self.assertIs(event["image_verified"], False)
            self.assertIsNone(saved[0]["thumbnail_url"])
            self.assertIsNone(saved[0]["image_origin_url"])
            self.assertEqual(saved[1]["image_url"], fixture["events"][1]["image_url"])
            self.assertEqual(report["stats"]["generic_images_cleared"], 2)
            self.assertEqual(report["events_still_missing_images"], 2)


if __name__ == "__main__":
    unittest.main()
