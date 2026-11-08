"""Reviewed Hebrew copy is available before the optional editorial network load.

Exercise the historical English-source variant with an isolated fixture. A live
cinema feed may legitimately stop listing a film; its removal must not block
unrelated public event deployments.
"""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import cinema_loading
from cinema_loading import build_listing, ROOT

registry = json.loads((ROOT / 'events-preview/shared/data/movie-editorial.json').read_text())
for ident in ('cinema-city-6555', 'cinema-city-6639'):
    assert registry['aliases'][ident] == 'matchmaking-3'

path = ROOT / 'events-preview/herzliya/data/cinema.json'
before = path.read_bytes()

# Test the former English-only source variant even when the live film rotates out.
with TemporaryDirectory() as directory:
    fixture_root = Path(directory)
    data_dir = fixture_root / 'events-preview/herzliya/data'
    editorial_dir = fixture_root / 'events-preview/shared/data'
    data_dir.mkdir(parents=True)
    editorial_dir.mkdir(parents=True)
    (data_dir / 'cinema.json').write_text(json.dumps({
        'updated_at': 'fixture', 'movies': [{
            'id': 'cinema-city-6639',
            'title': 'בחורים טובים 3',
            'synopsis': 'Baruch Auerbach is looking for his match.',
            'venues': [],
        }],
    }, ensure_ascii=False))
    (editorial_dir / 'movie-editorial.json').write_text(json.dumps({
        'aliases': {'cinema-city-6639': 'matchmaking-3'},
        'movies': {'matchmaking-3': registry['movies']['matchmaking-3']},
    }, ensure_ascii=False))
    with patch.object(cinema_loading, 'ROOT', fixture_root):
        listing = cinema_loading.build_listing('herzliya', check=True)

film = next(m for m in listing['movies'] if m['id'] == 'cinema-city-6639')
assert film['synopsis'].startswith(registry['movies']['matchmaking-3']['original_text'][:100])
assert 'Baruch Auerbach' not in film['synopsis']
assert path.read_bytes() == before, 'Source facts and their verification date must remain intact'

for city in ('ashdod', 'rishon-lezion', 'yavne', 'kiryat-gat', 'holon', 'herzliya'):
    raw = json.loads((ROOT / f'events-preview/{city}/data/cinema.json').read_text())
    compact = build_listing(city, check=True)
    assert [m['id'] for m in compact['movies']] == [m['id'] for m in raw['movies']]
    for old, new in zip(raw['movies'], compact['movies']):
        assert [v.get('schedule') for v in new['venues']] == [v.get('schedule') for v in old['venues']]
        assert [v.get('article_url') for v in new['venues']] == [v.get('article_url') for v in old['venues']]

print('PASS: Hebrew first paint for historical movie variants; all six city IDs, schedules and links preserved')
