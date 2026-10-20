#!/usr/bin/env python3
"""Collect public Yavne culinary listings; city evidence and provenance are required."""
import json,re,hashlib,time,io
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin,urlsplit
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parents[1];CITY=ROOT/'events-preview/yavne';DATA=CITY/'data/restaurants.json'
HEAD={'User-Agent':'ISNET-Yavne-Food/1.0 (public business directory)','Accept-Language':'he-IL,he;q=0.9'}
SOURCES=['https://easy.co.il/list/Restaurants-and-Fast-Food?region=883','https://easy.co.il/list/Cafes?region=883','https://easy.co.il/list/Bakeries-and-Patisseries?region=883','https://www.rest.co.il/restaurants/yavne/','https://www.rest.co.il/restaurants/yavne/cafes/','https://www.rest.co.il/restaurants/yavne/ice-cream-parlors/','https://coffeetrail.co.il/coffeecart/cafe-batsheva/']
REPORT={'sources':[],'details':[],'rejected':[]};STAMP=datetime.now().date().isoformat()
def clean(s):return re.sub(r'\s+',' ',str(s or '')).strip()
def norm(s):return re.sub(r'[^a-z0-9א-ת]','',str(s).lower())
def get(url):
 r=requests.get(url,headers=HEAD,timeout=20);r.raise_for_status()
 if 'text/html' not in r.headers.get('Content-Type',''):raise ValueError('not_html')
 return BeautifulSoup(r.content,'html.parser'),r.url
def walk(v):
 if isinstance(v,list):
  for x in v:yield from walk(x)
 elif isinstance(v,dict):
  yield v
  for x in v.values():
   if isinstance(x,(dict,list)):yield from walk(x)
def schemas(soup):
 for tag in soup.select('script[type="application/ld+json"]'):
  try:yield from walk(json.loads(tag.string or tag.get_text()))
  except (ValueError,TypeError):pass
def locality(address):
 if isinstance(address,list):return any(locality(a) for a in address)
 if isinstance(address,dict):return clean(address.get('addressLocality')) in {'יבנה','Yavne','YAVNE'}
 return bool(re.search(r'(?:,|^)\s*יבנה(?:\s|$|\()',clean(address))) and 'גן יבנה' not in str(address)
def address_text(a):
 if isinstance(a,dict):return clean(a.get('streetAddress'))+', יבנה'
 return clean(a)
def classify(name,meta):
 t=norm(name+' '+meta)
 for k,terms in [('coffee_carts',['עגלתקפה','פודטראק']),('deli',['מעדניה','מעדנייה']),('wine',['חנותיין','חנותאלכוהול']),('pizza',['פיצה','פיצריה']),('dessert',['גליד','יוגורט','שוקולד','מתוקים','קינוח','עוגות']),('bakery',['מאפ','קונדיטור','בורקס']),('burger',['burger','בורגר']),('asian',['סושי','אסיי','אסיא','תאילנדי','דיםסאם']),('cafe',['קפה','cafe','coffee']),('fish',['דגים']),('local',['בית','מוכן','גחנון','תבשיל','קייטרינג']),('street',['פלאפל','שווארמה','חומוס','טוסט','טורטיה','נקניק','בפיתה']),('italian',['איטלקי','פסטה']),('meat',['בשר','גחלים','שיפוד']),('bar',['ברמסעדה','פאב','bar'])]:
  if any(norm(x) in t for x in terms):return k
 return 'restaurant'
LABEL={'coffee_carts':'עגלת קפה','pizza':'פיצריה','dessert':'גלידה ומתוקים','bakery':'מאפייה וקונדיטוריה','burger':'המבורגרים','asian':'מטבח אסייתי','cafe':'בית קפה','fish':'דגים','local':'אוכל ביתי ומוכן','street':'אוכל רחוב','italian':'מטבח איטלקי','meat':'בשרים וגריל','bar':'בר ואוכל','restaurant':'מסעדה','deli':'מעדנייה','wine':'יין ומשקאות'}
def make(name,address,url,meta='',image=None):
 name=clean(name).replace(' מנוהל','');address=clean(address)
 if not name or len(name)>100 or not locality(address):return None
 kind=classify(name,meta);uid='yavne-'+hashlib.sha256((norm(name)+'|'+norm(address)).encode()).hexdigest()[:14]
 return {'id':uid,'name':name,'en':'','kind':kind,'kinds':[kind],'label':LABEL[kind],'moods':['coffee'] if kind in {'cafe','coffee_carts','bakery','dessert'} else ['family','evening'],'address':address,'description':f'{name} — {LABEL[kind]} ביבנה. פרטי המקום, דרכי הקשר והניווט מרוכזים בכרטיס; התפריט ופרטי ההזמנה זמינים במקור המקושר.','image':'','credit':'','site':url,'source_url':url,'source_label':'מדריך העסקים','source_business_type':meta,'checked_at':STAMP,'city':'yavne','activity_status':'public_business_listing','kosher':'לא אומתה כשרות עדכנית','kosherVerified':False,'saturdayVerified':False,'saturday_note':'יש לבדוק שעות פעילות מול המקום','original_image_url':image}
