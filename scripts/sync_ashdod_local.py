#!/usr/bin/env python3
"""Daily local Ashdod cards: fresh facts, recoverable legacy reset, no invented dates."""
import argparse, json, re, hashlib
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
from sync_ashdod_supplemental import make, ld, convert, equivalent, ticket_identity, Z
from sync_events_from_sources import smarticket_rows
from ofek_event_source import extract_ofek_events

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'events-preview/admin/data'
SOURCES={
 'ashdod_smarticket':dict(url='https://ashdod.smarticket.co.il/',parser='smarticket',venue='אשדוד'),
 'mishkan_smarticket':dict(url='https://mishkan-ashdod.smarticket.co.il/',parser='smarticket',venue='המשכן לאמנויות הבמה אשדוד'),
 'mishkan_primary':dict(url='https://www.mishkan-ashdod.co.il/events.asp',parser='mishkan_primary',venue='המשכן לאמנויות הבמה אשדוד'),
 'ofek_ashdod':dict(url='https://www.ofek-ashdod.org.il/page.php?type=events',parser='ofek',venue='קתדרת אופק, אשדוד',listing_pages=[dict(url='https://www.ofek-ashdod.org.il/page.php?gr='+str(gr)+'&m=296&type=events',category=cat) for gr,cat in [(644,'tour'),(643,'lecture'),(648,'lecture'),(1140,'workshop')]]),
 'up60':dict(url='https://www.coing.co/Ashdod_up60',parser='coing',venue='אפ 60+, סטרומה 5, אשדוד'),
 'ironit':dict(url='https://www.ironit.org.il/',parser='ironit',venue='אשדוד'),
 'tarbutashdod':dict(url='https://www.tarbutashdod.com/',parser='municipal_posts',venue='אשדוד',public_api='https://www.tarbutashdod.com/wp-json/wp/v2/posts?per_page=50'),
}
def get(url,**kw):
 r=requests.get(url,timeout=30,headers={'User-Agent':'ISNET local public event reader/1.0',**kw.pop('headers',{})},**kw);r.raise_for_status();return r
def page(url):return BeautifulSoup(get(url).text,'html.parser')
def fetch_once(spec):
 try:return page(spec['url']),None
 except requests.RequestException as ex:return None,str(ex)[:200]
def text(node):return node.get_text('\n',strip=True) if node else ''
def future(e):
 return bool(e.get('start_date') and e.get('start_time') and e.get('venue') and e['start_date']>=datetime.now(Z).date().isoformat())
def classify_local(e):
 if e.get('local_source_name') in ['ofek_ashdod','up60']:return
 title=e.get('title','');body=e.get('source_description') or e.get('description','')
 if re.search(r'\b(?:ל|ה)?ילדים\b|לכל המשפחה|שעת סיפור|פעוט',title):e.update(category='kids',subcategory='creative-workshops' if 'סדנ' in title else 'kids-activities')
 elif re.search(r'סדנ|קורס|חוג',title):e.update(category='workshop',subcategory='creative')
 elif re.search(r'פילאטיס|יוגה|התעמלות',title):e.update(category='sport',subcategory='activities')
 elif re.search(r'הרצא|פאנל|כנס|מפגש שיח',title):e.update(category='lecture',subcategory='lecture')
 elif 'מועדון קריאה' in title:e.update(category='community',subcategory='reading-clubs')
 elif e.get('category')=='music' and not re.search(r'מוזיק|מוסיק|קונצרט|תזמורת|\b(?:ה|ל)?שירים\b|\b(?:ה|ל)?להקה\b|\b(?:ה|ל)?זמר\b|מחול|בלט|הופעה חיה|מופע מוזיקלי',title+' '+body):
  e.update(category='community',subcategory='community-meeting',taxonomy_review_required=True)
  e.setdefault('internal_notes',[]).append('אין ראיה שמדובר בהופעה מוזיקלית; נדרש שיוך תוכני מדויק.')
 if e['category']=='community' and re.search(r'לנשים|נשים|גדולות מהחיים',title):e['subcategory']='women-events';e['audiences']=['women']
