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
  self.assertTrue(all('חולון' not in e['venue'] and 'אשדוד' not in e['venue'] for e in events))
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
    if v['id']=='cinema-city':
     source=read('cinema-city-glilot');allowed={(s['date'],s['time'],s['booking_url']) for row in source['movies'] for s in row['sessions']}
     self.assertIn('גלילות',v['name']);self.assertTrue(v['nearby_city'])
    else:allowed=raw
    for s in v['sessions']:self.assertIn((s['date'],s['time'],s['booking_url']),allowed)
 def test_shared_shell_and_routes(self):
  page=(C/'index.html').read_text();self.assertNotIn('http-equiv="refresh"',page);self.assertIn('ISNET shared layout',page);self.assertIn('herzliya-events.js',page);self.assertIn('מה עושים בהרצליה',page)
  for name in ['index.html','cinema.html','restaurants.html','category.html','event.html','movie.html','seniors.html','sources.html','health.html']:
   p=C/name;self.assertTrue(p.is_file());s=BeautifulSoup(p.read_text(),'html.parser')
   for tag in s.select('script[src],link[rel="stylesheet"]'):
    u=(tag.get('src') or tag.get('href')).split('?')[0]
    if not u.startswith(('https:','http:','//')):self.assertTrue(((ROOT/u.lstrip('/')) if u.startswith('/') else p.parent/u).is_file(),name+': '+u)
 def test_reviewed_stage_productions_are_not_films(self):
  from herzliya_event_quality import reviewed,REVIEWED
  for (host,path),(category,subtype) in REVIEWED.items():
   e=dict(source_url='https://'+host+path+'/',category='cinema',start_date='2026-12-01',start_time='20:30',venue='אולם המקור')
   fixed=reviewed(e);self.assertEqual(fixed['category'],category)
   self.assertEqual((fixed['start_date'],fixed['start_time'],fixed['venue']),(e['start_date'],e['start_time'],e['venue']))
  film=dict(source_url='https://www.hcinema.org.il/movies/123',category='cinema',title='עפרה')
  self.assertEqual(reviewed(film),film)
  self.assertFalse(any(m['title'] in ['עפרה – תיאטרון העברי','זוגות בזיג זג – קומדיה בקצב גבוה','מעשה בחמישה בלונים'] for m in read('cinema')['movies']))
 def test_catalog_media_files_exist(self):
  for catalog,key in [('events','events'),('categories','categories'),('guides','items'),('restaurants','items')]:
   for row in read(catalog)[key]:
    image=row.get('image','')
    if image and not image.startswith(('https:','http:','data:')):
     self.assertTrue((C/image.split('?')[0]).is_file(),catalog+': '+image)
 def test_failed_senior_source_preserves_only_valid_last_known_records(self):
  from collect_herzliya_seniors import retain_unverified_catalog,SOURCES
  name=SOURCES['matnas-classes'][0]
  old=[dict(id='valid',source_name=name,checked_at='2026-11-01',term_end='2027-06-30'),dict(id='expired',source_name=name,checked_at='2026-11-01',term_end='2026-10-31')]
  reports=[dict(name=name,status='checked',checked_at='2026-11-02')]
  result=retain_unverified_catalog(old,[],reports,'2026-11-02')
  self.assertEqual([x['id'] for x in result],['valid']);self.assertEqual(result[0]['checked_at'],'2026-11-01')
  self.assertEqual(result[0]['last_refresh_status'],'unverified');self.assertEqual(reports[0]['retained_items'],1)
  fresh={**old[0],'checked_at':'2026-11-02'}
  self.assertEqual(retain_unverified_catalog(old,[fresh],reports,'2026-11-02'),[fresh])
 def test_direct_senior_catalog(self):
  catalog=read('senior-catalog');self.assertGreaterEqual(len(catalog['items']),100)
  self.assertEqual(len({x['id'] for x in catalog['items']}),len(catalog['items']))
  self.assertGreaterEqual(sum(x['source_name']=='חוגים לגיל השלישי במרכזים הקהילתיים' for x in catalog['items']),70)
  self.assertTrue(all(x['source_url'].startswith('https://') for x in catalog['items']))
  self.assertIn('senior-catalog.js',(C/'category.html').read_text())
  self.assertTrue(any(x['source_url'].startswith('https://www.nde.co.il/') for x in catalog['items']))
 def test_local_directories(self):
  food=read('restaurants')['items'];self.assertGreaterEqual(len(food),6)
  self.assertTrue(all(x['city']=='הרצליה' for x in food))
  ids={x['id'] for x in read('sources')['sources']};self.assertTrue({'friends','ale','sirkin','cinematheque','rest','easy','rol'}<=ids)
if __name__=='__main__':unittest.main()
