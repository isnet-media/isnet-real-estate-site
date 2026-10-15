#!/usr/bin/env python3
"""Merge source-bound editorial programs and exact official calendar facts."""
import argparse,copy,hashlib,json,re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta
from pathlib import Path
from urllib.parse import urlsplit,unquote
from zoneinfo import ZoneInfo
import requests
from rishon_editorial_sources import norm,clean
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'events-preview/rishon-lezion';DATA=SITE/'data/events.json';TODAY=datetime.now(ZoneInfo('Asia/Jerusalem')).date();LIMIT=(TODAY+timedelta(days=153)).isoformat();STAMP=datetime.now(ZoneInfo('Asia/Jerusalem')).isoformat()
def venue_key(text):
 n=norm(text)
 if 'friends'in n or 'מופ ת'in n or 'מופת'in n:return 'friends-rishon'
 if 'בית מכבי'in n:return 'beit-maccabi'
 for key in ['חביב','אלון','שקמה','כרמים','גורדון','יד לבנים','אודיטוריום']:
  if key in n:return key
 if 'היכל התרבות' in n or n=='היכל'or 'מאיר ניצן' in n:return 'htrl'
 return n.replace('ראשון לציון','').strip()
def same_venue(a,b):return not a or not b or venue_key(a)==venue_key(b)
def verified_image(url):
 if not url.startswith('https://'):return False
 decoded=unquote(url).lower()
 if any(x in decoded for x in ['logo','placeholder','בית-יד-לבנים','בית_יד_לבנים','כותר-אלון','כותר-ראשון','בית-גורדון','גלריה-לאמנות','default']):return False
 try:
  with requests.get(url,stream=True,timeout=12)as r:return r.ok and r.headers.get('Content-Type','').lower().startswith('image/')
 except requests.RequestException:return False

def canonical_booking(row):
 u=clean(row.get('booking_url'))
 # Some source anchors contain prose instead of a URL. Only a literal source
 # URL can be used for booking, never a guessed route.
 if u and not any(c.isspace()for c in u)and urlsplit(u).scheme in ['http','https']and urlsplit(u).hostname:return u
 if 'זום'in row.get('source_text','')or 'מהכורסא'in row.get('source_category',''):
  m=re.search(r'https://(?:us\d+web\.zoom\.us|lecturesonline\.co\.il)/[^\s<>]+',row.get('source_text',''))
  if m:return m[0].rstrip('.,;')
 return ''