def localize(e,name):
 e['source']='local_'+name;e['local_source_name']=name;e['local_source_refresh']=True
 e['event_id']='local_'+hashlib.sha256((name+'|'+str(ticket_identity(e))+'|'+e['start_date']+'|'+e['start_time']).encode()).hexdigest()[:22]
 e['source_content_authoritative']=True;e['content_locked']=True;e['source_priority']=1
 e['source_fact_status']='date_time_venue_confirmed' if e.get('start_time') else 'date_venue_confirmed_hour_missing'
 e['source_description']=e.get('description','')
 if not e.get('description'):
  e['description']=e['series_description']=f"{e['title']} — {e['venue']}. מועד האירוע: {e['start_date']}."+(f" שעה: {e['start_time']}." if e.get('start_time') else ' השעה המדויקת טרם פורסמה.')
  e['content_completion_status']='facts_only';e['internal_notes'].append('תיאור המקור חסר; פורסמו עובדות מאומתות בלבד, ללא המצאת תוכנית.')
 else:e['content_completion_status']='source_description'
 e['source_image_kind']='source_card_image' if e.get('image_url') else 'not_available'
 if name in ['ofek_ashdod','up60']:
  activity=e.get('activity_type') or e['category'];e['category']='seniors';e['subcategory']={'lecture':'senior-lectures','tour':'senior-trips','workshop':'senior-workshops','music':'senior-music','sport':'senior-sport'}.get(activity,'senior-social');e['audiences']=['seniors']
 elif re.search(r'\b(?:ל|ה)?ילדים\b|לכל המשפחה|שעת סיפור|פעוט',e['title']):
  e['category']='kids';e['subcategory']='creative-workshops' if 'סדנ' in e['title'] else 'kids-activities'
 classify_local(e)
 return e
def card(row,name):
 u=row['ticket_url'];p=page(u);structured=ld(p)
 matches=[o for o in structured if str(o.get('startDate',''))[:10]==row['start_date']]
 if structured and not matches:raise ValueError('listing/detail date mismatch')
 if matches:
  e=convert(matches[0],name)
  if not e:raise ValueError('detail city mismatch')
  duration=re.fullmatch(r'PT(?:(\d+)H)?(?:(\d+)M)?',str(matches[0].get('duration','')))
  if duration:e['duration_minutes']=int(duration[1] or 0)*60+int(duration[2] or 0)
  location=matches[0].get('location') or {}
  if isinstance(location,dict) and location.get('streetAddress'):e['venue_address']=location['streetAddress']
  if str(e.get('price_min_ils')) in ['0','0.00']:e['is_free']=True
 else:e=make(name,row['title'],row['start_date'],row['start_time'],row['venue'],u)
 e['content_source_url']=u
 body=p.select_one('.txt_container, [itemprop=description], .event-description')
 if body:e['description']=e['series_description']=text(body).removeprefix('פרטים נוספים').strip()
 elif name=='ofek_ashdod':
  body=p.select_one('.entry-content, .content-text, .page-content, #event-description')
  if body:e['description']=e['series_description']=text(body)
 if name=='ofek_ashdod':
  # Ofek's structured startDate uses midnight as a date placeholder. Its
  # explicitly labelled civil-date/hour fields are the verified schedule.
  e['start_date']=row['start_date'];e['start_time']=row['start_time']
  if e['start_time']=='00:00':e['start_time']='';e['internal_notes'].append('במקור מופיעה שעת חצות כללית; שעה מדויקת טרם אומתה.')
  place=p.select_one('.eic-place .eic-value')
  if place and text(place) not in ['חיצוני','']:
   e['venue']=text(place)
  elif row.get('activity_type')=='tour':
   e['venue']='סיור מטעם אופק — נקודת המפגש לא פורסמה';e['internal_notes'].append('המקור מציין מיקום חיצוני בלבד; נדרשת השלמת נקודת המפגש.')
 if not e.get('image_url'):
  im=p.select_one('meta[property="og:image"]')
  if im:e['image_url']=e['image_origin_url']=urljoin(u,im.get('content',''))
 e['ticket_status']=row.get('ticket_status','unknown')
 for k in ['price_min_ils','price_max_ils','purchase_phone','activity_type']:
  if row.get(k) is not None:e[k]=row[k]
 return localize(e,name)
def smart(name,spec,p):
 rows=smarticket_rows(p,spec);seen=set();rows=[r for r in rows if future(r)]
 out=[];issues=[]
 def read(r):
  try:return card(r,name),None
  except Exception as ex:return None,dict(url=r['ticket_url'],title=r['title'],error=str(ex)[:250])
 with ThreadPoolExecutor(max_workers=4) as pool:
  for e,err in pool.map(read,rows):
   if err:issues.append(err)
   elif e['event_id'] not in seen and future(e):out.append(e);seen.add(e['event_id'])
 return out,issues,[]
