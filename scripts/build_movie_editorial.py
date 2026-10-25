"""Publish crawlable movie articles independently of source-owned cinema feeds."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urljoin
from xml.etree.ElementTree import Element,SubElement,tostring
import json,html,re
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];CITIES={'ashdod':'אשדוד','rishon-lezion':'ראשון לציון','yavne':'יבנה'}
BASE='https://isnet.co.il/events-preview/'
def esc(v):return html.escape(str(v or ''),quote=True)
def safe(v):return v if isinstance(v,str) and v.startswith('https://') else ''
def editorial_html(record):
 critics=record.get('critics');rating=record.get('audience_rating')
 if critics:
  criticism='<p>'+esc(critics['summary'])+'</p><p class="movieEditorialSource"><a href="'+esc(safe(critics['url']))+'" target="_blank" rel="noopener">'+esc(critics['source'])+' · למקור הביקורות</a> · נבדק '+esc(critics['checked_at'])+'</p>'
 else:criticism='<p class="movieEditorialMuted">סיכום ביקורות מאומת עדיין אינו זמין במדור.</p>'
 if rating:
  score=esc(rating['value'])+('%' if rating['scale']==100 else '/'+str(rating['scale']))
  audience='<p class="movieAudienceScore"><bdi>'+score+'</bdi><span>'+esc(rating['label'])+'</span></p><p>'+esc(rating.get('count_label',''))+'</p><p class="movieEditorialSource"><a href="'+esc(safe(rating['url']))+'" target="_blank" rel="noopener">'+esc(rating['source'])+' · לציון במקור</a> · נבדק '+esc(rating['checked_at'])+'</p>'
 else:audience='<p class="movieEditorialMuted">אין כרגע ציון קהל מאומת להצגה במדור.</p>'
 if record.get('content_type')=='screening_event':criticism='<p>זהו אירוע תוכן או שידור, ולא סרט עלילתי. ביקורות וציוני סרטים אינם מוצגים עבורו.</p>';audience='<p>לא חל על סוג האירוע הזה.</p>'
 source=next((x for x in record.get('synopsis_sources',[]) if safe(x)),None)
 note='<p class="movieEditorialSource">נוסח מקורי של מערכת מה עושים'+(' · <a href="'+esc(source)+'" target="_blank" rel="noopener">לפרטי הסרט במקור</a>' if source else '')+'</p>'
 return '<section id="movieEditorial" class="contentCard movieEditorial"><h2>ביקורות ותגובת הקהל</h2><div class="movieEditorialGrid"><section><h3>מה אומרים המבקרים?</h3>'+criticism+'</section><section><h3>מה חושב הקהל?</h3>'+audience+'</section></div><p class="movieEditorialMethod">נתוני הקהל הם תמונת מצב ממקור חיצוני, לא הצבעות באתר שלנו. אחוז אהדה מציין את שיעור המדרגים שנתנו ציון חיובי; הוא אינו ציון ממוצע מתוך 10. נתונים חסרים אינם מוצגים כאפס.</p>'+note+'</section>'
def merged(movies):
 out=dict(movies[0]);venues={}
 for m in movies:
  for v in m.get('venues',[]):
   target=venues.setdefault(v['id'],{**v,'schedule':{},'sessions':[]})
   for day,times in v.get('schedule',{}).items():target['schedule'][day]=sorted(set(target['schedule'].get(day,[])+times))
   for s in v.get('sessions',[]):
    if s not in target['sessions']:target['sessions'].append(s)
 out['venues']=list(venues.values());return out
def schedule_html(movie,day):
 out=[]
 for venue in movie['venues']:
  rows=[]
  for date,times in sorted(venue.get('schedule',{}).items()):
   if date<day or not times:continue
   links=[]
   for time in sorted(set(times)):
    urls={s.get('booking_url') for s in venue.get('sessions',[]) if s.get('date')==date and s.get('time')==time and safe(s.get('booking_url'))}
    url=next(iter(urls)) if len(urls)==1 else safe(venue.get('article_url'))
    links.append('<a class="showtime" href="'+esc(url)+'" target="_blank" rel="noopener">'+esc(time)+'</a>' if url else '<span class="showtime">'+esc(time)+'</span>')
   rows.append('<div class="dayRow"><div class="dayDate"><b>'+esc(date)+'</b></div><div class="dayTimes">'+''.join(links)+'</div></div>')
  out.append('<section class="cinemaBlock"><div class="cinemaBlock__head"><h3>'+esc(venue['name'])+'</h3></div>'+(''.join(rows) or '<p class="noSchedule">אין כרגע שעות הקרנה מאומתות. בדקו באתר בית הקולנוע.</p>')+'</section>')
 return ''.join(out)
def build():
 registry=json.loads((ROOT/'events-preview/shared/data/movie-editorial.json').read_text());aliases=registry['aliases'];records=registry['movies'];today=datetime.now(ZoneInfo('Asia/Jerusalem')).date().isoformat();urls=[];index={};report={'cities':{},'editorial_records':len(records),'audience_scores':sum(bool(r.get('audience_rating')) for r in records.values()),'critics_summaries':sum(bool(r.get('critics')) for r in records.values()),'description_words':{'min':min(len(r.get('original_text','').split()) for r in records.values()),'max':max(len(r.get('original_text','').split()) for r in records.values())}}
 for city,label in CITIES.items():
  folder=ROOT/'events-preview'/city;data=json.loads((folder/'data/cinema.json').read_text());groups={};index[city]={}
  for m in data['movies']:
   key=aliases.get(m['id'],m['id']);assert re.fullmatch(r'[a-zA-Z0-9_-]+',key),key
   groups.setdefault(key,[]).append(m)
   index[city][m['id']]=f'/events-preview/{city}/movies/{key}/'
   for alias in m.get('aliases',[]):index[city][alias]=index[city][m['id']]
  template=(folder/'movie.html').read_text();links=[]
  for key,movies in groups.items():
   movie=merged(movies);record=records.get(key) or {'original_text':movie.get('synopsis',''),'synopsis_sources':[v.get('article_url') for v in movie['venues']]};text=record.get('original_text') or movie.get('synopsis') or 'פרטי הסרט יתעדכנו לאחר אימות המקור.'
   soup=BeautifulSoup(template,'html.parser');url=BASE+city+'/movies/'+key+'/'
   base=soup.new_tag('base',href='/events-preview/'+city+'/');soup.head.insert(0,base)
   title=movie['title']+' – תקציר, ביקורות והקרנות ב'+label;soup.title.string=title+' | מה עושים'
   soup.find('meta',attrs={'name':'description'})['content']=text[:170]
   for prop,value in [('og:title',title),('og:description',text[:200]),('og:url',url),('og:type','article')]:soup.head.append(soup.new_tag('meta',attrs={'property':prop,'content':value}))
   for old in soup.select('link[rel=canonical]'):old.decompose()
   for anchor in soup.select('a[href^="#"]'):anchor['href']=url+anchor['href']
   soup.head.append(soup.new_tag('link',rel='canonical',href=url));soup.head.append(soup.new_tag('meta',attrs={'name':'robots','content':'index,follow,max-image-preview:large'}))
   soup.body['data-movie-id']=movie['id'];soup.body['data-static-movie']='true';soup.find(id='page').attrs.pop('hidden',None);soup.find(id='loadingState')['hidden']=''
   for ident,value in [('movieTitle',movie['title']),('fullSynopsis',text)]:soup.find(id=ident).string=value
   soup.find(id='cinemaSchedules').clear();soup.find(id='cinemaSchedules').append(BeautifulSoup(schedule_html(movie,today),'html.parser'))
   soup.find(id='movieEditorial').replace_with(BeautifulSoup(editorial_html(record),'html.parser'))
   poster=safe(urljoin(BASE+city+'/',movie.get('poster_url') or '')) if movie.get('poster_url') else ''
   if poster:
    image=soup.new_tag('img',src=poster,alt='כרזת הסרט '+movie['title']);image['class']=['officialPoster'];soup.find(id='heroMedia').append(image)
   tickets=soup.find(id='ticketLinks');tickets.clear();available=[]
   for v in movie['venues']:
    if safe(v.get('article_url')) and any(d>=today and times for d,times in v.get('schedule',{}).items()):
     label_venue='ב'+v['name'].replace('HOT Cinema','הוט סינמה');available.append(v)
     tickets.append(BeautifulSoup('<a href="'+esc(v['article_url'])+'" target="_blank" rel="noopener noreferrer">'+esc(label_venue)+' <span aria-hidden="true">↗</span></a>','html.parser'))
   if not available:soup.find(id='ticketAvailability').attrs.pop('hidden',None)
   trailer=movie.get('trailer_youtube_id');soup.find(id='trailerSection').attrs.pop('hidden',None)
   if trailer and re.fullmatch(r'[a-zA-Z0-9_-]{11}',trailer):
    soup.find(id='trailerAvailability').string='קדימון מקושר ממקור הסרט.'
    soup.find(id='trailerExternal')['href']='https://www.youtube.com/watch?v='+trailer
    soup.find(id='youtubeFrame')['src']='https://www.youtube-nocookie.com/embed/'+trailer+'?rel=0'
    soup.find(id='youtubeFrame')['title']='טריילר - '+movie['title']
   else:
    soup.find(id='trailerAvailability').string='טריילר רשמי לסרט זה טרם אומת.'
    soup.find(id='trailerExternal')['hidden']='';soup.find(id='youtubeFrame').parent['hidden']=''
   schema={'@context':'https://schema.org','@type':'Movie' if record.get('content_type')!='screening_event' else 'CreativeWork','@id':url+'#movie','url':url,'name':movie['title'],'description':text,'inLanguage':'he'}
   if poster:schema['image']=urljoin(BASE+city+'/',poster)
   if movie.get('runtime_minutes'):schema['duration']='PT'+str(movie['runtime_minutes'])+'M'
   if movie.get('genres'):schema['genre']=movie['genres']
   ld=soup.new_tag('script',type='application/ld+json');ld.string=json.dumps(schema,ensure_ascii=False).replace('<','\\u003c');soup.head.append(ld)
   breadcrumb={'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':i+1,'name':name,'item':item} for i,(name,item) in enumerate([('מה עושים ב'+label,BASE+city+'/'),('קולנוע ב'+label,BASE+city+'/cinema.html'),(movie['title'],url)])]}
   ld=soup.new_tag('script',type='application/ld+json');ld.string=json.dumps(breadcrumb,ensure_ascii=False).replace('<','\\u003c');soup.head.append(ld)
   dest=folder/'movies'/key/'index.html';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(str(soup)+'\n');urls.append(url)
   links.append('<li><a href="'+esc(url)+'">'+esc(movie['title'])+' – תקציר וביקורות</a></li>')
  nav='<!-- MOVIE_EDITORIAL_INDEX_START --><nav class="cinemaEditorialIndex" aria-label="דפי הסרטים"><details><summary>כל הסרטים: תקצירים, ביקורות והקרנות</summary><ul>'+''.join(links)+'</ul></details></nav><!-- MOVIE_EDITORIAL_INDEX_END -->'
  for name in ('cinema.html','index.html'):
   cinema=folder/name;content=cinema.read_text();content=re.sub(r'<!-- MOVIE_EDITORIAL_INDEX_START -->.*?<!-- MOVIE_EDITORIAL_INDEX_END -->','',content,flags=re.S);content=content.replace('</body>',nav+'</body>');cinema.write_text(content)
  report['cities'][city]={'feed_records':len(data['movies']),'pages':len(groups),'original_copy':sum(bool(records.get(k,{}).get('original_text')) for k in groups)}
 (ROOT/'events-preview/shared/data/movie-page-index.json').write_text(json.dumps(index,ensure_ascii=False,separators=(',',':'))+'\n')
 sitemap=Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
 for url in sorted(urls):SubElement(SubElement(sitemap,'url'),'loc').text=url
 (ROOT/'events-preview/movie-sitemap.xml').write_bytes(tostring(sitemap,encoding='utf-8',xml_declaration=True))
 (ROOT/'events-preview/admin/data/movie-editorial-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False));return urls
if __name__=='__main__':build()
