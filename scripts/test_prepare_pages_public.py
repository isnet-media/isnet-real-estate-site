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
