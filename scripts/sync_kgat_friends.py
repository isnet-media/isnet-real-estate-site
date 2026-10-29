#!/usr/bin/env python3
"""FRIENDS hall occurrences: exact local dates, reviewed aliases and scoped offers."""
import argparse,copy,hashlib,json,re
from datetime import date,datetime
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];CITY=ROOT/'events-preview/kiryat-gat'
HALL='https://friends-hist.co.il/hall/היכל-התרבות-קרית-גת-2/'
CITY_PAGE='https://friends-hist.co.il/city_cat/קרית-גת/'
IDENTITIES=[('yuval','יובל המבולבל'),('tarzan','טרזן'),('stav','סתיו בכל'),('highschool','היי סקול|טרסוב'),('cinderella','סינדרלה'),('roni','הסינור של רוני'),('couples','זוגות בזיג')]
COPY={
 'yuval':'המסע של יובל המבולבל אל הכוכב מגיע לבמה עם שירים מסיפורו המוכר והופעת אורח של שרי פופ. יובל שם טוב כתב וביים את ההצגה.',
 'tarzan':'מחזמר לילדים על המפגש של טרזן וג׳יין בג׳ונגל, עם שחקנים, רקדנים ושירים. במרכז העלילה עומדים חברות, אומץ והקשר לטבע.',
 'stav':'סתיו והרולרים מנסים להשיב את הצבעים לעולם לאחר שמכונת הצבעים נהרסת. ההצגה המוזיקלית משלבת שירי חנוכה ונכתבה ובוימה בידי אלירן חזן.',
 'highschool':'משפחת טרסוב נכנסת לאקדמיה לכוכבי רשת ומגלה שהדרך להצלחה כוללת תחרות ולחצים. מחזמר על משפחה ופופולריות, עם לירית בלבן ודניס טל.',
 'cinderella':'נעמה סופר על מככבת בעיבוד מוזיקלי לסינדרלה, לצד שמחה גואטה ומאיר תמם. המפגש עם הנסיך מציב את הפשטות מול עולם של ראווה.',
 'roni':'ספרה של רינת הופר עולה לבמה בהצגה המשלבת מוזיקה ויצירה. הכנת מתנה לאמא מובילה את רוני להרפתקה של דמיון וקשר משפחתי.',
 'couples':'סוף שבוע שדניאל מתכנן בסוד מסתבך עם אורחים לא צפויים וזהויות מתחלפות. קומדיית טעויות מאת מארק קאמולטי, בתרגום דניאל לפין ובבימוי אודי גוטשלק.'}
def norm(s):return re.sub(r'[^\w\u0590-\u05ff]','',str(s).lower()).replace('קריית','קרית')
def identity(title):return next((key for key,pattern in IDENTITIES if re.search(pattern,title)),norm(title))
def text(node):return node.get_text(' ',strip=True) if node else ''
def number(node,pattern):
 m=re.search(pattern,text(node));return float(m[1]) if m else None

