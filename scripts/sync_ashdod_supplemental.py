#!/usr/bin/env python3
"""Source-authoritative Ashdod supplements. No editorial text/image gating."""
import argparse, json, re, math, hashlib
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urljoin, urlparse, parse_qs, unquote
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup
from sync_mevalim_ashdod_direct import clean, norm, same_show, venue_key, remove_conflicting_address
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'events-preview/admin/data'; Z=ZoneInfo('Asia/Jerusalem')
SOURCE_WARNINGS={}
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
   if unquote(urlparse(o.get('url','')).path).rstrip('/')==unquote(urlparse(a['href']).path).rstrip('/'):
    o['genre']=', '.join(t.get_text(strip=True) for t in tags)
    if im:o['image']=urljoin(SOURCES['makore'],im['src'])
 return rows
def image(o):
 x=o.get('image') or o.get('vivenu_image')
 if isinstance(x,list):x=x[0] if x else None
 if isinstance(x,dict):x=x.get('url') or x.get('contentUrl')
 return x
RULES=[(r'כנס|פאנל','conference','conference'),(r'קולינריה|\bאוכל\b|בישול','food','food-events'),(r'סטנד.?אפ|standup','standup','standup'),(r'סדנ|ציור|פיסול|קרמיקה','workshop','creative'),(r'הרצא|מרצה|פאנל|כנס|lecture','lecture','lecture'),(r'תערוכ|מוזיאון|מוזאון','exhibition','exhibition'),(r'שעת סיפור','kids','story-time'),(r'ילדים|ילד|קטנטנ|פעוט|משפחה|childrens','kids','kids-activities'),(r'בלט|מחול|טנגו|פלמנקו','music','dance'),(r'תיאטרון|תאטרון|הצג|מחזמר|קומדיה|theater','theatre','theatre'),(r'מוזיקה|מוסיקה|קונצרט|concert|שיר|להקה|זמר|מופע|הופע','music','live'),(r'סיור|טיול','tour','guided-tours'),(r'ספורט|פילאטיס|יוגה','sport','activities'),(r'גיל השלישי|גמלאי','seniors','seniors-activities')]
def category(raw,title):
 # Classify festival-branded productions by their actual event type.
 if re.search(r'מיסייה אלבר',title):return 'theatre','one-person-show'
 if re.search(r'סן רמו בעברית|תרועת הפסטיבלים',title):return 'music','tribute-shows'
 for text in [raw,title]:
  for pattern,cat,sub in RULES:
   if not re.search(pattern,text,re.I):continue
   if text==title and cat=='kids' and not re.search(r'\bילדים\b|קטנטנ|פעוט|לכל המשפחה|למשפחות|childrens|שעת סיפור',text,re.I):continue
   if text==title and cat=='music' and sub=='live' and not re.search(r'מוזיק|מוסיק|קונצרט|concert|שיר|להקה|זמר|הופעות חיות|הופעה חיה',text,re.I):continue
   return cat,sub
 return 'community','source-'+hashlib.sha256((raw or 'פעילות').encode()).hexdigest()[:10]
def source_placeholder(url):return any(x in str(url or '') for x in ['/placeholders/','/images/live/more/eventNew.jpg','/images/artists/artistShadow.png'])
def make(src,title,date,time,venue,url,description='',img=None,raw='',uid=None):
 text=BeautifulSoup(description or '','html.parser').get_text('\n',strip=True);text,removed=remove_conflicting_address(text);cat,sub=category(raw,title)
 if cat=='community':cat,sub=category(raw,title+' '+text[:700])
 eid=src+'_as_'+hashlib.sha256((str(uid or url)+date+time).encode()).hexdigest()[:18]
 e=dict(event_id=eid,source='supplemental_'+src,city='אשדוד',title=clean(title),start_date=date,start_time=time,venue=clean(venue),status='active',category=cat,subcategory=sub,source_category=raw,source_subcategory=raw,description=text,series_description=text,image_url=img,image_origin_url=img,image_source=src,image_verified=bool(img),image_publishable=bool(img),image_represents_event=bool(img),image_strategy='source_event_image_copy',image_rights_status='publisher_directed_source_reuse',ticket_url=url,purchase_url=url,content_source_url=url,source_content_authoritative=True,content_locked=True,source_priority=2,last_imported_at=datetime.now(Z).isoformat(),internal_notes=[],taxonomy_review_required=sub.startswith('source-'))
 e['source_image_kind']='source_placeholder' if source_placeholder(img) else 'source_event_photo' if img else 'not_available'
 if source_placeholder(img):e['image_verified']=e['image_publishable']=e['image_represents_event']=False
 if removed:e['removed_conflicting_source_addresses']=removed
 if e['taxonomy_review_required']:e['internal_notes'].append('נפתחה קטגוריה/תת קטגוריה חדשה; שיוך מוצע לקהילה ופנאי: '+(raw or 'ללא קטגוריה במקור'))
 return e
