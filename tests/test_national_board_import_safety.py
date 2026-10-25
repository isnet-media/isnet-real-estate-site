"""Regression tests: national stage-board import must never reuse IDs or delete events."""
import unittest
from scripts.import_national_board_events import claim_import_identity


class NationalBoardIdentitySafety(unittest.TestCase):
    def setUp(self):
        self.row = {
            "title": "הופעה לדוגמה",
            "start_date": "2026-11-30",
            "start_time": "20:30",
            "venue": "היכל התרבות ראשון לציון",
        }
        self.key = tuple(self.row[k] for k in ("title", "start_date", "start_time", "venue"))

    def test_valid_import_claims_unique_id_and_occurrence(self):
        occurrences, ids = set(), set()
        event_id, reason = claim_import_identity("rishon-lezion", self.row, occurrences, ids)
        self.assertIsNone(reason)
        self.assertTrue(event_id.startswith("auto_ri_"))
        self.assertIn(event_id, ids)
        self.assertIn(self.key, occurrences)
        duplicate_id, reason = claim_import_identity("rishon-lezion", self.row, occurrences, ids)
        self.assertIsNone(duplicate_id)
        self.assertEqual(reason, "existing_occurrence")
        self.assertEqual(len(ids), 1)

    def test_existing_id_with_different_current_fields_never_reused(self):
        first_id, _ = claim_import_identity("rishon-lezion", self.row, set(), set())
        # Existing editor-modified row has the same stable ID but a changed venue.
        existing_key = (self.row["title"], self.row["start_date"],
                        self.row["start_time"], "אולם אחר")
        occurrences, ids = {existing_key}, {first_id}
        duplicate_id, reason = claim_import_identity("rishon-lezion", self.row, occurrences, ids)
        self.assertIsNone(duplicate_id)
        self.assertEqual(reason, "event_id_collision")
        self.assertEqual(occurrences, {existing_key})
        self.assertEqual(ids, {first_id})

    def test_same_occasion_with_existing_title_and_venue_is_not_duplicated(self):
        occurrences, ids = {self.key}, set()
        duplicate_id, reason = claim_import_identity("ashdod", self.row, occurrences, ids)
        self.assertIsNone(duplicate_id)
        self.assertEqual(reason, "existing_occurrence")
        self.assertFalse(ids)


if __name__ == "__main__":
    unittest.main()
