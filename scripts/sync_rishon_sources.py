#!/usr/bin/env python3
"""Source-authoritative Rishon intake; shares tested readers, never writes Ashdod.

Collect all dated Mevalim occurrences and supplemental national/official cards.
Source failures preserve existing records. An occurrence is keyed by title/date/time/venue.
"""
import argparse, hashlib, json, re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta
from pathlib import Path
from urllib.parse import urljoin,urlparse,unquote
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup
import sync_mevalim_ashdod_direct as mevalim
import sync_ashdod_supplemental as shared
ROOT=Path(__file__).resolve().parents[1];Z=ZoneInfo('Asia/Jerusalem');CITY='ראשון לציון';TODAY=datetime.now(Z).date();LIMIT=TODAY+timedelta(days=153)
OUT=ROOT/'events-preview/admin/data';DATA=ROOT/'events-preview/rishon-lezion/data/events.json'
SOURCES={'mevalim':'https://www.mevalim.co.il/rishon-lezion/','makore':'https://www.makore.co.il/browse/city/ראשון-לציון','tickchak':'https://live.tickchak.co.il/rishon-lezion','friends':'https://friends-hist.co.il/hall/friends-ראשון-לציון/','bravo':'https://kupatbravo.co.il/search/?all=1&producer=48','htrl':'https://htrl.co.il/לוח-שנה/','htrl_adults':'https://htrl.co.il/third-calendar/','kotar':'https://www.kotar-rishon-lezion.org.il/events-category/eventsactivities/'}
STAMP=datetime.now(Z).isoformat();WARNINGS={}
def local(text):return any(x in str(text) for x in [CITY,'ראשל','Rishon','rishon'])
def horizon(day):return TODAY.isoformat()<=day<=LIMIT.isoformat()
def clean_address(text):
 removed=[]
 def fix(m):
  line=m[0]
  if not local(line) and any(c in line for c in ['אשדוד','חולון','תל אביב','ירושלים','חיפה','באר שבע']):removed.append(line);return ''
  return line
 return re.sub(r'כתובת\s*[:：]\s*[^\n]+',fix,text or '').strip(),removed
shared.remove_conflicting_address=clean_address

def make(src,title,day,clock,venue,url,description='',image=None,raw=''):
 e=shared.make(src,title,day,clock,venue,url,description,image,raw)
 e['city']=CITY;e['event_id']='rishon_'+src+'_'+hashlib.sha256((url+day+clock+mevalim.norm(title)).encode()).hexdigest()[:20]
 if e['category']=='kids':e['audiences']=['kids','families']
 if src=='htrl_adults':e['audiences']=['adults','seniors'];e['local_source_name']='htrl_adults'
 return e

def collect_mevalim():
 p=shared.page(SOURCES['mevalim']);config=re.search(r'var mevalimAjax = (\{.*?\});',str(p));ajax=json.loads(config[1]) if config else None
 for button in list(p.select('.mevalim_load_more_events__btn')):
  if button.get('data-is-passed')!='0':continue
  if not ajax:raise ValueError('Missing source pagination configuration')
  n=2
  while n<=40:
   r=requests.post(ajax['url'],data={'action':'mevalim_load_more_events','nonce':ajax['nonce'],'is_passed':'0','post_id':button['data-table-id'],'page':n,'source_type':button.get('data-source-type','')},timeout=40);r.raise_for_status();j=r.json()
   if not j.get('success'):raise ValueError('Incomplete Mevalim pagination')
   p.append(BeautifulSoup(j.get('data',{}).get('content',''),'html.parser'))
   if not j.get('data',{}).get('canLoadMore'):break
   n+=1
 rows=[r for r in p.select('tr[data-mvlm-event-date]') if horizon(datetime.strptime(r['data-mvlm-event-date'],'%d.%m.%y %H:%M').date().isoformat())]
 def read(row):
  e,issues=mevalim.collect_row(row,STAMP);e['city']=CITY;e['event_id']=e['event_id'].replace('mevalim_as_','mevalim_ri_');e['description'],_=clean_address(e.get('description'));e['series_description']=e['description'];e['source_detail_issues']=issues
  if e['category']=='kids':e['audiences']=['kids','families']
  return e
 with ThreadPoolExecutor(max_workers=4)as pool:return list(pool.map(read,rows))

def convert(o,src):
 loc=o.get('location') or {};loc=loc[0] if isinstance(loc,list) and loc else loc
 if not isinstance(loc,dict):return None
 addr=loc.get('address') or {};address=addr.get('addressLocality','') if isinstance(addr,dict) else addr
 if not local(str(address)+' '+loc.get('name','')):return None
 dt=datetime.fromisoformat(o['startDate'].replace('Z','+00:00'));dt=dt.astimezone(Z) if dt.tzinfo else dt.replace(tzinfo=Z)
 if not horizon(dt.date().isoformat()):return None
 offers=o.get('offers')or{};offers=offers[0] if isinstance(offers,list) and offers else offers
 url=o.get('url')or str(o.get('@id','')).split('#')[0]or offers.get('url')
 if not url:return None
 e=make(src,o['name'],dt.date().isoformat(),dt.strftime('%H:%M'),loc.get('name',CITY),url,o.get('description',''),shared.image(o),str(o.get('genre')or o.get('additionalType')or''))
 e['ticket_url']=e['purchase_url']=offers.get('url')or url
 if 'Cancelled' in str(o.get('eventStatus','')):e['status']='cancelled'
 if 'Postponed' in str(o.get('eventStatus','')):e['status']='postponed'
 if offers.get('price')is not None:e['price_min_ils']=offers['price']
 return e

