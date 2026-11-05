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
def main():
 old=json.loads(OUT.read_text()) if OUT.exists() else {'events':[]};events=[];reports=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  futures={pool.submit(fn):name for name,fn in [('בית ליסין',lessin),('בית אריאלה',ariela),('לבונטין 7',levontin)]}
  for f in concurrent.futures.as_completed(futures):
   name=futures[f]
   try:
    rows=f.result()
    if not rows:raise ValueError('empty_source')
    events+=rows;reports.append({'name':name,'status':'ok','count':len(rows),'checked_at':STAMP})
   except Exception as e:
    previous=[x for x in old['events'] if x['source']==name and datetime.fromisoformat(x['start'])>NOW and (NOW-datetime.fromisoformat(x['verified_at'])).total_seconds()<172800];events+=previous;reports.append({'name':name,'status':'failed','retained':len(previous),'error':type(e).__name__,'attempted_at':STAMP})
 from tlvnet_publicity import enrich_events_images
 previous={e['source_url']:e for e in old.get('events',[]) if e.get('image_rights')=='user_confirmed_organizer_publicity'}
 for e in events:
  for key,val in previous.get(e['source_url'],{}).items():
   if key.startswith('image_'):e[key]=val
 events=enrich_events_images(events,BASE/'events-preview/tel-aviv/assets/publicity','https://raw.githubusercontent.com/isnet-media/isnet-real-estate-site/main/events-preview/tel-aviv/assets/publicity')
 events=sorted({x['id']:x for x in events}.values(),key=lambda x:x['start'])
 if not events:raise RuntimeError('no verified future events; refusing to replace feed')
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'city':'tel-aviv','updated_at':STAMP,'sources':reports,'events':events},ensure_ascii=False,indent=2)+'\n');print(json.dumps({'events':len(events),'sources':reports},ensure_ascii=False))
if __name__=='__main__':main()
