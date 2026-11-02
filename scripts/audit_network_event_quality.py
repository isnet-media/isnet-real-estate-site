#!/usr/bin/env python3
"""Evidence-based six-city content audit. Source freshness is distinct from new events and live delivery."""
import argparse,concurrent.futures,hashlib,json,subprocess
from collections import Counter
from datetime import datetime,timezone,date
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]
CITIES=('ashdod','rishon-lezion','yavne','kiryat-gat','holon','herzliya')
INACTIVE={'hidden','draft','unpublished','archived','trashed','deleted','cancelled','canceled'}
def identity(e):return e.get('event_id') or e.get('id')
def feed_path(city):return f'events-preview/{city}/data/'+('events-public.json' if city in ('holon','herzliya') else 'events.json')
def future(e,day):
    return e.get('is_active') is not False and e.get('status') not in INACTIVE and e.get('publication_status') not in INACTIVE and (e.get('end_date') or e.get('start_date') or '')>=day

def audience(e,kind):return e.get('category')==kind or kind in (e.get('audiences') or []) or any(x.get('category')==kind for x in e.get('category_memberships',[]))
def local_file(city,url):
    if not url or urlsplit(url).scheme or url.startswith('//'):return None
    path=urlsplit(url).path
    return ROOT/path.lstrip('/') if path.startswith('/') else ROOT/'events-preview'/city/path

def source_coverage(city):
    paths={'ashdod':['admin/data/ashdod-local-report.json','admin/data/ashdod-supplemental-report.json','admin/data/mevalim-ashdod-direct-report.json'],
           'rishon-lezion':['admin/data/rishon-source-report.json','admin/data/rishon-local-source-report.json'],
           'yavne':['admin/data/yavne-source-report.json'],'kiryat-gat':['admin/data/kgat-source-report.json'],
           'holon':['holon/data/source-report.json'],'herzliya':['herzliya/data/source-report.json']}[city]
    records=[]
    for relative in paths:
        path=ROOT/'events-preview'/relative
        if not path.is_file():continue
        payload=json.loads(path.read_text());sources=payload.get('sources',{})
        entries=sources.items() if isinstance(sources,dict) else [(x.get('id') or x.get('name'),x) for x in sources]
        for name,row in entries:
            if not isinstance(row,dict):continue
            records.append({'source':name,'report':relative,'status':row.get('status') or ('ok' if row.get('ok') is True else 'failed' if row.get('ok') is False else 'unknown'),
              'url':row.get('url'),'occurrences':row.get('read',row.get('occurrences',row.get('valid',row.get('events_found')))),
              'issue_count':len(row.get('issues') or []),'error':row.get('error') or row.get('note') or None})
    return {'sources':records,'attention':sum(x['status'] not in {'ok','collected'} or x['issue_count']>0 for x in records),
            'note':'A fresh file or successful workflow does not prove complete source coverage.'}

