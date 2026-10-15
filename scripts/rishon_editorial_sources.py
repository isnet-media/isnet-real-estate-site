#!/usr/bin/env python3
"""Exact calendar-to-detail linking for Rishon; facts only, no paid model calls."""
import argparse,hashlib,json,re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta
from pathlib import Path
from urllib.parse import urljoin,unquote
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'events-preview/rishon-lezion';CACHE=Path('/tmp/rishon-editorial-cache');TODAY=datetime.now(ZoneInfo('Asia/Jerusalem')).date().isoformat();LIMIT=(datetime.now(ZoneInfo('Asia/Jerusalem')).date()+timedelta(days=153)).isoformat();STAMP=datetime.now(ZoneInfo('Asia/Jerusalem')).isoformat()
URLS={'htrl':'https://htrl.co.il/לוח-שנה/','htrl_adults':'https://htrl.co.il/third-calendar/','kotar':'https://www.kotar-rishon-lezion.org.il/events-category/eventsactivities/'}
def clean(x):return re.sub(r'\s+',' ',str(x or'')).strip()
def norm(x):return re.sub(r'[^א-תa-z0-9]+',' ',clean(x).lower()).strip()
def page(url):
 CACHE.mkdir(exist_ok=True);f=CACHE/(hashlib.sha256(url.encode()).hexdigest()+'.html')
 if f.exists():return BeautifulSoup(f.read_text(),'html.parser')
 r=requests.get(url,timeout=25);r.raise_for_status();f.write_text(r.text);return BeautifulSoup(r.text,'html.parser')
def txt(p,selector):
 x=p.select_one(selector);return clean(x.get_text(' ',strip=True))if x else''
def calendars(errors=None):
 rows=[];errors=errors if errors is not None else {}
 for src,url in URLS.items():
  try:p=page(url)
  except Exception as ex:
   errors[url]=str(ex)[:200];print('Calendar unavailable',src,flush=True);continue
  if src!='kotar':
   for c in p.select('.show-list-item'):
    day=txt(c,'.day-list');tm=txt(c,'.time-list');title=txt(c,'.name-list');a=c.select_one('.btn-purchase a[href]')
    if not re.fullmatch(r'\d{2}\.\d{2}\.\d{2}',day)or not re.fullmatch(r'\d{2}:\d{2}',tm)or not a:continue
    day=datetime.strptime(day,'%d.%m.%y').date().isoformat()
    if not TODAY<=day<=LIMIT:continue
    rows.append(dict(source=src,title=title,start_date=day,start_time=tm,venue=txt(c,'.place-list'),detail_url=urljoin(url,a['href'])))
  else:
   for c in p.select('.day .event'):
    d=c.find_parent(class_='day');h=d.select_one('.title[data-date2]')if d else None
    if not h:continue
    day=datetime.strptime(h['data-date2'],'%d/%m/%Y').date().isoformat()
    if not TODAY<=day<=LIMIT:continue
    facts={}
    for block in c.select('.detail'):
     label=txt(block,'label').strip(':');facts[label]=txt(block,'.text')
    tm=re.search(r'\d{2}:\d{2}',facts.get('שעות',''));a=c.select_one('a.external-link[href]')
    if not tm:continue
    content=txt(c,'.introtext')or txt(c,'.fulltext');image=c.select_one('img[src]')
    rows.append(dict(source=src,title=txt(c,'.event-title'),start_date=day,start_time=tm[0],venue=facts.get('מיקום',''),detail_url=url,booking_url=urljoin(url,a['href'])if a else'',source_text=content,source_category=txt(c,'.category'),age_text=facts.get('גילאים',''),price_text=facts.get('מחיר',''),address=facts.get('כתובת',''),image_url=urljoin(url,image['src'])if image else''))
  print('Calendar',src,len([x for x in rows if x['source']==src]),flush=True)
 return rows

def detail(url):
 p=page(url);box=p.select_one('.show-text,.show-culture-text');desc=box.select_one('.fest-description')if box else None;meta=p.select_one('meta[property="og:image"]');own=p.select_one('main section');booking=own.select_one('a[href*="showURL"],a[href*="smarticket"],a[href*="tickchak"]')if own else None
 title=txt(box,'h1,.title-culture-show')if box else txt(p,'h1');text=clean(desc.get_text(' ',strip=True))if desc else''
 source_category=' '.join(clean(a.get_text())for a in p.select('.breadcrumb a,.breadcrumbs a'))
 return dict(detail_title=title,source_text=text,speaker=txt(box,'.speaker')if box else'',duration_text=txt(box,'.dur-theater,.duration')if box else'',booking_url=urljoin(url,booking['href'])if booking else'',image_url=meta['content']if meta else'',image_credit=txt(box,'.author-show')if box else'',source_category=source_category)

def museum_rows(url):
 p=page(url);title=txt(p,'h1');meta=p.select_one('meta[property="og:image"]');out={}
 months={'ינואר':1,'פברואר':2,'מרץ':3,'אפריל':4,'מאי':5,'יוני':6,'יולי':7,'אוגוסט':8,'ספטמבר':9,'אוקטובר':10,'נובמבר':11,'דצמבר':12}
 for tr in p.select('table tbody tr'):
  a=tr.select_one('td a[href]');text=clean(a.get_text())if a else''
  m=re.search(r'(\d{1,2}) ב([א-ת]+) (\d{4}) בשעה (\d{2}:\d{2})',text)
  if not m or m[2]not in months:continue
  day=datetime(int(m[3]),months[m[2]],int(m[1])).date().isoformat()
  if not TODAY<=day<=LIMIT:continue
  booking=urljoin(url,a['href']);key=(day,m[4]);out[key]=dict(source='yama',title=title,start_date=day,start_time=m[4],venue='מוזיאון אגם',address='מיש״ר 1, ראשון לציון',detail_url=url,booking_url=booking,image_url=meta['content']if meta else'',source_text=txt(p,'.show_details'),ticket_status='sold_out'if'אזלו'in tr.get_text()else'available')
 return list(out.values())

def collect():
 errors={};rows=calendars(errors);urls=sorted(set(x['detail_url']for x in rows if x['source']!='kotar'));details={}
 def read(u):
  try:return u,detail(u),None
  except Exception as ex:return u,{},str(ex)[:200]
 with ThreadPoolExecutor(max_workers=4)as pool:
  for i,(url,result,error)in enumerate(pool.map(read,urls),1):
   details[url]=result
   if error:errors[url]=error
   if i%15==0:print('Detail pages',i,'/',len(urls),flush=True)
 for row in rows:
  if row['source']!='kotar':row.update(details[row['detail_url']])
 for slug in ['גמצ_יק_-_סיור_תיאטרלי_לקטנטנים','הארמון_של_איתי_-_מופע_מחול_לכל_המשפחה']:
  url='https://yama.smarticket.co.il/'+slug
  try:rows.extend(museum_rows(url))
  except Exception as ex:errors[url]=str(ex)[:200]
 return {'checked_at':STAMP,'rows':rows,'errors':errors}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='/tmp/rishon-editorial-sources.json');a=ap.parse_args();result=collect();Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('Saved',len(result['rows']),'calendar rows;',len(result['errors']),'detail failures',flush=True)
if __name__=='__main__':main()
