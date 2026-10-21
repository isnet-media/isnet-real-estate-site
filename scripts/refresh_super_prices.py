"""Refresh only registered Ashdod branches from their official public feeds.
A branch is replaced atomically after identity/date/count checks. Failed sources
retain the last verified snapshot. No online substitutions or guessed equivalents.
"""
from pathlib import Path
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse,unquote
import argparse,collections,gzip,hashlib,json,math,re,tempfile
import xml.etree.ElementTree as ET
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'SUPER.ASHDOD/data';TZ=ZoneInfo('Asia/Jerusalem')
PUBLIC='https://url.publishedprices.co.il'
ACCOUNTS={'רמי לוי':'RamiLevi','יוחננוף':'yohananof','אושר עד':'osherad','טיב טעם':'TivTaam','קשת טעמים':'Keshet','פרשמרקט':'freshmarket'}
def session():
 s=requests.Session();s.mount('https://',HTTPAdapter(max_retries=Retry(total=2,backoff_factor=1,status_forcelist=[429,500,502,503,504],allowed_methods=['GET','HEAD'])));return s
def request(s,url,**kw):
 r=s.request(kw.pop('method','GET'),url,timeout=(25,45),**kw);r.raise_for_status();return r

def filetime(name):
 m=re.search(r'-(\d{8})-?(\d{4,6})\.',name,re.I)
 if not m:raise ValueError('Unrecognized publication timestamp')
 return m[1]+m[2].ljust(6,'0')
def matching(entries,b,kind):
 pattern=rf'^{kind}{b["chain_id"]}-(?:\d+-)?0*{int(b["store_id"])}-\d{{8}}'
 return sorted([e for e in entries if re.match(pattern,e['name'],re.I)],key=lambda e:filetime(e['name']))
def xmlbytes(s,e):
 raw=request(s,e['url']).content
 if len(raw)>30_000_000:raise ValueError('Oversized source')
 xml=gzip.decompress(raw) if raw[:2]==b'\x1f\x8b' else raw
 if len(xml)>120_000_000 or b'<!DOCTYPE' in xml.upper():raise ValueError('Unsafe or oversized XML')
 return xml

def listing(b):
 s=session();chain=b['chain'];entries=[]
 if chain in ACCOUNTS:
  r=request(s,PUBLIC+'/login');token=BeautifulSoup(r.text,'html.parser').find('meta',attrs={'name':'csrftoken'})['content']
  r=request(s,PUBLIC+'/login/user',method='POST',data={'username':ACCOUNTS[chain],'password':'','csrftoken':token})
  if '/file' not in r.url:raise ValueError('Public feed sign-in not accepted')
  token=BeautifulSoup(r.text,'html.parser').find('meta',attrs={'name':'csrftoken'})['content']
  j=request(s,PUBLIC+'/file/json/dir',method='POST',data={'csrftoken':token,'sEcho':1,'iDisplayStart':0,'iDisplayLength':100000,'sSearch':'','cd':'/'},headers={'X-CSRFToken':token,'Referer':PUBLIC+'/file'}).json()
  if int(j.get('iTotalRecords',0))>len(j.get('aaData',[])):raise ValueError('Truncated publication listing')
  entries=[{'name':x['name'],'url':PUBLIC+'/file/d/'+x['name']} for x in j.get('aaData',[]) if re.match(r'^(Price|Promo)',x['name'])]
 elif chain=='קרפור':
  html=request(s,'https://prices.carrefour.co.il/').text
  files=json.loads(re.search(r'const files\s*=\s*(\[.*?\]);',html,re.S)[1]);folder=re.search(r"const path\s*=\s*'([^']+)'",html)[1]
  entries=[{'name':x['name'],'url':f'https://prices.carrefour.co.il/{folder}/{x["name"]}'} for x in files]
 elif chain=='ויקטורי':
  js=request(s,b['source_url']).json();entries=[{'name':x['fileName'],'url':f'https://laibcatalog.co.il/webapi/{b["chain_id"]}/{x["fileName"]}'} for x in js]
 elif chain=='שופרסל':
  html=request(s,'https://prices.shufersal.co.il/FileObject/UpdateCategory',params={'catID':0,'storeId':int(b['store_id'])}).text
  entries=[{'name':unquote(urlparse(a['href']).path.split('/')[-1]),'url':a['href']} for a in BeautifulSoup(html,'html.parser').select('a[href]') if a['href'].startswith('https://')]
 elif chain=='זול ובגדול':
  base='https://zolvebegadol.binaprojects.com/';request(s,base+'Main.aspx')
  for day in (datetime.now(TZ).date(),datetime.now(TZ).date()-timedelta(days=1)):
   for typ in ('4','6'):
    js=request(s,base+'MainIO_Hok.aspx',method='POST',data={'WStore':str(int(b['store_id'])),'WDate':day.strftime('%d/%m/%Y'),'WFileType':typ}).json()
    for x in js:
     if x.get('FileNm'):entries.append({'name':x['FileNm'],'url':base+'Download/'+x['FileNm']})
 else:raise ValueError('No reviewed official connector for branch')
 return s,entries

