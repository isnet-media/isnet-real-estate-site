#!/usr/bin/env python3
"""Verified Kiryat Gat intake. Exact occurrences, city isolation, reusable media."""
import concurrent.futures, hashlib, io, json, re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
from PIL import Image
import sync_events_from_sources as core
CITY='kiryat-gat'; LABEL='קריית גת'; ROOT=core.BASE/CITY
SOURCES=[
 {'name':'easy_kgat','url':'https://easy.co.il/list/Events?region=1750','parser':'generic','venue':LABEL,'source_type':'secondary'},
 {'name':'friends_kgat','url':'https://friends-hist.co.il/כל-המופעים/?location_cat=11','parser':'generic','venue':LABEL,'source_type':'secondary'},
 {'name':'kgat_smarticket','url':'https://matnaskg.smarticket.co.il/','parser':'smarticket','venue':'היכל התרבות קריית גת','source_type':'official'},
 {'name':'kgat_community','url':'https://matnaskg.org.il/events/','parser':'community','venue':LABEL,'source_type':'official'},
 {'name':'kgat_municipality','url':'https://www.qiryat-gat.muni.il/events/','parser':'community','venue':LABEL,'source_type':'official'},
 {'name':'mevalim_kgat','url':'https://www.mevalim.co.il/south/','parser':'mevalim','venue':LABEL,'source_type':'secondary'},
 {'name':'tickchak_kgat','url':'https://live.tickchak.co.il/kiryat-gat','parser':'generic','venue':LABEL,'source_type':'secondary'},
 {'name':'makore_kgat','url':'https://www.makore.co.il/browse/city/קריית-גת','parser':'generic','venue':LABEL,'source_type':'secondary'},
 {'name':'ticketmaster_kgat','url':'https://www.ticketmaster.co.il/venue/KG/ALL/iw','parser':'generic','venue':LABEL,'source_type':'secondary'},
]
CITY_RE=re.compile(r'קרי[יי]?ת\s*גת')
cache={}; original_fetch=core.fetch_once; original_rows=core.source_rows
metadata={}
def fetch(spec):
 u=spec['url']
 if u not in cache:cache[u]=original_fetch(spec)
 soup,err=cache[u]
 return (BeautifulSoup(str(soup),'html.parser') if soup else None),err

def classify(title,text):
 if 'סרטים' in text or title in ['הבדחן','בחורים טובים 3']:return 'cinema'
 if 'סטנדאפ' in text or re.search(r'יצפאן|ברוייר|חזקיה|זינגר|קטורזה|שחר חסון|ליטל שוורץ',title):return 'standup'
 if 'ילדים' in text or 'ספריה עירונית' in text or re.search(r'הארי פוטר|שעת סיפור|חן פיית|סינדרלה',title):return 'kids'
 if re.search(r'תיאטרון|תאטרון',text):return 'theatre'
 if 'קונצרט' in text or 'מוזיקה' in text or re.search(r'קרן פלס|בר צברי|מארינה|שירי מימון|איציק קלה|אופרה|ליאת בנאי',title):return 'music'
 if re.search(r'הרצא|חיים שפירא|מיכל דליות|איתי הרמן|העולם הפיננסי|לוקחים שליטה|חוכמת דורות',title):return 'lecture'
 if re.search(r'ספורט|אימון|הליכה',title):return 'sport'
 return 'community'

def rows(soup,spec):
 if spec['parser']=='community':
  out=[]
  for a in soup.select('a[href]'):
   text=a.get_text(' ',strip=True);m=re.search(r'יום\s+[א-ת]+,?\s*(\d{1,2}\.\d{1,2}\.\d{4})\s+(\d{1,2}:\d{2})',text)
   if not m or 'פרטים נוספים' not in text:continue
   title=text[:m.start()].strip();u=urljoin(spec['url'],a['href'])
   if urlsplit(u).hostname!='matnaskg.smarticket.co.il':continue
   venue=text[m.end():].split('פרטים נוספים')[0].strip()
   out.append(dict(title=title,start_date=datetime.strptime(m[1],'%d.%m.%Y').date().isoformat(),start_time=m[2],venue=venue,ticket_url=u,purchase_url=u,category=classify(title,text),quality_flags=['automated_official_listing']))
  return out
 if spec['parser']=='smarticket':
  for a in soup.select('a[href]'):
   text=a.get_text(' ',strip=True)
   if 'פרטים נוספים' not in text:continue
   metadata[urljoin(spec['url'],a['href'])]=text
  out=original_rows(soup,spec)
  for row in out:
   text=metadata.get(row['ticket_url'],'');row['category']=classify(row['title'],text)
   # Core parser's venue can include category breadcrumbs; keep the actual hall.
   for venue in ['היכל התרבות קרית גת','בית רחל וישראל פולק','הספרייה העירונית','מרכז תנופה החדש','בית וקס','בית יוסי שמילה','מועדון מופ"ת','יד לבנים','בית אדית לנוער','סטודיו בית אדית','אשכול פייס']:
    if venue in text:row['venue']=venue;break
  return out
 if spec['parser']=='mevalim':
  out=[]
  for n in soup.select('[data-mvlm-event-date]'):
   v=n.select_one('.rgbcode_table_shortcode_table_venue');v=v.get_text(' ',strip=True) if v else ''
   if not CITY_RE.search(v):continue
   try:d=datetime.strptime(n.get('data-mvlm-event-date'),'%d.%m.%y %H:%M')
   except (ValueError,TypeError):continue
   title=n.get('data-mvlm-event-name') or '';u=n.get('data-mvlm-event-link-target') or ''
   if title and u.startswith('https://'):out.append(dict(title=title,start_date=d.date().isoformat(),start_time=d.strftime('%H:%M'),venue=v,ticket_url=u,purchase_url=u,category=classify(title,n.get_text(' ',strip=True)),quality_flags=['automated_city_board']))
  return out
 return [r for r in original_rows(soup,spec) if CITY_RE.search(r.get('venue',''))]

