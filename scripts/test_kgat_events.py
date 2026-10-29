"""Launch safety: city provenance, complete occurrences, local media and links."""
import json,re
from pathlib import Path
from bs4 import BeautifulSoup
import sync_kgat_events as intake
R=Path(__file__).resolve().parents[1];C=R/'events-preview/kiryat-gat'
# A national board cannot turn a different city into a local occurrence.
soup=BeautifulSoup('<script type="application/ld+json">'+json.dumps({'@type':'Event','name':'מופע בעיר אחרת','startDate':'2027-01-01T20:00:00+02:00','location':{'name':'אולם באשדוד'},'url':'https://example.com/event'})+'</script>','html.parser')
assert intake.rows(soup,{'name':'national','url':'https://example.com/','parser':'generic','venue':'קריית גת','source_type':'secondary'})==[]
d=json.loads((C/'data/events.json').read_text());assert len(d['events'])>=30
ids=set();keys=set()
for e in d['events']:
 assert e['event_id'] not in ids;ids.add(e['event_id'])
 assert re.fullmatch(r'\d{4}-\d{2}-\d{2}',e['start_date']) and re.fullmatch(r'\d{2}:\d{2}',e['start_time'])
 assert e['city']=='קריית גת' and e['title'] and e['venue'] and e.get('description')
 assert e.get('sources') and not any(x in e['venue'] for x in ['אשדוד','יבנה','ראשון לציון'])
 k=(e['title'],e['start_date'],e['start_time'],e['venue']);assert k not in keys;keys.add(k)
 if e.get('image_publishable'):
  assert e['image_verified'] and e['image_credit'] and e['image_source']
  assert (C/e['image_url']).is_file()
for file in C.glob('*.html'):
 assert 'meusharim-ashdod' not in file.read_text(),file.name
 s=BeautifulSoup(file.read_text(),'html.parser')
 for tag in s.select('script[src],link[rel=stylesheet],img[src]'):
  u=tag.get('src') or tag.get('href');u=u.split('?',1)[0]
  if not u or u.startswith(('http:','https:','data:')):continue
  p=R/u.lstrip('/') if u.startswith('/') else file.parent/u
  assert p.is_file(),(file.name,u)
assert 'const places=[{"id":"kgat-' in (C/'restaurants.js').read_text()
assert 'kgatnet.co.il' in (C/'index.html').read_text()
assert 'kiryat-gat' in (R/'assets/isnet-top-navigation.js').read_text()
print('Kiryat Gat safety checks passed:',len(ids),'events')