def convert(o,src):
 loc=o.get('location') or {}; address=loc.get('address') or {};city=address.get('addressLocality','') if isinstance(address,dict) else str(address)
 if city and not any(x in clean(city).lower() for x in ['אשדוד','ashdod']):return None
 dt=datetime.fromisoformat(o['startDate'].replace('Z','+00:00'));dt=dt.astimezone(Z) if dt.tzinfo else dt.replace(tzinfo=Z)
 offers=o.get('offers') or {};offers=offers[0] if isinstance(offers,list) and offers else offers
 url=o.get('url') or str(o.get('@id','')).split('#')[0] or offers.get('url','')
 e=make(src,o['name'],dt.date().isoformat(),dt.strftime('%H:%M'),loc.get('name','אשדוד'),url,o.get('description',''),image(o),str(o.get('genre') or o.get('additionalType') or ({'concerts':'הופעות חיות','theater':'תיאטרון','standup':'סטנדאפ','childrens-shows':'ילדים ומשפחה','lectures':'הרצאות'}.get(urlparse(url).path.split('/')[1],''))),o.get('@id') or url)
 if 'Cancelled' in str(o.get('eventStatus','')):e['status']='cancelled'
 elif 'Postponed' in str(o.get('eventStatus','')):e['status']='postponed'
 e['purchase_url']=e['ticket_url']=offers.get('url') or url
 if offers.get('price') is not None:e['price_min_ils']=offers['price']
 if 'SoldOut' in offers.get('availability',''):e['ticket_status']='sold_out'
 return e