def field(node,key):return next(((c.text or '').strip() for c in node if c.tag.split('}')[-1].casefold()==key.casefold()),'')
def kg(unit):return bool(re.fullmatch(r'(?:1\s*)?(?:קילוגרמים?|קילוגרם|ק[״\"]?ג)',unit))
def parse_price(xml,b):
 root=ET.fromstring(xml)
 if field(root,'ChainID')!=b['chain_id'] or int(field(root,'StoreID'))!=int(b['store_id']):raise ValueError('Branch identity mismatch')
 out={};bad=0
 for item in root.findall('.//Item'):
  t=lambda k:field(item,k)
  try:price=float(t('ItemPrice'))
  except ValueError:bad+=1;continue
  if not math.isfinite(price) or price<0 or price>100000:bad+=1;continue
  code=t('ItemCode')
  if not code.isdigit():bad+=1;continue
  external_type='0' if b['chain_id']=='7290876100000' else '1'
  pid=code if t('ItemType')==external_type and len(code) in (8,12,13,14) else b['chain_id']+':'+code
  # Zero price removes an observation. ItemStatus varies by publisher and is not a deletion flag.
  if price==0:out[pid]=None;continue
  weighted=t('bIsWeighted');unit=t('UnitQty');calc='package' if weighted=='0' else 'kg' if weighted=='1' and kg(unit) else 'unknown'
  p={'id':pid,'barcode':code,'name':t('ItemName'),'unit':t('UnitOfMeasure'),'quantity':t('Quantity'),'unit_quantity':unit,'weighted':weighted,'manufacturer':t('ManufactureName'),'calculation_unit':calc,'search_text':' '.join([code,t('ItemName'),t('ManufactureName')]).lower()}
  p['offers']=[{'branch_id':b['id'],'price':price,'unit_price':t('UnitOfMeasurePrice'),'updated_at':t('PriceUpdateTime'),'source_type':'official_file','kind':'רגיל','eligible_for_basket':calc!='unknown','calculation_unit':calc,'raw_price':price,'raw_unit':unit}];out[pid]=p
 if bad>max(20,len(out)*.03):raise ValueError('Too many malformed price records')
 return out

