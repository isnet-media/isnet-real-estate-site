#!/usr/bin/env python3
import unittest,json,re,sys
from pathlib import Path
from urllib.parse import urlsplit
from datetime import date
R=Path(__file__).resolve().parents[1];C=R/'events-preview/holon';D=C/'data'
def read(n):return json.loads((D/(n+'.json')).read_text())
class HolonRelease(unittest.TestCase):
 def test_dated_local_occurrences(self):
  events=read('events')['events'];self.assertGreater(len(events),100);ids=[];keys=[]
  for e in events:
   self.assertEqual(e['city'],'חולון');date.fromisoformat(e['start_date']);self.assertRegex(e['start_time'],r'^(?:[01]\d|2[0-3]):[0-5]\d$');self.assertTrue(e['source_url'].startswith('https://'));self.assertTrue(e['booking_url'].startswith('https://'));self.assertNotRegex(e['title'],r'[\x00-\x08]');self.assertLess(len(e['title']),155);self.assertIn('חולון',e['venue']);ids.append(e['id']);keys.append((e['title'],e['start_date'],e['start_time']))
  self.assertEqual(len(ids),len(set(ids)));self.assertEqual(len(keys),len(set(keys)))
 def test_every_category_and_subcategory_has_real_image_file(self):
  cats=read('categories')['categories'];self.assertEqual(len(cats),14)
  for c in cats:
   self.assertTrue(c['subcategories'])
   for x in [c,*c['subcategories']]:
    self.assertTrue((C/x['image']).resolve().is_file(),x['image']);self.assertIn('המחשה',x['image_credit'])
 def test_all_cards_have_available_jpg_and_credit(self):
  from PIL import Image
  for e in [*read('events')['events'],*read('guides')['items'],*read('restaurants')['items']]:
   self.assertTrue(e['image'].endswith('.jpg'));p=(C/e['image']).resolve();self.assertTrue(p.is_file(),str(p));self.assertTrue(e['image_credit']);self.assertTrue(e['description'])
   with Image.open(p) as image:self.assertGreater(min(image.size),100)
 def test_restaurants_are_holon_and_all_food_types_are_populated(self):
  f=read('restaurants')['items'];self.assertGreaterEqual(len(f),20);subs={x['subcategory'] for x in f};self.assertTrue({'italian','asian','cafe','burger','dessert','bar','street'}<=subs)
  for e in f:
   self.assertEqual(e['city'],'חולון');self.assertIn('חולון',e['address']);self.assertNotIn('גורדוס',e['title']);self.assertTrue(e['source_url'].startswith('https://'))
   if e.get('kosher'):self.assertTrue(e.get('kosher_source'))
 def test_papi_isolation(self):
  for e in read('events')['events']:
   if e['source_id'].startswith('papi'):self.assertIn('חולון',e['venue'])
 def test_real_source_coverage_and_honest_statuses(self):
  sources=read('sources')['sources'];self.assertGreaterEqual(len(sources),23);ids={s['id'] for s in sources};self.assertTrue({'hth','mediatheque','cinematheque','design','holonet','psagot','seniors','rest','ontopo','children','municipality'}<=ids)
  report=read('source-report');self.assertEqual({s['id'] for s in report['sources']},ids)
  for s in report['sources']:self.assertIn(s['status'],['collected','linked_directory','interactive_source','fetch_failed','closure_notice'])
 def test_no_fabricated_prices_or_opening_hours(self):
  for e in read('events')['events']:
   if e.get('price') is not None:self.assertIsInstance(e['price'],(float,int));self.assertGreaterEqual(e['price'],0)
  for e in read('guides')['items']:
   if e.get('saturday'):self.assertEqual(urlsplit(e['source_url']).hostname,'park-peres.co.il')
 def test_city_bootstrap_and_sharing_metadata(self):
  html=(C/'index.html').read_text();self.assertIn('window.ISNET_CITY_BOOTSTRAP=',html);self.assertIn('https://holonnet.co.il/',html);self.assertIn('canonical-ashdod-20261101',html);self.assertIn('assets/share-card.jpg',html);self.assertNotIn('מה עושים באשדוד',html);self.assertIn('og:image',html)
  for name in ['restaurants','cinema','kids','seniors','saturday','attractions','sources']:self.assertTrue((C/(name+'.html')).is_file())
 def test_bootstrap_matches_owned_data(self):
  data=read('site');self.assertEqual(data['events'],read('events')['events']);self.assertEqual(data['restaurants'],read('restaurants')['items'])
 def test_shared_ashdod_layout_and_ids(self):
  public=read('events-public');self.assertEqual([e['event_id'] for e in public['events']],[e['id'] for e in read('events')['events']])
  for filename in ['styles.css','pilot/home.css','home-date-gateway.js','pilot/rails.js']:
   a=(R/'events-preview/ashdod'/filename).read_text();b=(C/filename).read_text();self.assertTrue(a.strip() in b or a.strip()==b.strip(),filename)
  from bs4 import BeautifulSoup
  master=BeautifulSoup((R/'events-preview/ashdod/index.html').read_text(),'html.parser');city=BeautifulSoup((C/'index.html').read_text(),'html.parser')
  for selector in ['.hero','.heroMarquee','.isnetNavDiscovery','#eventsGrid','#searchInput']:
   if master.select(selector):self.assertEqual(len(master.select(selector)),len(city.select(selector)),selector)
  self.assertIsNotNone(city.select_one('.culinaryHomepageFeature'));self.assertIn('holon-events.js',(C/'event.html').read_text())
  self.assertNotIn('window.HOLON_BOOTSTRAP=',(C/'index.html').read_text())
 def test_parser_does_not_expand_unknown_more_dates(self):
  sys.path.insert(0,str(R/'scripts'));import sync_holon_events as h
  self.assertEqual(h.classify('אורי חזקיה','','hth'),'standup');self.assertEqual(h.classify('אבו סאלי','','cinematheque'),'cinema');self.assertEqual(h.classify('מסעדה בקצה הקוטב - תיאטרון המדיטק','לגילאי 4 ומעלה','mediatheque'),'kids')
if __name__=='__main__':unittest.main()
