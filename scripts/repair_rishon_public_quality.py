#!/usr/bin/env python3
"""Source-verified corrections for Rishon's public board and daily refreshes."""
import re
from collections import defaultdict, Counter
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
# Equivalent names observed at the same venue and occurrence; never fuzzy-match
# unrelated productions or merge separate performance times.
ALIASES={
 'נישואים גרעיניים - קומדיה זוגית פרועה':'נישואים גרעיניים',
 'מחזמר מצחיקונת - Funny Girl':'מצחיקונת','מצחיקונת המחזמר - Funny Girl':'מצחיקונת',
 'עפרה - המחזמר על עופרה חזה':'עפרה','אהבה בהפתעה - התיאטרון העברי':'אהבה בהפתעה',
 'הרצאה – סוד המוח הצעיר':'סוד המוח הצעיר','סוד המוח הצעיר: הרצאה חווייתית הכוללת משחקי חשיבה וחידות היגיון':'סוד המוח הצעיר',
 'גיל שוחט מארח את שלמה בראבא מס\' 1':'גיל שוחט מארח את שלמה בראבא',
 'אף מילה לאמא - תיאטרון בית ליסין':'אף מילה לאמא','עידן ניידיץ – סטנדאפ':'עידן ניידיץ',
 'מחסן השטוזים של דתיה - תיאטרון אורנה פורת':'מחסן השטוזים של דתיה',
 'שקרים קטנים - קומדיה משפחתית מופרעת':'שקרים קטנים',
 'טינטן - תיאטרון אורנה פורת':'טינטן','טינטן - תיאטרון אורנה פורת לילדים ולנוער':'טינטן',
 'אוי אלוהים - תיאטרון הבימה':'אוי אלוהים','מיקה שלי - מחזמר משיריו של יאיר רוזנבלום':'מיקה שלי',
 'שושנה - המחזמר בכיכובה של גל דה פז':'שושנה מחזמר','שושנה-מחזמר':'שושנה מחזמר','שושנה- מחזמר':'שושנה מחזמר',
 'זוג משמיים - התיאטרון העברי':'זוג משמיים','זוגיות AI - התיאטרון העברי':'זוגיות AI',
 'גיא ויעל – בוא לא נדבר על זה':'בוא לא נדבר על זה',
 'שומרי הדרקונים - מחזמר הרפתקאות - חנוכה 2026':'שומרי הדרקונים',
 'לילות ספרד - המחזמר':'לילות ספרד','לילות ספרד - מחזמר':'לילות ספרד',
 'היומן - המחזמר עטור השבחים מברודוויי':'היומן',
 'אסף יצחקי – מופע סטנדאפ לא מצונזר':'אסף יצחקי','ליטל שוורץ – במופע סטנדאפ':'ליטל שוורץ',
 'שלומי קוריאט במופע סטנדאפ':'שלומי קוריאט',
 'באמבע מעשיות "Bombe Mayses"':'בארבע מעשיות',
}
MUSEUM='https://yama.smarticket.co.il/'
# Original editorial summaries based on the official detail pages checked 16 Oct.
PROGRAMS=[
 ('שיח גלריה | יניב שפירא | אגם וקדישמן','lecture','lecture',MUSEUM+'שיח_גלריה_|_יניב_שפירא_|_אגם_וקדישמן','האוצר יניב שפירא נפגש עם הקהל במוזיאון אגם לשיחה על התערוכה המשותפת ליעקב אגם ולמנשה קדישמן. המפגש מיועד למתעניינים באמנות ישראלית ומציע מבט על הקשר בין שתי דרכי יצירה שונות ועל הרעיונות המחברים ביניהן.'),
 ('בחירות 2026 - כניסה','exhibition','exhibition',MUSEUM+'בחירות_2026_-_כניסה','מוזיאון אגם מציע בילוי באמנות ביום הבחירות, עם היכרות עם יצירתו הקינטית של יעקב אגם וביקור בתערוכה המפגישה בינו לבין מנשה קדישמן. באותו יום מוצעים גם סיורים לקהל הרחב ולמשפחות וסדנאות לילדים; יש לבחור את הכרטיס המתאים לכל פעילות בנפרד.'),
 ('בחירות 2026 - משפחות','kids','kids-family',MUSEUM+'בחירות__2026_-_משפחות','סיור משפחתי במוזיאון אגם ביום הבחירות, שמפגיש ילדים והורים עם צבע, תנועה ואמנות קינטית. הפעילות מאפשרת להכיר יחד את עולמו של יעקב אגם ואת התערוכה עם יצירות מנשה קדישמן. סדנאות היצירה המוצעות במוזיאון באותו יום מחייבות בדיקת כרטיס מתאים בנפרד.'),
 ('בחירות 2026 - קהל רחב','exhibition','exhibition',MUSEUM+'בחירות_2026_-_קהל_רחב','סיור מודרך לקהל הרחב במוזיאון אגם ביום הבחירות, סביב העבודות של יעקב אגם והדרך שבה הן משתנות עם תנועת הצופה. הביקור מציע גם היכרות עם התערוכה המשלבת יצירות של אגם ומנשה קדישמן ומתאים לחובבי אמנות וסקרנים.'),
 ('להקת המחול ורטיגו - "נונה" גרסת המוזיאון','music','dance',MUSEUM+'להקת_המחול_ורטיגו_-_נונה__גרסת_המוזיאון','להקת ורטיגו מגיעה למוזיאון אגם עם גרסה אינטימית של ״נונה״, בכוריאוגרפיה של נעה ורטהיים ורנה קורן ורטהיים. הקהל יושב סביב הבמה בזווית של 270 מעלות וצופה מקרוב ביצירה העוסקת בזמן ובתנועה. לפני המופע, שאורכו כשעה, מתקיימת שיחה עם נעה ורטהיים; הבילוי מיועד לקהל אוהבי המחול והאמנות.'),
 ('שלישי לגיל השלישי - תושבי ראשון לציון','seniors','senior-culture',MUSEUM+'שלישי_לגיל_השלישי_-_תושבי_ראשון_לציון','סיור מודרך במוזיאון אגם לגמלאים תושבי ראשון לציון, המוקדש ליצירותיו של יעקב אגם ולחוויית הצפייה באמנות קינטית. הפעילות מתחילה ב־12:00 ומאפשרת מפגש משותף עם אמנות וצבע. יש להביא תעודת זהות ולהזמין מראש, משום שמספר המקומות מוגבל. קרובים שאינם זכאים להטבה יכולים להצטרף בתשלום המפורסם בעמוד המארגן.'),
 ('הרפתקה במוזיאון - הצגה בתערוכה','kids','kids-theatre',MUSEUM+'הרפתקה_במוזיאון_-_הצגה_בתערוכה','״תמיד יוצא לי סוס״ היא הרפתקה תיאטרלית בין יצירותיו של אגם, המשלבת בובות והשתתפות קהל בסיפור על רוח האמנות הבורחת מהמוזיאון. המופע של קבוצת הבובנאיות החופשיות, ביצירת מעין רזניק וליאת שבתאי, מיועד להורים ולילדים מגיל חמש. זו הזדמנות לפגוש אמנות דרך משחק ודמיון בתוך חלל התערוכה.'),
 ('אימפרובוק: מופע תיאטרלי ספרותי שסופו לא ידוע','theatre','theatre','https://www.kotar-rishon-lezion.org.il/events-category/eventsactivities/','נעמי לבוב, יואב היימן ורועי צדוק מאלתרים על הבמה מחזה קצר בהשראת ספרים שהקהל בוחר מעגלת ההחזרות של הספרייה. המופע מיועד למבוגרים, ומשלב ספרות, משחק והפתעות שנוצרות בזמן אמת. כל ערב מקבל סיפור אחר בזכות הבחירות של המשתתפים.'),
]

