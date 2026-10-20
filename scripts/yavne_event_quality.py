"""City-specific factual classification; never invent showtimes or places."""
import re
from collections import defaultdict
import sync_events_from_sources as core
EXCLUDE=re.compile(r'הדרכת הורים|הדרכה בשימושי|מיומנויות|לימודי חשיבה|פעילות בתנועה|קבוצה [אב][\'׳]? שעה|מועדון יולדות|קבוצת הורים|סקוושי|פיינט דייט')
def refine(events):
 kept=[];held=[]
 for e in events:
  title=e['title'];text=(e.get('source_detail_text') or '').split('רוצים עוד אירועים')[0];head=text.split('פרטים נוספים')[0]
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
  classify(e)
  # Reject unrelated ticket links scraped from a seller's surrounding page.
  detail=e.get('detail_source_url') or e.get('ticket_url') or ''
  purchase=e.get('purchase_url') or ''
  if ('ticket.gozalypro.com/112317' in purchase and 'סיפור הנס' not in title) or ('makore.co.il/event/' in purchase and purchase!=detail):
   e['purchase_url']=detail;e['purchase_source']='event_detail_fallback'
  kept.append(e)
 # Only coalesce same-time, same-venue records with a shared exact title prefix
 # or substantial shared title evidence. Prefer official facts and keep aliases.
 def priority(e):return not any(s.get('source_type')=='official' for s in e.get('sources',[]))
 output=[]
 for e in sorted(kept,key=priority):
  match=None
  for old in output:
   if (old.get('start_date'),old.get('start_time'))!=(e.get('start_date'),e.get('start_time')):continue
   # Reviewed aliases whose secondary seller supplied the wrong venue/name.
   known=next((name for name in ['אלי פיניש','סיפור הנס','דניאל סטיופין'] if name in old['title'] and name in e['title']),None)
   if old.get('venue')!=e.get('venue') and not known:continue
   a=core.text_norm(old['title']);b=core.text_norm(e['title'])
   prefix=lambda x:core.text_norm(re.split(r'[-–|]',x)[0])
   if known or a==b or (min(len(a),len(b))>=7 and (a in b or b in a)) or (len(prefix(old['title']))>=5 and prefix(old['title'])==prefix(e['title'])) or (core.overlap_score(a,b)>=.55 and len(set(a.split())&set(b.split()))>=3):match=old;break
  if match:
   alias={'event_id':e['event_id'],'title':e['title'],'url':e.get('ticket_url')}
   if alias not in match.setdefault('source_aliases',[]):match['source_aliases'].append(alias)
   for source in e.get('sources',[]):
    if source not in match.setdefault('sources',[]):match['sources'].append(source)
   if not match.get('image_publishable') and e.get('image_publishable'):
    for key in ['image_url','image_source','image_credit','image_verified','image_publishable','image_represents_event','source_image_kind','image_origin_url','thumbnail_url','thumbnail_ready']:match[key]=e.get(key)
  else:output.append(e)
 return sorted(output,key=lambda e:(e['start_date'],e['start_time'],e['title'])),held


def classify(e):
 """Specific local evidence; audience tags supplement, never duplicate occurrences."""
 t=e['title'];cat=e['category']
 # Ignore third-party related-event footers when using source copy as evidence.
 text=(e.get('source_detail_text') or '').split('רוצים עוד אירועים')[0]
 if t=='בלב הפרא':cat='cinema'
 if t=='מסביב לעולם' or 'סיגי הסופגנייה' in t:cat='kids'
 e['category']=cat
 audience=set(e.get('audiences') or [])
 if cat=='kids':audience.update(['kids','families'])
 if t=='מפרץ ההרפתקאות':audience.update(['kids','families'])
 if 'מועדון פתוח' in t and 'נוער' in (e.get('venue') or ''):audience.add('youth')
 e['audiences']=sorted(audience)
 sub=e.get('subcategory')
 if cat=='kids':
  sub='kids-theatre'
  if 'חיות וחיוכים' in t:sub='family-activity'
  if any(x in t for x in ['אבן האושר','פינוקיו (','רחוב חנוכה','מאחורי כל שיר']):sub='story-time'
 elif cat=='lecture':
  sub='general-enrichment'
  for pattern,value in [(r'אוטיזם|מוח|שעון הגיל|סוגי הזיכרון','health-medicine'),(r'קהלת|רמב','judaism-spirit'),(r'מפלגות|תושבי חוץ|מזרח תיכון','current-affairs'),(r'גואטמלה','travel-geography'),(r'אוסטרו','history'),(r'ילדים בהזמנה','parenting-family'),(r'השעה הארוכה','psychology-growth')]:
   if re.search(pattern,t):sub=value;break
 elif cat=='music':
  sub='artists-bands'
  if 'מחול' in t or 'מיומנה' in t:sub='dance-performance'
  elif any(x in t for x in ['ויוולדי','אופרה']):sub='concerts'
  elif any(x in t for x in ['קליף','KING OF POP','שושנה','שרים יהונתן']):sub='tribute-shows'
  elif 'יוונית' in t:sub='world-music'
 elif cat=='standup':sub='entertainment-show' if any(x in t for x in ['יצפאן','מיקי כאן']) else 'standup'
 elif cat=='theatre':
  sub='theatre'
  if any(x in t for x in ['קומדיה','הזוג המוזר','שקרים קטנים','דרושה עוזרת','לנקות את הראש']):sub='comedy'
 elif cat=='community':
  sub='community-meeting'
  if 'מועדון קריאה' in t:sub='reading-clubs'
  elif 'ריקודי עם' in t:sub='folk-dancing'
  elif 'אימהות' in t:sub='women-events'
 e['subcategory']=sub
 # Category-scoped memberships, preserving the original single primary label.
 memberships=[{'category':cat,'subcategory':sub}]
 if 'seniors' in audience and cat!='seniors':
  senior='senior-health' if sub=='health-medicine' else {'lecture':'senior-lectures','music':'senior-music','community':'senior-social','theatre':'senior-culture'}.get(cat,'seniors-activities')
  memberships.append({'category':'seniors','subcategory':senior})
  if cat=='lecture' and senior!='senior-lectures':memberships.append({'category':'seniors','subcategory':'senior-lectures'})
 if cat=='cinema' and 'kids' in audience:memberships.append({'category':'kids','subcategory':'family-activity'})
 if cat=='kids' and sub=='kids-theatre':memberships.append({'category':'theatre','subcategory':'theatre'})
 if 'DNA' in t:memberships.append({'category':'music','subcategory':'dance-performance'})
 if sub=='folk-dancing':memberships.append({'category':'music','subcategory':'dance'})
 e['category_memberships']=memberships
