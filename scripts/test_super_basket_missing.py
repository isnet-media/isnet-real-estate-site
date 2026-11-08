"""Missing prices must never shrink the reviewed basket or create a winner."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import build_super_city_basket as b
from super_family_checks import verify_fixed_family
import copy
with TemporaryDirectory() as tmp:
 d=Path(tmp);(d/'data/offers').mkdir(parents=True);(d/'data/source-status.json').write_text('{"pending":[]}')
 branches=[{'id':x,'chain':x,'name':x} for x in ('a','b')]
 products={}
 for pid in ('11','22','33'):
  products[pid]={'id':pid,'name':pid,'weighted':'0','calculation_unit':'package','offers':[{'branch_id':x,'price':2,'source_type':'official_file','kind':'רגיל','eligible_for_basket':True,'calculation_unit':'package'} for x in ('a','b') if not(pid=='33' and x=='b')]}
 for pid,p in products.items():(d/'data/offers'/f'{pid}.json').write_text(json.dumps({pid:p}))
 cat={'branches':branches,'rows':[],'city':'test','retrieved_at':'2026-10-25T06:00:00+02:00'}
 definition=[{'id':pid,'name':pid,'quantity':1} for pid in products]
 with patch.object(b,'D',d):result=b.build_variant(definition,cat,'family')
 assert len(result['branches'])==2 and result['complete_branch_count']==1
 assert [p['id'] for p in result['products']]==['11','22','33'] and not result['omitted_products']
 assert all([l['id'] for l in x['lines']]==['11','22','33'] for x in result['branches'])
 by={x['id']:x for x in result['branches']}
 assert by['a']['total_cents']==600 and by['b']['total_cents'] is None
 assert by['b']['lines'][-1]['price_cents'] is None
 assert not result['ranking_available'] and result['winner_ids']==result['most_expensive_ids']==[]
 assert result['minimum_cents']==result['maximum_cents']==None
 verify_fixed_family(result,definition,{'a','b'})
 for mutate in [lambda x:x['products'].pop(),lambda x:x['winner_ids'].append('b')]:
  bad=copy.deepcopy(result);mutate(bad)
  try:verify_fixed_family(bad,definition,{'a','b'})
  except AssertionError:pass
  else:raise AssertionError('Publication guard accepted a shrinking basket or partial winner')
 products['33']['offers']=[];(d/'data/offers/33.json').write_text(json.dumps({'33':products['33']}))
 with patch.object(b,'D',d):empty=b.build_variant(definition,cat,'family')
 assert len(empty['products'])==3 and empty['complete_branch_count']==0 and empty['average_cents'] is None
 assert not empty['ranking_available'] and all(x['total_cents'] is None for x in empty['branches'])
 verify_fixed_family(empty,definition,{'a','b'})
print('Passed: fixed products and quantities, null missing prices, partial branches excluded, zero/one complete branch has no ranking')
