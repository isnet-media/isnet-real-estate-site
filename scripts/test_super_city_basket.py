"""Verify fixed basket source prices, unit compatibility and complete-only ranking."""
from pathlib import Path
from decimal import Decimal
import json
from build_super_city_basket import D,kg_unit,cents
bundle=json.loads((D/'data/city-basket.json').read_text());assert bundle['default_variant']=='family'
for key,data in bundle['variants'].items():
 assert key==data['variant_id'];assert len({p['id'] for p in data['products']})==len(data['products'])
 complete=[];shards={}
 for b in data['branches']:
  assert len(b['lines'])==len(data['products'])
  for item,line in zip(data['products'],b['lines']):
   assert item['id']==line['id'] and line['quantity']==item['quantity']
   if line['price_cents'] is None:assert line['line_total_cents'] is None;continue
   assert line['kind']=='רגיל' and line['source_type']=='official_file' and line['source_url'].startswith('https://')
   assert line['product_id'] in item.get('candidates',[item['id']])
   suffix=line['product_id'][-2:]
   if suffix not in shards:shards[suffix]=json.loads((D/'data/offers'/f'{suffix}.json').read_text())
   product=shards[suffix][line['product_id']]
   offers=[o for o in product['offers'] if o['branch_id']==b['id'] and o.get('kind')=='רגיל' and o.get('eligible_for_basket') and o.get('source_type')=='official_file']
   assert any(cents(o['price'])==line['price_cents'] for o in offers)
   assert line['line_total_cents']==cents(Decimal(line['price_cents'])/100*Decimal(str(item['quantity'])))
   if item['pricing_unit']=='kg':assert kg_unit(line['raw_unit']) and kg_unit(line['product_unit']) and cents(line['raw_price'])==line['price_cents']
   else:assert product['weighted']=='0' and product['calculation_unit']=='package'
  found=sum(l['price_cents'] is not None for l in b['lines']);assert found==b['found'];assert b['complete']==(found==len(data['products']))
  if b['complete']:
   assert b['total_cents']==sum(l['line_total_cents'] for l in b['lines']);complete.append(b)
  else:assert b['total_cents'] is None and b['id'] not in data['winner_ids'] and b['id'] not in data['most_expensive_ids']
 assert data['complete_branch_count']==len(complete) and data['ranking_available']==(len(complete)>=2)
 if data['ranking_available']:
  low=min(b['total_cents'] for b in complete);high=max(b['total_cents'] for b in complete)
  assert data['minimum_cents']==low and data['maximum_cents']==high and data['gap_cents']==high-low
  assert data['gap_percent_of_cheapest']==round((high-low)/low*100,2)
  assert set(data['winner_ids'])=={b['id'] for b in complete if b['total_cents']==low}
  assert set(data['most_expensive_ids'])=={b['id'] for b in complete if b['total_cents']==high}
  assert data['average_cents']==round(sum(b['total_cents'] for b in complete)/len(complete))
family=bundle['variants']['family'];assert family['target_budget_ils']==[600,700]
assert {'פירות','ירקות','עוף ודגים'}<={p.get('group') for p in family['products']}
assert sum('יכין' in p['name'] for p in family['products'])>=3
print('Verified both baskets: exact source prices, kg metadata, complete-only ranking, ties, mean and percentage gap')
