#!/usr/bin/env python3
"""Public Ironit course catalog. pip install requests beautifulsoup4.
Conditional GET cache, stable source IDs, bounded concurrency, conservative status.
"""
import argparse, concurrent.futures, datetime, hashlib, json, pathlib, re, threading, time
from urllib.parse import urlsplit, urlunsplit
import requests
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--cache',default=str(ROOT/'.cache/meusharim'));p.add_argument('--workers',type=int,default=3);p.add_argument('--refresh',action='store_true');args=p.parse_args()
cache=pathlib.Path(args.cache);cache.mkdir(parents=True,exist_ok=True)
lock=threading.Lock();next_request=0
local=threading.local()
TODAY=datetime.datetime.now(datetime.timezone.utc).isoformat()
def fetch(url,data=None):
 global next_request
 key=hashlib.sha256((url+str(data)).encode()).hexdigest();fp=cache/(key+'.json')
 try:old=json.loads(fp.read_text()) if fp.exists() else None
 except json.JSONDecodeError:old=None
 if old and not args.refresh:return old['body']
 headers={'User-Agent':'ISNET-Meusharim/1.0 (public course catalog)'}
 if old:
  if old.get('etag'):headers['If-None-Match']=old['etag']
  if old.get('modified'):headers['If-Modified-Since']=old['modified']
 with lock:
  delay=max(0,next_request-time.monotonic());next_request=max(next_request,time.monotonic())+0.5
 if delay:time.sleep(delay)
 if not hasattr(local,'session'):local.session=requests.Session()
 r=local.session.post(url,data=data,headers=headers,timeout=40) if data else local.session.get(url,headers=headers,timeout=40)
 if r.status_code==304:
  old['checked']=TODAY;tmp=fp.with_suffix('.tmp');tmp.write_text(json.dumps(old,ensure_ascii=False));tmp.replace(fp);return old['body']
 r.raise_for_status();body=r.text
 tmp=fp.with_suffix('.tmp');tmp.write_text(json.dumps({'body':body,'etag':r.headers.get('ETag'),'modified':r.headers.get('Last-Modified'),'checked':TODAY},ensure_ascii=False));tmp.replace(fp);return body

def txt(s,sel):
 x=s.select_one(sel);return x.get_text(' ',strip=True) if x else ''
def canonical(u):
 x=urlsplit(u);return urlunsplit((x.scheme,x.netloc,x.path,'',''))
listing_path=cache/'listing.json'
if listing_path.exists() and not args.refresh: listing=json.loads(listing_path.read_text())
else:
 data=[('filters[events_type][]','52')]+[('filters[events_age][]',str(x)) for x in (5,4,3,2,7,6)]
 listing=json.loads(fetch('https://www.ironit.org.il/wp-content/themes/ironit/inc/event-filter.php',data));listing_path.write_text(json.dumps(listing,ensure_ascii=False))
s=BeautifulSoup(listing['data']['events_data'],'html.parser')
# Taxonomy tabs identify subcategories without guessing from names.
categories={}
for tab in s.select('.tab-content'):
 if tab.get('data-tab')=='all':continue
 title=s.select_one('button[data-tab="'+tab['data-tab']+'"]')
 for e in tab.select('.event'):
  i=e.select_one('[data-post-id]');
  if i and title:categories[i['data-post-id']]=title.get_text(' ',strip=True)
records={};duplicates=0
for e in s.select('.tab-content[data-tab="all"] .event'):
 ident=e.select_one('[data-post-id]');a=e.select_one('a');
 if not ident or not a:continue
 ident=ident['data-post-id']
 if ident in records:duplicates+=1;continue
 image=e.select_one('.image');m=re.search(r'url\((.*?)\)',image.get('style','')) if image else None
 loc=e.select_one('.location');spans=loc.select(':scope > span') if loc else []
 records[ident]={'id':'ironit-'+ident,'source_id':ident,'name':txt(e,'.title'),'subtitle':txt(e,'.title-text > span:nth-child(2)'), 'category':categories.get(ident,''),'age':txt(e,'.events-age-terms'),'ages':[], 'district':'','address':'','day':txt(e,'.date').strip(' |'),'time':txt(e,'.time').strip(' |'),'place':spans[-1].get_text(' ',strip=True) if spans else '', 'instructor':txt(e,'.master').removeprefix('בהדרכת:').strip(),'source':'החברה העירונית לתרבות ופנאי אשדוד','source_url':canonical(a['href']),'registration_url':None,'status':'requires_confirmation','price':None,'phone':None,'image':m.group(1) if m else None,'verified_at':TODAY,'detail_verified':False}
