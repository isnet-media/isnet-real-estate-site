"""Regression checks for safe publication and indexable local event pages."""
import json,tempfile
from pathlib import Path
from xml.etree import ElementTree
from event_seo import build_seo,local_title
from build_event_public_assets import slug,visible
assert local_title('הרצאה')=='הרצאה באשדוד'
assert local_title('הרצאה באשדוד')=='הרצאה באשדוד'
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);admin=root/'events-preview/admin/data';city=root/'events-preview/ashdod';admin.mkdir(parents=True);(city/'data').mkdir(parents=True)
 (admin/'taxonomy.json').write_text(json.dumps({'primary_categories':[{'id':'lecture','label':'הרצאות','subcategories':[{'id':'history','label':'היסטוריה'},{'id':'empty','label':'ללא אירועים'}]}]}))
 base={'event_id':'abc12345678','title':'היסטוריה <script>alert(1)</script>','category':'lecture','subcategory':'history','start_date':'2099-01-01','start_time':'20:00','venue':'בית יד לבנים','address':'אשדוד','description':'תוכן מקורי','internal_notes':'DO_NOT_PUBLISH','price_min_ils':45,'ticket_status':'sold_out','purchase_url':'https://example.com/tickets'}
 events=[base,{**base,'event_id':'hidden','status':'hidden'},{**base,'event_id':'noindex','seo_index':False},{**base,'event_id':'past','start_date':'2000-01-01'},{**base,'event_id':'draft','publication_status':'draft'}]
 urls,report=build_seo(root,events,slug,visible,'2026-10-19');assert report['events']==1
 manifest=json.loads((city/'data/seo-index.json').read_text());assert set(manifest['events'])=={base['event_id']};assert not manifest['categories']['lecture:empty']['indexable'];assert manifest['categories']['lecture:empty']['url'] not in urls
 page=next((city/'discover').glob('event-*.html')).read_text();assert 'DO_NOT_PUBLISH' not in page and '<script>alert' not in page;assert '2099-01-01T20:00:00+02:00' in page;assert 'SoldOut' in page and 'InStock' not in page;assert 'PostalAddress' in page;assert 'היסטוריה' in page
 # Removing or hiding an event also removes its stale HTML on the next build.
 build_seo(root,[],slug,visible,'2026-10-19');assert not list((city/'discover').glob('event-*.html'))
print('PASS: local titles, static HTML, escaped text, privacy, published-only coverage, empty subtype noindex, real price/availability, timezone, stale-page removal')
