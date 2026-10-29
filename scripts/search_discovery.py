"""City-specific, visible search discovery, identity and cinema collections."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from xml.etree.ElementTree import Element,SubElement,tostring
from urllib.parse import urljoin
import html,json,re
from bs4 import BeautifulSoup
BASE='https://isnet.co.il/events-preview/'
EDITIONS={
 'kiryat-gat':{'name':'קריית גת','publisher':'קריית גת נט','publisher_url':'https://kgatnet.co.il/','logo':'assets/branding/what-to-do-kgat-dark.svg','publisher_logo':'assets/branding/kgatnet-dark.svg'},
 'ashdod':{'name':'אשדוד','publisher':'אשדוד נט','publisher_url':'https://ashdodnet.com/','logo':'assets/branding/what-to-do-ashdod-dark.svg','publisher_logo':'assets/branding/ashdodnet-dark.svg'},
 'rishon-lezion':{'name':'ראשון לציון','publisher':'ראשון נט','publisher_url':'https://www.rishonet.com/','logo':'assets/branding/what-to-do-rishon-dark.svg','publisher_logo':'assets/branding/rishonet-dark.svg'},
 'yavne':{'name':'יבנה','publisher':'יבנה נט','publisher_url':'https://www.yavnenet.co.il/','logo':'assets/branding/what-to-do-yavne-dark.svg','publisher_logo':'assets/branding/yavnenet-dark.svg'}}
def esc(v):return html.escape(str(v or ''),quote=True)
def ld(v):return json.dumps(v,ensure_ascii=False).replace('<','\\u003c')
def publisher(city):
 c=EDITIONS[city];return {'@type':'NewsMediaOrganization','@id':c['publisher_url']+'#organization','name':c['publisher'],'url':c['publisher_url']}
def page_schema(city,url,title,description,kind='CollectionPage'):
 c=EDITIONS[city];return {'@context':'https://schema.org','@type':kind,'@id':url+'#webpage','url':url,'name':title,'description':description,'inLanguage':'he','spatialCoverage':{'@type':'City','name':c['name'],'containedInPlace':{'@type':'Country','name':'ישראל'}},'publisher':publisher(city),'isPartOf':{'@id':BASE+city+'/#webpage'}}
def lastmod(record,data):
 candidates=[record.get('copy_updated_at'),data.get('updated_at')]
 for source in ('critics','audience_rating'):
  if record.get(source):candidates.append(record[source].get('checked_at'))
 dates=[]
 for value in candidates:
  if isinstance(value,str):
   try:dates.append(datetime.fromisoformat(value[:10]).date().isoformat())
   except ValueError:pass
 return max(dates) if dates else None

def build(root):
 from build_movie_editorial import merged
 root=Path(root);registry=json.loads((root/'events-preview/shared/data/movie-editorial.json').read_text());today=datetime.now(ZoneInfo('Asia/Jerusalem')).date().isoformat();urls=set();report={}
 for city,c in EDITIONS.items():
  folder=root/'events-preview'/city;home_url=BASE+city+'/';hub_url=home_url+'cinema/';label=c['name'];brand='מה עושים ב'+label
  data=json.loads((folder/'data/cinema.json').read_text());groups={}
  for m in data['movies']:groups.setdefault(registry['aliases'].get(m['id'],m['id']),[]).append(m)
  active=[];archive=[]
  for key,versions in groups.items():
   movie=merged(versions);record=registry['movies'].get(key,{});movie_url=home_url+'movies/'+key+'/'
   venues=[v['name'] for v in movie['venues'] if any(day>=today and times for day,times in v.get('schedule',{}).items())]
   synopsis=record.get('original_text') or movie.get('synopsis') or 'פרטי התוכן מתעדכנים לאחר אימות.'
   opening=synopsis.split('\n\n')[0]
   item='<article class="cinemaSearchCard"><h2><a href="'+esc(movie_url)+'">'+esc(movie['title'])+'</a></h2><p>'+esc(opening)+'</p><p class="cinemaSearchFacts">'+(esc(' · '.join(venues)) if venues else 'אין כרגע שעות הקרנה מאומתות בעיר')+'</p><a href="'+esc(movie_url)+'">לסיפור המלא, לביקורות ולהקרנות ב'+esc(label)+' ←</a></article>'
   (active if venues else archive).append((movie['title'],movie_url,item))
  title='סרטים וקולנוע ב'+label+' – תקצירים, ביקורות ושעות הקרנה';description='מה רואים ב'+label+'? תיאורי סרטים מקוריים ומורחבים, ביקורות, ציוני קהל, טריילרים והפניות להקרנות ולרכישת כרטיסים בבתי הקולנוע בעיר.'
  schema=page_schema(city,hub_url,title,description);schema['mainEntity']={'@type':'ItemList','numberOfItems':len(active),'itemListElement':[{'@type':'ListItem','position':i+1,'name':name,'url':url} for i,(name,url,_) in enumerate(active)]}
  crumbs={'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':brand,'item':home_url},{'@type':'ListItem','position':2,'name':'קולנוע ב'+label,'item':hub_url}]}
  meta='<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><base href="'+home_url+'"><title>'+esc(title)+' | '+esc(brand)+'</title><meta name="description" content="'+esc(description)+'"><meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"><link rel="canonical" href="'+hub_url+'"><meta property="og:type" content="website"><meta property="og:title" content="'+esc(title)+'"><meta property="og:description" content="'+esc(description)+'"><meta property="og:url" content="'+hub_url+'"><meta property="og:locale" content="he_IL"><link rel="stylesheet" href="/events-preview/ashdod/seo-pages.css?v=1"><link rel="stylesheet" href="/events-preview/shared/search-discovery.css?v=20261025"><script defer src="/assets/isnet-top-navigation.js?v=20261029-kgat1"></script><script defer src="site-share.js?v=20261019-all-pages2"></script>'
  if city=='ashdod':meta+='<script src="ashdod-analytics.js?v=20261015-ga-complete1"></script>'
  header='<header class="siteTopbar"><div class="isnetBrandGroup"><a href="'+home_url+'"><img src="'+esc(c['logo'])+'" alt="'+esc(brand)+'" width="145" height="68"></a><a href="'+esc(c['publisher_url'])+'"><small>מבית</small><img src="'+esc(c['publisher_logo'])+'" alt="'+esc(c['publisher'])+'" width="80" height="34"></a></div><a href="'+home_url+'">עמוד הבית</a></header>'
  body='<nav aria-label="מיקומכם באתר"><a href="'+home_url+'">'+esc(brand)+'</a> / קולנוע</nav><h1>'+esc(title)+'</h1><p class="lead">'+esc(description)+'</p><p>בדפי הסרטים תוכלו לקרוא מעבר לתקציר הקצר: על הדמויות והקונפליקט, על אופי הסיפור ולמי הוא עשוי להתאים. נתוני הביקורות והקהל מיוחסים למקורם ומסומנים בתאריך בדיקה.</p><a class="primary" href="'+home_url+'#cinema">לתצוגת הסרטים והמסננים ב'+esc(label)+' ←</a><h2>סרטים עם הקרנות ב'+esc(label)+'</h2><p>'+str(len(active))+' כותרים עם שעות במאגר. מועדים ומקומות עשויים להשתנות; לפני הזמנה בדקו באתר בית הקולנוע.</p><div class="cinemaSearchGrid">'+(''.join(item for _,_,item in active) or '<p>אין כרגע הקרנות מאומתות במאגר. <a href="'+home_url+'">לכל הבילויים בעיר</a></p>')+'</div>'
  if archive:body+='<section><h2>סרטים נוספים במדריך</h2><p>המידע על הסרטים זמין לקריאה גם כשעדיין אין להם שעות הקרנה מאומתות בעיר.</p><div class="cinemaSearchGrid">'+''.join(item for _,_,item in archive)+'</div></section>'
  body+='<nav aria-label="מדריכי הערים">'+''.join('<a href="'+BASE+other+'/cinema/">קולנוע ב'+esc(info['name'])+'</a> ' for other,info in EDITIONS.items() if other!=city)+'</nav>'
  dest=folder/'cinema/index.html';dest.parent.mkdir(exist_ok=True);dest.write_text('<!doctype html><html lang="he" dir="rtl"><head>'+meta+'<script type="application/ld+json">'+ld([schema,crumbs])+'</script></head><body>'+header+'<main>'+body+'</main><footer><a href="'+home_url+'">'+esc(brand)+'</a> · מבית <a href="'+esc(c['publisher_url'])+'">'+esc(c['publisher'])+'</a></footer></body></html>')
  urls.add(hub_url)
  # Metadata and a visible crawl path to every topic, in the correct city edition.
  home=folder/'index.html';raw=home.read_text();raw=re.sub(r'<!-- SEARCH_DISCOVERY_META_START -->.*?<!-- SEARCH_DISCOVERY_META_END -->','',raw,flags=re.S)
  soup=BeautifulSoup(raw,'html.parser')
  for tag in soup.select('link[rel=canonical]'):tag.decompose()
  desc='מה עושים ב'+label+'? אירועים קרובים, הופעות, סרטים, פעילויות לילדים ולגמלאים ומקומות בילוי בעיר, מבית '+c['publisher']+'.'
  head_schema=page_schema(city,home_url,brand,desc);head_schema.pop('isPartOf',None)
  for tag in soup.select('meta[property="og:title"],meta[property="og:description"],meta[property="og:url"],meta[property="og:locale"]'):tag.decompose()
  # Add only this city's verified metadata; preserve independent homepage content.
  snippet='<!-- SEARCH_DISCOVERY_META_START --><meta property="og:title" content="'+esc(brand)+'"><meta property="og:description" content="'+esc(desc)+'"><meta property="og:url" content="'+home_url+'"><link rel="stylesheet" href="/events-preview/shared/search-discovery.css?v=20261025"><link rel="canonical" href="'+home_url+'"><meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"><meta property="og:locale" content="he_IL"><script id="discoveryPageSchema" type="application/ld+json">'+ld(head_schema)+'</script><!-- SEARCH_DISCOVERY_META_END -->'
  for name,value in [('description',desc)]:
   tag=soup.find('meta',attrs={'name':name})
   if tag:tag['content']=value
  if city!='ashdod':soup.title.string=brand+' – אירועים, סרטים ובילויים | '+c['publisher']
  raw=str(soup).replace('</head>',snippet+'</head>')
  manifest_file=folder/'data/seo-index.json';manifest=json.loads(manifest_file.read_text()) if manifest_file.exists() else {}
  entries=[(hub_url,'סרטים וקולנוע ב'+label)]+[(item['url'],item['title']) for item in manifest.get('pages',{}).values()]
  navigation='<!-- SEARCH_DISCOVERY_LINKS_START --><nav class="cinemaEditorialIndex searchDiscoveryLinks" aria-label="מדריכי בילוי ב'+esc(label)+'"><h2>מדריכי בילוי ב'+esc(label)+'</h2>'+''.join('<a href="'+esc(url)+'">'+esc(name)+'</a> ' for url,name in entries)+'</nav><!-- SEARCH_DISCOVERY_LINKS_END -->'
  raw=re.sub(r'<!-- SEARCH_DISCOVERY_LINKS_START -->.*?<!-- SEARCH_DISCOVERY_LINKS_END -->','',raw,flags=re.S);home.write_text(raw.replace('</body>',navigation+'</body>'))
  if city!='ashdod':
   for entry in ('event.html','category.html'):
    path=folder/entry;content=path.read_text();tag='<script src="/events-preview/shared/search-metadata.js?v=20261025"></script>'
    if '/shared/search-metadata.js' not in content:path.write_text(content.replace('</head>',tag+'</head>'))
  report[city]={'city':label,'publisher':c['publisher'],'home':home_url,'cinema':hub_url,'movies':len(groups),'active_movies':len(active),'indexable_event_pages':len(manifest.get('events',{}))}
 index=Element('sitemapindex',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
 for path in ('sitemap.xml','movie-sitemap.xml','discovery-sitemap.xml'):SubElement(SubElement(index,'sitemap'),'loc').text=BASE+path
 (root/'events-preview/sitemap-index.xml').write_bytes(tostring(index,encoding='utf-8',xml_declaration=True))
 sm=Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
 for url in sorted(urls):SubElement(SubElement(sm,'url'),'loc').text=url
 (root/'events-preview/discovery-sitemap.xml').write_bytes(tostring(sm,encoding='utf-8',xml_declaration=True))
 (root/'events-preview/admin/data/search-discovery-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 return urls