def detail(e):
 e.pop('source_detail_error',None)
 try:
  p=page(e['content_source_url']); meta=p.find('meta',property='og:image')
  if meta and meta.get('content') and e['source']!='supplemental_makore':e['image_url']=e['image_origin_url']=urljoin(e['content_source_url'],meta['content'])
  matches=[x for x in ld(p) if norm(x.get('name'))==norm(e['title'])]
  if matches:
   o=matches[0]
   if o.get('description'):e['description']=e['series_description']=BeautifulSoup(o['description'],'html.parser').get_text('\n',strip=True)
   if image(o):e['image_url']=e['image_origin_url']=image(o)
  if e['source']=='supplemental_tickchak':
   node=p.select_one('#__NEXT_DATA__')
   if node:
    original_event=json.loads(node.get_text()).get('props',{}).get('pageProps',{}).get('initialState',{}).get('event',{})
    production=original_event.get('link');purchase=original_event.get('pageUrl');production=production or purchase
    if purchase and purchase.startswith('https://'):e['ticket_url']=e['purchase_url']=purchase
    if original_event.get('description'):e['description']=e['series_description']=BeautifulSoup(original_event['description'],'html.parser').get_text('\n',strip=True)
    if production and production.startswith('https://') and urlparse(production).hostname!='live.tickchak.co.il':
     primary=page(production);e['original_production_url']=production;im=primary.find('meta',property='og:image')
     if im and im.get('content'):e['image_url']=e['image_origin_url']=urljoin(production,im['content']);e['image_source']='original_production'
     body=primary.select_one('.event-description, .event_description, .show-description, .txt_container, [itemprop=description]')
     original_text=body.get_text('\n',strip=True) if body else ''
     meta_description=primary.find('meta',attrs={'name':'description'})
     if not original_text and meta_description:original_text=meta_description.get('content','')
     if original_text:e['network_description']=e['description'];e['description']=e['series_description']=original_text
     e['original_source_checked_at']=datetime.now(Z).isoformat()
  # Read the source's displayed production description, never the site navigation.
  for selector in ['.wrap_brief','.event-description','[itemprop="description"]']:
   block=p.select_one(selector)
   if block and block.get_text(strip=True):e['description']=e['series_description']=block.get_text('\n',strip=True);break
  if e['source']=='supplemental_makore' and 'smarticket.co.il' in urlparse(e['ticket_url']).hostname:
   original=page(e['ticket_url']);block=original.select_one('.txt_container');im=original.find('meta',property='og:image')
   primary_time=original.select_one('.event-time');primary_date=original.select_one('.breadcrumb_event')
   if primary_time:
    m=re.search(r'\d{2}:\d{2}',primary_time.get_text())
    if m:e['start_time']=m[0]
   if primary_date:
    m=re.search(r'\d{2}/\d{2}/\d{4}',primary_date.get_text())
    if m:e['start_date']=datetime.strptime(m[0],'%d/%m/%Y').date().isoformat()
   if block:e['description']=e['series_description']=block.get_text('\n',strip=True).removeprefix('פרטים נוספים').strip();e['source_detail_text']=e['description']
   if im and im.get('content'):e['image_url']=e['image_origin_url']=urljoin(e['ticket_url'],im['content']);e['image_source']='smarticket'
  e['detail_checked_at']=datetime.now(Z).isoformat()
 except Exception as ex:
  e['source_detail_error']=str(ex)[:200]
  if isinstance(ex,requests.HTTPError) and ex.response is not None and ex.response.url==e.get('purchase_url'):
   e['unavailable_original_purchase_url']=e['purchase_url'];e['purchase_url']=None;e['ticket_url']=e['content_source_url'];e['source_purchase_confirmation_pending']=True
 img=e.get('image_url')
 e['source_image_kind']='source_placeholder' if source_placeholder(img) else 'source_event_photo' if img else 'not_available'
 e['image_verified']=e['image_publishable']=e['image_represents_event']=bool(img) and not source_placeholder(img)
 e['description'],removed=remove_conflicting_address(e.get('description'));e['series_description']=e['description']
 return e