def image_from(node,base):
 for img in node.select('img'):
  for attr in ['data-src','src','data-original']:
   u=urljoin(base,img.get(attr) or '')
   if u.startswith('https://') and not re.search(r'logo|placeholder|default|no.?image|loading|icon|avatar|transparent',u,re.I):return u
 return None
def listing(soup,url):
 found=[];links=[]
 for obj in schemas(soup):
  typ=str(obj.get('@type',''))
  if any(x in typ for x in ['Restaurant','CafeOrCoffeeShop','FoodEstablishment','Bakery','IceCreamShop','LocalBusiness']) and locality(obj.get('address')):
   image=obj.get('image');image=image[0] if isinstance(image,list) and image else image;image=image.get('url') if isinstance(image,dict) else image
   item=make(obj.get('name'),address_text(obj['address']),urljoin(url,obj.get('url') or url),str(obj.get('servesCuisine') or typ),image)
   if item:found.append(item)
 for a in soup.select('a[href]'):
  href=urljoin(url,a['href']);text=clean(a.get_text(' ',strip=True));host=urlsplit(href).hostname or ''
  if ('/page/' in href and host=='easy.co.il') or re.search(r'rest.co.il/rest/\d+',href) or (host.endswith('.rest.co.il') and host!='www.rest.co.il'):
   if not text:continue
   node=a
   for _ in range(7):
    if node.parent is None:break
    ctx=clean(node.get_text(' ',strip=True))
    if 'יבנה' in ctx and len(ctx)<2200:break
    node=node.parent
   ctx=clean(node.get_text(' ',strip=True))
   if len(ctx)>2200 or 'יבנה' not in ctx or 'גן יבנה' in ctx:continue
   links.append(href)
   title=a.find(['h2','h3','h4']) or a
   name=clean(title.get_text(' ',strip=True))
   name=re.sub(r'^ציון העסק\s*[\d.]+\s*','',name)
   if len(name)>90:continue
   m=re.search(r'([א-תA-Za-z0-9\'׳"״ .()\-/]{2,90},\s*יבנה)(?:\s*[|·(]|$|\s)',ctx)
   if m:
    address=m[1]
    # Remove the card title/type from a captured address by using text nodes.
    lines=list(node.stripped_strings)
    addr=next((clean(x).split('|')[0].strip() for x in lines if ', יבנה' in x and len(x)<140),address)
    item=make(name,addr,href,ctx[:250],image_from(node,url))
    if item:found.append(item)
 return found,list(dict.fromkeys(links))
def detail(url):
 try:
  soup,final=get(url);rows,_=listing(soup,final)
  h=soup.find('h1');name=clean(h.get_text(' ',strip=True)) if h else ''
  # Easy/Rest address lines describe the business; ignore nearby suggestions.
  lines=[clean(x) for x in soup.stripped_strings];address=next((x for x in lines[:130] if ', יבנה' in x and len(x)<130),'')
  if any(x in ' '.join(lines[:80]) for x in ['נסגר לצמיתות','העסק נסגר לצמיתות']):
   REPORT['rejected'].append({'url':url,'reason':'permanently_closed'});return None
  if not address and not rows:return None
  item=rows[0] if rows else make(name,address,final,' '.join(lines[:45]))
  if not item:return None
  item['phone']=next((re.sub(r'\D','',a['href']) for a in soup.select('a[href^="tel:"]')),None)
  image=soup.find('meta',property='og:image');item['original_image_url']=image.get('content') if image else image_from(soup,final)
  item['source_label']='איזי' if 'easy.co.il' in final else 'Rest' if 'rest.co.il' in final else 'אתר המקום'
  # Only use an explicitly linked business website; do not fabricate a URL.
  for a in soup.select('a[href]'):
   if clean(a.get_text(' ',strip=True)) in {'אתר הבית','לאתר המסעדה','לאתר הבית','אתר האינטרנט'}:
    link=urljoin(final,a['href'])
    if link.startswith('https://') and (urlsplit(link).hostname or '') not in {'easy.co.il','www.rest.co.il'}:item['site']=link
  item['activity_evidence']='עמוד עסק נגיש עם כתובת ביבנה'
  return item
 except Exception as exc:
  REPORT['details'].append({'url':url,'error':str(exc)[:130]});return None
