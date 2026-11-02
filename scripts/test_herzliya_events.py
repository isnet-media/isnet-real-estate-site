"""Release checks for city isolation, sourced sessions, shared layout and local media."""
import json,re,unittest
from pathlib import Path
from datetime import date
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];C=ROOT/'events-preview/herzliya'
def read(n):return json.loads((C/'data'/(n+'.json')).read_text())
class EditionTests(unittest.TestCase):
 def test_city_occurrences(self):
  events=read('events')['events'];public=read('events-public')['events']
  self.assertGreaterEqual(len(events),20);self.assertEqual({e['id'] for e in events},{e['id'] for e in public})
  self.assertTrue(all(e['city']=='הרצליה' and e['source_url'].startswith('https://') for e in events))
  self.assertEqual(len(events),len({(e['title'],e['start_date'],e['start_time']) for e in events}))
  for e in events:
   date.fromisoformat(e['start_date']);self.assertRegex(e['start_time'],r'^\d{2}:\d{2}$')
 def test_source_photos(self):
  events=read('events')['events'];photos=[e for e in events if e.get('image_role')=='official_promotional'];self.assertGreater(len(photos),20)
  for e in photos:self.assertTrue((C/e['image']).is_file(),e['image']);self.assertTrue(e.get('image_origin_url'));self.assertTrue(e['image_credit'])
 def test_local_films(self):
  movies=read('cinema')['movies'];self.assertGreater(len(movies),0)
  raw={(e['start_date'],e['start_time'],e['booking_url']) for e in read('events')['events'] if e['category']=='cinema'}
  for m in movies:
   self.assertTrue(m['synopsis']);self.assertTrue(m['venues'])
   for v in m['venues']:
    self.assertIn('הרצליה',v['name'])
    for s in v['sessions']:self.assertIn((s['date'],s['time'],s['booking_url']),raw)
 def test_shared_shell_and_routes(self):
  page=(C/'index.html').read_text();self.assertNotIn('http-equiv="refresh"',page);self.assertIn('ISNET shared layout',page);self.assertIn('herzliya-events.js',page);self.assertIn('מה עושים בהרצליה',page)
  for name in ['index.html','cinema.html','restaurants.html','category.html','event.html','movie.html','seniors.html','sources.html','health.html']:
   p=C/name;self.assertTrue(p.is_file());s=BeautifulSoup(p.read_text(),'html.parser')
   for tag in s.select('script[src],link[rel="stylesheet"]'):
    u=(tag.get('src') or tag.get('href')).split('?')[0]
    if not u.startswith(('https:','http:','//')):self.assertTrue(((ROOT/u.lstrip('/')) if u.startswith('/') else p.parent/u).is_file(),name+': '+u)
 def test_local_directories(self):
  food=read('restaurants')['items'];self.assertGreaterEqual(len(food),6)
  self.assertTrue(all(x['city']=='הרצליה' for x in food))
  ids={x['id'] for x in read('sources')['sources']};self.assertTrue({'friends','ale','sirkin','cinematheque','rest','easy','rol'}<=ids)
if __name__=='__main__':unittest.main()
