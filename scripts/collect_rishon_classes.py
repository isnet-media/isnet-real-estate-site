#!/usr/bin/env python3
"""Build Rishon's city-owned course catalog from reviewed 2026–27 brochures.

Facts only: brochure titles and explicitly associated age/schedule lines.
Descriptions are original. No registration availability or prices are inferred.
Use --cache-dir to retain downloaded HTML. Current edition links are explicit
because the municipal navigation still includes two previous-year brochures.
"""
import argparse,hashlib,json,re,time
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/'meusharim/rishon-lezion/data'
BOOKS=[('גני ראשון','vrun'),('כרמים','yutu'),('מישור הנוף','ofhx'),('נווה חוף','zmud'),('נאות אשלים','tlwg'),('נאות שקמה','psjy'),('נווה הדרים יגאל אלון','lgft'),('נחלת 360','owxv'),('גן נחום','pwpu'),('ניצנים','rtqx'),('עלומים','kddt'),('פרס נובל','ciqa'),('קריית גנים','llbs'),('קריית ראשון','prrk'),('רוזן','mvvq'),('נעורים','lvgx'),('בארי','qlzq'),('יסוד המעלה','dbps'),('שלמון','xkds'),('נווה דקלים','bien'),('רקפות','kqpw'),('נרקיסים','wjii'),('תמיר','kzxn')]
DAYS=['ראשון','שני','שלישי','רביעי','חמישי','שישי','שבת']
def norm(s):return re.sub(r'\s+',' ',str(s).replace('\\"','"').replace('׳',"'").replace('‘',"'").replace('’',"'")).strip()
def classify(s):
 for cat,words in [('אמנויות לחימה',['גודו','ג\'ודו','קראטה','קרב','איגרוף','אגרוף','קפוארה','אייקידו','MMA','הגנה עצמית']),('מוזיקה',['גיטרה','אורגנית','פיתוח קול','נגינה','מוסיקה','מוזיקה']),('מחול',['DollHouse','מחול','בלט','היפ','גאז',"ג'אז",'זומבה','ריקוד','LifeDance']),('אמנויות הבמה',['תיאטר','תאטר','משחק מול','דרמה','משחק ותיאטרון']),('ספורט מים',['במים','שחייה']),('ספורט אמנותי',['אקרובטיקה','אקרודאנס','קרקע','אומנותית','אמנותית','גלגיליות','קרקס','צ\'ירלידינג']),('התפתחות לגיל הרך',['תנועה','לגיל הרך','התעמלותי']),('התעמלות',['יוגה','פילאטיס','התעמלות','FITNESS','כושר','עיצוב','בוקר','כוח','פלדנקרייז','פרוגרס','אקטיבי']),('ספורט תחרותי',['טניס','פיקלבול','פיקל','כדור','בדמינטון']),('חשיבה והגיון',['שחמט','פוקימון','מבוכים']),('אמנויות יצירה',['ציור','מאנג','תכשיט','סוכר','פיסול','קרמיקה','אפיי','אפיה','בישול','קונדיט','אומנות','אמנות','תפירה'])]:
  if any(w.lower() in s.lower() for w in words):return cat
 return 'למידה והעשרה'
def ages(label):
 out=[]
 if re.search(r'גן|טרום חובה|קטנט|גיל הרך|פעוט',label):out.append('עד 5')
 if re.search(r"(?:כיתות|כתות)\s+[א-ו]'|ילדים",label):out.append('6-12')
 if re.search(r"(?:כיתות|כתות)\s+[ז-ט]'|י[אב]'|חטיבה",label):out.append('13-18')
 if re.search(r'נוער|חטיב|תיכון',label):out.append('13-18')
 if re.search(r'בוגר|נשים|אימהות|אמהות|גברים|18\+',label):out.append('18+')
 if re.search(r'גיל.{0,2}שלישי|זהב|גמלא|גימלא|60\+',label):out+=['18+','60+']
 for a,b in re.findall(r'(\d{1,2})\s*[-–]\s*(\d{1,2})',label):
  a,b=sorted([int(a),int(b)])
  if b>99:continue
  if a<=5:out.append('עד 5')
  if a<=12 and b>=6:out.append('6-12')
  if a<=17 and b>=13:out.append('13-18')
  if b>=18:out.append('18+')
  if b>=60:out.append('60+')
 return list(dict.fromkeys(out))
