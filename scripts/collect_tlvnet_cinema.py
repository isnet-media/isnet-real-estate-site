import urllib.request,urllib.parse,json,re,concurrent.futures,datetime,hashlib
from pathlib import Path
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo
root=Path(__file__).resolve().parents[1]/'events-preview/tel-aviv/data';root.mkdir(parents=True,exist_ok=True);now=datetime.datetime.now(ZoneInfo('Asia/Jerusalem'));stamp=now.isoformat();s=BeautifulSoup(urllib.request.urlopen('https://www.lev.co.il/location/telaviv/',timeout=20).read(),'html.parser');dates=[o['value'] for o in s.select('#locationfilterdate1 option[value]')][:7]
def levday(day):
 params={'clang':'he','action':'movie_on_location_new','loc':'לב תל אביב','date':day};url='https://www.lev.co.il/wp-content/themes/lev/ajax_data.php?'+urllib.parse.urlencode(params)
 try:
  html=urllib.request.urlopen(url,timeout=18).read().decode();return day,html,url
 except Exception as e:return day,'',url
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:pages=list(ex.map(levday,dates))
movies={};reports=[]
for day,html,url in pages:
 soup=BeautifulSoup(html,'html.parser');rows=soup.select('a.topmenua[data-pcode]');reports.append({'date':day,'sessions':len(rows),'source_url':url})
 for a in rows:
  tm=a.select_one('span');t=tm.get_text(strip=True) if tm else '';title=' '.join(a.get_text(' ',strip=True).replace(t,'').split()).split('- מדובב')[0].strip();dt=datetime.datetime.fromisoformat(day+'T'+t).replace(tzinfo=ZoneInfo('Asia/Jerusalem'))
  if dt<=now:continue
  source=a.parent.select_one('a.smovielink');src=source['href'] if source else 'https://www.lev.co.il/location/telaviv/';key=hashlib.sha256(title.encode()).hexdigest()[:12]
  m=movies.setdefault(key,{'id':'lev-tlv-'+key,'title':title,'synopsis':None,'poster_url':None,'poster_rights_status':'not_supplied','source_url':src,'verified_at':stamp,'venues':[{'id':'lev-tlv','name':'לב תל אביב — דיזנגוף סנטר','address':'דיזנגוף 50, קומה 3, תל אביב','locality':'תל אביב-יפו','nearby_city':False,'article_url':src,'schedule':{},'sessions':[]}]});v=m['venues'][0];v['schedule'].setdefault(day,[]).append(t);v['sessions'].append({'date':day,'time':t,'source_event_id':a['data-pcode'],'booking_url':a['href']})
