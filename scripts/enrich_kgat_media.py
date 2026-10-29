"""Match exact official event pages, reject logos, cache posters and derive screenings."""
import concurrent.futures,hashlib,io,json,re
from datetime import date
from pathlib import Path
from urllib.parse import urljoin,urlsplit
import requests
from bs4 import BeautifulSoup
from PIL import Image
from sync_kgat_events import classify
R=Path(__file__).resolve().parents[1]/'events-preview/kiryat-gat'
def norm(t):return re.sub(r'[^\w\u0590-\u05ff]','',str(t).lower()).replace('קריית','קרית')
def run():
 data=json.loads((R/'data/events.json').read_text());events=data['events']
 def enrich(e):
  if e.get('image_publishable') and e.get('image_verified') and str(e.get('image_url','')).startswith('assets/'):return
  urls=[e.get('ticket_url'),e.get('detail_source_url'),*(s.get('url') for s in e.get('sources',[]))]
  urls=[u for u in dict.fromkeys(urls) if u and urlsplit(u).hostname=='matnaskg.smarticket.co.il' and urlsplit(u).path!='/']
  for u in urls[:2]:
   try:
    r=requests.get(u,timeout=18);r.raise_for_status();s=BeautifulSoup(r.content,'html.parser');h=s.select_one('h1');h=h.get_text(' ',strip=True) if h else ''
    if not h or not(norm(h) in norm(e['title']) or norm(e['title']) in norm(h)):continue
    e['official_detail_url']=r.url;e['purchase_url']=r.url
    img=s.select_one('img[alt*="תמונת מופע"]')
    meta=s.select_one('meta[property="og:image"]')
    image=urljoin(r.url,img.get('src','')) if img else urljoin(r.url,meta.get('content','')) if meta else ''
    if not image or re.search(r'logo|no_pic|placeholder|artistShadow|eventNew',image,re.I):continue
    response=requests.get(image,timeout=18);response.raise_for_status();im=Image.open(io.BytesIO(response.content));im.load()
    if min(im.size)<120 or im.width>im.height*5:continue
    out=R/'assets/events';out.mkdir(parents=True,exist_ok=True);name=hashlib.sha256(image.encode()).hexdigest()[:20]+'.jpg';im.convert('RGB').save(out/name,'JPEG',quality=88)
    thumb=R/'assets/event-thumbs';thumb.mkdir(exist_ok=True);im.thumbnail((640,640));im.convert('RGB').save(thumb/name,'JPEG',quality=84)
    e.update(image_url='assets/events/'+name,image_origin_url=image,image_source=r.url,image_verified=True,image_publishable=True,image_represents_event=True,source_image_kind='official_event',image_rights_status='official_promotional_event',image_credit='תמונת האירוע: החברה העירונית קריית גת',thumbnail_url='assets/event-thumbs/'+name,thumbnail_ready=True)
    return
   except (requests.RequestException,ValueError,OSError):continue
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:list(ex.map(enrich,events))
 # Exact dates/times and normalized venue; official records win source disagreement.
 out=[];held=[]
 def identity(e):
  t=e['title']
  return next((key for key in ['יובל המבולבל','טרזן וג','חנות סופגניות'] if key in t),norm(t))
 for e in sorted(events,key=lambda e:not any(s.get('source_type')=='official' for s in e.get('sources',[]))):
  def venue(x):return norm(x.get('venue','')).replace('קריתגת','').replace('רחבת','')
  if not any(s.get('source_type')=='official' for s in e.get('sources',[])):
   official=next((x for x in out if any(s.get('source_type')=='official' for s in x.get('sources',[])) and identity(x)==identity(e) and x['start_date']==e['start_date'] and venue(x)==venue(e)),None)
   if official and official['start_time']!=e['start_time']:
    held.append({'event_id':e['event_id'],'title':e['title'],'reason':'secondary_time_conflicts_with_official','official_time':official['start_time'],'secondary_time':e['start_time']});continue
  same=next((x for x in out if x['start_date']==e['start_date'] and x['start_time']==e['start_time'] and venue(x)==venue(e) and (identity(x)==identity(e) or norm(x['title'])==norm(e['title']) or min(len(norm(x['title'])),len(norm(e['title'])))>7 and (norm(x['title']) in norm(e['title']) or norm(e['title']) in norm(x['title'])))),None)
  if same:
   same.setdefault('source_aliases',[]).append({'event_id':e['event_id'],'title':e['title'],'url':e.get('ticket_url')})
   for source in e.get('sources',[]):
    if source not in same.setdefault('sources',[]):same['sources'].append(source)
   if e.get('image_publishable') and not same.get('image_publishable'):
    for k,v in e.items():
     if k.startswith(('image_','thumbnail_')) or k=='source_image_kind':same[k]=v
  else:out.append(e)
 (R.parent/'admin/data/kgat-conflicts-review.json').write_text(json.dumps({'held':held},ensure_ascii=False,indent=2)+'\n')
 for e in out:
  if e['title']=='פינק ליידי':e['category']='theatre';e['subcategory']='theatre';e['category_memberships']=[{'category':'theatre','subcategory':'theatre'}]
 data['events']=sorted(out,key=lambda e:(e['start_date'],e['start_time'],e['title']));data['stats']={'events':len(out)}
 (R/'data/events.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 films={}
 for e in out:
  if e['category']!='cinema':continue
  key=norm(e['title']);m=films.setdefault(key,{'id':'kgat-film-'+hashlib.sha256(key.encode()).hexdigest()[:12],'title':e['title'],'synopsis':e.get('description',''),'poster_url':e.get('image_url') if e.get('image_publishable') else None,'is_family':'kids' in e.get('audiences',[]),'venues':[{'id':'municipal-hall','name':'היכל התרבות קריית גת','article_url':e.get('purchase_url'),'schedule':{},'sessions':[]}]})
  v=m['venues'][0];v['schedule'].setdefault(e['start_date'],[]).append(e['start_time']);v['sessions'].append({'date':e['start_date'],'time':e['start_time'],'booking_url':e.get('purchase_url')})
 (R/'data/cinema.json').write_text(json.dumps({'city':'קריית גת','source_name':'החברה העירונית קריית גת — הקרנות בהיכל התרבות','updated_at':date.today().isoformat(),'movies':list(films.values())},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'events':len(out),'verified_original_images':sum(bool(e.get('image_publishable')) for e in out),'films':len(films)},ensure_ascii=False))
if __name__=='__main__':run()
