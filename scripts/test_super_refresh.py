"""Regressions for cross-branch poisoning, zero prices and source rollback."""
import copy,gzip,json,tempfile
from pathlib import Path
from unittest.mock import patch
from datetime import datetime
import refresh_super_prices as r
import import_super_shufersal as boot
b={'id':'7290058173198-019','chain_id':'7290058173198','store_id':'019'}
xml=b'''<Root><ChainID>7290058173198</ChainID><StoreID>019</StoreID><Items><Item><ItemCode>14</ItemCode><ItemType>1</ItemType><ItemStatus>0</ItemStatus><ItemPrice>6.60</ItemPrice><bIsWeighted>0</bIsWeighted><ItemName>bread</ItemName></Item></Items></Root>'''
fresh=xml.replace(b'7290058173198',b'7290876100000').replace(b'<ItemCode>14',b'<ItemCode>7290004131074').replace(b'<ItemType>1',b'<ItemType>0')
assert '7290004131074' in r.parse_price(fresh,dict(b,chain_id='7290876100000'))
assert r.parse_price(xml.replace(b'ChainID',b'ChainId').replace(b'StoreID',b'StoreId'),b)
p=r.parse_price(xml,b);assert p['7290058173198:14']['offers'][0]['price']==6.6
assert r.parse_price(xml.replace(b'6.60',b'0'),b)['7290058173198:14'] is None
try:r.parse_price(xml.replace(b'<StoreID>019',b'<StoreID>020'),b);raise AssertionError('Wrong branch accepted')
except ValueError:pass
for name,stamp in [('PriceFull7290785400000-022-202610210010.gz','20261021001000'),('Price7290058173198-000-019-20261021-040416.GZ','20261021040416')]:assert r.filetime(name)==stamp
# A newer delta must never be replaced by an older full file.
branch=dict(b,chain='test',file_date='2026-10-21',files_applied=['Price7290058173198-000-019-20261021-160000.gz'])
entries=[{'name':'PriceFull7290058173198-000-019-20261021-040000.gz','url':'https://example.invalid'}]
with tempfile.TemporaryDirectory() as tmp,patch.object(r,'listing',return_value=(None,entries)):
 old,new,report=r.refresh_branch(branch,Path(tmp),datetime(2026,10,21,20,tzinfo=r.TZ));assert new is None and old==branch and 'roll back' in report['error']
# Bootstrap must be a no-op when a newer branch snapshot already exists.
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);data=root/'data';data.mkdir();snap=root/'scripts/super-ashdod';snap.mkdir(parents=True)
 newer=dict(b,file_date='2026-10-22',retrieved_at='2026-10-22T08:00:00+03:00')
 snapshot={'retrieved_at':'2026-10-21T08:00:00+03:00','branches':[dict(b,file_date='2026-10-21',retrieved_at='2026-10-21T08:00:00+03:00')],'products':[]}
 (data/'catalog.json').write_text(json.dumps({'branches':[newer]}));before=(data/'catalog.json').read_bytes();(snap/'shufersal-20261021.json.gz').write_bytes(gzip.compress(json.dumps(snapshot).encode()))
 with patch.object(boot,'ROOT',root),patch.object(boot,'D',data):boot.build()
 assert (data/'catalog.json').read_bytes()==before
print('Passed: branch identity, local codes, publisher status, zero-price removal, delta rollback and bootstrap freshness')

# End-to-end partial refresh: recovery must preserve ALL untouched old products.
import build_super_deals
with tempfile.TemporaryDirectory() as tmp:
 data=Path(tmp)/'data';(data/'offers').mkdir(parents=True)
 bad=dict(b,chain='unavailable',file_date='2026-10-20',name='old',address='A')
 good=dict(b,id='7290058173198-020',store_id='020',chain='available',file_date='2026-10-21',name='new',address='B')
 def product(pid,bid,price):
  return {'id':pid,'name':'food','quantity':'1','unit_quantity':'unit','weighted':'0','calculation_unit':'package','offers':[{'branch_id':bid,'price':price,'eligible_for_basket':True}]}
 old=product('7290000000011',bad['id'],12);new=product('7290000000028',good['id'],8)
 (data/'offers/11.json').write_text(json.dumps({old['id']:old}));(data/'catalog.json').write_text(json.dumps({'branches':[bad,good],'retrieved_at':'2026-10-21T08:00:00+03:00'}));(data/'prices.json').write_text('{}');(data/'deals.json').write_text('{}')
 def fake(branch,raw_dir,now):
  failed=branch['id']==bad['id']
  return branch,None if failed else {new['id']:new},{'branch_id':branch['id'],'status':'retained_previous' if failed else 'updated','error':'timeout' if failed else None}
 with patch.object(r,'D',data),patch.object(r,'refresh_branch',side_effect=fake),patch.object(build_super_deals,'build',return_value={}):report=r.run(Path(tmp)/'raw')
 actual=json.loads((data/'offers/11.json').read_text());assert actual[old['id']]==old
 actual_catalog=json.loads((data/'catalog.json').read_text());assert actual_catalog['product_count']==2 and actual_catalog['branches'][0]['file_date']=='2026-10-20'
 assert report['updated_count']==1 and not report['all_sources_updated'] and report['branches'][0]['attempts']==2
print('Passed: partial recovery preserves previous branch prices, products and true source dates')

# Two independent failed sources must recover concurrently, once each.
from threading import Barrier
barrier=Barrier(2,timeout=3)
results=[({'id':str(i)},None,{'status':'retained_previous','error':'first timeout'}) for i in range(2)]
def recovered(branch,raw_dir,now):
 barrier.wait()
 return branch,{'verified':True},{'status':'updated'}
with patch.object(r,'refresh_branch',side_effect=recovered) as retry:
 r.recover_branches(results,Path('/unused'))
 assert retry.call_count==2
assert all(x[2]['attempts']==2 and x[2]['first_error']=='first timeout' for x in results)
print('Passed: independent source recovery runs concurrently with one retry per branch')

# A shard whose last product is removed cannot resurrect stale offers on the next run.
with tempfile.TemporaryDirectory() as tmp:
 data=Path(tmp)/'data';(data/'offers').mkdir(parents=True)
 branch=dict(b,chain='available',file_date='2026-10-21')
 old=product('7290000000011',branch['id'],12);new=product('7290000000028',branch['id'],8)
 (data/'offers/11.json').write_text(json.dumps({old['id']:old}))
 (data/'catalog.json').write_text(json.dumps({'branches':[branch],'retrieved_at':'2026-10-21T08:00:00+03:00'}))
 (data/'prices.json').write_text('{}');(data/'deals.json').write_text('{}')
 def replace(branch,raw_dir,now):return branch,{new['id']:new},{'branch_id':branch['id'],'status':'updated'}
 with patch.object(r,'D',data),patch.object(r,'refresh_branch',side_effect=replace),patch.object(build_super_deals,'build',return_value={}):r.run(Path(tmp)/'raw')
 assert not (data/'offers/11.json').exists()
 assert json.loads((data/'catalog.json').read_text())['product_count']==1
print('Passed: deleted product shards cannot resurrect removed branch offers')
