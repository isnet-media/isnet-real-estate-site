#!/usr/bin/env python3
"""Single-source ISNET events UI: Ashdod changes propagate to Rishon LeZion.

Ashdod's frontend is the canonical presentation template. Event data, cinema data,
sports data, local image assets, fallback configuration and places data remain
city-owned and are never copied. This only copies root-level HTML, CSS and JS.
"""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "events-preview"
MASTER = ROOT / "ashdod"
TARGETS = {
    "rishon-lezion": {
        "slug": "rishon-lezion",
        "name": "ראשון לציון",
        "brand": "ראשון נט",
        "website": "https://www.rishonet.com/",
        "second_cinema": "פלאנט",
        "second_cinema_id": "planet",
    },
}
FRONTEND_EXTENSIONS = {".html", ".css", ".js"}
SKIP_NAMES = {"site-seo.js", "seo-pages.css", "isnet-advertise.js", "restaurants.html", "restaurants.css", "restaurants.js", "dark-preview.html", "hero-international-preview.html", "ashdod-event-identities.js", "ashdod-analytics.js"}
HEAD_MARKER = "<!-- ISNET shared layout: edit the Ashdod source; synced automatically -->"
CSS_MARKER = "/* ISNET shared layout: edit events-preview/ashdod, not this generated file. */"
JS_MARKER = "// ISNET shared layout: edit events-preview/ashdod, not this generated file."