def friends_prices(e,q):
 price_nodes=q.select('.price_item');texts=[x.get_text(' ',strip=True) for x in price_nodes]
 if texts:e['source_price_text']='\n'.join(texts)
 for x in texts:
  m=re.search(r'₪\s*(\d+(?:\.\d+)?)',x)
  if not m:continue
  if 'מחיר רגיל' in x:e['price_min_ils']=float(m[1]);e['price_is_starting']=True
  elif 'ההסתדרות' in x:e['member_price_min_ils']=float(m[1])
 duration=re.search(r'\b(\d+(?:\s*[-–]\s*\d+)?)\s*(דקות|שעות)\b',q.get_text(' ',strip=True))
 if duration:
  e['source_duration_text']=duration[0]
  if duration[1].isdigit():e['duration_minutes']=int(duration[1])*(60 if duration[2]=='שעות' else 1)
 extra='\n\n'.join(x for x in [e.get('source_duration_text'),e.get('source_price_text')] if x)
 if extra and extra not in e['description']:e['description']=e['series_description']=e['description']+'\n\n'+extra
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
 elif src in ['tickchak','sababa']:
  rows=ld(p)
  if src=='sababa':
   seen={SOURCES[src]};pending=[urljoin(SOURCES[src],a['href']) for a in p.select('a[rel=next],.pagination a[href],a.page-numbers[href]')]
   while pending:
    url=pending.pop(0)
    if url in seen or urlparse(url).hostname!=urlparse(SOURCES[src]).hostname:continue
    seen.add(url);q=page(url);rows.extend(ld(q));pending.extend(urljoin(url,a['href']) for a in q.select('a[rel=next],.pagination a[href],a.page-numbers[href]'))
  out=[convert(o,src) for o in rows]
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
   return [friends_prices(e,q) for e in events]
  with ThreadPoolExecutor(max_workers=6) as pool:
   for rows in pool.map(read,links):out.extend(rows)
 elif src=='leaan':
  script=p.select_one('#__NEXT_DATA__')
  if not script:raise ValueError('Source state unavailable')
  initial=json.loads(script.get_text())['props']['pageProps']['initialState']; states=[initial]
  sitemap=page('https://www.leaan.co.il/site-map');event_links=list(dict.fromkeys(urljoin(SOURCES[src],a['href']) for a in sitemap.select('a[href*="/events/"]')));routes={urlparse(u).path.rsplit('/',1)[-1]:u for u in event_links};artist_links=[urljoin(SOURCES[src],a['href']) for a in sitemap.select('a[href*="/category/"]') if len(urlparse(a['href']).path.strip('/').split('/'))>=3];links=list(dict.fromkeys(event_links+artist_links))
  def state(url):
   q=page(url);node=q.select_one('#__NEXT_DATA__')
   if not node:raise ValueError('Missing Leaan source state: '+url)
   data=json.loads(node.get_text())['props']['pageProps']
   primary={'data':data.get('data'),'pageData':data.get('initialState',{}).get('pageData',{})}
   for event in objects(primary):
    if isinstance(event.get('location'),dict) and event['location'].get('city')=='אשדוד' and event.get('event_start'):event['_source_page']=url
   return data
  def safe_state(url):
   try:return state(url)
   except Exception as ex:return {'_fetch_error':str(ex)[:200]}
  with ThreadPoolExecutor(max_workers=8) as pool:extra=list(pool.map(safe_state,links))
  SOURCE_WARNINGS[src]=[x['_fetch_error'] for x in extra if '_fetch_error' in x];states.extend(x for x in extra if '_fetch_error' not in x)
  for cat in initial.get('categories',[]):
   cp=page('https://www.leaan.co.il/category/'+cat['category_name'].replace(' ','-'));cs=cp.select_one('#__NEXT_DATA__')
   if cs:states.append(json.loads(cs.get_text())['props']['pageProps']['initialState'])
  for o in objects(states):
   if not isinstance(o.get('location'),dict) or o['location'].get('city')!='אשדוד' or not o.get('event_start'):continue
   dt=datetime.fromtimestamp(o['event_start'],Z);raw=', '.join(c.get('category_name','') for c in (o.get('categories') or {}).values())
   # Use only source-provided URLs; do not invent a detail route.
   url=o.get('redirect_url') or routes.get(str(o.get('id'))) or o.get('_source_page') or SOURCES[src]
   out.append(make(src,o.get('event_name') or o.get('name'),dt.date().isoformat(),dt.strftime('%H:%M'),o['location'].get('name','אשדוד'),url,o.get('description',''),image(o),raw,o['event_id']))
 out=[e for e in out if e and e['start_date']>=datetime.now(Z).date().isoformat()]
 if not out:raise ValueError('No source events parsed; retain previous records')
 return list({e['event_id']:e for e in out}.values())
