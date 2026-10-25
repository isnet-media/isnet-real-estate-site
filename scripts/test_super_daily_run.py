"""Daily gate regressions: DST, delayed runners, retries and partial publication."""
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from unittest.mock import patch
import subprocess
import super_daily_run as d
TZ=ZoneInfo('Asia/Jerusalem')
def now(s):return datetime.fromisoformat(s).astimezone(TZ)
# DST transition and a runner delayed beyond the original one-hour window.
assert not d.allowed(now('2026-10-25T03:59:00+00:00'),{}, {})
assert d.allowed(now('2026-10-25T04:00:00+00:00'),{}, {})
assert d.allowed(now('2026-10-25T09:12:00+00:00'),{}, {})
assert d.allowed(now('2026-07-01T03:00:00+00:00'),{}, {})
assert not d.allowed(now('2026-10-25T09:12:00+00:00'),{'started_at':'2026-10-25T06:00:00+02:00','status':'failed'}, {})
assert not d.allowed(now('2026-10-25T09:12:00+00:00'),{}, {'checked_at':'2026-10-25T06:30:00+02:00','updated_count':0})
assert d.allowed(now('2026-10-26T04:00:00+00:00'),{'started_at':'2026-10-25T06:00:00+02:00'}, {})
# A non-overlapping push race is retried without replacing another city's data.
calls=[]
def git(*args):
 calls.append(args)
 if args[:3]==('diff','--cached','--name-only'):return 'SUPER.YAVNE/data/prices.json'
 if args[0]=='push' and sum(x[0]=='push' for x in calls)==1:raise subprocess.CalledProcessError(1,['git','push'])
 return ''
with patch.object(d,'git',side_effect=git),patch.object(d.time,'sleep'):
 d.publish(['SUPER.YAVNE'],'test')
assert sum(x[0]=='push' for x in calls)==2
# All six workflows use a durable daily claim; stale prices cannot block valid city output.
for p in (d.ROOT/'.github/workflows').glob('super*-prices.yml'):
 t=p.read_text()
 assert 'super_daily_run.py claim' in t and 'super_daily_run.py publish' in t,p
 assert "local_hour" not in t,p
 assert '0 3,4 * * *' in t,p
 if p.name!='super-prices.yml':assert '--deployment-only' in t,p
 assert '  refresh:' in t and '    steps:' in t,p
print('Passed: DST, delayed runners, once-daily failed/successful attempts, concurrent publication retry and six workflow guards')