INTRO={'אמנויות לחימה':'תרגול תנועה וטכניקה בענף לחימה, במסגרת קבוצתית לפי רמות וגילאים.','מחול':'מפגשים של תנועה, קצב ולימוד ריקוד, עם אפשרות להתמיד ולהתקדם לאורך השנה.','מוזיקה':'מסגרת ללימוד ותרגול מוזיקלי, למי שרוצים לפתח את היכולת לנגן או לשיר.','אמנויות הבמה':'מסגרת לביטוי על הבמה ולתרגול משחק, דמיון ותקשורת בקבוצה.','אמנויות יצירה':'זמן קבוע לעבודה יצירתית, להתנסות בחומרים ולפיתוח ביטוי אישי.','ספורט תחרותי':'אימונים בענף הספורט, עם תרגול מיומנויות ומשחק במסגרת קבוצתית.','ספורט אמנותי':'פעילות המשלבת תרגול תנועה, שליטה בגוף ומיומנויות בענף.','התעמלות':'מסגרת שבועית לפעילות גופנית ולתרגול תנועה, לפי אופי החוג והקבוצה.','התפתחות לגיל הרך':'פעילות תנועה והתנסות לילדים צעירים, בחלוקה לקבוצות כפי שפורסמה במרכז.','חשיבה והגיון':'מפגשים של משחק, חשיבה ותכנון, עם אתגרים ותרגול בקבוצה.','למידה והעשרה':'מסלול להעשרה וללמידה מעבר לשעות הלימודים, לפי התוכנית שפורסמה במרכז הקהילה.','ספורט מים':'פעילות גופנית במים במסגרת המפורסמת בחוברת.'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cache-dir',default=str(ROOT/'.cache/rishon-classes'));args=ap.parse_args();cache=Path(args.cache_dir);cache.mkdir(parents=True,exist_ok=True)
 titles={norm(x) for x in json.loads((DEST/'source-titles.json').read_text())}
 def load(book):
  center,key=book;p=cache/(key+'.html');url='https://fliphtml5.com/msxll/'+key+'/'
  if not p.exists():
   r=requests.get(url,timeout=30);r.raise_for_status();p.write_text(r.text);time.sleep(.3)
  s=BeautifulSoup(p.read_text(),'html.parser');title=s.title.get_text()
  if not re.search(r'2026.?20?27|2026-27',title):raise ValueError('Old brochure: '+title)
  pages=[]
  for b in s.select('.flip-basic-text'):
   n=b.select_one('.flip-basic-num')
   if not n:continue
   pages.append((int(re.sub(r'\D','',n.get_text())),[norm(x.get_text(' ',strip=True)) for x in b.select('p')]))
  return center,key,url,pages
 books=list(ThreadPoolExecutor(4).map(load,BOOKS));records={};sources=[];audit=[];now=datetime.now(timezone.utc).isoformat()
 for center,key,url,pages in books:
  cover=' '.join(pages[0][1]);phone=next(iter(re.findall(r'0\d[-\d]{8,12}',cover)),'');address=next((l.split('׀')[0].strip() for l in pages[0][1] if re.search(r"רח['׳]|רחוב",l)),'')
  sources.append(dict(center=center,url=url,season='2026-2027',pages=len(pages)))
  branch='';branch_address=''
  for number,ls in pages:
   if number<4:continue
   text=' '.join(ls)
   if any(w in text for w in ['פתיחת קבוצה מותנית במינימום נרשמים','חיות וחוויות','yaelbrainess','דמי ההשתתפות','דבר ראש','אירועים קהילתיים']):continue
   # Dedicated school-branch sections have their own cover and address.
   if 'תשפ"ז 2026-27' in text and any('בית ספר' in l for l in ls):
    branch=next((l.replace('בבית ספר','בית ספר') for l in ls if 'בית ספר' in l),'')
    if branch=='בית ספר':branch+=' '+ls[0]
    branch_address=next((l.split('׀')[0] for l in ls if l.startswith(("רח'",'רחוב'))),'')
    continue
   starts=[i for i,l in enumerate(ls) if l in titles]
   for n,start in enumerate(starts):
    title=ls[start];end=starts[n+1] if n+1<len(starts) else len(ls);seg=ls[start+1:end]
    # A caption repeating the program's name must not create a second course.
    if not seg or not any(len(l)>45 and not re.search(r'רישום:|מענה טלפוני',l) for l in seg):continue
    name=re.sub(r'\s*חדש$|\s*/$','',title).strip();cat=classify(name)
    # Rows in a source's timetable can repeat headings. Merge at program/place.
    place='מרכז קהילה '+center+((' · '+branch) if branch else '')
    uid='rishon-'+key+'-'+hashlib.sha256((name+'|'+branch).encode()).hexdigest()[:12]
    instructor=next((re.sub(r'^ו?בהדרכת\s*','',l) for l in seg if l.startswith(('בהדרכת ','ובהדרכת ')) and len(l)<95),'')
    age_lines=[];schedule=[];days=[];current=[]
    for l in seg:
     if re.search(r'רישום:|מענה טלפוני|il\.co|www|׀',l):continue
     if re.match(r'ימי?\s',l):
      current=[d for d in DAYS if re.search(r'(?<![א-ת])ו?'+d+r'(?![א-ת])',l)];days+=current
     tm=re.search(r'(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})',l)
     if tm and current:
      a,b=tm.groups();a=a.zfill(5);b=b.zfill(5)
      # RTL PDF text sometimes puts the end first. Reject cross-midnight or
      # malformed OCR instead of guessing a duration.
      lo,hi=sorted([a,b]);mins=lambda t:int(t[:2])*60+int(t[3:]);duration=mins(hi)-mins(lo)
      label=l[:tm.start()].strip(' :–-')
      if 15<=duration<=240 and all(0<=int(t[:2])<=23 and 0<=int(t[3:])<=59 for t in [lo,hi]):
       for day in current:schedule.append(dict(day=day,time=lo+'–'+hi,label=label))
     if len(l)<110 and (tm or re.match(r'(?:ל?גילאי?|ל?כיתות|כתות|טרום חובה|גן חובה|מבוגרים|נשים|גיל שלישי)',l)):
      a=l[:tm.start()] if tm else l
      if re.search(r'גיל|כית|כתות|חובה|גן|נוער|בוגר|נשים|גברים',a):age_lines.append(a.strip(' :'))
    # Age metadata never uses phone numbers, course fees, or arbitrary prose.
    age_lines=list(dict.fromkeys(age_lines));age='; '.join(age_lines)[:350]
    age=re.sub(r'; (?:כיתות|כתות)$','',age)
    if not age:
     ctx=' '.join([name]+[l for l in ls[:3] if 'מרכז קהילה' in l])
     age='הגיל השלישי' if 'שלישי' in name else 'מבוגרים' if re.search(r'מבוגר|נשים|גברים',ctx) else 'הגיל הרך' if 'לגיל הרך' in name else ''
    raw_body=' '.join(seg)
    location_note='המרכז המפעיל מופיע בחוברת. יש לוודא מולו את מקום הפעילות המדויק ואת הקבוצה המתאימה.'
    explicit=next((l for l in seg if re.search(r'(?:יתקיי|האימונים).*?(?:בבית|בבי|באולם|במגרש)|^בבית הספר',l) and len(l)<120),'')
    if explicit:location_note=explicit+' יש לוודא את מקום המפגש מול המפעיל.'
    old=records.get(uid)
    if old:
     old['schedule']+=schedule;old['source_pages'].append(number);old['ages']=list(dict.fromkeys(old['ages']+ages(age)));old['age']='; '.join(dict.fromkeys(filter(None,[old['age'],age])))[:350];continue
    records[uid]=dict(id=uid,source_id=key+'-'+str(number)+'-'+name,name=name,subtitle='',category=cat,subcategory=name,age=age,ages=ages(age),district=branch or center,place=place,address=branch_address or (address+' ראשון לציון' if address else ''),phone=phone,instructor=instructor,day=', '.join(dict.fromkeys(days)),time='',schedule=schedule,price=None,registration_url='',status='source-listed',source_url=url+str(number)+'/',source_pages=[number],brochure_url=url,season='2026-2027',verified_at=now,detail_verified=True,location_note=location_note,description=name+' במסגרת '+place+'. '+INTRO[cat]+'\n'+('מיועד לקבוצות: '+age+'.\n' if age else '')+'פרטי הפעילות מופיעים בחוברת החוגים העירונית לשנת 2026–2027. לבחירת קבוצה ולבירור ההרשמה פונים למרכז המפעיל.',image='',image_illustrative=True,image_credit='תמונת פעילות להמחשה מתוך מאגר מעושרים; אינה צילום של חוג בראשון לציון.')
    audit.append(dict(id=uid,center=center,page=number,title=title,segment=seg))
 rows=list(records.values())
 for r in rows:
  r['schedule']=list({(x['day'],x['time'],x['label']):x for x in r['schedule']}.values());r['source_pages']=sorted(set(r['source_pages']))
 DEST.mkdir(parents=True,exist_ok=True)
 (DEST/'classes.json').write_text(json.dumps(dict(city='ראשון לציון',retrieved_on=now,season='2026-2027',record_type='program_at_center',records=rows),ensure_ascii=False,indent=2)+'\n')
 (DEST/'coverage.json').write_text(json.dumps(dict(city='ראשון לציון',programs=len(rows),centers=len(books),sources=sources,with_schedule=sum(bool(r['schedule']) for r in rows),with_age=sum(bool(r['age']) for r in rows),retrieved_on=now),ensure_ascii=False,indent=2)+'\n')
 (cache/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
 print('COLLECTED',len(rows),'programs at',len(books),'centers;',sum(bool(r['schedule']) for r in rows),'with schedules')
if __name__=='__main__':main()