def localize(content: str, name: str, city: dict, suffix: str) -> str:
    # Ashdod's analytics bootstrap is also embedded in the app/event bundles.
    # A city edition must not inherit another publisher's measurement stream.
    content = re.sub(r'// Ashdod GA4: public event metadata only;[^\n]*\n\(function \(\) \{[\s\S]*?\n\}\)\(\);\n?', '', content, count=1)
    # The Ashdod courses partner link belongs only to the Ashdod edition.
    content = content.replace(
        "<a class=\"isnetNavSmall\" data-city-only=\"ashdod\" href=\"https://meusharim-ashdod-v1.ebs987449.chatgpt.site/\"><span aria-hidden=\"true\">▧</span><strong>חוגים והעשרה</strong></a>",
        "<a class=\"isnetNavSmall\" href=\"category.html?category=exhibition\"><span aria-hidden=\"true\">▧</span><strong>תערוכות</strong></a>",
    )
    # The culinary catalog is Ashdod-owned; do not relabel it for other cities.
    content = re.sub(r'<a\b[^>]*data-ashdod-culinary[^>]*>[\s\S]*?</a>', '', content)
    # The city has its own data and booking destinations. Share presentation only.
    content = content.replace(' data-city-only="ashdod"', '')
    content = re.sub(r'<script\b[^>]*src="(?:ashdod-event-identities|ashdod-analytics|isnet-advertise|site-seo)\.js[^" ]*"[^>]*></script>', '', content)
    content = content.replace('/ashdod/', '/' + city['slug'] + '/')
    content = content.replace(r'\/ashdod', r'\/' + city['slug'])
    content = content.replace('isnet-ashdod-', 'isnet-' + city['slug'] + '-')
    content = content.replace('publishedEvents?.(\"ashdod\")', 'publishedEvents?.(\"' + city['slug'] + '\")')
    content = content.replace("publishedEvents?.('ashdod')", "publishedEvents?.('" + city['slug'] + "')")
    # Shared, non-geographic illustration assets remain in the canonical bank.
    content = re.sub(r'(?<![A-Za-z0-9_./-])assets/(?!branding/)', '../ashdod/assets/', content)
    content = content.replace('assets/branding/what-to-do-ashdod', 'assets/branding/what-to-do-rishon')
    content = content.replace('assets/branding/ashdodnet-dark.svg', 'assets/branding/rishonet-dark.svg')
    # Local partner/catalogs never silently load Ashdod content.
    if name == 'site-search-chat.js':
        content = content.replace("if(/חוג|קורס/.test(raw)&&!payload.courses)", "if(false&&/חוג|קורס/.test(raw)&&!payload.courses)")
        content = content.replace('/meusharim/ashdod/data/classes.json', 'data/classes.json')
    if name == 'site-search-engine.js':
        content = content.replace("const groups=[", "const groups=[\n ['seniors','גמלאים',['גמלאים','גימלאים','גמלאי','ותיקים','הגיל השלישי'],['seniors','גמלאים','גימלאים','ותיקים','לגלות תרבות']],")
        content = content.replace("e.sport_branch].filter(Boolean)", "e.sport_branch,...(e.local_source_name==='htrl_adults'?['seniors']:[])].filter(Boolean)")
        content = content.replace("const s=norm(q).slice(0,500)", "const s=norm(q).replace(/(?:ב?ראשונ לציונ|ב?ראשלצ)/g,' ').trim().slice(0,500)")
    if name == 'saturday.js':
        content = content.replace('../rishon-lezion/data/', '../ashdod/data/')
        content = content.replace("_guideCity:'ראשון לציון',_guideBase:'../rishon-lezion/'", "_guideCity:'ASHDOD_NEARBY',_guideBase:'../ashdod/'")
        content = content.replace('אוכל בביג', 'אוכל במתחמי הבילוי')
    if name in ('attractions.html','attraction.html'):
        content = content.replace('new URL(x);', 'new URL(x,location.href);')
        content = content.replace('kind:assignKind(x)', 'kind:x.kind||assignKind(x)')
        content = content.replace('audiences:["kids","adults"]', 'audiences:x.audiences||["kids","adults"]')
        content = content.replace('...normalizePlaces(places),', '...normalizePlaces(places).filter(x=>!(extra.verified_sources||[]).some(y=>y.id===x.id)),')
    if name == 'seniors-hub.js':
        content = content.replace('סדרת החיים הטובים ומופעים', 'תרבות, הצגות ומוזיקה בעיר')
        for old,new in [('בוקר של תרבות במשכן','לגלות תרבות בראשון'),('סדרת החיים הטובים','מופעים ומפגשים קרובים'),('על הסדרה במשכן','ללוח לגלות תרבות'),('באתר המשכן','באתר המארגן')]:
            content = content.replace(old,new)
        content = content.replace("cultureCatalog.programs.find(p=>", "cultureCatalog.programs.find(p=>(p.event_ids||[]).includes(e.event_id)||")
        content = content.replace("צילום: '+esc(p.image_credit)", "'+esc(p.image_credit)")
        content = content.replace("e.category==='seniors'||adultLecture(e)", "e.category==='seniors'||e.audiences?.includes('seniors')||adultLecture(e)")
        content = content.replace("return e.category==='lecture'?'senior-lectures':topics[e.subcategory]?e.subcategory:'other';", "return e.category==='lecture'?'senior-lectures':topics[e.subcategory]?e.subcategory:({tour:'senior-trips',workshop:'senior-workshops',music:'senior-music',theatre:'senior-culture',cinema:'senior-culture',community:'senior-social'}[e.category]||'other');")
        links = __import__('json').loads((ROOT / city['slug'] / 'data/senior-guide.json').read_text())['links']
        cards = '<section class=\"snExplore\"><div class=\"snSectionHead\"><h2>קהילה ותרבות לגמלאים בראשון לציון</h2></div><nav class=\"snExploreGrid\">' + ''.join('<a class=\"snExploreLink\" href=\"'+r['url']+'\" target=\"_blank\" rel=\"noopener\"><span><strong>'+r['title']+'</strong><small>'+r['description']+'</small></span><span aria-hidden=\"true\">↗</span></a>' for r in links) + '</nav></section>'
        content = content.replace('activities.after(discovery);', 'activities.after(discovery);discovery.insertAdjacentHTML(\"afterbegin\",'+__import__('json').dumps(cards,ensure_ascii=False)+');')
    if name == 'kids-hub.js':
        guide = __import__('json').loads((ROOT / city['slug'] / 'data/family-guide.json').read_text())
        content = re.sub(r'(function familyGuide\(\)\{\s*const sources=)\[[\s\S]*?\n \];', lambda m:m[1]+__import__('json').dumps(guide['links'],ensure_ascii=False)+';', content)
        content = content.replace('מופע חנוכה לילדים ולמשפחות במשכן לאמנויות הבמה באשדוד.', 'מופע חנוכה לילדים ולמשפחות. פרטי האולם וההשתתפות בעמוד האירוע.')
        content = content.replace("const ageText=age.length===2?", "const ageText=e.age_text?clean(e.age_text):age.length===2?")
    if name in ('kids-hub.js','seniors-hub.js'):
        content = content.replace('[e.source_description,e.description,e.series_description]', '[e.editorial_description,e.description,e.series_description,e.source_description]')
    if name == 'category-landing.js' and not (ROOT / city['slug'] / 'data/exhibitions-magazine.json').is_file():
        # A city without a curated exhibition catalog uses its own event list.
        # Do not launch Ashdod's museum magazine with missing city data.
        content = '\n'.join(line for line in content.split('\n') if 'window.ISNET_EXHIBITIONS.init()' not in line)
    if name == 'category.html' and (ROOT / city['slug'] / 'data/exhibitions-magazine.json').is_file():
        # City-owned catalog and renderer; never relabel another city's museums.
        content = re.sub(r'category-landing\.js\?v=[^\"\' ]+', 'category-landing.js?v=20261016-rishon-exhibitions2', content)
        asset = ROOT / city['slug'] / 'rishon-exhibitions.js'
        digest = hashlib.sha256(asset.read_bytes()).hexdigest()[:12]
        content = content.replace('<script src="category-landing.js', '<script src="rishon-exhibitions.js?v=' + digest + '" defer></script>\n<script src="category-landing.js')
    if name == 'index.html':
        # Geography-specific photography must not be relabeled as another city.
        def local_discovery(m):
            card=m[0]
            kind='culture' if 'category=culture' in card else 'park' if 'category=parks' in card else 'beach' if 'category=beaches' in card else 'attraction' if 'attractions.html' in card else 'nature' if 'category=nature' in card else 'city'
            import json
            places=json.loads((ROOT/city['slug']/'data/places.json').read_text())['categories']
            key={'park':'parks','beach':'beaches','attraction':'attractions','city':'must-see'}.get(kind,kind)
            image=places[key]['hero_image']
            card=re.sub(r'<img src="[^"]+"',lambda _: '<img src="'+image+'"',card)
            from html import escape
            credit=escape(places[key].get('hero_credit','מקור: ראשון נט'))
            alt=escape(places[key].get('hero_alt',places[key]['title']),quote=True)
            card=re.sub(r'(<img[^>]* alt=")[^"]*',lambda m:m[1]+alt,card)
            return re.sub(r'(<small class="cityDiscover__credit">)[\s\S]*?(</small>)',lambda m:m[1]+credit+m[2],card)
        content=re.sub(r'<a class="cityDiscover__card"[\s\S]*?</a>',local_discovery,content)
    # These are authored interface strings. Source data is NOT changed.
    content = content.replace("https://ashdodnet.com/", city["website"])
    content = content.replace("https://ashdodnet.com", city["website"].rstrip("/"))
    content = content.replace("אשדוד נט", city["brand"])
    content = content.replace("אשדוד", city["name"])
    content = content.replace('ASHDOD_NEARBY', 'אשדוד')
    # CMS city identifiers are ASCII slugs and must be localized explicitly.
    # Otherwise the Rishon public board silently fetches Ashdod CMS events.
    if suffix == ".js":
        content = content.replace('publishedEvents?.("ashdod")',
                                  'publishedEvents?.("' + city["slug"] + '")')
    # Cinema venues are city-specific. Preserve IDs on the canonical Ashdod site.
    content = content.replace("HOT Cinema", city["second_cinema"])
    content = content.replace('data-cinema="hot-cinema"', 'data-cinema="' + city["second_cinema_id"] + '"')
    content = content.replace('data-venue="hot-cinema"', 'data-venue="' + city["second_cinema_id"] + '"')
    content = content.replace('id==="hot-cinema"', 'id==="' + city["second_cinema_id"] + '"')
    # Avoid hardcoded dates on JS/CSS bundle URLs: the deployment adds fresh HTML
    # every time the Ashdod source changes.
    if suffix == ".html":
        def cache_bust(match):
            filename = match.group(1)
            src = MASTER / filename
            if not src.is_file():
                return filename
            localized = localize(src.read_text(encoding="utf-8"), filename, city, src.suffix)
            digest = hashlib.sha256(localized.encode("utf-8")).hexdigest()[:12]
            return filename + "?v=" + digest
        content = re.sub(
            r"\b((?:pilot/)?(?:(?:app|event|places|movie|cinema)\.js|(?:styles|event|places|movie|cinema|publisher-brand)\.css))(?:\?v=[^\"'& ]+)?(?![A-Za-z0-9._-])",
            cache_bust, content,
        )
        content = content.replace("<head>", "<head>\n  " + HEAD_MARKER, 1)
    elif suffix == ".css":
        content = CSS_MARKER + "\n" + content
    elif suffix == ".js":
        content = JS_MARKER + "\n" + content
    return "\n".join(line.rstrip() for line in content.split("\n"))



