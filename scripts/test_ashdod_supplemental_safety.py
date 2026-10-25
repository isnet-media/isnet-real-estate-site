#!/usr/bin/env python3
"""Non-destructive Ashdod supplemental-source merge regressions."""
import unittest
from sync_ashdod_supplemental import reconcile_ashdod_supplemental, source_placeholder


def row(event_id, source, title="הצגה לדוגמה", venue="משכן אשדוד",
        day="2026-11-04", hour="20:30", **kw):
    record=dict(event_id=event_id, source=source, title=title,
                venue=venue, start_date=day, start_time=hour,
                ticket_url="https://tickets.example.com/listing")
    record.update(kw)
    return record


class SafetyTests(unittest.TestCase):
    def test_preserve_stage_board_when_source_claims_same_occurrence(self):
        legacy=row("board_123", "national_stage_boards")
        supplement=row("makore_as_new", "supplemental_makore")
        kept, accepted, removed, review = reconcile_ashdod_supplemental(
            [legacy], [supplement])
        self.assertEqual(kept, [legacy])
        self.assertFalse(accepted)
        self.assertFalse(removed)
        self.assertEqual(review[0]["reason"], "occurrence_overlap_requires_source_cms_review")

    def test_exact_id_same_source_may_refresh_its_own_record(self):
        old=row("makore_as_123", "supplemental_makore", description="old")
        new=row("makore_as_123", "supplemental_makore", description="new")
        kept, accepted, removed, review = reconcile_ashdod_supplemental(
            [old], [new])
        self.assertFalse(kept)
        self.assertEqual(accepted, [new])
        self.assertEqual(removed, [old])
        self.assertFalse(review)

    def test_different_venues_are_distinct_even_with_generic_booking_url(self):
        first=row("board_1", "national_stage_boards", venue="אולם א")
        second=row("makore_as_2", "supplemental_makore", venue="אולם ב")
        kept, accepted, removed, review = reconcile_ashdod_supplemental(
            [first], [second])
        self.assertEqual(kept, [first])
        self.assertEqual(accepted, [second])
        self.assertFalse(removed)
        self.assertFalse(review)

    def test_same_id_different_source_is_reviewed_not_overwritten(self):
        old=row("shared_id", "national_stage_boards")
        new=row("shared_id", "supplemental_makore")
        kept, accepted, removed, review = reconcile_ashdod_supplemental(
            [old], [new])
        self.assertEqual(kept, [old])
        self.assertFalse(accepted)
        self.assertFalse(removed)
        self.assertEqual(review[0]["reason"], "existing_id_requires_source_cms_review")

    def test_manual_override_not_replaced(self):
        old=row("makore_as_123", "supplemental_makore",
                content_origin="manual", content_locked=True)
        new=row("makore_as_123", "supplemental_makore", description="new")
        kept, accepted, removed, review = reconcile_ashdod_supplemental(
            [old], [new])
        self.assertEqual(kept, [old])
        self.assertFalse(accepted)
        self.assertFalse(removed)
        self.assertEqual(len(review), 1)

    def test_inherited_duplicate_ids_fail_closed(self):
        old=[row("collision", "national_stage_boards", title="מופע 1"),
             row("collision", "mevalim", title="מופע 2")]
        with self.assertRaisesRegex(ValueError, "duplicate an event ID"):
            reconcile_ashdod_supplemental(old, [])

    def test_known_source_placeholders_never_count_as_verified_photo(self):
        self.assertTrue(source_placeholder("https://x/images/live/more/eventNew.jpg"))
        self.assertTrue(source_placeholder("https://x/images/artists/artistShadow.png"))
        self.assertFalse(source_placeholder("https://x/events/a-real-poster.jpg"))


if __name__ == "__main__":
    unittest.main()
