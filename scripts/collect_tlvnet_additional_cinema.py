"""Additional TLV cinema sources. Import collect_jaffa() in scheduled cinema collector.
No invented schedules; parse full year from official calendar URL. Failure returns no data
and caller should preserve previously verified unexpired records, not relabel them fresh.
"""
import datetime, hashlib, json, re
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

JAFFA_URL='https://www.jaffacinema.com/'

def collect_jaffa(html=None, now=None):
    now=now or datetime.datetime.now(ZoneInfo('Asia/Jerusalem'))
    stamp=now.isoformat()
    if html is None:
        r=requests.get(JAFFA_URL,timeout=25);r.raise_for_status();html=r.text
    soup=BeautifulSoup(html,'html.parser');movies=[]
    for card in soup.select('article.jaffa-movie-card[data-movie-id]'):
        title=card.select_one('.jaffa-movie-card__title')
        if not title:continue
        sessions=[];schedule={};src=None
        for a in card.select('a.jaffa-movie-card__screening[href]'):
            u=a['href'];dm=re.search(r'/calendar/(\d{2})-(\d{2})-(\d{4})-(\d{2})(\d{2})-',u)
            if not dm:continue
            day=f'{dm[3]}-{dm[2]}-{dm[1]}';time=f'{dm[4]}:{dm[5]}'
            when=datetime.datetime.fromisoformat(day+'T'+time).replace(tzinfo=ZoneInfo('Asia/Jerusalem'))
            if when<=now:continue
            src=src or u;schedule.setdefault(day,[]).append(time)
            sessions.append({'date':day,'time':time,'booking_url':u})
        if not sessions:continue
        meta=card.select_one('.jaffa-movie-card__meta');txt=meta.get_text(' ',strip=True) if meta else ''
        runtime=re.search(r"(\d+)\s*ש'\s*(\d+)\s*דק",txt)
        duration=int(runtime[1])*60+int(runtime[2]) if runtime else None
        director=re.search(r'בימוי:\s*(.*?)\s*משך הקרנה:',txt)
        trailer=card.select_one('a.jaffa-movie-card__trailer[href]')
        yt=re.search(r'(?:youtu\.be/|[?&]v=|embed/)([\w-]{11})',trailer['href']) if trailer else None
        img=card.select_one('img.jaffa-movie-card__image[src]')
        m={'id':'jaffa-cinema-'+card['data-movie-id'],'title':title.get_text(' ',strip=True),
           'synopsis':('סרט בבימוי '+director[1]+'. ' if director else '')+'הקרנה בקולנוע יפו. פרטי הסרט והכרטיסים באתר הקולנוע.',
           'runtime_minutes':duration,'source_url':src,'verified_at':stamp,
           'poster_candidate_url':img['src'] if img else None,
           'poster_rights_status':'organizer_publicity_candidate_permission_not_verified',
           'venues':[{'id':'jaffa-cinema','name':'קולנוע יפו','address':'מרזוק ועזר 14, תל אביב-יפו',
                      'locality':'תל אביב-יפו','nearby_city':False,'article_url':src,'schedule':schedule,'sessions':sessions}]}
        if yt:
            m.update(trailer_youtube_id=yt[1],trailer_source_url=JAFFA_URL,
                     poster_url='https://i.ytimg.com/vi/'+yt[1]+'/hqdefault.jpg',poster_credit='תמונה מקדימון רשמי · YouTube')
        movies.append(m)
    if not movies:raise ValueError('No future official Jaffa screenings found')
    return {'city':'tel-aviv','source':'קולנוע יפו — האתר הרשמי','source_url':JAFFA_URL,
            'updated_at':stamp,'movies':movies,
            'sources':[{'name':'קולנוע יפו','url':JAFFA_URL,'checked_at':stamp}]}