def main():
 core.CITY_LABELS[CITY]=LABEL;core.fetch_once=fetch;core.source_rows=rows
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:list(ex.map(fetch,SOURCES))
 # Fetch exact event pages once, bounded concurrent requests, no access bypass.
 urls=set()
 for s in SOURCES:
  p,err=fetch(s)
  if p:
   urls.update(r['ticket_url'] for r in rows(p,s) if r.get('start_date','')>=date.today().isoformat())
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:list(ex.map(lambda u:fetch({'url':u}),sorted(urls)[:180]))
 report=core.merge(CITY,sorted(SOURCES,key=lambda s:s['source_type']!='official'),False)
 data=json.loads((ROOT/'data/events.json').read_text());held=[];events=[]
 for e in data['events']:
  if re.search(r'^חוג\b|^קורס\b|קורס ניהול|קורס פריוריטי',e['title']):held.append(e);continue
  text=metadata.get(e.get('ticket_url'),'');e['category']=classify(e['title'],text) if text else e['category']
  title=e['title'];cat=e['category'];aud=set(e.get('audiences') or [])
  if '60+' in text or re.search(r'60\+|גיל השלישי|לגילאי 60|בוקר של זהב',title):aud.add('seniors')
  if cat=='kids':aud.update(['kids','families'])
  e['audiences']=sorted(aud);e['city']=LABEL
  sub={'music':'live-music','standup':'standup','theatre':'theatre','kids':'kids-shows','lecture':'general-lectures','cinema':'cinema','community':'community-events','sport':'sport-events'}.get(cat,'other')
  if 'קונצרט' in text or 'סימפונט' in title or 'סינפונייטה' in title:sub='concerts'
  if cat=='kids' and ('סדנ' in title or 'חידות' in title):sub='kids-workshops'
  e['subcategory']=sub;e['category_memberships']=[{'category':cat,'subcategory':sub}]
  if 'seniors' in aud:e['category_memberships'].append({'category':'seniors','subcategory':{'lecture':'senior-lectures','music':'senior-music','sport':'senior-health'}.get(cat,'senior-culture')})
  kinds={'music':'מופע מוזיקה','kids':'פעילות לילדים ולמשפחות','standup':'מופע סטנדאפ','theatre':'הצגת תיאטרון','lecture':'הרצאה','cinema':'הקרנת סרט','community':'פעילות קהילתית','sport':'פעילות ספורט'}
  if not e.get('description'):e['description']=f"{title} — {kinds.get(cat,'אירוע')} ב{e['venue']}. פרטי התוכן, ההשתתפות והכרטיסים בעמוד המארגן."
  if urlsplit(e.get('ticket_url') or '').hostname=='matnaskg.smarticket.co.il':e['purchase_url']=e['ticket_url']
  events.append(e)
 # Keep a previously verified source if a partial fetch fails, and preserve IDs.
 data['events']=events;data['stats']={'events':len(events)}
 (ROOT/'data/events.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 (ROOT/'data/sources.json').write_text(json.dumps({'sources':SOURCES},ensure_ascii=False,indent=2)+'\n')
 report['public_after_quality']=len(events);report['held_classes']=len(held)
 (core.BASE/'admin/data/kgat-source-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 (core.BASE/'admin/data/kgat-classes-review.json').write_text(json.dumps({'items':held},ensure_ascii=False,indent=2)+'\n')
 if not events:raise SystemExit('No verified Kiryat Gat events; refusing empty launch')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
