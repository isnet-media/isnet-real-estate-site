"""Build a compact Ashdod transit network from the official Israeli GTFS feed.
All stop/route/service IDs are source-owned. No inferred live arrival data.
"""
import argparse,csv,hashlib,io,json,re,zipfile
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
SOURCE='https://gtfs.mot.gov.il/gtfsfiles/israel-public-transportation.zip'
def rows(z,name):return csv.DictReader(io.TextIOWrapper(z.open(name),encoding='utf-8-sig'))
def seconds(t):
 h,m,s=map(int,t.split(':'));return h*3600+m*60+s

def collect(feed,output):
 with zipfile.ZipFile(feed) as z:
  stops={}
  for r in rows(z,'stops.txt'):
   if r['location_type'] not in ('','0'):continue
   city=re.search(r'עיר:\s*(.*?)\s*רציף:',r['stop_desc'])
   stops[r['stop_id']]={'id':r['stop_id'],'code':r['stop_code'],'name':r['stop_name'],'city':city[1].strip() if city else '', 'lat':float(r['stop_lat']),'lon':float(r['stop_lon'])}
  local={k for k,v in stops.items() if v['city']=='אשדוד'}
  print('Ashdod stops',len(local),flush=True)
  alltrips={r['trip_id']:r for r in rows(z,'trips.txt')}
  touched=set()
  with z.open('stop_times.txt') as f:
   next(f)
   for raw in f:
    a=raw.decode().rstrip().split(',')
    if a[3] in local:touched.add(a[0])
  route_ids={alltrips[t]['route_id'] for t in touched if t in alltrips}
  routemap={r['route_id']:r for r in rows(z,'routes.txt') if r['route_id'] in route_ids}
  # Bus and rail only, no ferry/unknown mode substitution.
  routemap={k:r for k,r in routemap.items() if r['route_type'] in ['2','3']}
  relevant={t:r for t,r in alltrips.items() if r['route_id'] in routemap}
  print('Routes',len(routemap),'trips',len(relevant),flush=True)
  timings={t:[] for t in relevant}
  with z.open('stop_times.txt') as f:
   next(f)
   for raw in f:
    a=raw.decode().rstrip().split(',');t=a[0]
    if t in timings and a[3] in stops and a[1] and a[2]:
     timings[t].append([a[3],int(a[4]),seconds(a[1]),seconds(a[2]),int(a[5] or 0),int(a[6] or 0)])
  agencies={r['agency_id']:r['agency_name'] for r in rows(z,'agency.txt')}
  services={r['service_id']:{'start':r['start_date'],'end':r['end_date'],'days':[int(r[d]) for d in ['sunday','monday','tuesday','wednesday','thursday','friday','saturday']]} for r in rows(z,'calendar.txt')}
  patterns=[];index={};trips=[];used_stops=set();used_services=set()
  for tid,info in relevant.items():
   ss=sorted(timings[tid],key=lambda x:x[1])
   if len(ss)<2 or not any(x[0] in local for x in ss):continue
   base=ss[0][3]
   times=[[x[0],x[2]-base,x[3]-base,x[4],x[5]] for x in ss]
   key=json.dumps([info['route_id'],info['trip_headsign'],times],ensure_ascii=False,separators=(',',':'))
   if key not in index:
    index[key]=len(patterns);patterns.append({'route':info['route_id'],'headsign':info['trip_headsign'],'stops':times})
   trips.append([index[key],info['service_id'],base]);used_stops.update(x[0] for x in ss);used_services.add(info['service_id'])
  routes={k:{'id':k,'number':r['route_short_name'],'name':r['route_long_name'],'operator':agencies.get(r['agency_id'],''),'mode':'rail' if r['route_type']=='2' else 'bus'} for k,r in routemap.items()}
  services={k:v for k,v in services.items() if k in used_services}
  dates=[v['end'] for v in services.values()]
  payload={'schema':1,'city':'אשדוד','generated_at':datetime.now(ZoneInfo('Asia/Jerusalem')).isoformat(),'source_url':SOURCE,'source_sha256':hashlib.sha256(Path(feed).read_bytes()).hexdigest(),'live':False,'valid_from':min(v['start'] for v in services.values()),'valid_until':max(dates),'stops':{k:stops[k] for k in sorted(used_stops,key=int)},'local_stop_ids':sorted(local&used_stops,key=int),'routes':routes,'services':services,'patterns':patterns,'trips':trips}
  output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
  output.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n')
  print('Built',len(patterns),'patterns',len(trips),'trips',len(used_stops),'stops',output.stat().st_size,'bytes',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--feed',default='/tmp/ashdod-bus-gtfs.zip');p.add_argument('--output',default=str(ROOT/'bus/ashdod/data/network.json'));a=p.parse_args()
 feed=Path(a.feed)
 if not feed.exists():
  temp=feed.with_suffix('.download')
  with requests.get(SOURCE,stream=True,timeout=(25,180)) as r:
   r.raise_for_status()
   with temp.open('wb') as f:
    for chunk in r.iter_content(1024*1024):f.write(chunk)
  temp.replace(feed)
 collect(feed,a.output)
