"""TLV snapshot isolation and safe bootstrap regressions; no source requests."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import copy,json
import refresh_tlv_super_prices as t
branches=t.reviewed()
assert len(branches)==19 and len({b['id'] for b in branches})==19
assert all(b['city']=='תל אביב' for b in branches)
assert t.collector().D==t.SITE/'data'
with TemporaryDirectory() as td:
 d=Path(td)/'data';(d/'offers').mkdir(parents=True)
 product={'id':'123400','offers':[{'branch_id':b['id'],'source_type':'official_file','price':5} for b in branches]}
 cat={'city':'תל אביב-יפו','branches':branches,'product_count':1,'offer_count':19,'rows':[['123400']]}
 def write(c,p):
  (d/'catalog.json').write_text(json.dumps(c),encoding='utf-8')
  (d/'offers/00.json').write_text(json.dumps({'123400':p}),encoding='utf-8')
 write(cat,product);assert t.validate(d)['offer_count']==19
 for kind in ['other_city','unregistered','negative_price','count']:
  c=copy.deepcopy(cat);p=copy.deepcopy(product)
  if kind=='other_city':c['city']='אשדוד'
  if kind=='unregistered':p['offers'][0]['branch_id']='other'
  if kind=='negative_price':p['offers'][0]['price']=-1
  if kind=='count':c['offer_count']=20
  write(c,p)
  try:t.validate(d)
  except ValueError:pass
  else:raise AssertionError(kind)
 write(cat,product)
 # Existing verified data is never replaced by re-downloading the original snapshot.
 with patch.object(t,'SITE',d.parent),patch.object(t.requests,'get',side_effect=AssertionError('Unexpected network')):
  assert t.bootstrap()['offer_count']==19
print('PASS: reviewed TLV identities, isolated shared adapter, city/offer/count guards')
