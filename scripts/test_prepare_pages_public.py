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
