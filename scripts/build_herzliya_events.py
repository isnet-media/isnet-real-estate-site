#!/usr/bin/env python3
"""Adapt Herzliya-owned data to the shared ISNET event UI and generate canonical pages."""
import json,hashlib,re,html
from pathlib import Path
from urllib.parse import urljoin,urlsplit
ROOT=Path(__file__).resolve().parents[1];C=ROOT/'events-preview/herzliya';D=C/'data';BASE='https://isnet.co.il/events-preview/herzliya/'
def read(n):return json.loads((D/(n+'.json')).read_text())
def save(n,x):(D/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def absolute(u):
 v=urljoin(BASE,u);return urlsplit(v).path if urlsplit(v).hostname=='isnet.co.il' else v
def production_identity(e):
 # Audience/program labels describe a performance slot, not a different production.
 title=re.sub(r'^(?:בין ערביים|קומדיה על הבוקר)\s*[-–—:]\s*','',e['title']).strip()
 if e.get('category')!='theatre':return None
 key=re.sub(r'[^א-תa-zA-Z0-9]+',' ',title).strip().lower()
 venue=re.sub(r'[^א-תa-zA-Z0-9]+',' ',e.get('venue','')).strip().lower()
 return title,key,venue

def build():
 raw=read('events');cats=read('categories')['categories'];guides=read('guides')['items'];food=read('restaurants')['items'];events=[]
 submap={'shows':'kids-shows','story':'story-time','workshops':'kids-workshops','live':'live-music','singing':'live-music','meetings':'cinema','screenings':'cinema','lectures':'general-lectures','design':'exhibitions','art':'exhibitions','comics':'exhibitions'}
 identities={e['id']:production_identity(e) for e in raw['events']}
 labelled_keys={value[1:] for e in raw['events'] if (value:=identities[e['id']]) and value[0]!=e['title']}
 for e in raw['events']:
  x=dict(e,event_id=e['id'],purchase_url=e['booking_url'],ticket_url=e['source_url'],image_url=e['image'],thumbnail_url=e['image'],thumbnail_ready=True,image_publishable=True,image_verified=True,image_represents_event=e.get('image_role')=='official_promotional',source_image_kind='official_promotional' if e.get('image_role')=='official_promotional' else 'illustration',image_rights_status='official_promotional' if e.get('image_role')=='official_promotional' else 'owned_ai_illustration',price_min_ils=e.get('price'),price_max_ils=e.get('price'),is_free=True if e.get('price')==0 else None,is_active=True,publication_status='published',source_content_authoritative=True,sources=[{'name':e['source_id'],'url':e['source_url']}],subcategory=submap.get(e['subcategory'],e['subcategory']))
  identity=identities[e['id']]
  if identity and identity[1:] in labelled_keys:
   x['series_id']='herzliya-production-'+hashlib.sha256('|'.join(identity[1:]).encode()).hexdigest()[:16]
   x['series_title']=identity[0]
   x['source_title']=e['title']
   x['production_match_method']='exact title after removing reviewed program prefix; same venue'
  members=[{'category':e['category'],'subcategory':x['subcategory']}]
  for a in e.get('audiences',[]):
   if a in ['seniors','kids'] and a!=e['category']:members.append({'category':a,'subcategory':({'music':'senior-music','lecture':'senior-lectures'}.get(e['category'],'senior-culture')) if a=='seniors' else 'kids-shows'})
  x['category_memberships']=members;events.append(x)
 public={'city':'הרצליה','city_slug':'herzliya','generated_at':raw['generated_at'],'events':events};save('events-public',public)
 (D/'site.json').write_text(json.dumps(dict(raw,categories=cats,guides=guides,restaurants=food,sources=read('sources')['sources']),ensure_ascii=False,separators=(',',':'))+'\n')
 # Convert directory records only; never copy city-owned data from another edition.
 def place(x):return dict(id=x['id'],name=x['title'],title=x['title'],description=x['description']+(' '+x['notice'] if x.get('notice') else ''),source_url=x['source_url'],museum_url=x['source_url'],operator_website_url=x['source_url'],image=absolute(x['image']),image_credit=x['image_credit'],image_alt=x['title'] if x.get('image_role')=='official_promotional' else 'תמונת המחשה בלבד',image_role=x.get('image_role','illustration'),map_query=(x.get('address') or x['title'])+' הרצליה',location=x.get('address') or 'הרצליה',badges=['הרצליה'],checked_at=raw['generated_at'][:10],kind='water' if x.get('subcategory')=='water' else 'culture' if x['category'] in ['exhibition','theatre','cinema'] else 'outdoor',audiences=['kids','families','adults'])
 paths={'parks':[g for g in guides if g['category']=='parks'],'culture':[g for g in guides if g['category'] in ['theatre','exhibition','cinema']],'nature':[g for g in guides if g['id'] in ['peres','fitness']],'attractions':[g for g in guides if g['category']=='attractions'],'must-see':[g for g in guides if g['id'] in ['peres','design','comics','mediatheque']]};paths['beaches']=[g for g in guides if g['category']=='beaches'];paths['nature']=[g for g in guides if g['category'] in ['nature','parks']];paths['must-see']=[g for g in guides if g['id'] in ['park','apollonia','marina','museum','rishonim']]
 catdata={}
 for key,items in paths.items():
  title={'parks':'פארקים בהרצליה','culture':'מוסדות תרבות בהרצליה','nature':'טבע וטיולים בהרצליה','attractions':'אטרקציות בהרצליה','must-see':'מקומות להכיר בהרצליה','beaches':'מקומות פתוחים בהרצליה'}[key]
  image=absolute(items[0]['image']) if items else absolute('../kiryat-gat/assets/illustrations/park.jpg')
  catdata[key]=dict(title=title,intro='מקומות ומוסדות בעיר, עם קישור למקור ולפרטים העדכניים. התמונות המקור נושאות קרדיט; תמונות המחשה מסומנות.',hero_image=image,hero_credit=items[0]['image_credit'] if items else '',hero_alt=items[0]['title'] if items else title,hero_image_role=items[0].get('image_role','illustration') if items else 'illustration',items=[place(g) for g in items])
 save('places',{'categories':catdata});save('attractions-guide',{'items':[],'verified_sources':[place(g) for g in guides if g['category']=='attractions']});save('institutions',{'institutions':[place(g) for g in guides if g['category'] in ['theatre','exhibition','cinema']]})
 save('family-guide',{'links':[['',g['title'],g['description'],g['source_url']] for g in guides if g['id'] in ['agada','community','park','apollonia','museum']]})
 save('senior-guide',{'checked_at':raw['generated_at'][:10],'note':'מועדים וזמינות לפי המקור הרשמי.','links':[{'title':g['title'],'description':g['description'],'url':g['source_url']} for g in guides if g['id'] in ['ale','sirkin','gold','community','cinema']]})
 if (D/'senior-catalog.json').exists():
  guide=read('senior-guide');existing={x['url'] for x in guide['links']}
  for source in read('senior-catalog')['sources']:
   if source['url'] not in existing:guide['links'].append(dict(title=source['name'],description='חוגים, מסגרות ומידע מהמקור. פרטים עדכניים והרשמה באתר המפעיל.',url=source['url']))
  save('senior-guide',guide)
 save('editorial',{'events':{}});save('senior-culture',{'programs':[]});save('sports',{'branches':{},'teams':[]});save('classes',{'records':[]})
 saturday=[]
 for g in [*guides,*food]:
  if not g.get('saturday'):continue
  saturday.append(dict(id=g['id'],title=g['title'],kind='food' if g['category']=='food' else 'nature',area='city',city='הרצליה',venue=g['title'],description=g['description'],family=True,recurring_saturday=True,saturday_verified=True,source_url=g['source_url'],booking_url=g.get('booking_url') or g['source_url'],image=absolute(g['image']),image_credit=g['image_credit'],image_role='illustration',checked_on='2026-11-01',recheck_on='2026-11-01',note='בדקו שעות עדכניות לפני יציאה.'))
 save('saturday-guide',{'items':saturday})
 movies={}
 for e in events:
  if e['category']!='cinema':continue
  key=re.sub(r'\s*\((?:שלישי זהב|ללא תשלום למנויים)\)','',e['title']).strip();m=movies.setdefault(key,dict(id='herzliya-film-'+hashlib.sha256(key.encode()).hexdigest()[:12],title=key,synopsis=e['description'],poster_url=absolute(e['image_url']),poster_credit=e['image_credit'],poster_verification={'url':absolute(e['image_url']),'kind':e['source_image_kind'],'source':e['source_url']},poster_alt=e['title'] if e['source_image_kind']=='official_promotional' else 'תמונת המחשה — לא כרזה רשמית של הסרט',is_family='kids' in e.get('audiences',[]),venues=[]))
  vid='hot-cinema' if 'hotcinema.co.il' in e['source_url'] else 'kids-cinema' if e['source_id']=='mediatheque' else 'cinematheque';v=next((v for v in m['venues'] if v['id']==vid),None)
  if v is None:v=dict(id=vid,name='HOT CINEMA DREAM STAGE הרצליה' if vid=='hot-cinema' else 'סינמטק הילדים — מדיטק' if vid=='kids-cinema' else 'סינמטק הרצליה',article_url=e['source_url'],schedule={},sessions=[]);m['venues'].append(v)
  v['schedule'].setdefault(e['start_date'],[]).append(e['start_time']);v['sessions'].append(dict(date=e['start_date'],time=e['start_time'],booking_url=e['purchase_url']))
 from herzliya_cinema_metadata import enrich_movies,write_media_report
 enrich_movies(list(movies.values()),events)
 write_media_report(events,list(movies.values()))
 from refresh_herzliya_city_cinema import merge_into
 save('cinema',merge_into({'city':'הרצליה','source_name':'לוחות המארגנים הרשמיים בהרצליה','updated_at':raw['generated_at'],'movies':list(movies.values())}))
 from shutil import copyfile
 cover=next((g for g in guides if g['id']=='park' and g.get('image_role')=='official_promotional'),next((g for g in guides if g.get('image_role')=='official_promotional'),None))
 if cover:copyfile(C/cover['image'],C/'assets/share-card.jpg')
 from herzliya_cinema_loading import build_listing
 build_listing()
 branding=C/'assets/branding';branding.mkdir(parents=True,exist_ok=True)
 for old,new in [('what-to-do-kgat-dark.svg','what-to-do-herzliya-dark.svg'),('kgatnet-dark.svg','herzliyanet-dark.svg')]:
  text=(ROOT/'events-preview/kiryat-gat/assets/branding'/old).read_text().replace('קריית גת','הרצליה').replace('בקרית גת','בהרצליה');(branding/new).write_text(text.replace('הרצליה נט','ישראל נט'))
 (C/'category-fallbacks.json').write_text('{}\n')
 # Adapter supplies the canonical normalized snapshot to every list/detail/hub.
 adapter='''/* Herzliya-owned source snapshot for the shared ISNET frontend. */
(()=>{const raw=()=>window.ISNET_CITY_BOOTSTRAP?Promise.resolve(window.ISNET_CITY_BOOTSTRAP):fetch('data/events-public.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('Herzliya feed unavailable');return r.json()});const data=()=>Promise.resolve(window.ISNET_EVENT_IDENTITIES?.ready).then(raw).then(d=>({...d,events:(d.events||[]).map(e=>window.ISNET_EVENT_IDENTITIES?.sanitize(e)||e)}));window.ISNET_PUBLIC_CMS={loadSource:data,loadCards:data,loadHub:data,publishedEvents:()=>Promise.resolve([]),metrics:{}};window.HERZLIYA_EVENTS={matches:(e,ids)=>ids.has(e.category)||(e.category_memberships||[]).some(m=>ids.has(m.category))||(ids.has('seniors')&&e.audiences?.includes('seniors'))||(ids.has('kids')&&e.audiences?.includes('kids'))};})();\n'''
 (C/'herzliya-events.js').write_text(adapter)
 from sync_event_city_views import files_to_sync,localize,TARGETS
 city=TARGETS['herzliya']
 for src in [*files_to_sync(),*(ROOT/'events-preview/ashdod/pilot').glob('*')]:
  if not src.is_file() or src.suffix not in ['.html','.css','.js']:continue
  rel=src.relative_to(ROOT/'events-preview/ashdod');target=C/rel;target.parent.mkdir(parents=True,exist_ok=True)
  target.write_text(localize(src.read_text(),str(rel),city,src.suffix))
 from herzliya_city_view import build_food
 build_food()
 from build_holon_health import build as health_builder
 def build_health():return health_builder(city_dir=C)
 build_health()
 # Preserve formerly shared hub URLs without introducing another UI implementation.
 for name,cat in [('kids','kids'),('seniors','seniors')]:
  (C/(name+'.html')).write_text('<!doctype html><html lang="he" dir="rtl"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=category.html?category='+cat+'"><a href="category.html?category='+cat+'">למדור בהרצליה</a></html>')
 # Keep the source coverage report, integrated with the same branding assets.
 report=read('source-report');rows=''.join('<li><a href="'+html.escape(s['url'],quote=True)+'">'+html.escape(s['name'])+'</a> — '+html.escape({'collected':'אירועים נקלטו','interactive_source':'מקור אינטראקטיבי — קישור ישיר','linked_directory':'מדריך מקושר','closure_notice':'מופיעה הודעת סגירה'}.get(s['status'],'יש לבדוק מול המקור'))+'</li>' for s in report['sources'])
 (C/'sources.html').write_text('<!doctype html><html lang="he" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>מקורות — מה עושים בהרצליה</title><link rel="stylesheet" href="styles.css"><link rel="stylesheet" href="publisher-brand.css"><script defer src="/assets/isnet-top-navigation.js?v=herzliya-canonical"></script><body><main style="max-width:1000px;margin:40px auto;padding:20px;color:#f5e6ca"><a href="./">מה עושים בהרצליה — ראשי</a><h1>מקורות ועדכונים</h1><p>מקורות אינטראקטיביים זמינים בקישור ישיר. תמונות ההמחשה מסומנות ואינן צילום מהמקום.</p><ul>'+rows+'</ul></main></body></html>')
 print('Canonical Herzliya edition:',len(events),'occurrences;',len(food),'culinary venues')
if __name__=='__main__':build()
