#!/usr/bin/env python3
"""Single-source ISNET events UI: Ashdod changes propagate to Rishon LeZion.

Ashdod's frontend is the canonical presentation template. Event data, cinema data,
sports data, local image assets, fallback configuration and places data remain
city-owned and are never copied. This only copies root-level HTML, CSS and JS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "events-preview"
MASTER = ROOT / "ashdod"
TARGETS = {
    "yavne": {"slug":"yavne","name":"יבנה","brand":"יבנה נט","website":"https://www.yavnenet.co.il/","second_cinema":"סינמטק יבנה","second_cinema_id":"cinematheque"},
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
SKIP_NAMES = {"yavne-events.js", "site-seo.js", "seo-pages.css", "isnet-advertise.js", "restaurants.html", "restaurants.css", "restaurants.js", "dark-preview.html", "hero-international-preview.html", "ashdod-event-identities.js", "ashdod-analytics.js"}
HEAD_MARKER = "<!-- ISNET shared layout: edit the Ashdod source; synced automatically -->"
CSS_MARKER = "/* ISNET shared layout: edit events-preview/ashdod, not this generated file. */"
JS_MARKER = "// ISNET shared layout: edit events-preview/ashdod, not this generated file."


def localize(content: str, name: str, city: dict, suffix: str) -> str:
    # Preserve other city editions' existing search metadata.
    content = content.replace('מה עושים באשדוד? אירועים, הופעות ובילויים | אשדוד נט', 'מה עושים באשדוד? | מבית אשדוד נט')
    content = content.replace('מה עושים באשדוד היום ובסוף השבוע? הופעות, הצגות, סטנדאפ, סרטים, פעילויות לילדים, בילויים לגמלאים ומסעדות — באתר האירועים של אשדוד נט.', 'כל האירועים, ההופעות, הסטנדאפ, הילדים, ההצגות, ההרצאות והתערוכות באשדוד במקום אחד.')
    # The Ashdod homepage identity belongs only to this edition.
    content = re.sub(r'<!-- ASHDOD_HOME_SEO_START -->[\s\S]*?<!-- ASHDOD_HOME_SEO_END -->', '', content)
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
    content = content.replace('assets/branding/what-to-do-ashdod', 'assets/branding/what-to-do-' + ('yavne' if city['slug']=='yavne' else 'rishon'))
    content = content.replace('what-to-do-' + ('yavne' if city['slug']=='yavne' else 'rishon') + '-dark.svg?v=20261020-logo2', 'what-to-do-' + ('yavne' if city['slug']=='yavne' else 'rishon') + '-dark.svg?v=20261021-door1')
    content = content.replace('assets/branding/ashdodnet-dark.svg', 'assets/branding/' + ('yavnenet-dark.svg' if city['slug']=='yavne' else 'rishonet-dark.svg'))
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
    if city['slug']=='yavne':
        content=content.replace('בראשון לציון','ביבנה').replace('לגלות תרבות בראשון','תרבות ביבנה')
        content=content.replace("cityEvents('ashdod')","cityEvents('yavne')").replace("cityEvents('rishon-lezion')","cityEvents('ashdod')")
        content=content.replace('location.pathname.includes("/rishon-lezion/")?"rishon-lezion":"ashdod"', '"yavne"')
        content=content.replace('סינמה סיטי יבנה','סינמטק יבנה')
        # Yavne must render from the same published HTML even when JSON/CMS requests fail.
        if suffix=='.js' and Path(name).name=='app.js':
            content=content.replace('(window.ISNET_PUBLIC_CMS?.loadCards?.()||fetch("data/events.json",{cache:"no-store"}).then(r=>r.json()))','(window.ISNET_CITY_BOOTSTRAP?Promise.resolve(window.ISNET_CITY_BOOTSTRAP):(window.ISNET_PUBLIC_CMS?.loadCards?.()||fetch("data/events.json",{cache:"no-store"}).then(r=>r.json())))')
            content=content.replace('fetch("category-fallbacks.json?v=20261005-21").then(r=>r.json()).catch(()=>({}))','(window.ISNET_CITY_BOOTSTRAP?Promise.resolve({}):fetch("category-fallbacks.json?v=20261005-21").then(r=>r.json()).catch(()=>({})))')
            content=content.replace('fetch("../admin/data/taxonomy.json",{cache:"no-store"}).then(r=>r.json()).catch(()=>({primary_categories:[]}))','(window.ISNET_CITY_BOOTSTRAP?Promise.resolve(window.ISNET_CITY_BOOTSTRAP.taxonomy):fetch("../admin/data/taxonomy.json",{cache:"no-store"}).then(r=>r.json()).catch(()=>({primary_categories:[]})))')
            content=content.replace('window.ISNET_PUBLIC_CMS?.publishedEvents?.("yavne",{listing:true})||Promise.resolve([])','(window.ISNET_CITY_BOOTSTRAP?Promise.resolve([]):window.ISNET_PUBLIC_CMS?.publishedEvents?.("yavne",{listing:true})||Promise.resolve([]))')
            content=content.replace('window.ISNET_PUBLIC_CMS?.publishedEvents?.("ashdod",{listing:true})||Promise.resolve([])','(window.ISNET_CITY_BOOTSTRAP?Promise.resolve([]):window.ISNET_PUBLIC_CMS?.publishedEvents?.("yavne",{listing:true})||Promise.resolve([]))')
            marker='  renderCinema();\n  if(state.cinemaOpen)'
            refresh='  renderCinema();\n  if(window.ISNET_CITY_BOOTSTRAP&&window.ISNET_PUBLIC_CMS){\n    Promise.all([window.ISNET_PUBLIC_CMS.loadCards("yavne"),window.ISNET_PUBLIC_CMS.publishedEvents("yavne",{listing:true})]).then(([fresh,rows])=>{\n      const updated=publishedBoardEvents(fresh.events||[],rows,iso(today()));\n      if(updated.length){state.events=updated;state.generatedAt=fresh.generated_at||state.generatedAt;render();renderCinema();}\n    }).catch(error=>console.warn("Keeping the published Yavne event snapshot",error));\n  }\n  if(state.cinemaOpen)'
            content=content.replace(marker,refresh,1)
        if name in ('index.html','category.html') and suffix=='.html':
            data=json.loads((ROOT/'yavne/data/events.json').read_text())
            data['events']=[{k:v for k,v in event.items() if k not in {'image_candidates','source_detail_text','raw_html','raw','html'}} for event in data.get('events',[])]
            data['taxonomy']=json.loads((ROOT/'admin/data/taxonomy.json').read_text())
            packed=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
            content=content.replace('<head>','<head>\n<script id="yavne-event-bootstrap">window.ISNET_CITY_BOOTSTRAP='+packed+';</script>',1)

        if suffix=='.js' and name in ('category-landing.js','app.js','pilot/app.js'):
            content=content.replace('const counts={};groupEvents(state.events).forEach(e=>counts[e.category]=(counts[e.category]||0)+1);', 'const counts={};groupEvents(state.events).forEach(e=>{for(const c of cats)if(window.YAVNE_EVENTS.matches(e,new Set([c])))counts[c]=(counts[c]||0)+1;});')
            content=content.replace('ids.has(e.category)', 'window.YAVNE_EVENTS.matches(e,ids)')
            content=content.replace('if(state.category&&e.category!==state.category)return false;', 'if(state.category&&!window.YAVNE_EVENTS.matches(e,new Set([state.category])))return false;')
            content=content.replace('if(state.subcategory&&e.subcategory!==state.subcategory)return false;', 'if(state.subcategory&&!window.YAVNE_EVENTS.matchesSub(e,state.category,state.subcategory))return false;')
            content=content.replace('e.category===c&&e.subcategory===sub.id', 'window.YAVNE_EVENTS.matchesSub(e,c,sub.id)')
        if name=='category-landing.js':
            content=content.replace('const filtered=events.filter(e=>', 'const selectedSub=params.get("subcategory");\n const filtered=events.filter(e=>(!selectedSub||window.YAVNE_EVENTS.matchesSub(e,key,selectedSub))&&')
            # Real data-driven subcategories, retaining the stage navigation.
            content=content.replace('sort((a,b)=>String(a.start_date||"").localeCompare(String(b.start_date||"")));render();', 'sort((a,b)=>String(a.start_date||"").localeCompare(String(b.start_date||"")));window.YAVNE_EVENTS.subnav(events,key,params);render();')
        if name in ('kids-hub.js','seniors-hub.js'):
            # Empty city place directories must not become prominent dead ends.
            local_explore="const explore=[['הצגות ותיאטרון','הצגות ומופעים ביבנה','category.html?category=theatre','◈'],['מוזיקה והופעות','הצלילים והמופעים בעיר','category.html?category=music','♫'],['קולנוע','הקרנות בסינמטק יבנה','cinema.html','▣'],['מסעדות וקולינריה','בתי קפה ומסעדות ביבנה','restaurants.html','♨'],['אירועי קהילה','מפגשים ופעילויות בעיר','category.html?category=community','✧']];"
            content=re.sub(r'const explore=\[[^\n]+;',lambda _:local_explore,content)
            content=content.replace('href="#senior-culture"','href="category.html?category=stage"')
        if name=='seniors-hub.js':
            # Broad adult lecture inclusion remains; health lectures have a second topic.
            content=content.replace("if(goodLifeProgram(e))return 'senior-culture';", "const member=e.category_memberships?.find(x=>x.category==='seniors');if(member?.subcategory&&topics[member.subcategory])return member.subcategory;\n if(goodLifeProgram(e))return 'senior-culture';")
        if name=='seniors-hub.js':
            content=content.replace("active==='all'||topic(e)===active", "active==='all'||topic(e)===active||window.YAVNE_EVENTS.matchesSub(e,'seniors',active)||(active==='senior-lectures'&&adultLecture(e))")
        if name=='event.js':
            content=content.replace('all.find(e=>e.event_id===requestedId)', 'all.find(e=>e.event_id===requestedId||e.source_aliases?.some(a=>a.event_id===requestedId))')
        if suffix=='.html':
            def yavne_bundle_version(match):
                asset=match.group(1)+'.js'
                localized=localize((MASTER/asset).read_text(),asset,city,'.js')
                return asset+'?v='+hashlib.sha256(localized.encode()).hexdigest()[:12]
            content=re.sub(r'(kids-hub|seniors-hub|category-landing)\.js(?:\?v=[^\"\s]+)?',yavne_bundle_version,content)
            helper=(ROOT/'yavne/yavne-events.js').read_text()
            version=hashlib.sha256(helper.encode()).hexdigest()[:12]
            content=re.sub(r'(<script[^>]*src="../shared/public-cms.js[^>]*></script>)',lambda m:m[1]+'\n<script src="yavne-events.js?v='+version+'" defer></script>',content)
            # Every existing navigation menu has the same local classes destination.
            content=content.replace('href="category.html?category=stage">הופעות ומוזיקה</a>', 'href="category.html?category=stage">הופעות ומוזיקה</a><a href="https://meusharim-yavne.ebs987449.chatgpt.site/">חוגים ביבנה</a>')
        if name=='index.html':
            classes='<a class="isnetNavFeature isnetNavFeature--gold" href="https://meusharim-yavne.ebs987449.chatgpt.site/"><span class="isnetNavFeature__icon" aria-hidden="true">▧</span><span class="isnetNavFeature__copy"><strong>חוגים ביבנה</strong><small>חוגים, קורסים ופעילויות העשרה</small></span><span class="isnetNavFeature__arrow" aria-hidden="true">←</span></a>'
            content=content.replace('</nav><nav class="isnetNavDiscovery__lifestyle"',classes+'</nav><nav class="isnetNavDiscovery__lifestyle"',1)
        content=re.sub(r'<button[^>]*data-(?:cinema|venue)="(?:cinema-city|cinematheque)"[^>]*>.*?</button>', '', content)
        content=re.sub(r'<a[^>]*href="https://(?:www\.)?(?:cinema-city\.co\.il|hotcinema\.co\.il)[^"]*"[^>]*>.*?</a>', '', content)
        content=content.replace('בחרו את שני בתי הקולנוע','בדקו מועדי הקרנות נוספים')
        content=re.sub(r'<section class="cityDiscover"[\s\S]*?</section>', '', content)
        content=re.sub(r'<a[^>]*href="(?:places|attractions|saturday)\.html[^"]*"[^>]*>[\s\S]*?</a>', '', content)
        if name=='index.html':
            content=re.sub(r'<a class="isnetNavFeature isnetNavFeature--blue" href="cinema.html">[\s\S]*?</a>', '<a class="isnetNavFeature isnetNavFeature--blue" href="restaurants.html"><span class="isnetNavFeature__icon" aria-hidden="true">♨</span><span class="isnetNavFeature__copy"><strong>מסעדות וקולינריה ביבנה</strong><small>מסעדות, בתי קפה ואוכל בעיר</small></span><span class="isnetNavFeature__arrow" aria-hidden="true">←</span></a>', content)
            content=re.sub(r'<a class="isnetNavSmall" href="category.html\?category=exhibition">[\s\S]*?</a>', '<a class="isnetNavSmall" href="../ashdod/cinema.html"><span aria-hidden="true">▣</span><strong>קולנוע באשדוד</strong></a>', content)
            content=re.sub(r'<a class="isnetNavSmall" href="category.html\?category=sport">[\s\S]*?</a>', '<a class="isnetNavSmall" href="../rishon-lezion/cinema.html"><span aria-hidden="true">▣</span><strong>קולנוע בראשון לציון</strong></a>', content)
            content=re.sub(r'<a class="cityDiscover__card"[\s\S]*?</a>', '', content)

    # CMS city identifiers are ASCII slugs and must be localized explicitly.
    # Otherwise the Rishon public board silently fetches Ashdod CMS events.
    if suffix == ".js":
        content = re.sub(r'publishedEvents\?\.\(([\"\'])ashdod\1(?=[,)])', lambda m: 'publishedEvents?.('+m.group(1)+city["slug"]+m.group(1), content)
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
