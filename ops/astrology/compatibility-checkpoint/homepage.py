from build import dist, root, signs, source, base
import shutil

links = "".join(
    f'<a href="{base}{slug}/"><span aria-hidden="true">{symbol}&#xfe0e;</span>{name}</a>'
    for slug, name, symbol, *_ in signs
)

section = f'''<section class="isnet-astro" dir="rtl" aria-labelledby="isnet-astro-title">
  <div class="isnet-astro__lead">
    <div class="isnet-astro__copy">
      <h2 id="isnet-astro-title">עולם האסטרולוגיה <em>שלך</em></h2>
      <p>גלו מה מספר המזל שלכם על אהבה, עבודה והרגלים.</p>
      <nav class="isnet-astro__topics" aria-label="נושאי המדור">
        <a class="isnet-astro__cta" href="{source}">התחזית השבועית של עוזי הכהן <span aria-hidden="true">←</span></a>
        <a class="isnet-astro__cta" href="{base}#daily">ההורוסקופ היומי <span aria-hidden="true">←</span></a>
        <a class="isnet-astro__cta" href="{base}compatibility/">אהבה והתאמה זוגית <span aria-hidden="true">←</span></a>
        <a class="isnet-astro__cta" href="{base}compass/">המצפן האישי <span aria-hidden="true">←</span></a>
        <a class="isnet-astro__cta" href="{base}guides/birth-chart/">איך קוראים מפת לידה <span aria-hidden="true">←</span></a>
        <a class="isnet-astro__cta" href="{base}#guides">מדריכי אסטרולוגיה <span aria-hidden="true">←</span></a>
      </nav>
    </div>
    <nav class="isnet-astro__signs" id="isnet-astro-signs" aria-label="בחירת מזל" tabindex="-1">{links}</nav>
  </div>
</section>'''
(dist / "astrology" / "homepage-section.html").write_text(section)
shutil.copy(root / "homepage.css", dist / "astrology")
image = root / "zodiac-wheel.jpg"
if image.exists():
    shutil.copy(image, dist / "astrology")

context = '''
<header class="mock-header"><strong>אשדוד נט</strong><span>תצוגת שילוב בשער</span></header>
<main class="mock-shell">
  <div class="mock-neighbor"><h2>חדשות אשדוד</h2><div aria-hidden="true"><i></i><i></i><i></i></div></div>
  {section}
  <div class="mock-neighbor"><h2>מה עושים באשדוד?</h2><div aria-hidden="true"><i></i><i></i><i></i></div></div>
</main>'''
(dist / "index.html").write_text('''<!doctype html>
<html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>תצוגת שילוב בשער אשדוד נט</title>
<link rel="stylesheet" href="/astrology/homepage.css">
<style>
*{box-sizing:border-box}body{margin:0;background:#f4f5f7;color:#20252d;font-family:Arial,sans-serif}
.mock-header{background:white;border-bottom:1px solid #dbe0e6;padding:12px max(12px,calc((100% - 1056px)/2));display:flex;align-items:center;justify-content:space-between;gap:12px}
.mock-header strong{font-size:1.45rem;color:#183c67}.mock-header span{color:#505969;font-size:.85rem}
.mock-shell{width:min(1056px,calc(100% - 24px));margin:16px auto 26px;display:grid;gap:16px}
.mock-neighbor{background:white;border-top:3px solid #25527e;padding:10px 12px}
.mock-neighbor h2{margin:0 0 8px;font-size:1.1rem}.mock-neighbor div{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.mock-neighbor i{height:24px;background:#edf0f4;border-radius:3px}
</style></head><body>''' + context.format(section=section) + '</body></html>')
