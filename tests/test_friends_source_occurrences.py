"""Static tests for venue/date proof in FRIENDS candidate discovery."""
import sys
import unittest
from datetime import date
from pathlib import Path
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from discover_friends_events import extract_dated_occurrences


def block(venue, when, event_id="1234"):
    return f"""<div class="wrap_item">
      <div class="hall-name-wrap">{venue}</div>
      <div class="wrap_event">יום חמישי {when} <a data-event_id="{event_id}">הזמנה</a></div>
    </div>"""


class FriendsOccurrenceTests(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 10, 30)

    def parse(self, markup, city):
        return extract_dated_occurrences(BeautifulSoup(markup, "html.parser"), city, self.today)

    def test_local_occurrences_only_and_no_auto_publish(self):
        html = f"""<div class="search_show_row">
          <div class="wrap_title"><h3>הבנאים</h3></div>
          <a href="/show/הבנאים">לפרטים</a>
          <div class="wrap_img"><a><img data-lazy-src="https://imagedelivery.net/photo.webp"></a></div>
          <div class="tooltip-show-content">מופע משפחתי אינטימי של שלושה דורות עם שירים וסיפורים שעוברים מדור לדור, מוזיקה מקורית וקולות אהובים.</div>
          <div class="events_list">
            {block("FRIENDS ראשון לציון", "05.11.26 20:30", "R-1")}
            {block("אולם מופעים דיונה אשדוד", "14.12.26 20:30", "A-1")}
            {block("אולם מופעים דיונה אשדוד", "14.12.26 20:30", "A-1")}
            {block("FRIENDS חדרה", "24.11.26 20:30", "H-1")}
          </div></div>"""
        ashdod = self.parse(html, "ashdod")
        rishon = self.parse(html, "rishon-lezion")
        self.assertEqual(len(ashdod), 1)
        self.assertEqual(len(rishon), 1)
        self.assertEqual(ashdod[0]["start_date"], "2026-12-14")
        self.assertEqual(rishon[0]["start_date"], "2026-11-05")
        self.assertEqual(rishon[0]["start_time"], "20:30")
        self.assertEqual(rishon[0]["source_event_id"], "R-1")
        self.assertEqual(ashdod[0]["image_rights_status"], "not_verified")
        self.assertFalse(ashdod[0]["publication_enabled"])
        self.assertTrue(ashdod[0]["description_candidate"])

    def test_no_venue_no_date_cross_origin_and_expired_are_held(self):
        html = f"""<div class="search_show_row"><h3>מופע אחד</h3><a href="/show/ok">פרטים</a>
          <div class="events_list">
           {block("תל אביב", "10.11.26 20:30")}
           {block("FRIENDS ראשון לציון", "01.10.26 20:30")}
           {block("FRIENDS ראשון לציון", "30.13.26 20:30")}
           {block("FRIENDS ראשון לציון", "לא ידוע")}
           {block("FRIENDS ראשון לציון", "01.11.26 25:00")}
          </div></div>
          <div class="search_show_row"><h3>מופע חיצוני</h3>
          <a href="https://unsafe.example/show/xyz">פרטים</a>
          <div class="events_list">{block("FRIENDS ראשון לציון", "05.11.26 20:30")}</div></div>"""
        self.assertEqual(self.parse(html, "rishon-lezion"), [])

    def test_valid_future_occurrence_without_image_is_candidate(self):
        html = f"""<div class="search_show_row"><h3>מופע</h3><a href="/show/מופע">פרטים</a>
          <div class="events_list">{block("אולם אשדוד", "01.11.2026 19:00")}</div></div>"""
        rows = self.parse(html, "ashdod")
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]["image_candidate_url"])
        self.assertIsNone(rows[0]["description_candidate"])
        self.assertEqual(rows[0]["status"], "candidate_requires_human_review")


if __name__ == "__main__":
    unittest.main()
