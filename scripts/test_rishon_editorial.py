#!/usr/bin/env python3
"""Regression checks for source binding, refresh preservation and public quality."""
import copy,json,unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup
import apply_rishon_editorial as a
import finalize_rishon_quality as q
import rishon_editorial_sources as source
import sync_rishon_sources as intake

class EditorialTests(unittest.TestCase):
 def setUp(self):
  self.day=a.TODAY.isoformat();self.url='https://htrl.co.il/show/example/'
  self.program=dict(lookup_title='סיפור',lookup_url=self.url,source_url=self.url,category='kids',subcategory='kids-theatre',description='תיאור מקורי של ההצגה ושל הדמויות המופיעות בה. פעילות לילדים ולמשפחות עם תוכן מפורט וקישור למקור הרשמי, המאפשרים לבחור מועד ולבדוק את פרטי ההשתתפות.')
  self.row=dict(source='htrl',title='סיפור',start_date=self.day,start_time='11:00',venue='היכל התרבות',detail_url=self.url,booking_url='https://htrl.co.il/tickets?showURL=42',source_text='מידע מקור',age_text='חצי שנה עד הליכה')
  self.catalog={'programs':[self.program]};self.snap={'checked_at':'2026-10-16T00:00:00+03:00','rows':[self.row]}
 def event(self,**kw):
  e=dict(event_id='original',title='סיפור',start_date=self.day,start_time='11:00',venue='היכל התרבות',category='other',is_active=True,sources=[]);e.update(kw);return e
 def test_date_time_and_venue_are_bound_to_their_own_occurrence(self):
  wrong=self.event(event_id='other-venue',venue='כותר אלון');data={'events':[wrong]}
  result,stats=a.merge(data,self.snap,self.catalog,False)
  self.assertEqual(stats['added'],1);self.assertEqual(wrong['category'],'other');self.assertEqual(result['events'][1]['purchase_url'],self.row['booking_url'])
 def test_repeated_refresh_has_stable_identity_and_no_duplicates(self):
  d={'events':[self.event()]}
  first,_=a.merge(d,self.snap,self.catalog,False);second,stats=a.merge(copy.deepcopy(first),self.snap,self.catalog,False)
  self.assertEqual(len(second['events']),1);self.assertEqual(stats.get('added',0),0);self.assertEqual(second['events'][0]['event_id'],'original')
 def test_online_venue_normalization_does_not_create_a_new_record_each_day(self):
  self.row.update(source='kotar',venue='כותר ראשון',source_category='מהכורסא',source_text='הרצאה בזום')
  self.program.pop('lookup_url');data={'events':[]}
  for _ in range(3):data,stats=a.merge(data,self.snap,self.catalog,False)
  self.assertEqual(len(data['events']),1);self.assertEqual(data['events'][0]['attendance_mode'],'online')
 def test_same_title_different_productions_keep_their_descriptions(self):
  other={**self.program,'lookup_url':'https://htrl.co.il/show/ballet/','category':'music','description':'מופע בלט אחר'}
  d={'events':[self.event(detail_source_url=self.url)]};q.finalize(d,{'programs':[self.program,other]})
  self.assertEqual(d['events'][0]['description'],self.program['description'])
 def test_ambiguous_title_without_detail_does_not_guess(self):
  other={**self.program,'lookup_url':'https://htrl.co.il/show/ballet/','description':'תיאור אחר'}
  d={'events':[self.event()]};q.finalize(d,{'programs':[self.program,other]})
  self.assertNotIn('editorial_description',d['events'][0])
 def test_approved_source_photo_survives_editorial_refresh(self):
  e=self.event(image_url='https://htrl.co.il/original.jpg',image_verified=True,image_strategy='official_event_poster')
  a.merge({'events':[e]},self.snap,self.catalog,False);self.assertEqual(e['image_url'],'https://htrl.co.il/original.jpg')
 def test_malformed_source_booking_is_not_guessed(self):
  self.assertEqual(a.canonical_booking({'booking_url':'https://example.com/please call us'}),'')
 def test_developmental_age_text_survives_without_invented_upper_age(self):
  d,_=a.merge({'events':[]},self.snap,self.catalog,False);e=d['events'][0]
  self.assertEqual(e['age_text'],'חצי שנה עד הליכה');self.assertIsNone(e.get('age_max'))
 def test_duplicates_retain_canonical_identity_for_old_links(self):
  p=self.event(description='הפקה',editorial_version=1,image_verified=True,image_url='https://a.test/a.jpg');dup=self.event(event_id='old-link');d={'events':[p,dup]};q.finalize(d,{'programs':[]})
  self.assertFalse(dup['is_active']);self.assertEqual(dup['canonical_event_id'],'original');self.assertEqual(len(d['events']),2)
 def test_unnamed_film_is_not_published_as_a_fabricated_program(self):
  e=self.event(title='הקרנת סרט',category='cinema');q.finalize({'events':[e]},{'programs':[]});self.assertFalse(e['is_active']);self.assertEqual(e['visibility_reason'],'awaiting_program_details')
 def test_illustration_is_explicit_and_not_credited_as_source_photo(self):
  e=self.event(category='kids',subcategory='kids-story');q.finalize({'events':[e]},{'programs':[]});self.assertEqual(e['image_strategy'],'approved_category_illustration');self.assertIn('אילוסטרציה',e['image_credit'])
 def test_national_refresh_preserves_locked_copy_and_verified_image(self):
  old=self.event(category='kids',description=self.program['description'],content_locked=True,image_verified=True,image_url='https://a.test/photo.jpg',thumbnail_url='https://a.test/photo.jpg',thumbnail_ready=True)
  fresh=self.event(event_id='new-intake',category='other',description='',image_url=None,content_source_url='https://listing.test/')
  merged,_=intake.merge([old],[fresh]);self.assertEqual(len(merged),1);self.assertEqual(merged[0]['description'],self.program['description']);self.assertEqual(merged[0]['image_url'],'https://a.test/photo.jpg');self.assertTrue(merged[0]['thumbnail_ready'])
 def test_museum_tables_do_not_duplicate_top_and_full_schedule(self):
  day=a.TODAY+timedelta(days=2);months=['ינואר','פברואר','מרץ','אפריל','מאי','יוני','יולי','אוגוסט','ספטמבר','אוקטובר','נובמבר','דצמבר']
  html='<h1>סיור</h1><table><tbody>'+('<tr><td><a href="/visit/?id=4922">ביום שבת, '+str(day.day)+' ב'+months[day.month-1]+' '+str(day.year)+' בשעה 10:15</a></td></tr>')*2+'</tbody></table>'
  with patch.object(source,'page',return_value=BeautifulSoup(html,'html.parser')):rows=source.museum_rows('https://yama.smarticket.co.il/visit')
  self.assertEqual(len(rows),1);self.assertEqual(rows[0]['booking_url'],'https://yama.smarticket.co.il/visit/?id=4922')

 def test_root_relative_media_is_not_prefixed_with_city(self):
  from repair_rishon_public_quality import normalize_media
  self.assertEqual(normalize_media('../rishon-lezion//events-preview/media-bank/cards/a.webp'),'/events-preview/media-bank/cards/a.webp')
  self.assertEqual(normalize_media('/events-preview/media-bank/cards/a.webp'),'/events-preview/media-bank/cards/a.webp')
  self.assertEqual(normalize_media('https://example.com/a.webp'),'https://example.com/a.webp')
 def test_title_aliases_hide_same_occurrence_but_preserve_different_times(self):
  from repair_rishon_public_quality import prepare,finish
  rows=[self.event(title='מצחיקונת',category='theatre'),self.event(event_id='alias',title='מחזמר מצחיקונת - Funny Girl',category='theatre'),self.event(event_id='later',title='מצחיקונת',category='theatre',start_time='19:00')]
  d,c=prepare({'events':rows},{'programs':[]});finish(d,c)
  self.assertEqual(sum(e.get('is_active')is not False for e in rows),2)
  self.assertTrue(rows[2]['is_active']);self.assertEqual(rows[1]['canonical_event_id'],'original')
 def test_named_cinderella_productions_are_not_aliased(self):
  from repair_rishon_public_quality import prepare
  d,c=prepare({'events':[]},{'programs':[],'title_aliases':{'סינדרלה — מחזמר חנוכה עם נעמה סופר על':'סינדרלה - בכיכובה של רינת גבאי קיץ 2026'}})
  self.assertNotIn('סינדרלה — מחזמר חנוכה עם נעמה סופר על',c['title_aliases'])
 def test_dance_at_museum_is_not_an_exhibition(self):
  e=self.event(title='להקת המחול ורטיגו - "נונה" גרסת המוזיאון',category='exhibition',venue='מוזיאון אגם')
  q.finalize({'events':[e]},{'programs':[]})
  self.assertEqual(e['category'],'music');self.assertEqual(e['subcategory'],'dance');self.assertNotIn('exhibition',e['categories'])

if __name__=='__main__':unittest.main()
