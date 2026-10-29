"""Regression tests for report-only event-image coverage classification."""
import unittest

from scripts.fast_fill_event_images_from_listings import bank_asset_provenance_matches as fast_bank_match
from scripts.reuse_media_bank_images import bank_asset_provenance_matches as reusable_bank_match
from scripts.fast_fill_event_images_from_listings import image_coverage_counts


class ImageCoverageTests(unittest.TestCase):
    def test_representative_art_is_not_verified_production_artwork(self):
        events = [
            {"image_url": "https://official.example/poster.jpg",
             "image_verified": True, "image_publishable": True,
             "image_strategy": "official_source_image"},
            # The existing fallback writer sets image_verified=True for owned art;
            # that must not inflate event-specific image coverage.
            {"image_url": "/events-preview/media-bank/defaults/theatre.webp",
             "image_verified": True, "image_publishable": True,
             "image_strategy": "super_editor_representative_fallback",
             "image_represents_event": False},
            {"thumbnail_url": "assets/defaults/music.svg",
             "image_verified": True, "image_publishable": True,
             "image_represents_event": False},
            {"image_url": "https://example.org/unreviewed.jpg",
             "image_verified": False, "image_publishable": False},
            {"image_url": None, "thumbnail_url": None},
        ]
        result = image_coverage_counts(events)
        self.assertEqual(result["images_present"], 4)
        self.assertEqual(result["verified_images"], 1)
        self.assertEqual(result["representative_fallback_images"], 2)
        self.assertEqual(result["unverified_or_unknown_images"], 1)
        self.assertEqual(result["still_missing"], 1)
        self.assertEqual(result["needs_verified_event_photo"], 4)
        self.assertEqual(
            sum(result[key] for key in ("verified_images",
                "representative_fallback_images",
                "unverified_or_unknown_images", "still_missing")),
            len(events),
        )

    def test_bank_reuse_requires_same_title_for_every_provenance_reference(self):
        same_show = {
            "events": [
                {"title": "מופע מקורי", "event_id": "ashdod-1", "date": "2026-11-10"},
                {"title": "מופע מקורי", "event_id": "rishon-2", "date": "2026-12-05"},
            ],
            "reuse_risk": "low",
        }
        suspicious = {
            "events": [
                {"title": "סדנת צרכנות דיגיטלית"},
                {"title": "סדנאת לעיצוב עוגות בנטו"},
            ],
            "reuse_risk": "low",
        }
        for match in (fast_bank_match, reusable_bank_match):
            with self.subTest(implementation=match.__module__):
                self.assertTrue(match({"title": "מופע מקורי"}, same_show))
                self.assertFalse(match({"title": "סדנאת לעיצוב עוגות בנטו"}, suspicious))
                self.assertFalse(match({"title": "מופע מקורי"}, {"events": []}))
                self.assertFalse(match({"title": "מופע מקורי"}, dict(same_show, reuse_risk="review")))
                self.assertFalse(match({"title": "מופע אחר"}, same_show))
                self.assertFalse(match({"title": "מופע מקורי"}, {"events": [{"title": ""}]}))

    def test_empty_feed(self):
        result = image_coverage_counts([])
        self.assertEqual(result["verified_images"], 0)
        self.assertEqual(result["images_present"], 0)
        self.assertEqual(result["needs_verified_event_photo"], 0)

    def test_duplicate_identifiers_do_not_modify_or_deduplicate_rows(self):
        rows = [
            {"event_id": "same", "image_url": "official.png",
             "image_verified": True, "image_publishable": True},
            {"event_id": "same", "image_url": "illustration.png",
             "image_strategy": "super_editor_representative_fallback",
             "image_verified": True, "image_publishable": True},
        ]
        before = [dict(x) for x in rows]
        result = image_coverage_counts(rows)
        self.assertEqual(result["verified_images"], 1)
        self.assertEqual(result["representative_fallback_images"], 1)
        self.assertEqual(rows, before)


if __name__ == "__main__":
    unittest.main()