def collect_friends():
 p=shared.page(SOURCES['friends']);posters={urljoin(SOURCES['friends'],a['href']):urljoin(SOURCES['friends'],row.select_one('img[src]')['src']) for row in p.select('.search_show_row') if (a:=row.select_one('a.btn_info[href]')) and row.select_one('img[src]')}
 def read(pair):
  url,poster=pair
  try:
   q=shared.page(url);h=q.find('h1');title=h.get_text(' ',strip=True)if h else '';desc=q.select_one('.wrap_brief');out=[]
   for block in q.select('.info_col'):
    header=block.select_one('.date_time_address');d=block.select_one('.date_wrap');v=block.select_one('.address_wrap')
    if not header or not d or not local(header.get_text()):continue
    dt=datetime.strptime(d.get_text(strip=True),'%d/%m/%y');tm=re.search(r'\b\d{2}:\d{2}\b',header.get_text())
    if not horizon(dt.date().isoformat())or not tm:continue
    e=make('friends',title,dt.date().isoformat(),tm[0],v.get_text(' ',strip=True)if v else 'FRIENDS ראשון לציון',url,desc.get_text('\n',strip=True)if desc else '',poster)
    a=block.select_one('a[href*="tickets"],a.btn_purchase[href],a[href*="smarticket"]')
    if a:e['ticket_url']=e['purchase_url']=urljoin(url,a['href'])
    out.append(shared.friends_prices(e,q))
   return out
  except Exception as ex:WARNINGS.setdefault('friends',[]).append(str(ex)[:200]);return []
 with ThreadPoolExecutor(max_workers=4)as pool:return [e for rows in pool.map(read,posters.items())for e in rows]

def collect_bravo():
 p=shared.page(SOURCES['bravo'])
 links={urljoin(SOURCES['bravo'],a['href']) for a in p.select('a.block-img[href*="/announce/"]')}
 def read(url):
  try:
   q=shared.page(url);h=q.find('h1');meta=q.find('meta',property='og:image');image=meta.get('content')if meta else None
   desc=q.select_one('[itemprop="description"],.announce-description,.description');out=[]
   for row in q.select('tr[data-city]'):
    if not local(row.get('data-city')):continue
    tm=row.select_one('time[datetime]');v=row.select_one('[data-hall]');a=row.select_one('a[href*="/announce/buy/"]')
    if not tm or not h or not a:continue
    dt=datetime.fromisoformat(tm['datetime'])
    if not horizon(dt.date().isoformat()):continue
    e=make('bravo',h.get_text(' ',strip=True),dt.date().isoformat(),dt.strftime('%H:%M'),v.get('data-hall')if v else CITY,url,desc.get_text(' ',strip=True)if desc else '',image)
    e['ticket_url']=e['purchase_url']=urljoin(url,a['href']);out.append(e)
   return out
  except Exception as ex:WARNINGS.setdefault('bravo',[]).append(str(ex)[:200]);return []
 with ThreadPoolExecutor(max_workers=4)as pool:return [e for rows in pool.map(read,sorted(links))for e in rows]

