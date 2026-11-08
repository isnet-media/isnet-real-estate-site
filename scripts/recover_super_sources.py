"""Bounded recovery of stale official branches from a network that can reach them.
Never re-fetch healthy branches. Keep existing promotions until a full collection.
Run city builders and publication checks after this script, before publication.
"""
import argparse,copy,fcntl,importlib,json
from datetime import datetime
from pathlib import Path
import build_super_deals
import refresh_super_prices
CITIES=('ASHDOD','YAVNE','KGAT','RISHON','HOLON','BATYAM')
def read(path):return json.loads(path.read_text()) if path.exists() else {}
def day(value,now):
 stamp=datetime.fromisoformat(value)
 if stamp.tzinfo is None:raise ValueError('Recovery evidence requires an explicit timezone')
 return stamp.astimezone(now.tzinfo).date()
def claim_attempt(c,city,now,old,selected):
 # A started/failed attempt consumes the allowance too. Write before any request,
 # so an exception or process crash cannot silently permit a second source scan.
 daily=read(c.ROOT/'.supermarket-runs'/f'{city}.json')
 if daily.get('status')=='started':
  raise RuntimeError('Daily collection is active; wait for publication before recovery')
 if (daily.get('status') not in ('completed','failed') or
     not daily.get('started_at') or day(daily['started_at'],now)!=now.date() or
     not daily.get('finished_at') or day(daily['finished_at'],now)!=now.date()):
  raise RuntimeError('Recovery requires evidence that today\'s daily collection has finished')
 if (old.get('collection_mode')=='stale_source_recovery' and old.get('checked_at') and
     day(old['checked_at'],now)>=now.date()):
  raise RuntimeError('Recovery already attempted today; preserve the real source dates')
 path=c.D/'recovery-attempt.json';previous=read(path)
 if previous.get('started_at') and day(previous['started_at'],now)>=now.date():
  raise RuntimeError('Recovery already claimed today, including failed or interrupted attempts')
 attempt={'city':city,'started_at':now.isoformat(),'status':'started','branch_ids':sorted(selected)}
 # The caller holds the per-city lock while checking and replacing this journal.
 temporary=path.with_suffix('.tmp');c.write(temporary,attempt);temporary.replace(path)
 return path,attempt
def recover(city,raw_dir):
 c=refresh_super_prices if city=='ASHDOD' else importlib.import_module('refresh_'+city.lower()+'_super_prices').collector()
 now=datetime.now(c.TZ)
 if now.weekday()==5:raise RuntimeError('No Saturday collection')
 # File locks cover concurrent processes in this checkout; the published report
 # and journal cover later invocations from a fresh main checkout.
 locks=c.ROOT/'.supermarket-runs';locks.mkdir(exist_ok=True)
 with (locks/f'{city}.recovery.lock').open('a') as lock:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise RuntimeError('Another workspace recovery is active for this city')
  return recover_locked(c,city,raw_dir,now)
def recover_locked(c,city,raw_dir,now):
 old=json.loads((c.D/'refresh-status.json').read_text())
 selected={b['branch_id'] for b in old['branches'] if b['status']!='updated'}
 cat=json.loads((c.D/'catalog.json').read_text())
 selected.update(b['id'] for b in cat['branches'] if not b.get('file_date') or b['file_date']<now.date().isoformat())
 if not selected:return print(city,'No stale sources to recover')
 journal,attempt=claim_attempt(c,city,now,old,selected)
 previous={b['branch_id']:b for b in old['branches']}
 original_refresh=c.refresh_branch;original_retry=c.recover_branches;original_build=build_super_deals.build
 def refresh(branch,folder,stamp):
  if branch['id'] in selected:return original_refresh(branch,folder,stamp)
  report=copy.deepcopy(previous[branch['id']]);report['skipped_healthy']=True
  return branch,None,report
 def retry(results,folder):
  # The first pass already uses transport retries; never retry skipped branches.
  for _,_,report in results:report.setdefault('attempts',1)
 try:
  c.refresh_branch=refresh;c.recover_branches=retry;build_super_deals.build=lambda *_:None
  result=c.run(raw_dir)
 except BaseException:
  attempt.update(status='failed',finished_at=datetime.now(c.TZ).isoformat());c.write(journal,attempt)
  raise
 finally:
  c.refresh_branch=original_refresh;c.recover_branches=original_retry;build_super_deals.build=original_build
 result.update(collection_mode='stale_source_recovery',attempted_count=len(selected),promotions='retained_previous')
 c.write(c.D/'refresh-status.json',result)
 if city!='ASHDOD':
  for name in ('catalog.json','prices.json'):
   value=json.loads((c.D/name).read_text());value['coverage_complete']=result['all_sources_updated'];c.write(c.D/name,value)
  path=c.D/'source-status.json'
  if path.exists():
   value=json.loads(path.read_text());value.pop('connection_notes',None);c.write(path,value)
 attempt.update(status='completed',finished_at=datetime.now(c.TZ).isoformat(),updated_count=result['updated_count'])
 c.write(journal,attempt)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--city',choices=CITIES,required=True);p.add_argument('--raw-dir',type=Path,required=True);a=p.parse_args();recover(a.city,a.raw_dir)
