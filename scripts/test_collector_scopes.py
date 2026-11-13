"""No-network regression checks for independent collector scopes and last-good state."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup
import sync_herzliya_events as city
import collect_herzliya_seniors as seniors

class CollectorScopeTests(unittest.TestCase):
 def test_directory_refresh_never_collects_or_rewrites_events(self):
  saves={}
  with patch.object(city,'read',return_value={'items':[{'id':'restaurant'}]}), patch.object(city,'save',side_effect=lambda k,v:saves.update({k:v})),patch.object(city,'enrich_directory',side_effect=lambda x:x),patch.object(city,'ingest',side_effect=AssertionError('event source called')),patch('requests.sessions.Session.request',side_effect=AssertionError('unexpected network')):
   city.main('directories')
  self.assertEqual(set(saves),{'guides','restaurants'})

 def test_weekly_events_never_scan_directory_sources_or_write_directory_timestamps(self):
  rows=[{'id':str(i),'source_id':'city','title':'event '+str(i),'start_date':'2099-01-01','start_time':'20:00'} for i in range(20)]
  data={'sources':{'sources':[{'id':'city','parser':'municipal'},{'id':'food','parser':'directory'}]},'events':{'events':[]}}
  seen=[];saves={}
  def ingest(spec):seen.append(spec['id']);return copy.deepcopy(rows),{'id':spec['id'],'status':'ok'}
  with patch.object(city,'read',side_effect=lambda k:copy.deepcopy(data[k])),patch.object(city,'save',side_effect=lambda k,v:saves.update({k:v})),patch.object(city,'ingest',side_effect=ingest),patch.object(city,'enrich',side_effect=lambda x:x),patch.object(city,'enrich_directory',side_effect=AssertionError('directory called')),patch('requests.sessions.Session.request',side_effect=AssertionError('unexpected network')):
   city.main('events')
  self.assertEqual(seen,['city']);self.assertEqual(set(saves),{'events','source-report'})

 def senior_scope(self,scope):
  previous={'id':'untouched-course','source_name':seniors.SOURCES['matnas-classes'][0],'checked_at':'2026-01-01','term_end':'2099-01-01'}
  event_card={'id':'untouched-event-card','source_name':seniors.SOURCES['matnas-events'][0],'checked_at':'2026-02-01','term_end':'2099-01-01'}
  values={'events':{'events':[]},'senior-catalog':{'checked_at':'2026-02-01','items':[previous,event_card],'sources':[]},'sources':{'sources':[]}}
  fetched=[];saved={}
  def page(k):fetched.append(k);return BeautifulSoup('<html></html>','html.parser')
  with tempfile.TemporaryDirectory() as d:
   Path(d,'senior-catalog.json').write_text('{}')
   with patch.object(seniors,'D',Path(d)),patch.object(seniors,'page',side_effect=page),patch.object(city,'read',side_effect=lambda k:copy.deepcopy(values[k])),patch.object(city,'save',side_effect=lambda k,v:saved.update({k:v})),patch('requests.sessions.Session.request',side_effect=AssertionError('unexpected network')):
    seniors.main(scope)
  return fetched,saved,previous,event_card

 def test_weekly_senior_events_preserve_unscanned_classes_and_their_original_dates(self):
  fetched,saved,previous,_=self.senior_scope('events')
  self.assertEqual(set(fetched),{'matnas-events','municipal24'})
  self.assertIn(previous,saved['senior-catalog']['items'])
  self.assertEqual(saved['senior-catalog']['checked_at'],'2026-02-01')
  self.assertEqual(saved['senior-catalog']['refresh_scope'],'events')

 def test_quarterly_catalog_does_not_scan_or_save_dated_events(self):
  fetched,saved,_,event_card=self.senior_scope('catalog')
  self.assertNotIn('matnas-events',fetched);self.assertNotIn('municipal24',fetched)
  self.assertNotIn('events',saved)
  self.assertIn(event_card,saved['senior-catalog']['items'])

 def test_unknown_scope_fails_before_source_read(self):
  with patch.object(city,'read',side_effect=AssertionError('read before scope validation')):
   with self.assertRaises(ValueError):city.main('unknown')
  with self.assertRaises(ValueError):seniors.scoped_sources('unknown')

if __name__=='__main__':unittest.main()
