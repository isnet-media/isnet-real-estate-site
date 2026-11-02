#!/usr/bin/env python3
"""Match official editorial pages to Holon events; never alter ticket sessions."""
import concurrent.futures, hashlib, io, json, re, unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]; CITY=ROOT/'events-preview/holon'; DATA=CITY/'data'
HOSTS=['https://www.mediatheque.org.il/','https://www.cinemaholon.org.il/','https://www.hth.co.il/','https://kids-cinema.org.il/']
HEAD={'User-Agent':'ISNET Holon public cultural guide/1.0'}
def norm(t):
 t=''.join(c for c in unicodedata.normalize('NFKD',t) if not unicodedata.combining(c))
 t=t.replace("'",'').replace('׳','').replace('פיניק 2','פיניק')
 t=re.split(r'\s*מפגש עם',t)[0]
 t=re.sub(r'\s+בדיבוב.*$','',t)
 t=t.replace('מאדם תיק תק','מאדאם תיק תק')
 t=re.sub(r'בין ערביים\s*[-–]?|על הבוקר\s*[-–]?','',t)
 t=re.split(r'\s*[-–]\s*(?:בדיבוב|תיאטרון|תאטרון|טרום|פסטיבל)|\s*\+\s*|\s*\(',t)[0]
 t=re.sub(r'\b(?:מופע|סרט|הצגת|ילדים|הקרנת|טרום בכורה)\b','',t)
 return re.sub(r'[^א-תa-zA-Z0-9]+',' ',t).strip().lower()
def score(a,b):
 a,b=norm(a),norm(b)
 if a==b:return 1
 if len(a)>5 and (b.startswith(a+' ') or a.startswith(b+' ')) and len(b)>5:return .92
 return 0
def get(u):
 r=requests.get(u,headers=HEAD,timeout=22);r.raise_for_status();return BeautifulSoup(r.content,'html.parser')
def image(url,source):
 if not url or urlsplit(url).hostname.removeprefix('www.') not in ['mediatheque.org.il','cinemaholon.org.il','hth.co.il','kids-cinema.org.il','mediatheque-theater.org.il','dmh.org.il'] or '/uploads/' not in url:return None
 if re.search(r'logo|no.pic|(?:^|/)default[.-]',url,re.I):return None
 path=CITY/'assets/events'/(hashlib.sha256(url.encode()).hexdigest()[:20]+'.jpg')
 if not path.exists():
  r=requests.get(url,headers=HEAD,timeout=22);r.raise_for_status();im=Image.open(io.BytesIO(r.content))
  if min(im.size)<180:return None
  im=im.convert('RGB');im.thumbnail((1400,1400));im.save(path,'JPEG',quality=87,optimize=True)
 return str(path.relative_to(CITY))
