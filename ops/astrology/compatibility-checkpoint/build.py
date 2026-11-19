from ad_slots import ad_head, ad_slot
from compatibility import build_compatibility
from datetime import datetime
from zoneinfo import ZoneInfo
from editions import load_editions, forecast_html
from html import escape
import json
from pathlib import Path
import shutil

root = Path(__file__).resolve().parent
dist = root / "dist"
base = "/astrology/"
source = "https://ashdodnet.com/מגזין/אסטרולוגיה"
signs = json.loads((root / "content.json").read_text())
title = "עולם האסטרולוגיה שלך"
guides = [
    ("sun-moon-rising", "שמש, ירח ואופק", "במסורת המערבית, מזל השמש מתייחס למיקום השמש בגלגל המזלות בשעת הלידה. מזל הירח מתייחס למיקום הירח, שנע מהר יותר. האופק הוא נקודת המפגש של מישור המילקה עם האופק המזרחי, ולכן חישובו תלוי בשעה ובמקום.", "בקריאה אסטרולוגית נהוג לקשר את השמש לזהות, את הירח להרגלים רגשיים ואת האופק לאופן שבו אדם פוגש את סביבתו. אפשר להשתמש בהבחנה הזאת כנקודת מוצא לשאלות על שלוש החוויות הללו."),
    ("birth-chart", "איך קוראים מפת לידה", "מפת לידה מסמנת מיקומים שמימיים לפי זמן ומקום נתונים. התחילו בזיהוי מזל השמש והירח. לאחר מכן, אם ידועה שעת הלידה, בדקו את האופק ואת חלוקת הבתים.", "היבט הוא זווית בין שתי נקודות במפה. בתי המפה תלויים גם בשיטת החלוקה שנבחרה. כאשר השעה חסרה כדאי לסמן במפורש את החלקים שתלויים בה ולהשאיר אותם פתוחים."),
    ("mercury", "מהי נסיגת מרקורי", "בפרקי זמן מסוימים נראה מכדור הארץ שמרקורי משנה זמנית את כיוון תנועתו ביחס לכוכבי הרקע. התנועה הנראית נובעת מהמיקום היחסי של שני כוכבי הלכת במסלוליהם.", "המסורת האסטרולוגית מקשרת את מרקורי לתקשורת ולתנועה. אפשר לקרוא את הרעיון כהזמנה מעשית לעבור על פרטים ולוודא שהצד השני הבין את הכוונה."),
    ("tarot", "טארוט למתחילים", "בקריאה נפוצה בטארוט מבחינים בין הארקנה הגדולה, שבה דמויות וסמלים כמו הקוסם והכוהנת הגדולה, לבין ארבע סדרות הקלפים הקטנים. בקריאה להתבוננות אפשר להתחיל בתיאור מה שרואים בקלף לפני שבוחרים משמעות.", "בחרו שאלה פתוחה, למשל מה חסר לי כדי להתקדם בשיחה הזו. אם עולה קלף השוטה, נסו לזהות בתמונה גם סקרנות וגם סיכון. כתבו אפשרות אחת שכדאי לבדוק וצעד מעשי שאפשר לנקוט."),
    ("numerology", "נומרולוגיה למתחילים", "בכמה מסורות נומרולוגיות מצמצמים את סכום ספרות תאריך הלידה למספר חד־ספרתי. למשל, בתאריך הדמיוני 14.5.1990 הסכום הוא 29, אחר כך 11 ולבסוף 2. יש שיטות שעוצרות ב־11 או ב־22 ומייחסות להם פירוש נפרד.", "בפרשנות נפוצה, 2 משמש סמל לשיתוף פעולה. אפשר להפוך אותו לשאלה מעשית: באיזו החלטה השבוע חשוב לי לשתף אדם נוסף, ואיזו החלטה אני מעדיף לקבל בעצמי?")
]
options = "".join(f'<option value="{i}">{row[1]}</option>' for i,row in enumerate(signs))

def page(slug, heading, intro, content, kicker="אשדוד נט · מגזין", *, sign_hero="", canonical=""):
    compass_link = "" if slug.startswith("compatibility/") else f'<a href="{base}compass/">המצפן האישי</a>'
    canonical_tag = f'<link rel="canonical" href="{escape(canonical, quote=True)}">' if canonical else ""
    path = dist / "astrology" / slug
    path.mkdir(parents=True, exist_ok=True)
    (path / "index.html").write_text(f"""<!doctype html>
<html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
{canonical_tag}<meta name="robots" content="noindex, nofollow"><meta name="description" content="{escape(intro, quote=True)}">
<title>{escape(heading)}{'' if heading == title else ' | ' + title}</title><link rel="stylesheet" href="{base}style.css"><script defer src="{base}app.js"></script>{ad_head('class="adsbygoogle"' in content)}</head>
<body><a class="skip" href="#main">דילוג לתוכן</a><header><div class="bar"><a class="brand" href="{base}">✦ {title}</a><nav aria-label="ניווט ראשי"><a href="{base}#signs">המזלות</a><a href="{base}compatibility/">התאמה זוגית</a>{compass_link}<a href="{base}#guides">מדריכים</a></nav></div></header>
<main id="main" class="{'astro-landing' if not slug else 'sign-page' if sign_hero else ''}">{sign_hero or f'<section class="hero"><div class="hero-inner"><small>{kicker}</small><h1>{escape(heading)}</h1><p>{escape(intro)}</p></div></section>'}<div class="body">{content}</div></main>
<footer><a href="{base}">{title}</a><p>התוכן מבוסס על מסורות אסטרולוגיות ומיועד לבידור ולהתבוננות אישית.</p></footer></body></html>""")

