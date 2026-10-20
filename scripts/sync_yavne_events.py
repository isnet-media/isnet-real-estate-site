#!/usr/bin/env python3
"""Daily Yavne edition intake, using the shared occurrence merge and detail reader."""
import json,re
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
import sync_events_from_sources as core
SOURCES=[
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
 return rows
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
 return original_rows(soup,source)
def main():
 core.CITY_LABELS['yavne']='יבנה';core.source_rows=source_rows
 report=core.merge('yavne',SOURCES,False)
 path=core.BASE/'yavne/data/events.json';data=json.loads(path.read_text())
 labels={'music':'מופע מוזיקה','kids':'הצגה לילדים ולמשפחות','standup':'מופע סטנדאפ','theatre':'הצגת תיאטרון','lecture':'הרצאה','community':'מפגש קהילתי','cinema':'הקרנה','seniors':'מפגש תרבות'}
 for e in data['events']:
  # Preserve manual/editorial copy. Write only a factual original launch summary.
  if not e.get('description'):
   kind=labels.get(e.get('category'),'אירוע');e['description']=f"{e['title']} — {kind} ב{e['venue']}. המפגש יתקיים ב־{e['start_date']} בשעה {e['start_time']}. פרטי ההשתתפות והזמנת הכרטיסים בעמוד האירוע של המארגן."
  if 'בוקר של תרבות' in e['title']:e['audiences']=sorted(set(e.get('audiences',[])+['adults','seniors']));e['category']='lecture'
  if 'סטנדאפ' in e['title'] or 'סטנד אפ' in e['title']:e['category']='standup'
  # A hall name containing cinematheque is not evidence of a film screening.
  if e['category']=='cinema' and any(x in e['title'] for x in ['סטנד','זינגר','נוסבאום','אלתרמן','פיניש']):e['category']='standup'
 data['stats']={'events':len(data['events'])};path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 (core.BASE/'admin/data/yavne-source-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(report,ensure_ascii=False))
 if not data['events']:raise SystemExit('No verified Yavne events; refusing an empty launch')
 if not any(s['status']=='ok' for s in report['sources'].values()):raise SystemExit('All Yavne sources failed; existing data preserved')
if __name__=='__main__':main()
