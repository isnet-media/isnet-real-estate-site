"""Build the Holon health directory from reviewed official service links."""
import json,html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CITY=ROOT/'events-preview/holon'
esc=lambda x:html.escape(str(x),quote=True)
def build(check=False,city_dir=None):
 target=Path(city_dir) if city_dir else CITY
 data=json.loads((target/'data/health.json').read_text())
 def link(url,label,cls=''):
  external=url.startswith('https:')
  return '<a class="health-action '+cls+'" href="'+esc(url)+'"'+(' target="_blank" rel="noopener"' if external else '')+'>'+label+(' ↗' if external else '')+'</a>'
 def card(x,pharmacy=False):
  actions=link(x['source_url'],'בדיקת פתיחה באתר הסניף' if pharmacy else 'פרטים באתר הרשמי')
  if x.get('phone'):actions+=link('tel:'+x['phone'],'חיוג <bdi>'+esc(x['phone'])+'</bdi>','secondary')
  if x.get('address'):actions+=link('https://www.google.com/maps/search/?api=1&query='+__import__('urllib.parse',fromlist=['quote']).quote(x['name']+' '+x['address']),'ניווט','secondary')
  return '<article class="health-card" data-health-kind="'+('pharmacy' if pharmacy else 'service')+'"><p class="health-eyebrow">'+esc(x['label'])+'</p><h3>'+esc(x['name'])+'</h3>'+('<p>'+esc(x['address'])+'</p>' if x.get('address') else '')+'<p>'+esc(x['description'])+'</p><div class="health-actions">'+actions+'</div><small>מקור: '+esc(x['source_name'])+' · נבדק ב־'+esc(data['checked_at'])+'</small></article>'
 sections=''
 for section in data['sections']:
  sections+='<section id="'+esc(section['id'])+'" aria-labelledby="'+esc(section['id'])+'-title"><h2 id="'+esc(section['id'])+'-title">'+esc(section['title'])+'</h2><p class="health-intro">'+esc(section['description'])+'</p><div class="health-grid">'+''.join(card(x,section['id']=='pharmacies') for x in section['items'])+'</div></section>'
 page='''<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>בריאות וחירום בחולון — בתי מרקחת ומוקדי רפואה</title><meta name="description" content="בתי מרקחת בחולון לבדיקת פתיחה, חיוג למוקדי קופות החולים ושירותי חירום — קישורים למקורות רשמיים."><link rel="canonical" href="https://isnet.co.il/events-preview/holon/health.html"><link rel="stylesheet" href="styles.css"><link rel="stylesheet" href="publisher-brand.css"><link rel="stylesheet" href="health.css?v=20261101"><script defer src="/assets/isnet-top-navigation.js?v=holon-health1"></script></head><body class="health-page"><main class="health-main"><a class="health-back" href="./">← מה עושים בחולון</a><header class="health-header"><p class="health-eyebrow">שירותים לתושבי חולון</p><h1>בריאות וחירום</h1><p>בית מרקחת, ייעוץ רפואי או טיפול דחוף — כל הדרכים לפנות, במקום אחד.</p></header><aside class="health-emergency" aria-label="חירום רפואי"><div><strong>חירום רפואי או סכנת חיים?</strong><p>חייגו למד״א. אל תמתינו לחיפוש מקום פתוח.</p></div><a href="tel:101" class="health-action emergency-call">חיוג למד״א <bdi>101</bdi></a><a class="health-emergency-source" href="https://www.mdais.org/101" target="_blank" rel="noopener">המקור: מגן דוד אדום ↗</a></aside><nav class="health-jumps" aria-label="מציאת שירות"><a href="#pharmacies">בית מרקחת פתוח</a><a href="#hmo">ייעוץ בקופת החולים</a><a href="#urgent">רפואה דחופה</a></nav><p class="health-note"><strong>לפני היציאה:</strong> אין כאן חיווי פתיחה בזמן אמת או רשימת תורנות עירונית חיה. בדקו באתר הסניף והתקשרו לוודא שהרוקח נמצא, שיש מלאי לתרופה ושיש הסדר עם הקופה. שעות חנות הפארם עשויות להיות שונות משעות בית המרקחת.</p>'''+sections+'''<footer class="health-footer"><p>המידע מסייע לאתר שירות ולקבל פרטי קשר. לקבלת הנחיה רפואית פנו לצוות רפואי. תנאי זכאות, הפניה, עלות ושעות פעילות יש לברר עם נותן השירות.</p><a href="./">חזרה למה עושים בחולון ←</a></footer></main></body></html>'''
 if data['city']=='herzliya':
  page=page.replace('בחולון','בהרצליה').replace('חולון','הרצליה').replace('/holon/health.html','/herzliya/health.html')
  page=page.replace('href="styles.css"','href="../holon/styles.css"').replace('href="publisher-brand.css"','href="../holon/publisher-brand.css"').replace('href="health.css?v=20261101"','href="../holon/health.css?v=20261101"><link rel="stylesheet" href="health-only.css?v=20261101"')
  page=page.replace('<script defer src="/assets/isnet-top-navigation.js?v=holon-health1"></script>','<meta name="health-city" content="herzliya"><script defer src="../shared/event-share.js?v=20261030-1"></script>')
  page=page.replace('<body class="health-page">','<body class="health-page"><nav class="health-topbar" aria-label="בריאות וחירום בהרצליה"><a class="health-brand" href="health.html">בריאות וחירום בהרצליה <small>ISNET · ישראל נט</small></a><button type="button" class="isnetSiteShare" aria-label="שיתוף עמוד הבריאות">'+chr(8599)+' שיתוף</button></nav>')
  page=page.replace('<a class="health-back" href="./">← מה עושים בהרצליה</a>','').replace('<h1>בריאות וחירום</h1>','<h1>בריאות וחירום בהרצליה</h1>').replace('<a href="./">חזרה למה עושים בהרצליה ←</a>','<a href="https://isnet.co.il/">ישראל נט ←</a>')
 p=target/'health.html' ;changed=not p.exists() or p.read_text()!=page
 if changed and not check:p.write_text(page)
 return changed
if __name__=='__main__':build()
