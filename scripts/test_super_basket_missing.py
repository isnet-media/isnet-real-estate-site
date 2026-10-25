"""A missing reviewed product changes every branch's basket identically."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import build_super_city_basket as b
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
 assert len(result['branches'])==2 and result['complete_branch_count']==2
 assert [p['id'] for p in result['products']]==['11','22']
 assert result['omitted_products'][0]['id']=='33'
 assert all([l['id'] for l in x['lines']]==['11','22'] and x['total_cents']==400 for x in result['branches'])
 assert result['minimum_cents']==result['maximum_cents']==400
print('Passed: missing product is omitted equally, all branches retained, exact totals and ties preserved')