def merge(data,snapshot,catalog,image_checks=True):
 programs=catalog['programs'];rows=[r for r in snapshot['rows']if TODAY.isoformat()<=r['start_date']<=LIMIT];events=data['events'];counts=Counter();images={}
 def needs_image(r):
  return not any(norm(e.get('title'))==norm(r['title'])and e.get('start_date')==r['start_date']and str(e.get('start_time')or'')[:5]==r['start_time']and same_venue(e.get('venue'),r.get('venue'))and e.get('image_verified')and e.get('image_strategy')!='approved_category_illustration'and e.get('image_url')for e in events)
 candidates=sorted(set(r.get('image_url')or''for r in rows if r.get('image_url')and needs_image(r)))
 if image_checks:
  with ThreadPoolExecutor(max_workers=4)as pool:images=dict(zip(candidates,pool.map(verified_image,candidates)))
 calendar_slots=Counter((r['source'],norm(r['title']),r['start_date'],r['start_time'])for r in rows)
 for row in rows:
  title=norm(row['title']);program=next((p for p in programs if p.get('lookup_url')==row['detail_url']and norm(p['lookup_title'])==title),None)or next((p for p in programs if not p.get('lookup_url')and norm(p['lookup_title'])==title),None)
  if not program:
   counts['unidentified_programs']+=1;continue
  stable_id='local_ri_'+hashlib.sha256((row['source']+row['detail_url']+row['title']+row['start_date']+row['start_time']+row['venue']).encode()).hexdigest()[:20]
  matches=[e for e in events if e.get('event_id')==stable_id or norm(e.get('title'))==title and e.get('start_date')==row['start_date']and str(e.get('start_time')or'')[:5]==row['start_time']and (same_venue(e.get('venue'),row.get('venue'))or(calendar_slots[(row['source'],title,row['start_date'],row['start_time'])]==1 and any(x.get('name')==row['source']or(row['source']=='kotar'and x.get('name')=='kotar_rishon')for x in e.get('sources',[]))))]
  if matches:primary=max(matches,key=lambda e:(e.get('is_active')is not False,bool(e.get('source_content_authoritative')),len(e.get('long_description')or e.get('description')or''),bool(e.get('image_verified'))))
  else:
   primary={'event_id':stable_id,'city':'ראשון לציון','title':row['title'],'start_date':row['start_date'],'start_time':row['start_time'],'venue':row['venue'],'status':'active','is_active':True,'sources':[]};events.append(primary);counts['added']+=1
  if primary.get('content_origin')=='manual'and primary.get('content_locked'):
   counts['preserved_manual']+=1;continue
  original_image=primary.get('image_verified')and primary.get('image_url')and primary.get('image_strategy')!='approved_category_illustration'
  category=program['category'];sub=program.get('subcategory')or category;desc=program['description'];audiences=['kids','families']if category=='kids'else['adults']
  if row['source']=='htrl_adults' or sub.startswith('senior-')or 'אזרחים ותיקים' in row.get('source_text',''):audiences.append('seniors')
  if 'נשים בלבד'in row.get('source_text',''):audiences.append('women')
  if 'גברים בלבד'in row.get('source_text',''):audiences.append('men')
  primary.update(category=category,subcategory=sub,audiences=sorted(set(audiences)),description=desc,long_description=desc,series_description=desc,short_pitch=desc.split('. ')[0]+'.',editorial_description=desc,description_manual_override=True,content_locked=True,source_content_authoritative=True,content_origin='editorial',editorial_version=1,content_source_url=row['detail_url'],detail_source_url=row['detail_url'],source_description=row.get('source_text',''),content_enrichment_status='ready',content_ready_for_media=True,local_source_name='htrl_adults'if row['source']=='htrl_adults'else row['source'],last_verified_at=snapshot['checked_at'])
  if primary.get('duplicate_of'):
   primary.pop('duplicate_of',None);primary.pop('canonical_event_id',None);primary['is_active']=True
  booking=canonical_booking(row)
  if booking:primary.update(ticket_url=booking,purchase_url=booking,purchase_source='official_event_booking')
  elif not primary.get('purchase_url')or primary.get('purchase_source') in ['official_listing','direct']:primary.update(ticket_url=row['detail_url'],purchase_url=row['detail_url'],purchase_source='official_event_detail')
  if not primary.get('address')and row.get('address'):primary['address']=row['address']
  primary['categories']=sorted(set(primary.get('categories',[])+[category]+(['seniors']if'seniors'in audiences else[])))
  source={'name':'kotar_rishon'if row['source']=='kotar'else row['source'],'url':row['detail_url'],'source_type':'official','observed_at':snapshot['checked_at']}
  primary['sources']=[s for s in primary.get('sources',[])if s.get('name') not in [row['source'],source['name']]]+[source]
  if row.get('ticket_status'):primary['ticket_status']=row['ticket_status']
  elif 'אזלו הכרטיסים'in row['title']:primary['ticket_status']='sold_out'
  if row.get('duration_text'):
   m=re.search(r'(\d+)\s*(?:דק|דקות)',row['duration_text'])
   if m:primary['duration_minutes']=int(m[1])
  if row.get('price_text'):
   m=re.search(r'\d+(?:\.\d+)?',row['price_text'])
   if m:primary['price_min_ils']=float(m[0]);primary['is_free']=float(m[0])==0
   elif 'ללא תשלום'in row['price_text']:primary['is_free']=True;primary['price_min_ils']=0
  if category=='kids'and row.get('age_text'):
   # Keep the exact age wording; developmental groups are not rounded into
   # invented numeric bounds.
   primary['age_text']=row['age_text'];numbers=[int(x)for x in re.findall(r'\d+',row['age_text'])]
   if len(numbers)==2:primary['age_min']=min(numbers);primary['age_max']=max(numbers)
   elif 'חצי שנה'in row['age_text']:
    primary['age_min']=.5
    if numbers:primary['age_max']=numbers[-1]
  if 'מהכורסא'in row.get('source_category','')or 'בזום'in row.get('source_text',''):
   primary['attendance_mode']='online';primary['venue']='אונליין — לצפייה מהבית';primary['address']=None
  if not original_image and images.get(row.get('image_url')):
   primary.update(image_url=row['image_url'],image_source=row['detail_url'],image_origin_url=row['image_url'],image_credit=row.get('image_credit')or'צילום או כרזה: אתר המארגן הרשמי',image_verified=True,image_publishable=True,image_strategy='official_event_poster_remote',image_rights_status='verified_official_source',thumbnail_url=row['image_url'],thumbnail_ready=True);counts['source_images']+=1
  primary['target_audience']=['ילדים ומשפחות']if category=='kids'else['מבוגרים','גמלאים']if'seniors'in audiences else['קהל בוגר']
  counts['enriched']+=1
  for duplicate in matches:
   if duplicate is primary:continue
   duplicate['is_active']=False;duplicate['canonical_event_id']=primary['event_id'];duplicate['duplicate_of']=primary['event_id'];counts['duplicates']+=1
 data['generated_at']=STAMP;data['generatedAt']=STAMP;data['events']=events
 return data,dict(counts)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--snapshot',default='/tmp/rishon-editorial-sources.json');ap.add_argument('--skip-image-check',action='store_true');a=ap.parse_args()
 data=json.loads(DATA.read_text());snapshot=json.loads(Path(a.snapshot).read_text());catalog=json.loads((SITE/'data/editorial-programs.json').read_text());data,counts=merge(data,snapshot,catalog,not a.skip_image_check);DATA.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');report={'checked_at':STAMP,'counts':counts,'source_errors':snapshot.get('errors',{})};(ROOT/'events-preview/admin/data/rishon-editorial-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
