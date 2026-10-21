"""Idempotently merge an attributed official Shufersal snapshot at build time."""
from pathlib import Path
import gzip,json,collections
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'SUPER.ASHDOD/data'
def write(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':'))+'\n')
def build():
 snapshot=json.loads(gzip.decompress((ROOT/'scripts/super-ashdod/shufersal-20261021.json.gz').read_bytes()))
 catalog=json.loads((D/'catalog.json').read_text())
 existing={b['id']:b for b in catalog['branches']}
 def newer(b):
  old=existing.get(b['id'])
  return not old or (old.get('file_date',''),old.get('retrieved_at','')) < (b['file_date'],b['retrieved_at'])
 snapshot['branches']=[b for b in snapshot['branches'] if newer(b)]
 if not snapshot['branches']:
  print('Shufersal bootstrap skipped: current data is at least as recent');return
 bids={b['id'] for b in snapshot['branches']};products={}
 for f in (D/'offers').glob('*.json'):products.update(json.loads(f.read_text()))
 for p in products.values():p['offers']=[o for o in p['offers'] if o['branch_id'] not in bids]
 for original in snapshot['products']:
  p=dict(original,offers=[o for o in original['offers'] if o['branch_id'] in bids])
  if not p['offers']:continue
  if p['id'] not in products:products[p['id']]=p
  else:products[p['id']]['offers'].extend(p['offers'])
 products={k:p for k,p in products.items() if p['offers']}
 shards=collections.defaultdict(dict)
 for pid,p in products.items():shards[pid[-2:]][pid]=p
 for key,values in shards.items():write(D/'offers'/f'{key}.json',values)
 catalog=json.loads((D/'catalog.json').read_text());catalog['branches']=[b for b in catalog['branches'] if b['id'] not in bids]+snapshot['branches']
 catalog['retrieved_at']=max(catalog.get('retrieved_at',''),snapshot['retrieved_at']);catalog['product_count']=len(products);catalog['offer_count']=sum(len(p['offers']) for p in products.values())
 catalog['rows']=[[pid,p['name'],p['quantity'],p['unit_quantity'],p['weighted'],p.get('manufacturer',''),min(o['price'] for o in p['offers']),len(p['offers']),[o['branch_id'] for o in p['offers']],p['calculation_unit']] for pid,p in products.items()]
 write(D/'catalog.json',catalog)
 prices=json.loads((D/'prices.json').read_text())
 for k in ('branches','retrieved_at','product_count','offer_count'):prices[k]=catalog[k]
 prices['branch_count']=len(catalog['branches']);prices['chains']=dict(collections.Counter(b['chain'] for b in catalog['branches']));write(D/'prices.json',prices)
 status=json.loads((D/'source-status.json').read_text());status['connected']['שופרסל']=sum(b['chain']=='שופרסל' for b in catalog['branches']);status['pending']=[p for p in status['pending'] if p['chain']!='שופרסל'];write(D/'source-status.json',status)
 print('Imported Shufersal:',len(bids),'branches;',sum(len(p['offers']) for p in snapshot['products']),'price observations')
if __name__=='__main__':build()
