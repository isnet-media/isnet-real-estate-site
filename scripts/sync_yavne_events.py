#!/usr/bin/env python3
"""Daily Yavne edition intake, using the shared occurrence merge and detail reader."""
import json,re
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
import sync_events_from_sources as core
SOURCES=[
 {"name":"friends_yavne","url":"https://friends-hist.co.il/hall/היכל-התרבות-יבנה/","parser":"generic","venue":"יבנה","source_type":"secondary"},
 {"name":"easy_yavne","url":"https://easy.co.il/list/Events?region=883","parser":"generic","venue":"יבנה","source_type":"secondary"},
 {"name":"makore_yavne","url":"https://www.makore.co.il/browse/city/יבנה","parser":"generic","venue":"יבנה","source_type":"secondary"},
 {"name":"mevalim_yavne","url":"https://www.mevalim.co.il/yavne/","parser":"mevalim","venue":"יבנה","source_type":"secondary"},
 {"name":"tickchak_yavne","url":"https://live.tickchak.co.il/yavne","parser":"generic","venue":"יבנה","source_type":"secondary"},
 {'name':'yavne_municipality','url':'https://www.yavne.muni.il/events/','parser':'yavne_community','venue':'יבנה','source_type':'official'},
 {'name':'htyavne','url':'https://www.htyavne.co.il/','parser':'smarticket','venue':'היכל התרבות יבנה','source_type':'official'},
 {'name':'yavne_community','url':'https://www.matnasyavne.co.il/events/','parser':'yavne_community','venue':'יבנה','source_type':'official'},
]
def community_rows(soup,source):
 rows=[]
 for a in soup.select('a[href]'):
  text=a.get_text(' ',strip=True)
  m=re.search(r'(?:יום\s+[א-ת]+,?\s*)?(\d{1,2}[./]\d{1,2}[./]\d{4})\s+(\d{1,2}:\d{2})',text)
  if not m or 'פרטים נוספים' not in text:continue
  title=re.sub(r'יום\s+[א-ת]+,?\s*$','',text[:m.start()]).strip()
  if not core.valid_title(title):continue
  url=core.safe_url(a.get('href'),source['url'],allow_external=True)
  if not url or url==source['url'] or '/login' in url:continue
  if core.urlsplit(url).hostname not in {'www.htyavne.co.il','htyavne.co.il','yavne-matnasim.smarticket.co.il','www.yavne.muni.il','www.matnasyavne.co.il','www.migdal-or.co.il'}:continue
  day=core.iso_dmy(core.DAY_DOT.fullmatch(m[1]))
  venue=text[m.end():].split('פרטים נוספים')[0].strip() or 'יבנה'
  row={'title':title,'start_date':day,'start_time':m[2],'venue':venue,'ticket_url':url,'purchase_url':url,'quality_flags':['automated_official_listing']}
  row.update(core.image_candidate_from_node(a,source));rows.append(row)
 from yavne_event_quality import EXCLUDE
 return [r for r in rows if not EXCLUDE.search(r['title'])]
original_fetch=core.fetch_once
page_cache={}
def cached_fetch(source):
 url=source['url']
 if url not in page_cache:page_cache[url]=original_fetch(source)
 result,error=page_cache[url]
 # Parsers may remove script nodes; each caller receives its own tree.
 return (BeautifulSoup(str(result),'html.parser') if result else None),error
original_rows=core.source_rows
def source_rows(soup,source):
 if source['parser']=='yavne_community':return community_rows(soup,source)
 if source['parser']=='mevalim':
  from sync_mevalim_ashdod_direct import MAP
  rows=[]
  for node in soup.select('[data-mvlm-event-date]'):
   try:dt=datetime.strptime(node.get('data-mvlm-event-date'),'%d.%m.%y %H:%M')
   except (TypeError,ValueError):continue
   venue=node.select_one('.rgbcode_table_shortcode_table_venue')
   venue=venue.get_text(' ',strip=True) if venue else ''
   if 'יבנה' not in venue or 'גן יבנה' in venue:continue
   title=node.get('data-mvlm-event-name') or ''
   link=node.get('data-mvlm-event-link-target') or ''
   if not title or not link.startswith('https://'):continue
   row={'title':title,'start_date':dt.date().isoformat(),'start_time':dt.strftime('%H:%M'),'venue':venue,'ticket_url':link,'purchase_url':link,'category':MAP.get(node.get('data-mvlm-event-category'),('other',''))[0],'quality_flags':['automated_city_board']}
   row.update(core.image_candidate_from_node(node,source));rows.append(row)
  return rows
 return [r for r in original_rows(soup,source) if 'גן יבנה' not in (r.get('venue','')+' '+r.get('title','')) and ('יבנה' in r.get('venue','') or source['name']=='htyavne')]