def normalize_media(value):
 if not isinstance(value,str):return value
 # A root-relative media-bank URL is already portable between cities.
 marker='/events-preview/'
 if marker in value and value.startswith(('../','assets/','/events-preview/rishon-lezion//')):
  return value[value.index(marker):]
 return value

def prepare(data,catalog):
 from rishon_editorial_sources import norm
 aliases=catalog.setdefault('title_aliases',{});aliases.update(ALIASES)
 # The old Cinderella alias incorrectly claimed two named casts were identical.
 aliases.pop('סינדרלה — מחזמר חנוכה עם נעמה סופר על',None)
 long_nona=next((e['title']for e in data['events']if 'נונה' in e['title'] and 'חמישי |'in e['title']),None)
 if long_nona:aliases[long_nona]=PROGRAMS[4][0]
 existing={norm(p['lookup_title']):p for p in catalog['programs']}
 for title,cat,sub,url,text in PROGRAMS:
  p=dict(lookup_title=title,source_url=url,category=cat,subcategory=sub,description=text)
  if norm(title) in existing:existing[norm(title)].update(p)
  else:catalog['programs'].append(p)
 for e in data['events']:
  for k in ['image_url','thumbnail_url','image_origin_url']:
   if k in e:e[k]=normalize_media(e[k])
  if 'נונה'in e['title']and 'ורטיגו'in e['title']:
   e['title']=PROGRAMS[4][0];e['category']='music';e['subcategory']='dance';e['categories']=['music'];e['audiences']=['adults'];e['content_source_url']=PROGRAMS[4][3]
   e['ticket_url']=PROGRAMS[4][3];e['purchase_url']=PROGRAMS[4][3]
  if e.get('event_id')=='r_k_1019_1700':
   e['venue']='כותר ראשון אלון'
  if norm(e['title'])==norm(PROGRAMS[6][0]):e['categories']=['kids'];e['audiences']=['kids','families'];e['age_min']=5
  if norm(e['title'])==norm(PROGRAMS[5][0]):e['categories']=['seniors'];e['audiences']=['seniors','adults']
  if norm(e['title'])==norm(PROGRAMS[2][0]):e['categories']=['kids'];e['audiences']=['kids','families']
 return data,catalog

