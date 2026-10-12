#!/usr/bin/env python3
"""Source-authoritative Ashdod supplements. No editorial text/image gating."""
import argparse, json, re, math, hashlib
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup
from sync_mevalim_ashdod_direct import clean, norm, same_show, remove_conflicting_address
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'events-preview/admin/data'; Z=ZoneInfo('Asia/Jerusalem')
SOURCES={'makore':'https://www.makore.co.il/browse/city/אשדוד','tickchak':'https://live.tickchak.co.il/ashdod','friends':'https://friends-hist.co.il/city_cat/אשדוד','leaan':'https://www.leaan.co.il/','sababa':'https://sababa.events/he/venues/tsentr-stsenicheskikh-iskusstv-ashdod/'}
def page(url):
 r=requests.get(url,timeout=40,headers={'User-Agent':'ISNET official event source reader/1.0'});r.raise_for_status();return BeautifulSoup(r.text,'html.parser')
def objects(o):
 if isinstance(o,dict):
  yield o
  for v in o.values():
   if isinstance(v,(dict,list)):yield from objects(v)
 elif isinstance(o,list):
  for v in o:yield from objects(v)
def ld(p):
 out=[]
 for s in p.select('script[type="application/ld+json"]'):
  try:out.extend(o for o in objects(json.loads(s.get_text())) if 'Event' in str(o.get('@type','')) and o.get('startDate'))
  except (ValueError,TypeError):pass
 return out
def makore_rows(p):
 rows=ld(p)
 for card in p.select('[data-testid="event-card"]'):
  a=card.select_one('a[href]');im=card.select_one('img[src]');tags=card.select('[data-testid="event-card-category-badge"]')
  if not a:continue
  for o in rows:
   if urlparse(o.get('url','')).path==urlparse(a['href']).path:
    o['genre']=', '.join(t.get_text(strip=True) for t in tags)
    if im:o['image']=urljoin(SOURCES['makore'],im['src'])
 return rows
def image(o):
 x=o.get('image') or o.get('vivenu_image')
 if isinstance(x,list):x=x[0] if x else None
 if isinstance(x,dict):x=x.get('url') or x.get('contentUrl')
 return x
RULES=[(r'סטנד.?אפ|standup','standup','standup'),(r'סדנ|יצירה|ציור|פיסול|קרמיקה','workshop','creative'),(r'הרצא|כנס|lecture','lecture','lecture'),(r'תערוכ|מוזיאון|מוזאון','exhibition','exhibition'),(r'שעת סיפור','kids','story-time'),(r'ילדים|ילד|קטנטנ|פעוט|משפחה|childrens','kids','kids-activities'),(r'תיאטרון|הצגה|theater','theatre','theatre'),(r'מוזיקה|מוסיקה|קונצרט|concert|שירי|מופע|הופעה','music','live'),(r'ספורט|פילאטיס|יוגה','sport','activities'),(r'גיל השלישי|גמלאי','seniors','seniors-activities')]
def category(raw,title):
 for pattern,cat,sub in RULES:
  if re.search(pattern,raw+' '+title,re.I):return cat,sub
 return 'community','source-'+hashlib.sha256((raw or 'פעילות').encode()).hexdigest()[:10]
def make(src,title,date,time,venue,url,description='',img=None,raw='',uid=None):
 cat,sub=category(raw,title);text=BeautifulSoup(description or '','html.parser').get_text('\n',strip=True);text,removed=remove_conflicting_address(text)
 eid=src+'_as_'+hashlib.sha256((str(uid or url)+date+time).encode()).hexdigest()[:18]
 e=dict(event_id=eid,source='supplemental_'+src,city='אשדוד',title=clean(title),start_date=date,start_time=time,venue=clean(venue),status='active',category=cat,subcategory=sub,source_category=raw,source_subcategory=raw,description=text,series_description=text,image_url=img,image_origin_url=img,image_source=src,image_verified=bool(img),image_publishable=bool(img),image_represents_event=bool(img),image_strategy='official_source_event_image',image_rights_status='publisher_directed_source_reuse',ticket_url=url,purchase_url=url,content_source_url=url,source_content_authoritative=True,content_locked=True,source_priority=2,last_imported_at=datetime.now(Z).isoformat(),internal_notes=[],taxonomy_review_required=sub.startswith('source-'))
 if removed:e['removed_conflicting_source_addresses']=removed
 if e['taxonomy_review_required']:e['internal_notes'].append('נפתחה קטגוריה/תת קטגוריה חדשה; שיוך מוצע לקהילה ופנאי: '+(raw or 'ללא קטגוריה במקור'))
 return e
