"""Generate indexable Ashdod category, subtype and event HTML from published facts."""
import json,re,html,hashlib
from pathlib import Path
from urllib.parse import quote,urljoin
from datetime import datetime
from zoneinfo import ZoneInfo
BASE='https://isnet.co.il/events-preview/ashdod/'
def clean(v):
 s=re.sub('<[^>]*>',' ',str(v or ''));return re.sub(r'\s+',' ',s).strip()
def local_title(v):
 s=clean(v);return s if 'אשדוד' in s else s+' באשדוד'
def description(e):return clean(e.get('seo_description') or e.get('short_pitch') or e.get('description') or e.get('series_description'))[:180]
def safe_url(v):return str(v or '') if str(v or '').startswith(('https://','http://')) else ''
def ld(v):return json.dumps(v,ensure_ascii=False).replace('<','\\u003c')
def build_seo(root,events,slug,visible,day):
 folder=root/'events-preview/ashdod';out=folder/'discover';out.mkdir(exist_ok=True)
 taxonomy=json.loads((root/'events-preview/admin/data/taxonomy.json').read_text())['primary_categories']
 taxonomy=[{'id':'stage','label':'הופעות במה','subcategories':[]}]+taxonomy
 cats={x['id']:x for x in taxonomy};rows=[e for e in events if visible(e,day)];manifest={'generated_at':datetime.now(ZoneInfo('UTC')).isoformat(),'categories':{},'events':{},'pages':{}}
 urls=set();report={'generated_at':manifest['generated_at'],'city':'ashdod','events':0,'categories':0,'subcategories':0,'warnings':[],'pages':[]}
 esc=lambda v:html.escape(str(v or ''),quote=True)
 def page(filename,title,desc,body,schema,index=True):
  canonical=BASE+'discover/'+quote(filename);urls.add(canonical) if index else None
  breadcrumbs={'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'מה עושים באשדוד','item':BASE},{'@type':'ListItem','position':2,'name':title,'item':canonical}]}
  text='''<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><base href="../"><title>'''+esc(title)+' | מה עושים באשדוד</title><meta name="description" content="'+esc(desc)+'"><meta name="robots" content="'+('index,follow' if index else 'noindex,follow')+'"><link rel="canonical" href="'+esc(canonical)+'"><meta property="og:title" content="'+esc(title)+'"><meta property="og:description" content="'+esc(desc)+'"><meta property="og:url" content="'+esc(canonical)+'"><meta property="og:type" content="website"><link rel="stylesheet" href="seo-pages.css?v=1"><script defer src="/assets/isnet-top-navigation.js?v=20261021-nav2"></script><script defer src="site-share.js?v=20261019-all-pages2"></script><script src="ashdod-analytics.js?v=20261015-ga-complete1"></script><script type="application/ld+json">'+ld([schema,breadcrumbs])+'</script></head><body><header class="siteTopbar"><div class="isnetBrandGroup"><a href="./"><img src="assets/branding/what-to-do-ashdod-dark.svg" width="145" height="68" alt="מה עושים באשדוד"></a><a href="https://ashdodnet.com/" aria-label="מבית אשדוד נט"><small>מבית</small><img src="assets/branding/ashdodnet-dark.svg" width="80" height="34" alt="אשדוד נט"></a></div><a href="./">ראשי — מה עושים באשדוד</a></header><main><h1>'+esc(title)+'</h1><p class="lead">'+esc(desc)+'</p>'+body+'</main><footer><a href="./">כל הבילויים באשדוד</a> · מבית <a href="https://ashdodnet.com/">אשדוד נט</a></footer></body></html>'
  (out/filename).write_text(text);report['pages'].append({'url':canonical,'title':title,'indexable':index})
  return canonical
 def event_file(e):return 'event-'+slug(e)+'.html'
 def event_link(e):return BASE+'discover/'+quote(event_file(e))
 def card(e):
  return '<article><h2><a href="'+esc(event_link(e))+'">'+esc(local_title(e.get('series_title') or e.get('title')))+'</a></h2><p>'+esc(description(e))+'</p><p>'+esc(e.get('start_date'))+' '+esc(e.get('start_time'))+' · '+esc(e.get('venue'))+'</p></article>'
 for e in rows:
  name=clean(e.get('series_title') or e.get('title'));title=local_title(e.get('seo_title') or name);desc=description(e) or title+' — מידע על האירוע, המקום והזמנת כרטיסים.'
  image=e.get('image_url') if e.get('image_verified') and e.get('image_publishable') else None
  image=urljoin(BASE,image) if image and not str(image).startswith('data:') else None
  schema={'@context':'https://schema.org','@type':'WebPage','name':title,'description':desc,'url':event_link(e)}
  if e.get('start_date') and e.get('venue'):
   dt=e['start_date'];time=e.get('start_time')
   if time and re.match(r'^\d{2}:\d{2}',time):
    try:dt=datetime.fromisoformat(dt+'T'+time[:5]).replace(tzinfo=ZoneInfo('Asia/Jerusalem')).isoformat()
    except ValueError:pass
   schema.update({'@type':'Event','name':name,'startDate':dt,'eventAttendanceMode':'https://schema.org/OfflineEventAttendanceMode','eventStatus':'https://schema.org/'+('EventCancelled' if e.get('status') in ('cancelled','canceled') else 'EventPostponed' if e.get('status')=='postponed' else 'EventScheduled'),'location':{'@type':'Place','name':clean(e['venue']),'address':{'@type':'PostalAddress','streetAddress':clean(e.get('address')),'addressLocality':'אשדוד','addressCountry':'IL'}}})
   if image:schema['image']=[image]
   if e.get('end_date') and e['end_date']>=e['start_date']:schema['endDate']=e['end_date']
   purchase=safe_url(e.get('purchase_url') or e.get('ticket_url'))
   if purchase:
    offer={'@type':'Offer','url':purchase}
    if e.get('is_free') is True:offer.update(price=0,priceCurrency='ILS')
    elif isinstance(e.get('price_min_ils'),(int,float)):offer.update(price=e['price_min_ils'],priceCurrency='ILS')
    if e.get('ticket_status') in ('available','sold_out'):offer['availability']='https://schema.org/'+('SoldOut' if e['ticket_status']=='sold_out' else 'InStock')
    schema['offers']=offer
  else:report['warnings'].append({'event_id':e.get('event_id'),'reason':'Missing date or venue: no Event schema emitted'})
  cat=e.get('category');catname=cats.get(cat,{}).get('label','אירועים');body='<nav><a href="discover/category-'+esc(cat or 'community')+'.html">'+esc(local_title(catname))+'</a></nav>'
  if image:body+='<img class="hero" src="'+esc(image)+'" alt="'+esc(name)+'">'
  body+='<p>'+esc(clean(e.get('description') or e.get('series_description') or e.get('short_pitch')))+'</p><dl><dt>מתי</dt><dd>'+esc(e.get('start_date'))+' '+esc(e.get('start_time'))+'</dd><dt>איפה</dt><dd>'+esc(e.get('venue'))+' · '+esc(e.get('address'))+'</dd></dl><a class="primary" href="event.html?slug='+quote(slug(e))+'">לכל פרטי האירוע והזמנת כרטיסים</a>'
  if e.get('is_free') is True:body+='<p>הכניסה ללא תשלום</p>'
  elif isinstance(e.get('price_min_ils'),(int,float)):body+='<p>מחיר החל מ־'+esc(e['price_min_ils'])+' ₪</p>'
  if e.get('ticket_status')=='sold_out':body+='<p>הכרטיסים אזלו לפי המידע שפורסם.</p>'
  canonical=page(event_file(e),title,desc,body,schema);manifest['events'][str(e['event_id'])]={'url':canonical,'slug':slug(e)};report['events']+=1
 for cat in taxonomy:
  key=cat['id'];selected=[e for e in rows if e.get('category')==key or key=='stage' and e.get('category') in ('music','theatre','standup')];subnav=[]
  for sub in cat.get('subcategories',[]):
   sid=sub['id'];matches=[e for e in selected if e.get('subcategory')==sid];filename='category-'+key+'--'+sid+'.html';title=local_title(sub['label'] if sub['label'] not in ('event','פעילויות') else cat['label']);desc=title+' — אירועים קרובים, מועדים, מקומות ופרטי הזמנה.'
   u=page(filename,title,desc,'<nav><a href="discover/category-'+key+'.html">'+esc(local_title(cat['label']))+'</a></nav>'+''.join(card(e) for e in matches) if matches else '<p>אין כרגע אירועים מתאימים. <a href="./">לכל האירועים באשדוד</a></p>',{'@context':'https://schema.org','@type':'CollectionPage','name':title},bool(matches))
   manifest['categories'][key+':'+sid]={'url':u,'title':title,'description':desc,'count':len(matches),'indexable':bool(matches)};report['subcategories']+=1
   if matches:subnav.append('<a href="'+esc(u)+'">'+esc(title)+'</a>')
  title=local_title(cat['label']);desc=title+' — לוח האירועים הקרובים, מידע על המופעים, מועדים ומקומות. מתעדכן מתוך מערכת האירועים.'
  body='<nav class="chips">'+''.join(subnav)+'</nav>'+(''.join(card(e) for e in selected) or '<p>אין כרגע אירועים מתאימים. <a href="./">לכל הבילויים באשדוד</a></p>')
  u=page('category-'+key+'.html',title,desc,body,{'@context':'https://schema.org','@type':'CollectionPage','name':title},bool(selected));manifest['categories'][key]={'url':u,'title':title,'description':desc,'count':len(selected),'indexable':bool(selected)};report['categories']+=1
  if selected:manifest['pages'][key]=manifest['categories'][key]
 # Remove stale generated pages so hidden/deleted events cannot remain public.
 expected={quote(p['url'].rsplit('/',1)[-1],safe='%-._~') for p in report['pages']}
 from urllib.parse import unquote
 expected={unquote(x) for x in expected}
 for old in out.glob('*.html'):
  if old.name not in expected:old.unlink()
 (folder/'data/seo-index.json').write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':')))
 (root/'events-preview/admin/data/seo-report-ashdod.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 return urls,report