def finish(data,catalog,protected_event_ids=frozenset()):
 from rishon_editorial_sources import norm
 from apply_rishon_editorial import venue_key
 aliases={norm(k):norm(v)for k,v in catalog.get('title_aliases',{}).items()}
 def identity(e):
  n=norm(e['title']);n=aliases.get(n,n)
  if n.startswith('מרתון סטנדאפ'):n=re.sub(r' פאצ ו בר$','',n)
  return n
 def venue(e):
  n=norm(e.get('venue'));title=identity(e)
  if title=='סוד המוח הצעיר'and n in ['כותר ראשון ראשון לציון','כותר אלון ראשון לציון','כותר ראשון אלון']:return 'אלון'
  if 'אחד העם 7'in n or 'חביב'in n:return 'חביב'
  if 'מוזיאון אגם'in n:return 'yama'
  if 'פטיפון'in n:return 'patiphone'
  if 'פאצ'in n:return 'pacho'
  # Auditorium is used as an alternative label for the same venue for this show.
  if 'מועדון הזמר של אילנה כץ'in title and ('היכל'in n or 'אודיטוריום'in n):return 'htrl'
  return venue_key(e.get('venue'))
 groups=defaultdict(list)
 for e in data['events']:
  if e.get('is_active')is not False:groups[(identity(e),e.get('start_date'),str(e.get('start_time')or'')[:5],venue(e))].append(e)
 stats=Counter()
 for rows in groups.values():
  # Duplicate public identifiers are unresolved until source/CMS review.
  if len(rows)<2 or any(e.get('event_id') in protected_event_ids for e in rows):continue
  primary=max(rows,key=lambda e:(bool(e.get('source_content_authoritative')),bool(e.get('editorial_version')),bool(e.get('image_verified')and e.get('image_strategy')!='approved_category_illustration'),len(e.get('description')or'')))
  primary.pop('canonical_event_id',None);primary.pop('duplicate_of',None)
  for other in rows:
   if other is primary:continue
   if other.get('content_origin')=='manual'and other.get('content_locked'):continue
   if not primary.get('description')and other.get('description'):primary['description']=other['description']
   if primary.get('image_strategy')=='approved_category_illustration'and other.get('image_verified')and other.get('image_strategy')!='approved_category_illustration':
    for k in ['image_url','thumbnail_url','thumbnail_ready','image_strategy','image_source','image_origin_url','image_verified','image_publishable','image_credit','image_rights_status']:
     if k in other:primary[k]=other[k]
   for k in ['price_min_ils','price_max_ils','address','duration_minutes']:
    if primary.get(k)is None and other.get(k)is not None:primary[k]=other[k]
   other.update(is_active=False,duplicate_of=primary['event_id'],canonical_event_id=primary['event_id']);stats['duplicate_occurrences_hidden']+=1
 # Resolve links through any earlier duplicate mapping without discarding records.
 byid={e['event_id']:e for e in data['events']}
 for e in data['events']:
  if e.get('event_id') in protected_event_ids or e.get('canonical_event_id') in protected_event_ids:continue
  target=e.get('canonical_event_id');seen={e['event_id']}
  while target in byid and target not in seen:
   seen.add(target);nxt=byid[target].get('canonical_event_id')
   if not nxt:break
   target=nxt
  if target and target not in [e['event_id']]:e['canonical_event_id']=target;e['duplicate_of']=target
 return dict(stats)