def convert(o,src):
 loc=o.get('location') or {}; address=loc.get('address') or {};city=address.get('addressLocality','') if isinstance(address,dict) else str(address)
 if city and 'אשדוד' not in city:return None
 dt=datetime.fromisoformat(o['startDate'].replace('Z','+00:00'));dt=dt.astimezone(Z) if dt.tzinfo else dt.replace(tzinfo=Z)
 offers=o.get('offers') or {};offers=offers[0] if isinstance(offers,list) and offers else offers
 url=o.get('url') or str(o.get('@id','')).split('#')[0] or offers.get('url','')
 e=make(src,o['name'],dt.date().isoformat(),dt.strftime('%H:%M'),loc.get('name','אשדוד'),url,o.get('description',''),image(o),str(o.get('genre') or o.get('additionalType') or urlparse(url).path.split('/')[1]),o.get('@id') or url)
 e['purchase_url']=e['ticket_url']=offers.get('url') or url
 if offers.get('price') is not None:e['price_min_ils']=offers['price']
 if 'SoldOut' in offers.get('availability',''):e['ticket_status']='sold_out'
 return e
def detail(e):
 try:
  p=page(e['content_source_url']); meta=p.find('meta',property='og:image')
  if meta and meta.get('content') and e['source']!='supplemental_makore':e['image_url']=e['image_origin_url']=urljoin(e['content_source_url'],meta['content'])
  matches=[x for x in ld(p) if norm(x.get('name'))==norm(e['title'])]
  if matches:
   o=matches[0]
   if o.get('description'):e['description']=e['series_description']=BeautifulSoup(o['description'],'html.parser').get_text('\n',strip=True)
   if image(o):e['image_url']=e['image_origin_url']=image(o)
  # Read the source's displayed production description, never the site navigation.
  for selector in ['.wrap_brief','.event-description','[itemprop="description"]']:
   block=p.select_one(selector)
   if block and block.get_text(strip=True):e['description']=e['series_description']=block.get_text('\n',strip=True);break
  if e['source']=='supplemental_makore' and 'smarticket.co.il' in urlparse(e['ticket_url']).hostname:
   original=page(e['ticket_url']);block=original.select_one('.txt_container');im=original.find('meta',property='og:image')
   if block:e['description']=e['series_description']=block.get_text('\n',strip=True).removeprefix('פרטים נוספים').strip();e['source_detail_text']=e['description']
   if im and im.get('content'):e['image_url']=e['image_origin_url']=urljoin(e['ticket_url'],im['content']);e['image_source']='smarticket'
  e['detail_checked_at']=datetime.now(Z).isoformat()
 except Exception as ex:e['source_detail_error']=str(ex)[:200]
 e['image_verified']=e['image_publishable']=e['image_represents_event']=bool(e.get('image_url'))
 e['description'],removed=remove_conflicting_address(e.get('description'));e['series_description']=e['description']
 return e

