"""Publication checks for independent Rishon LeZion data, units, paths and shared UI."""
from pathlib import Path
import json,math,sys,importlib.util,argparse
from super_city_runtime import ROOT,load
D=ROOT/'SUPER.RISHON';data=D/'data'
cat=json.loads((data/'catalog.json').read_text());prices=json.loads((data/'prices.json').read_text());ids={b['id'] for b in cat['branches']}
assert cat['city']==prices['city']=='ראשון לציון'
assert len(ids)>=15 and all(b['city']=='ראשון לציון' for b in cat['branches'])
assert '7290696200003-023' in ids and '7290696200003-055' not in ids
products={}
for p in (data/'offers').glob('*.json'):products.update(json.loads(p.read_text()))
assert len(products)==cat['product_count']>10000
for p in products.values():
 assert p['offers'] and all(o['branch_id'] in ids and math.isfinite(o['price']) and o['price']>0 for o in p['offers'])
assert sum(len(p['offers']) for p in products.values())==cat['offer_count']
basket=json.loads((data/'city-basket.json').read_text())['variants']['family'];branches=basket['branches']
assert len(branches)==basket['complete_branch_count']==len(ids)
assert all(b['complete'] and b['total_cents']==sum(l['line_total_cents'] for l in b['lines']) for b in branches)
assert basket['gap_cents']==basket['maximum_cents']-basket['minimum_cents']
assert round(basket['gap_cents']/basket['minimum_cents']*100,2)==basket['gap_percent_of_cheapest']
for b in branches:
 for l in b['lines']:
  if l['id']=='7290003361441':assert l['total_grams']==3000
  if l['id']=='7290000104881':assert l['total_grams']==1600
  if l['id']=='7290000104201':assert l['total_grams']==1200
for p in D.rglob('*.html'):
 if 'assets' in p.relative_to(D).parts or p.name.startswith('qa-'):continue
 t=p.read_text();assert t.count('SUPER_SHELL_START')==1 and 'מחירי הסופר בראשון לציון' in t
 assert 'ashdod-analytics.js' not in t and 'ashdodnet.com' not in t
 assert 'super-rishon-logo.svg' in t and 'rishonet-publisher.svg' in t
for p in [D/'live.js',D/'assets/compare-page.js']:
 t=p.read_text();assert 'isnetRealBasket' not in t and 'isnetRishonBasket' in t
# Reuse the existing local-link audit without touching Ashdod's report.
spec=importlib.util.spec_from_file_location('city_audit',ROOT/'scripts/audit_super_site.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.SITE=D;m.D=data
parser=argparse.ArgumentParser(description='Validate Rishon LeZion supermarket pages and price-feed freshness')
parser.add_argument('--deployment-only', action='store_true', help='Warn about stale official prices during unrelated site deploys; supermarket refresh is still strict')
args=parser.parse_args()
r=m.audit()
assert not r['errors'], 'Rishon LeZion public site integrity failure'
if r['stale_branches']:
 msg=f"Rishon LeZion official supermarket prices have {len(r['stale_branches'])} stale branches; no claim of current full coverage"
 if not args.deployment_only:raise AssertionError(msg)
 print(f"::warning title=Rishon LeZion price freshness::{msg}; source dates retained in site-health.json.")
print('Rishon LeZion verified: registered physical branches, isolated offers and lists, complete equivalent basket, shared mobile shell, local links')