def baseline():
 p=page('https://www.mevalim.co.il/ashdod/');out=[]
 config=re.search(r'var mevalimAjax = (\{.*?\});',str(p));ajax=json.loads(config[1]) if config else None
 for button in p.select('.mevalim_load_more_events__btn'):
  if button.get('data-is-passed')!='0':continue
  if not ajax:raise ValueError('Mevalim pagination configuration missing')
  n=2
  while True:
   r=requests.post(ajax['url'],data={'action':'mevalim_load_more_events','nonce':ajax['nonce'],'is_passed':'0','post_id':button['data-table-id'],'page':n,'source_type':button.get('data-source-type','')},timeout=40);r.raise_for_status();j=r.json()
   if not j.get('success'):raise ValueError('Mevalim load-more failed')
   fragment=BeautifulSoup(j.get('data',{}).get('content',''),'html.parser');table=p.new_tag('table')
   for row in fragment.select('tr'):table.append(row)
   p.append(table)
   if not j.get('data',{}).get('canLoadMore'):break
   n+=1
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
 if a.get('start_time') and b.get('start_time') and a['start_time']!=b['start_time']:return False
 x=norm(a['title']).replace('באשדוד','').replace('תאטרון','תיאטרון').replace('אימי','אמי');y=norm(b['title']).replace('באשדוד','').replace('תאטרון','תיאטרון').replace('אימי','אמי')
 core=lambda t:norm(re.split(r'\s[-–|]\s',t.replace('באשדוד',''))[0]).replace('תאטרון','תיאטרון').replace('אימי','אמי')
 ac,bc=core(a['title']),core(b['title']);same_core=len(ac)>=4 and ac==bc
 named=[['ישראלי','ישראלית'],['רוסיה','רוסי'],['נתי הגעתי']]
 tags=lambda t:{i for i,terms in enumerate(named) if any(term in t for term in terms)}
 if tags(a['title']) and tags(b['title']) and tags(a['title'])!=tags(b['title']):same_core=False
 words=lambda t:set(re.findall(r'[א-ת]{2,}',t.replace('באשדוד','')))
 ax,by=words(a['title']),words(b['title']);tokens=len(ax&by)>=3 and (ax<=by or by<=ax)
 return x==y or same_core or tokens or (min(len(x),len(y))>=6 and (x in y or y in x))
def preferred_match(e,m):
 if equivalent(e,m):return True
 if not str(e.get('source','')).startswith('supplemental_') or venue_key(e.get('venue'))!=venue_key(m.get('venue')):return False
 if not equivalent({'title':e['title'],'start_date':e['start_date']},m):return False
 try:
  minute=lambda t:int(t[:2])*60+int(t[3:5])
  return abs(minute(e['start_time'])-minute(m['start_time']))<=60
 except (ValueError,TypeError,KeyError):return False