def collect(src):
 p=page(SOURCES[src]);out=[]
 if src=='makore':
  rows=makore_rows(p);h=p.find('h1');m=re.search(r'\d+',h.get_text()) if h else None
  if not m:raise ValueError('Listing count unavailable; retain previously published cards')
  count=int(m[0]);per=len(rows)
  if not per:raise ValueError('Empty listing')
  with ThreadPoolExecutor(max_workers=5) as pool:
   for more in pool.map(lambda n:makore_rows(page(SOURCES[src]+'?pages='+str(n))),range(2,math.ceil(count/per)+1)):rows.extend(more)
  if len(rows)<count:raise ValueError(f'Incomplete pagination: {len(rows)}/{count}')
  out=[convert(o,src) for o in rows]
 elif src in ['tickchak','sababa']:out=[convert(o,src) for o in ld(p)]
 elif src=='friends':
  posters={row.select_one('a.btn_info[href]')['href']:row.select_one('img[src]')['src'] for row in p.select('.search_show_row') if row.select_one('a.btn_info[href]') and row.select_one('img[src]')}
  links=list(posters)
  def read(url):
   q=page(url);h=q.find('h1');title=h.get_text(' ',strip=True) if h else '';desc=q.select_one('.wrap_brief');meta=q.find('meta',property='og:image');events=[]
   for block in q.select('.info_col'):
    header=block.select_one('.date_time_address');d=block.select_one('.date_wrap');v=block.select_one('.address_wrap')
    if not header or not d or 'אשדוד' not in header.get_text():continue
    tm=re.search(r'\b\d{2}:\d{2}\b',header.get_text());date=datetime.strptime(d.get_text(strip=True),'%d/%m/%y')
    events.append(make(src,title,date.date().isoformat(),tm[0] if tm else '',v.get_text(' ',strip=True) if v else 'אשדוד',url,desc.get_text('\n',strip=True) if desc else '',meta.get('content') if meta else posters.get(url)))
   return events
  with ThreadPoolExecutor(max_workers=6) as pool:
   for rows in pool.map(read,links):out.extend(rows)
 elif src=='leaan':
  script=p.select_one('#__NEXT_DATA__')
  if not script:raise ValueError('Source state unavailable')
  initial=json.loads(script.get_text())['props']['pageProps']['initialState']; states=[initial]
  for cat in initial.get('categories',[]):
   cp=page('https://www.leaan.co.il/category/'+cat['category_name'].replace(' ','-'));cs=cp.select_one('#__NEXT_DATA__')
   if cs:states.append(json.loads(cs.get_text())['props']['pageProps']['initialState'])
  for o in objects(states):
   if not isinstance(o.get('location'),dict) or o['location'].get('city')!='אשדוד' or not o.get('event_start'):continue
   dt=datetime.fromtimestamp(o['event_start'],Z);raw=', '.join(c.get('category_name','') for c in (o.get('categories') or {}).values())
   # Use only source-provided URLs; do not invent a detail route.
   url=o.get('redirect_url') or SOURCES[src]
   out.append(make(src,o.get('event_name') or o.get('name'),dt.date().isoformat(),dt.strftime('%H:%M'),o['location'].get('name','אשדוד'),url,o.get('description',''),image(o),raw,o['event_id']))
 out=[e for e in out if e and e['start_date']>=datetime.now(Z).date().isoformat()]
 if not out:raise ValueError('No source events parsed; retain previous records')
 return list({e['event_id']:e for e in out}.values())
def baseline():
 p=page('https://www.mevalim.co.il/ashdod/');out=[]
 for table in p.select('table'):
  for tr in table.select('tr'):
   name=tr.select_one('.rgbcode_table_shortcode_table_event_name');day=tr.select_one('.rgbcode_table_shortcode_table_date');tm=tr.select_one('.rgbcode_table_shortcode_table_time')
   if not all([name,day,tm]):continue
   d=tr.get('data-mvlm-event-date')
   if d:dt=datetime.strptime(d,'%d.%m.%y %H:%M')
   else:
    dd,mm=map(int,day.get_text(strip=True).split('.'));now=datetime.now(Z);yr=now.year if mm>=now.month else now.year+1;dt=datetime(yr,mm,dd)
   out.append(dict(title=name.get_text(' ',strip=True),start_date=dt.date().isoformat(),start_time=tm.get_text(strip=True)))
 if not out:raise ValueError('Mevalim comparison unavailable; no publication')
 return out