result={'city':'tel-aviv','source':'LEV official website','source_url':'https://www.lev.co.il/location/telaviv/','updated_at':stamp,'movies':list(movies.values()),'source_reports':reports};(root/'lev-tlv.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print({'lev_movies':len(movies),'lev_sessions':sum(len(m['venues'][0]['sessions']) for m in movies.values()),'reports':reports})
# Cinematheque date explicitly printed in official homepage; upcoming cards refer to this date.
soup=BeautifulSoup(urllib.request.urlopen('https://www.cinema.co.il/',timeout=20).read(),'html.parser');date_text=soup.select_one('#upcomingDateWrap .date-time').get_text();dm=re.search(r'(\d{2})\.(\d{2})\.(\d{2})',date_text);day='20'+dm[3]+'-'+dm[2]+'-'+dm[1];wrap=soup.select_one('#upcomingDateWrap').parent;movies=[]
for box in wrap.select('.box[event_id]'):
 title=box.select_one('h4');link=box.select_one('a.details');sessionlinks=box.select('a.cal_link');img=box.select_one('img[data-src]');schedule=[];sessions=[]
 if not title or not link:continue
 for a in sessionlinks:
  tm=a.select_one('.time');t=tm.get_text(strip=True) if tm else '';dt=datetime.datetime.fromisoformat(day+'T'+t).replace(tzinfo=ZoneInfo('Asia/Jerusalem'))
  if dt<=now:continue
  schedule.append(t);sessions.append({'date':day,'time':t,'booking_url':a['href']})
 if not schedule:continue
 movies.append({'id':'cintlv-'+box['event_id'],'title':title.get_text(' ',strip=True),'synopsis':None,'poster_url':None,'poster_candidate_url':img['data-src'] if img else None,'poster_rights_status':'reuse_permission_not_verified','source_url':link['href'],'verified_at':stamp,'venues':[{'id':'cinematheque-tlv','name':'סינמטק תל אביב','address':'הארבעה 5, תל אביב','locality':'תל אביב-יפו','nearby_city':False,'article_url':link['href'],'schedule':{day:schedule},'sessions':sessions}]})
result={'city':'tel-aviv','source':'Tel Aviv Cinematheque official website','source_url':'https://www.cinema.co.il/','updated_at':stamp,'movies':movies};(root/'cinematheque-tlv.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print({'cinematheque_movies':len(movies),'cinematheque_sessions':sum(len(m['venues'][0]['sessions']) for m in movies)})

# Enrich primary-source facts and official trailer embeds; no copied descriptions.
lev=json.loads((root/'lev-tlv.json').read_text())
oldpath=root/'cinema-local.json'
old=json.loads(oldpath.read_text()) if oldpath.exists() else {'movies':[]}
oldmovies={m['id']:m for m in old.get('movies',[])}
def metadata(m):
 try:
  page=BeautifulSoup(urllib.request.urlopen(m['source_url'],timeout=12).read(),'html.parser')
  txt=page.get_text(' ',strip=True);run=re.search(r'(\d{2,3})\s*דקות',txt)
  if run:m['runtime_minutes']=int(run[1])
  frames=[f.get('src','') for f in page.select('iframe[src]')]
  yt=next((re.search(r'(?:embed/|v=)([\w-]{11})',u)[1] for u in frames if 'youtube' in u and re.search(r'(?:embed/|v=)([\w-]{11})',u)),None)
  if yt:m['trailer_youtube_id']=yt;m['trailer_source_url']=m['source_url']
 except Exception:
  previous=oldmovies.get(m['id'],{})
  for key in ['trailer_youtube_id','trailer_source_url','runtime_minutes','age_rating']:
   if previous.get(key):m[key]=previous[key]
 return m
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:lev['movies']=list(ex.map(metadata,lev['movies']))
ct=json.loads((root/'cinematheque-tlv.json').read_text())
combined=[]
for source in [lev,ct]:
 rows=source.get('movies',[])
 if rows:
  combined.extend(rows)
 else:
  # Preserve source verification timestamps; never label a failed source fresh.
  sid='lev-tlv' if source is lev else 'cinematheque-tlv'
  combined.extend(m for m in old.get('movies',[]) if any(v.get('id')==sid for v in m.get('venues',[])))
for m in combined:
 if m.get('trailer_youtube_id'):
  m['poster_url']='https://i.ytimg.com/vi/'+m['trailer_youtube_id']+'/hqdefault.jpg';m['poster_credit']='תמונה מקדימון רשמי · YouTube'
 elif m.get('poster_candidate_url') and any(v['id']=='cinematheque-tlv' for v in m['venues']):
  m['poster_url']=m['poster_candidate_url'];m['poster_credit']='כרזה מטעם סינמטק תל אביב';m['poster_rights_status']='organizer_publicity'
if not combined:raise SystemExit('No verified cinema data; refusing replacement')
result={'city':'tel-aviv','updated_at':stamp,'movies':combined,'sources':[{'name':x['source'],'url':x['source_url'],'checked_at':x['updated_at']} for x in [lev,ct]]}
temp=oldpath.with_suffix('.tmp');temp.write_text(json.dumps(result,ensure_ascii=False,indent=2));temp.replace(oldpath)
print({'public_cinema_movies':len(combined),'updated_at':stamp})
