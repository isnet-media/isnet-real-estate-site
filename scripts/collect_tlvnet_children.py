"""Verified public listing intake. Images are candidates, not a reuse licence."""
import json,re,hashlib,requests,concurrent.futures
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from pathlib import Path
TZ=ZoneInfo('Asia/Jerusalem'); NOW=datetime.now(TZ); STAMP=NOW.isoformat(); ROOT=Path(__file__).resolve().parents[1]/'events-preview/tel-aviv/data';ROOT.mkdir(parents=True,exist_ok=True)

def fetch(url):
 r=requests.get(url,timeout=30,headers={'User-Agent':'TLVNET public event directory/1.0'});r.raise_for_status();return BeautifulSoup(r.text,'html.parser')
def clean(x):return re.sub(r'\s+',' ',x.get_text(' ',strip=True) if hasattr(x,'get_text') else str(x or '')).strip()
def make(title,dt,venue,address,source,url,note='',price=None,image=None,credit=None):
 if not NOW<=dt<=NOW+timedelta(days=45):return None
 return dict(id=hashlib.sha256((source+url+dt.isoformat()).encode()).hexdigest()[:20],title=clean(title),start=dt.isoformat(),venue=clean(venue),address=clean(address),category='kids',source=source,source_url=url,verified_at=STAMP,note=note,price=price,image=None,image_rights='not_supplied',city='tel-aviv',publication_status='published',image_candidate=image,image_candidate_credit=credit,image_evidence_url=url)
def ariela_children():
 urls=[];seen=set()
 for audience in ['events-kids','events-infants','events-teen']:
  for page in range(1,4):
   url='https://ariela.today/events/audience:'+audience+('/page:'+str(page) if page>1 else '')
   b=fetch(url);cards=b.select('.event-item-link')
   if not cards:break
   for a in cards:
    u=a['href']
    if u in seen:continue
    seen.add(u)
    d=[a.select_one('.event-date-'+k) for k in ['year','month','day']]
    tm=re.search(r'\d{2}:\d{2}',clean(a.select_one('.event-item-info-time')))
    if not all(d) or not tm:continue
    dt=datetime(2000+int(clean(d[0])),int(clean(d[1])),int(clean(d[2])),*map(int,tm[0].split(':')),tzinfo=TZ)
    if NOW<=dt<=NOW+timedelta(days=45):urls.append((u,dt))
   if not any('next page' in a.get_text() for a in b.select('a')):break
 def detail(pair):
  u,dt=pair;b=fetch(u);h=b.select_one('h1.event-title');sub=b.select_one('.event-subhead');place=b.select_one('.event-attributes-place');address=place.select_one('em') if place else None
  audience=clean(b.select_one('.event-attributes-audience'))
  if not audience and not any(k in clean(h)+' '+clean(sub) for k in ['ילדים','ילדות','קטנט','שעת סיפור','לכל המשפחה']):return None
  price=clean(b.select_one('.event-attributes-price'));img=b.select_one('.event-image img');credit=b.select_one('.event-image figcaption')
  return make(clean(h)+' · '+clean(sub),dt,clean(place).replace(clean(address),'').strip() if address else clean(place),clean(address)+' תל אביב-יפו','בית אריאלה וספריות העיר',u,' | '.join(x for x in [audience,price,'מחיר וזמינות במקור; חלק מהמפגשים מחייבים הרשמה מראש'] if x),image=img.get('src') if img else None,credit=clean(credit))
 out=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
  for f in concurrent.futures.as_completed([pool.submit(detail,p) for p in urls]):
   try:
    r=f.result()
    if r:out.append(r)
   except Exception:pass
 return out