def equivalent(a,b):
 if a['start_date']!=b['start_date']:return False
 x=norm(a['title']).replace('באשדוד','');y=norm(b['title']).replace('באשדוד','')
 return x==y or (min(len(x),len(y))>=6 and (x in y or y in x))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--collect-only',action='store_true');ap.add_argument('--snapshot');args=ap.parse_args();OUT.mkdir(exist_ok=True)
 if args.snapshot:snap=json.loads(Path(args.snapshot).read_text())
 else:
  base=baseline();new=[];status={};excluded=[]
  for src in SOURCES:
   try:
    rows=collect(src);unique=[e for e in rows if not any(equivalent(e,b) for b in base)];excluded.extend(e for e in rows if e not in unique)
    if src in ['makore','tickchak']:
     with ThreadPoolExecutor(max_workers=8) as pool:unique=list(pool.map(detail,unique))
    new.extend(unique);status[src]={'ok':True,'read':len(rows),'not_in_mevalim':len(unique)}
   except Exception as ex:status[src]={'ok':False,'error':str(ex)[:300]}
   print(src,status[src],flush=True)
  snap={'at':datetime.now(Z).isoformat(),'sources':status,'mevalim_compared':len(base),'events':new,'excluded_mevalim':len(excluded)}
  (OUT/'ashdod-supplemental-snapshot.json').write_text(json.dumps(snap,ensure_ascii=False,indent=2)+'\n')
 if args.collect_only:return
 path=ROOT/'events-preview/ashdod/data/events.json';data=json.loads(path.read_text());old=data['events'];new=[];duplicates=0
 for e in snap['events']:
  match=next((n for n in new if equivalent(e,n) and e['start_time']==n['start_time']),None)
  if match:
   duplicates+=1;match.setdefault('crosscheck_sources',[]).append(e['content_source_url']);continue
  previous=next((p for p in old if p.get('event_id')==e['event_id']),{})
  for key in ['description','series_description','image_url','image_origin_url']:
   if not e.get(key) and previous.get(key):e[key]=previous[key];e['source_detail_incomplete']=True
  e['image_publishable']=e['image_verified']=e['image_represents_event']=bool(e.get('image_url'));new.append(e)
 removed=[];kept=[]
 for e in old:
  # Replace matching occurrences only. Never delete unrelated source records.
  match=next((n for n in new if equivalent(dict(title=e.get('title',''),start_date=e.get('start_date')),n) and str(e.get('start_time') or '')[:5]==n['start_time']),None)
  if match and e.get('source')!='mevalim_direct':removed.append(e)
  else:kept.append(e)
 data['events']=kept+new;data.setdefault('stats',{})['events']=len(data['events']);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 taxpath=OUT/'taxonomy.json';tax=json.loads(taxpath.read_text());cats=tax['primary_categories']
 for e in new:
  cat=next((c for c in cats if c['id']==e['category']),None)
  if not cat:cat=dict(id=e['category'],label={'workshop':'סדנאות ויצירה','community':'קהילה ופנאי'}.get(e['category'],e['category']),subcategories=[]);cats.append(cat)
  if not any(s['id']==e['subcategory'] for s in cat.get('subcategories',[])):cat.setdefault('subcategories',[]).append(dict(id=e['subcategory'],label=e['source_category'] or 'פעילויות',requires_mapping=e['taxonomy_review_required']))
 taxpath.write_text(json.dumps(tax,ensure_ascii=False,indent=2)+'\n')
 report={k:v for k,v in snap.items() if k!='events'};report.update(published_occurrences=len(new),replaced=len(removed),duplicates_merged=duplicates,with_image=sum(bool(e.get('image_url')) for e in new),with_text=sum(bool(e.get('description')) for e in new))
 (OUT/'ashdod-supplemental-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(OUT/'ashdod-supplemental-replaced.json').write_text(json.dumps({'at':snap['at'],'events':removed},ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
