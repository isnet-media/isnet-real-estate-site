"""TLVNET factual event intake. No AI calls, copied descriptions or unlicensed images."""
import json,re,hashlib,urllib.request,concurrent.futures
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from urllib.parse import urljoin,urlparse,quote
from pathlib import Path
from bs4 import BeautifulSoup
TZ=ZoneInfo('Asia/Jerusalem');NOW=datetime.now(TZ);STAMP=NOW.isoformat();MONTHS=dict(zip(['ינואר','פברואר','מרץ','אפריל','מאי','יוני','יולי','אוגוסט','ספטמבר','אוקטובר','נובמבר','דצמבר'],range(1,13)))
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'events-preview/tel-aviv/data/events.json'
def fetch(url):
 url=quote(url,safe=':/?=&%+#');req=urllib.request.Request(url,headers={'User-Agent':'TLVNET public event directory/1.0'})
 with urllib.request.urlopen(req,timeout=25) as r:return BeautifulSoup(r.read().decode('utf-8'),'html.parser')
def item(title,dt,venue,address,category,source,url,note='',price=None):
 if not NOW<=dt<=NOW+timedelta(days=45):return None
 if urlparse(url).scheme!='https':return None
 return dict(id=hashlib.sha256((source+url+dt.isoformat()).encode()).hexdigest()[:20],title=title[:240],start=dt.isoformat(),venue=venue,address=address,category=category,source=source,source_url=url,verified_at=STAMP,note=note,price=price,image=None,image_rights='not_supplied',city='tel-aviv',publication_status='published')
def lessin():
 u='https://www.lessin.co.il/הצגות/';b=fetch(u);out=[]
 for tr in b.select('tr.showlistitem'):
  cells=tr.find_all('td',recursive=False);a=tr.select_one('td[style*="width: 100%"] a');t=cells[2].get_text(' ',strip=True) if len(cells)>2 else ''
  if not a or not re.fullmatch(r'\d{2}:\d{2}',t):continue
  dt=datetime.strptime(tr['data-date']+' '+t,'%d-%m-%Y %H:%M').replace(tzinfo=TZ);hall=cells[3].get_text(' ',strip=True)
  if hall not in ['אולם 1','אולם 2','פואיה בית ליסין']:continue
  sold='אזל' in tr.get_text(' ',strip=True)
  out.append(item(a.get_text(' ',strip=True),dt,'בית ליסין · '+hall,'דיזנגוף 101, כניסה מפרישמן 44, תל אביב','tour' if 'סיור' in a.get_text() else 'theatre','בית ליסין',urljoin(u,a['href']),'אזלו הכרטיסים לפי המקור' if sold else 'מחיר וזמינות באתר התיאטרון'))
 return [x for x in out if x]
def ariela():
 u='https://beitariela.smarticket.co.il/';b=fetch(u);out=[]
 for a in b.select('.show_cube > a'):
  title=a.select_one('.details .h2');d=a.select_one('.show_date');t=a.select_one('.event-time');v=a.select_one('.theater_name')
  if not all([title,d,t,v]) or 'מקוון' in a.get_text() or 'VOD' in a.get_text():continue
  m=re.search(r'(\d{1,2}) ב('+'|'.join(MONTHS)+r') (\d{4})',d.get_text(' ',strip=True));tm=re.search(r'\d{2}:\d{2}',t.get_text())
  if not m or not tm or v.get_text(' ',strip=True)!='בית אריאלה':continue
  dt=datetime(int(m[3]),MONTHS[m[2]],int(m[1]),*map(int,tm[0].split(':')),tzinfo=TZ);name=title.get_text(' ',strip=True)
  cat='kids' if any(z in name for z in ['לגילי','כיתות','ילדים']) else 'workshop' if any(z in name for z in ['סדנ','כתיבה','לכתוב']) else 'lecture'
  out.append(item(name,dt,'בית אריאלה','שדרות שאול המלך 25, תל אביב',cat,'בית אריאלה',urljoin(u,a['href']),'מפגש במסגרת סדרה; יש לבדוק אפשרות הרשמה למפגש בודד ומחיר במקור'))
 return [x for x in out if x]