def collect_ravhen(now=None):
    import concurrent.futures
    now=now or datetime.datetime.now(ZoneInfo('Asia/Jerusalem'));stamp=now.isoformat()
    base='https://www.rav-hen.co.il/rh/data-api-service/v1/quickbook/10104/film-events/in-cinema/1071/at-date/'
    days=[(now.date()+datetime.timedelta(days=i)).isoformat() for i in range(7)]
    def daydata(day):
        url=base+day+'?attr=&lang=he_IL'
        r=requests.get(url,timeout=20);r.raise_for_status();return day,r.json()['body'],url
    pages=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        for fut in [ex.submit(daydata,d) for d in days]:
            try:pages.append(fut.result())
            except Exception:pass
    movies={};reports=[]
    for day,body,url in pages:
        reports.append({'date':day,'source_url':url,'events':len(body.get('events',[]))})
        filmmap={f['id']:f for f in body.get('films',[])}
        for event in body.get('events',[]):
            if str(event.get('cinemaId'))!='1071':continue
            dt=datetime.datetime.fromisoformat(event['eventDateTime']).replace(tzinfo=ZoneInfo('Asia/Jerusalem'))
            if dt<=now:continue
            f=filmmap.get(event['filmId'])
            if not f:continue
            key='ravhen-dizengoff-'+str(f['id']);day=dt.date().isoformat();tm=dt.strftime('%H:%M')
            m=movies.setdefault(key,{'id':key,'title':f['name'],'runtime_minutes':f.get('length'),
                'synopsis':'סרט המוצג ברב חן דיזנגוף. פרטים ומועדים באתר הרשמי של הקולנוע.',
                'source_url':f['link'],'verified_at':stamp,'poster_candidate_url':f.get('posterLink'),
                'poster_rights_status':'organizer_publicity_candidate_permission_not_verified',
                'is_family':'family' in f.get('attributeIds',[]),
                'venues':[{'id':'ravhen-dizengoff','name':'רב חן דיזנגוף','address':'בן עמי 16, כיכר דיזנגוף, תל אביב-יפו','locality':'תל אביב-יפו','nearby_city':False,
                    'article_url':'https://www.rav-hen.co.il/cinemas/dizengoff/1071','schedule':{},'sessions':[]}]})
            yt=re.search(r'(?:youtu\.be/|[?&]v=|embed/)([\w-]{11})',f.get('videoLink') or '')
            if yt:m.update(trailer_youtube_id=yt[1],trailer_source_url=f['link'])
            v=m['venues'][0]
            if tm not in v['schedule'].setdefault(day,[]):v['schedule'][day].append(tm)
            v['sessions'].append({'date':day,'time':tm,'source_event_id':event['id'],'booking_url':event.get('bookingLink') or f['link'],'auditorium':event.get('auditorium')})
    if not movies:raise ValueError('No future official Rav-Hen Dizengoff data')
    return {'city':'tel-aviv','updated_at':stamp,'source':'רב חן — האתר הרשמי','source_url':'https://www.rav-hen.co.il/cinemas/dizengoff/1071','movies':list(movies.values()),'source_reports':reports,
        'sources':[{'name':'רב חן דיזנגוף','url':'https://www.rav-hen.co.il/cinemas/dizengoff/1071','checked_at':stamp}]}

def verify_publicity_posters(data):
    """User confirmed publicity usage. Verify actual image bytes before enabling."""
    from PIL import Image
    import io,concurrent.futures
    def check(m):
        u=m.get('poster_candidate_url')
        if not u:return m
        try:
            r=requests.get(u,timeout=20);r.raise_for_status()
            img=Image.open(io.BytesIO(r.content));img.verify()
            img=Image.open(io.BytesIO(r.content))
            if min(img.size)<120:raise ValueError('tiny image')
            # Pixel variance catches common solid/loading placeholders, not just HTTP200.
            from PIL import ImageStat
            if max(ImageStat.Stat(img.convert('RGB').resize((64,64))).stddev)<10:raise ValueError('placeholder')
            m.update(poster_url=u,poster_credit='תמונת יח״צ מטעם '+('קולנוע יפו' if m['id'].startswith('jaffa-') else 'רב חן'),
                poster_rights_status='user_confirmed_organizer_publicity',poster_verified=True,
                poster_evidence_url=(JAFFA_URL if m['id'].startswith('jaffa-') else m['source_url']),poster_width=img.width,poster_height=img.height)
        except Exception as e:m['poster_verification_error']=str(e)
        return m
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:data['movies']=list(ex.map(check,data['movies']))
    return data

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]/'events-preview/tel-aviv/data';root.mkdir(parents=True,exist_ok=True)
    outpath=root/'cinema-additional.json';old=json.loads(outpath.read_text()) if outpath.exists() else {'movies':[]}
    movies=[];sources=[]
    for name,collector,venue in [('קולנוע יפו',collect_jaffa,'jaffa-cinema'),('רב חן דיזנגוף',collect_ravhen,'ravhen-dizengoff')]:
        try:
            data=verify_publicity_posters(collector());movies+=data['movies'];sources.append({'name':name,'status':'ok','count':len(data['movies']),'checked_at':data['updated_at']})
        except Exception as error:
            movies.extend(m for m in old['movies'] if any(v['id']==venue for v in m['venues']));sources.append({'name':name,'status':'failed','error':type(error).__name__})
    if not movies:raise SystemExit('No verified additional cinema; preserving prior feed')
    result={'city':'tel-aviv','updated_at':datetime.datetime.now(ZoneInfo('Asia/Jerusalem')).isoformat(),'movies':movies,'sources':sources}
    outpath.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print({'movies':len(movies),'sources':sources})
