"""Ensure staging preserves public data and rejects unsafe output paths."""
import tempfile
from pathlib import Path
from prepare_pages_public import stage

with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp)
    root = base / 'source'
    root.mkdir()
    for name in ['index.html', 'robots.txt', 'SUPER.TLV/data/prices.json',
                 'events-preview/ashdod/assets/photo.jpg', 'ops/MONITOR.md',
                 'weather/ashdod/sea.json', '.supermarket-repair/evidence.json',
                 'scripts/collector.py', 'tests/test.py', '.git/config']:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
    output = base / 'public'
    stage(root, output)
    for path in ['index.html', 'robots.txt', 'SUPER.TLV/data/prices.json',
                 'events-preview/ashdod/assets/photo.jpg', 'ops/MONITOR.md',
                 'weather/ashdod/sea.json']:
        assert (output / path).read_bytes() == (root / path).read_bytes()
    for path in ['scripts', 'tests', '.git', '.supermarket-repair']:
        assert not (output / path).exists()
    for unsafe in [root, root / 'public', output]:
        try:
            stage(root, unsafe)
            raise AssertionError('Unsafe output accepted')
        except ValueError:
            pass
print('Public paths and bytes preserved; operational evidence excluded; unsafe outputs refused')

from prepare_pages_public import check_capacity, PAGES_LIMIT
check_capacity(803_380_493)
try:
    check_capacity(PAGES_LIMIT)
    raise AssertionError('Oversized Pages upload allowed')
except ValueError:
    pass
print('Capacity limit guard passed')

# Exercise the cutover and rollback on a real git fixture: public URLs and
# shopping-list browser origin remain unchanged; only data leaves Pages.
import json, subprocess
with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp); root = base/'source'; root.mkdir()
    for name, body in {'index.html':'<head></head>news',
      'SUPER.KGAT/index.html':'<html><head></head><body>unchanged</body></html>',
      'SUPER.KGAT/compare/index.html':'<html><head></head><body>compare</body></html>',
      'SUPER.KGAT/assets/branding/super-shell.html':'<header>fragment</header>',
      'SUPER.KGAT/assets/app.js':'fetch("../data/catalog.json")',
      'SUPER.KGAT/data/catalog.json':'{"rows":[]}',
      'SUPER.KGAT/data/offers/00.json':'{}',
      'SUPER.YAVNE/data/catalog.json':'{}',
      'scripts/super_delivery.json':'{"cities":["KGAT"]}'}.items():
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body)
    subprocess.run(['git','init','-q',str(root)],check=True)
    subprocess.run(['git','-C',str(root),'add','.'],check=True)
    subprocess.run(['git','-C',str(root),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture'],check=True)
    output=base/'routed';stage(root,output)
    assert not (output/'SUPER.KGAT/data').exists()
    assert (output/'SUPER.YAVNE/data/catalog.json').read_text()=='{}'
    assert (output/'SUPER.KGAT/assets/app.js').read_text()==(root/'SUPER.KGAT/assets/app.js').read_text()
    page=(output/'SUPER.KGAT/compare/index.html').read_text()
    assert page.index('data-super-delivery')<page.index('</head>')
    assert 'location.replace' not in page and 'localStorage' not in page
    report=json.loads((output/'super-delivery-status.json').read_text())
    assert report['html_pages_routed']==2 and report['data_bytes_offloaded']>0
    (root/'scripts/super_delivery.json').write_text('{"cities":[]}')
    restored=base/'rollback';stage(root,restored)
    for name in ['SUPER.KGAT/index.html','SUPER.KGAT/data/catalog.json','SUPER.KGAT/data/offers/00.json']:
        assert (restored/name).read_bytes()==(root/name).read_bytes()
print('PASS: immutable data cutover, retained frontend/other cities, nested-page injection, untouched list origin and byte-exact rollback')

with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp)
    root = base / 'source'
    home = '<html><head><title>Example</title></head><body><main>Editorial content</main></body></html>'
    astrology_home = home.replace('</main>', '<aside hidden data-placement="astrology-landing"></aside></main>')
    astrology_sign = home.replace('</main>', '<aside hidden data-placement="astrology-forecast"></aside></main>')
    fixtures = {
        'index.html': home,
        'events-preview/ashdod/index.html': home,
        'events-preview/ashdod/category.html': home,
        'events-preview/ashdod/event.html': home,
        'events-preview/herzliya/index.html': home,
        'astrology/index.html': astrology_home,
        'astrology/aries/index.html': astrology_sign,
        'astrology/rising/index.html': home,
        'astrology/homepage-section.html': home,
        'astrology/guides/redirect/index.html': home.replace('<title>', '<meta http-equiv="refresh" content="0;url=/astrology/"><title>'),
        'events-preview/admin/index.html': home,
        'events-preview/ashdod/private/index.html': home.replace('<title>', '<meta name="robots" content="noindex"><title>'),
        'SUPER.ASHDOD/index.html': home,
    }
    placements = {
        'events-preview/ashdod/index.html': 'events-landing',
        'events-preview/ashdod/category.html': 'events-article',
        'events-preview/ashdod/event.html': 'events-article',
        'events-preview/herzliya/index.html': 'events-landing',
        'astrology/index.html': 'astrology-landing',
        'astrology/aries/index.html': 'astrology-forecast',
        'astrology/rising/index.html': 'astrology-article',
    }
    for name, html in fixtures.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html)
    output = base / 'public'
    stage(root, output, cities=set())
    for name, html in fixtures.items():
        rendered = (output / name).read_text()
        if name in placements:
            assert rendered.count('data-isnet-adsense') == 1, name
            assert 'async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3043177344534285"' in rendered
            assert f'<aside hidden data-placement="{placements[name]}" aria-hidden="true"></aside>' in rendered
            assert 'class="adsbygoogle"' not in rendered
            assert rendered.rindex('data-placement=') < rendered.rindex('</main>')
        else:
            assert rendered == html, name
        assert (root / name).read_text() == html
    print('PASS: event and astrology placements scoped to public standalone pages; inactive slots have no visible gap')

    config = root / 'scripts' / 'isnet_adsense_slots.json'
    config.parent.mkdir()
    config.write_text('{"events-landing":"12345","astrology-forecast":"67890"}')
    stage(root, base / 'configured', cities=set())
    for name, slot in {'events-preview/ashdod/index.html': '12345', 'astrology/aries/index.html': '67890'}.items():
        rendered = (base / 'configured' / name).read_text()
        assert rendered.count(f'data-ad-slot="{slot}"') == 1
        assert 'data-isnet-ad-style' in rendered
        assert 'data-ad-status="unfilled"' in rendered
    assert 'data-ad-slot' not in (base / 'configured' / 'astrology/index.html').read_text()
    print('PASS: only explicitly configured display units render and their responsive styles remain scoped')
