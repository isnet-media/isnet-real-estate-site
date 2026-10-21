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
