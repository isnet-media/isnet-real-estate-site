from html import escape
from itertools import combinations_with_replacement
from urllib.parse import quote, urlencode
import json

HEADINGS = (
    "אהבה ורומנטיקה", "תקשורת והבנה", "משיכה וכימיה", "אמון ויציבות",
    "נקודות חיכוך ואתגרים", "סיכום ההתאמה"
)
TITLE = "התאמה זוגית לפי מזלות"
INTRO = "בחרו שני מזלות וגלו איך האהבה, הרגלי השיחה והצרכים שלכם עשויים להיפגש."
CANONICAL = "https://isnet.co.il/astrology/compatibility/"


def pair_key(first, second):
    return '-'.join(sorted((first, second)))


def build_compatibility(page, root, base, rows):
    by_slug = {row[0]: row for row in rows}
    data_file = root / "compatibility-pairs.json"
    pairs = json.loads(data_file.read_text())
    required = {pair_key(left, right) for left, right in combinations_with_replacement(by_slug, 2)}
    if set(pairs) != required:
        raise ValueError(f"Compatibility pairs missing {required-set(pairs)} or unexpected {set(pairs)-required}")

    def form(first="", second=""):
        def field(name, label, selected):
            options = "".join(
                f'<option value="{slug}"{" selected" if slug==selected else ""}>{escape(name)}</option>'
                for slug,name,*_ in rows
            )
            return (f'<label for="{name}">{label}'
                    f'<select name="{name}" id="{name}" required><option value="">בחרו מזל</option>'
                    f'{options}</select></label>')
        return (f'<form class="match-form" id="match-form" action="{base}compatibility/">'
                f'{field("first","המזל שלך",first)}{field("second","המזל השני",second)}'
                '<button class="button" type="submit">גלו את ההתאמה שלכם</button></form>'
                '<p class="match-status" role="status" hidden></p>')

    def sign_card(slug):
        _,name,symbol,element,*_ = by_slug[slug]
        return (f'<div class="match-sign-card" data-element="{escape(element)}">'
                f'<img src="{base}sign-art/{slug}.jpg" alt="" width="384" height="341">'
                f'<div><span aria-hidden="true">{escape(symbol)}&#xfe0e;</span>'
                f'<h3>{escape(name)}</h3><p>יסוד {escape(element)}</p></div></div>')

    def content(key, first, second):
        headline, opening, takeaway, sections = pairs[key]
        if not all(isinstance(value,str) and value.strip() for value in (headline,opening,takeaway)):
            raise ValueError(f"Missing editorial copy for {key}")
        if len(sections)!=len(HEADINGS) or any(len(parts)!=2 or not all(parts) for parts in sections):
            raise ValueError(f"Missing topic copy for {key}")
        names = [by_slug[slug][1] for slug in (first, second)]
        share_text = f"ההתאמה האסטרולוגית בין {names[0]} ל{names[1]}\n{CANONICAL}{key}/"
        share_href = 'https://wa.me/?' + urlencode({'text':share_text},quote_via=quote)
        details = "".join(
            f'<details class="match-topic"><summary>{topic}</summary>'
            f'<p>{escape(body)}</p><p class="match-takeaway"><strong>{escape(point)}</strong></p></details>'
            for topic,(body,point) in zip(HEADINGS, sections, strict=True)
        )
        return (
            f'<section class="match-result" id="match-result" data-pair="{key}" aria-labelledby="match-title">'
            f'<p class="match-edition">ישראל נט · אסטרולוגיה</p>'
            f'<h2 id="match-title" tabindex="-1">{escape(headline)}</h2><p class="match-opening">{escape(opening)}</p>'
            f'<div class="match-cards">{sign_card(first)}{sign_card(second)}</div>'
            f'<p class="match-qualifier">{escape(takeaway)}</p>'
            f'<div class="match-topics">{details}</div>'
            f'<div class="match-actions"><a class="button match-reset" href="{base}compatibility/">בדקו שילוב אחר</a>'
            f'<a class="button match-share" href="{escape(share_href, quote=True)}" target="_blank" rel="noopener noreferrer">שיתוף בוואטסאפ</a></div></section>'
        )

    def document(slug, selected=("", ""), result='<div id="match-result" hidden></div>', heading=TITLE, canonical=CANONICAL):
        hero = (f'<section class="hero match-hero"><div class="hero-inner">'
                f'<p>ישראל נט · עולם האסטרולוגיה שלך</p><h1>{TITLE}</h1><p>{INTRO}</p></div></section>')
        body = (f'<link rel="stylesheet" href="{base}compatibility.css"><div class="match-page">{form(*selected)}{result}'
                '<p class="match-disclaimer">הקריאה מציעה זווית אסטרולוגית להתבוננות ולשיחה. טיב הקשר נבנה גם מתוך הבחירות והנסיבות שלכם.</p></div>'
                f'<script type="module" src="{base}compatibility.mjs"></script>')
        page(slug, heading, INTRO, body, sign_hero=hero, canonical=canonical)

    document("compatibility/")
    for left,right in combinations_with_replacement(by_slug, 2):
        first,second = sorted((left,right))
        key = pair_key(first,second)
        document(f"compatibility/{key}/", (first,second), content(key,first,second),
                 pairs[key][0], f"{CANONICAL}{key}/")
        if first != second:
            alias = root / "dist" / "astrology" / "compatibility" / f"{second}-{first}"
            alias.mkdir(parents=True,exist_ok=True)
            (alias/"index.html").write_text(
                '<!doctype html><html lang="he" dir="rtl"><meta charset="utf-8">'
                f'<link rel="canonical" href="{CANONICAL}{key}/">'
                f'<meta http-equiv="refresh" content="0;url={base}compatibility/{key}/">'
                f'<title>{escape(pairs[key][0])}</title><a href="{base}compatibility/{key}/">לתוצאת ההתאמה</a></html>'
            )
