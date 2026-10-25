"""Regression tests: national stage-board import must never reuse IDs or delete events."""
import json
import unittest
from scripts.import_national_board_events import claim_import_identity, extract
from scripts.collect_unified_stage_events import event_from_jsonld


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


class StageTimezoneSafety(unittest.TestCase):
    def stage_event(self, start):
        return {
            "@type": "Event", "name": "מופע בדיקה", "startDate": start,
            "location": {"name": "אולם אשדוד", "address": {"addressLocality": "אשדוד"}},
        }

    def test_collector_utc_winter_clock_and_source_provenance(self):
        row = event_from_jsonld(self.stage_event("2026-10-26T15:00:00.000Z"), "makore", "https://example.org/event")
        self.assertEqual(row["date_time"], "2026-10-26T17:00:00+02:00")
        self.assertEqual(row["source_date_time"], "2026-10-26T15:00:00.000Z")

    def test_collector_summer_dst_and_winter_day_rollover(self):
        summer = event_from_jsonld(self.stage_event("2027-07-03T17:00:00Z"), "makore", "https://example.org/event")
        winter = event_from_jsonld(self.stage_event("2027-01-01T22:30:00Z"), "makore", "https://example.org/event")
        self.assertEqual(summer["date_time"], "2027-07-03T20:00:00+03:00")
        self.assertEqual(winter["date_time"], "2027-01-02T00:30:00+02:00")

    def test_collector_leaves_naive_local_time_unchanged(self):
        row = event_from_jsonld(self.stage_event("2026-10-26T17:00:00"), "makore", "https://example.org/event")
        self.assertEqual(row["date_time"], "2026-10-26T17:00:00")

    def test_national_board_importer_converts_utc_jsonld(self):
        page = '<script type="application/ld+json">' + json.dumps(
            self.stage_event("2026-10-26T15:00:00.000Z"), ensure_ascii=False
        ) + '</script>'
        rows = extract(page, "https://example.org/event", "אשדוד")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["start_date"], "2026-10-26")
        self.assertEqual(rows[0]["start_time"], "17:00")


if __name__ == "__main__":
    unittest.main()
