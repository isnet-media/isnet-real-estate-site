"""Kiryat Gat edition of the canonical events UI; data remains city-owned."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'events-preview'
def localize(content,name,city,suffix):
 content=re.sub(r'<!-- (?:ASHDOD_HOME_SEO|MOVIE_EDITORIAL_INDEX|SEARCH_DISCOVERY_META)_START -->[\s\S]*?<!-- (?:ASHDOD_HOME_SEO|MOVIE_EDITORIAL_INDEX|SEARCH_DISCOVERY_META)_END -->','',content)
 content=re.sub(r'<script\b[^>]*src="(?:ashdod-event-identities|ashdod-analytics|isnet-advertise|site-seo)\.js[^" ]*"[^>]*></script>','',content)
 content=re.sub(r'// Ashdod GA4: public event metadata only;[^\n]*\n\(function \(\) \{[\s\S]*?\n\}\)\(\);\n?','',content,count=1)
 # Canonical illustration bank is non-geographical. Never reuse another city's photos.
 content=re.sub(r'(?<![A-Za-z0-9_./-])assets/(?!branding/)', '../ashdod/assets/',content)
 content=content.replace('assets/branding/what-to-do-ashdod','assets/branding/what-to-do-kgat').replace('assets/branding/ashdodnet-dark.svg','assets/branding/kgatnet-dark.svg')
 content=content.replace('assets/branding/site-logo.png','assets/branding/what-to-do-kgat-dark.svg').replace('assets/branding/what-to-do-kgat.svg','assets/branding/what-to-do-kgat-dark.svg')
 content=content.replace('/ashdod/','/kiryat-gat/').replace(r'\/ashdod',r'\/kiryat-gat').replace('isnet-ashdod-','isnet-kiryat-gat-')
 # The preceding replacement must not relocate the shared media bank.
 content=content.replace('../kiryat-gat/assets/','../ashdod/assets/')
 content=content.replace('https://ashdodnet.com/','https://kgatnet.co.il/').replace('https://ashdodnet.com','https://kgatnet.co.il')
 content=content.replace('אשדוד נט','קריית גת נט').replace('אשדוד','קריית גת')
 content=re.sub(r'([\"\'])ashdod\1',lambda m:m[1]+'kiryat-gat'+m[1],content)
 content=content.replace('location.pathname.includes("/rishon-lezion/")?"rishon-lezion":"kiryat-gat"','"kiryat-gat"')
 if name=='index.html':
  food='<a class="isnetNavFeature isnetNavFeature--gold culinaryHomepageFeature" href="restaurants.html"><span aria-hidden="true" class="isnetNavFeature__icon">♨</span><span class="isnetNavFeature__copy"><strong>מסעדות וקולינריה</strong><small>מסעדות, בתי קפה ואוכל רחוב</small></span><span aria-hidden="true" class="isnetNavFeature__arrow">←</span></a>'
  cinema='<a class="isnetNavFeature cinemaHomepageFeature" href="cinema.html"><span aria-hidden="true" class="isnetNavFeature__icon">▣</span><span class="isnetNavFeature__copy"><strong>קולנוע בהיכל התרבות</strong><small>הסרטים וההקרנות הקרובות בהיכל</small></span><span aria-hidden="true" class="isnetNavFeature__arrow">←</span></a>'
  content=re.sub(r'<a class="isnetNavFeature isnetNavFeature--blue" href="cinema.html">[\s\S]*?</a>',lambda _:food,content,count=1)
  # The canonical page has both a menu link and a lifestyle card. Replace the card explicitly.
  content=re.sub(r'<a class="isnetNavFeature culinaryHomepageFeature"[^>]*data-ashdod-culinary[^>]*>[\s\S]*?</a>',lambda _:cinema,content,count=1)
  content=content.replace('<a href="cinema.html">קולנוע וסרטים</a>','<a href="restaurants.html">מסעדות וקולינריה</a>')
 content=re.sub(r'<a\b[^>]*data-city-only="(?:ashdod|kiryat-gat)"[^>]*>[\s\S]*?</a>','',content)
 content=re.sub(r'<a\b[^>]*data-ashdod-culinary[^>]*>[\s\S]*?</a>','',content)
 content=re.sub(r'<section class="cityDiscover"[\s\S]*?</section>','',content)
 if name=='index.html':
  nav='<nav class="kgat-discover" aria-label="מגלים את קריית גת"><a href="/meusharim/kiryat-gat/">חוגים וקורסים</a><a href="restaurants.html">מסעדות ובתי קפה</a><a href="places.html?category=parks">פארקים</a><a href="places.html?category=nature">טבע וטיולים באזור</a><a href="places.html?category=culture">מוסדות תרבות</a><a href="attractions.html">אטרקציות ומשפחה</a><a href="places.html?category=must-see">מקומות להכיר</a></nav>'
  content=content.replace('<main',nav+'<main',1)
  content=content.replace('<a class="isnetNavSmall" href="places.html?category=beaches">','<a class="isnetNavSmall" href="places.html?category=nature">').replace('<strong>חופים</strong>','<strong>טיולים בסביבה</strong>')
 if suffix=='.js':
  content=content.replace('if(e.price_min_ils==null)return "מחיר לא פורסם";', 'if(e.price_min_ils==null)return e.friends_offer?.regular_price_ils!=null?"מחיר רגיל ב־FRIENDS: "+currency.format(e.friends_offer.regular_price_ils):"מחיר לא פורסם";')
 if name=='event.js':
  content=content.replace('window.ISNET_EVENT_TOOLS?.render(e,occ);','window.ISNET_EVENT_TOOLS?.render(e,occ);window.KGAT_EVENTS?.renderOffers?.(e);')
  content=content.replace('all.find(e=>e.event_id===requestedId)','all.find(e=>e.event_id===requestedId||e.source_aliases?.some(a=>a.event_id===requestedId))')
  content=content.replace('originalAll.find(e=>e.event_id===requestedId)','originalAll.find(e=>e.event_id===requestedId||e.source_aliases?.some(a=>a.event_id===requestedId))')
 if name=='category-landing.js':
  content='\n'.join(line for line in content.split('\n') if 'window.ISNET_EXHIBITIONS.init()' not in line)
  content=content.replace('ids.has(e.category)','window.KGAT_EVENTS.matches(e,ids)')
  content=content.replace('משחקי הקבוצות בעיר, תחרויות ואירועי ספורט','משחקי בית של הקבוצות הייצוגיות, תחרויות ופעילות ספורט עממית')
  content=content.replace('const date=esc(e.start_date||"");','const date=esc(e.start_date||"")+(key==="sport"?" · "+esc(e.start_time||"השעה טרם פורסמה"):"");')
  content=content.replace('sourceImage?e.title:"תמונת המחשה"','sourceImage&&e.source_image_kind!=="illustration"?e.title:"תמונת המחשה"')
  content=content.replace("return '<a class=\"card\"", "const mediaCredit=e.source_image_kind==='illustration'?'<small class=\"imageCredit\">תמונת המחשה</small>':'';\n return '<a class=\"card\"")
  content=content.replace("'+media+'<div class=\"body\">", "'+media+mediaCredit+'<div class=\"body\">")
 if name=='category-landing.js':
  content += "\n(()=>{'use strict';if(!location.pathname.includes('/kiryat-gat/')||new URLSearchParams(location.search).get('category')!=='seniors')return;\nfetch('data/senior-guide.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('guide');return r.json()}).then(d=>{if(document.getElementById('kgSeniorSources'))return;const s=document.createElement('section');s.id='kgSeniorSources';s.style.cssText='margin:28px 0;padding:20px;border:1px solid #a28a59;border-radius:18px;background:#171e26;color:#fff';const h=document.createElement('h2');h.textContent='עוד פעילויות ומסגרות לגמלאים בעיר';s.append(h);const note=document.createElement('p');note.textContent=d.note+' נבדק ב־30.10.2026.';s.append(note);const grid=document.createElement('div');grid.style.cssText='display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,270px),1fr));gap:14px';for(const x of d.links||[]){const u=new URL(x.url);if(u.protocol!=='https:')continue;const card=document.createElement('article');card.style.cssText='padding:18px;border:1px solid #65716e;border-radius:14px;background:#202b33';const title=document.createElement('h3');title.textContent=x.title;const p=document.createElement('p');p.textContent=x.description;const a=document.createElement('a');a.textContent='פרטים והרשמה אצל המארגן ↗';a.href=u.href;a.target='_blank';a.rel='noopener';a.style.cssText='display:block;color:#f3d59c;min-height:44px;padding:8px 0';card.append(title,p,a);if(/^\\d{9,10}$/.test(x.phone||'')){const tel=document.createElement('a');tel.href='tel:'+x.phone;tel.textContent='התקשרו לבירור: '+x.phone;tel.style.cssText='display:block;min-height:44px;padding:8px 0;color:#b5efcf';card.append(tel)}grid.append(card)}s.append(grid);document.querySelector('main')?.append(s)}).catch(()=>{});\n})();\n"
 if name=='attractions.html':
  content=re.sub(r'function assignKind\(x\)\{[^\n]*\}', 'function assignKind(x){const t=x.name||"";return /קאנטרי|בריכ|שחייה/.test(t)?"water":/תרבות|מוזיאון/.test(t)?"culture":"nature"}',content,count=1)
  content=content.replace('water:"ים ושיט"','water:"בריכות ושחייה"')
  content=content.replace('ספורט ימי, חדרי בריחה, משחקים, טבע ורכיבה','בריכות, פארקים, טבע ומקומות לבילוי משפחתי')
  content=content.replace('entries=[...normalizePlaces(places),...(extra.verified_sources||[]).map(x=>({...x,local:false,area:"kiryat-gat"}))];render()', 'entries=[...new Map([...normalizePlaces(places),...(extra.verified_sources||[]).map(x=>({...x,kind:assignKind(x),local:false,area:"kiryat-gat"}))].map(x=>[x.id,x])).values()];document.querySelectorAll("[data-kind]").forEach(b=>{if(b.dataset.kind!=="all"&&!entries.some(x=>x.kind===b.dataset.kind))b.remove()});render()')
  content=content.replace('alt="\'+esc(x.name)+\'"','alt="\'+esc(x.image_alt||x.name)+\'"')
  content=content.replace('</div><div class="body"><div class="tags">','</div><div class="body">\'+(x.image_credit?\'<small class="imageCredit">\'+esc(x.image_credit)+\'</small>\':\'\')+\'<div class="tags">')
 if name in ('kids-hub.js','seniors-hub.js'):
  content=content.replace('[e.source_description,e.description,e.series_description]','[e.editorial_description,e.description,e.series_description,e.source_description]')
  content=content.replace("e.category==='seniors'||adultLecture(e)","e.category==='seniors'||e.audiences?.includes('seniors')||adultLecture(e)")
  content=re.sub(r'const explore=\[[^\n]+;',"const explore=[['הצגות ותיאטרון','במות ומופעים בעיר','category.html?category=theatre','◈'],['מוזיקה','מופעים וקונצרטים','category.html?category=music','♫'],['קולנוע','הקרנות בהיכל התרבות','cinema.html','▣'],['קהילה','מפגשים ופעילויות','category.html?category=community','✧']];",content)
 if name=='kids-hub.js':
  links=json.loads((ROOT/'kiryat-gat/data/family-guide.json').read_text())['links']
  content=re.sub(r'(function familyGuide\(\)\{\s*const sources=)\[[\s\S]*?\n \];',lambda m:m[1]+json.dumps(links,ensure_ascii=False)+';',content)
 if name=='seniors-hub.js':
  content=content.replace('בוקר של תרבות במשכן','תרבות בוקר בקריית גת').replace('סדרת החיים הטובים','מופעים ומפגשים בעיר').replace('באתר המשכן','באתר המארגן')
  content=content.replace('return e.category===\'lecture\'?\'senior-lectures\':topics[e.subcategory]?e.subcategory:\'other\';',"return e.category==='lecture'?'senior-lectures':topics[e.subcategory]?e.subcategory:({music:'senior-music',theatre:'senior-culture',cinema:'senior-culture',community:'senior-social',sport:'senior-health'}[e.category]||'other');")
 if name=='saturday.js':
  content=content.replace("cityEvents('rishon-lezion')","Promise.resolve({events:[]})")
  content=content.replace("fetch('../rishon-lezion/data/cinema.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error();return r.json()})","Promise.resolve({movies:[]})")
 if name=='site-search-chat.js':content=content.replace('/meusharim/ashdod/data/classes.json','data/classes.json').replace("if(/חוג|קורס/.test(raw)&&!payload.courses)","if(false&&/חוג|קורס/.test(raw)&&!payload.courses)")
 # Screening venue is the municipal hall, not a commercial cinema chain.
 content=content.replace('HOT Cinema','היכל התרבות').replace('סינמה סיטי','היכל התרבות')
 content=re.sub(r'<button[^>]*data-(?:cinema|venue)="(?:cinema-city|hot-cinema)"[^>]*>.*?</button>','',content)
 content=re.sub(r'<a[^>]*href="https://(?:www\.)?(?:cinema-city\.co\.il|hotcinema\.co\.il)[^"]*"[^>]*>.*?</a>','',content)
 content=content.replace('שני בתי הקולנוע','כל ההקרנות').replace('פארקים, ים, תרבות ורעיונות לבילוי משפחתי','פארקים, תרבות וטיולים למשפחה')
 content=content.replace('בחרו את שני בתי הקולנוע','הקרנות בהיכל התרבות קריית גת')
 if suffix=='.html':
  content=re.sub(r'<script defer src="/events-preview/shared/cinema-editorial.js[^"]*"></script>', '<script src="/events-preview/shared/cinema-editorial.js?v=20261029-kgat1"></script>',content)
  content=content.replace('isnet-top-navigation.js?v=20261021-nav2','isnet-top-navigation.js?v=20261029-kgat1')
  if name in ('index.html','category.html'):
   data=json.loads((ROOT/'kiryat-gat/data/events.json').read_text());data['events']=[{k:v for k,v in e.items() if k not in {'image_candidates','source_detail_text','raw_html','raw','html'}} for e in data['events']]
   data['taxonomy']=json.loads((ROOT/'admin/data/taxonomy.json').read_text())
   packed=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
   content=content.replace('<head>','<head><script>window.ISNET_CITY_BOOTSTRAP='+packed+';</script>',1)
  # City adapter executes immediately after the shared reader, before UI bundles.
  content=re.sub(r'<script[^>]*src="../shared/public-cms.js[^>]*></script>', '<script src="kgat-events.js?v=2"></script>',content)
  content=content.replace('</head>','<link rel="stylesheet" href="kgat-local.css?v=1"></head>')
 if suffix=='.js' and Path(name).name=='app.js':
  content=content.replace('fetch("category-fallbacks.json?v=20261005-21").then(r=>r.json()).catch(()=>({}))','Promise.resolve({})')
  content=content.replace('fetch("../admin/data/taxonomy.json",{cache:"no-store"}).then(r=>r.json()).catch(()=>({primary_categories:[]}))','(window.ISNET_CITY_BOOTSTRAP?Promise.resolve(window.ISNET_CITY_BOOTSTRAP.taxonomy):fetch("../admin/data/taxonomy.json").then(r=>r.json()))')
  content=content.replace('if(state.category&&e.category!==state.category)return false;','if(state.category&&!window.KGAT_EVENTS.matches(e,new Set([state.category])))return false;')
  content=content.replace('ids.has(e.category)','window.KGAT_EVENTS.matches(e,ids)')
 content=re.sub(r'(assets/branding/(?:what-to-do-kgat-dark|kgatnet-dark)\.svg)\?v=[^\"\s\']+',r'\1?v=20261029-kgat3',content)
 if suffix=='.html':
  def fingerprint(match):
   attribute,asset=match.group(1),match.group(2)
   source=ROOT/'ashdod'/asset
   if source.is_file():
    body=localize(source.read_text(),source.name,city,source.suffix)
   else:
    source=ROOT/'kiryat-gat'/asset
    if not source.is_file():return match[0]
    body=source.read_text()
   digest=hashlib.sha256(body.encode()).hexdigest()[:12]
   return attribute+'="'+asset+'?v='+digest+'"'
  content=re.sub(r'(src|href)="((?:pilot/)?[A-Za-z0-9_-]+\.(?:js|css))(?:\?v=[^"\s]*)?"',fingerprint,content)
 return content
