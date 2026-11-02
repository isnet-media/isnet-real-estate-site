"""Reuse approved artwork only for the same named production, never its dates."""
import concurrent.futures,hashlib,io,json
from pathlib import Path
import requests
from PIL import Image
from enrich_holon_media import norm,score
ROOT=Path(__file__).resolve().parents[1];CITY=ROOT/'events-preview/holon'
def enrich(events):
 bank=json.loads((ROOT/'events-preview/media-bank/data/media.json').read_text())['media']
 productions=json.loads((ROOT/'events-preview/media-bank/data/productions.json').read_text())['productions'];media={x['media_id']:x for x in bank}
 jobs=[]
 for e in events:
  if e.get('image_role')=='official_promotional':continue
  matches=[p for p in productions if p.get('preferred_media_id') and score(e['title'],p['name'])>=.9]
  if not matches:continue
  production=max(matches,key=lambda p:score(e['title'],p['name']));m=media[production['preferred_media_id']]
  if m.get('status')!='approved' or not m.get('verified') or not m.get('publishable') or m.get('ai_generated'):continue
  jobs.append((e,m,production['name']))
 def download(job):
  e,m,name=job;u=m['url'];path=CITY/'assets/events'/('production-'+hashlib.sha256(u.encode()).hexdigest()[:16]+'.jpg')
  try:
   if not path.exists():
    if u.startswith('/events-preview/'):im=Image.open(ROOT/u.lstrip('/'))
    elif u.startswith('https://'):
     r=requests.get(u,timeout=20);r.raise_for_status();im=Image.open(io.BytesIO(r.content))
    else:return
    if min(im.size)<120:return
    im=im.convert('RGB');im.thumbnail((1400,1400));im.save(path,'JPEG',quality=87,optimize=True)
   e.update(image=str(path.relative_to(CITY)),image_role='official_promotional',image_origin_url=m.get('origin_url')or u,image_source_url=m.get('source_url')if str(m.get('source_url','')).startswith('https://')else m.get('origin_url')or u,image_credit=m.get('credit')or'תמונת יח״צ של ההפקה — מאגר המדיה המאומת של ISNET',media_production_match=name)
  except Exception as ex:print('PRODUCTION_MEDIA_UNAVAILABLE',name,str(ex)[:100])
 with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:list(pool.map(download,jobs))