errors=[]
def enrich(r):
 try:
  body=fetch(r['source_url']);d=BeautifulSoup(body,'html.parser');main=d.select_one('.event-single')
  if not main or txt(main,'h1')!=r['name']:raise ValueError('Course detail identity mismatch')
  key=hashlib.sha256((r['source_url']+'None').encode()).hexdigest();r['verified_at']=json.loads((cache/(key+'.json')).read_text()).get('checked',TODAY)
  r['detail_verified']=True;r['ages']=[a.get_text(' ',strip=True) for a in main.select('.ages a')];r['age']=' / '.join(r['ages']) or r['age'];r['description']=txt(main,'.text-container');r['subtitle']=txt(main,'.title h2') or r['subtitle']
  r['schedule']=[{'day':txt(x,'.date'),'time':txt(x,'.time')} for x in main.select('.shedule-day')]
  a=main.select_one('a.buy[href]');r['registration_url']=a['href'] if a and a['href'].startswith('https://') else None
  r['location_url']=(main.select_one('.location a') or {}).get('href')
  tel=main.select_one('a[href^="tel:"]');r['phone']=tel['href'][4:] if tel else None
  r['enrollment_label']=txt(main,'.button')
  if any(x in r['enrollment_label'] for x in ('ההרשמה נסגרה','ההרשמה הסתיימה','אין מקומות')):r['status']='closed'
  r['detail_hash']=hashlib.sha256(body.encode()).hexdigest()
 except Exception as ex:errors.append({'id':r['id'],'url':r['source_url'],'error':str(ex)})
 return r
out=ROOT/'meusharim/ashdod/data';out.mkdir(parents=True,exist_ok=True)
result=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=min(args.workers,6)) as pool:
 for r in pool.map(enrich,records.values()):
  result.append(r)
  if len(result)%25==0:print('details',len(result),'/',len(records),'errors',len(errors),flush=True)
# District association uses the source's public district filter, not place-name guesses.
landing=BeautifulSoup(fetch('https://www.ironit.org.il/type/%D7%97%D7%95%D7%92%D7%99%D7%9D/'),'html.parser')
byid={r['source_id']:r for r in result}
for item in landing.select('.filter-district li'):
 try:
  fp=cache/'districts'/(item['data-id']+'.json')
  if fp.exists() and not args.refresh:
   x=json.loads(fp.read_text());ids=x['ids'];label=x['district']
  else:
   label=item.get_text(' ',strip=True)
   j=json.loads(fetch('https://www.ironit.org.il/wp-content/themes/ironit/inc/event-filter.php',[('filters[events_type][]','52'),('filters[events_district][]',item['data-id'])]))
   ds=BeautifulSoup(j['data']['events_data'],'html.parser');ids=[e['data-post-id'] for e in ds.select('.tab-content[data-tab="all"] [data-post-id]')]
  for ident in ids:
   if ident in byid:byid[ident]['district']=label
 except Exception as ex:errors.append({'district':item.get_text(' ',strip=True),'error':str(ex)})
# Public activity taxonomy gives broad categories; retain exact course type as subcategory.
for r in result:r['subcategory']=r['category'];r['category']=''
for item in landing.select('.filter-activity li'):
 try:
  fp=cache/'categories'/(item['data-id']+'.json')
  if fp.exists() and not args.refresh:
   x=json.loads(fp.read_text());ids=x['ids'];label=x['category']
  else:
   label=item.get_text(' ',strip=True)
   j=json.loads(fetch('https://www.ironit.org.il/wp-content/themes/ironit/inc/event-filter.php',[('filters[events_type][]','52'),('filters[events_activity][]',item['data-id'])]))
   ds=BeautifulSoup(j['data']['events_data'],'html.parser');ids=[e['data-post-id'] for e in ds.select('.tab-content[data-tab="all"] [data-post-id]')]
  for ident in ids:
   if ident in byid:byid[ident]['category']=label
 except Exception as ex:errors.append({'category':item.get_text(' ',strip=True),'error':str(ex)})
fields=['name','category','age','day','time','place','instructor','registration_url','image','price','address','district','phone']
report={'verified_at':TODAY,'source_reported_total':listing['data']['all_events'],'unique_records':len(result),'duplicates_removed':duplicates,'detail_verified':sum(r['detail_verified'] for r in result),'errors':errors,'completion_percent':{f:round(100*sum(bool(r.get(f)) for r in result)/len(result),1) for f in fields},'status_note':'Registration link is not evidence of open enrollment.'}
(out/'classes.json').write_text(json.dumps({'city':'אשדוד','scope':'public_ironit_catalog','retrieved_on':TODAY,'records':result},ensure_ascii=False,indent=2))
(out/'coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False),flush=True)
