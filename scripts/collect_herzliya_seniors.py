"""Direct senior sources: dated events, current recurring classes, clubs and services."""
import re,json,hashlib,concurrent.futures
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import sync_herzliya_events as c
D=c.D;BASE='https://www.herzliya-matnasim.org.il/'
SOURCES={
 'ale-club':('מועדון צמרות 60+','https://www.ale-herzliya.co.il/?services=moadon-tzamarot-60'),
 'ale-college':('מכללת הגמלאים','https://www.ale-herzliya.co.il/?services=michlalot'),
 'ale-sport':('ספורט ותנועה — ע.ל.ה','https://www.ale-herzliya.co.il/?services=sport-activities'),
 'ale-neighborhood':('מועדון נוף ים','https://www.ale-herzliya.co.il/?services=moadonim-shhunatim'),
 'matnas-events':('קהילת ותיקים — אירועים',BASE+'events/?category=94'),
 'matnas-classes':('חוגים לגיל השלישי במרכזים הקהילתיים',BASE+'activities/?ageGroup=גיל+שלישי+66+ומעלה&branch=&category=&free_text=&group='),
 'wix-classes':('חוגי בית הגמלאי','https://gimlaeim6.wixsite.com/gimlaeim/blank-9'),
 'municipal24':('הגיל השלישי — עיריית הרצליה','https://www.herzliya.muni.il/events/?category=24'),
 'gold-info':('זמן זהב — מידע, זכויות ופנאי','https://www.herzliya.muni.il/2139/'),
 'nde':('מרכזי יום ומועדונים — מדריך NDE','https://www.nde.co.il/day-center/city/הרצליה')}

def ident(s):return hashlib.sha256(s.encode()).hexdigest()[:16]
def topic(t):
 if re.search('יוגה|פילאט|פילט|התעמלות|פלדנקרייז|כושר|תנועה|צ.י קונג|ספורט',t):return 'sport'
 if re.search('שפות|אנגלית|צרפתית|ספרדית|עברית|לימוד|מכלל|תשבצ|ברידג|מחשב|סמארטפון',t):return 'learning'
 if re.search('ציור|אמנות|אומנות|יצירה|ויטראז|תכשיט|מלאכת|פיסול',t):return 'art'
 if re.search('מקהלה|ריקוד|זמר|שירה',t):return 'music'
 return 'social'
def page(key):
 u=SOURCES[key][1];p=__import__('pathlib').Path('/tmp/senior-'+key+'.html')
 # Same-session research pages are a local cache only; scheduled runs fetch fresh sources.
 return BeautifulSoup(p.read_text(),'html.parser') if p.exists() else c.get(u)
def record(key,title,description,kind='club',**fields):return dict(id='senior-'+ident(key+'|'+title),title=title,description=description,kind=kind,topic=topic(title),source_name=SOURCES[key][0],source_url=SOURCES[key][1],checked_at=c.NOW.isoformat(),**fields)

def retain_unverified_catalog(previous,current,reports,today):
 # A failed or unparsed page is not evidence that a current course has closed.
 # Keep its last source timestamp and expose the failed refresh to the reader.
 by_name={v[0]:k for k,v in SOURCES.items()};present={x['id'] for x in current};retained=[]
 for report in reports:
  name=report['name'];old=[x for x in previous if x.get('source_name')==name];fresh=[x for x in current if x.get('source_name')==name]
  incomplete=report['status']=='fetch_failed' or (old and len(fresh)<len(old)/2)
  if not incomplete:continue
  report['status']='retained_after_failed_or_partial_collection';report['fresh_items']=len(fresh)
  for item in old:
   if item['id'] in present:continue
   end=item.get('term_end')
   if end and end<today:continue
   if not end:
    try:age=(datetime.fromisoformat(today).date()-datetime.fromisoformat(item['checked_at'].replace('Z','+00:00')).date()).days
    except (ValueError,KeyError):continue
    if age>30:continue
   kept=dict(item,last_refresh_status='unverified',last_refresh_attempt=report['checked_at'],availability_note='הפרטים לא אומתו בעדכון האחרון. יש לברר פעילות, שעות ומקום פנוי עם המפעיל.')
   retained.append(kept);present.add(item['id'])
  report['retained_items']=sum(x.get('source_name')==name for x in retained)
 return current+retained