weekly = f'<aside class="feature"><small>אשדוד נט</small><h2>התחזית השבועית של עוזי הכהן</h2><p>התחזית המקורית בשיטת התרולוגיה וקלפי הטארוט.</p><a class="button" href="{source}">לתחזית באשדוד נט ←</a></aside>'
guide_cards = "".join(f'<a class="card" href="{base}guides/{slug}/"><strong>{name}</strong></a>' for slug,name,*_ in guides)
editions = load_editions(root / "editions.json", {row[0] for row in signs})
today = datetime.now(ZoneInfo("Asia/Jerusalem")).date()
labels = [("love","אהבה, זוגיות ונישואים"),("dating","פנויים ופנויות"),("career","עבודה וקריירה"),("money","כסף והרגלים"),("family","משפחה וחברים"),("reflection","התפתחות אישית")]

def sign_links(anchor):
    return "".join(f'<a href="{base}{slug}/#{anchor}">{name}</a>' for slug,name,*_ in signs)

daily_dates = [start for period,start in editions if period == "daily" and start <= today]
newest = max(daily_dates, default=None)
date_line = ""
if newest:
    status = " · מהדורה קודמת" if newest < today else ""
    date_line = f'<p class="landing-date"><time datetime="{newest}">{newest:%d.%m.%Y}</time>{status}</p>'

sign_cards = "".join(
    f'<a class="landing-sign" href="{base}{slug}/{"#forecast-daily" if newest else ""}">'
    f'<img src="{base}sign-art/{slug}.jpg" width="384" height="341" loading="lazy" alt="">'
    f'<span><strong>{name}</strong><small>{element} · {ruler}</small></span></a>'
    for slug,name,_,element,ruler,*_ in signs
)
topics = "".join(f'<details class="topic"><summary>{label}</summary><div class="topic-signs">{sign_links(anchor)}</div></details>'
                 for anchor,label in labels)
landing_hero = f'''<section class="landing-hero">
  <div class="landing-hero__inner">
    <div class="landing-hero__copy">
      <p class="landing-hero__eyebrow">אשדוד נט · אסטרולוגיה</p>
      <h1>עולם האסטרולוגיה <em>שלך</em></h1>
      <p>תחזיות ל־12 המזלות, אהבה והתאמה זוגית, מצפן אישי ומדריכים.</p>
      <nav aria-label="כניסות למדור">
        <a class="button" href="#daily">{"לתחזית היומית" if newest else "לבחירת מזל"} ←</a>
        <a class="landing-secondary" href="#weekly">התחזית של עוזי הכהן ←</a>
      </nav>
    </div>
    <img src="{base}zodiac-wheel.jpg" alt="" width="1100" height="733" fetchpriority="high">
  </div>
</section>'''
page("", title, "תחזיות ל־12 המזלות, אהבה והתאמה זוגית, מצפן אישי ומדריכים.",
     '<nav class="landing-nav" aria-label="ניווט במדור"><a href="#signs">12 המזלות</a><a href="#weekly">עוזי הכהן</a><a href="#tools">כלים אישיים</a><a href="#topics">נושאי המדור</a><a href="#guides">מדריכים</a></nav>'
     + f'<section id="daily"><div id="signs" class="landing-heading"><h2>{"ההורוסקופ היומי" if newest else "12 המזלות"}</h2>{date_line}</div><div class="landing-signs">{sign_cards}</div></section>{ad_slot("astrology-landing")}'
     + f'<section id="weekly">{weekly}</section>'
     + f'<section id="tools"><h2>הכלים האישיים</h2><div class="links landing-tools"><a class="card" href="{base}rising/"><strong>מחשבון אופק</strong><small>קריאה אישית לפי זמן ומקום הלידה</small></a><a class="card" href="{base}compatibility/"><strong>אהבה והתאמה זוגית</strong><small>בחרו שני מזלות</small></a><a class="card" href="{base}compass/"><strong>המצפן האישי שלי</strong><small>תרגיל אישי להתבוננות</small></a><a class="card" href="{base}guides/birth-chart/"><strong>איך קוראים מפת לידה</strong><small>מדריך לקריאת המפה</small></a></div></section>'
     + f'<section id="topics"><h2>אסטרולוגיה בחיי היומיום</h2><div class="links">{topics}</div></section>'
     + f'<section id="guides"><h2>מדריכי אסטרולוגיה</h2><div class="links">{guide_cards}</div></section>',
     sign_hero=landing_hero)
