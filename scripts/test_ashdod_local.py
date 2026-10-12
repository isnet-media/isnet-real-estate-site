import copy, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import sync_ashdod_local as s

class LocalResetTests(unittest.TestCase):
 def event(self,source,eid='e'):
  return dict(event_id=eid,source=source,title='הרצאה על היסטוריה',start_date='2026-12-01',start_time='18:00',venue='אשדוד',category='lecture',subcategory='lecture',source_category='הרצאות',image_url=None,source_image_kind='not_available',description='תיאור מאומת',content_source_url='https://official.example/event/'+eid,ticket_url='https://official.example/event/'+eid)
 def test_reset_is_recoverable_and_does_not_delete_national(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);out=root/'events-preview/admin/data';out.mkdir(parents=True);data=root/'events-preview/ashdod/data';data.mkdir(parents=True)
   legacy=self.event(None,'old');legacy['sources']=[dict(name='ashdod_smarticket')];legacy['image_url']='https://example.com/unrelated.jpg'
   national=self.event('mevalim_direct','national');national['title']='מופע אחר'
   fresh=self.event('local_ashdod_smarticket','fresh');fresh.update(local_source_refresh=True,local_source_name='ashdod_smarticket')
   (data/'events.json').write_text(json.dumps(dict(events=[legacy,national])));(out/'taxonomy.json').write_text(json.dumps(dict(primary_categories=[])))
   snap=dict(at='2026-10-12T15:00:00+03:00',sources={'ashdod_smarticket':dict(ok=True)},events=[fresh])
   with patch.object(s,'ROOT',root),patch.object(s,'OUT',out):s.merge(snap)
   result=json.loads((data/'events.json').read_text())['events']
   self.assertEqual({e['event_id'] for e in result},{'fresh','national'})
   self.assertIsNone(next(e for e in result if e['event_id']=='fresh')['image_url'])
   self.assertEqual(json.loads((out/'ashdod-local-reset-backup.json').read_text())['events'][0],legacy)
 def test_failed_source_preserves_only_rebuilt_cards(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);out=root/'events-preview/admin/data';out.mkdir(parents=True);data=root/'events-preview/ashdod/data';data.mkdir(parents=True)
   fresh=self.event('local_up60');fresh.update(local_source_refresh=True,local_source_name='up60')
   (data/'events.json').write_text(json.dumps(dict(events=[fresh])));(out/'taxonomy.json').write_text(json.dumps(dict(primary_categories=[])))
   with patch.object(s,'ROOT',root),patch.object(s,'OUT',out):s.merge(dict(at='now',sources={'up60':dict(ok=False)},events=[]))
   self.assertEqual(json.loads((data/'events.json').read_text())['events'],[fresh])
 def test_child_workshop_and_factual_short_copy(self):
  e=self.event('x');e.update(title='סדנת ציור לילדים',description='',internal_notes=[])
  r=s.localize(e,'ironit');self.assertEqual(r['category'],'kids');self.assertEqual(r['content_completion_status'],'facts_only');self.assertNotIn('משתתפים',r['description'])
 def test_valid_jpeg_is_accepted_with_octet_stream_header(self):
  class Response:
   ok=True
   headers={'Content-Type':'application/octet-stream'}
   def iter_content(self,n):yield b'\xff\xd8\xff\xe0JFIF'
   def close(self):pass
  e=self.event('local_ironit');e.update(image_url='https://official.example/photo.jfif',source_image_kind='source_card_image',internal_notes=[])
  with patch.object(s.requests,'get',return_value=Response()):s.image_policy([e])
  self.assertTrue(e['image_verified']);self.assertEqual(e['source_image_kind'],'source_card_image')
 def test_rich_life_experience_is_not_a_music_genre(self):
  e=self.event('local_ashdod_smarticket');e.update(title='מוצאים עוגן בתוך הסערה | לנשים בלבד',category='music',description='ניסיון החיים העשיר והחוסן שבניתם',internal_notes=[],local_source_name='ashdod_smarticket')
  s.classify_local(e);self.assertEqual(e['category'],'community');self.assertEqual(e['subcategory'],'women-events')
 def test_primary_schedule_confirms_year_instead_of_short_post_date(self):
  from bs4 import BeautifulSoup
  p=BeautifulSoup('<img src="/FilesSrc/Galleries/Pic.jpg" alt="מופע מחול"><div id="PageContent"><h1>מופע מחול</h1><p>הפקת המחול</p><h2>מועדים</h2><table><tr><td>08.03.2027</td><td>שני</td><td>20:00</td><td><a href="tickets.asp?showURL=8224">הזמנה</a></td></tr></table></div>','html.parser')
  e=s.primary_cards('tarbutashdod','https://www.mishkan-ashdod.co.il/event.asp?event=5717',p,dict(event_date='8.3',location='המשכן',content=dict(rendered='הפקת המחול'),link='https://www.tarbutashdod.com/post'))[0]
  self.assertEqual(e['start_date'],'2027-03-08');self.assertEqual(e['start_time'],'20:00');self.assertEqual(e['image_url'],'https://www.mishkan-ashdod.co.il/FilesSrc/Galleries/Pic.jpg')
 def test_midnight_metadata_is_replaced_by_explicit_ofek_hour(self):
  from bs4 import BeautifulSoup
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);out=root/'events-preview/admin/data';out.mkdir(parents=True);data=root/'events-preview/ashdod/data';data.mkdir(parents=True)
   e=self.event('local_ofek_ashdod');e.update(local_source_refresh=True,local_source_name='ofek_ashdod',start_time='00:00',internal_notes=[],content_completion_status='facts_only')
   (data/'events.json').write_text(json.dumps(dict(events=[])));(out/'taxonomy.json').write_text(json.dumps(dict(primary_categories=[])))
   doc=BeautifulSoup('<div class="eic-field"><span class="eic-label">שעה</span><span class="eic-value">07:20</span></div>','html.parser')
   with patch.object(s,'ROOT',root),patch.object(s,'OUT',out),patch.object(s,'page',return_value=doc):s.merge(dict(at='now',sources={'ofek_ashdod':dict(ok=True)},events=[e]))
   result=json.loads((data/'events.json').read_text())['events'][0];self.assertEqual(result['start_time'],'07:20');self.assertNotIn('00:00',result['description'])
 def test_official_venue_corrects_portal_without_overwriting_discount(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);out=root/'events-preview/admin/data';out.mkdir(parents=True);data=root/'events-preview/ashdod/data';data.mkdir(parents=True)
   old=self.event('supplemental_makore','old');old.update(venue='מוזיאון',address='כתובת שגויה',price_min_ils=79)
   fresh=self.event('local_ashdod_smarticket','fresh');fresh.update(local_source_refresh=True,local_source_name='ashdod_smarticket',venue='מונארט',venue_address='דרך ארץ 8 אשדוד',price_min_ils=100)
   (data/'events.json').write_text(json.dumps(dict(events=[old])));(out/'taxonomy.json').write_text(json.dumps(dict(primary_categories=[])))
   with patch.object(s,'ROOT',root),patch.object(s,'OUT',out):s.merge(dict(at='now',sources={'ashdod_smarticket':dict(ok=True)},events=[fresh]))
   result=json.loads((data/'events.json').read_text())['events'][0];self.assertEqual(result['venue'],'מונארט');self.assertEqual(result['address'],'דרך ארץ 8 אשדוד');self.assertEqual(result['price_min_ils'],79)

if __name__=='__main__':unittest.main()
