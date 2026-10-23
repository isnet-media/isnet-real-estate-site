"""Publication checks for independent Yavne data, units, paths and shared UI."""
from pathlib import Path
import json,math,sys,importlib.util,argparse
from super_city_runtime import ROOT,load
D=ROOT/'SUPER.YAVNE';data=D/'data'
cat=json.loads((data/'catalog.json').read_text());prices=json.loads((data/'prices.json').read_text());ids={b['id'] for b in cat['branches']}
assert cat['city']==prices['city']=='יבנה'
assert len(ids)==7 and all(b['city']=='יבנה' for b in cat['branches'])
assert '7290696200003-056' in ids and '7290696200003-001' not in ids
products={}
for p in (data/'offers').glob('*.json'):products.update(json.loads(p.read_text()))
assert len(products)==cat['product_count']>10000
for p in products.values():
 assert p['offers'] and all(o['branch_id'] in ids and math.isfinite(o['price']) and o['price']>0 for o in p['offers'])
assert sum(len(p['offers']) for p in products.values())==cat['offer_count']
basket=json.loads((data/'city-basket.json').read_text())['variants']['family'];branches=basket['branches']
assert len(branches)==basket['complete_branch_count']==7
assert all(b['complete'] and b['total_cents']==sum(l['line_total_cents'] for l in b['lines']) for b in branches)
assert basket['gap_cents']==basket['maximum_cents']-basket['minimum_cents']
assert round(basket['gap_cents']/basket['minimum_cents']*100,2)==basket['gap_percent_of_cheapest']
for b in branches:
 for l in b['lines']:
  if l['id']=='7290019322184':assert l['total_grams']==2000
for p in D.rglob('*.html'):
 if 'assets' in p.relative_to(D).parts:continue
 t=p.read_text();assert t.count('SUPER_SHELL_START')==1 and 'מחירי הסופר ביבנה' in t
 assert 'ashdod-analytics.js' not in t and 'ashdodnet.com' not in t
 assert 'super-yavne-logo.svg' in t and 'yavnenet-publisher.svg' in t
for p in [D/'live.js',D/'assets/compare-page.js']:
 t=p.read_text();assert 'isnetRealBasket' not in t and 'isnetYavneBasket' in t
# Reuse the existing local-link audit without touching Ashdod's report.
spec=importlib.util.spec_from_file_location('city_audit',ROOT/'scripts/audit_super_site.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.SITE=D;m.D=data
parser=argparse.ArgumentParser(description='Validate Yavne supermarket site and price-source freshness')
parser.add_argument('--deployment-only',action='store_true',help='Allow the unrelated website deployment to continue with an explicit freshness warning; dedicated refresh remains strict')
args=parser.parse_args()
r=m.audit()
assert not r['errors'], 'Yavne supermarket has broken public pages or links'
if r['stale_branches']:
 msg=f"Yavne supermarket has {len(r['stale_branches'])} stale official price sources; price coverage is not fresh"
 if not args.deployment_only:raise AssertionError(msg)
 print(f"::warning title=Yavne price freshness::{msg}. Site health report retains full source dates; events deployment is not blocked.")
print('Yavne verified: 7 branches, isolated offers and lists, complete equivalent basket, shared mobile shell, local links')
