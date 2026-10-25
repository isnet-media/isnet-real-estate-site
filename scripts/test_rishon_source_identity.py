#!/usr/bin/env python3
"""Non-destructive tests for reused Rishon source IDs and editorial details."""
import unittest
from copy import deepcopy
from sync_rishon_sources import merge


def event(event_id, title, date='2026-12-27', time='17:30',
          venue='היכל התרבות ראשון לציון', source='mevalim_direct', **more):
    return {
        'event_id': event_id, 'title': title, 'start_date': date,
        'start_time': time, 'venue': venue, 'source': source,
        'description': '', 'content_source_url': 'https://example.test/show',
        'image_url': None, **more,
    }


class RishonSourceIdentitySafety(unittest.TestCase):
    def test_existing_duplicated_id_cannot_be_overwritten(self):
        editorial = event('mevalim_ri_legacy', 'סינדרלה — עם נעמה סופר על')
        editorial.update(content_locked=True, description='Source-reviewed text',
                         image_url='illustration.webp', image_verified=True)
        stale = event('mevalim_ri_legacy', 'סינדרלה - רינת גבאי קיץ')
        existing = [editorial, stale]
        before = deepcopy(existing)
        after, report = merge(existing, [deepcopy(stale)])
        self.assertEqual(after, before)
        self.assertEqual(report['id_collisions_quarantined'], 1)
        self.assertEqual(report['added'], 0)
        self.assertEqual(report['updated'], 0)

    def test_existing_id_changed_title_is_quarantined(self):
        existing = [event('same', 'Original show')]
        before = deepcopy(existing)
        after, report = merge(existing, [event('same', 'Different show')])
        self.assertEqual(after, before)
        self.assertEqual(report['id_collisions_quarantined'], 1)

    def test_existing_id_changed_time_is_quarantined(self):
        existing = [event('same', 'Same show')]
        after, report = merge(existing, [event('same', 'Same show', time='20:30')])
        self.assertEqual(after, existing)
        self.assertEqual(report['id_collisions_quarantined'], 1)

    def test_existing_id_changed_venue_is_quarantined(self):
        existing = [event('same', 'Same show')]
        after, report = merge(existing, [event('same', 'Same show', venue='אולם אחר')])
        self.assertEqual(after, existing)
        self.assertEqual(report['id_collisions_quarantined'], 1)

    def test_exact_id_identity_refresh_preserves_editorial_and_media(self):
        original = event('same', 'Same show')
        original.update(content_locked=True, description='Approved description',
                        image_url='event-photo.jpg', image_verified=True,
                        thumbnail_url='old-thumb.jpg', thumbnail_ready=True)
        incoming = event('same', 'Same show')
        incoming.update(description='Unreviewed source text', image_url='generic.jpg')
        after, report = merge([original], [incoming])
        self.assertEqual(len(after), 1)
        self.assertEqual(after[0]['description'], 'Approved description')
        self.assertEqual(after[0]['image_url'], 'event-photo.jpg')
        self.assertEqual(after[0]['thumbnail_url'], 'old-thumb.jpg')
        self.assertEqual(report['updated'], 1)
        self.assertEqual(report['id_collisions_quarantined'], 0)

    def test_new_reused_id_in_same_batch_is_quarantined(self):
        first = event('fresh', 'Show A')
        second = event('fresh', 'Show B')
        after, report = merge([], [first, second])
        self.assertEqual(len(after), 1)
        self.assertEqual(report['added'], 1)
        self.assertEqual(report['id_collisions_quarantined'], 1)

    def test_genuinely_new_distinct_ids_are_added(self):
        after, report = merge([], [event('new-a', 'Show A'),
                                   event('new-b', 'Show B', time='20:30')])
        self.assertEqual(len(after), 2)
        self.assertEqual(report['added'], 2)
        self.assertEqual(report['id_collisions_quarantined'], 0)


if __name__ == '__main__':
    unittest.main()
