"""Publication checks for recipe completeness, budget arithmetic and local assets."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,statistics
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'SUPER.ASHDOD';D=SITE/'recipes'
data=json.loads((D/'recipes.json').read_text());rs=data['recipes'];assert len(rs)==18 and len({r['slug'] for r in rs})==18
class Links(HTMLParser):
 def __init__(self):super().__init__();self.refs=[];self.h1=0;self.imgs=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='h1':self.h1+=1
  if tag=='img':assert a.get('alt');self.imgs+=1
  for k in ('href','src'):
   if a.get(k):self.refs.append(a[k])
refs=json.loads((D/'price-reference.json').read_text())['references']
for ref in refs.values():
 bybranch={}
 for o in ref['offers']:
  assert o['price']>0 and o['price_file_url'].startswith('https://') and o['file_date']=='2026-10-21'
  bybranch.setdefault(o['branch_id'],[]).append(o['unit_price'])
 assert ref['branch_count']==len(bybranch)
 assert abs(ref['unit_price']-statistics.median(statistics.median(v) for v in bybranch.values()))<.00001
 assert ref['limited_coverage']==(len(bybranch)<3)
for ceiling,slugs in data['budget_collections'].items():
 assert 6<=len(slugs)<=8 and len(set(slugs))==len(slugs)
 assert all(next(r for r in rs if r['slug']==slug)['total']<=int(ceiling) for slug in slugs)
assert set().union(*map(set,data['budget_collections'].values()))=={r['slug'] for r in rs}
for r in rs:
 assert 0<r['total']<=100
 assert abs(r['total']-sum(x['cost'] for x in r['ingredients']))<.001
 for x in r['ingredients']:
  assert x['components']
  assert abs(x['cost']-round(sum(refs[c['ref']]['unit_price']*c['quantity'] for c in x['components']),2))<.001
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
print('Verified18 recipes, images, links, source medians, ingredient costs and6–8 meals per familybudget ceiling50/75/100 ILS')