def levontin():
 u='https://levontin7.com/';b=fetch(u);links={a['href']:a for a in b.select('.fat-event-title a[data-s]')};out=[]
 for url,a in list(links.items())[:10]:
  dt=datetime.fromtimestamp(int(a['data-s']),TZ)
  if not NOW<=dt<=NOW+timedelta(days=45):continue
  # Event title in listing is truncated: only a complete detail-page title is accepted.
  try:
   detail=fetch(url);h=detail.select_one('h1');name=h.get_text(' ',strip=True) if h else (detail.title.get_text(' ',strip=True).split(' – Levontin')[0] if detail.title else '')
   if len(name)<3 or '…' in name:continue
   # Use the explicitly displayed performance time, not opening doors.
   card=a.find_parent(class_='fat-event-item')
   if not card:card=a.find_parent(class_='fat-event')
   time=card.select_one('.begin-time') if card else None
   if time:
    m=re.search(r'\d{2}:\d{2}',time.get_text(' ',strip=True))
    if m:dt=dt.replace(hour=int(m[0][:2]),minute=int(m[0][3:]))
   else:continue
   out.append(item(name,dt,'לבונטין 7','לבונטין 7, תל אביב','music','לבונטין 7',url,'מחיר וזמינות באתר המקום'))
  except Exception:continue
 return [x for x in out if x]
# Only complete visible occurrences are published. Hidden legacy calendars are ignored.
def cameri():
 u='https://www.cameri.co.il/';b=fetch(u);out=[]
 m=re.search(r"let lastDate\s*=\s*\{\s*day:\s*'(\d+)',\s*month:\s*'(\d+)',\s*year:\s*'(\d+)'",str(b))
 if not m:raise ValueError('calendar_year_missing')
 last_month,last_year=int(m[2]),int(m[3])
 for day in b.select('.day-box'):
  date=day.select_one('.day-date')
  if not date or not re.fullmatch(r'\d{1,2}\.\d{1,2}',date.get_text(strip=True)):continue
  d,mo=map(int,date.get_text(strip=True).split('.'));year=last_year-(mo>last_month)
  for show in day.select('.show-item'):
   title=show.select_one('h3');page=show.select_one('a.show-img-link[href]');kind=show.select_one('.category')
   if not title or not page or not kind or kind.get_text(' ',strip=True) not in ['הצגות הקאמרי','הצגה אורחת','מחזמר']:continue
   for a in show.select('.shows-times a[href*="tickets.cameri.co.il/order/"]'):
    time=a.get_text(strip=True)
    if not re.fullmatch(r'\d{2}:\d{2}',time):continue
    dt=datetime(year,mo,d,*map(int,time.split(':')),tzinfo=TZ)
    e=item(title.get_text(' ',strip=True),dt,'הקאמרי','שדרות שאול המלך 19, תל אביב','theatre','הקאמרי',a['href'],'מחיר, אולם וזמינות באישור ההזמנה')
    if e:e['production_url']=urljoin(u,page['href']);out.append(e)
 return out

def gesher():
 u='https://www.gesher-theatre.co.il/he/company/a/calendar/';b=fetch(u);out=[]
 full_dates=[]
 for x in b.select('ul.allshows li'):
  try:full_dates.append(datetime.strptime(x.get_text(strip=True),'%d/%m/%Y %H:%M').replace(tzinfo=TZ))
  except ValueError:pass
 for row in b.select('.showRow'):
  get=lambda sel:row.select_one(sel).get_text(' ',strip=True) if row.select_one(sel) else ''
  title=get('.showItemListName');date=get('.showItemListDate').replace('תאריך:','').strip();time=get('.showItemListTime');hall=get('.showItemListLocation')
  date=re.search(r'(\d{1,2})\.(\d{1,2})',date)
  a=row.select_one('a[href*="DateID="]')
  if not date or not title or not a or not re.fullmatch(r'\d{2}:\d{2}',time):continue
  # Reject touring venues: this calendar is scoped to Gesher's own Jaffa halls.
  if hall not in ['תיאטרון גשר','אולם נגה','אולם נוגה','אולם האנגר גשר','האנגר גשר','אולם גשר']:continue
  matches=[dt for dt in full_dates if (dt.day,dt.month,dt.hour,dt.minute)==(int(date[1]),int(date[2]),int(time[:2]),int(time[3:]))]
  if len(matches)!=1:continue
  e=item(title,matches[0],'גשר · '+hall,'תיאטרון גשר, '+hall+', תל אביב–יפו','theatre','גשר',urljoin(u,a['href']),'כתובת האולם, מחיר וזמינות באישור ההזמנה')
  if e:out.append(e)
 return out

