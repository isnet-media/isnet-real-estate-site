#!/usr/bin/env python3
"""Holon-only public calendars; exact source dates, retained provenance and local JPGs."""
import concurrent.futures, hashlib, io, json, re
from datetime import datetime,date
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup
from PIL import Image
import sync_events_from_sources as core
ROOT=Path(__file__).resolve().parents[1];CITY=ROOT/'events-preview/holon';DATA=CITY/'data';NOW=datetime.now(ZoneInfo('Asia/Jerusalem'));TODAY=NOW.date();HEAD={'User-Agent':'ISNET-Holon-Guide/1.0 public calendar reader','Accept-Language':'he-IL,he;q=0.9'}
def read(n):return json.loads((DATA/(n+'.json')).read_text())
def save(n,d):(DATA/(n+'.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def get(url):
 r=requests.get(url,headers=HEAD,timeout=25);r.raise_for_status();r.encoding='utf-8';return BeautifulSoup(r.text,'html.parser')
def clean(s):return re.sub(r'\s+',' ',s or '').strip()
def classify(title,text,sid):
 s=title+' '+text[:450]
 if sid=='cinematheque' or re.search(r'בדיבוב|הקרנת|בימוי:|[Cc]inema',s):return 'cinema'
 if re.search(r'סטנד.?אפ|דניאל סטיופין|רועי לוי|אלי פיניש|אורי חזקיה|אסף יצחקי|גיורא זינגר|דניאל חן|הדר לוי|חן מזרחי|יובל סמו|יונתן ברק|לירון אופיר',s):return 'standup'
 if re.search(r'לגיל|גילי|ילדים|שעת סיפור|קטנטנים|כראמל|האריה שבפנים|נילס|קרקס|חוג איור|סדנ|אוצר החברות|בשביל עם חברים|ג.ק ואפון|דני דני|הממלכה הקטנטנה|המסע של|זהבה ושלושת|טרזן|לולי שבלולי|מוכר הכובעים|מחסן השטוזים|מעשה בחמישה|מר צפרדע|סבתא בישלה|סיפור טעים|עמי ותמי|קסם של|רחוב חנוכה|שוליית האור|שוקו וניל|אליסה בארץ|אצבעוני|הילד שהדליק|המכבים|מלכת השלג|סיפור לקטנטנים',s) and not re.search(r'לגילאי 60|גיל השלישי',s):return 'kids'
 if re.search(r'הרצא|מאחורי הקלעים|שיחה עם|תרבות ודעת|מסע עולמי|אלצהיימר|נשואה לפשע|דרמה בסיפורי|מה זה להיות יהודי',s):return 'lecture'
 if sid=='design' or re.search(r'תערוכ|מוזיאון הקומיקס|המעגל|סיור מודרך',title):return 'exhibition'
 if re.search(r'קומדיה|תיאטרון|תאטרון|מחזה|בימוי|אור לגויים|זוגות בזיגזג|מאדם תיק תק|הזוג המוזר|אף מילה לאמא|דרושה עוזרת|המאסטר|מדיאה|זוגיות AI|עד הרבנות|צ.רלי וחצי|שקרים קטנים',s):return 'theatre'
 if re.search(r'קונצרט|תזמורת|זמר|מוזיק|מוסיק|שרים|דוידוב|צלילים|אתונה|אברהם טל|דוד ד.אור|דני רובס|בלבוש יווני|ערב פילהרמוני|קלאסיקל|ירושלים פינת|לילה ברומא|לילות ספרד|פארטי',s):return 'music'
 return 'community'
def subcat(cat,title,sid):
 return {'music':'concerts' if re.search(r'תזמורת|קונצרט|דוידוב',title) else 'singing' if re.search(r'שרים|זמר',title) else 'live','kids':'story' if re.search(r'שעת סיפור|סיפור לקטנטנים',title) else 'workshops' if re.search(r'סדנ|חוג',title) else 'shows','theatre':'dance' if 'מחול' in title else 'theatre','cinema':'meetings' if re.search(r'מפגש|שיחה',title) else 'screenings','lecture':'workshops' if re.search(r'סדנ',title) else 'lectures','exhibition':'design' if sid=='design' else 'comics' if 'קומיקס' in title else 'art'}.get(cat,{'standup':'standup','community':'community'}.get(cat,'culture'))
def fallback(cat):return next(c['image'] for c in read('categories')['categories'] if c['id']==cat)
def promo(url,source_url):
 if not url or not ('/uploads/' in url or '/images/' in url and 'hotcinema.co.il' in urlsplit(url).hostname) or any(w in url.lower() for w in ['no_pic','logo','no-image']):return None
 if urlsplit(url).hostname.removeprefix('www.')!=urlsplit(source_url).hostname.removeprefix('www.'):return None
 try:
  name=hashlib.sha256(url.encode()).hexdigest()[:20]+'.jpg';p=CITY/'assets/events'/name
  if not p.exists():
   r=requests.get(url,headers=HEAD,timeout=20);r.raise_for_status();im=Image.open(io.BytesIO(r.content));
   if min(im.size)<120:return None
   im=im.convert('RGB');im.thumbnail((1000,1000));im.save(p,'JPEG',quality=84,optimize=True)
  return 'assets/events/'+name
 except Exception:return None

def ingest(spec):
 report={'id':spec['id'],'name':spec['name'],'url':spec['url'],'checked_at':NOW.isoformat(),'events_found':0}
 try:
  soup=get(spec['url']);text=soup.get_text(' ',strip=True)
  if 'JavaScript' in text and (len(text)<2000 or 'מושבת' in text):
   report.update(status='interactive_source',note='המקור דורש JavaScript; מוצג קישור ישיר, ללא המצאת אירועים');return [],report
  parser=spec.get('parser')
  if parser=='hot-events':
   rows=[]
   for a in soup.select('a.event-thumb[href]'):
    heading=a.select_one('.event-thumb-name');title=clean(heading.get_text(' ',strip=True)) if heading else ''
    image=a.select_one('img[src]')
    for node in a.select('.event-thumb-date'):
     hit=re.fullmatch(r'(.*חולון)\s*-\s*(\d{2}/\d{2}/\d{2})\s+(\d{2}:\d{2})',clean(node.get_text(' ',strip=True)))
     if not hit:continue
     dt=datetime.strptime(hit[2],'%d/%m/%y');u=urljoin(spec['url'],a['href'])
     title=re.sub(r'\s*(?:ב?דרים סטייג|DREAM STAGE|\(פארק עסקים).*$', '',title,flags=re.I).strip()
     title=re.sub(r'\s*\d{1,2}\.\d{1,2}(?:\.\d{2,4})?\s*$', '',title).strip()
     rows.append(dict(title=title,start_date=dt.date().isoformat(),start_time=hit[3],venue='DREAM STAGE חולון',ticket_url=u,purchase_url=u,image_origin_url=urljoin(spec['url'],image['src']) if image else None))
  elif parser=='structured':rows=core.generic_jsonld_rows(soup,{'url':spec['url'],'venue':spec['venue']})
  elif parser=='smarticket':rows=core.smarticket_rows(soup,{'url':spec['url'],'venue':spec['venue']})
  elif parser=='mevalim':
   rows=[]
   for n in soup.select('[data-mvlm-event-date]'):
    v=n.select_one('.rgbcode_table_shortcode_table_venue');venue=v.get_text(' ',strip=True) if v else ''
    if 'חולון' not in venue:continue
    try:dt=datetime.strptime(n.get('data-mvlm-event-date'),'%d.%m.%y %H:%M')
    except (ValueError,TypeError):continue
    rows.append(dict(title=n.get('data-mvlm-event-name'),start_date=dt.date().isoformat(),start_time=dt.strftime('%H:%M'),venue=venue,ticket_url=n.get('data-mvlm-event-link-target'),purchase_url=n.get('data-mvlm-event-link-target')))
  else:rows=core.generic_jsonld_rows(soup,{'url':spec['url'],'venue':spec['venue']}) if parser=='municipal' else []
  rows=[r for r in rows if r.get('start_date','')>=TODAY.isoformat() and r.get('start_date','')<=core.add_months(TODAY,5).isoformat()]
  # Keep all calendar dates explicitly represented by the public listing. Do not turn +N into invented daily dates.
  report.update(status='collected' if rows else 'linked_directory',events_found=len(rows),note='' if rows else 'מקור זמין; פרטים וקבלת מועדים דרך האתר המקורי')
  if spec['id']=='children' and 'המוזיאון סגור לקהל' in text:report.update(status='closure_notice',note='מופיעה הודעת סגירה במקור; יש לבדוק מול המוזיאון')
  out=[]
  for row in rows:
   title=clean(row.get('title'));u=row.get('ticket_url')
   if not title or not u or not u.startswith('https://'):continue
   # Venue text lives immediately before the Hebrew day in listing anchors.
   anchor=next((a for a in soup.select('a[href]') if urljoin(spec['url'],a['href'])==u and 'פרטים נוספים' in a.get_text()),None)
   heading=anchor.select_one('.details .h2,.overlay .h3') if anchor else None
   if heading:title=clean(heading.get_text(' ',strip=True))
   info=anchor.get_text(' ',strip=True) if anchor else '';tail=info.split('פרטים נוספים',1)[-1];venue=tail[len(title):].split('ביום')[0].strip() if tail.startswith(title) else row.get('venue')
   v=anchor.select_one('.theater_name') if anchor else None
   if v:venue=clean(v.get_text(' ',strip=True))
   if spec.get('city_filter') and ('חולון' not in venue or parser!='structured' and not v):continue
   if not venue or venue=='חולון':venue=spec['venue']
   if spec['id']=='hth':venue='תיאטרון חולון · '+venue if 'תיאטרון חולון' not in venue else venue
   elif spec['id'] in ['mediatheque','cinematheque','design'] and 'מדיטק' not in venue and 'חולון' not in venue:venue=('סינמטק חולון' if spec['id']=='cinematheque' else 'מוזיאון העיצוב חולון' if spec['id']=='design' else 'מדיטק חולון')+' · '+venue
   cat=classify(title,info,spec['id']);sub=subcat(cat,title,spec['id'])
   out.append(dict(id='holon-'+hashlib.sha256((core.text_norm(title)+'|'+row['start_date']+'|'+row['start_time']+'|'+core.text_norm(venue)).encode()).hexdigest()[:16],title=title,city='חולון',start_date=row['start_date'],start_time=row['start_time'],venue=venue,category=cat,subcategory=sub,source_url=u,booking_url=row.get('purchase_url') or u,source_id=spec['id'],source_name=spec['name'],image=fallback(cat),image_origin_url=row.get('image_origin_url'),image_credit='תמונת המחשה — לא צילום מהאירוע',description='',ticket_status=row.get('ticket_status','unknown'),price=None,source_checked_at=NOW.isoformat()))
  report['events_found']=len(out)
  return out,report
 except Exception as ex:report.update(status='fetch_failed',note=str(ex)[:180]);return [],report

def enrich(e):
 try:
  soup=get(e['source_url']);main=soup.select_one('#mainContent') or soup.select_one('main') or soup
  # Price belongs to this exact dated occurrence, never to another performance.
  for node in soup.select('script[type="application/ld+json"]'):
   try:
    obj=json.loads(node.string or node.get_text())
    if isinstance(obj,dict) and obj.get('@type')=='Event' and str(obj.get('startDate',''))[:16]==e['start_date']+'T'+e['start_time']:
     offer=obj.get('offers') or {}
     if isinstance(offer,dict) and offer.get('priceCurrency')=='ILS' and re.fullmatch(r'\d+(?:\.\d+)?',str(offer.get('price',''))):e['price']=float(offer['price'])
   except (ValueError,TypeError):pass
  # Retain concise descriptive copy from the event body, never navigation or the whole sales page.
  paras=[clean(p.get_text(' ',strip=True)) for p in main.select('p')]
  paras=[p for p in paras if 50<len(p)<1500 and not re.search(r'עוגיות|זכויות|נגישות|הזנת|סיסמה|התחברות|מדיניות|ניוזלטר|דואר אלקטרוני',p)]
  e['description']='\n\n'.join(dict.fromkeys(paras))[:1800]
  if e['source_id']!='cinematheque':
   updated=classify(e['title'],e['description'],e['source_id'])
   if updated!='community':e['category']=updated
   e['subcategory']=subcat(e['category'],e['title'],e['source_id'])
  meta=soup.select_one('meta[property="og:image"]');url=urljoin(e['source_url'],meta.get('content','')) if meta else e.get('image_origin_url')
  image=promo(url,e['source_url'])
  if not image and e.get('image_origin_url') and e['image_origin_url']!=url:
   url=e['image_origin_url'];image=promo(url,e['source_url'])
  if image:e.update(image=image,image_origin_url=url,image_credit='תמונת יח״צ: '+e['source_name'],image_role='official_promotional')
  else:e.update(image=fallback(e['category']),image_role='illustration')
  if re.search(r'גמלא|גיל השלישי|מינחת|על הבוקר|בין ערביים|60\+',e['title']+' '+e['description']):e['audiences']=['seniors']
  else:e['audiences']=[]
  age=re.search(r'(?:לגילאי|גילי|גילאי)\s*(\d{1,2})\s*[-–]\s*(\d{1,2})',e['description']+' '+e['title'])
  if age:e['age_text']='גילאי '+age[1]+'–'+age[2]
 except Exception:pass
 if not e['description']:e['description']='פרטי התוכנית וההשתתפות באתר המארגן.'
 return e

def collect_rest():
 """Directory records accepted only when their own detail confirms a Holon address."""
 base='https://www.rest.co.il';items=[]
 try:
  soup=get(base+'/restaurants/holon/');links={urljoin(base,a['href']) for a in soup.select('a[href]') if re.fullmatch(r'/rest/\d+/',a['href'])}
  links.update(read('culinary-seeds')['rest_detail_urls'])
  links.update(x['source_url'] for x in read('restaurants')['items'] if x['id'].startswith('rest-'))
 except Exception:return []
 def one(u):
  try:
   s=get(u);text=s.get_text(' ',strip=True);h=s.find('h1');title=clean(h.get_text()) if h else ''
   if not title or title=='גורדוס':return
   # Structured address proves locality; never infer it from the search result page.
   blocks=[]
   for script in s.select('script[type="application/ld+json"]'):
    try:v=json.loads(script.string or script.get_text());blocks.extend(v if isinstance(v,list) else [v])
    except ValueError:pass
   obj=next((x for x in blocks if isinstance(x,dict) and 'חולון' in json.dumps(x.get('address',{}),ensure_ascii=False)),None)
   if not obj:return
   address=obj.get('address',{});addr=clean(' '.join([address.get('streetAddress',''),address.get('addressLocality','')]))
   description=clean(BeautifulSoup(obj.get('description',''),'html.parser').get_text(' ',strip=True))[:400]
   typ=' '.join(obj.get('servesCuisine',[])) if isinstance(obj.get('servesCuisine'),list) else str(obj.get('servesCuisine',''))
   t=title+' '+typ+' '+description
   sub='dessert' if re.search(r'מאפ|פטיסרי|גליד|בורקס|קונדיט',t) else 'cafe' if re.search(r'קפה|בית קפה',t) else 'asian' if re.search(r'סושי|אסיית|סיני',t) else 'burger' if re.search(r'בשר|המבורגר|סטק|אגאדיר|burger',t,re.I) else 'italian' if re.search(r'איטלק|פסט|פיצ',t) else 'street'
   return dict(id='rest-'+u.strip('/').split('/')[-1],title=title,city='חולון',category='food',subcategory=sub,description=description or 'לפרטי התפריט והזמנה יש לפנות למקום.',source_url=u,booking_url=u,address=addr,image='../kiryat-gat/assets/food/'+sub+'-illustration.jpg',image_credit='תמונת המחשה — לא צילום מהמסעדה',source_checked_at=NOW.isoformat(),kosher=None,saturday=None)
  except Exception:return
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:items=[r for r in ex.map(one,sorted(links)) if r]
 return items

def main():
 specs=read('sources')['sources'];events=[];reports=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
  for rows,report in ex.map(ingest,specs):events.extend(rows);reports.append(report)
 # Prefer specialist cinema source for duplicates, matching exact title, date and time.
 events.sort(key=lambda e:0 if e['source_id']=='cinematheque' else 1 if e['source_id']=='design' else 3 if e['source_id']=='mevalim' else 2);unique={}
 for e in events:
  key=(core.text_norm(e['title']),e['start_date'],e['start_time']);unique.setdefault(key,e)
 events=list(unique.values())
 old_by_url={e['source_url']:e for e in read('events')['events']} if (DATA/'events.json').exists() else {}
 def reuse(e):
  old=old_by_url.get(e['source_url'])
  if not old or old.get('source_checked_at','')[:10]!=NOW.date().isoformat():return enrich(e)
  for field in ['description','image','image_credit','image_role','image_origin_url','audiences','age_text','price','image_source_url']:
   if field in old:e[field]=old[field]
  cat=classify(e['title'],e.get('description',''),e['source_id'])
  if cat!='community':e['category']=cat;e['subcategory']=subcat(cat,e['title'],e['source_id'])
  if e.get('image_role')!='official_promotional':e['image']=fallback(e['category'])
  return e
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:events=list(ex.map(reuse,events))
 # Secondary title suffixes do not create a second card for the same local performance.
 deduped=[]
 for e in events:
  t=core.text_norm(e['title']);match=next((x for x in deduped if x['start_date']==e['start_date'] and x['start_time']==e['start_time'] and (t.startswith(core.text_norm(x['title'])+' ') or core.text_norm(x['title']).startswith(t+' ')) and min(len(t),len(core.text_norm(x['title'])))>=5),None)
  if match:
   if len(e.get('description',''))>len(match.get('description','')):match['description']=e['description']
   match.setdefault('additional_sources',[]).append(e['source_url'])
  else:deduped.append(e)
 events=deduped
 old=read('events')['events'] if (DATA/'events.json').exists() else []
 failed={r['id'] for r in reports if r['status'] in ['fetch_failed','interactive_source']}
 keys={(core.text_norm(e['title']),e['start_date'],e['start_time']) for e in events}
 for e in old:
  k=(core.text_norm(e['title']),e['start_date'],e['start_time'])
  if e['source_id'] in failed and e['start_date']>=TODAY.isoformat() and k not in keys:events.append(e);keys.add(k)
 if len(events)<30:raise SystemExit('Too few verified dated Holon events; refusing replacement')
 events.sort(key=lambda e:(e['start_date'],e['start_time'],e['title']))
 save('events',{'city':'חולון','generated_at':NOW.isoformat(),'events':events})
 food=read('restaurants');fixed=[r for r in food['items'] if not r['id'].startswith('rest-')];auto=collect_rest();names={core.text_norm(r['title']) for r in fixed}
 old_auto={r['id']:r for r in food['items'] if r['id'].startswith('rest-')}
 old_auto.update({r['id']:r for r in auto})
 food['items']=fixed+[r for r in old_auto.values() if core.text_norm(r['title']) not in names];food['checked_at']=NOW.isoformat();save('restaurants',food)
 # Check each authored restaurant at its direct source; a failed fetch does not imply closure.
 def check(item):
  try:s=get(item['source_url']);return {'id':item['id'],'status':'checked' if len(s.get_text())>100 else 'needs_review','url':item['source_url'],'checked_at':NOW.isoformat()}
  except Exception:return {'id':item['id'],'status':'fetch_failed','url':item['source_url'],'checked_at':NOW.isoformat()}
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:food_reports=list(ex.map(check,food['items']))
 guides=read('guides')
 children=next((r for r in reports if r['id']=='children'),None)
 museum=next((g for g in guides['items'] if g['id']=='children'),None)
 if museum and children and children['status'] not in ['fetch_failed','interactive_source']:
  if children['status']=='closure_notice':museum.update(title='מוזיאון הילדים — בדקו מצב פתיחה',notice='מופיעה הודעת סגירה במקור — יש לוודא מול המוזיאון',availability='closure_notice')
  else:
   museum.update(title='מוזיאון הילדים הישראלי',description='מסלולי חוויה מודרכים לילדים ולמבוגרים; ביקור מחייב תיאום מראש ובדיקת הגיל המתאים.',availability='check_operator');museum.pop('notice',None)
 save('guides',guides)
 save('source-report',{'checked_at':NOW.isoformat(),'sources':reports,'food_sources':food_reports,'events':len(events),'restaurants':len(food['items']),'note':'Interactive and failed sources remain direct links. No dates or openings inferred. +N dates are not expanded without explicit source occurrences.'})
 print(json.dumps({'events':len(events),'restaurants':len(food['items']),'sources':reports},ensure_ascii=False))
if __name__=='__main__':main()
