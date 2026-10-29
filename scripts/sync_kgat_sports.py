"""Official senior representative-team home fixtures, with explicit unknown times/venues."""
import argparse,concurrent.futures,hashlib,json,re
from datetime import datetime,date,timedelta
from pathlib import Path
from urllib.parse import urljoin,urlsplit,parse_qs,urlencode,urlunsplit
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup
from kgat_sport_rules import repair
ROOT=Path(__file__).resolve().parents[1];CITY=ROOT/'events-preview/kiryat-gat'
MANAGED='kgat_sports';TODAY=datetime.now(ZoneInfo('Asia/Jerusalem')).date()
TEAMS=[('maccabi','מכבי קריית גת','7521','כדורגל גברים'),('beitar','בית"ר ע. קרית גת דודו','3627','כדורגל גברים'),('women','מ.ס. קרית גת','6159','כדורגל נשים')]
BASKET='https://ibasketball.co.il/team/3043-א-ס-אשקלון-קרית-גת/'
def normalize(s):return re.sub(r'\s+',' ',s).strip()
def get(url):
 r=requests.get(url,timeout=30,headers={'User-Agent':'ISNET local events source reader'});r.raise_for_status();return r.text
def fixture(key,home,away,day,time,venue,url,source,branch):
 time=time if time and time!='00:00' else None
 outside=bool(venue and not re.search(r'קרי[יי]?ת גת',venue))
 location=(venue+' — מחוץ לקריית גת' if outside else venue) or 'המגרש או האולם טרם פורסם'
 event_id='kgat_sport_'+hashlib.sha256((key+'|'+home+'|'+away+'|'+day).encode()).hexdigest()[:20]
 desc=f'משחק בית של {home} מול {away}. {branch}. '
 desc+=(f'המשחק ייערך ב{location}. ' if venue else 'מיקום המשחק טרם פורסם. ')
 desc+=('שעת המשחק טרם פורסמה. ' if not time else '')+'המועדים כפופים לעדכוני האיגוד; יש לוודא מיקום, שעה ופרטי כניסה במקור לפני היציאה.'
 return dict(event_id=event_id,city='קריית גת',title=home+' — '+away,description=desc,series_description=desc,start_date=day,start_time=time,end_date=None,end_time=None,venue=location,address=None,category='sport',subcategory='sport-events',category_memberships=[{'category':'sport','subcategory':'sport-events'}],audiences=['adults','families'],activity_type='sport',sport_event_kind='home_game',sport_branch='כדורסל' if 'כדורסל' in branch else 'כדורגל',sport_competition=branch,home_team=home,away_team=away,is_home_game=True,representative_team=True,managed_by=MANAGED,sport_team_id=key,time_status='confirmed' if time else 'pending',venue_status='published' if venue else 'pending',location_scope='outside_city' if outside else 'city' if venue else 'pending',ticket_url=url,purchase_url=None,purchase_source='schedule_information',source_url=url,source_type='official',sources=[{'name':source,'url':url,'type':'official'}],source_last_checked=TODAY.isoformat(),ticket_status='unknown',is_free=None,price_min_ils=None,price_max_ils=None,image_url='',image_publishable=False,image_verified=False,is_active=True,status='published',publication_status='published')
def football(html,team,today=TODAY):
 key,expected,_,branch=team;source='https://www.football.org.il/team-details/team-games/?season_id=28&team_id='+team[2]
 soup=BeautifulSoup(html,'html.parser');out=[];count=0
 for a in soup.select('a.table_row[href*="game_id="]'):
  cols=a.select('.table_col')
  for sp in a.select('.sr-only'):sp.decompose()
  vals=[normalize(c.get_text(' ',strip=True)) for c in cols]
  if len(vals)<5:continue
  try:day=datetime.strptime(vals[0],'%d/%m/%Y').date()
  except ValueError:continue
  count+=1
  if day<today or vals[4] or ' - ' not in vals[1]:continue
  home,away=map(normalize,vals[1].split(' - ',1))
  if home!=expected or 'חופשית' in away:continue
  link=urljoin(source,a['href']) if re.search(r'game_id=[1-9]\d*',a['href']) else source
  out.append(fixture(key,home,away,day.isoformat(),vals[3],vals[2],link,'ההתאחדות לכדורגל',branch))
 if count<10:raise ValueError('Incomplete football schedule '+key)
 return out