def coing(name,spec,p):
 match=re.search(r'var cid\s*=\s*(\d+)',str(p));cid=int(match[1]) if match else None
 if not cid:raise ValueError('public community id missing')
 out=[];issues=[];undated=[];seen=set()
 for pn in range(1,101):
  j=get(urljoin(spec['url'],'/site/communities/groups'),params=dict(cid=cid,type='regular',view='auto',gid=0,page=pn),headers={'X-Requested-With':'XMLHttpRequest'}).json()
  if not j.get('success'):raise ValueError('public listing unsuccessful')
  if not j.get('items'):break
  fresh=0
  for html in j['items']:
   q=BeautifulSoup(html,'html.parser');a=q.select_one('a.community-resource-link[href]')
   if not a or a['href'] in seen:continue
   seen.add(a['href']);fresh+=1;u=a['href'];d=page(u);h=d.select_one('h1');title=text(h)
   rows=ld(d)
   if rows:
    for o in rows:
     e=convert(o,name)
     if e and future(e):out.append(localize(e,name))
   else:undated.append(dict(title=title,url=u,reason='אין מועד עתידי ושעה מאומתים בכרטיס; שירות קבוע או הרשמת התעניינות'))
  if not fresh:break
 return out,issues,undated
def primary_cards(name,u,p,post=None):
 h=p.select_one('#PageContent h1');title=text(h) or (post or {}).get('title',{}).get('rendered','')
 if not title:return []
 body=p.select_one('#PageContent');description=text(body).split('מועדים',1)[0].removeprefix(title).strip()
 key=re.sub(r'\s+',' ',title).strip().casefold()
 im=next((i for i in p.select('img[src]') if '/FilesSrc/Galleries/' in i['src'] and key==re.sub(r'\s+',' ',i.get('alt','')).strip().casefold()),None)
 photo=urljoin(u,im['src']) if im else (post or {}).get('featured_image_url')
 out=[]
 for tr in p.select('tr'):
  cells=tr.find_all('td',recursive=False)
  if len(cells)<3 or not re.fullmatch(r'\d{1,2}\.\d{1,2}\.\d{4}',text(cells[0])) or not re.fullmatch(r'\d{2}:\d{2}',text(cells[2])):continue
  d=datetime.strptime(text(cells[0]),'%d.%m.%Y').date().isoformat();clock=text(cells[2]);venue=(post or {}).get('location') or SOURCES['mishkan_primary']['venue']
  e=make(name,title,d,clock,venue,u,(post or {}).get('content',{}).get('rendered') or description,photo)
  a=tr.select_one('a[href]');buy=urljoin(u,a['href']) if a else u;e['purchase_url']=e['ticket_url']=buy
  e['verified_schedule_source_url']=u;e['source_image_kind']='source_card_image' if photo else 'not_available'
  if post:e['crosscheck_sources']=[post['link']]
  if future(e):out.append(localize(e,name))
 return out
def primary(name,spec,p):
 links={urljoin(spec['url'],a['href']) for a in p.select('a[href]') if 'event.asp?' in a['href']};out=[];issues=[]
 def read(u):
  try:return primary_cards(name,u,page(u)),None
  except Exception as ex:return [],dict(url=u,error=str(ex)[:250])
 with ThreadPoolExecutor(max_workers=4) as pool:
  for rows,error in pool.map(read,sorted(links)):
   out.extend(rows)
   if error:issues.append(error)
 return out,issues,[]
def municipal(name,spec,p):
 out=[];issues=[];undated=[];pn=1
 while True:
  r=get(spec['public_api'],params={'page':pn});posts=r.json()
  for post in posts:
   if post.get('status')!='publish':continue
   buy=post.get('ticket_link') or '';rows=[]
   if buy:
    try:
     detail=page(buy)
     if urlparse(buy).hostname=='www.mishkan-ashdod.co.il':rows=primary_cards(name,buy,detail,post)
     else:
      for o in ld(detail):
       e=convert(o,name)
       if e and future(e):e['crosscheck_sources']=[post['link']];rows.append(localize(e,name))
    except Exception as ex:issues.append(dict(url=buy,error=str(ex)[:250]))
   out.extend(rows)
   if not rows:undated.append(dict(title=BeautifulSoup(post.get('title',{}).get('rendered',''),'html.parser').get_text(),url=post['link'],reason='לא אומתו תאריך עתידי מלא ושעה; אין להסיק שנה מתאריך מקוצר או להפוך מועד הגשת מועמדות לאירוע'))
  if pn>=int(r.headers.get('X-WP-TotalPages','1')):break
  pn+=1
 return out,issues,undated