def extract(html,url=HALL,today=None):
 today=today or datetime.now(ZoneInfo('Asia/Jerusalem')).date();soup=BeautifulSoup(html,'html.parser');rows=[];seen=set()
 for card in soup.select('.search_show_row'):
  title=text(card.select_one('.wrap_title h3') or card.select_one('h3'))
  a=card.select_one('a[href*="/show/"]');detail=urljoin(url,a['href']) if a else ''
  if not title or urlsplit(detail).hostname not in {'friends-hist.co.il','www.friends-hist.co.il'}:continue
  body=text(card.select_one('.tooltip-show-content'));image=card.select_one('.wrap_img a img')
  image_url=urljoin(url,image.get('data-lazy-src') or image.get('data-src') or image.get('src','')) if image else None
  if not str(image_url).startswith('https://'):image_url=None
  price=number(card.select_one('.tooptip-regular-price'),r'מחיר\s+רגיל:\s*(\d+(?:\.\d+)?)')
  member=number(card.select_one('.tooptip-discounted-price'),r'מחיר לחברי ההסתדרות:\s*(\d+(?:\.\d+)?)')
  age=re.search(r'(?:לגילאי[ם]?|גילאי[ם]?)\s*[–-]?\s*(\d+)\s*[-–]\s*(\d+)',body)
  minimum=re.search(r'(?:החל מגיל|החל מגילאי)\s*(\d+)',body)
  age_min=int(age[1]) if age else int(minimum[1]) if minimum else 2 if 'החל מגיל שנתיים' in body else None
  age_max=int(age[2]) if age else None
  minutes=re.search(r'(\d+)\s*דקות',body)
  duration=int(minutes[1]) if minutes else 90 if 'שעה וחצי' in body or re.search(r'90\s*ד[\s\'׳]',body) else 75 if 'שעה ורבע' in body else None
  card_duration=number(card.select_one('.time-new'),r'(\d+)\s*דקות')
  conflict=bool(duration and card_duration and duration!=card_duration)
  for item in card.select('.events_list .wrap_item'):
   venue=text(item.select_one('.hall-name-wrap'));when=text(item.select_one('.wrap_event'))
   if not re.search(r'קרי[יי]?ת\s+גת',venue):continue
   stamp=re.search(r'(?<!\d)(\d{2}\.\d{2}\.\d{2,4})\s+(\d{2}:\d{2})(?!\d)',when)
   if not stamp:continue
   try:day=datetime.strptime(stamp[1],'%d.%m.%Y' if len(stamp[1])==10 else '%d.%m.%y').date()
   except ValueError:continue
   if day<today:continue
   key=(identity(title),day.isoformat(),stamp[2],norm(venue))
   if key in seen:continue
   seen.add(key);button=item.select_one('[data-event_id]')
   rows.append(dict(title=title,start_date=day.isoformat(),start_time=stamp[2],venue=venue.rstrip('. '),source_url=detail,hall_url=url,source_event_id=button.get('data-event_id') if button else None,regular_price=price,member_price=member,age_min=age_min,age_max=age_max,duration_minutes=None if conflict else duration or card_duration,duration_conflict=conflict,image_candidate_url=image_url,all_ages_require_ticket='בכל גיל' in body or 'כל גיל מחויב בכרטיס' in body))
 return rows

