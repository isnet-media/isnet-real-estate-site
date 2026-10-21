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

# Homepage identity is present before JavaScript and stays city-specific.
from html.parser import HTMLParser
class HomeHead(HTMLParser):
 def __init__(self):
  super().__init__();self.canonicals=[];self.description=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='link' and a.get('rel')=='canonical':self.canonicals.append(a.get('href'))
  if tag=='meta' and a.get('name')=='description':self.description=a.get('content')
repo=Path(__file__).resolve().parents[1]
home=(repo/'events-preview/ashdod/index.html').read_text();head=HomeHead();head.feed(home)
assert head.canonicals==['https://isnet.co.il/events-preview/ashdod/']
assert 'מה עושים באשדוד' in head.description
import re
schema=json.loads(re.search(r'<script type="application/ld\+json" id="homeSiteSchema">(.*?)</script>',home,re.S)[1])
website=next(x for x in schema['@graph'] if x['@type']=='WebSite')
assert website['name']=='מה עושים באשדוד' and website['url']==head.canonicals[0]
assert website['publisher']['@id']=='https://ashdodnet.com/#organization'
from sync_event_city_views import localize,TARGETS
for city in TARGETS.values():
 localized=localize(home,'index.html',city,'.html')
 assert 'homeSiteSchema' not in localized and 'aboutEventsTitle' not in localized
 assert 'https://isnet.co.il/events-preview/ashdod/' not in localized
print('PASS: static homepage canonical, Hebrew identity, publisher relationship and city isolation')
