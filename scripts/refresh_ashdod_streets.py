"""Refresh Ashdod official street names and synonyms, without inventing coordinates."""
import argparse,hashlib,json,re,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]
API='https://data.gov.il/api/3/action/'
def get(action,**params):
 url=API+action+'?'+urlencode(params)
 for attempt in range(3):
  try:
   with urlopen(Request(url,headers={'User-Agent':'ISNET-public-transit/1.0'}),timeout=60) as response:d=json.load(response)
   if not d.get('success'):raise ValueError('Official API returned failure')
   return d['result']
  except Exception:
   if attempt==2:raise
   time.sleep(2)
def fetch(package,filters):
 metadata=get('package_show',id=package)
 resource=max((r for r in metadata['resources'] if r.get('format','').upper()=='CSV' and r.get('datastore_active')),key=lambda r:r.get('last_modified') or '')
 result=get('datastore_search',resource_id=resource['id'],filters=json.dumps(filters,ensure_ascii=False),limit=5000)
 if len(result['records'])!=result['total']:raise ValueError('Incomplete official street response')
 return result['records'],resource.get('last_modified'),resource['id']
def build(rows,aliases,updated_at,alias_updated_at):
 result={str(r['סמל_רחוב']):{'cityCode':'70','streetCode':str(r['סמל_רחוב']),'name':r['שם_רחוב'],'aliases':[]} for r in rows if str(r['סמל_ישוב'])=='70' and r['שם_ישוב']=='אשדוד' and int(r['סמל_רחוב'])<9000}
 if len(result)<600:raise ValueError('Official Ashdod street count unexpectedly low')
 for row in aliases:
  if str(row.get('city_code'))!='70':continue
  entry=result.get(str(row.get('official_code')))
  if entry and row['street_name']!=entry['name'] and row['street_name'] not in entry['aliases']:entry['aliases'].append(row['street_name'])
 return {'schema':1,'city':'אשדוד','source':'רשות האוכלוסין וההגירה','source_url':'https://data.gov.il/datasets/population_authority/321','synonyms_source_url':'https://data.gov.il/datasets/population_authority/israel-streets-synom','source_updated_at':updated_at,'synonyms_updated_at':alias_updated_at,'checked_at':datetime.now(timezone.utc).isoformat(),'verifiedCoordinates':False,'streets':sorted(result.values(),key=lambda x:int(x['streetCode']))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--streets-json');p.add_argument('--synonyms-json');p.add_argument('--source-updated');p.add_argument('--synonyms-updated');a=p.parse_args()
 if a.streets_json and a.synonyms_json:
  raw=json.load(open(a.streets_json))['result'];syn=json.load(open(a.synonyms_json))['result']
  if len(raw['records'])!=raw['total'] or len(syn['records'])!=syn['total']:raise ValueError('Truncated source records')
  rows,aliases=raw['records'],syn['records'];updated,alias_updated=a.source_updated,a.synonyms_updated
 else:
  rows,updated,_=fetch('321',{'שם_ישוב':'אשדוד'});aliases,alias_updated,_=fetch('israel-streets-synom',{'city_code':70})
 payload=build(rows,aliases,updated,alias_updated)
 out=ROOT/'bus/ashdod/data/ashdod-streets.json';out.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n')
 print('Official streets:',len(payload['streets']),'aliases:',sum(len(s['aliases']) for s in payload['streets']))