def enrich(data,rows,checked):
 events=copy.deepcopy(data['events']);report={'new':[],'matched':[],'held':[],'duration_conflicts':[],'checked_at':checked}
 for row in rows:
  candidates=[e for e in events if e.get('start_date')==row['start_date'] and e.get('start_time')==row['start_time'] and re.search(r'קרי[יי]?ת\s*גת',str(e.get('city',''))+' '+str(e.get('venue',''))) and identity(e['title'])==identity(row['title'])]
  if len(candidates)>1:report['held'].append({'title':row['title'],'reason':'ambiguous_exact_local_occurrence'});continue
  if candidates:e=candidates[0];report['matched'].append({'event_id':e['event_id'],'source_title':row['title']})
  else:
   eid='friends_kgat_'+hashlib.sha256('|'.join(str(row.get(k,'')) for k in ['source_event_id','source_url','start_date','start_time','venue']).encode()).hexdigest()[:20]
   kind='theatre' if identity(row['title'])=='couples' else 'kids' if identity(row['title']) in COPY else 'community'
   e=dict(event_id=eid,title=row['title'],start_date=row['start_date'],start_time=row['start_time'],venue=row['venue'],city='קריית גת',category=kind,subcategory='theatre' if kind=='theatre' else 'kids-shows',audiences=['adults'] if kind=='theatre' else ['kids','families'],sources=[],status='active',is_active=True,ticket_url=row['source_url'],purchase_url=row['source_url'],ticket_status='unknown',image_publishable=False,image_verified=False)
   events.append(e);report['new'].append(eid)
  locked=set(e.get('locked_fields') or [])
  provenance={'name':'friends_kgat','url':row['source_url'],'listing_url':row['hall_url'],'source_type':'official_seller','checked_at':checked}
  e['sources']=[s for s in e.get('sources',[]) if s.get('name')!='friends_kgat']+[provenance]
  e['friends_offer']={'url':row['source_url'],'source_event_id':row['source_event_id'],'regular_price_ils':row['regular_price'],'member_price_ils':row['member_price'],'eligibility':'חברי הסתדרות זכאים בלבד; בהתאם לתנאי FRIENDS','checked_at':checked,'start_date':row['start_date'],'start_time':row['start_time'],'venue':row['venue']}
  story=COPY.get(identity(row['title'])) or row['title']+' — מופע בהיכל התרבות קריית גת. המועד וההזמנה בעמוד FRIENDS.'
  facts=[]
  if row['age_min'] is not None:facts.append('מתאים לגילאי '+str(row['age_min'])+'–'+str(row['age_max'])+'.' if row['age_max'] else 'מומלץ מגיל '+str(row['age_min'])+' ומעלה.')
  if row['duration_minutes']:facts.append('משך המופע כ־'+str(int(row['duration_minutes']))+' דקות.')
  if row['all_ages_require_ticket']:facts.append('כל גיל מחויב בכרטיס.')
  if row['regular_price'] is not None:facts.append('מחיר רגיל ב־FRIENDS: '+str(int(row['regular_price']))+' ₪.')
  if row['member_price'] is not None:facts.append('מחיר לחברי הסתדרות זכאים: '+str(int(row['member_price']))+' ₪, בכפוף לתנאי ההטבה וזמינות הכרטיסים.')
  if not e.get('description_manual_override') and not locked.intersection({'description','series_description','long_description'}):
   e['description']=story+'\n\n'+' '.join(facts);e['series_description']=e['description'];e['content_source_url']=row['source_url'];e['content_enrichment_source']='friends_kgat'
  for field in ['age_min','age_max','duration_minutes']:
   if row[field] is not None and field not in locked:e[field]=row[field]
  if row['age_min'] is not None and 'age_text' not in locked:e['age_text']=str(row['age_min'])+'–'+str(row['age_max']) if row['age_max'] else str(row['age_min'])+' ומעלה'
  if row['duration_conflict']:report['duration_conflicts'].append({'event_id':e['event_id'],'reason':'FRIENDS card duration differs from description; duration not imported'})
  if row['image_candidate_url']:
   candidates=e.setdefault('image_candidates',[]);candidate={'url':row['image_candidate_url'],'source_url':row['source_url'],'rights_status':'needs_review','source':'friends_kgat'}
   if candidate not in candidates:candidates.append(candidate)
 data=copy.deepcopy(data);data['events']=events;data['stats']={'events':len(events)}
 return data,report

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--html',type=Path);args=parser.parse_args();checked=datetime.now(ZoneInfo('UTC')).isoformat()
 if args.html:html=args.html.read_text()
 else:
  response=requests.get(HALL,timeout=25,headers={'User-Agent':'ISNET-Events/1.0 (isnet.co.il)'});response.raise_for_status()
  if urlsplit(response.url).hostname not in {'friends-hist.co.il','www.friends-hist.co.il'}:raise RuntimeError('Unexpected FRIENDS redirect')
  html=response.text
 rows=extract(html)
 if not rows:raise SystemExit('No dated local FRIENDS occurrences; existing records preserved')
 path=CITY/'data/events.json';original=json.loads(path.read_text());data,report=enrich(original,rows,checked)
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 report.update(source_url=HALL,discovered=len(rows),total_before=len(original['events']),total_after=len(data['events']),images_replaced=0)
 (ROOT/'events-preview/admin/data/kgat-friends-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 general=ROOT/'events-preview/admin/data/kgat-source-report.json';summary=json.loads(general.read_text()) if general.exists() else {'sources':{}}
 summary.setdefault('sources',{})['friends_kgat']={'status':'ok','url':HALL,'discovered':len(rows),'valid':len(rows)-len(report['held']),'new':len(report['new']),'updated':len(report['matched']),'images_collected':0,'images_candidates_only':True};summary['public_after_quality']=len(data['events']);general.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