def scoped_sources(scope):
 if scope=='all':return list(SOURCES)
 if scope=='events':return ['matnas-events','municipal24']
 if scope=='catalog':return [k for k in SOURCES if k not in ('matnas-events','municipal24')]
 raise ValueError('invalid senior collection scope')

def main(scope='all'):
 selected=scoped_sources(scope)
 catalog=[];incoming=[];reports=[];pages={}
 def load(k):
  try:return k,page(k),None
  except Exception as e:return k,None,str(e)[:160]
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
  for k,s,error in ex.map(load,selected):
   reports.append(dict(id=k,name=SOURCES[k][0],url=SOURCES[k][1],status='checked' if s else 'fetch_failed',error=error,checked_at=c.NOW.isoformat()))
   if s:pages[k]=s
 # Current school-year classes: actual source days, times, location and registration destination.
 s=pages.get('matnas-classes')
 if s:
  for tr in s.select('tr:has(.toggle-activity)'):
   cols=tr.find_all('td',recursive=False)
   if len(cols)<7:continue
   vals=[]
   for col in cols:
    copy=BeautifulSoup(str(col),'html.parser')
    for node in copy.select('.md-only'):node.decompose()
    vals.append(c.clean(copy.get_text(' ',strip=True)))
   if 'גיל שלישי' not in vals[2]:continue
   target=tr.select_one('[aria-controls]')['aria-controls'];detail=s.find(id=target);a=detail.select_one('a[href^="https:"]') if detail else None
   text=detail.get_text(' ',strip=True) if detail else '';dates=re.findall(r'\d{2}/\d{2}/\d{4}',text)
   end=datetime.strptime(dates[1],'%d/%m/%Y').date().isoformat() if len(dates)>1 else None
   if end and end<c.TODAY.isoformat():continue
   title=vals[0]+' — '+vals[1]
   phone=re.search(r'0\d[-\s]?\d{7,8}',vals[5])
   catalog.append(record('matnas-classes',title,'קבוצה לגיל השלישי במרכזים הקהילתיים, עם ימי פעילות והרשמה לפי המקור הרשמי.','class',venue=vals[3],schedule=vals[4],price_text=vals[6]+' לחודש' if 'מחיר לחודש' in text else vals[6],booking_url=a['href'] if a else SOURCES['matnas-classes'][1],phone=phone[0] if phone else None,term_end=end,availability_note='יש לוודא שיש מקום בקבוצה לפני ההרשמה.'))
 # Wix describes programs but does not establish that its old prices/times are current.
 s=pages.get('wix-classes');seen=set()
 if s:
  for h in s.select('h1'):
   if 'font-size:23px' not in h.get('style','').replace(' ',''):continue
   title=c.clean(h.get_text(' ',strip=True))
   if not 3<len(title)<75 or title=='בית הגמלאי הרצליה' or re.search('₪|על המורה|כלול|ללא תשלום|^יום|^ימי',title):continue
   if title in seen:continue
   seen.add(title)
   catalog.append(record('wix-classes',title,'פעילות המופיעה בתוכנית בית הגמלאי. פרטי הקבוצה והרשמה מול הבית; אין כאן אישור שהמחירים והמועדים בעמוד הוותיק עדיין בתוקף.','class',venue='בית הגמלאי הרצליה',availability_note='יש לאמת פעילות נוכחית, מחיר ושעות עם המפעיל.'))
 # Institution cards use concise authored descriptions and contacts transcribed from official pages.
 authored=[('ale-club','מועדון צמרות 60+','חוגי אמנות ויצירה, ספורט, חשיבה, ערבי שירה וסיורים. מתאים למי שמחפש מסגרת חברתית קבועה.',"ר׳ שמעון לביא 21, הרצליה",'052-2764336'),('ale-college','מכללת הגמלאים — ללמוד בבוקר','מסגרת הרצאות בתחומי תרבות וידע. התוכנית העונתית וההרשמה באתר העמותה.','היכל בעיר, בן גוריון 5, הרצליה','09-9519828'),('ale-sport','ספורט ותנועה עם ע.ל.ה','פלדנקרייז, פילאטיס, ניה והתעמלות בריאותית במוקדים ברחבי העיר. בחרו חוג ובדקו התאמה והרשמה עם המפעיל.','מוקדים ברחבי הרצליה','09-9519828'),('ale-neighborhood','מועדון גמלאי נוף ים בתאו','מפגש חברתי והרצאות בימי ראשון אחר הצהריים, בתחומי מסעות, היסטוריה, אקטואליה ותרבות.','תאו, וינגייט 168, קומה 2, הרצליה','054-5296090')]
 for k,t,d,v,p in authored:
  if k not in pages:continue
  x=record(k,t,d,venue=v,phone=p)
  s=pages[k];image=next((im.get('src') for im in s.select('img[src]') if im.get('alt') and any(w in im.get('alt') for w in ['ציור','יוגה','נשים','גבר'])),None)
  if image:
   local=c.photo(urljoin(SOURCES[k][1],image),SOURCES[k][1])
   if local:x.update(image=local,image_credit='צילום: ע.ל.ה הרצליה')
  catalog.append(x)
 if scope!='events':catalog.extend([record('gold-info','זמן זהב — זכויות, שירותים ופנאי','שער המידע העירוני לוותיקים: תרבות והעשרה, זכויות והטבות, סיוע וחוברת הפעילויות.','service'),record('nde','מרכזי יום ומועדונים חברתיים','מדריך לאיתור מסגרות בהרצליה ופרטי קשר. זהו מקור מידע חיצוני; יש לברר ישירות מול המסגרת פעילות, התאמה ותנאי הצטרפות.','service',availability_note='פרטי המדריך לא אומתו מול כל מרכז בנפרד.')])
 # Dated source events: a course interval is not turned into invented daily occurrences.
 s=pages.get('matnas-events')
 if s:
  for a in s.select('a.event-promo[href]'):
   h=a.select_one('h2');d=a.select_one('.date');t=a.select_one('.time');v=a.select_one('.place')
   if not h or not d:continue
   dates=re.findall(r'\d{2}\.\d{2}\.\d{4}',d.get_text());times=re.findall(r'\d{2}:\d{2}',t.get_text() if t else d.get_text());title=c.clean(h.get_text());u=urljoin(BASE,a['href'])
   if not dates or not times:continue
   start=datetime.strptime(dates[0],'%d.%m.%Y').date().isoformat();end=datetime.strptime(dates[-1],'%d.%m.%Y').date().isoformat()
   if end<c.TODAY.isoformat():continue
   if start<c.TODAY.isoformat():
    catalog.append(record('matnas-events',title,'סדרה או קורס שנמשכים בתקופה המפורסמת. מועד המפגש הבא יש לברר באתר המארגן.','class',booking_url=u,venue=c.clean(v.get_text()) if v else 'הרצליה',term_end=end));continue
   image=a.select_one('img[src]');image_url=urljoin(BASE,image['src']) if image else None
   row=dict(id='herzliya-senior-'+ident(u+'|'+start+'|'+times[0]),title=title,city='הרצליה',start_date=start,start_time=times[0],venue=c.clean(v.get_text()) if v else 'הרצליה',category='seniors',subcategory={'sport':'senior-sport','learning':'senior-lectures','art':'senior-workshops','music':'senior-music'}.get(topic(title),'senior-social'),audiences=['seniors'],source_id='matnas-seniors',source_name=SOURCES['matnas-events'][0],source_url=u,booking_url=u,description='פעילות מקהילת הוותיקים במרכזים הקהילתיים. פרטי התוכנית וההרשמה באתר המארגן.',image_origin_url=image_url,image=c.h.fallback('seniors'),image_role='illustration',image_credit='תמונת המחשה — לא צילום הפעילות',price=None,source_checked_at=c.NOW.isoformat())
   price=a.select_one('.price');hit=re.search(r'(\d+(?:\.\d+)?)',price.get_text()) if price else None
   if hit:row['price']=float(hit[1])
   if 'אזל המלאי' in a.get_text():row['ticket_status']='sold_out'
   incoming.append(row)
 s=pages.get('municipal24')
 if s:
  for r in c.municipal(s):
   if r['start_date']<c.TODAY.isoformat():continue
   incoming.append(dict(id='herzliya-senior-'+ident(r['ticket_url']),title=r['title'],city='הרצליה',start_date=r['start_date'],start_time=r['start_time'],venue=r['venue'],category='seniors',subcategory='senior-health',audiences=['seniors'],source_id='municipal24',source_name=SOURCES['municipal24'][0],source_url=r['ticket_url'],booking_url=r['ticket_url'],description='פעילות הגיל השלישי לפי לוח עיריית הרצליה. פרטי ההרשמה בעמוד הפעילות.',image_origin_url=r.get('image_origin_url'),image=c.h.fallback('seniors'),image_role='illustration',image_credit='תמונת המחשה — לא צילום הפעילות',price=None,source_checked_at=c.NOW.isoformat()))
 def art(e):
  im=c.photo(e.get('image_origin_url'),e['source_url'])
  if im:e.update(image=im,image_role='official_promotional',image_credit='תמונת המקור: '+e['source_name'])
  return e
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:incoming=list(ex.map(art,incoming))
 raw=c.read('events');added=0;matched=0
 for e in incoming:
  match=next((x for x in raw['events'] if x['source_url'].rstrip('/')==e['source_url'].rstrip('/') and x['start_date']==e['start_date'] and x['start_time']==e['start_time']),None)
  if match:
   match['audiences']=list(set(match.get('audiences',[])+['seniors']));match['senior_subcategory']=e['subcategory'];match['ticket_status']=e.get('ticket_status',match.get('ticket_status','unknown'))
   if e.get('price') is not None:match['price']=e['price']
   matched+=1
  else:raw['events'].append(e);added+=1
 # A child-only label is never evidence of a senior audience.
 for e in raw['events']:
  if re.search('ילדים|ילדות|תינוק|פעוט|כיתות|גילאי [1-9]|דן דן הנגן',e['title']) and not re.search('ותיק|גמלא|בין.דורי',e['title']):e['audiences']=[a for a in e.get('audiences',[]) if a!='seniors']
 previous_container=c.read('senior-catalog') if (D/'senior-catalog.json').exists() else {}
 previous=previous_container.get('items',[])
 catalog=retain_unverified_catalog(previous,catalog,reports,c.TODAY.isoformat())
 if scope!='all':
  touched={SOURCES[k][0] for k in selected};seen={x['id'] for x in catalog}
  # Untouched classes/services keep their source timestamps, even if older than
  # a retention window for failed sources. No request or verification occurred.
  catalog.extend(dict(x) for x in previous if x.get('source_name') not in touched and x['id'] not in seen)
  reports.extend(x for x in previous_container.get('sources',[]) if x.get('name') not in touched)
 if scope!='catalog':c.save('events',raw)
 stamp=c.NOW.isoformat() if scope=='all' else previous_container.get('checked_at')
 c.save('senior-catalog',dict(checked_at=stamp,partial_checked_at=c.NOW.isoformat() if scope!='all' else None,refresh_scope=scope,items=catalog,sources=reports))
 source=c.read('sources');existing={x['url'] for x in source['sources']}
 for k,(n,u) in SOURCES.items():
  if u not in existing:source['sources'].append(dict(id='senior-'+k,name=n,url=u,parser='directory',venue=n,kind='official' if k!='nde' else 'directory'))
 c.save('sources',source);print('Senior catalog',len(catalog),'dated source occurrences',len(incoming),'new',added,'matched',matched,flush=True)
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--scope',choices=['all','events','catalog'],default='all')
 main(ap.parse_args().scope)