def muza_children():
 u='https://www.eretzmuseum.org.il/לוח-אירועים-דיג/';b=fetch(u);raw=b.select_one('#events-datepicker-data')
 if not raw:raise ValueError('muza missing calendar JSON')
 out=[]
 for e in json.loads(raw.string):
  title=e.get('title','');tm=e.get('time','')
  if not any(k in title for k in ['לכל המשפחה','לילדים','כיתות','לגיל','חנוכה','אורנה פורת']):continue
  if not re.fullmatch(r'\d{2}:\d{2}',tm):continue
  dt=datetime.fromisoformat(e['dateKey']+'T'+tm).replace(tzinfo=TZ)
  url=e.get('moreInfoUrl') or e.get('orderUrl')
  if not url:continue
  row=make(title,dt,'מוז״א · מוזיאון ארץ ישראל'+(' · '+e['venue'] if e.get('venue') else ''),'חיים לבנון 2, תל אביב','מוז״א',url,'אזלו הכרטיסים לפי המקור' if e.get('soldOut') else 'מחיר וזמינות באתר המוזיאון')
  if row:row['booking_url']=e.get('orderUrl');out.append(row)
 # Obtain image candidates from actual institutional detail pages, no assumption of licence.
 def add_image(r):
  try:
   d=fetch(r['source_url']);m=d.select_one('meta[property="og:image"]')
   if m:r['image_candidate']=m.get('content')
  except Exception:pass
  return r
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:return list(pool.map(add_image,out))

def nature_children():
 u='https://smnh.tau.ac.il/events/';b=fetch(u);out=[]
 for card in b.select('.event-item-a'):
  tags=clean(card.select_one('.item-tags'))
  if 'לכל המשפחה' not in tags:continue
  title=card.select_one('.event-item-title a');date=clean(card.select_one('.event-item-date'));m=re.search(r'(\d{2}\.\d{2}\.\d{4})\s*∙\s*(\d{2}:\d{2})',date)
  if not title or not m:continue
  dt=datetime.strptime(m[1]+' '+m[2],'%d.%m.%Y %H:%M').replace(tzinfo=TZ);img=card.select_one('img')
  row=make(clean(title),dt,'מוזיאון הטבע ע״ש שטיינהרדט','קלאוזנר 12, תל אביב','מוזיאון הטבע',title['href'],'הזמנה מראש באתר המוזיאון; מועדים נוספים ומחיר בקישור',image=img.get('src') if img else None)
  if row:out.append(row)
 return out

if __name__=='__main__':
 events=[];sources=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  futures={pool.submit(fn):name for name,fn in [('בית אריאלה וספריות העיר',ariela_children),('מוז״א',muza_children),('מוזיאון הטבע',nature_children)]}
  for f in concurrent.futures.as_completed(futures):
   name=futures[f]
   try:
    rows=f.result();events+=rows;sources.append({'name':name,'status':'ok','count':len(rows),'checked_at':STAMP})
   except Exception as e:sources.append({'name':name,'status':'failed','error':repr(e)})
 out={'city':'tel-aviv','updated_at':STAMP,'sources':sources,'events':sorted({e['id']:e for e in events}.values(),key=lambda e:e['start'])}
 # Publicity asset use confirmed by publisher. Only exact institutional images,
 # real image bytes and local JPG copies; never a guessed/generic image.
 from PIL import Image,ImageStat
 import io
 assets=ROOT.parent/'assets/publicity';assets.mkdir(parents=True,exist_ok=True)
 def image_for(e):
  try:
   u=e.get('image_candidate');host=__import__('urllib.parse',fromlist=['urlsplit']).urlsplit(u or '').hostname or ''
   if not u or not any(host==d or host.endswith('.'+d) for d in ['ariela.today','eretzmuseum.org.il','smnh.tau.ac.il']):return e
   if re.search(r'no.?pic|def.?img|logo|placeholder|favicon',u,re.I):return e
   resp=requests.get(u,timeout=20);resp.raise_for_status();pic=Image.open(io.BytesIO(resp.content));pic.load()
   if min(pic.size)<150 or max(ImageStat.Stat(pic.convert('RGB').resize((64,64))).stddev)<8:return e
   pic=pic.convert('RGB');pic.thumbnail((1400,1400));name='kids-'+hashlib.sha256(u.encode()).hexdigest()[:18]+'.jpg';pic.save(assets/name,quality=86,optimize=True)
   e.update(image_url='https://raw.githubusercontent.com/isnet-media/isnet-real-estate-site/main/events-preview/tel-aviv/assets/publicity/'+name,image_credit=e.get('image_candidate_credit') or 'תמונת יח״צ מטעם '+e['source'],image_source_url=e['source_url'],image_rights='user_confirmed_organizer_publicity')
  except Exception:pass
  return e
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:out['events']=list(pool.map(image_for,out['events']))
 if not out['events']:raise SystemExit('No verified children events; preserving feed')
 (ROOT/'children.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'sources':sources,'events':len(out['events'])},ensure_ascii=False))
