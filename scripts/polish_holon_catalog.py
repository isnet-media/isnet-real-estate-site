#!/usr/bin/env python3
"""Reviewed Holon metadata and original short descriptions; no invented dates."""
import json,re,concurrent.futures
from pathlib import Path
import sync_holon_events as core
from urllib.parse import urljoin
R=core.CITY;D=core.DATA
EDITORIAL={
'אור לגויים':'קומדיה של תיאטרון בית ליסין בכיכוב אבי קושניר. גילוי מפתיע על אמו שולח מורה לספרות לבירור משעשע של זהותו ומשפחתו.',
'זוגות בזיגזג':'סוף שבוע שתוכנן למפגש סודי מסתבך כשבני משפחה ואורחים משבשים את התוכנית. קומדיית טעויות עם זהויות מתחלפות.',
'כראמל':'הרפתקה מוזיקלית על פי ספריה של מאירה ברנע גולדברג: שלושה אחים יורשים טירה, מפעל וחתול בעל כוחות יוצאי דופן.',
'מסעדה בקצה הקוטב':'שלושה פינגווינים פותחים מסעדה אחרי שהאגם קופא. הצגת מדיטק על עבודה משותפת, חברות וטעמים שונים.',
'המכשפה בבית ממול':'ילדים שיוצאים לפעולה נגד שכנה מסתורית מגלים שהמציאות שונה מהדימוי שיצרו לה. הצגה על חברות, בדידות ודעות קדומות.',
'אריה הספריה':'אריה מצטרף לשגרת הספרייה ומעמיד את הכללים במבחן. הצגת ילדים של תיאטרון המדיטק.',
'חנן הגנן':'מפגש עם עגלת הפירות של חנן ועם ההפתעה שמסתתרת בחרצן קטן. הצגת ילדים על סקרנות, צמיחה וסבלנות.',
'מיקי - הבית של יעל':'מיקי מביאה לבמה עיבוד לספר של מרים רות על ילדה שמחפשת לעצמה מקום משלה. הצגת ילדים בשילוב שירים והומור.',
'קרקס קבורקה':'מופע לכל המשפחה של אורי ונועה וייס, עם ג׳אגלינג, אקרובטיקה ותיאטרון ללא מילים.',
'דרושה עוזרת':'קומדיה על זוג שאת שגרת הבית שלו מנהלת עוזרת לא שגרתית. בהשתתפות ניקי גולדשטיין, אקי אבני ונתי קלוגר.',
'זוגיות AI':'קומדיה של התיאטרון העברי על גבר שמנסה לפתור את משבר הזוגיות בעזרת בת זוג מלאכותית — ומגלה סיבוכים חדשים.',
'פארטי':'מופע מחווה לשירי מסיבות מתקופות שונות, מלהיטים בינלאומיים ועד מוזיקה ישראלית.',
'דוידוב- קפה פריז':'אריק דוידוב מארח את הזמרת עדן הולן ואת שלישיית בוז׳ולה למפגש מוזיקלי בהשראה פריזאית.',
'אלאדין':'עיבוד במה לאגדת אלאדין ומנורת הקסמים, עם דמויות מתחלפות, מוזיקה והומור לכל המשפחה.',
'אנחנו כבר גדולים':'ילדים שנשארים עם סבתא מכינים הצגה ומגלים מה הם כבר יכולים לעשות בעצמם. בהפקה משולבים שירים וסיפורים לילדים.',
'מעשה בחמישה בלונים':'עיבוד במה לסיפור הילדים על חמישה בלונים, הפתעות קטנות וההתמודדות עם פרידה.',
'חיפזון וזהירון':'דמויות הסדרה מתכוננות למסיבת חנוכה ופוגשות מכשולים בדרך. מופע לילדים עם שירים וסיפור החג.',
'רעותי הילדה':'מופע חנוכה עם רעותי וחברים, בשילוב שירים ודמויות מעולם התוכן של הילדים.'}
ALIASES={'כראמל 1':'כראמל','כראמל - תיאטרון אורנה פורת':'כראמל','הווירטואוזים של אריק דוידוב - קפה פריז':'דוידוב- קפה פריז','תזמורת ירושלים מזרח ומערב - תחנות בזמן איציק קלה':'תזמורת ירושלים- איציק קלה','הזוג המוזר-תיאטרון חיפה':'הזוג המוזר','מדיאה‎ - תיאטרון הקאמרי':'מדיאה'}
def base(title):
 title=re.split(r'[\x00-\x08]',title)[0].strip();title=ALIASES.get(title,title);title=re.sub(r'^מופע\s+','',title);title=re.sub(r'^Party\b','פארטי',title,flags=re.I);title=re.sub(r'רעותי הילדה הישראלית.*','רעותי הילדה הישראלית',title);title=re.sub(r'^בין ערביים\s*[-–]\s*','',title);title=re.sub(r'\s*[-–]\s*(?:תיאטרון|קומדיה|מופע סטנדאפ).*$', '',title);return core.core.text_norm(title)
