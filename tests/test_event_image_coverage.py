"""Regression tests for report-only event-image coverage classification."""
import unittest

from scripts.fast_fill_event_images_from_listings import (
    image_coverage_counts,
    is_non_event_representative_art,
    correct_inherited_representative_metadata,
)


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

    def test_owned_fallback_cannot_be_reused_as_official_show_photo(self):
        fallback = {
            "image_url": "assets/defaults/festival.svg",
            "image_source": "ISNET internal representative artwork",
            "image_verified": True,
            "image_publishable": True,
            "image_represents_event": False,
            "image_strategy": "super_editor_representative_fallback",
        }
        self.assertTrue(is_non_event_representative_art(fallback))
        official = {
            "image_url": "https://official.example/show-poster.jpg",
            "image_source": "official.example",
            "image_verified": True,
            "image_publishable": True,
            "image_strategy": "official_source_image",
            "image_represents_event": True,
        }
        self.assertFalse(is_non_event_representative_art(official))

    def test_inherited_category_art_metadata_is_corrected_without_removing_image(self):
        inherited = {
            "image_url": "assets/defaults/festival.svg",
            "image_source": "ISNET internal representative artwork",
            "image_strategy": "same_production_reuse",
            "image_rights_status": "verified_official_source",
            "image_verified": True,
            "image_publishable": True,
            "image_represents_event": False,
        }
        before_url = inherited["image_url"]
        self.assertTrue(correct_inherited_representative_metadata(inherited))
        self.assertEqual(inherited["image_url"], before_url)
        self.assertEqual(inherited["image_strategy"], "super_editor_representative_fallback")
        self.assertEqual(inherited["image_rights_status"], "owned_system_asset")
        self.assertTrue(inherited["image_represents_category"])
        self.assertFalse(correct_inherited_representative_metadata(inherited))

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