def fingerprint_master_html(check: bool = False) -> list[str]:
    """Version Ashdod's own JS/CSS references on every publish, as for Rishon.

    A fixed query string caused browsers to keep the previous date-stack UI.
    Only local frontend assets are rewritten, and only in the build workspace.
    """
    changed = []
    pattern = r"\b((?:pilot/)?(?:(?:app|event|places|movie|cinema)\.js|(?:styles|event|places|movie|cinema|publisher-brand)\.css))(?:\?v=[^\"'& ]+)?(?![A-Za-z0-9._-])"
    for html in sorted(MASTER.glob("*.html")):
        original = html.read_text(encoding="utf-8")

        def version_asset(match):
            filename = match.group(1)
            asset = MASTER / filename
            if not asset.is_file():
                return filename
            digest = hashlib.sha256(asset.read_bytes()).hexdigest()[:12]
            return filename + "?v=" + digest

        expected = re.sub(pattern, version_asset, original)
        if expected != original:
            changed.append("ashdod/" + html.name)
            if not check:
                html.write_text(expected, encoding="utf-8")
    return changed


def files_to_sync():
    return sorted(
        (p for p in MASTER.iterdir()
         if p.is_file() and p.suffix in FRONTEND_EXTENSIONS and p.name not in SKIP_NAMES),
        key=lambda p: p.name,
    )


