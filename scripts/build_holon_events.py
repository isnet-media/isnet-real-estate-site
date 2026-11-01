#!/usr/bin/env python3
"""Adapt Holon-owned data to the shared ISNET event UI and generate canonical pages."""
import json,hashlib,re,html
from pathlib import Path
from urllib.parse import urljoin
ROOT=Path(__file__).resolve().parents[1];C=ROOT/'events-preview/holon';D=C/'data';BASE='https://isnet.co.il/events-preview/holon/'
def read(n):return json.loads((D/(n+'.json')).read_text())
def save(n,x):(D/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def absolute(u):return urljoin(BASE,u)
def build():
 raw=read('events');cats=read('categories')['categories'];guides=read('guides')['items'];food=read('restaurants')['items'];events=[]
 submap={'shows':'kids-shows','story':'story-time','workshops':'kids-workshops','live':'live-music','singing':'live-music','meetings':'cinema','screenings':'cinema','lectures':'general-lectures','design':'exhibitions','art':'exhibitions','comics':'exhibitions'}
 for e in raw['events']:
  x=dict(e,event_id=e['id'],purchase_url=e['booking_url'],ticket_url=e['source_url'],image_url=e['image'],thumbnail_url=e['image'],thumbnail_ready=True,image_publishable=True,image_verified=True,image_represents_event=e.get('image_role')=='official_promotional',source_image_kind='official_promotional' if e.get('image_role')=='official_promotional' else 'illustration',image_rights_status='official_promotional' if e.get('image_role')=='official_promotional' else 'owned_ai_illustration',price_min_ils=e.get('price'),price_max_ils=e.get('price'),is_free=True if e.get('price')==0 else None,is_active=True,publication_status='published',source_content_authoritative=True,sources=[{'name':e['source_id'],'url':e['source_url']}],subcategory=submap.get(e['subcategory'],e['subcategory']))
  members=[{'category':e['category'],'subcategory':x['subcategory']}]
  for a in e.get('audiences',[]):
   if a in ['seniors','kids'] and a!=e['category']:members.append({'category':a,'subcategory':({'music':'senior-music','lecture':'senior-lectures'}.get(e['category'],'senior-culture')) if a=='seniors' else 'kids-shows'})
  x['category_memberships']=members;events.append(x)
 public={'city':'חולון','city_slug':'holon','generated_at':raw['generated_at'],'events':events};save('events-public',public)
 (D/'site.json').write_text(json.dumps(dict(raw,categories=cats,guides=guides,restaurants=food,sources=read('sources')['sources']),ensure_ascii=False,separators=(',',':'))+'\n')
 # Convert directory records only; never copy city-owned data from another edition.
 def place(x):return dict(id=x['id'],name=x['title'],title=x['title'],description=x['description']+(' '+x['notice'] if x.get('notice') else ''),source_url=x['source_url'],museum_url=x['source_url'],operator_website_url=x['source_url'],image=absolute(x['image']),image_credit=x['image_credit'],image_alt='תמונת המחשה בלבד',image_role='illustration',map_query=(x.get('address') or x['title'])+' חולון',location=x.get('address') or 'חולון',badges=['חולון'],checked_at='2026-11-01',kind='water' if x.get('subcategory')=='water' else 'culture' if x['category'] in ['exhibition','theatre','cinema'] else 'outdoor',audiences=['kids','families','adults'])
 paths={'parks':[g for g in guides if g['category']=='parks'],'culture':[g for g in guides if g['category'] in ['theatre','exhibition','cinema']],'nature':[g for g in guides if g['id'] in ['peres','fitness']],'attractions':[g for g in guides if g['category']=='attractions'],'must-see':[g for g in guides if g['id'] in ['peres','design','comics','mediatheque']]};paths['beaches']=paths['nature']
 catdata={}
 for key,items in paths.items():
  title={'parks':'פארקים בחולון','culture':'מוסדות תרבות בחולון','nature':'טבע וטיולים בחולון','attractions':'אטרקציות בחולון','must-see':'מקומות להכיר בחולון','beaches':'מקומות פתוחים בחולון'}[key]
  image=absolute(items[0]['image']) if items else absolute('../kiryat-gat/assets/illustrations/park.jpg')
  catdata[key]=dict(title=title,intro='מקומות ומוסדות בעיר, עם קישור למקור ולפרטים העדכניים. התמונות המסומנות הן להמחשה.',hero_image=image,hero_credit='תמונת המחשה — לא צילום מהמקום',hero_alt='תמונת המחשה',hero_image_role='illustration',items=[place(g) for g in items])
 save('places',{'categories':catdata});save('attractions-guide',{'items':[],'verified_sources':[place(g) for g in guides if g['category']=='attractions']});save('institutions',{'institutions':[place(g) for g in guides if g['category'] in ['theatre','exhibition','cinema']]})
 save('family-guide',{'links':[['',g['title'],g['description'],g['source_url']] for g in guides if g['id'] in ['children','mediatheque','community','peres','water','lapark']]})
 save('senior-guide',{'checked_at':'2026-11-01','note':'מועדים וזמינות לפי המקור הרשמי.','links':[{'title':g['title'],'description':g['description'],'url':g['source_url']} for g in guides if g['id'] in ['senior-clubs','psagot','community']]})
 save('editorial',{'events':{}});save('senior-culture',{'programs':[]});save('sports',{'branches':{},'teams':[]});save('classes',{'records':[]})
 saturday=[]
 for g in [*guides,*food]:
  if not g.get('saturday'):continue
  saturday.append(dict(id=g['id'],title=g['title'],kind='food' if g['category']=='food' else 'nature',area='city',city='חולון',venue=g['title'],description=g['description'],family=True,recurring_saturday=True,saturday_verified=True,source_url=g['source_url'],booking_url=g.get('booking_url') or g['source_url'],image=absolute(g['image']),image_credit=g['image_credit'],image_role='illustration',checked_on='2026-11-01',recheck_on='2026-11-01',note='בדקו שעות עדכניות לפני יציאה.'))
 save('saturday-guide',{'items':saturday})
 movies={}
 for e in events:
  if e['category']!='cinema':continue
  key=e['title'];m=movies.setdefault(key,dict(id='holon-film-'+hashlib.sha256(key.encode()).hexdigest()[:12],title=key,synopsis=e['description'],poster_url=absolute(e['image_url']),poster_credit=e['image_credit'],poster_verification={'url':absolute(e['image_url']),'kind':e['source_image_kind'],'source':e['source_url']},poster_alt=e['title'] if e['source_image_kind']=='official_promotional' else 'תמונת המחשה — לא כרזה רשמית של הסרט',is_family='kids' in e.get('audiences',[]),venues=[]))
  vid='hot-cinema' if 'hotcinema.co.il' in e['source_url'] else 'cinema-city';v=next((v for v in m['venues'] if v['id']==vid),None)
  if v is None:v=dict(id=vid,name='HOT CINEMA DREAM STAGE חולון' if vid=='hot-cinema' else 'סינמטק חולון',article_url=e['source_url'],schedule={},sessions=[]);m['venues'].append(v)
  v['schedule'].setdefault(e['start_date'],[]).append(e['start_time']);v['sessions'].append(dict(date=e['start_date'],time=e['start_time'],booking_url=e['purchase_url']))
 save('cinema',{'city':'חולון','source_name':'לוחות המארגנים הרשמיים בחולון','updated_at':raw['generated_at'],'movies':list(movies.values())})
 branding=C/'assets/branding';branding.mkdir(exist_ok=True)
 for old,new in [('what-to-do-kgat-dark.svg','what-to-do-holon-dark.svg'),('kgatnet-dark.svg','holonnet-dark.svg')]:
  text=(ROOT/'events-preview/kiryat-gat/assets/branding'/old).read_text().replace('קריית גת','חולון').replace('בקרית גת','בחולון');(branding/new).write_text(text)
 (C/'category-fallbacks.json').write_text('{}\n')
 # Adapter supplies the canonical normalized snapshot to every list/detail/hub.
 adapter='''/* Holon-owned source snapshot for the shared ISNET frontend. */
(()=>{const data=()=>window.ISNET_CITY_BOOTSTRAP?Promise.resolve(window.ISNET_CITY_BOOTSTRAP):fetch('data/events-public.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('Holon feed unavailable');return r.json()});window.ISNET_PUBLIC_CMS={loadSource:data,loadCards:data,loadHub:data,publishedEvents:()=>Promise.resolve([]),metrics:{}};window.HOLON_EVENTS={matches:(e,ids)=>ids.has(e.category)||(e.category_memberships||[]).some(m=>ids.has(m.category))||(ids.has('seniors')&&e.audiences?.includes('seniors'))||(ids.has('kids')&&e.audiences?.includes('kids'))};})();\n'''
 (C/'holon-events.js').write_text(adapter)
 from sync_event_city_views import files_to_sync,localize,TARGETS
 city=TARGETS['holon']
 for src in [*files_to_sync(),*(ROOT/'events-preview/ashdod/pilot').glob('*')]:
  if not src.is_file() or src.suffix not in ['.html','.css','.js']:continue
  rel=src.relative_to(ROOT/'events-preview/ashdod');target=C/rel;target.parent.mkdir(parents=True,exist_ok=True)
  target.write_text(localize(src.read_text(),str(rel),city,src.suffix))
 from holon_city_view import build_food
 build_food()
 from build_holon_health import build as build_health
 build_health()
 # Preserve formerly shared hub URLs without introducing another UI implementation.
 for name,cat in [('kids','kids'),('seniors','seniors')]:
  (C/(name+'.html')).write_text('<!doctype html><html lang="he" dir="rtl"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=category.html?category='+cat+'"><a href="category.html?category='+cat+'">למדור בחולון</a></html>')
 # Keep the source coverage report, integrated with the same branding assets.
 report=read('source-report');rows=''.join('<li><a href="'+html.escape(s['url'],quote=True)+'">'+html.escape(s['name'])+'</a> — '+html.escape({'collected':'אירועים נקלטו','interactive_source':'מקור אינטראקטיבי — קישור ישיר','linked_directory':'מדריך מקושר','closure_notice':'מופיעה הודעת סגירה'}.get(s['status'],'יש לבדוק מול המקור'))+'</li>' for s in report['sources'])
 (C/'sources.html').write_text('<!doctype html><html lang="he" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>מקורות — מה עושים בחולון</title><link rel="stylesheet" href="styles.css"><link rel="stylesheet" href="publisher-brand.css"><script defer src="/assets/isnet-top-navigation.js?v=holon-canonical"></script><body><main style="max-width:1000px;margin:40px auto;padding:20px;color:#f5e6ca"><a href="./">מה עושים בחולון — ראשי</a><h1>מקורות ועדכונים</h1><p>מקורות אינטראקטיביים זמינים בקישור ישיר. תמונות ההמחשה מסומנות ואינן צילום מהמקום.</p><ul>'+rows+'</ul></main></body></html>')
 print('Canonical Holon edition:',len(events),'occurrences;',len(food),'culinary venues')
if __name__=='__main__':build()