art = root / "sign-art"
if art.is_dir():
    shutil.copytree(art, dist / "astrology" / "sign-art", dirs_exist_ok=True)

for slug,name,symbol,element,ruler,profile,*sections in signs:
    details = "".join(f'<article id="{anchor}"><h2>{label}</h2><p>{value}</p></article>' for (anchor,label),value in zip(labels,sections,strict=True))
    forecast = forecast_html(editions, slug, today, ad_slot("astrology-forecast"))
    period_links = "".join(f'<a href="#forecast-{period}">{label}</a>'
                           for period,label in (("daily","יומית"),("weekly","שבועית"),("monthly","חודשית"))
                           if f'id="forecast-{period}"' in forecast)
    hero = f'''<section class="zodiac-hero" data-element="{element}">
      <div class="zodiac-hero__inner">
        <div class="zodiac-hero__copy">
          <a class="zodiac-hero__back" href="{base}#signs">גלגל המזלות ←</a>
          <h1>מזל {name}</h1>
          <p>{escape(profile)}</p>
          <dl><div><dt>יסוד</dt><dd>{element}</dd></div><div><dt>שליט</dt><dd>{ruler}</dd></div></dl>
        </div>
        <figure><img src="{base}sign-art/{slug}.jpg" alt="איור אסטרולוגי של מזל {name}" width="384" height="341" fetchpriority="high"></figure>
      </div>
    </section>'''
    jump = f'<nav class="zodiac-jump" aria-label="ניווט בתחזיות"><strong>התחזית שלך</strong>{period_links}<a href="#life-topics">אהבה, קריירה ועוד</a></nav>'
    discover = f'''<aside class="zodiac-discover" aria-label="עוד בעולם האסטרולוגיה שלך">
      <div><h2>עולם האסטרולוגיה שלך</h2><p>תחזיות לכל המזלות, התאמה זוגית, המצפן האישי ומדריכי אסטרולוגיה.</p></div>
      <a class="button" href="{base}">כניסה לעולם האסטרולוגיה <span aria-hidden="true">←</span></a>
    </aside>'''
    page(slug + "/", f"מזל {name}", profile, f'{jump}<div class="zodiac-editions">{forecast}</div><section id="life-topics"><h2>אסטרולוגיה בחיי היומיום</h2><div class="links">{details}</div></section>{weekly}<section><h2>לגלות עוד</h2><div class="links"><a href="{base}compatibility/?sign={slug}">התאמה עם מזל {name} ←</a><a href="{base}guides/birth-chart/">מדריך לקריאת מפת לידה ←</a><a href="{base}rising/">מחשבון אופק ←</a></div></section>{discover}', sign_hero=hero)

def guide_body(paragraphs):
    return "".join(f"<p>{escape(paragraph)}</p>" for paragraph in paragraphs)


for index, (slug, name, *paragraphs) in enumerate(guides):
    following = guides[index + 1:] + guides[:index]
    next_articles = "".join(
        f'<article class="reader-next"><p class="facts">הכתבה הבאה</p>'
        f'<h2>{escape(next_name)}</h2>{guide_body(next_paragraphs)}'
        f'<a href="{base}guides/{next_slug}/" aria-label="קישור ישיר לכתבה {escape(next_name, quote=True)}">קישור לכתבה</a></article>'
        for next_slug, next_name, *next_paragraphs in following
    )
    page(f"guides/{slug}/", name, "מדריכי עולם האסטרולוגיה שלך",
         f'<article>{guide_body(paragraphs)}</article><section class="reader-flow" aria-label="המשך קריאה">{next_articles}</section>')

build_compatibility(page, root, base, signs)
for name in ("compatibility.mjs", "compatibility.css"):
    shutil.copy(root / name, dist / "astrology")
page("compass/","המצפן האישי שלי","בחרו תחום להתבוננות וקחו ממנו צעד מעשי לשבוע הקרוב.",'<form id="compass"><label>תחום להתבוננות<select id="topic"><option>הרגלים</option><option>יחסים</option><option>עבודה</option></select></label><button type="submit">לקבלת תרגיל</button></form><article id="result" aria-live="polite" hidden></article>')
page("rising/", "מחשבון אופק", "גלו מהו מזל האופק שלכם וקראו פרשנות אישית על הדרך שבה אתם ניגשים לאנשים ולמצבים חדשים.", (root / "rising.html").read_text())
shutil.copy(root / "rising.mjs", dist / "astrology")
shutil.copy(root / "style.css", dist / "astrology")
shutil.copy(root / "app.js", dist / "astrology")
(dist / "astrology" / "signs.json").write_text(json.dumps([s[:4] for s in signs],ensure_ascii=False))
(dist / "index.html").write_text('<!doctype html><html lang="he" dir="rtl"><meta charset="utf-8"><meta name="robots" content="noindex,nofollow"><meta http-equiv="refresh" content="0;url=/astrology/"><title>עולם האסטרולוגיה שלך</title><a href="/astrology/">לעולם האסטרולוגיה שלך</a></html>')
(dist / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