def collect_structured(src):
 p=shared.page(SOURCES[src]);objects=shared.ld(p)
 if src=='makore':
  count=re.search(r'\d+',p.h1.get_text())if p.h1 else None;total=int(count[0])if count else len(objects)
  per=len(objects)
  if per:
   for n in range(2,min(1+(total+per-1)//per,30)):
    objects.extend(shared.ld(shared.page(SOURCES[src]+'?pages='+str(n))))
 rows=[e for o in objects if(e:=convert(o,src))]
 if src in ['makore','tickchak']:
  with ThreadPoolExecutor(max_workers=4)as pool:rows=list(pool.map(shared.detail,rows))
 return rows

def official_details(src,existing):
 p=shared.page(SOURCES[src]);links={}
 for a in p.select('a[href]'):
  href=urljoin(SOURCES[src],a['href']);label=mevalim.clean(a.get_text(' ',strip=True))
  if any(x in href for x in ['/show/','/event/','/events/','/product/'])and len(label)>3:links[href]=label
 candidates=[]
 for url,label in links.items():
  matches=[e for e in existing if horizon(e.get('start_date','')) and e.get('category')!='conference' and (mevalim.norm(e.get('title'))in mevalim.norm(label)or mevalim.norm(label)in mevalim.norm(e.get('title')))and min(len(mevalim.norm(label)),len(mevalim.norm(e.get('title'))))>=7]
  if matches:candidates.append((url,matches))
 def read(pair):
  url,matches=pair
  try:
   q=shared.page(url);meta=q.find('meta',property='og:image');body=q.select_one('.txt_container,.wrap_brief,.event-description,.entry-content,[itemprop="description"]');desc=body.get_text('\n',strip=True)if body else '';img=urljoin(url,meta['content'])if meta and meta.get('content')else None
   if not desc and not img:return []
   return [make(src,e['title'],e['start_date'],str(e.get('start_time')or'')[:5],e.get('venue')or CITY,url,desc,img,{'kids':'ילדים ומשפחה','lecture':'הרצאות','music':'מוזיקה','theatre':'תיאטרון'}.get(e.get('category'),''))for e in matches]
  except Exception as ex:WARNINGS.setdefault(src,[]).append(str(ex)[:200]);return []
 with ThreadPoolExecutor(max_workers=4)as pool:return [e for rows in pool.map(read,candidates)for e in rows]

def venue_key(value):
 text=mevalim.norm(value)
 if 'מאיר ניצנ' in text or 'היכל התרבות' in text:return 'htrl'
 if 'יד לבנימ' in text:return 'yad-labanim'
 return re.sub(r'ראשונ לציונ|ראשלצ','',text).strip()

def merge(events,new):
 out=list(events);added=updated=duplicates=0
 for e in sorted(new,key=lambda e:0 if e.get('source')=='mevalim_direct'else 1):
  match=next((x for x in out if x.get('start_date')==e['start_date']and str(x.get('start_time')or'')[:5]==e['start_time']and venue_key(x.get('venue'))==venue_key(e.get('venue'))and (mevalim.norm(x.get('title'))==mevalim.norm(e['title'])or shared.equivalent({'title':x.get('title',''),'start_date':x['start_date']},e))),None)
  if match:
   if match.get('source')=='mevalim_direct'and e.get('source')!='mevalim_direct':match['crosscheck_sources']=sorted(set(match.get('crosscheck_sources',[])+[e['content_source_url']]));duplicates+=1;continue
   preserved={k:match[k]for k in ['event_id','operator_id','operator_name','venue_institution_id','age_min','age_max','audiences','address']if match.get(k)is not None}
   if match.get('content_locked') or match.get('description_manual_override'):
    for field in ['title','category','subcategory','categories','description','long_description','series_description','editorial_description','short_pitch','content_source_url','detail_source_url','ticket_url','purchase_url','purchase_source','is_active','visibility_reason','canonical_event_id','duplicate_of']:
     if field in match:preserved[field]=match[field]
   if match.get('image_verified') and match.get('image_url'):
    for field in ['image_url','image_origin_url','image_source','image_credit','image_strategy','image_verified','image_publishable','image_rights_status','thumbnail_url','thumbnail_ready']:
     if field in match:preserved[field]=match[field]
   for field in ['description','series_description','image_url','image_origin_url']:
    if not e.get(field)and match.get(field):e[field]=match[field]
   match.update(e);match.update(preserved)
   if not preserved.get('thumbnail_url'):match.pop('thumbnail_url',None);match['thumbnail_ready']=False
   updated+=1
  else:out.append(e);added+=1
 return out,{'added':added,'updated':updated,'duplicates_merged':duplicates}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--sources',nargs='*',default=list(SOURCES));ap.add_argument('--snapshot');ap.add_argument('--collect-only',action='store_true');args=ap.parse_args();data=json.loads(DATA.read_text());report={'checked_at':STAMP,'city':CITY,'sources':{},'warnings':WARNINGS};new=[]
 if args.snapshot:snap=json.loads(Path(args.snapshot).read_text());new=snap['events'];report=snap['report']
 else:
  for src in args.sources:
   try:
    rows=collect_mevalim()if src=='mevalim'else collect_friends()if src=='friends'else official_details(src,data['events'])if src in ['htrl','htrl_adults','kotar']else collect_bravo()if src=='bravo'else collect_structured(src)
    rows=list({e['event_id']:e for e in rows if horizon(e['start_date'])}.values());new.extend(rows);report['sources'][src]={'status':'ok'if rows else'no_detail_enrichment'if src in ['htrl','htrl_adults','kotar']else'no_parseable_occurrences','occurrences':len(rows),'images':sum(bool(e.get('image_url'))for e in rows)}
   except Exception as ex:report['sources'][src]={'status':'failed','error':str(ex)[:300]}
   print(src,report['sources'][src],flush=True)
  OUT.mkdir(exist_ok=True);(OUT/'rishon-source-snapshot.json').write_text(json.dumps({'events':new,'report':report},ensure_ascii=False,indent=2)+'\n')
 if not args.collect_only:
  data['events'],counts=merge(data['events'],new);data['generated_at']=STAMP;data['generatedAt']=STAMP;data.setdefault('stats',{})['events']=len(data['events']);DATA.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');report.update(counts);(OUT/'rishon-source-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('MERGE',counts,flush=True)
 return 0 if new else 2
if __name__=='__main__':raise SystemExit(main())
