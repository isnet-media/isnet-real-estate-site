"""Content and link integrity checks for the Kiryat Gat board."""
import json,re,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'meusharim/kiryat-gat'
class CatalogueTests(unittest.TestCase):
 def test_records(self):
  rs=json.loads((D/'data/classes.json').read_text())['records']
  self.assertGreaterEqual(len(rs),100);self.assertEqual(len(rs),len({r['id'] for r in rs}))
  for r in rs:
   self.assertEqual(r['city'],'קריית גת');self.assertTrue(r['phone']);self.assertTrue(r['source_url'].startswith('https://'))
   self.assertEqual(r['status'],'requires_confirmation');self.assertNotEqual(r['price'],0)
   self.assertTrue(r['image_illustrative']);self.assertTrue(r['image_credit'])
   with Image.open(D/r['image']) as im:self.assertGreaterEqual(im.width,300)
   for schedule in r['schedule']:
    self.assertIn(schedule['day'],r['days'])
    a,b=re.split('[–-]',schedule['time']);self.assertLess(a.zfill(5),b.zfill(5))
   if r['source_kind']=='annual_booklet':self.assertIn('26_27',r['source_url']);self.assertIsNone(r['registration_url'])
  featured=json.loads((D/'data/featured.json').read_text())['items']
  self.assertEqual(len(featured),6);self.assertTrue(all(f['id'] in {r['id'] for r in rs} for f in featured))
  special=[r for r in rs if r['subtitle']=='חינוך מיוחד'];self.assertTrue(special);self.assertEqual(special[0]['days'],['שלישי'])
  self.assertFalse(any(r['schedule'] for r in rs if r['source_page'] in [26,30,36,37,49]))
 def test_assets(self):
  for p in D.glob('*.html'):
   s=p.read_text();self.assertNotRegex(s,'יבנה|אשדוד|yavne|ashdod');self.assertEqual(s.count('rel="canonical"'),1)
   for asset in re.findall(r'(?:href|src)="\./([^"?#]+)',s):self.assertTrue((D/asset).exists(),asset)
  self.assertIn('לבירור והרשמה בטלפון',(D/'course.js').read_text())
if __name__=='__main__':unittest.main()