def refresh_branch(b,raw_dir,now):
 report={'branch_id':b['id'],'chain':b['chain'],'previous_file_date':b.get('file_date'),'checked_at':now.isoformat()}
 try:
  s,entries=listing(b);fulls=matching(entries,b,'PriceFull')
  if not fulls:raise ValueError('No full price file in official listing')
  full=fulls[-1];stamp=filetime(full['name']);date=datetime.strptime(stamp[:8],'%Y%m%d').date()
  if date>now.date() or date<now.date()-timedelta(days=2):raise ValueError('Publication outside freshness window')
  previous=max([filetime(x) for x in b.get('files_applied',[]) if re.match(r'^Price',x,re.I)] or ['0'])
  deltas=[x for x in matching(entries,b,'Price') if filetime(x['name'])>stamp]
  applied=[full]+deltas
  if filetime(applied[-1]['name'])<previous:raise ValueError('Source would roll back newer prices')
  products={};hashes=[]
  for e in applied:
   xml=xmlbytes(s,e);products.update(parse_price(xml,b));hashes.append({'filename':e['name'],'sha256':hashlib.sha256(xml).hexdigest()})
  products={k:v for k,v in products.items() if v is not None}
  if len(products)<max(100,int(b.get('product_count',0)*.65)):raise ValueError('Unexpected loss of branch products')
  if len(products)>max(1000,b.get('product_count',0)*2):raise ValueError('Unexpected branch product growth')
  latest=datetime.strptime(filetime(applied[-1]['name'])[:8],'%Y%m%d').date()
  if latest>now.date():raise ValueError('Future publication timestamp')
  updated=dict(b,file_date=latest.isoformat(),base_file_date=date.isoformat(),retrieved_at=now.isoformat(),files_applied=[x['name'] for x in applied],product_count=len(products),source_files=hashes,price_file_url=b['source_url'],source_type='official_file')
  report.update(status='updated',file_date=latest.isoformat(),product_count=len(products),files=hashes)
  promos=matching(entries,b,'PromoFull')
  if promos:
   try:
    e=promos[-1];xml=xmlbytes(s,e);root=ET.fromstring(xml)
    if field(root,'ChainID')!=b['chain_id'] or int(field(root,'StoreID'))!=int(b['store_id']):raise ValueError('Promotion branch mismatch')
    path=raw_dir/(b['id']+'.xml');path.write_bytes(xml);path.with_suffix('.meta.json').write_text(json.dumps({'source_url':b['source_url'],'filename':e['name']}));report['promotions']='downloaded'
   except Exception as ex:report['promotions']='failed';report['promotion_error']=type(ex).__name__
  else:report['promotions']='unavailable'
  print(b['id'],report['status'],len(products),flush=True);return updated,products,report
 except Exception as ex:
  # Avoid leaking signed URLs/cookies through request exception strings.
  report.update(status='retained_previous',error=str(ex) if isinstance(ex,ValueError) else type(ex).__name__)
  print(b['id'],'retained_previous',report['error'],flush=True);return b,None,report

def write(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':'))+'\n')
def run(raw_dir):
 now=datetime.now(TZ);catalog=json.loads((D/'catalog.json').read_text());products={}
 for f in (D/'offers').glob('*.json'):products.update(json.loads(f.read_text()))
 raw_dir.mkdir(parents=True,exist_ok=True)
 with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(lambda b:refresh_branch(b,raw_dir,now),catalog['branches']))
 # One recovery pass only, after other sources had time to complete.
 for index,(branch,products,report) in enumerate(results):
  report['attempts']=1
  if products is None:
   retried=refresh_branch(branch,raw_dir,datetime.now(TZ))
   retried[2]['attempts']=2;retried[2]['first_error']=report.get('error')
   results[index]=retried
 reports=[];branches=[]
 for b,new,report in results:
  branches.append(b);reports.append(report)
  if new is None:continue
  for p in products.values():p['offers']=[o for o in p['offers'] if o['branch_id']!=b['id']]
  for pid,p in new.items():
   if pid not in products:products[pid]=p
   else:products[pid]['offers'].extend(p['offers'])
 products={k:p for k,p in products.items() if p['offers']}
 shards=collections.defaultdict(dict)
 for pid,p in products.items():shards[pid[-2:]][pid]=p
 for suffix,ps in shards.items():write(D/'offers'/f'{suffix}.json',ps)
 updated=sum(r['status']=='updated' for r in reports)
 if updated:catalog['retrieved_at']=now.isoformat()
 catalog.update(branches=branches,product_count=len(products),offer_count=sum(len(p['offers']) for p in products.values()))
 catalog['rows']=[[pid,p['name'],p['quantity'],p['unit_quantity'],p['weighted'],p.get('manufacturer',''),min(o['price'] for o in p['offers']),len(p['offers']),[o['branch_id'] for o in p['offers']],p['calculation_unit']] for pid,p in products.items()]
 write(D/'catalog.json',catalog)
 prices=json.loads((D/'prices.json').read_text())
 for k in ('branches','retrieved_at','product_count','offer_count'):prices[k]=catalog[k]
 prices['branch_count']=len(branches);prices['chains']=dict(collections.Counter(b['chain'] for b in branches));write(D/'prices.json',prices)
 report={'checked_at':now.isoformat(),'updated_count':updated,'branch_count':len(branches),'all_sources_updated':updated==len(branches),'branches':reports};write(D/'refresh-status.json',report)
 from build_super_deals import build
 # Promotion publication failure must preserve the last verified selection.
 old=(D/'deals.json').read_bytes()
 try:build(raw_dir)
 except Exception as ex:(D/'deals.json').write_bytes(old);report['promotion_build']='retained_previous';write(D/'refresh-status.json',report)
 print('Updated',updated,'of',len(branches));return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--raw-dir',type=Path,required=True);a=p.parse_args();run(a.raw_dir)