CLASSICAL=re.compile(r'קונצרט|קאמרי|רסיטל|סימפוני|תזמורת|פילהרמוני|באך|בטהובן|מוצרט|שופן|ברהמס|שוברט|ויוואלדי')
NOT_MUSIC=re.compile(r'השקת הספר|סדנ[אה]|הרצאה|סטנדאפ|רגע של אמת|רבקה מיכאלי|טייכר|זרחוביץ|פה דה דה|Pas De Deux',re.I)
def music_kind(title):return 'classical' if CLASSICAL.search(title) else 'live'

def blumental():
 u='https://fbmc.co.il/shows/';b=fetch(u);out=[]
 for month in b.select('.shows-schedule-month-container[data-month]'):
  ym=month['data-month']
  if not re.fullmatch(r'\d{4}-\d{2}',ym):continue
  year,mo=map(int,ym.split('-'))
  for show in month.select('.shows-schedule-show'):
   title=show.select_one('.show-name');a=show.select_one('a.no-underline[href*="/show/"]');venue=show.select_one('.schedule-day-date .flagship-link');date=show.select_one('.schedule-day-date span')
   if not all([title,a,venue,date]) or venue.get_text(strip=True)!='סטודיו אנט':continue
   name=title.get_text(' ',strip=True)
   if NOT_MUSIC.search(name):continue
   times=re.findall(r'(?<!\d)([0-2]\d:[0-5]\d)(?!\d)',a.get_text(' ',strip=True));dm=re.fullmatch(r'(\d{1,2})\.(\d{1,2})',date.get_text(strip=True))
   if len(times)!=1 or not dm or int(dm[2])!=mo:continue
   dt=datetime(year,mo,int(dm[1]),*map(int,times[0].split(':')),tzinfo=TZ)
   e=item(name,dt,'סטודיו אנט · פליציה בלומנטל','שביל המרץ 2, תל אביב–יפו','music','פליציה בלומנטל',a['href'],'מחיר וזמינות אצל המארגנים')
   if e:e['concert_kind']=music_kind(name);out.append(e)
 return out

def hatarbut():
 u='https://www.hatarbut.co.il/';b=fetch(u);out=[]
 candidates=[]
 for article in b.select('article.type-event'):
  a=article.select_one('.eo-event-title a[href]');date=article.select_one('.eo-event-date')
  if not a or not date:continue
  name=a.get_text(' ',strip=True)
  if NOT_MUSIC.search(name):continue
  dm=re.fullmatch(r'(\d{2})\.(\d{2})\.(\d{2})',date.get_text(strip=True))
  if not dm:continue
  day=datetime(2000+int(dm[3]),int(dm[2]),int(dm[1]),tzinfo=TZ)
  if not NOW.date()<=day.date()<=(NOW+timedelta(days=45)).date():continue
  candidates.append((name,day,a['href']))
 def detail(x):
  name,day,url=x;page=fetch(url);head=page.select_one('h1.elementor-heading-title')
  if not head or head.get_text(' ',strip=True)!=name:return None
  program=' '.join(x.get_text(' ',strip=True) for x in page.select('.elementor-widget-text-editor'))
  if not re.search(r'קונצרט|תזמורת|פילהרמוני|מוזיק|מוסיק|פסנתר|גיטר|שירים|אלבום|ג[׳\']?אז|JAZZ',name+' '+program,re.I):return None
  fields=[t.get_text(' ',strip=True) for t in page.select('span.elementor-heading-title')]
  times=[t for t in fields if re.fullmatch(r'\d{2}:\d{2}',t)];halls=[t for t in fields if t in ['צוקר','לאוי','לואי','Lowy','Zucker']]
  if len(times)!=1 or len(halls)!=1:return None
  dt=day.replace(hour=int(times[0][:2]),minute=int(times[0][3:]));hall='צוקר' if halls[0] in ['צוקר','Zucker'] else 'לאוי'
  e=item(name,dt,'היכל התרבות · אולם '+hall,'הוברמן 1, תל אביב','music','היכל התרבות',url,'מחיר וזמינות אצל המארגנים')
  if e:e['concert_kind']=music_kind(name)
  return e
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
  futures=[pool.submit(detail,x) for x in candidates]
  for f in concurrent.futures.as_completed(futures):
   try:
    e=f.result()
    if e:out.append(e)
   except Exception:pass
 return out