def enrich(events):
 cache_path=DATA/'media-editorial.json';cache=json.loads(cache_path.read_text()) if cache_path.exists() else {'pages':{}}
 urls={}
 for host in HOSTS:
  try:
   s=get(host)
   links=[(urljoin(host,a['href']),a.get_text(' ',strip=True)) for a in s.select('a[href]')]
   if 'hth.co.il' in host:
    listing=get(urljoin(host,'events/'))
    links += [(urljoin(host,a['href']),a.get_text(' ',strip=True)) for a in listing.select('a[href]')]
   if True:
    robots='Sitemap: https://www.hth.co.il/sitemap_index.xml' if 'hth.co.il' in host else requests.get(urljoin(host,'robots.txt'),headers=HEAD,timeout=15).text
    for sitemap in re.findall(r'^Sitemap:\s*(https://\S+)',robots,re.M):
     index=get(sitemap)
     for loc in index.select('loc'):
      if 'event-sitemap' in loc.text:
       for page in get(loc.text).select('loc'):links.append((page.text,''))
   for u,label in links:
    if urlsplit(u).hostname!=urlsplit(host).hostname or '/events/' not in u:continue
    slug=unquote(urlsplit(u).path).strip('/').split('/')[-1].replace('-',' ')
    urls[u]=[slug,label]
  except Exception as ex:print('SOURCE_UNAVAILABLE',host,str(ex)[:100],flush=True)
 jobs={}
 for e in events:
  allowed=['mediatheque.org.il','cinemaholon.org.il','kids-cinema.org.il'] if e['source_id'] in ['mediatheque','cinematheque','design'] else ['hth.co.il'] if e['source_id']=='hth' else ['mediatheque.org.il','hth.co.il'] if e['source_id']=='mevalim' else []
  candidates=[(max(score(e['title'],x) for x in names),u) for u,names in urls.items() if any(h in u for h in allowed)]
  candidates=[x for x in candidates if x[0]>=.9]
  if 'עולם הדיבוב' in e['title'] and 'האי הנעלם' in e['title']:
   jobs[e['id']]='https://www.mediatheque.org.il/events/מפגש-על-עולם-הדיבוב-עם-עדי-ארד-הקרנת-ה/';continue
  if candidates:jobs[e['id']]=sorted(candidates,key=lambda x:(-x[0], 'cinemaholon' not in x[1] if e['category']=='cinema' else False))[0][1]
 Path('/tmp/holon-media-jobs.json').write_text(json.dumps(jobs,ensure_ascii=False))
 def fetch(u):
  try:
   cached=cache['pages'].get(u,{})
   if cached.get('title') and cached.get('image') and cached.get('checked_at','').startswith(datetime.now(ZoneInfo('Asia/Jerusalem')).date().isoformat()):return u,cached
   s=get(u);h=s.select_one('h1');meta_title=s.select_one('meta[property="og:title"]');title=h.get_text(' ',strip=True) if h else (meta_title.get('content','').split(' • ')[0] if meta_title else '')
   og=s.select_one('meta[property="og:image"]');origin=og.get('content') if og else None
   featured=s.select_one('.single-event-desktop-main-image img,.entry-image img')
   if not origin and featured:origin=featured.get('src')
   im=image(origin,u)
   # Keep source prose only in a research cache; public descriptions are reviewed separately.
   body=s.select_one('.elementor-widget-theme-post-content') or s.select_one('.entry-content') or s
   paragraphs=list(dict.fromkeys(p.get_text(' ',strip=True) for p in body.select('p') if len(p.get_text(' ',strip=True))>60))
   videos=re.findall(r'(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=)|youtu\.be/)([A-Za-z0-9_-]{11})',str(body))
   return u,dict(title=title,image=im,image_origin_url=origin,source_url=u,checked_at=datetime.now(ZoneInfo('Asia/Jerusalem')).isoformat(),trailer_youtube_id=videos[0] if videos else None,source_excerpt=paragraphs[:6])
  except Exception as ex:return u,{'error':str(ex)[:160]}
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  for u,record in pool.map(fetch,sorted(set(jobs.values()))):
   if record.get('image'):cache['pages'][u]=record
   else:print('MEDIA_MISSING',u,record.get('error','no specific image'),flush=True)
 research_path=Path('/tmp/holon-media-research.json')
 research=json.loads(research_path.read_text()) if research_path.exists() else {'pages':{}}
 for u,rec in cache['pages'].items():research['pages'].setdefault(u,{}).update(rec)
 research_path.write_text(json.dumps(research,ensure_ascii=False,indent=2)+'\n')
 cache_path.write_text(json.dumps({'pages':{u:{k:v for k,v in rec.items() if k!='source_excerpt'} for u,rec in cache['pages'].items()}},ensure_ascii=False,indent=2)+'\n')
 good=0
 for e in events:
  u=jobs.get(e['id']);record=cache['pages'].get(u,{})
  if not record.get('image'):
   record=next((r for r in cache['pages'].values() if r.get('image') and score(e['title'],r.get('title',''))>=.9),{})
   if record.get('image'):u=record['source_url']
  if not record.get('image') or (score(e['title'],record['title'])<.9 and not ('עדי ארד' in e['title'] and 'עדי ארד' in record['title'] and 'האי הנעלם' in e['title'] and 'האי הנעלם' in record['title'])):continue
  publisher='תיאטרון חולון' if 'hth.co.il' in u else 'סינמטק חולון' if 'cinemaholon' in u else 'מדיטק חולון'
  e.update(image=record['image'],image_role='official_promotional',image_origin_url=record['image_origin_url'],image_source_url=u,image_credit='תמונת יח״צ: '+publisher,media_checked_at=record['checked_at'])
  if record.get('trailer_youtube_id'):e['trailer_youtube_id']=record['trailer_youtube_id'];e['trailer_source_url']=u
  good+=1
 print('OFFICIAL_MEDIA',good,'of',len(events),'occurrences;',len(cache['pages']),'pages',flush=True)
 return events
if __name__=='__main__':
 p=DATA/'events.json';d=json.loads(p.read_text());enrich(d['events']);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