def ironit(name,spec,p):
 origins=[(spec['url'],p)];issues=[];out=[];undated=[]
 for a in p.select('a[href]'):
  if 'לוח אירועים' not in a.get_text():continue
  u=urljoin(spec['url'],a['href'])
  if any(u==b for b,_ in origins):continue
  try:origins.append((u,page(u)))
  except Exception as ex:issues.append(dict(url=u,error=str(ex)[:250]))
 links={urljoin(origin,a['href']) for origin,q in origins for a in q.select('a[href]') if '/events/' in a['href'] or '/event/' in a['href']}
 if not links:issues.append(dict(url=spec['url'],error='calendar_cards_not_supported_or_not_exposed; cannot claim full source coverage'))
 for u in sorted(links):
  try:
   q=page(u);buy=next((urljoin(u,a['href']) for a in q.select('a[href]') if 'smarticket.co.il' in a['href'] and '/event/' in a['href']),None)
   # Calendar export is an explicit source record, not a date inferred from prose.
   cal=next((a['href'] for a in q.select('a[href]') if 'outlook.live.com/calendar/' in a['href']),None)
   if cal:
    params=parse_qs(urlparse(cal).query);start=params.get('startdt',[''])[0]
    if start:
     dt=datetime.fromisoformat(start);dt=dt.astimezone(Z) if dt.tzinfo else dt.replace(tzinfo=Z)
     e=make(name,text(q.select_one('h1')),dt.date().isoformat(),dt.strftime('%H:%M'),params.get('location',[''])[0],u,params.get('body',[''])[0])
     meta=q.select_one('meta[property="og:image"]')
     if meta:e['image_url']=e['image_origin_url']=urljoin(u,meta.get('content',''))
     e['ticket_url']=e['purchase_url']=buy or u
     if future(e):out.append(localize(e,name))
     continue
   if buy:
    bp=page(buy)
    for o in ld(bp):
     e=convert(o,name)
     if not e or not future(e):continue
     body=bp.select_one('.txt_container');e['description']=e['series_description']=text(body) or e['description'];e['content_source_url']=buy;e['crosscheck_sources']=[u];out.append(localize(e,name))
    continue
   rows=ld(q)
   if rows:
    for o in rows:
     e=convert(o,name)
     if e and future(e):out.append(localize(e,name))
   else:undated.append(dict(url=u,reason='אין מועד ושעה מובנים מאומתים; נדרש קורא ייעודי'))
  except Exception as ex:issues.append(dict(url=u,error=str(ex)[:250]))
 return out,issues,undated
