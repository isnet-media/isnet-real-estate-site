import unittest
from bs4 import BeautifulSoup
from collect_unified_stage_events import mevalim_ticket_extract
from event_source_media import friends_image,lazy_image
class SourceMedia(unittest.TestCase):
 def test_lazy_main_and_no_recommendation_donors(self):
  soup=BeautifulSoup('<img src="https://x/logo.png"><div class="wrap_main_img"><img src="data:image/svg+xml,blank" data-lazy-src="https://imagedelivery.net/show/public"></div><div class="wrap_img"><img src="https://x/another-show.jpg"></div>','html.parser')
  self.assertEqual(friends_image(soup,'https://friends-hist.co.il/show/one'),'https://imagedelivery.net/show/public')
  soup.select_one('.wrap_main_img').decompose();self.assertIsNone(friends_image(soup,'https://friends-hist.co.il/show/one'))
 def test_listing_lazy_and_meta_placeholder(self):
  soup=BeautifulSoup('<meta property="og:image" content="data:image/svg+xml,blank"><img data-src="https://x/real.jpg" src="data:image/svg+xml,blank">','html.parser');self.assertEqual(lazy_image(soup.img,'https://x/'),'https://x/real.jpg');self.assertIsNone(friends_image(soup,'https://x/'))
class TicketHeadingTests(unittest.TestCase):
 def test_brand_header_is_not_event_and_venue_stops_at_doors(self):
  soup=BeautifulSoup('<h1>מבלים</h1><h1>פאטמה הסטנדאפיסטית הבדואית</h1><p>20:30 · יום ג · 03.11.2026 · מתנ״ס דיונה, אשדוד פתיחת דלתות: 20:00 פאטמה 20:30</p>','html.parser')
  rows=mevalim_ticket_extract(soup,'https://tickets.mevalim.co.il/event/example')
  self.assertEqual(rows[0]['title'],'פאטמה הסטנדאפיסטית הבדואית')
  self.assertEqual(rows[0]['venue'],'מתנ״ס דיונה, אשדוד')
  self.assertEqual(rows[0]['date_time'],'2026-11-03T20:30:00')
if __name__=='__main__':unittest.main()