def main():
 core.CITY_LABELS['yavne']='יבנה';core.source_rows=source_rows;core.fetch_once=cached_fetch
 report=core.merge('yavne',sorted(SOURCES,key=lambda s:s['source_type']!='official'),False)
 path=core.BASE/'yavne/data/events.json';data=json.loads(path.read_text())
 labels={'music':'מופע מוזיקה','kids':'הצגה לילדים ולמשפחות','standup':'מופע סטנדאפ','theatre':'הצגת תיאטרון','lecture':'הרצאה','community':'מפגש קהילתי','cinema':'הקרנה','seniors':'מפגש תרבות'}
 for e in data['events']:
  original_venue=e.get('venue') or ''
  if e.get('category')=='other':e['category']=core.choose_category(e['title'],original_venue)
  if 'סינמטק יבנה' in original_venue:e['venue']='סינמטק יבנה, הדוגית 6'
  elif 'היכל התרבות יבנה' in original_venue:e['venue']='היכל התרבות יבנה'
  text=e.get('source_detail_text') or ''
  price=re.search(r'מחיר\s+(\d+(?:\.\d+)?)\s*(?:עד\s+(\d+(?:\.\d+)?))?\s*₪',text)
  if price and e.get('price_min_ils') is None:
   e['price_min_ils']=float(price[1]);e['price_max_ils']=float(price[2]) if price[2] else float(price[1])
  detail=e.get('detail_source_url') or e.get('ticket_url') or ''
  host=core.urlsplit(detail).hostname or ''
  if e.get('image_url') and not any(x in e['image_url'].lower() for x in ['logo','placeholder','no-image']):
   page,_=page_cache.get(detail,(None,None))
   if page is None and not e.get('image_verified') and host in {'www.htyavne.co.il','htyavne.co.il','yavne-matnasim.smarticket.co.il'}:page,_=cached_fetch({'url':detail})
   title=page.select_one('h1') if page else None
   if title and core.text_norm(e['title']) in core.text_norm(title.get_text(' ',strip=True)) and host in {'www.htyavne.co.il','htyavne.co.il','yavne-matnasim.smarticket.co.il'}:
    e.update(image_verified=True,image_publishable=True,image_represents_event=True,image_credit='תמונת האירוע: '+('היכל התרבות יבנה' if 'htyavne' in host else 'רשת המרכזים הקהילתיים יבנה'),image_rights_status='official_promotional_event',source_image_kind='official_event')
  # Preserve manual/editorial copy. Write only a factual original launch summary.
  if not e.get('description'):
   kind=labels.get(e.get('category'),'אירוע');e['description']=f"{e['title']} — {kind} ב{e['venue']}. המפגש יתקיים ב־{e['start_date']} בשעה {e['start_time']}. פרטי ההשתתפות והזמנת הכרטיסים בעמוד האירוע של המארגן."
  if 'בוקר של תרבות' in e['title']:e['audiences']=sorted(set(e.get('audiences',[])+['adults','seniors']));e['category']='lecture'
  if 'סטנדאפ' in e['title'] or 'סטנד אפ' in e['title']:e['category']='standup'
  # A hall name containing cinematheque is not evidence of a film screening.
  if e['category']=='cinema' and any(x in e['title'] for x in ['סטנד','זינגר','נוסבאום','אלתרמן','פיניש']):e['category']='standup'
 from yavne_event_quality import refine
 data['events'],held=refine(data['events'])
 (core.BASE/'admin/data/yavne-non-event-review.json').write_text(json.dumps({'reason':'Classes, skills groups and individual guidance excluded from events board','events':held},ensure_ascii=False,indent=2))
 report['public_after_quality']=len(data['events']);report['excluded_non_events']=len(held)
 films={}
 summaries={'מפרץ ההרפתקאות':'יחידת החילוץ יוצאת להרפתקה באי דינוזאורים, שם היא נדרשת להתמודד עם סכנת התפרצות הר געש. הקרנה בסינמטק יבנה.','בלב הפרא':'קצין כוחות מיוחדים וכלבו שורדים התרסקות מטוס באלסקה ונאבקים לחזור הביתה. בראד פיט מככב בסרטו של דיוויד אייר.'}
 for e in data['events']:
  if e['category']!='cinema':continue
  movie=films.setdefault(e['title'],{'id':'yavne-film-'+core.hashlib.sha256(e['title'].encode()).hexdigest()[:12],'title':e['title'],'synopsis':summaries.get(e['title'],e['description']),'poster_url':e.get('image_url') if e.get('image_publishable') else None,'is_family':e['title']=='מפרץ ההרפתקאות','venues':[{'id':'cinematheque','name':'סינמטק יבנה','article_url':e.get('purchase_url') or e['ticket_url'],'schedule':{},'sessions':[]}]})
  venue=movie['venues'][0];venue['schedule'].setdefault(e['start_date'],[]).append(e['start_time']);venue['sessions'].append({'date':e['start_date'],'time':e['start_time'],'booking_url':e.get('purchase_url') or e['ticket_url']})
 (core.BASE/'yavne/data/cinema.json').write_text(json.dumps({'city':'יבנה','source_name':'סינמטק יבנה — מועדים מהיכל התרבות','movies':list(films.values())},ensure_ascii=False,indent=2))
 data['stats']={'events':len(data['events'])};path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 (core.BASE/'admin/data/yavne-source-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(report,ensure_ascii=False))
 if not data['events']:raise SystemExit('No verified Yavne events; refusing an empty launch')
 if not any(s['status']=='ok' for s in report['sources'].values()):raise SystemExit('All Yavne sources failed; existing data preserved')
if __name__=='__main__':main()
