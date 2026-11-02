#!/usr/bin/env python3
"""Collect Herzliya's own dated sources and source photographs; preserve provenance."""
import concurrent.futures,hashlib,json,re,io,copy
from datetime import datetime
from urllib.parse import urljoin,urlsplit
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
import requests
import sync_holon_events as h
from friends_city_source import collect as collect_friends
from herzliya_event_quality import reviewed
ROOT=Path(__file__).resolve().parents[1];C=ROOT/'events-preview/herzliya';D=C/'data'
h.CITY=C;h.DATA=D
NOW=h.NOW;TODAY=h.TODAY
read=h.read;save=h.save;get=h.get;clean=h.clean

def photo(url,source):
 if not url or not url.startswith('https://') or any(k in url.lower() for k in ['no_pic','logo','no-image','placeholder','icon']):return None
 host=urlsplit(url).hostname or '';origin=urlsplit(source).hostname or ''
 if host.removeprefix('www.')!=origin.removeprefix('www.') and not (host.endswith('smarticket.co.il') or host.endswith('wixstatic.com') or host=='cdn.shopify.com' or host=='images.rest.co.il' and origin=='www.rest.co.il' or host=='media.getmood.io' and origin in {'www.sebastian.co.il','sebastian.co.il'}):return None
 try:
  dest=C/'assets/events'/(hashlib.sha256(url.encode()).hexdigest()[:20]+'.jpg');dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists():
   r=requests.get(url,timeout=18);r.raise_for_status();im=Image.open(io.BytesIO(r.content))
   if min(im.size)<160:return None
   im=im.convert('RGB');im.thumbnail((1200,1000));im.save(dest,'JPEG',quality=86,optimize=True)
  return 'assets/events/'+dest.name
 except Exception:return None
h.promo=photo

def municipal(s):
 rows=[]
 for e in s.select('.event[data-id]'):
  a=e.select_one('h2 a[href]');date=e.select_one('.date[title]');ps=e.select('.h p');im=e.select_one('img[src]')
  if not a or not date:continue
  try:d=datetime.strptime(date['title'],'%d/%m/%Y').date().isoformat()
  except ValueError:continue
  text=e.get_text(' ',strip=True);t=re.search(r'\b(\d{2}:\d{2})\b',text)
  if not t:continue
  venue=ps[1].get_text(' ',strip=True) if len(ps)>1 else 'הרצליה'
  rows.append(dict(title=clean(a.get_text()),start_date=d,start_time=t[1],venue=venue,ticket_url=urljoin('https://herzliya.muni.il/',a['href']),image_origin_url=urljoin('https://herzliya.muni.il/',im['src']) if im else None,audiences=['seniors'] if 'זמן זהב' in text else []))
 return rows

def ingest(spec):
 report=dict(id=spec['id'],name=spec['name'],url=spec['url'],checked_at=NOW.isoformat(),events_found=0)
 try:
  p=spec['parser'];s=get(spec['url'])
  if p=='municipal':rows=municipal(s)
  elif p=='friends':rows=collect_friends('הרצליה',get)
  elif p=='smarticket':rows=h.core.smarticket_rows(s,spec)
  elif p=='mevalim':
   rows=[]
   for n in s.select('[data-mvlm-event-date]'):
    v=n.select_one('.rgbcode_table_shortcode_table_venue');venue=v.get_text(' ',strip=True) if v else ''
    if 'הרצליה' not in venue:continue
    try:d=datetime.strptime(n['data-mvlm-event-date'],'%d.%m.%y %H:%M')
    except ValueError:continue
    rows.append(dict(title=n.get('data-mvlm-event-name'),start_date=d.date().isoformat(),start_time=d.strftime('%H:%M'),venue=venue,ticket_url=n.get('data-mvlm-event-link-target')))
  else:rows=[]
  out=[]
  for r in rows:
   if not TODAY.isoformat()<=r.get('start_date','')<=h.core.add_months(TODAY,5).isoformat():continue
   title=clean(r.get('title'));u=r.get('ticket_url');venue=r.get('venue') or spec['venue']
   if not title or not u:continue
   cat=h.classify(title,'',spec['id']);cat='kids' if spec['id']=='municipality' and 'מרכז אגדה' in title else cat;cat='cinema' if spec['id']=='cinematheque' else cat
   if re.search('בלט|מחול',title):cat='theatre'
   e=dict(id='herzliya-'+hashlib.sha256((h.core.text_norm(title)+'|'+r['start_date']+'|'+r['start_time']+'|'+h.core.text_norm(venue)).encode()).hexdigest()[:16],title=title,city='הרצליה',start_date=r['start_date'],start_time=r['start_time'],venue=venue,category=cat,subcategory=h.subcat(cat,title,spec['id']),source_url=u,booking_url=r.get('purchase_url') or u,source_id=spec['id'],source_name=spec['name'],image=h.fallback(cat),image_origin_url=r.get('image_origin_url'),image_credit='תמונת המחשה — לא צילום האירוע',description='',price=None,source_checked_at=NOW.isoformat(),audiences=r.get('audiences',[]))
   out.append(e)
  report.update(status='collected' if out else 'linked_directory',events_found=len(out));return out,report
 except Exception as ex:report.update(status='fetch_failed',note=str(ex)[:160]);return [],report