def main():
 old=json.loads(OUT.read_text()) if OUT.exists() else {'events':[]};events=[];reports=[]
 adapters={'בית ליסין':lessin,'בית אריאלה':ariela,'לבונטין 7':levontin,'הקאמרי':cameri,'גשר':gesher,'פליציה בלומנטל':blumental,'היכל התרבות':hatarbut}
 inventory_path=BASE/'events-preview/tel-aviv/data/culture-sources.json'
 requested={v.get('collector') for v in json.loads(inventory_path.read_text())['venues']} if inventory_path.exists() else set(adapters)
 requested.add('בית אריאלה')
 with concurrent.futures.ThreadPoolExecutor(max_workers=7) as pool:
  futures={pool.submit(fn):name for name,fn in adapters.items() if name in requested}
  for f in concurrent.futures.as_completed(futures):
   name=futures[f]
   try:
    rows=f.result()
    if not rows:raise ValueError('empty_source')
    events+=rows;reports.append({'name':name,'status':'ok','count':len(rows),'checked_at':STAMP});print(json.dumps(reports[-1],ensure_ascii=False),flush=True)
   except Exception as e:
    previous=[x for x in old['events'] if x['source']==name and datetime.fromisoformat(x['start'])>NOW and (NOW-datetime.fromisoformat(x['verified_at'])).total_seconds()<172800];events+=previous;reports.append({'name':name,'status':'failed','retained':len(previous),'error':type(e).__name__,'attempted_at':STAMP})
 from tlvnet_publicity import enrich_events_images
 previous={e['source_url']:e for e in old.get('events',[]) if e.get('image_rights')=='user_confirmed_organizer_publicity'}
 for e in events:
  for key,val in previous.get(e['source_url'],{}).items():
   if key.startswith('image_'):e[key]=val
 asset_dir=BASE/'events-preview/tel-aviv/assets/publicity'
 pending=[e for e in events if not (e.get('image_rights')=='user_confirmed_organizer_publicity' and e.get('image_url','').startswith('https://raw.githubusercontent.com/isnet-media/isnet-real-estate-site/main/events-preview/tel-aviv/assets/publicity/') and (asset_dir/e['image_url'].rsplit('/',1)[-1]).is_file())]
 enriched=enrich_events_images(pending,asset_dir,'https://raw.githubusercontent.com/isnet-media/isnet-real-estate-site/main/events-preview/tel-aviv/assets/publicity')
 by_image={e['id']:e for e in enriched}
 events=[by_image.get(e['id'],e) for e in events]
 # Same occurrence can be reached through more than one listing or booking URL.
 unique={}
 for e in events:
  if e['category']=='music':e.setdefault('concert_kind','live')
  key=(re.sub(r'\s+',' ',e['title']).strip(),e['start'],e['venue'])
  unique.setdefault(key,e)
 events=sorted(unique.values(),key=lambda x:x['start'])
 inventory=BASE/'events-preview/tel-aviv/data/culture-sources.json'
 coverage=[]
 if inventory.exists():
  for source in json.loads(inventory.read_text())['venues']:
   rows=[e for e in events if e['source']==source.get('collector') and any(v in e['venue'] for v in source.get('venue_match',[]))]
   report=next((r for r in reports if r['name']==source.get('collector')),None)
   coverage.append({**source,'status':('active' if report and report['status']=='ok' else 'failed') if source.get('collector') else 'awaiting_adapter','upcoming_events':len(rows),'last_attempt':STAMP if report else None})
 (OUT.parent/'culture-coverage.json').write_text(json.dumps({'updated_at':STAMP,'requested_venues':len(coverage),'venues':coverage},ensure_ascii=False,indent=2)+'\n')
 if not events:raise RuntimeError('no verified future events; refusing to replace feed')
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'city':'tel-aviv','updated_at':STAMP,'sources':reports,'events':events},ensure_ascii=False,indent=2)+'\n');print(json.dumps({'events':len(events),'sources':reports},ensure_ascii=False))
if __name__=='__main__':main()

