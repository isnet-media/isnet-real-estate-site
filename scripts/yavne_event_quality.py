"""City-specific factual classification; never invent showtimes or places."""
import re
from collections import defaultdict
import sync_events_from_sources as core
EXCLUDE=re.compile(r'הדרכת הורים|הדרכה בשימושי|מיומנויות|לימודי חשיבה|פעילות בתנועה|קבוצה [אב][\'׳]? שעה|מועדון יולדות|קבוצת הורים|סקוושי|פיינט דייט')
def refine(events):
 kept=[];held=[]
 for e in events:
  title=e['title'];text=e.get('source_detail_text') or '';head=text.split('פרטים נוספים')[0]
  if EXCLUDE.search(title) or 'גן יבנה' in title+' '+(e.get('venue') or ''):held.append(e);continue
  e['venue']=re.sub(r'\s+ל$','',e.get('venue') or '')
  e['venue']=re.sub(r',?\s*יבנה$','',e['venue']).strip() if 'היכל התרבות' not in e['venue'] and 'סינמטק' not in e['venue'] else e['venue']
  e['venue']=re.sub(r'\s+מפה$','',e['venue'])
  if e['venue'] in {'הדוגית 6','הדוגית 6, יבנה'}:e['venue']='סינמטק יבנה, הדוגית 6'
  if 'סינמטק יבנה' in head:e['venue']='סינמטק יבנה, הדוגית 6'
  elif 'היכל התרבות יבנה' in head:e['venue']='היכל התרבות יבנה'
  host=core.urlsplit(e.get('detail_source_url') or e.get('ticket_url') or '').hostname or ''
  meta=head.split('דף הבית',1)[-1] if host in {'www.htyavne.co.il','htyavne.co.il','yavne-matnasim.smarticket.co.il'} else ''
  if 'תקציר הסרט' in text or ('במאי/ת' in text and 'סינמטק' in head):e['category']='cinema'
  elif re.search(r'סטנד\s?אפ|סטנד אפ',meta) or any(x in title for x in ['נוסבאום','גיורא זינגר','אסף יצחקי','אלי פיניש','דניאל חן','אורי ברויר','נגה ד','בן בן ברוך','שלום אסייג','עידן אלתרמן','אלי יצפאן']):e['category']='standup'
  elif 'ילדים' in meta or any(x in title for x in ['פליימוביל','חיות וחיוכים','אבן האושר','פינוקיו','רחוב חנוכה','מאחורי כל שיר','סיפור הנס']):e['category']='kids'
  elif 'תאטרון' in meta or 'תיאטרון' in meta or title=='דרושה עוזרת':e['category']='theatre'
  elif 'מחול' in meta:e['category']='music';e['subcategory']='dance'
  elif 'מוזיקה' in meta or 'KING OF POP' in title or 'גל דה פז' in title or 'ויוולדי' in title:e['category']='music'
  elif 'בוקר של תרבות' in title or 'הרצאת' in title or 'לפנסיונרים' in title:e['category']='lecture'
  elif 'מרוץ יבנה' in title:e['category']='sport'
  elif 'ריקודי עם' in title or 'מועדון קריאה' in title or 'מועדון פתוח' in title or 'אימהות מיוחדות' in title:e['category']='community'
  if 'כניסה חופשית' in head:e['is_free']=True;e['price_min_ils']=0
  if 'גמלא' in text or 'לפנסיונרים' in title or 'בוקר של תרבות' in title:e['audiences']=sorted(set(e.get('audiences',[])+['seniors']))
  kind={'music':'מופע מוזיקה','kids':'אירוע לילדים ולמשפחות','standup':'מופע סטנדאפ','theatre':'הצגת תיאטרון','lecture':'הרצאה','community':'אירוע קהילתי','cinema':'הקרנת סרט','sport':'אירוע ספורט'}.get(e['category'],'אירוע')
  if 'פרטי ההשתתפות והזמנת הכרטיסים בעמוד האירוע של המארגן.' in (e.get('description') or ''):
   e['description']=f"{title} — {kind} ב{e['venue']}. המפגש יתקיים ב־{e['start_date']} בשעה {e['start_time']}. פרטי ההשתתפות והזמנת הכרטיסים בעמוד האירוע של המארגן."
  purchase=e.get('purchase_url') or ''
  if purchase and re.search(r'https?://[^/]+/.*(?:\.co\.il|\.com)',purchase):
   detail=e.get('detail_source_url') or e.get('ticket_url') or ''
   if core.urlsplit(detail).hostname in {'www.htyavne.co.il','htyavne.co.il','yavne-matnasim.smarticket.co.il'}:e['purchase_url']=detail
  kept.append(e)
 # Only coalesce same-time, same-venue records with a shared exact title prefix
 # or substantial shared title evidence. Prefer official facts and keep aliases.
 def priority(e):return not any(s.get('source_type')=='official' for s in e.get('sources',[]))
 output=[]
 for e in sorted(kept,key=priority):
  match=None
  for old in output:
   if (old.get('start_date'),old.get('start_time'),old.get('venue'))!=(e.get('start_date'),e.get('start_time'),e.get('venue')):continue
   a=core.text_norm(old['title']);b=core.text_norm(e['title'])
   prefix=lambda x:core.text_norm(re.split(r'[-–|]',x)[0])
   if a==b or (min(len(a),len(b))>=7 and (a in b or b in a)) or (len(prefix(old['title']))>=5 and prefix(old['title'])==prefix(e['title'])) or (core.overlap_score(a,b)>=.55 and len(set(a.split())&set(b.split()))>=3):match=old;break
  if match:
   alias={'event_id':e['event_id'],'title':e['title'],'url':e.get('ticket_url')}
   if alias not in match.setdefault('source_aliases',[]):match['source_aliases'].append(alias)
  else:output.append(e)
 return sorted(output,key=lambda e:(e['start_date'],e['start_time'],e['title'])),held
