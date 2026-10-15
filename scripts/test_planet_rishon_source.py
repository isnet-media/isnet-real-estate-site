#!/usr/bin/env python3
import copy, unittest
from unittest.mock import MagicMock,patch
import planet_rishon_source as p
import refresh_ashdod_cinema as cinema

class PlanetTests(unittest.TestCase):
 def setUp(self):
  self.body={'films':[{'id':'film-1','name':'סרט בדיקה','link':p.SITE+'/films/test/film-1','length':100,'attributeIds':['family']}], 'events':[{'id':'event-1','filmId':'film-1','cinemaId':'1072','businessDay':'2026-10-17','eventDateTime':'2026-10-18T00:30:00','bookingLink':'https://tickets5.planetcinema.co.il/api/order/event-1','auditorium':'IMAX'}]}
 def test_after_midnight_uses_actual_calendar_date_and_direct_booking(self):
  row=p.parse_day(self.body,'2026-10-17',{})['film-1']
  self.assertEqual(row['schedule'],{'2026-10-18':{'00:30'}})
  self.assertEqual(row['sessions'][0]['booking_url'],self.body['events'][0]['bookingLink'])
  self.assertTrue(row['is_family'])
 def test_language_metadata_survives_for_screening_labels(self):
  self.body['events'][0]['languages']={'dubbed':['he'],'subtitles':['he']}
  session=p.parse_day(self.body,'2026-10-17',{})['film-1']['sessions'][0]
  self.assertEqual(session['dubbed_language'],'he');self.assertEqual(session['subtitled_language'],'he')
 def test_other_city_cannot_enter_branch_snapshot(self):
  self.body['events'][0]['cinemaId']='1073'
  with self.assertRaisesRegex(ValueError,'Non-Rishon'):p.parse_day(self.body,'2026-10-17',{})
 def test_missing_film_invalidates_snapshot(self):
  self.body['films']=[]
  with self.assertRaisesRegex(ValueError,'missing'):p.parse_day(self.body,'2026-10-17',{})
 def test_conflicting_date_invalidates_snapshot(self):
  self.body['events'][0]['eventDateTime']='2026-10-20T19:00:00'
  with self.assertRaisesRegex(ValueError,'conflicts'):p.parse_day(self.body,'2026-10-17',{})
 def test_untrusted_ticket_destination_rejected(self):
  self.body['events'][0]['bookingLink']='https://planetcinema.co.il.example.com/order/1'
  with self.assertRaisesRegex(ValueError,'destination'):p.parse_day(self.body,'2026-10-17',{})
 def test_official_original_poster_is_used_when_large_size_fails(self):
  bad=MagicMock();bad.__enter__.return_value=bad;bad.raise_for_status.side_effect=ValueError('missing size')
  good=MagicMock();good.__enter__.return_value=good;good.headers={'Content-Type':'image/jpeg'}
  row={'source_url':p.SITE+'/films/test/film-1','poster_source_url':p.SITE+'/large.jpg','poster_alternatives':[p.SITE+'/original.jpg']}
  with patch.object(p.requests,'get',side_effect=[bad,good]):p.verify_poster(row)
  self.assertEqual(row['poster_verified']['url'],p.SITE+'/original.jpg');self.assertNotIn('poster_error',row)
 def test_planet_provenance_and_failed_source_retention(self):
  row=p.parse_day(self.body,'2026-10-17',{})['film-1'];old={'movies':[{'id':'f','title':'סרט בדיקה','venues':[{'id':'planet','schedule':{cinema.TODAY:['19:00']}}]}]}
  cinema.VENUES['planet']='פלאנט ראשון לציון'
  kept,_=cinema.merge(copy.deepcopy(old),{'planet':{'status':'failed'}})
  self.assertEqual(kept['movies'][0]['venues'][0]['schedule'],old['movies'][0]['venues'][0]['schedule'])
  merged,_=cinema.merge(old,{'planet':{'status':'ok','movies':[row],'source_url':p.BRANCH_URL}})
  venue=merged['movies'][0]['venues'][0]
  self.assertEqual(venue['source_branch_id'],'1072');self.assertEqual(venue['schedule_source_url'],p.BRANCH_URL)
  self.assertEqual(merged['sources'][0]['url'],p.BRANCH_URL)
if __name__=='__main__':unittest.main()
