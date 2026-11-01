"""Extract the official national rail timetable for city train alternatives."""
import argparse,csv,hashlib,io,json,re,zipfile,math
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def rows(z,name):return csv.DictReader(io.TextIOWrapper(z.open(name),encoding='utf-8-sig'))
def sec(s):
 h,m,s=map(int,s.split(':'));return h*3600+m*60+s
def norm(s):return re.sub(r'[^\w\u0590-\u05ff]','',s).replace('קריית','קרית').replace('״','').replace('׳','')
def collect(feed,out,city_name='אשדוד'):
 with zipfile.ZipFile(feed) as z:
  raw_routes={r['route_id']:r for r in rows(z,'routes.txt') if r['route_type']=='2'}
  station_cities={}
  for r in raw_routes.values():
   for terminal in r['route_long_name'].split('<->'):
    if '-' in terminal:
     station,city=terminal.rsplit('-',1);station_cities[norm(station)]=city.strip()
  all_stops={r['stop_id']:r for r in rows(z,'stops.txt')}
  bus_cities=[]
  for r in all_stops.values():
   city=re.search(r'עיר:\s*(.*?)\s*רציף:',r['stop_desc'])
   if city and city[1].strip():bus_cities.append((float(r['stop_lat']),float(r['stop_lon']),city[1].strip(),r['stop_id']))
  def nearest_city(r):
   lat,lon=float(r['stop_lat']),float(r['stop_lon'])
   closest=min(bus_cities,key=lambda b:(b[0]-lat)**2+((b[1]-lon)*math.cos(math.radians(lat)))**2)
   meters=111200*math.sqrt((closest[0]-lat)**2+((closest[1]-lon)*math.cos(math.radians(lat)))**2)
   return (closest[2],closest[3]) if meters<=1000 else ('','')
  trips={r['trip_id']:r for r in rows(z,'trips.txt') if r['route_id'] in raw_routes};timings={k:[] for k in trips}
  # Stream the large stop_times member once; retain only official rail trips.
  for r in rows(z,'stop_times.txt'):
   if r['trip_id'] in timings and r['arrival_time'] and r['departure_time']:
    timings[r['trip_id']].append([r['stop_id'],int(r['stop_sequence']),sec(r['arrival_time']),sec(r['departure_time']),int(r.get('pickup_type') or 0),int(r.get('drop_off_type') or 0)])
  patterns=[];indices={};runs=[];used=set();service_ids=set();route_ids=set()
  for tid,trip in trips.items():
   stops=sorted(timings[tid],key=lambda x:x[1])
   if len(stops)<2:continue
   base=stops[0][3];relative=[[s[0],s[2]-base,s[3]-base,s[4],s[5]] for s in stops]
   key=json.dumps([trip['route_id'],trip['trip_headsign'],relative])
   if key not in indices:
    indices[key]=len(patterns);patterns.append({'route':trip['route_id'],'headsign':trip['trip_headsign'],'stops':relative})
   runs.append([indices[key],trip['service_id'],base]);used.update(s[0] for s in stops);service_ids.add(trip['service_id']);route_ids.add(trip['route_id'])
  stops={}
  for sid in used:
   r=all_stops[sid];name=re.sub(r'\s*-\s*מטרופול$','',r['stop_name']).strip();city=station_cities.get(norm(name),'');source_stop=''
   if not city:city,source_stop=nearest_city(r)
   stops[sid]={'id':sid,'code':r['stop_code'],'name':name,'city':city,'lat':float(r['stop_lat']),'lon':float(r['stop_lon']),'mode':'rail','street':'','house':'','city_assignment':'nearby_gtfs_stop' if source_stop else 'gtfs_route_terminus','city_source_stop_id':source_stop}
  origins=[s['id'] for s in stops.values() if norm(s['city'])==norm(city_name) and (city_name!='אשדוד' or 'הלום' in s['name'])]
  if not origins:raise ValueError('Official city rail station missing')
  services={r['service_id']:{'start':r['start_date'],'end':r['end_date'],'days':[int(r[d]) for d in ['sunday','monday','tuesday','wednesday','thursday','friday','saturday']]} for r in rows(z,'calendar.txt') if r['service_id'] in service_ids}
  routes={k:{'id':k,'number':'רכבת','name':r['route_long_name'],'operator':'רכבת ישראל','mode':'rail'} for k,r in raw_routes.items() if k in route_ids}
  payload={'schema':1,'city':city_name,'mode':'rail','live':False,'generated_at':datetime.now(timezone.utc).isoformat(),'source_url':'https://gtfs.mot.gov.il/gtfsfiles/israel-public-transportation.zip','source_sha256':hashlib.sha256(Path(feed).read_bytes()).hexdigest(),'valid_from':min(v['start'] for v in services.values()),'valid_until':max(v['end'] for v in services.values()),'origin_ids':origins,**({'ashdod_origin_ids':origins} if city_name=='אשדוד' else {}),'stops':stops,'routes':routes,'services':services,'patterns':patterns,'trips':runs}
  if len(stops)<40 or len(runs)<100:raise ValueError('Rail extraction unexpectedly small')
  Path(out).write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n')
  print('Rail stations',len(stops),'trips',len(runs),'City station IDs',origins,'unassigned cities',[s['name'] for s in stops.values() if not s['city']])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--feed',default='/tmp/ashdod-bus-gtfs.zip');p.add_argument('--output',required=True);p.add_argument('--city',required=True);a=p.parse_args();collect(a.feed,a.output,a.city)
