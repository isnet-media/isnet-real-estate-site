"""No source request on repeated, concurrent, early or interrupted recovery."""
import fcntl,json,tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
import recover_super_sources as recovery
import refresh_super_prices as c

NOW=datetime.fromisoformat('2026-11-08T11:00:00+02:00')
class Clock(datetime):
 current=NOW
 @classmethod
 def now(cls,tz=None):return cls.current.astimezone(tz) if tz else cls.current.replace(tzinfo=None)

def fixture(root):
 data=root/'data';data.mkdir()
 c.write(data/'catalog.json',{'branches':[{'id':'bad','file_date':'2026-11-06'}]})
 c.write(data/'refresh-status.json',{'checked_at':NOW.isoformat(),'branches':[{'branch_id':'bad','status':'retained_previous'}]})
 ledger=root/'.supermarket-runs/ASHDOD.json';ledger.parent.mkdir()
 c.write(ledger,{'status':'completed','started_at':NOW.isoformat(),'finished_at':NOW.isoformat()})
 return data,ledger

def blocked(data,root,match):
 before={p.name:p.read_bytes() for p in data.glob('*.json')}
 with patch.object(c,'D',data),patch.object(c,'ROOT',root),patch.object(c,'run') as run:
  try:recovery.recover('ASHDOD',root/'raw')
  except RuntimeError as e:assert match in str(e),(match,str(e))
  else:raise AssertionError('Unsafe recovery accepted')
  run.assert_not_called()
 assert before=={p.name:p.read_bytes() for p in data.glob('*.json')},'Guard changed source data'

with patch.object(recovery,'datetime',Clock):
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);data,ledger=fixture(root)
  # Backward-compatible evidence: today's already-published legacy recovery.
  report=json.loads((data/'refresh-status.json').read_text());report['collection_mode']='stale_source_recovery'
  c.write(data/'refresh-status.json',report)
  blocked(data,root,'already attempted today')
  report.pop('collection_mode');c.write(data/'refresh-status.json',report)
  # Prior-day or missing daily evidence is not permission for an early scan.
  claim=json.loads(ledger.read_text());claim['started_at']='2026-11-06T06:00:00+02:00'
  c.write(ledger,claim);blocked(data,root,'daily collection has finished')
  claim['status']='started';c.write(ledger,claim);blocked(data,root,'Daily collection is active')
  ledger.unlink();blocked(data,root,'daily collection has finished')
  claim.update(status='failed',started_at=NOW.isoformat());c.write(ledger,claim)
  # An overlapping process cannot enter even before its first output exists.
  with (ledger.parent/'ASHDOD.recovery.lock').open('a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   blocked(data,root,'Another workspace recovery is active')
  # Crash before the collector publishes anything still consumes the allowance.
  with patch.object(c,'D',data),patch.object(c,'ROOT',root),patch.object(c,'run',side_effect=RuntimeError('simulated crash')):
   try:recovery.recover('ASHDOD',root/'raw')
   except RuntimeError as e:assert str(e)=='simulated crash'
   else:raise AssertionError('Crash not propagated')
  attempt=json.loads((data/'recovery-attempt.json').read_text())
  assert attempt['status']=='failed' and attempt['branch_ids']==['bad']
  blocked(data,root,'already claimed today')
  # A completed attempt that retained stale prices is equally final for today.
  attempt['status']='completed';c.write(data/'recovery-attempt.json',attempt)
  blocked(data,root,'already claimed today')
  # Next Israel day permits one new claim after that day's normal collector.
  Clock.current=datetime.fromisoformat('2026-11-09T11:00:00+02:00')
  claim.update(status='completed',started_at=Clock.current.isoformat(),finished_at=Clock.current.isoformat());c.write(ledger,claim)
  with patch.object(c,'D',data),patch.object(c,'ROOT',root):
   _,new=recovery.claim_attempt(c,'ASHDOD',Clock.current,report,{'bad'})
  assert new['started_at'].startswith('2026-11-09')
  blocked(data,root,'already claimed today')
  # Friday UTC has already become Saturday in Israel (summer UTC+3).
  Clock.current=datetime.fromisoformat('2026-07-03T21:30:00+00:00')
  blocked(data,root,'No Saturday collection')

print('Passed: daily prerequisite, legacy report, concurrent lock, crash, failed/complete retry, next-day and Israel Saturday guards; no network calls')
