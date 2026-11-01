"""Content and generated-page safeguards for the health-only Herzliya edition."""
import json,re,sys,unittest
from pathlib import Path
from urllib.parse import urlparse
from html.parser import HTMLParser
from build_herzliya_health import build
from build_holon_health import build as build_holon
ROOT=Path(__file__).resolve().parents[1];CITY=ROOT/'events-preview/herzliya'
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if a.get('href'):self.links.append(a['href'])
class HealthTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=json.loads((CITY/'data/health.json').read_text());cls.page=(CITY/'health.html').read_text();cls.sections={s['id']:s for s in cls.data['sections']}
 def test_local_scope_and_phone_transcription(self):
  self.assertEqual(self.data['city'],'herzliya');self.assertFalse(self.data['live_open_status']);self.assertNotIn('חולון',self.page)
  ph=self.sections['pharmacies']['items'];self.assertEqual(len(ph),7);self.assertEqual(len({x['phone'] for x in ph}),7)
  self.assertTrue(all('הרצליה' in x['address'] for x in ph))
  self.assertEqual({x['phone'] for x in ph},{'0778880010','0778880260','0778880870','0778881420','0778883140','0778881100','099558157'})
  self.assertEqual({x['name']:x['phone'] for x in self.sections['hmo']['items']},{'כללית':'*2700','מכבי':'*3555','מאוחדת':'*3833','לאומית':'*507'})
 def test_sources_and_opening_claims(self):
  allowed={'shop.super-pharm.co.il','serguide.maccabi4u.co.il','www.clalit.co.il','www.maccabi4u.co.il','www.herzliya.muni.il','www.meuhedet.co.il','leumit.co.il','www.gov.il'}
  for s in self.data['sections']:
   for x in s['items']:
    u=urlparse(x['source_url']);self.assertEqual(u.scheme,'https');self.assertIn(u.hostname,allowed);self.assertTrue(x['source_name']);self.assertRegex(x['phone'],r'^(?:0\d{8,9}|\*\d{3,4})$')
  self.assertIn('אין כאן חיווי פתיחה בזמן אמת',self.page);self.assertNotIn('פתוח עכשיו',self.page);self.assertIn('מחוץ להרצליה',self.page)
 def test_links_and_build(self):
  p=Links();p.feed(self.page);self.assertIn('tel:101',p.links);self.assertIn('https://www.mdais.org/101',p.links)
  self.assertLess(self.page.index('charset="utf-8"'),1024)
  for link in p.links:
   if not link.startswith(('https:','tel:','#')):self.assertTrue((CITY/link.split('?')[0]).is_file(),link)
  self.assertFalse(build(check=True));self.assertFalse(build_holon(check=True),'Holon must keep its existing page')
if __name__=='__main__':unittest.main()
