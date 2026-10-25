"""Validate publication output without changing source schedules or ratings."""
import json
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
from build_movie_editorial import ROOT, CITIES, BASE, merged, editorial_html
registry=json.loads((ROOT/'events-preview/shared/data/movie-editorial.json').read_text())
index=json.loads((ROOT/'events-preview/shared/data/movie-page-index.json').read_text())
urls=set();total=0
for key,record in registry['movies'].items():
    assert len(record['original_text'])>=100,key
    assert record.get('synopsis_sources'),key
    for field in ('critics','audience_rating'):
        source=record.get(field)
        if not source: continue
        assert source['url'].startswith('https://') and source['checked_at'],key
    rating=record.get('audience_rating')
    if rating:
        assert rating['scale'] in (10,100) and 0<float(rating['value'])<=rating['scale'],key
        assert rating['metric'] in ('weighted_user_average','positive_audience_percentage'),rating
for city in CITIES:
    feed=json.loads((ROOT/f'events-preview/{city}/data/cinema.json').read_text())
    groups={}
    for movie in feed['movies']:
        key=registry['aliases'].get(movie['id'],movie['id'])
        groups.setdefault(key,[]).append(movie)
        assert index[city][movie['id']].endswith('/'+key+'/')
    nav=BeautifulSoup((ROOT/f'events-preview/{city}/index.html').read_text(),'html.parser')
    for key,movies in groups.items():
        url=BASE+city+'/movies/'+key+'/'
        page=ROOT/urlparse(url).path.lstrip('/')/'index.html'
        soup=BeautifulSoup(page.read_text(),'html.parser');record=registry['movies'].get(key,{'original_text':movies[0].get('synopsis','')})
        assert soup.find(id='page') and not soup.find(id='page').has_attr('hidden'),url
        assert soup.find(id='fullSynopsis').get_text()==record['original_text'],url
        assert soup.find(id='movieEditorial') and soup.h1.get_text(),url
        assert soup.select_one('link[rel=canonical]')['href']==url,url
        assert soup.base['href']==f'/events-preview/{city}/'
        assert soup.select_one('a.primaryButton')['href']==url+'#showtimes'
        assert nav.find('a',href=url),url
        ld=[json.loads(e.string) for e in soup.select('script[type="application/ld+json"]')]
        assert any(e['@type'] in ('Movie','CreativeWork') and e['description']==record['original_text'] for e in ld)
        assert 'AggregateRating' not in json.dumps(ld) and not any('aggregateRating' in e for e in ld)
        if record.get('audience_rating'):
            r=record['audience_rating'];assert soup.find('a',href=r['url'])
            expected=str(r['value'])+('%' if r['scale']==100 else '/10')
            assert expected in soup.find(id='movieEditorial').get_text(),url
        else:
            assert not soup.select('.movieAudienceScore'),url
        union=merged(movies)
        for venue in union['venues']:
            for day,times in venue.get('schedule',{}).items():
                original=set(t for m in movies for v in m['venues'] if v['id']==venue['id'] for t in v.get('schedule',{}).get(day,[]))
                assert set(times)==original,(key,venue['id'],day)
        urls.add(url);total+=1
sitemap=ET.parse(ROOT/'events-preview/movie-sitemap.xml')
assert urls=={e.text for e in sitemap.findall('.//{*}loc')}
xss=editorial_html({'critics':{'summary':'<script>alert(1)</script>','source':'<img>','url':'javascript:alert(1)','checked_at':'today'}})
assert '<script>' not in xss and 'javascript:' not in xss
print(f'PASS: {total} crawlable articles; city links, canonical URLs, original copy, attributed ratings, structured data, schedule union and escaping')