def enrich(e):
 audiences=e.get('audiences',[])
 if e['source_id']=='municipality' and not audiences and not re.search('סינמטק|סרט|גמלא|ותיק|זהב',e['title']):
  image=photo(e.get('image_origin_url'),e['source_url'])
  if image:e.update(image=image,image_role='official_promotional',image_credit='תמונת המקור: עיריית הרצליה')
  e['description']=e['title']+' — '+e['venue']+'. פרטי הפעילות, ההרשמה והתנאים בעמוד העירייה המקושר.'
  return reviewed(e)
 e=h.enrich(e)
 if audiences:e['audiences']=list(set(e.get('audiences',[])+audiences))
 # Do not carry whole ticket-sales documents or boilerplate into cards.
 e['description']=e['description'][:850]
 if re.search(r'גמלא|זהב|ותיק|גיל השלישי|60\+',e['title']+' '+e['description']):e['audiences']=list(set(e.get('audiences',[])+['seniors']))
 return reviewed(e)

def enrich_directory(item):
 try:
  s=get(item['source_url']);text=s.get_text(' ',strip=True)
  if item.get('category')=='food' and 'הרצליה' not in text:return None
  meta=s.select_one('meta[property="og:image"]');u=urljoin(item['source_url'],meta.get('content','')) if meta else None
  image=photo(u,item['source_url'])
  if image:item.update(image=image,image_origin_url=u,image_role='official_promotional',image_credit='צילום: אתר '+item['title'])
  item['source_checked_at']=NOW.isoformat()
  if item.get('category')=='food':
   # Unknown remains unknown unless the direct source explicitly states it.
   if re.search(r'מסעדה כשרה|כשרה \(רבנות',text):item['kosher']=True
   if item['id']=='sebastian' and re.search('שבת',text):item['saturday']=True
  return item
 except Exception:return item

def main():
 events=[];reports=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=7) as ex:
  for rows,report in ex.map(ingest,read('sources')['sources']):events.extend(rows);reports.append(report)
 # Source priority and exact title/date/time first; alternate URLs stay attached.
 events.sort(key=lambda e:0 if e['source_id']=='cinematheque' else 1 if e['source_id']=='hall' else 2)
 unique={}
 for e in events:
  key=(h.core.text_norm(e['title']),e['start_date'],e['start_time'])
  if key in unique:unique[key].setdefault('additional_sources',[]).append(e['source_url'])
  else:unique[key]=e
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:events=list(ex.map(enrich,unique.values()))
 failed={x['id'] for x in reports if x['status']=='fetch_failed'}
 for e in read('events')['events']:
  if e['source_id'] in failed and e['start_date']>=TODAY.isoformat() and e['id'] not in {v['id'] for v in events}:events.append(e)
 if len(events)<20:raise SystemExit('Refusing to replace the feed: fewer than 20 dated local occurrences')
 events.sort(key=lambda e:(e['start_date'],e['start_time'],e['title']))
 save('events',dict(city='הרצליה',generated_at=NOW.isoformat(),events=events))
 for name in ['guides','restaurants']:
  obj=read(name)
  with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:obj['items']=[x for x in ex.map(enrich_directory,obj['items']) if x]
  obj['checked_at']=NOW.isoformat();save(name,obj)
 save('source-report',dict(checked_at=NOW.isoformat(),sources=reports,events=len(events),note='Only exact source dates; directories without parsed dates remain source links. No neighboring-city sessions.'))
 print(json.dumps({'events':len(events),'photos':sum(e.get('image_role')=='official_promotional' for e in events),'sources':reports},ensure_ascii=False))
if __name__=='__main__':main()
