#!/usr/bin/env python3
"""Build the Yavne-owned culinary edition from the reviewed Ashdod UI."""
import json,re,hashlib
from pathlib import Path
from sync_event_city_views import localize,TARGETS
ROOT=Path(__file__).resolve().parents[1];MASTER=ROOT/'events-preview/ashdod';DEST=ROOT/'events-preview/yavne'
def build():
 payload=json.loads((DEST/'data/restaurants.json').read_text());places=payload['restaurants'];city=TARGETS['yavne']
 for p in places:
  overrides={"New York Hot Dog Yavne":('street','נקניקיות ואוכל רחוב'),"בורגר 110":('burger','המבורגרים'),"יול'ס טוסט נקניק ונקנקיות":('street','טוסטים ונקניקיות'),"שייק אפ":('dessert','שייקים ומיצים'),"יגאל מבשל בשבילכם":('local','אוכל ביתי ומוכן')}
  if p['name'] in overrides:
   p['kind'],p['label']=overrides[p['name']];p['kinds']=[p['kind']]
  typ=p.get('source_business_type','')
  if 'כשר' in typ or 'בד"צ' in typ:
   p['kosher']='לפי עמוד העסק: '+typ+'. יש לוודא תעודת כשרות בתוקף מול המקום.';p['kosherVerified']=True
  p['kinds']=list(dict.fromkeys(p.get('kinds') or [p['kind']]))
  if p['kind'] in {'restaurant','meat','burger','italian','asian','fish','bar','street'} and 'restaurant' not in p['kinds']:p['kinds'].append('restaurant')
  if 'קייטרינג' in p.get('source_business_type',''):p['kinds'].append('catering')
  if p['kind']=='coffee_carts':p['kinds'].append('cafe')
  if p['kind']=='bakery' and any(w in p['name'] for w in ['עוג','מתוק','cakes','קונדיטור']):p['kinds'].append('dessert')
  p['source_label']=p.get('source_label') or 'עמוד העסק'
  p['site_label']='לעמוד העסק' if any(w in p.get('site','') for w in ['easy.co.il','rest.co.il']) else 'לאתר המקום'
  p.setdefault('kosher','לא אומתה כשרות עדכנית');p.setdefault('credit','')
 js=localize((MASTER/'restaurants.js').read_text(),'restaurants.js',city,'.js')
 start=js.index('const places=');end=js.index('\nconst kinds=',start)
 js=js[:start]+'const places='+json.dumps(places,ensure_ascii=False,separators=(',',':'))+';'+js[end:]
 start=js.index('const kinds=');end=js.index('\nconst esc=',start)
 kinds={'all':'הכול','restaurant':'מסעדות','meat':'בשרים וגריל','burger':'המבורגרים','italian':'איטלקי','asian':'אסייתי וסושי','fish':'דגים','street':'אוכל רחוב וחומוס','pizza':'פיצריות','cafe':'בתי קפה','coffee_carts':'עגלות קפה','bakery':'מאפיות וקונדיטוריות','dessert':'גלידה ומתוקים','local':'אוכל ביתי ומוכן','bar':'ברים ואוכל','deli':'מעדניות','catering':'קייטרינג ואירוח','wine':'יין ומשקאות'}
 js=js[:start]+'const kinds='+json.dumps(kinds,ensure_ascii=False)+';'+js[end:]
 js=js.replace("p.kind===state.kind","(p.kinds||[p.kind]).includes(state.kind)")
 js=js.replace("['sea','evening','coffee']","['family','evening','coffee']")
 js=js.replace('נבדק ב־19.10.2026',"נבדק ב־'+esc(p.checked_at||'2026-10-20')+'")
 js=js.replace("(p.booking?'הזמנת שולחן':'לאתר המקום')","(p.booking?'הזמנת שולחן':p.site_label)")
 js=js.replace("'>אתר המקום ↗</a>'","'>'+esc(p.site_label)+' ↗</a>'")
 js=js.replace(". צילום: '+esc(p.credit)+'. נבדק", ". '+(p.image?'צילום: '+esc(p.credit)+'. ':'')+'נבדק")
 # Do not show another city's photography, or turn missing photos into broken images.
 js=js.replace("'<img class=\"detail-image\" src=\"'+esc(p.image)+'\" alt=\"'+esc(p.name)+'\">", "(p.image?'<img class=\"detail-image\" src=\"'+esc(p.image)+'\" alt=\"'+esc(p.name)+'\">':'')+'")
 js=js.replace("<img src=\"'+esc(p.image)+'\" alt=\"'+esc(p.name)+'\" loading=\"lazy\" decoding=\"async\"><small class=\"photo-credit\">צילום: '+esc(p.credit)+'</small>", "'+(p.image?'<img src=\"'+esc(p.image)+'\" alt=\"'+esc(p.name)+'\" loading=\"lazy\" decoding=\"async\"><small class=\"photo-credit\">צילום: '+esc(p.credit)+'</small>':'<div class=\"food-no-photo\"><span>'+esc(p.label)+'</span><strong>'+esc(p.name)+'</strong></div>')+'")
 html=localize((MASTER/'restaurants.html').read_text(),'restaurants.html',city,'.html')
 html=html.replace('ASHDOD','YAVNE').replace('עיר של ים.','קרוב לבית.').replace('ים תיכון. שולחן פתוח.','יבנה. סביב השולחן.').replace('מהדגים של הנמל לקפה של הבוקר, מארוחה טובה לערב שנשארים בו עוד קצת. בואו למצוא את המקום שלכם.','מסעדות, בתי קפה ועגלות קפה, מאפיות, אוכל רחוב ומתוקים. כל המקומות ביבנה, עם כרטיס אישי ודרכי קשר.').replace('מסעדות דגים, בשרים, מטבח אסייתי ובתי קפה','מסעדות, בתי קפה, עגלות קפה, מאפיות ואוכל רחוב')
 html=html.replace('data-mood="sea"','data-mood="family"').replace('עם הפנים לים','משהו לאכול').replace('נוף, בריזה ושולחן טוב','מוצאים מקום לפי הטעם שלכם').replace('value="sea">עם נוף לים','value="family">ארוחה בעיר').replace('נבדק ב־19.10.2026','נבדק ב־'+payload['checked_at'])
 html=html.replace('ים אחד.','עיר אחת.').replace('דגים וים, מטבחים שעברו בין דורות','מטבחים שעברו בין דורות').replace('כל המקומות ביבנה, עם כרטיס אישי','מקומות ביבנה, עם כרטיס אישי').replace('<button type="button" data-service="saturday" aria-pressed="false">פתוח בשבת</button>','')
 hero=next((p for p in places if p['kind']=='coffee_carts' and p.get('image')),None) or next((p for p in places if p['kind']=='cafe' and p.get('image')),None) or next((p for p in places if p.get('image')),None)
 if hero:
  from html import escape
  photo='<div class="hero-photo"><img src="'+escape(hero['image'])+'" alt="'+escape(hero['name'])+' ביבנה" fetchpriority="high"><small>צילום: '+escape(hero['credit'])+'</small></div>'
 else:photo='<div class="hero-photo hero-typography"><span>YAVNE / FOOD</span><strong>הטעמים<br>של יבנה.</strong><small>קפה של בוקר. ארוחה טובה. משהו מתוק.</small></div>'
 html=re.sub(r'<div class="hero-photo">[\s\S]*?</div>',lambda _:photo,html,count=1)
 css=(MASTER/'restaurants.css').read_text()+'''\n.food-no-photo{height:100%;min-height:220px;display:flex;flex-direction:column;justify-content:center;align-items:center;padding:25px;background:radial-gradient(ellipse at 15% 0,#997d4d33,transparent 70%),#252b24;text-align:center;color:#e5cf9e}.food-no-photo span{font-size:13px;color:#c8bdae;margin-bottom:12px}.food-no-photo strong{font-size:29px;line-height:1.4}.hero-typography{background:radial-gradient(ellipse at 10% 100%,#a57d3c55,transparent 70%),#283027;display:flex;flex-direction:column;justify-content:center;padding:8%;color:#f2ddb2}.hero-typography strong{font-size:clamp(56px,7vw,105px);line-height:1.1;font-weight:900}.hero-typography>span{letter-spacing:.2em;font-size:14px;margin-bottom:30px}.hero-typography>small{position:static;margin-top:30px}.food-media{overflow:hidden}.chips{scrollbar-width:thin}@media(max-width:650px){.hero-typography{min-height:330px}.food-no-photo{min-height:190px}}\n'''
 (DEST/'restaurants.js').write_text(js);(DEST/'restaurants.css').write_text(css)
 for filename,text in [('restaurants.js',js),('restaurants.css',css)]:
  digest=hashlib.sha256(text.encode()).hexdigest()[:12];html=re.sub(filename.replace('.','\\.')+r'\?v=[^" ]+',filename+'?v='+digest,html)
 (DEST/'restaurants.html').write_text(html)
 print('Yavne culinary edition:',len(places),'places;',sum(bool(p.get('image')) for p in places),'local photos')
if __name__=='__main__':build()
