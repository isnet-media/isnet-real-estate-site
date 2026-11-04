#!/usr/bin/env python3
"""Apply city search metadata after generators; index only explicit public routes."""
from pathlib import Path
import html, json, re
from xml.etree.ElementTree import Element, SubElement, tostring
from bs4 import BeautifulSoup
ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://isnet.co.il'
SUPERS = {'ASHDOD':'אשדוד','YAVNE':'יבנה','KGAT':'קריית גת','RISHON':'ראשון לציון','HOLON':'חולון','BATYAM':'בת ים'}
EVENTS = {'ashdod':'אשדוד','yavne':'יבנה','kiryat-gat':'קריית גת','rishon-lezion':'ראשון לציון','holon':'חולון','herzliya':'הרצליה'}
SUPER_TOPICS = {'index.html':'השוואת מחירי סופר', 'compare/index.html':'השוואת מחירי מוצרים בסופר', 'deals/index.html':'מבצעים בסופר', 'smart-shopping/index.html':'קנייה חכמה וחיסכון בסופר', 'recipes/index.html':'מתכונים חסכוניים למשפחה'}
EVENT_TOPICS = {'index.html':'אירועים ובילויים', 'kids.html':'פעילויות לילדים', 'seniors.html':'פעילויות לגמלאים', 'restaurants.html':'מסעדות ובתי קפה', 'saturday.html':'מה פתוח בשבת', 'cinema.html':'סרטים וקולנוע', 'attractions.html':'אטרקציות ומקומות בילוי'}
START='<!-- LOCAL_SEARCH_START -->'; END='<!-- LOCAL_SEARCH_END -->'
def url(path):
    rel=path.relative_to(ROOT).as_posix()
    return ORIGIN+'/'+(rel[:-10] if rel.endswith('index.html') else rel)
def apply(path, title, desc, links=None):
    raw=path.read_text(); match=re.search(r'<head\b[^>]*>(.*?)</head>',raw,re.S|re.I)
    if not match: raise ValueError(f'Missing head: {path}')
    head=BeautifulSoup(match.group(0),'html.parser').head
    for tag in list(head.select('title,meta[name="description"],meta[name="robots"],meta[name="googlebot"],link[rel="canonical"],meta[property="og:title"],meta[property="og:description"],meta[property="og:url"],script#localSearchSchema')): tag.decompose()
    for node in list(head.contents):
        if isinstance(node,str) and not node.strip(): node.extract()
    for name,attrs,text in [('title',{},title),('meta',{'name':'description','content':desc},None),('meta',{'name':'robots','content':'index,follow,max-image-preview:large'},None),('link',{'rel':'canonical','href':url(path)},None),('meta',{'property':'og:title','content':title},None),('meta',{'property':'og:description','content':desc},None),('meta',{'property':'og:url','content':url(path)},None)]:
        tag=BeautifulSoup('', 'html.parser').new_tag(name,attrs=attrs)
        if text: tag.string=text
        head.append(tag)
    schema=BeautifulSoup('','html.parser').new_tag('script',attrs={'id':'localSearchSchema','type':'application/ld+json'})
    schema.string=json.dumps({'@context':'https://schema.org','@type':'CollectionPage','url':url(path),'name':title,'description':desc,'inLanguage':'he'},ensure_ascii=False).replace('<','\\u003c');head.append(schema)
    raw=raw[:match.start()]+str(head)+raw[match.end():]
    raw=re.sub(re.escape(START)+'.*?'+re.escape(END),'',raw,flags=re.S)
    if links:
        section=START+'<section aria-label="מדריכים מקומיים" style="max-width:1188px;margin:28px auto;padding:20px;line-height:1.8;font-size:17px"><h2>'+html.escape(title)+'</h2><p>'+html.escape(desc)+'</p><nav aria-label="מדריכים בעיר" style="display:flex;flex-wrap:wrap;gap:12px">'+''.join('<a href="'+html.escape(href,quote=True)+'">'+html.escape(label)+'</a>' for href,label in links)+'</nav></section>'+END
        # Place outside app view containers so the crawl path stays visible.
        pos=re.search(r'<footer\b',raw,re.I) or re.search(r'</body>',raw,re.I)
        if not pos: raise ValueError(f'Missing body: {path}')
        raw=raw[:pos.start()]+section+raw[pos.start():]
    path.write_text(raw)
    return url(path)