def image_policy(events):
 # Repeated site art across unrelated productions is not an event photograph.
 titles={}
 for e in events:
  if e.get('rejected_source_image_url'):
   e['image_url']=e['rejected_source_image_url'];e['source_image_kind']='source_card_image'
 for e in events:titles.setdefault(e.get('image_url'),set()).add(e['title'])
 def check(u):
  if not u:return u,False
  if u.startswith('/events-preview/'):return u,(ROOT/u.lstrip('/')).is_file()
  try:
   r=requests.get(u,stream=True,timeout=20,headers={'User-Agent':'ISNET local event image verification/1.0'})
   header=next(r.iter_content(32),b'')
   magic=header.startswith((b'\xff\xd8\xff',b'\x89PNG\r\n\x1a\n',b'GIF87a',b'GIF89a')) or (header.startswith(b'RIFF') and header[8:12]==b'WEBP') or b'ftypavif' in header[:20]
   ok=r.ok and magic;r.close();return u,ok
  except requests.RequestException:return u,False
 with ThreadPoolExecutor(max_workers=4) as pool:valid=dict(pool.map(check,titles))
 for e in events:
  u=e.get('image_url') or '';generic=bool(u and (len(titles.get(u,set()))>3 or urlparse(u).path in ['','/'] or any(w in u.lower() for w in ['placeholder','logo','no-image','no_pic','unsplash.com'])))
  if generic or (u and not valid.get(u)):
   e['rejected_source_image_url']=u;e['internal_notes'].append('תמונת המקור כללית או לא נטענה בבדיקת תמונה; נבחרה חלופה מתאימה ככל שקיימת.');u=''
  if not u:
   activity=e.get('activity_type') or e.get('subcategory') or e['category'];bank=None
   if e['category']=='seniors':
    bank='senior-lecture'
    for term,photo in [('digital','senior-digital'),('trip','senior-guided-tour'),('tour','senior-guided-tour'),('workshop','senior-handcraft'),('music','senior-live-music'),('sport','senior-fitness'),('social','senior-social-coffee')]:
     if term in activity:bank=photo;break
    u='/events-preview/shared/images/defaults/ashdod-seniors/'+bank+'.webp'
   elif e['category']=='workshop':u='/events-preview/shared/images/defaults/seniors-workshops.webp'
   if u:e['source_image_kind']='illustration';e['image_caption']='תמונת אילוסטרציה';e['image_strategy']='local_topic_photo_bank'
   else:e['source_image_kind']='not_available';e['image_strategy']='awaiting_suitable_photo';e['internal_notes'].append('חסרה תמונה מתאימה; לא הועתקה תמונה גנרית מהרשומה הישנה.')
  else:
   e['image_strategy']='source_card_image';e['source_image_kind']='source_card_image';e.pop('image_caption',None);e.pop('rejected_source_image_url',None)
  e['image_url']=u or None;e['image_origin_url']=u or None;e['image_verified']=e['image_publishable']=bool(u);e['image_represents_event']=bool(u and e['source_image_kind']!='illustration');e['image_review_status']='source_card_provenance' if e['source_image_kind']=='source_card_image' else e['source_image_kind']
def legacy_local(e):
 return bool(e.get('local_source_refresh') or e.get('source') in SOURCES or any(s.get('name') in SOURCES for s in e.get('sources',[]))) and not str(e.get('source','')).startswith(('supplemental_','mevalim_'))