def run(check: bool = False) -> int:
    source_files = files_to_sync()
    assert source_files and {"index.html", "app.js", "styles.css"} <= {p.name for p in source_files}
    stale = fingerprint_master_html(check=check)
    for slug, city in TARGETS.items():
        dest = ROOT / slug
        assert (dest / "data" / "events.json").is_file(), "City-specific event dataset missing: " + slug
        for src in source_files:
            source = src.read_text(encoding="utf-8")
            expected = localize(source, src.name, city, src.suffix)
            if "https://ashdodnet.com" in expected:
                raise AssertionError(f"Unlocalized Ashdod text in {slug}/{src.name}")
            path = dest / src.name
            current = path.read_text(encoding="utf-8") if path.is_file() else None
            if current != expected:
                stale.append(f"{slug}/{src.name}")
                if not check:
                    path.write_text(expected, encoding="utf-8")
    # The reviewed pilot and its rails are the current homepage implementation.
    for slug, city in TARGETS.items():
        for src in sorted((MASTER / 'pilot').glob('*')):
            if not src.is_file() or src.suffix not in FRONTEND_EXTENSIONS: continue
            path = ROOT / slug / 'pilot' / src.name
            expected = localize(src.read_text(), src.name, city, src.suffix)
            if not path.exists() or path.read_text() != expected:
                stale.append(f'{slug}/pilot/{src.name}')
                if not check:
                    path.parent.mkdir(exist_ok=True);path.write_text(expected)
    status = "OUT OF SYNC" if check and stale else "UPDATED" if stale else "IN SYNC"
    print(f"Event UI {status}; {len(source_files)} frontend files sourced from Ashdod; "
          f"{len(TARGETS)} target city; {len(stale)} changed files.")
    for path in stale:
        print("  " + path)
    return int(check and bool(stale))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if generated city layouts need an update")
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
