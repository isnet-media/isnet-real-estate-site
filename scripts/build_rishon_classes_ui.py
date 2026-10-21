#!/usr/bin/env python3
"""Localize the reviewed classes UI without importing another city's facts."""
import json,re,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'meusharim/rishon-lezion';T=ROOT/'meusharim/yavne'
for name in ['index.html','catalog.html','course.html','app.js','course.js','style.css','course.css']:
 s=(T/name).read_text()
 s=s.replace('https://www.yavnenet.co.il/','https://www.rishonet.com/').replace('/events-preview/yavne/','/events-preview/rishon-lezion/').replace('/meusharim/yavne/','/meusharim/rishon-lezion/')
 s=s.replace('yavnenet.svg','rishonet.svg').replace('what-to-do-yavne.svg','what-to-do-rishon.svg')
 s=s.replace('ביבנה','בראשון לציון').replace('יבנה נט','ראשון נט').replace('יבנה','ראשון לציון')
 s=s.replace('הקבוצות והמסלולים','החוגים והמסלולים').replace('קבוצות שמתאימות לכם','חוגים שמתאימים לכם').replace('קבוצות ומסלולים','חוגים ומסלולים')
 s=s.replace('עושים את החיים מגוונים יותר במקום','חוגים, קורסים והעשרה לכל הגילאים בראשון לציון')
 s=s.replace('rishonet.svg?v=2','rishonet.svg?v=light1')
 s=s.replace('מידע ממפעילי החוגים בראשון לציון','מידע מחוברות החוגים העירוניות').replace('המידע נאסף מעמודי המפעילים בראשון לציון.','המידע נאסף מחוברות החוגים העירוניות לשנת 2026–2027.')
 # Keep group labels attached to their schedule rows.
 if name=='course.js':s=s.replace("row.day?'יום '+row.day:'מועד'","(row.day?'יום '+row.day:'מועד')+(row.label?' · '+row.label:'')")
 if name=='app.js':
  s=s.replace("const t=node('button','tile isnetNavFeature')", "const t=node('a','tile isnetNavFeature')")
  s=s.replace("t.type='button';t.dataset.category=c;t.onclick=()=>{el('category').value=el('category').value===c?'':c;limit=24;render()}", "t.dataset.category=c;t.href='./catalog.html?'+new URLSearchParams({category:c})")
  s=s.replace("t.day+' · '+t.time", "t.day+' · '+t.time+(t.label?' · '+t.label:'')")
  s=s.replace("for(const t of r.schedule)","for(const t of r.schedule.slice(0,2))")
  s=s.replace("}else if(r.day||r.time)",";if(r.schedule.length>2)b.append(node('div','info','ועוד '+(r.schedule.length-2)+' מועדים בכרטיס החוג'));}else if(r.day||r.time)")
 (D/name).write_text(s)
with (D/'style.css').open('a') as css:
 css.write('\n.tiles>a.tile{text-decoration:none;color:inherit}\n')
for src,dest in [('rishonet-dark.svg','rishonet.svg'),('what-to-do-rishon-dark.svg','what-to-do-rishon.svg')]:shutil.copy(ROOT/'events-preview/rishon-lezion/assets/branding'/src,D/'assets'/dest)
logo=D/'assets/rishonet.svg';logo.write_text(logo.read_text().replace('#fffaf2','#103d72'))
for old in ['yavnenet.svg','what-to-do-yavne.svg']:(D/'assets'/old).unlink(missing_ok=True)
# The photo bank remains shared; its provenance is retained alongside assignments.
bank=json.loads((T/'data/image-bank.json').read_text());data=json.loads((D/'data/classes.json').read_text());used={}
keymap=[('כלב', 'אילוף כלבים'),('וטרינר','מדע ורפואה'),('אלקטרונ','רובוטיקה'),('רובוט','רובוטיקה'),('טכנוטריק','רובוטיקה'),('הנדסה','רובוטיקה'),('מדע','מדע ורפואה'),('רפואה','מדע ורפואה'),('מחשבים','מחשבים'),('תכנות','מחשבים'),('יוטיובר','מחשבים'),('אפיי','בישול'),('אפיה','בישול'),('סוכר','בישול'),('קונדיט','בישול'),('קרמיקה','קרמיקה'),('חימר','קרמיקה'),('פיסול','קרמיקה'),('ציור','ציור'),('מאנג','ציור'),('תכשיט','סריגה'),('תפירה','סריגה'),('שחמט','שחמט'),('פוקימון','שחמט'),('גיטרה','גיטרה'),('אורגנית','גיטרה'),('פיתוח קול','גיטרה'),('כדורגל','כדורגל'),('כדורסל','כדורסל'),('טניס שדה','טניס'),('האקדמיה לטניס','טניס'),('טניס בנחלה','טניס'),('היפ','היפ הופ'),('קפוארה','קפוארה'),('פילאטיס','פילאטיס'),('בונה עצם','פילאטיס'),('במים','אקווה ארובי')]
category_fallback={'אמנויות הבמה':'תיאטרון','אמנויות לחימה':'קראטה','מחול':'מחול','התעמלות':'תנועה','ספורט אמנותי':'התעמלות קרקע','התפתחות לגיל הרך':'תנועה','מוזיקה':'גיטרה','חשיבה והגיון':'שחמט','אמנויות יצירה':'ציור','למידה והעשרה':'אנגלית'}
for r in data['records']:
 topic=next((v for k,v in keymap if k in r['name']),category_fallback.get(r['category']))
 candidates=[b for b in bank if b['topic']==topic]
 if candidates:
  b=candidates[int(hashlib.sha256(r['id'].encode()).hexdigest()[:8],16)%len(candidates)];r['image']='../yavne/'+b['image'];used[r['image']]={**b,'image':r['image'],'illustrative':True}
 r['description']=r['description'].replace('ראשון לציון. מסגרת','ראשון לציון. מסגרת')
extra=json.loads((D/'data/source-images.json').read_text())
for r in data['records']:
 for b in extra:
  if b['topic'] in r['name'] or (b['topic']=='כדורעף' and 'כדורשת' in r['name']):
   r['image']=b['image'];used[r['image']]=b;break
(D/'data/classes.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
(D/'data/image-bank.json').write_text(json.dumps(list(used.values()),ensure_ascii=False,indent=2)+'\n')
choices=[('טניס שדה','טניס בראשון לציון'),('היפ הופ','היפ הופ ומחול'),('פיסול בקרמיקה','יוצרים בקרמיקה'),('רובוטיקה הנדסית','רובוטיקה והנדסה לילדים'),('פילאטיס מזרן','פילאטיס למבוגרים'),('גיטרה / אורגנית','לומדים לנגן')]
featured=[]
for name,title in choices:
 r=next(r for r in data['records'] if r['name']==name and r['image']);featured.append(dict(id=r['id'],display_title=title,position=len(featured)+1,sponsored=False))
(D/'data/featured.json').write_text(json.dumps({'items':featured},ensure_ascii=False,indent=2)+'\n')
for p in D.glob('*.html'):
 s=p.read_text()
 for a in ['app.js','course.js','style.css','course.css']:
  digest=hashlib.sha256((D/a).read_bytes()).hexdigest()[:12];s=re.sub(re.escape(a)+r'(?:\?v=[^" ]+)?',a+'?v='+digest,s)
 p.write_text(s)
print('Built Rishon classes UI;',len(data['records']),'programs;',sum(bool(r['image']) for r in data['records']),'illustrative photos')
