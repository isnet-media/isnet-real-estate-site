"""Reviewed Hebrew copy is available before the optional editorial network load."""
import json
from pathlib import Path
from cinema_loading import build_listing, ROOT

registry=json.loads((ROOT/'events-preview/shared/data/movie-editorial.json').read_text())
for ident in ('cinema-city-6555','cinema-city-6639'):
    assert registry['aliases'][ident]=='matchmaking-3'
path=ROOT/'events-preview/herzliya/data/cinema.json'
before=path.read_bytes()
full=json.loads(before)
listing=build_listing('herzliya',check=True)
film=next(m for m in listing['movies'] if m['id']=='cinema-city-6639')
assert film['synopsis'].startswith(registry['movies']['matchmaking-3']['original_text'][:100])
assert 'Baruch Auerbach' not in film['synopsis']
assert path.read_bytes()==before,'Source facts and their verification date must remain intact'
for city in ('ashdod','rishon-lezion','yavne','kiryat-gat','holon','herzliya'):
    raw=json.loads((ROOT/f'events-preview/{city}/data/cinema.json').read_text())
    compact=build_listing(city,check=True)
    assert [m['id'] for m in compact['movies']]==[m['id'] for m in raw['movies']]
    for old,new in zip(raw['movies'],compact['movies']):
        assert [v.get('schedule') for v in new['venues']]==[v.get('schedule') for v in old['venues']]
        assert [v.get('article_url') for v in new['venues']]==[v.get('article_url') for v in old['venues']]
print('PASS: Hebrew first paint for reviewed movie variants; all six city IDs, schedules and links preserved')
