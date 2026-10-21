"""Read-only hourly monitoring of deployed supermarket data and core pages."""
import concurrent.futures,json,requests
from datetime import datetime,date
from zoneinfo import ZoneInfo
BASE='https://isnet.co.il/SUPER.ASHDOD/';now=datetime.now(ZoneInfo('Asia/Jerusalem'))
def get(path):
 r=requests.get(BASE+path,timeout=(10,40),headers={'Cache-Control':'no-cache'});r.raise_for_status();return path,r
paths=['','deals/','recipes/','smart-shopping/','data/prices.json','data/refresh-status.json']
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:responses=dict(pool.map(get,paths))
prices=responses['data/prices.json'].json();refresh=responses['data/refresh-status.json'].json()
assert prices['branch_count']>=19,'Connected branch coverage dropped'
stale=[b['id'] for b in prices['branches'] if (now.date()-date.fromisoformat(b['file_date'])).days>1]
assert not stale,'Stale branches: '+','.join(stale)
assert (now-datetime.fromisoformat(refresh['checked_at'])).total_seconds()<30*3600,'Daily collection overdue'
failed=[b['branch_id'] for b in refresh['branches'] if b['status']!='updated']
assert not failed,'Sources retaining previous data: '+','.join(failed)
print('Public core pages available; all branch sources fresh and last collection complete')
