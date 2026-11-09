#!/usr/bin/env python3
"""Audit the official film category; publish only exact, city-owned screenings.
Runs inside the existing serialized Kiryat Gat collector after event/media intake.
A failed or empty response never erases previously verified cinema data.
"""
import hashlib,json,re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]/'events-preview/kiryat-gat/data'
SOURCE='https://matnaskg.smarticket.co.il/סרטים_page_39'
MONTHS=dict(zip(['ינואר','פברואר','מרץ','אפריל','מאי','יוני','יולי','אוגוסט','ספטמבר','אוקטובר','נובמבר','דצמבר'],range(1,13)))
def parse(html,now):
 soup=BeautifulSoup(html,'html.parser'); rows=[]
 for a in soup.select('a.show[href]'):
  title=a.select_one('h2');day=a.select_one('.date_container');time=a.select_one('.time_container');venue=a.select_one('.theater_container');category=a.select_one('.category')
  if not all([title,day,time,venue,category]) or 'סרטים' not in category.get_text():continue
  if not re.search(r'קרי[יי]?ת\s*גת',venue.get_text()):continue
  dm=re.search(r'(\d{1,2})\s+ב?([א-ת]+)\s+(20\d{2})',day.get_text(' ',strip=True));tm=re.search(r'\b(\d{1,2}:\d{2})\b',time.get_text())
  if not dm or not tm or dm[2] not in MONTHS:continue
  try:at=datetime(int(dm[3]),MONTHS[dm[2]],int(dm[1]),*map(int,tm[1].split(':')),tzinfo=ZoneInfo('Asia/Jerusalem'))
  except ValueError:continue
  if at<now:continue
  rows.append(dict(title=title.get_text(' ',strip=True),date=at.date().isoformat(),time=at.strftime('%H:%M'),booking_url=urljoin(SOURCE,a['href'])))
 return rows

def run():
 now=datetime.now(ZoneInfo('Asia/Jerusalem'));report={'checked_at':now.isoformat(),'source_url':SOURCE,'status':'failed','screenings':[]}
 try:
  response=requests.get(SOURCE,timeout=35,headers={'User-Agent':'ISNET Cinema Schedule Check (https://isnet.co.il/)'});response.raise_for_status()
  soup=BeautifulSoup(response.content,'html.parser')
  if not soup.select_one('h1') or 'סרטים' not in soup.select_one('h1').get_text():raise ValueError('Official cinema category not recognized')
  rows=parse(response.content,now);report.update(status='ok',screenings=rows,future_screenings=len(rows),future_films=len({r['title'] for r in rows}))
  cinema=json.loads((ROOT/'cinema.json').read_text()); movies=cinema['movies'];norm=lambda s:re.sub(r'\W','',s)
  for row in rows:
   movie=next((m for m in movies if norm(m['title'])==norm(row['title'])),None)
   if movie is None:
    movie={'id':'kgat-film-'+hashlib.sha256(norm(row['title']).encode()).hexdigest()[:12],'title':row['title'],'synopsis':row['title']+' — הקרנה בהיכל התרבות קריית גת. פרטים וכרטיסים באתר המארגן.','poster_url':None,'venues':[]};movies.append(movie)
   venue=next((v for v in movie['venues'] if v['id']=='municipal-hall'),None)
   if venue is None:
    venue={'id':'municipal-hall','name':'היכל התרבות קריית גת','article_url':row['booking_url'],'schedule':{},'sessions':[]};movie['venues'].append(venue)
   times=venue.setdefault('schedule',{}).setdefault(row['date'],[])
   if row['time'] not in times:times.append(row['time'])
   session={k:row[k] for k in ['date','time','booking_url']}
   if session not in venue.setdefault('sessions',[]):venue['sessions'].append(session)
  cinema['schedule_checked_at']=now.isoformat();cinema['schedule_source_url']=SOURCE
  if rows:(ROOT/'cinema.json').write_text(json.dumps(cinema,ensure_ascii=False,indent=2)+'\n')
 except Exception as exc:report['error']=str(exc)[:250]
 (ROOT/'cinema-scan-status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(report,ensure_ascii=False))
 if report['status']!='ok':raise SystemExit('Cinema source check failed; previous screenings preserved')
if __name__=='__main__':run()
