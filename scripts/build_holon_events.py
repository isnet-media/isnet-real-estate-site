#!/usr/bin/env python3
"""Build Holon's static bootstrap, truthful source coverage and sharing card."""
import json,html
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
R=Path(__file__).resolve().parents[1];C=R/'events-preview/holon';D=C/'data'
def read(n):return json.loads((D/(n+'.json')).read_text())
def build():
 events=read('events');data=dict(events,categories=read('categories')['categories'],guides=read('guides')['items'],restaurants=read('restaurants')['items'],sources=read('sources')['sources'])
 (D/'site.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
 pack=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
 no='<ul>'+''.join('<li><a href="'+html.escape(e['source_url'],quote=True)+'">'+html.escape(e['title']+' · '+e['start_date']+' '+e['start_time'])+'</a></li>' for e in data['events'])+'</ul>'
 template=(C/'template.html').read_text();page=template.replace('<!--BOOTSTRAP-->','<script>window.HOLON_BOOTSTRAP='+pack+';</script>').replace('<!--NOSCRIPT-->',no)
 (C/'index.html').write_text(page)
 report=read('source-report');labels={'collected':'נקלטו אירועים מתוארכים','linked_directory':'קישור למדריך המקורי','interactive_source':'דורש JavaScript — קישור ישיר','fetch_failed':'הקליטה לא הצליחה — קישור למקור','closure_notice':'מופיעה הודעת סגירה — יש לבדוק מול המוסד'}
 rows=''.join('<tr><td><a target="_blank" rel="noopener" href="'+html.escape(s['url'],quote=True)+'">'+html.escape(s['name'])+'</a></td><td>'+labels.get(s['status'],s['status'])+'</td><td>'+str(s['events_found'])+'</td></tr>' for s in report['sources'])
 food=''.join('<li><a href="'+html.escape(s['url'],quote=True)+'">'+html.escape(next((x['title'] for x in data['restaurants'] if x['id']==s['id']),s['id']))+'</a> — '+('המקור נבדק' if s['status']=='checked' else 'נדרשת בדיקה מול המקום')+'</li>' for s in report['food_sources'])
 museum_note='באתר המפעיל מופיעה הודעת סגירה עד להודעה אחרת. יש לוודא פתיחה מול המוזיאון.' if next((x for x in report['sources'] if x['id']=='children'),{}).get('status')=='closure_notice' else 'הביקור במסלולים מחייב בדיקת זמינות ותיאום מראש מול המוזיאון.'
 sourcepage='<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>מקורות ועדכונים — מה עושים בחולון</title><link rel="stylesheet" href="style.css?v=holon-launch-20261101"><link rel="canonical" href="https://isnet.co.il/events-preview/holon/sources.html"></head><body><header class="sticky"><div class="topbar"><a class="brand" href="./">מה עושים <em>בחולון?</em><span class="byline">מבית חולון נט</span></a><a href="./">חזרה לראשי ←</a></div></header><main class="wrap report"><h1>מקורות ועדכונים</h1><p>בדיקה אחרונה: '+html.escape(report['checked_at'][:10])+'. הלוח משלב אירועים מתוארכים ומדריכי בילוי קבועים. מדריך קבוע אינו אישור שהמקום פתוח ברגע זה.</p><p>במקורות אינטראקטיביים מוצג קישור ישיר. לא משוכפלים מועדים מתוך סימון „עוד תאריכים” ללא פרטי תאריך מפורשים. תמונות יח״צ מסומנות בשם המארגן; שאר התמונות הן המחשה.</p><h2>אירועים, תרבות ופנאי</h2><table><thead><tr><th>מקור</th><th>מצב הקליטה</th><th>מועדים שנמצאו</th></tr></thead><tbody>'+rows+'</tbody></table><h2>מקורות הקולינריה</h2><ul>'+food+'</ul><h2>עדכונים שחשוב להכיר</h2><p>מוזיאון הילדים: '+museum_note+'</p><p>גורדוס אינה נכללת במדריך כמסעדה פעילה בעקבות <a href="https://www.hashikma-holon.co.il/culture/66825">הודעת הסגירה שפורסמה</a>.</p><p>שעות פתיחה וכשרות מוצגות בסינון רק כשנמצאה אסמכתה. המידע עשוי להשתנות; יש לוודא מול המקום לפני יציאה.</p><a class="primary" href="./">מוצאים בילוי בחולון ←</a></main><footer>מבית חולון נט</footer></body></html>'
 (C/'sources.html').write_text(sourcepage)
 # Alias routes retain the same city-owned interface and queryable detail views.
 for name,cat in [('restaurants','food'),('cinema','cinema'),('kids','kids'),('seniors','seniors'),('saturday','saturday'),('attractions','attractions')]:
  alias=page.replace('<script>window.HOLON_BOOTSTRAP=', '<script>if(!location.search)history.replaceState({},"","?category='+cat+'");window.HOLON_BOOTSTRAP=',1)
  alias=alias.replace('href="https://isnet.co.il/events-preview/holon/"','href="https://isnet.co.il/events-preview/holon/'+name+'.html"',1)
  (C/(name+'.html')).write_text(alias)
 # A local JPEG provides a stable WhatsApp/Facebook preview, not an external hotlink.
 target=C/'assets/share-card.jpg'
 if not target.exists():
  im=Image.open(R/'events-preview/kiryat-gat/assets/illustrations/live-music.jpg').convert('RGB');im=ImageOps.fit(im,(1200,630));overlay=Image.new('RGB',im.size,'#111d24');im=Image.blend(im,overlay,.64);draw=ImageDraw.Draw(im);font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
  draw.text((1120,145),'מה עושים בחולון?',font=ImageFont.truetype(font,83),fill='#f5e8cd',anchor='ra',direction='rtl');draw.text((1110,285),'הופעות · הצגות · ילדים · מסעדות',font=ImageFont.truetype(font,38),fill='white',anchor='ra',direction='rtl');draw.line((80,420,1120,420),fill='#d7bc80',width=3);draw.text((1110,464),'מבית חולון נט',font=ImageFont.truetype(font,42),fill='#e2c28a',anchor='ra',direction='rtl');im.save(target,quality=90,optimize=True)
 print('Built Holon:',len(data['events']),'events;',len(data['restaurants']),'restaurants;',len(data['categories']),'categories')
if __name__=='__main__':build()
