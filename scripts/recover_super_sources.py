"""Bounded recovery of stale official branches from a network that can reach them.
Never re-fetch healthy branches. Keep existing promotions until a full collection.
Run city builders and publication checks after this script, before publication.
"""
import argparse,copy,importlib,json
from datetime import datetime
from pathlib import Path
import build_super_deals
import refresh_super_prices
CITIES=('ASHDOD','YAVNE','KGAT','RISHON','HOLON','BATYAM')
def recover(city,raw_dir):
 c=refresh_super_prices if city=='ASHDOD' else importlib.import_module('refresh_'+city.lower()+'_super_prices').collector()
 now=datetime.now(c.TZ)
 if now.weekday()==5:raise RuntimeError('No Saturday collection')
 ledger=c.ROOT/'.supermarket-runs'/f'{city}.json'
 if ledger.exists():
  claim=json.loads(ledger.read_text())
  if claim.get('status')=='started' and claim.get('started_at','')[:10]==now.date().isoformat():
   raise RuntimeError('Daily collection is active; wait for publication before recovery')
 old=json.loads((c.D/'refresh-status.json').read_text())
 selected={b['branch_id'] for b in old['branches'] if b['status']!='updated'}
 cat=json.loads((c.D/'catalog.json').read_text())
 selected.update(b['id'] for b in cat['branches'] if not b.get('file_date') or b['file_date']<now.date().isoformat())
 if not selected:return print(city,'No stale sources to recover')
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
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--city',choices=CITIES,required=True);p.add_argument('--raw-dir',type=Path,required=True);a=p.parse_args();recover(a.city,a.raw_dir)