def main():
 d=core.read('events');events=d['events'];categories={c['id']:c for c in core.read('categories')['categories']};held=[];out=[]
 events.sort(key=lambda e:e['source_id']=='mevalim')
 for e in events:
  if e['source_id'].startswith('papi') and 'חולון' not in e['venue']:held.append({'title':e['title'],'source_url':e['source_url'],'reason':'outside Holon'});continue
  e['title']=re.split(r'[\x00-\x08]',e['title'])[0].strip();e['venue']=e['venue'].replace('חולון חולון','חולון')
  if e['source_id'] in ['hth','mediatheque','cinematheque','design','tarbut'] and 'חולון' not in e['venue']:e['venue']+=' · חולון'
  match=next((x for x in out if base(x['title'])==base(e['title']) and x['start_date']==e['start_date'] and (x['start_time']==e['start_time'] or e['source_id']=='mevalim' and abs(int(x['start_time'][:2])*60+int(x['start_time'][3:])-int(e['start_time'][:2])*60-int(e['start_time'][3:]))<=60)),None)
  if match:held.append({'title':e['title'],'date':e['start_date'],'time':e['start_time'],'source_url':e['source_url'],'reason':'same show and date; primary organizer occurrence retained'});continue
  if e['category']=='community' and e['source_id']=='hth':e['category']='theatre';e['subcategory']='theatre'
  if e['source_id']=='hot-events' and re.search(r'הצדעה|מחווה|הרפז|תמוז|בי ג',e['title']):e['category']='music';e['subcategory']='live'
  if e['source_id']=='hot-events' and 'יאנה דרום' in e['title']:e['category']='lecture';e['subcategory']='lectures'
  if e['source_id']=='hot-events' and 'שבלול בצנצנת' in e['title']:e['category']='kids';e['subcategory']='shows'
  if 'שוקו וניל' in e['title']:e['category']='theatre';e['subcategory']='theatre'
  if 'סדנ' in e['title'] or 'חוג איור' in e['title']:e['category']='kids';e['subcategory']='workshops'
  if re.search(r'אלאדין|חנות סופגניות|היי סקול דרמה|אנחנו כבר גדולים|מסעדה בקצה',e['title']):e['category']='kids';e['subcategory']='shows'
  if e.get('image_role')!='official_promotional':e['image']=categories[e['category']]['image']
  desc=next((v for k,v in EDITORIAL.items() if base(k) in base(e['title'])),None)
  if desc:e['description']=desc
  else:
   kind={'cinema':'הקרנת סרט','music':'מופע מוזיקה','standup':'מופע סטנדאפ','theatre':'הצגה','kids':'פעילות לילדים','lecture':'הרצאה או מפגש תוכן','exhibition':'תערוכה או פעילות במוזיאון','community':'מפגש או פעילות קהילתית'}.get(e['category'],'אירוע')
   e['description']=kind+' ב'+e['venue']+'. פרטי התוכנית, הגיל המתאים וההשתתפות מפורסמים אצל המארגן.'
  aud=set(e.get('audiences',[]))
  if re.search(r'על הבוקר|בין ערביים|קלאסיקל|הפוגת זמר|שרים מכל הלב',e['title']):aud.add('seniors')
  if e['category']=='kids' or re.search(r'לכל המשפחה|גילי \d|ילדים',e['title']):aud.update(['kids','families'])
  e['audiences']=sorted(aud);out.append(e)
 # Official editorial pages enrich imagery only. Their dates never override the ticket calendar.
 try:
  soup=core.get('https://www.hth.co.il/');links=[(core.core.text_norm(a.get_text(' ',strip=True)),urljoin('https://www.hth.co.il/',a['href'])) for a in soup.select('a[href]') if '/events/' in a.get('href','') and a.get_text(' ',strip=True)]
 except Exception:links=[]
 urls={}
 for e in out:
  if e['source_id']!='hth':continue
  t=base(e['title']);u=next((u for n,u in links if n==t or n.startswith(t+' ')),None)
  if u:urls[e['id']]=u
 def picture(u):
  try:
   s=core.get(u);m=s.select_one('meta[property="og:image"]');img=core.promo(m.get('content') if m else None,u);return u,img,m.get('content') if m else None
  except Exception:return u,None,None
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:pictures={u:(im,origin) for u,im,origin in ex.map(picture,sorted(set(urls.values()))[:30])}
 for e in out:
  u=urls.get(e['id']);im,origin=pictures.get(u,(None,None))
  if im:e.update(image=im,image_role='official_promotional',image_origin_url=origin,image_credit='תמונת יח״צ: תיאטרון חולון',image_source_url=u)
 out.sort(key=lambda e:(e['start_date'],e['start_time']));d['events']=out;core.save('events',d)
 core.save('quality-report',{'checked_at':core.NOW.isoformat(),'events':len(out),'held_duplicates_or_conflicts':held,'event_photos':sum(e.get('image_role')=='official_promotional' for e in out),'note':'All remaining events and all categories/subcategories have labeled local or shared JPG illustrations.'})
 f=core.read('restaurants')
 for x in f['items']:
  if 'אייסברג' in x['title']:x['subcategory']='dessert';x['image']='../kiryat-gat/assets/food/dessert-illustration.jpg'
 core.save('restaurants',f)
 report=core.read('source-report');report['events']=len(out)
 for r in report['sources']:
  if r['id']=='easy':r.update(url='https://easy.co.il/list/Events?region=773',status='linked_directory',note='קישור לאיתור משלים; לא נקלטו ממנו אירועים')
 core.save('source-report',report)
 print('Polished',len(out),'events;',len(held),'duplicates/conflicts held;',sum(e.get('image_role')=='official_promotional' for e in out),'source photos')
if __name__=='__main__':main()