def build():
    urls=[]; report={}
    for code,city in SUPERS.items():
        folder=ROOT/('SUPER.'+code)
        pages=[(folder/rel,topic) for rel,topic in SUPER_TOPICS.items() if (folder/rel).exists() and '<head' in (folder/rel).read_text().lower()]
        guide=folder/'guides/save-on-groceries/index.html'
        guide.parent.mkdir(parents=True,exist_ok=True)
        guide_title='איך לחסוך בקניות בסופר ב'+city+'?'
        guide.write_text('<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+guide_title+'</title><style>body{margin:0;background:#fffdf8;color:#273c32;font:18px/1.8 Arial,sans-serif}header,main,footer{max-width:850px;margin:auto;padding:24px}a{color:#21664e}h1{font-size:clamp(28px,5vw,40px);line-height:1.3}h2{font-size:25px}nav{display:flex;flex-wrap:wrap;gap:18px}</style></head><body><header><a href="'+url(folder/'index.html')+'">מחירי הסופר ב'+city+'</a></header><main><h1>'+guide_title+'</h1><p>קנייה שבועית או סל קניות חודשי למשפחה? לפני שיוצאים לסופר ב'+city+', כדאי לבדוק את הרשימה כולה, את הכמויות ואת מחיר היחידה. כך ההשוואה מתאימה למה שבאמת צריך בבית.</p><h2>איפה הכי זול לקנות ב'+city+'?</h2><p>אין סניף שהוא בהכרח הזול ביותר לכל רשימה. השוו סל קניות זהה בין הסניפים שנקלטו בעיר, בדקו את תאריכי המקור ואת מספר המוצרים שיש להם מחיר. סל שחסרים בו מוצרים אינו בר השוואה לסל מלא.</p><h2>השוואת סל קניות משפחתי</h2><p>בנו רשימה שכוללת מזון, ניקיון והיגיינה לפי הצריכה בבית. בקנייה חודשית הכפילו בכמויות שמתכננים לקנות בפועל. הפרש קטן במוצר שקונים כמה פעמים עשוי להשפיע על הסכום הכולל.</p><h2>איך לחסוך בקניות בסופר בלי לקנות יותר?</h2><p>בדקו מה כבר יש במקרר ובמזווה, תכננו ארוחות והכינו רשימת קניות לפני היציאה. השוו מחיר לקילוגרם או לליטר לצד מחיר האריזה; אריזה גדולה מועילה רק אם תשתמשו בתכולה.</p><h2>מבצעים בסופר: מה צריך לבדוק?</h2><p>קראו את תנאי המבצע: כמות מינימלית, חברות מועדון, תוקף וסניפים משתתפים. חשבו כמה תשלמו על הכמות שאתם צריכים. מבצע של כמה יחידות לא בהכרח חוסך כסף אם חלקן לא ישמשו אתכם.</p><h2>מותג פרטי וחלופות זולות</h2><p>אפשר לבדוק חלופה למוצר קבוע, ולהשוות גודל אריזה, רכיבים, כשרות והתאמה לבית. מחיר נמוך אינו מעיד כשלעצמו על איכות זהה. התחילו במוצר אחד ובדקו אם הוא מתאים לכם.</p><h2>חיסכון באוכל למשפחה</h2><p>תכננו כמה ארוחות שמשתמשות באותם מצרכים וקנו בהתאם למספר הסועדים. במתכונים החכמים תוכלו לעיין במרכיבים ובהוראות הכנה ולהחליט מה מתאים לתקציב שלכם.</p><p>ההשוואה באתר מוגבלת לסניפים ולמוצרים שנקלטו. מחירי המקור אינם הבטחת מלאי או מחיר בקופה, ואין הבטחה לסכום חיסכון קבוע.</p></main><footer></footer></body></html>')
        pages.append((guide,'איך לחסוך בקניות בסופר'))
        links=[(url(path),topic+' ב'+city) for path,topic in pages]
        for path,topic in pages:
            title=(topic+' ב'+city+' וחיסכון בקניות') if path.parent==folder else topic+' ב'+city+' | מחירי הסופר'
            desc='איפה כדאי לקנות ב'+city+'? השוואת מחירי מוצרים וסלי קניות בין סניפי הסופר בעיר, מבצעים וקנייה חכמה. תאריכי המקור והכיסוי מוצגים באתר; מחיר מדווח אינו הבטחת מלאי.' if path.name=='index.html' and path.parent==folder else topic+' ב'+city+' — בדקו את האפשרויות לפני הקנייה. מחירים וכיסוי לפי הנתונים שנקלטו, עם תאריכי מקור ותנאי ההשוואה באתר.'
            urls.append(apply(path,title,desc,links if path.parent==folder else None))
        report[folder.name]=len(pages)
    for slug,city in EVENTS.items():
        folder=ROOT/'events-preview'/slug
        pages=[(folder/rel,topic) for rel,topic in EVENT_TOPICS.items() if (folder/rel).exists() and '<head' in (folder/rel).read_text().lower()]
        links=[(url(path),topic+' ב'+city) for path,topic in pages if path.name!='index.html']
        # Existing static category pages already enforce publication and expiry rules.
        manifest=folder/'data/seo-index.json'
        if manifest.exists():
            for entry in json.loads(manifest.read_text()).get('pages',{}).values():
                if entry.get('indexable') and entry.get('count',0)>0: links.append((entry['url'],entry['title']))
        for path,topic in pages:
            title=('מה עושים ב'+city+'? אירועים, הופעות ופעילויות לילדים') if path.name=='index.html' else topic+' ב'+city+' | מה עושים בעיר'
            desc=('מחפשים מה לעשות ב'+city+'? לוח אירועים ובילויים בעיר: הופעות, הצגות, סטנדאפ, פעילויות לילדים ולגמלאים ומסעדות. בדקו מועדים, מקומות ופרטי הזמנה.') if path.name=='index.html' else topic+' ב'+city+' — מדריך מקומי לבילוי בעיר. בדקו את פרטי הפעילות, המיקום והמועדים; זמינות ושעות עשויות להשתנות.'
            urls.append(apply(path,title,desc,links if path.name=='index.html' else None))
        report[slug]=len(pages)
    sm=Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for item in sorted(set(urls)): SubElement(SubElement(sm,'url'),'loc').text=item
    (ROOT/'local-search-sitemap.xml').write_bytes(tostring(sm,encoding='utf-8',xml_declaration=True))
    robots=ROOT/'robots.txt';text=robots.read_text();line='Sitemap: '+ORIGIN+'/local-search-sitemap.xml'
    if line not in text: robots.write_text(text.rstrip()+'\n'+line+'\n')
    print(json.dumps({'pages':len(urls),'editions':report},ensure_ascii=False))
if __name__=='__main__': build()
