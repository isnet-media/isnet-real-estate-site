"""City identity, crawl paths, published-only coverage and honest search notification."""
import json,tempfile
from pathlib import Path
from urllib.parse import urlparse,unquote
from urllib.robotparser import RobotFileParser
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
from search_discovery import BASE,EDITIONS
from notify_search_indexes import notify,fingerprints
ROOT=Path(__file__).resolve().parents[1]
robots=RobotFileParser();robots.parse((ROOT/'robots.txt').read_text().splitlines())
for agent in ('Googlebot','bingbot','OAI-SearchBot','PerplexityBot','Claude-SearchBot'):
 assert robots.can_fetch(agent,BASE+'ashdod/movies/our-loves/')
 assert not robots.can_fetch(agent,BASE+'admin/')
main={e.text for e in ET.parse(ROOT/'events-preview/sitemap.xml').findall('.//{*}loc')}
for city,c in EDITIONS.items():
 folder=ROOT/'events-preview'/city;home_url=BASE+city+'/';home=BeautifulSoup((folder/'index.html').read_text(),'html.parser')
 assert [a['href'] for a in home.select('link[rel=canonical]')]==[home_url],city
 identity=json.loads(home.find(id='discoveryPageSchema').string)
 assert identity['spatialCoverage']['name']==c['name']
 assert identity['publisher']['name']==c['publisher']
 assert identity['publisher']['url']==c['publisher_url']
 assert home.find('a',href=home_url+'cinema/')
 manifest=json.loads((folder/'data/seo-index.json').read_text())
 assert manifest['events'],city
 for record in list(manifest['events'].values())+list(manifest['pages'].values()):
  url=record['url'];assert url.startswith(home_url+'discover/'),(city,url)
  assert url in main,(city,url)
  p=ROOT/unquote(urlparse(url).path).lstrip('/');s=BeautifulSoup(p.read_text(),'html.parser')
  assert s.select_one('link[rel=canonical]')['href']==url
  assert c['name'] in s.title.get_text()
  graphs=json.loads(s.select_one('script[type="application/ld+json"]').string)
  event=graphs[0]
  if event['@type']=='Event':assert event['location']['address']['addressLocality']==c['name']
 hub=BeautifulSoup((folder/'cinema/index.html').read_text(),'html.parser')
 assert hub.h1 and c['name'] in hub.h1.get_text()
 assert hub.select_one('link[rel=canonical]')['href']==home_url+'cinema/'
 index=json.loads((ROOT/'events-preview/shared/data/movie-page-index.json').read_text())[city]
 for url in set(index.values()):
  absolute='https://isnet.co.il'+url;assert hub.find('a',href=absolute),(city,url)
  s=BeautifulSoup((ROOT/url.lstrip('/')/'index.html').read_text(),'html.parser')
  schemas=[json.loads(x.string) for x in s.select('script[type="application/ld+json"]')]
  local=next(x for x in schemas if x['@type']=='WebPage')
  assert local['spatialCoverage']['name']==c['name']
  assert local['publisher']['url']==c['publisher_url']
  assert local['isPartOf']['@id']==home_url+'#webpage'
  assert not any('aggregateRating' in x for x in schemas)
  assert s.find('a',href=home_url+'cinema/')
 print('PASS:',city,'canonical city identity, publisher,',len(manifest['events']),'event pages and all movie crawl paths')
# Notifications are change-based, verified by public ownership, and never claim indexing.
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);(root/'events-preview/shared/data').mkdir(parents=True);page=root/'events-preview/example.html';page.write_text('first version')
 (root/'events-preview/sitemap.xml').write_text('<urlset><url><loc>https://isnet.co.il/events-preview/example.html</loc></url><url><loc>https://isnet.co.il/events-preview/admin/private.html</loc></url><url><loc>https://other.example/example.html</loc></url></urlset>')
 key='12345678abcdef00';(root/'events-preview/shared/data/search-indexing.json').write_text(json.dumps({'indexnow_key':key}))
 state=root/'state.json';calls=[]
 class Reply:
  status=202
  def __enter__(self):return self
  def __exit__(self,*args):pass
  def read(self):return key.encode()
 def opener(request,timeout=0):
  calls.append(request)
  return Reply()
 report=notify(root,state,False,opener);assert report['changed']==1 and not calls and not state.exists()
 report=notify(root,state,True,opener);assert report['status']=='accepted' and report['http_status']==202
 payload=json.loads(calls[-1].data);assert payload['urlList']==['https://isnet.co.il/events-preview/example.html']
 assert 'not a promise' in report['note']
 count=len(calls);assert notify(root,state,True,opener)['status']=='unchanged' and len(calls)==count
 page.unlink();assert notify(root,state,False,opener)['removed']==1
 print('PASS: IndexNow public ownership, canonical-only filtering, no repeated unchanged URLs and deleted-page notification')
