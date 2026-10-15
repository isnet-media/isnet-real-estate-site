#!/usr/bin/env python3
"""Read the same public Planet branch calendar used by its website (branch 1072).

A complete dates/films/events snapshot is required before replacing schedules.
No booking, authentication or challenge endpoint is used.
"""
import json,re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup

SITE='https://www.planetcinema.co.il'
BRANCH='1072'
BRANCH_URL=SITE+'/cinemas/rishon_letziyon/1072'
API=SITE+'/il/data-api-service/v1'
QUICK=API+'/quickbook/10100'
TZ=ZoneInfo('Asia/Jerusalem')

def get(url):
 r=requests.get(url,timeout=30);r.raise_for_status();return r.json()

def parse_day(body,requested_day,rows):
 films={str(f['id']):f for f in body['films']}
 for e in body['events']:
  if str(e['cinemaId'])!=BRANCH:raise ValueError('Non-Rishon event in Planet branch response')
  if e['businessDay']!=requested_day:raise ValueError('Unexpected Planet business date')
  f=films.get(str(e['filmId']))
  if not f:raise ValueError('Planet event missing its film metadata')
  dt=datetime.fromisoformat(e['eventDateTime'])
  if dt.tzinfo:dt=dt.astimezone(TZ)
  day,clock=dt.date().isoformat(),dt.strftime('%H:%M')
  delta=(dt.date()-datetime.fromisoformat(requested_day).date()).days
  if delta not in [0,1]or(delta==1 and dt.hour>=8):raise ValueError('Event datetime conflicts with Planet business date')
  booking=e.get('bookingLink')or e.get('bookingRouterLaunchLink')
  if not booking or not (urlparse(booking).hostname or '').endswith('.planetcinema.co.il'):raise ValueError('Unverified Planet booking destination')
  if e.get('soldOut')or e.get('compositeBookingLink',{}).get('blockOnlineSales'):continue
  attrs=f.get('attributeIds',[])
  row=rows.setdefault(str(f['id']),dict(source_id=str(f['id']),title=f['name'],source_url=f['link'],venue_id='planet',source_branch_id=BRANCH,schedule_source_url=BRANCH_URL,synopsis='',genres=[],runtime_minutes=f.get('length'),poster_source_url=f.get('posterLink'),poster_alternatives=[f.get('posterLink')],trailer_url=f.get('videoLink'),is_family=any(a in attrs for a in ['family','animation','kids']),schedule={},sessions=[]))
  row['schedule'].setdefault(day,set()).add(clock)
  row['sessions'].append(dict(date=day,time=clock,source_event_id=str(e['id']),booking_url=booking,screen=e.get('auditorium'),languages=e.get('languages',{}),dubbed_language=next(iter(e.get('languages',{}).get('dubbed',[])),None),subtitled_language=next(iter(e.get('languages',{}).get('subtitles',[])),None)))
 return rows

def collect():
 r=requests.get(BRANCH_URL,timeout=30);r.raise_for_status();p=BeautifulSoup(r.text,'html.parser');component=p.select_one('schedule-component')
 if not component or component.get('data-default-cinema')!=BRANCH or 'ראשון לציון'not in component.get('data-title-param',''):raise ValueError('Planet Rishon branch identity changed')
 today=datetime.now(TZ).date();until=(today+timedelta(days=35)).isoformat()
 dates=get(QUICK+'/dates/in-cinema/'+BRANCH+'/until/'+until+'?attr=')['body']['dates']
 if not dates or any(not re.fullmatch(r'\d{4}-\d{2}-\d{2}',d)for d in dates):raise ValueError('Incomplete Planet dates response')
 dates=sorted(set(d for d in dates if today.isoformat()<=d<=until))
 def read(day):return day,get(QUICK+'/film-events/in-cinema/'+BRANCH+'/at-date/'+day+'?attr=')['body']
 print('Planet Rishon: reading',len(dates),'published dates',flush=True)
 rows={}
 with ThreadPoolExecutor(max_workers=4)as pool:
  for day,body in pool.map(read,dates):parse_day(body,day,rows)
 print('Planet Rishon: collected',len(rows),'film versions',flush=True)
 if not rows:raise ValueError('No verified Planet sessions; preserve previous schedules')
 for row in rows.values():row['schedule']={d:sorted(t)for d,t in row['schedule'].items()}
 def details(row):
  try:
   f=get(API+'/10100/films/byDistributorCode/'+row['source_id'])['body']['filmDetails']
   if str(f['id'])!=row['source_id']:raise ValueError('Film identity mismatch')
   genres={'action':'פעולה','adventure':'הרפתקאות','animation':'אנימציה','comedy':'קומדיה','drama':'דרמה','family':'משפחה','horror':'אימה','thriller':'מתח','romance':'רומנטיקה','sci-fi':'מדע בדיוני','fantasy':'פנטזיה'}
   row.update(synopsis=BeautifulSoup(f.get('synopsis')or'','html.parser').get_text(' ',strip=True),genres=[genres.get(g,g)for g in f.get('categoriesAttributes',[])],age_rating={'all':'מותר לכל','14-plus':'14+','16-plus':'16+','18-plus':'18+'}.get(f.get('ageRestrictionName'),f.get('ageRestrictionName')),poster_source_url=f.get('posterLinkLarge')or row['poster_source_url'])
   row['is_family']=row['is_family']or any(g in f.get('categoriesAttributes',[])for g in ['family','animation','kids'])
  except Exception as ex:row['detail_error']=str(ex)[:180]
  return row
 with ThreadPoolExecutor(max_workers=4)as pool:return list(pool.map(details,rows.values()))


def verify_poster(row):
 # Both sizes are URLs explicitly supplied by the official film response.
 for url in dict.fromkeys([row.get('poster_source_url'),*row.get('poster_alternatives',[])]):
  if not url:continue
  try:
   with requests.get(url,stream=True,timeout=15)as response:
    response.raise_for_status();kind=response.headers.get('Content-Type','')
    if not kind.startswith('image/'):raise ValueError('Official poster did not return an image')
   row['poster_source_url']=url
   row['poster_verified']={'url':url,'source_url':row['source_url'],'verified_at':datetime.now(TZ).isoformat(),'content_type':kind,'delivery':'remote_official_source'}
   row.pop('poster_error',None);break
  except Exception as ex:row['poster_error']=str(ex)[:180]
 return row