def merge(snap):
 # Repair snapshots produced before the Ofek midnight-metadata correction.
 def repair_hour(e):
  if e.get('local_source_name')!='ofek_ashdod' or e.get('start_time')!='00:00':return e
  try:
   q=page(e['content_source_url']);field=next((f for f in q.select('.eic-field') if text(f.select_one('.eic-label'))=='שעה'),None);clock=text(field.select_one('.eic-value')) if field else ''
  except requests.RequestException:clock=''
  if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',clock) or clock=='00:00':clock='';e.setdefault('internal_notes',[]).append('שעה מדויקת טרם אומתה; אין לפרסם חצות משדה התאריך המובנה.')
  if e.get('content_completion_status')=='facts_only':e['description']=e['series_description']=''
  kind=e.get('source_image_kind');e['start_time']=clock;e=localize(e,'ofek_ashdod');e['source_image_kind']=kind;return e
 with ThreadPoolExecutor(max_workers=4) as pool:snap['events']=list(pool.map(repair_hour,snap['events']))
 path=ROOT/'events-preview/ashdod/data/events.json';data=json.loads(path.read_text());old=data['events'];archive=OUT/'ashdod-local-reset-backup.json'
 removed=[e for e in old if legacy_local(e) and not e.get('local_source_refresh')]
 if removed and not archive.exists():archive.write_text(json.dumps(dict(at=snap['at'],events=removed),ensure_ascii=False,indent=2)+'\n')
 # Initial user-authorized reset quarantines all legacy local cards. Later failed reads
 # preserve only records already rebuilt under this policy, never old generic material.
 failed={name for name,v in snap['sources'].items() if not v.get('ok') or v.get('issues')}
 kept=[e for e in old if not legacy_local(e) or (e.get('local_source_refresh') and e.get('local_source_name') in failed)]
 new=[];duplicates=0;completed_images=0
 for e in snap['events']:
  classify_local(e)
  match=next((k for k in kept+new if k.get('start_date')==e['start_date'] and str(k.get('start_time') or '')[:5]==e['start_time'] and (equivalent(k,e) or (ticket_identity(k)==ticket_identity(e) and ticket_identity(e)[0]))),None)
  if match:
   if match.get('local_source_refresh'):
    if e['local_source_name']=='mishkan_primary':
     for field in ['venue','venue_address','price_min_ils','price_max_ils','is_free']:
      if match.get(field) is not None:e[field]=match[field]
    if match in kept:kept.remove(match)
    else:new.remove(match)
   else:
    if e.get('source_image_kind')=='source_card_image' and e.get('image_verified') and (not match.get('image_url') or match.get('source_image_kind') in ['illustration','source_placeholder','not_available'] or any(w in str(match.get('image_url')) for w in ['/placeholders/','no_pic.png'])):
     completed_images+=1
     for field in ['image_url','image_origin_url','image_source','image_verified','image_publishable','image_represents_event','source_image_kind','image_strategy','image_review_status']:
      if field in e:match[field]=e[field]
     match.pop('image_caption',None)
    if not match.get('description') and e.get('source_description'):match['description']=match['series_description']=e['source_description']
    match.setdefault('crosscheck_sources',[])
    if e['content_source_url'] not in match['crosscheck_sources']:match['crosscheck_sources'].append(e['content_source_url'])
    duplicates+=1;continue
  if not any(k['event_id']==e['event_id'] for k in new):new.append(e)
 data['events']=kept+new;data['generated_at']=data['generatedAt']=snap['at'];data.setdefault('stats',{})['events']=len(data['events'])
 assert len({e['event_id'] for e in data['events']})==len(data['events'])
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 taxpath=OUT/'taxonomy.json';tax=json.loads(taxpath.read_text())
 for e in new:
  cat=next((c for c in tax['primary_categories'] if c['id']==e['category']),None)
  if not cat:
   cat=dict(id=e['category'],label=e['source_category'] or 'קהילה ופנאי',subcategories=[]);tax['primary_categories'].append(cat)
  if not any(s['id']==e['subcategory'] for s in cat.get('subcategories',[])):
   cat.setdefault('subcategories',[]).append(dict(id=e['subcategory'],label=e.get('source_subcategory') or ('סדנאות לילדים' if e['subcategory']=='creative-workshops' else 'פעילויות'),requires_mapping=e.get('taxonomy_review_required',False)))
 taxpath.write_text(json.dumps(tax,ensure_ascii=False,indent=2)+'\n')
 report={k:v for k,v in snap.items() if k!='events'};report.update(published_local_occurrences=len(new),legacy_quarantined=len(removed),duplicates_matched=duplicates,existing_images_completed=completed_images,with_text=sum(bool(e.get('description')) for e in new),with_image=sum(bool(e.get('image_url')) for e in new),illustrations=sum(e['source_image_kind']=='illustration' for e in new),missing_verified_hour=sum(not e.get('start_time') for e in new),total=len(data['events']))
 (OUT/'ashdod-local-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['sources','undated_services']},ensure_ascii=False),flush=True)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--collect-only',action='store_true');ap.add_argument('--snapshot');a=ap.parse_args();OUT.mkdir(exist_ok=True)
 if a.snapshot:snap=json.loads(Path(a.snapshot).read_text())
 else:
  events=[];states={};undated=[]
  for name,spec in SOURCES.items():
   try:
    p=page(spec['url'])
    if spec['parser']=='smarticket':rows,issues,services=smart(name,spec,p)
    elif spec['parser']=='mishkan_primary':rows,issues,services=primary(name,spec,p)
    elif spec['parser']=='municipal_posts':rows,issues,services=municipal(name,spec,p)
    elif spec['parser']=='ofek':
     raw=extract_ofek_events(p,spec,fetch_once,limit=1000);rows,issues,services=[],[],[]
    elif spec['parser']=='coing':rows,issues,services=coing(name,spec,p)
    else:rows,issues,services=ironit(name,spec,p)
    if spec['parser']=='ofek':
     for r in raw:
      try:rows.append(card(r,name))
      except Exception as ex:issues.append(dict(url=r['ticket_url'],error=str(ex)[:250]))
    events.extend(rows);undated.extend(services);states[name]=dict(ok=True,read=len(rows),issues=issues,undated=len(services),url=spec['url'])
   except Exception as ex:states[name]=dict(ok=False,error=str(ex)[:250],url=spec['url'])
   print(name,json.dumps(states[name],ensure_ascii=False),flush=True)
  image_policy(events);snap=dict(at=datetime.now(Z).isoformat(),sources=states,events=events,undated_services=undated)
 (OUT/'ashdod-local-snapshot.json').write_text(json.dumps(snap,ensure_ascii=False,indent=2)+'\n')
 if not a.collect_only:merge(snap)
if __name__=='__main__':main()
