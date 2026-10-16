import ast
import importlib.util
import os
import re
from pathlib import Path

from event_overrides import FIELDS, merge_event

root = Path(__file__).resolve().parents[1]
js = (root / 'events-preview/shared/event-overlay.js').read_text()
assert FIELDS == ast.literal_eval(re.search(r'const fields=(\[.*?\]);', js).group(1))
base = {'title': 'source', 'start_date': '2099-01-02', 'category': 'music'}
patch = {'title': 'manual', 'start_date': '2000-01-01', 'overlay_version': 2, 'locked_fields': ['title']}
assert merge_event(base, patch)['title'] == 'manual'
assert merge_event(base, patch)['start_date'] == '2099-01-02'
assert merge_event(base, {**patch, 'locked_fields': []})['title'] == 'source'
assert merge_event(base, {'title': 'legacy'})['title'] == 'legacy'
# Dummy configuration only: importing constructs no network requests.
os.environ.setdefault('SUPABASE_URL', 'https://example.invalid')
os.environ.setdefault('SUPABASE_SERVICE_ROLE_KEY', 'test-placeholder')
spec = importlib.util.spec_from_file_location('publisher', root / 'scripts/auto_publish_ready_events.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)
class Response:
    def __init__(self, rows): self.rows = rows
    def raise_for_status(self): pass
    def json(self): return self.rows
class Session:
    def __init__(self): self.offsets = []
    def get(self, url, params, timeout):
        self.offsets.append(params['offset'])
        return Response([{'city_slug':'ashdod', 'event_id':str(i)} for i in range(params['offset'], min(params['offset'] + 200, 405))])
publisher.SESSION = Session()
assert len(publisher.get_cms_records()) == 405
assert publisher.SESSION.offsets == [0, 200, 400]
a = {'_citySlug': 'ashdod', 'event_id': 'a', 'title':'same', 'venue':'hall', 'start_date':'2099-01-01', 'start_time':'19:00'}
b = {**a, 'event_id':'b', 'start_time':'21:00'}
assert not publisher.duplicate_keys([a, b])
assert publisher.duplicate_keys([a, {**b, 'start_time':'19:00'}]) == {'ashdod:a','ashdod:b'}
print('PASS: browser/agent field parity, protected edits, source updates, legacy records, complete CMS pagination, distinct performance times')
