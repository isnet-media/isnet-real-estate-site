"""Publication checks for recipe completeness, budget arithmetic and local assets."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'SUPER.ASHDOD';D=SITE/'recipes'
data=json.loads((D/'recipes.json').read_text());rs=data['recipes'];assert len(rs)==12 and len({r['slug'] for r in rs})==12
class Links(HTMLParser):
 def __init__(self):super().__init__();self.refs=[];self.h1=0;self.imgs=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='h1':self.h1+=1
  if tag=='img':assert a.get('alt');self.imgs+=1
  for k in ('href','src'):
   if a.get(k):self.refs.append(a[k])
for r in rs:
 assert 40<=r['total']<=60
 assert abs(r['total']-sum(x['cost'] for x in r['ingredients']))<.001
 assert r['total']/5>=8 and r['total']/4<=15
 assert len(r['steps'])>=4 and len(r['ingredients'])>=8
 assert r['saving'] and r['plate']
 if r['category']=='עוף':assert '74' in r['safety']
 if r['category']=='דגים':assert '63' in r['safety']
 assert (D/'images'/f"{r['slug']}.webp").is_file()
for p in [D/'index.html']+[D/r['slug']/'index.html' for r in rs]:
 h=Links();h.feed(p.read_text());assert h.h1==1,(p,h.h1)
 for ref in h.refs:
  u=urlsplit(ref)
  if u.scheme or u.netloc or not u.path:continue
  target=(p.parent/unquote(u.path)).resolve()
  if target.is_dir():target=target/'index.html'
  assert target.is_file(),(p,ref)
main=(SITE/'index.html').read_text();assert 'href="recipes/"' in main and "location.href='recipes/'" in main
legacy=(ROOT/'.github/workflows/import-super-ashdod.yml').read_text();assert '  push:' not in legacy
print('Verified 12 complete recipe pages, images, local links, cost arithmetic and 8–15 ILS per-person range for 4–5 diners')