def cache_image(item):
 url=item.get('original_image_url') or ''
 if not url.startswith('https://') or re.search(r'logo|placeholder|default|no.?image|icon|avatar|/shared/og',url,re.I):return
 try:
  r=requests.get(url,headers={'User-Agent':HEAD['User-Agent'],'Referer':item['source_url']},timeout=18);r.raise_for_status()
  if len(r.content)>12_000_000:raise ValueError('too_large')
  img=Image.open(io.BytesIO(r.content));img=ImageOps.exif_transpose(img).convert('RGB')
  if min(img.size)<180:raise ValueError('too_small')
  img.thumbnail((1200,900));out=CITY/'assets/restaurants';out.mkdir(exist_ok=True,parents=True)
  img.save(out/(item['id']+'.webp'),'WEBP',quality=86)
  item['image']='assets/restaurants/'+item['id']+'.webp';item['credit']='תמונת המקום במקור המקושר';item['image_source_url']=item['source_url']
 except Exception as exc:REPORT.setdefault('image_errors',[]).append({'id':item['id'],'error':str(exc)[:100]})
def main():
 items=json.loads(DATA.read_text())['restaurants'] if DATA.exists() else []
 for seed in json.loads((CITY/'data/food-source-seeds.json').read_text()):
  item=make(seed['name'],seed['address'],seed['url'],seed['type'])
  if item:
   item['source_label']='איזי';item['activity_evidence']='כרטיס עסק מאומת עם כתובת מקומית';items.append(item)
 urls=list(SOURCES);visited=set();detail_urls=[p['source_url'] for p in items]
 while urls and len(visited)<40:
  url=urls.pop(0)
  if url in visited:continue
  visited.add(url)
  try:
   soup,final=get(url);rows,links=listing(soup,final);items.extend(rows);detail_urls.extend(links)
   REPORT['sources'].append({'url':url,'status':'ok','listings':len(rows),'detail_links':len(links)})
   for a in soup.select('a[href]'):
    link=urljoin(final,a['href']);label=clean(a.get_text(' ',strip=True))
    if '/restaurants/yavne/' in link and (label.isdigit() or label in {'הבא','לעמוד הבא'}) and link not in visited:urls.append(link)
   print('SOURCE',url,len(rows),len(links),flush=True)
  except Exception as exc:REPORT['sources'].append({'url':url,'status':'failed','error':str(exc)[:150]})
  time.sleep(.2)
 unique_urls=list(dict.fromkeys(detail_urls))[:240]
 with ThreadPoolExecutor(max_workers=4) as pool:
  for item in pool.map(detail,unique_urls):
   if item:items.append(item)
 merged={}
 for item in items:
  if item['source_url'] in {r.get('url') for r in REPORT['rejected'] if r.get('reason')=='permanently_closed'}:continue
  if not locality(item.get('address','')):REPORT['rejected'].append(item);continue
  # A branch is a separate record; merge spelling aliases only at same address.
  key=norm(item['name'])+'|'+norm(item['address'])
  old=merged.get(key)
  if not old:merged[key]=item
  elif item.get('phone') or item.get('activity_evidence'):
   for k,v in item.items():
    if v and (k not in {'description','image','id'} or not old.get(k)):old[k]=v
 rows=[]
 for seed in json.loads((CITY/'data/food-source-seeds.json').read_text()):
  item=make(seed['name'],seed['address'],seed['url'],seed['type'])
  if not item:continue
  matches=[p for p in merged.values() if p.get('source_url','').rstrip('/')==seed['url'].rstrip('/')]
  matches.sort(key=lambda p:sum(bool(p.get(k)) for k in ['image','phone','original_image_url']),reverse=True)
  if matches:
   for k in ['image','credit','phone','site','original_image_url','image_source_url']:
    if matches[0].get(k):item[k]=matches[0][k]
  item['source_label']='איזי' if 'easy.co.il' in seed['url'] else 'Rest'
  if '/shared/og' in item.get('original_image_url','') or '/shared/og' in item.get('image',''):item['image']='';item['original_image_url']=''
  if seed.get('image_url'):
   item['image']='';item['original_image_url']=seed['image_url'];item['image_source_url']=seed.get('image_source_url',seed['url'])
  if seed['url'] in {r.get('url') for r in REPORT['rejected'] if r.get('reason')=='permanently_closed'}:continue
  rows.append(item)
 if len(rows)<15:raise SystemExit('Insufficient verified city coverage; preserving existing public data')
 with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(cache_image,[p for p in rows if not p.get('image')]))
 rows.sort(key=lambda x:(x['kind'],x['name']))
 payload={'city':'yavne','checked_at':STAMP,'restaurants':rows,'total':len(rows),'coverage':'Public business listings located inside Yavne; absence is not proof that a business does not exist.'}
 DATA.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
 REPORT.update(total=len(rows),with_images=sum(bool(x.get('image')) for x in rows),generated_at=STAMP)
 (ROOT/'events-preview/admin/data/yavne-food-source-report.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2)+'\n')
 print('FOOD_RESULT',json.dumps({k:REPORT[k] for k in ['total','with_images']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
