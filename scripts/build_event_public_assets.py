#!/usr/bin/env python3
"""Build compact listing feeds and a canonical sitemap from published event facts."""
import argparse, gzip, json, re, unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from xml.etree.ElementTree import Element,SubElement,tostring
from zoneinfo import ZoneInfo
from event_overrides import merge_event
from event_seo import build_seo
ROOT=Path(__file__).resolve().parents[1]
CITIES=('ashdod','rishon-lezion')
API='https://qomkxhafrprooekwgsxf.supabase.co/rest/v1/cms_event_records'
PUBLIC_KEY='sb_publishable_njxvSKmgkOQqkGL3JbWiIA_od-9l3wb'
LONG_FIELDS=('description','series_description','source_description','long_description','editorial_description')
PRIVATE_FIELDS=('internal_notes','source_detail_text','crosscheck_sources','review_notes','editorial_notes','source_description','editorial_description','long_description')
def compact(event):
    out={k:v for k,v in event.items() if k not in PRIVATE_FIELDS}
    for k in LONG_FIELDS:
        if isinstance(out.get(k),str):out[k]=out[k][:400]
    out['_listing_only']=True
    return out

def slugify(value):
    s=unicodedata.normalize('NFKC',str(value or '')).strip().lower()
    s=re.sub('[\"\u0027״׳]','',s)
    s=''.join(c if unicodedata.category(c)[0] in ('L','N') else '-' for c in s)
    return re.sub('-+','-',s).strip('-')[:90]
def slug(event):
    if event.get('seo_slug'):return slugify(event['seo_slug'])
    title=slugify(event.get('series_title') or event.get('title') or 'אירוע') or 'event'
    suffix=re.sub('[^a-zA-Z0-9]+','',event.get('event_id',''))[-8:].lower()
    return title+('-'+suffix if suffix else '')
def published(city):
    rows=[]
    for offset in range(0,100000,200):
        query=urlencode({'city_slug':'eq.'+city,'publication_status':'eq.published','select':'event_id,record_type,payload,seo_slug','order':'event_id.asc','offset':offset,'limit':200})
        with urlopen(Request(API+'?'+query,headers={'apikey':PUBLIC_KEY}),timeout=20) as response:page=json.load(response)
        if not isinstance(page,list):raise ValueError('Invalid published CMS response')
        rows.extend(page)
        if len(page)<200:return rows
    raise ValueError('CMS pagination limit exceeded')
def merge(events,rows):
    out={e['event_id']:e for e in events}
    for row in rows:
        key=row['event_id']
        if key not in out and row['record_type']!='manual':continue
        event=merge_event(out.get(key,{}),row.get('payload') or {})
        event['event_id']=key
        if row.get('seo_slug'):event['seo_slug']=row['seo_slug']
        out[key]=event
    return list(out.values())
def visible(e,day):
    return e.get('seo_index') is not False and e.get('is_active') is not False and e.get('status') not in ('hidden','draft','archived','trashed','deleted') and e.get('publication_status') not in ('draft','hidden','unpublished','archived') and (e.get('end_date') or e.get('start_date') or '')>=day

def build(with_cms=False):
    report={'generated_at':datetime.now(ZoneInfo('UTC')).isoformat(),'measurement':'Serialized payload bytes and gzip bytes; not a browser latency or load test.','cities':{}}
    day=datetime.now(ZoneInfo('Asia/Jerusalem')).date().isoformat()
    sitemap=Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    urls=set()
    audit_path=ROOT/'events-preview/admin/data/purchase-link-audit.json'
    audit=json.loads(audit_path.read_text()) if audit_path.exists() else {}
    broken={url:row for url,row in audit.get('results',{}).items() if row.get('state')=='broken'}
    (ROOT/'events-preview/shared/purchase-link-health.json').write_text(json.dumps({'generated_at':audit.get('generated_at'),'results':broken},ensure_ascii=False,separators=(',',':')))

    for city in CITIES:
        folder=ROOT/'events-preview'/city
        original=(folder/'data/events.json').read_bytes();data=json.loads(original)
        cards={**data,'events':[compact(e) for e in data['events']],'listing_only':True}
        encoded=json.dumps(cards,ensure_ascii=False,separators=(',',':')).encode()
        (folder/'data/events-cards.json').write_bytes(encoded)
        events=merge(data['events'],published(city)) if with_cms else data['events']
        if city=='ashdod' and with_cms:
            seo_urls,seo_report=build_seo(ROOT,events,slug,visible,day)
            urls.update(seo_urls)
        for path in ('','restaurants.html','category.html?category=stage','category.html?category=music','category.html?category=theatre','category.html?category=standup','category.html?category=lecture','category.html?category=sport','category.html?category=exhibition','category.html?category=community','category.html?category=kids','category.html?category=seniors','cinema.html','saturday.html','attractions.html'):
            if city=='ashdod' and with_cms and path.startswith('category.html'):continue
            if path=='restaurants.html' and city!='ashdod':continue
            urls.add(f'https://isnet.co.il/events-preview/{city}/'+path)
        event_urls={f'https://isnet.co.il/events-preview/{city}/event.html?'+urlencode({'slug':slug(e)}) for e in events if visible(e,day)}
        if city!='ashdod' or not with_cms:urls.update(event_urls)
        report['cities'][city]={'events':len(data['events']),'full_bytes':len(original),'listing_bytes':len(encoded),'full_gzip_bytes':len(gzip.compress(original)),'listing_gzip_bytes':len(gzip.compress(encoded)),'canonical_event_urls':len(event_urls),'published_cms_included':with_cms}
    for url in sorted(urls):SubElement(SubElement(sitemap,'url'),'loc').text=url
    if with_cms:
        (ROOT/'events-preview/sitemap.xml').write_bytes(tostring(sitemap,encoding='utf-8',xml_declaration=True))
    report['sitemap_written']=with_cms
    (ROOT/'events-preview/admin/data/site-build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--with-cms',action='store_true');args=parser.parse_args();build(args.with_cms)
