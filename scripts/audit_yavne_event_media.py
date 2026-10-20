"""Refresh event-specific promotional photographs from exact official event pages."""
import concurrent.futures,hashlib,io,json,re
from pathlib import Path
from urllib.parse import urljoin,urlsplit
import requests
from bs4 import BeautifulSoup
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]/'events-preview/yavne'
HOSTS={'www.htyavne.co.il','htyavne.co.il','yavne-matnasim.smarticket.co.il'}
def norm(s):return re.sub(r'[^\w\u0590-\u05ff]','',s.lower())
def run():
 data=json.loads((ROOT/'data/events.json').read_text());events=data['events']
 home=BeautifulSoup(requests.get('https://www.htyavne.co.il/',timeout=25).text,'html.parser')
 links=[(a.get_text(' ',strip=True),urljoin('https://www.htyavne.co.il/',a.get('href',''))) for a in home.select('a[href]') if re.search(r'[?&]id=\d+',a.get('href',''))]
 def enrich(e):
  if e.get('image_verified') and e.get('image_publishable') and str(e.get('image_url','')).startswith('assets/'):return None
  urls=[u for u in [e.get('purchase_url'),e.get('detail_source_url'),e.get('ticket_url')] if u and urlsplit(u).hostname in HOSTS]
  title=norm(e['title'])
  urls += [u for t,u in links if len(title)>4 and (title in norm(t) or any(len(norm(x))>5 and norm(x) in norm(t) for x in re.split('[-–|]',e['title'])[:1]))]
  for u in dict.fromkeys(urls):
   try:
    r=requests.get(u,timeout=16);r.raise_for_status();soup=BeautifulSoup(r.text,'html.parser')
    h=soup.select_one('h1');h=norm(h.get_text(' ',strip=True)) if h else ''
    # Exact source occurrence, not a city index or related-event image.
    if not h or not (title in h or h in title ):continue
    poster=soup.select_one('img[alt*="תמונת מופע"]');image=urljoin(r.url,poster.get('src','')) if poster else ''
    if not image:
     meta=soup.select_one('meta[property="og:image"]');image=urljoin(r.url,meta.get('content','')) if meta else ''
    if not image or re.search(r'logo|no_pic|placeholder|artistShadow|eventNew',image,re.I):continue
    raw=requests.get(image,timeout=18).content;im=Image.open(io.BytesIO(raw));im.load()
    if min(im.size)<120:continue
    name=hashlib.sha256(image.encode()).hexdigest()[:20]+'.webp';path=ROOT/'assets/events'/name
    im.convert('RGB').save(path,'WEBP',quality=88)
    e.update(image_url='assets/events/'+name,image_origin_url=image,image_source=r.url,image_verified=True,image_publishable=True,image_represents_event=True,source_image_kind='official_event',image_rights_status='official_promotional_event',image_credit='תמונת האירוע: '+('היכל התרבות יבנה' if 'htyavne' in r.url else 'רשת המרכזים הקהילתיים יבנה'),thumbnail_ready=False)
    return {'event_id':e['event_id'],'title':e['title'],'source':r.url}
   except Exception:continue
  return None
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:updated=[x for x in pool.map(enrich,events) if x]
 (ROOT/'data/events.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'updated':updated,'remaining_without_verified_photo':sum(not e.get('image_publishable') for e in events)},ensure_ascii=False))
if __name__=='__main__':run()