def report_city(city,baseline='HEAD',now=None):
    now=now or datetime.now(timezone.utc);day=now.astimezone(ZoneInfo('Asia/Jerusalem')).date().isoformat()
    path=feed_path(city);payload=json.loads((ROOT/path).read_text());rows=payload['events'];current={identity(e):e for e in rows}
    active=[e for e in rows if future(e,day) and not e.get('duplicate_of')]
    try:
        raw=subprocess.check_output(['git','show',baseline+':'+path],cwd=ROOT,stderr=subprocess.DEVNULL)
        old=json.loads(raw)['events'];previous={identity(e) for e in old};added=[e for k,e in current.items() if k not in previous];baseline_state='compared'
    except (subprocess.CalledProcessError,ValueError):previous=set();added=[];baseline_state='unavailable'
    stamp=payload.get('generated_at') or payload.get('generatedAt');age=None
    try:age=round((now-datetime.fromisoformat(stamp.replace('Z','+00:00'))).total_seconds()/3600,2)
    except (ValueError,TypeError,AttributeError):pass
    invalid=[];missing_media=[]
    for e in active:
        try:
            start=date.fromisoformat(e.get('start_date',''));end=date.fromisoformat(e.get('end_date') or e.get('start_date',''))
            if end<start:raise ValueError('reversed interval')
        except ValueError:invalid.append(identity(e))
        for field in ('image_url','thumbnail_url'):
            value=e.get(field);file=local_file(city,value)
            if file and not file.is_file():missing_media.append({'event_id':identity(e),'field':field,'url':value})
    directory=ROOT/'events-preview'/city/'data/restaurants.json';food=json.loads(directory.read_text());food=next((food[k] for k in ('restaurants','items','places') if isinstance(food.get(k),list)),[])
    food_media=[]
    for row in food:
        image=row.get('image') or row.get('image_url');file=local_file(city,image)
        if file and not file.is_file():food_media.append({'id':row.get('id'),'name':row.get('name') or row.get('title'),'url':image})
    return {'city':city,'source_feed':path,'source_sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),
      'feed_generated_at':stamp,'feed_age_hours':age,'freshness':'unknown' if age is None else 'future_timestamp' if age<-.1 else 'stale' if age>36 else 'within_36_hours',
      'source_coverage':source_coverage(city),'records':len(rows),'future_visible_candidates':len(active),'past_or_inactive_records_retained_in_source':sum(not future(e,day) for e in rows),
      'invalid_future_dates':invalid,'missing_local_event_media':missing_media,'categories':dict(Counter(e.get('category') for e in active)),
      'senior_candidates':sum(audience(e,'seniors') for e in active),'kids_candidates':sum(audience(e,'kids') for e in active),
      'content_without_description':sum(not any(str(e.get(k) or '').strip() for k in ('description','long_description','short_pitch')) for e in active),
      'restaurants':len(food),'food_without_source':sum(not any(row.get(k) for k in ('source_url','site','website','sources')) for row in food),'missing_local_food_media':food_media,
      'baseline':{'ref':baseline,'state':baseline_state,'records':len(previous) if baseline_state=='compared' else None},
      'new_event_ids_since_baseline':len(added),'new_future_examples':[{k:e.get(k) for k in ('event_id','id','title','start_date','start_time','venue','purchase_url','source_url','content_source_url')} for e in added if future(e,day)][:5]}

def live_readback(city,local):
    import requests
    url='https://isnet.co.il/'+feed_path(city)
    try:
        response=requests.get(url,params={'qa':local['source_sha256'][:12]},timeout=20);response.raise_for_status();data=response.json()
        expected=json.loads((ROOT/feed_path(city)).read_text())['events'];actual=data['events'];a={identity(e):e for e in actual};b={identity(e):e for e in expected}
        ids=set(a)==set(b);facts=ids and all(all(a[k].get(f)==v.get(f) for f in ('title','start_date','start_time','venue')) for k,v in b.items())
        return {'url':url,'checked_at':datetime.now(timezone.utc).isoformat(),'state':'matches' if facts else 'different_snapshot','records':len(actual),'ids_match':ids,'protected_facts_match':facts}
    except (requests.RequestException,ValueError,KeyError) as exc:return {'url':url,'state':'unverified','reason':type(exc).__name__}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--baseline-ref',default='HEAD');parser.add_argument('--live',action='store_true');args=parser.parse_args()
    cities={c:report_city(c,args.baseline_ref) for c in CITIES}
    if args.live:
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
            results=list(ex.map(lambda c:(c,live_readback(c,cities[c])),CITIES))
        for c,result in results:cities[c]['public_readback']=result
    report={'checked_at':datetime.now(timezone.utc).isoformat(),'timezone':'Asia/Jerusalem','scope':'All six public city feeds, source history comparison and local asset references; semantic image rights and external source availability require separate evidence.','cities':cities}
    out=ROOT/'events-preview/admin/data/network-content-quality.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    for c,x in cities.items():print(c,x['records'],x['freshness'],'new',x['new_event_ids_since_baseline'],'missing_media',len(x['missing_local_event_media'])+len(x['missing_local_food_media']))
if __name__=='__main__':main()
