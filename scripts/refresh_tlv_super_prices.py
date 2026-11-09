"""TLV adapter for the established ISNET official-feed collector."""
from pathlib import Path
import argparse,json,math,re,shutil,tempfile
from concurrent.futures import ThreadPoolExecutor
import requests
from super_city_runtime import ROOT,load
SITE=ROOT/'SUPER.TLV'; REGISTRY=ROOT/'scripts/super-tlv/branch-registry.json'
def reviewed():
 branches=json.loads(REGISTRY.read_text(encoding='utf-8'))['branches']
 ids=[b['id'] for b in branches]
 if len(ids)!=len(set(ids)) or not branches:raise ValueError('Invalid TLV registry')
 if any(b.get('city') not in ('תל אביב','תל אביב-יפו') or not b.get('identity_source') or not b.get('source_url') for b in branches):raise ValueError('Unverified TLV branch')
 return branches
def collector():return load('refresh_super_prices','TLV')
def validate(data):
 cat=json.loads((data/'catalog.json').read_text(encoding='utf-8'))
 expected={b['id'] for b in reviewed()}
 if cat.get('city') not in ('תל אביב','תל אביב-יפו') or {b['id'] for b in cat['branches']}!=expected:raise ValueError('Cross-city or unregistered branches')
 if any(b.get('city') not in ('תל אביב','תל אביב-יפו') for b in cat['branches']):raise ValueError('Wrong branch locality')
 if len(cat['rows'])!=cat['product_count']:raise ValueError('Catalog count mismatch')
 seen=set();offers=0
 for f in (data/'offers').glob('*.json'):
  for pid,p in json.loads(f.read_text(encoding='utf-8')).items():
   if pid in seen or str(pid)[-2:]!=f.stem:raise ValueError('Duplicate or misplaced product')
   seen.add(pid)
   for o in p['offers']:
    price=o.get('price')
    if o.get('branch_id') not in expected or o.get('source_type')!='official_file' or not isinstance(price,(int,float)) or not math.isfinite(price) or not 0<price<=100000:raise ValueError('Invalid TLV offer')
    offers+=1
 if seen!={r[0] for r in cat['rows']} or offers!=cat['offer_count']:raise ValueError('Offer count mismatch')
 return cat
def bootstrap():
 data=SITE/'data'
 if (data/'catalog.json').exists():return validate(data)
 # Only bootstrap the known existing public snapshot; subsequent runs use committed data.
 with tempfile.TemporaryDirectory(prefix='tlv-bootstrap-') as td:
  stage=Path(td);(stage/'offers').mkdir()
  def get(path):
   if not re.fullmatch(r'(?:catalog|prices|refresh-status|source-status|city-basket|smart-shopping|deals)\.json|offers/[0-9]{2}\.json',path):raise ValueError('Unexpected bootstrap path')
   r=requests.get('https://tlvnet.com/super/data/'+path,timeout=(15,45));r.raise_for_status()
   if not r.url.startswith('https://tlvnet.com/super/data/'):raise ValueError('Unexpected bootstrap redirect')
   obj=r.json();(stage/path).write_text(json.dumps(obj,ensure_ascii=False)+'\n',encoding='utf-8');return obj
  cat=get('catalog.json')
  if cat.get('city') not in ('תל אביב','תל אביב-יפו') or {b['id'] for b in cat.get('branches',[])}!={b['id'] for b in reviewed()}:raise ValueError('Untrusted bootstrap identity')
  paths=['prices.json','refresh-status.json','source-status.json','city-basket.json','smart-shopping.json','deals.json']+['offers/'+s+'.json' for s in sorted({str(r[0])[-2:] for r in cat['rows']})]
  with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(get,paths))
  validate(stage)
  data.mkdir(parents=True,exist_ok=True);shutil.copytree(stage,data,dirs_exist_ok=True)
 return validate(data)
def run(raw_dir):
 bootstrap();c=collector();deals=load('build_super_deals','TLV')
 import build_super_deals
 original=build_super_deals.build;build_super_deals.build=deals.build
 try:report=c.run(raw_dir)
 finally:build_super_deals.build=original
 # Registered branches and full city coverage are distinct. Legacy identifiers stay pending.
 status=json.loads((c.D/'source-status.json').read_text(encoding='utf-8'));status.pop('connection_notes',None);c.write(c.D/'source-status.json',status)
 report['registered_branch_count']=len(reviewed());report['pending_branch_count']=len(status.get('pending',[]));report['coverage_note']='19 reviewed physical branches; other sources remain unverified'
 for name in ('catalog.json','prices.json'):
  value=json.loads((c.D/name).read_text(encoding='utf-8'));value['coverage_complete']=False;c.write(c.D/name,value)
 deals=json.loads((c.D/'deals.json').read_text(encoding='utf-8'));deals['city']='תל אביב-יפו';c.write(c.D/'deals.json',deals)
 c.write(c.D/'refresh-status.json',report);validate(c.D);return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--raw-dir',type=Path);p.add_argument('--bootstrap-only',action='store_true');a=p.parse_args()
 if a.bootstrap_only:bootstrap()
 elif a.raw_dir:run(a.raw_dir)
 else:p.error('--raw-dir is required for collection')
