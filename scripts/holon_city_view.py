"""Small Holon adaptations to the canonical Ashdod event frontend, never a separate UI."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'events-preview';CITY=ROOT/'holon'
def read(name):return json.loads((CITY/'data'/(name+'.json')).read_text())
def decorate(content,name,suffix):
 content=content.replace('הים, התרבות, הטבע והפינות שעוד לא הכרתם.','התרבות, הפארקים והפינות שעוד לא הכרתם.').replace('discover-ashdod','discover-holon')
 content=content.replace('ראשון לציון','חולון').replace('לגלות תרבות בראשון','תרבות בחולון').replace('סינמה סיטי','סינמטק חולון')
 content=content.replace('https://www.cinema-city.co.il/','https://www.cinemaholon.org.il/')
 content=content.replace('location.pathname.includes("/rishon-lezion/")?"rishon-lezion":"ashdod"','"holon"')
 content=content.replace("cityEvents('ashdod')","cityEvents('holon')").replace("cityEvents('rishon-lezion')","Promise.resolve({events:[]})")
 if name=='saturday.js':
  content=content.replace("fetch('../ashdod/data/cinema.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error();return r.json()})","Promise.resolve({movies:[]})")
 if name=='category-landing.js':
  content=content.replace('ids.has(e.category)','window.HOLON_EVENTS.matches(e,ids)')
 if name.endswith('.js') and Path(name).name=='app.js':
  content=content.replace("'<div class=\"cinemaCard__body\">'+","'<div class=\"cinemaCard__body\"><small class=\"imageCredit\">'+escapeHtml(movie.poster_credit||'')+'</small>'+")
  content=content.replace('fetch("category-fallbacks.json?v=20261005-21").then(r=>r.json()).catch(()=>({}))','Promise.resolve({})')
  content=content.replace('if(state.category&&e.category!==state.category)return false;','if(state.category&&!window.HOLON_EVENTS.matches(e,new Set([state.category])))return false;')
  content=content.replace('ids.has(e.category)','window.HOLON_EVENTS.matches(e,ids)')
 if name in ['kids-hub.js','seniors-hub.js']:
  content=content.replace('פארקים, ים, תרבות ורעיונות לבילוי משפחתי','פארקים, תרבות ורעיונות לבילוי משפחתי').replace("['חופים וטיילת','חול, אוויר ים וזמן ביחד','places.html?category=beaches','≈']","['פעילויות בקהילה','מפגשים ופעילויות למשפחה','category.html?category=community','◎']").replace("['חופים','ים, אוויר ורגע לעצמכם','places.html?category=beaches','≈']","['מוסדות תרבות','מוזיאונים ומקומות להכיר','places.html?category=culture','◇']")
 if name=='site-search-chat.js':content=content.replace('/meusharim/ashdod/data/classes.json','data/classes.json')
 if name=='index.html':
  # Restore the canonical culinary entry using the existing city's own catalog.
  src=(ROOT/'ashdod/index.html').read_text()
  food=re.search(r'<a\b[^>]*class="[^"]*culinaryHomepageFeature[^"]*"[^>]*data-ashdod-culinary[^>]*>[\s\S]*?</a>',src)
  if food:
   card=food[0].replace(' data-ashdod-culinary',' data-holon-culinary')
   content=content.replace('<nav class="isnetNavDiscovery__lifestyle" aria-label="בילויים וקולינריה">','<nav class="isnetNavDiscovery__lifestyle" aria-label="בילויים וקולינריה">'+card,1)
  # Holon has no beach; do not present another city's coastline as local.
  content=re.sub(r'<a class="cityDiscover__card"[^>]*href="places.html\?category=beaches"[\s\S]*?</a>','',content)
  content=re.sub(r'<a class="isnetNavSmall"[^>]*href="places.html\?category=beaches"[\s\S]*?</a>','',content)
  # Preserve old shared links while using the same real detail routes as every edition.
  aliases={x['id']:('restaurants.html?place=' if x.get('category')=='food' else 'attraction.html?id=')+x['id'] for x in [*read('guides')['items'],*read('restaurants')['items']]}
  code='(()=>{const p=new URLSearchParams(location.search);if(p.get("id"))location.replace("event.html?id="+encodeURIComponent(p.get("id")));const old='+json.dumps(aliases,ensure_ascii=False)+';if(p.get("place")&&old[p.get("place")])location.replace(old[p.get("place")]);})();'
  content=content.replace('</head>','<script>'+code+'</script></head>')
 if suffix=='.html':
  content=re.sub(r'<script[^>]*src="../shared/public-cms.js[^>]*></script>','<script src="holon-events.js?v=canonical-20261101"></script>',content)
  if name in ['index.html','category.html']:
   data=read('events-public');data['taxonomy']=json.loads((ROOT/'admin/data/taxonomy.json').read_text())
   packed=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
   content=content.replace('<head>','<head><script>window.ISNET_CITY_BOOTSTRAP='+packed+';</script>',1)
  meta='<meta name="holon-layout" content="canonical-ashdod-20261101"><meta property="og:image" content="https://isnet.co.il/events-preview/holon/assets/share-card.jpg">'
  content=content.replace('</head>',meta+'</head>')
  if name=='index.html':content=content.replace('</head>','<link rel="canonical" href="https://isnet.co.il/events-preview/holon/"></head>')
 # Canonical logo filenames already localized by the shared generator.
 content=content.replace('what-to-do-holon.svg','what-to-do-holon-dark.svg')
 return content.rstrip()+'\n'

def build_food(check=False):
 """The established culinary frontend, with Holon data substituted before output."""
 from sync_event_city_views import localize,TARGETS
 city=TARGETS['holon'];items=read('restaurants')['items'];cats={x['id']:x['label'] for x in read('categories')['categories']};places=[]
 mapping={'street':'local','dessert':'dessert','burger':'burger','bar':'bar','cafe':'cafe','asian':'asian','italian':'italian'}
 for x in items:
  k=mapping.get(x['subcategory'],'local');places.append(dict(id=x['id'],name=x['title'],en='',kind=k,kinds=['restaurant',k],label={'local':'אוכל ביתי ואוכל רחוב','dessert':'מאפיות וקינוחים','burger':'המבורגר ובשרים','bar':'ברים ובילוי ערב','cafe':'בתי קפה','asian':'סושי ואסייתי','italian':'איטלקי וים תיכוני'}[k],moods=['coffee','family'] if k in ['cafe','dessert'] else ['family','evening'],address=x['address'],description=x['description'],image=x['image'],credit=x['image_credit'],image_alt='תמונת המחשה — לא צילום מהמסעדה',image_role='illustration',site=x['source_url'],site_label='לפרטי המקום',booking=x.get('booking_url'),menu=x.get('menu_url'),source_url=x['source_url'],source_label='אתר המקום או מערכת ההזמנה',checked_at=read('restaurants').get('checked_at','2026-11-01')[:10],kosher='כשרות מצוינת במקור; יש לוודא תעודה עדכנית מול המקום.' if x.get('kosher') else 'יש לבדוק מול המקום.',kosherVerified=x.get('kosher') is True,saturdayVerified=x.get('saturday') is True,saturday_note='פתיחה בשבת מצוינת במקור; יש לוודא שעות לפני היציאה.' if x.get('saturday') else 'פתיחה בשבת לא אומתה.'))
 # The KG culinary renderer is the shared Ashdod design with generic venue-kind support.
 outputs={};changed=[]
 for name in ['restaurants.js','restaurants.css','restaurants.html']:
  source=(ROOT/'ashdod'/name).read_text()
  if name=='restaurants.js':source=re.sub(r'^const places=.*?;$','const places=__HOLON_OWN_PLACES__;',source,count=1,flags=re.M)
  source=source.replace('אשדוד','חולון').replace('ashdodnet.com','holonnet.co.il').replace('what-to-do-ashdod','what-to-do-holon').replace('ashdodnet-dark','holonnet-dark').replace('/ashdod/','/holon/').replace('isnet-ashdod-','isnet-holon-').replace('ASHDOD','HOLON')
  if name=='restaurants.js':source=source.replace("'sea'","'family'").replace("const kinds={all:","const kinds={dessert:'מאפיות וקינוחים',all:")
  source=source.replace('קריית גת','חולון').replace('בקרית גת','בחולון').replace('kiryat-gat','holon').replace('kgatnet.co.il','holonnet.co.il').replace('what-to-do-kgat','what-to-do-holon').replace('kgatnet-dark','holonnet-dark').replace('KIRYAT GAT','HOLON')
  if name=='restaurants.html':
   source=source.replace('אשדוד','חולון').replace('ashdodnet.com','holonnet.co.il').replace('what-to-do-ashdod','what-to-do-holon').replace('ashdodnet-dark','holonnet-dark').replace('/ashdod/','/holon/').replace('ASHDOD','HOLON')
   source=source.replace('assets/restaurants/rooftop.webp','../kiryat-gat/assets/food/cafe-illustration.jpg').replace('צילום: אתר Kira Rooftop','תמונת המחשה — לא צילום מהמסעדה')
   for old,new in [('עיר של ים.','קרוב לבית.'),('מהדגים של הנמל לקפה של הבוקר, מארוחה טובה לערב שנשארים בו עוד קצת. בואו למצוא את המקום שלכם.','מסעדות, בתי קפה ואוכל מקומי בחולון, עם מידע וקישורים למקומות.'),('ים תיכון. שולחן פתוח.','חולון. שולחן פתוח.'),('ים אחד.','עיר אחת.'),('דגים וים, מטבחים','מטבחים'),('עם הפנים לים','עם המשפחה'),('נוף, בריזה ושולחן טוב','ארוחה, קפה ושולחן טוב'),('עם נוף לים','ארוחה בעיר'),('data-mood="sea"','data-mood="family"'),('value="sea"','value="family"')]:source=source.replace(old,new)
  if name=='restaurants.html':source=source.replace('</head>','<meta name="holon-layout" content="canonical-ashdod-20261101"></head>')
  source=source.replace('__HOLON_OWN_PLACES__',json.dumps(places,ensure_ascii=False,separators=(',',':')))
  if name=='restaurants.html':
   for asset,body in outputs.items():source=re.sub(re.escape(asset)+r'(?:\?v=[^"\s]+)?',asset+'?v='+hashlib.sha256(body.encode()).hexdigest()[:12],source)
  outputs[name]=source
  if not (CITY/name).exists() or (CITY/name).read_text()!=source:
   changed.append(name)
   if not check:(CITY/name).write_text(source)
 return changed
