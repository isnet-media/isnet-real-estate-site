#!/usr/bin/env python3
"""HTRL discovery regression: dated provenance only, no media auto-publication."""
import unittest
from unittest.mock import patch
from bs4 import BeautifulSoup
import sync_rishon_sources as subject


def soup(html):
    return BeautifulSoup(html, 'html.parser')


def existing(title='לנקות את הראש', date='2026-11-10', time='20:30',
             venue='היכל התרבות ראשון לציון'):
    return [{'event_id': 'review-test', 'title': title, 'start_date': date,
             'start_time': time, 'venue': venue, 'category': 'theatre'}]


LISTING = """
<a href="/show/לנקות-את-הראש-2/">רכישה</a>
<a href="/show/לנקות-את-הראש-2/">רכישה</a>
<a href="https://other.example/show/לנקות-את-הראש-2/">רכישה</a>
"""
DETAIL = """
<html><head><meta property="og:image" content="/uploads/clean.jpg"></head>
<body><h1>לנקות את הראש</h1>
<p>אגדה אורבנית, קומדיה עם הצגה ארוכה ונושא חברתי מרתק...</p>
<h2>מועדי המופע</h2>
<div>10.11.26</div><div>שלישי</div><div>20:30</div><div>היכל התרבות</div><a>לרכישה</a>
<div>11.11.26</div><div>רביעי</div><div>20:30</div><div>היכל התרבות</div><a>לרכישה</a>
<section>תיאטרון 18-21.11 אוי אלוהים</section>
<h2>רכישת מנוי לסדרות</h2>
</body></html>
"""


class OfficialReviewCandidateTests(unittest.TestCase):
    def setUp(self):
        subject.WARNINGS.clear()

    def find(self, listing=LISTING, detail=DETAIL, event=None, src='htrl'):
        def fetch(url):
            return soup(listing if url == subject.SOURCES[src] else detail)
        with patch.object(subject.shared, 'page', side_effect=fetch):
            return subject.official_review_candidates(src, event or existing())

    def test_generic_purchase_links_resolve_from_strict_detail_identity(self):
        rows = self.find()
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual((row['event_id'], row['start_date'], row['start_time']),
                         ('review-test', '2026-11-10', '20:30'))
        self.assertEqual(row['image_rights_status'], 'unknown')
        self.assertEqual(row['publication_status'], 'review_required')
        self.assertTrue(row['image_candidate_url'].endswith('/uploads/clean.jpg'))
        self.assertNotIn('image_url', row)
        self.assertNotIn('description', row)

    def test_different_day_or_time_never_matches(self):
        self.assertEqual(self.find(event=existing(date='2026-11-12')), [])
        self.assertEqual(self.find(event=existing(time='18:00')), [])

    def test_different_venue_or_title_never_matches(self):
        self.assertEqual(self.find(event=existing(venue='מוזיאון אגם')), [])
        self.assertEqual(self.find(detail=DETAIL.replace(
            '<h1>לנקות את הראש</h1>', '<h1>מחזה אחר</h1>')), [])

    def test_no_show_schedule_does_not_infer_related_cards(self):
        detail = '<h1>לנקות את הראש</h1><p>11.11.26 20:30 היכל התרבות</p>'
        self.assertEqual(self.find(detail=detail), [])

    def test_adults_show_culture_route_supported_without_auto_import(self):
        listing = '<a href="/show-culture/מופע-מוזיקלי-3/">רכישה</a>'
        detail = ('<h1>מופע מוזיקלי</h1><h3>מועדי המופע</h3>'
                  '<span>10.11.26</span><span>שלישי</span>'
                  '<span>11:00</span><span>אודיטוריום היכל התרבות</span>')
        rows = self.find(listing=listing, detail=detail,
                         event=existing(title='מופע מוזיקלי', time='11:00',
                                        venue='אודיטוריום היכל התרבות ראשון לציון'),
                         src='htrl_adults')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['publication_status'], 'review_required')


if __name__ == '__main__':
    unittest.main()