def ticket_identity(e):
 u=e.get('purchase_url') or e.get('ticket_url') or e.get('content_source_url') or '';p=urlparse(u);q=parse_qs(p.query);m=re.search(r'/event/(\d+)',p.path)
 uid=q.get('id') or q.get('event') or ([m[1]] if m else None)
 return (p.hostname,str(uid[0])) if uid else (p.hostname,p.path.rstrip('/'))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--collect-only',action='store_true');ap.add_argument('--snapshot');args=ap.parse_args();OUT.mkdir(exist_ok=True)
 if args.snapshot:
  snap=json.loads(Path(args.snapshot).read_text())
  (OUT/'ashdod-supplemental-snapshot.json').write_text(json.dumps(snap,ensure_ascii=False,indent=2)+'\n')
 else:
  base=baseline();new=[];status={};excluded=[]
  for src in SOURCES:
   try:
    rows=collect(src);unique=[e for e in rows if not any(equivalent(e,b) for b in base)];excluded.extend(e for e in rows if e not in unique)
    if src in ['makore','tickchak']:
     with ThreadPoolExecutor(max_workers=8) as pool:unique=list(pool.map(detail,unique))
    new.extend(unique);status[src]={'ok':True,'read':len(rows),'not_in_mevalim':len(unique),'detail_fetch_failures':len(SOURCE_WARNINGS.get(src,[])),'card_detail_errors':sum(bool(e.get('source_detail_error')) for e in unique)}
   except Exception as ex:status[src]={'ok':False,'error':str(ex)[:300]}
   print(src,status[src],flush=True)
  snap={'at':datetime.now(Z).isoformat(),'sources':status,'mevalim_compared':len(base),'events':new,'excluded_mevalim':len(excluded)}
  (OUT/'ashdod-supplemental-snapshot.json').write_text(json.dumps(snap,ensure_ascii=False,indent=2)+'\n')
 if args.collect_only:return
 path=ROOT/'events-preview/ashdod/data/events.json';data=json.loads(path.read_text());old=data['events'];new=[];duplicates=0
 for e in sorted(snap['events'],key=lambda e:{'supplemental_friends':0,'supplemental_leaan':1,'supplemental_tickchak':2,'supplemental_sababa':3,'supplemental_makore':4}.get(e['source'],5)):
  match=next((n for n in new if equivalent(e,n) and e['start_time']==n['start_time']),None)
  if match:
   duplicates+=1;match.setdefault('crosscheck_sources',[]).append(e['content_source_url']);continue
  previous=next((p for p in old if p.get('event_id')==e['event_id']),{})
  for key in ['description','series_description','image_url','image_origin_url']:
   if not e.get(key) and previous.get(key):e[key]=previous[key];e['source_detail_incomplete']=True
  e['image_publishable']=e['image_verified']=e['image_represents_event']=bool(e.get('image_url'));new.append(e)
 removed=[];kept=[]
 preferred=[e for e in old if e.get('source')=='mevalim_direct']
 new=[e for e in new if not any(preferred_match(e,m) for m in preferred)]
 for e in old:
  # Replace matching occurrences only. Never delete unrelated source records.
  match=next((n for n in new if e.get('event_id')==n['event_id']),None)
  if not match:match=next((n for n in new if e.get('start_date')==n['start_date'] and ((ticket_identity(e)==ticket_identity(n) and ticket_identity(n)[0]) or (equivalent(dict(title=e.get('title',''),start_date=e.get('start_date')),n) and str(e.get('start_time') or '')[:5]==n['start_time']))),None)
  if not match and e.get('source')!='mevalim_direct' and any(preferred_match(e,m) for m in preferred):match=True
  if match and e.get('source')!='mevalim_direct':removed.append(e)
  else:kept.append(e)
 data['events']=kept+new;data['generated_at']=datetime.now(Z).isoformat();data['generatedAt']=data['generated_at'];data.setdefault('stats',{})['events']=len(data['events']);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 taxpath=OUT/'taxonomy.json';tax=json.loads(taxpath.read_text());cats=tax['primary_categories']
 for e in new:
  cat=next((c for c in cats if c['id']==e['category']),None)
  if not cat:cat=dict(id=e['category'],label={'workshop':'סדנאות ויצירה','community':'קהילה ופנאי','tour':'טיולים וסיורים'}.get(e['category'],e['category']),subcategories=[]);cats.append(cat)
  if not any(s['id']==e['subcategory'] for s in cat.get('subcategories',[])):cat.setdefault('subcategories',[]).append(dict(id=e['subcategory'],label=e['source_category'] or 'פעילויות',requires_mapping=e['taxonomy_review_required']))
 tax.setdefault('source_taxonomies',{})['ashdod_supplemental']={'label':'מקורות ארציים – השלמות לאשדוד','categories':[{'label':raw or 'ללא קטגוריה במקור','source':src,'requires_mapping':not raw} for src,raw in sorted({(e['source'],e.get('source_category','')) for e in new})]}
 taxpath.write_text(json.dumps(tax,ensure_ascii=False,indent=2)+'\n')
 report={k:v for k,v in snap.items() if k!='events'};report['source_detail_issues']=[{'event_id':e['event_id'],'title':e['title'],'url':e.get('content_source_url'),'error':e['source_detail_error']} for e in new if e.get('source_detail_error')];report.update(published_occurrences=len(new),replaced=len(removed),duplicates_merged=duplicates,with_image=sum(bool(e.get('image_url')) for e in new),with_text=sum(bool(e.get('description')) for e in new),source_placeholder_images=sum(source_placeholder(e.get('image_url')) for e in new),replaced_legacy_occurrences=sum(not str(e.get('source','')).startswith('supplemental_') for e in removed))
 (OUT/'ashdod-supplemental-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(OUT/'ashdod-supplemental-replaced.json').write_text(json.dumps({'at':snap['at'],'events':removed},ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
