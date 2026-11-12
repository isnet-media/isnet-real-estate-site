"""Read-only verification of deployed supermarket data in every city."""
import concurrent.futures,json,requests
from datetime import datetime,date,timedelta
from zoneinfo import ZoneInfo
from super_schedule import in_window, expected_collection_day
CITIES={'ASHDOD':20,'YAVNE':7,'KGAT':9,'RISHON':24,'HOLON':23,'BATYAM':19,'TLV':19}
now=datetime.now(ZoneInfo('Asia/Jerusalem'))
def collection_due(checked_at, current):
 expected=expected_collection_day(current)
 checked=datetime.fromisoformat(checked_at).astimezone(ZoneInfo('Asia/Jerusalem'))
 return checked.date()<expected
def check(city,minimum):
 base='https://tlvnet.com/super/' if city=='TLV' else f'https://isnet.co.il/SUPER.{city}/'
 def get(path):
  url=('https://tlvnet.com/api/super-data/'+path[len('data/'):]) if city=='TLV' and path.startswith('data/') else base+path
  response=requests.get(url,timeout=(10,40),headers={'Cache-Control':'no-cache'})
  response.raise_for_status()
  return path,response
 paths=['','deals/','recipes/','smart-shopping/','data/prices.json','data/refresh-status.json']
 try:
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:responses=dict(pool.map(get,paths))
  prices=responses['data/prices.json'].json();refresh=responses['data/refresh-status.json'].json()
  errors=[]
  if prices['branch_count']<minimum:errors.append('Connected branch coverage dropped')
  stale=[b['id'] for b in prices['branches'] if not b.get('file_date') or (expected_collection_day(now)-date.fromisoformat(b['file_date'])).days>1]
  if stale:errors.append('Stale branches: '+','.join(stale))
  if collection_due(refresh['checked_at'],now):errors.append('Scheduled collection overdue: last public collection '+refresh['checked_at'])
  failed=[b['branch_id'] for b in refresh['branches'] if b['status']!='updated']
  if failed:errors.append('Sources retaining previous data: '+','.join(failed))
  # Confirm both published data entry points carry the same branch metadata.
  catalog=get('data/catalog.json')[1].json()
  if catalog['branches']!=prices['branches']:errors.append('Catalog/prices branch metadata mismatch')
  return city,errors
 except Exception as error:return city,[type(error).__name__+': public read-back failed']
def main():
 if not in_window(now,health=True):
  print("Skipped: supermarket health checks only Sun/Tue/Thu mornings in Israel")
  return
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  results=list(pool.map(lambda item:check(*item),CITIES.items()))
 for city,errors in results:
  print(city+': '+('; '.join(errors) if errors else 'public pages and branch data verified'))
 if any(errors for _,errors in results):raise SystemExit(1)
if __name__=='__main__':main()