def basket_rows(rows,today=TODAY,venues=None):
 out=[]
 for r in rows:
  home=r.get('home',{}).get('team','');away=r.get('away',{}).get('team','')
  if not re.search(r'קרי[יי]?ת גת',home) or not away or r.get('status') not in ['future','publish']:continue
  if (r.get('home') or {}).get('points') is not None:continue
  try:dt=datetime.fromisoformat(r['date'])
  except (ValueError,KeyError):continue
  if dt.date()<today:continue
  # Never substitute the club's usual hall for an unverified match venue.
  venue='; '.join((venues or {}).get(str(v),'') for v in r.get('venues',[]) if (venues or {}).get(str(v)))
  e=fixture('basket',home,away,dt.date().isoformat(),dt.strftime('%H:%M'),venue,r['link'],'איגוד הכדורסל','כדורסל — '+r.get('league',{}).get('name',''))
  e['venue_ids']=r.get('venues',[])
  out.append(e)
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--fixtures-dir');args=ap.parse_args();feed=json.loads((CITY/'data/events.json').read_text());fresh=[];reports=[];successful=set()
 for team in TEAMS:
  key=team[0];url='https://www.football.org.il/team-details/team-games/?season_id=28&team_id='+team[2]
  try:
   html=(Path(args.fixtures_dir)/(key+'.html')).read_text() if args.fixtures_dir else get(url)
   rows=football(html,team);fresh+=rows;successful.add(key);reports.append(dict(team=key,url=url,status='ok',home_fixtures=len(rows)))
  except Exception as exc:reports.append(dict(team=key,url=url,status='error',error=str(exc)[:200]))
 try:
  if args.fixtures_dir:rows=json.loads((Path(args.fixtures_dir)/'basket.json').read_text())
  else:
   soup=BeautifulSoup(get(BASKET),'html.parser');base=soup.select_one('table.data-table[data-ajax-url]')['data-ajax-url'];parts=urlsplit(base);params=parse_qs(parts.query);urls=[]
   # Bounded published monthly schedule queries, October through April this season.
   for n in range(7):
    month=(TODAY.month-1+n)%12+1;year=TODAY.year+(TODAY.month-1+n)//12
    p={k:v[-1] for k,v in params.items()};p['month']=f'{year}-{month:02}';urls.append(urlunsplit((parts.scheme,parts.netloc,parts.path,urlencode(p),'')))
   with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:parts_data=list(ex.map(lambda u:json.loads(get(u)),urls))
   if not all(isinstance(x,list) for x in parts_data):raise ValueError('Basketball schedule format changed')
   rows=[r for part in parts_data for r in part]
  venues={}
  if args.fixtures_dir:
   vp=Path(args.fixtures_dir)/'basket-venues.json'
   if vp.exists():venues=json.loads(vp.read_text())
  else:
   venue_ids={v for r in rows if r.get('teams',[None])[0]==168288 for v in r.get('venues',[])}
   for v in venue_ids:
    try:
     info=json.loads(get('https://ibasketball.co.il/wp-json/sportspress/v2/venues/'+str(v)));venues[str(v)]=info['name']
    except Exception:pass
  games=basket_rows(rows,venues=venues);fresh+=games;successful.add('basket');reports.append(dict(team='basket',url=BASKET,status='ok',home_fixtures=len(games)))
 except Exception as exc:reports.append(dict(team='basket',url=BASKET,status='error',error=str(exc)[:200]))
 old=[repair(e) for e in feed['events'] if not(e.get('managed_by')==MANAGED and e.get('sport_team_id') in successful)]
 byid={e['event_id']:e for e in old}
 for e in fresh:
  prev=next((x for x in feed['events'] if x['event_id']==e['event_id']),{})
  # An approved event image or manual editorial description wins over intake defaults.
  if prev.get('image_verified') and prev.get('image_publishable'):
   e.update({k:v for k,v in prev.items() if k.startswith(('image_','thumbnail_'))})
  if prev.get('description_manual_override'):e.update(description=prev['description'],description_manual_override=True)
  byid[e['event_id']]=e
 feed['events']=list(byid.values());feed['stats']={'events':len(feed['events'])}
 (CITY/'data/events.json').write_text(json.dumps(feed,ensure_ascii=False,indent=2)+'\n')
 (ROOT/'events-preview/admin/data/kgat-sports-report.json').write_text(json.dumps({'checked_at':TODAY.isoformat(),'sources':reports,'policy':'Senior representative-team HOME fixtures, competitions, public sport participation. No classes, lectures, away games or 00:00 placeholders. Unknown venues remain explicit; home fixtures outside the city are labeled.'},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(reports,ensure_ascii=False))
if __name__=='__main__':main()
