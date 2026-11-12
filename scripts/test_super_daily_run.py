"""Daily gate regressions: DST, delayed runners, retries and partial publication."""
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from unittest.mock import patch
import subprocess
import super_daily_run as d
TZ=ZoneInfo('Asia/Jerusalem')
def now(s):return datetime.fromisoformat(s).astimezone(TZ)
# Boundaries use the real local clock, including summer and winter offsets.
for stamp in ['2026-11-15T07:59:59+02:00','2026-11-15T11:00:00+02:00',
              '2026-11-15T17:00:00+02:00','2026-11-16T08:30:00+02:00',
              '2026-11-18T08:30:00+02:00','2026-11-20T08:30:00+02:00',
              '2026-11-21T08:30:00+02:00','2026-07-07T09:00:00+00:00']:
 assert not d.allowed(now(stamp),{},{}),stamp
for stamp in ['2026-11-15T08:00:00+02:00','2026-11-17T10:59:59+02:00',
              '2026-11-19T09:00:00+02:00','2026-07-07T05:00:00+00:00',
              '2026-10-25T06:00:00+00:00']:
 assert d.allowed(now(stamp),{},{}),stamp
for record in [{'started_at':'2026-11-15T08:00:00+02:00','status':'failed'},
               {'started_at':'2026-11-15T08:00:00+02:00','status':'completed'}]:
 assert not d.allowed(now('2026-11-15T09:00:00+02:00'),record,{})
assert not d.allowed(now('2026-11-15T09:00:00+02:00'),{}, {'checked_at':'2026-11-15T08:00:00+02:00'})
assert d.allowed(now('2026-11-17T08:00:00+02:00'),{'started_at':'2026-11-15T08:00:00+02:00'}, {})
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
# All seven collectors retain one publisher-approved morning wake-up and a durable daily claim.
# UTC wake-ups are staggered; the real local clock gate remains authoritative.
expected_minutes={'super-prices.yml': 0, 'super-yavne-prices.yml': 4, 'super-kgat-prices.yml': 8, 'super-rishon-prices.yml': 12, 'super-holon-prices.yml': 16, 'super-batyam-prices.yml': 20, 'super-tlv-prices.yml': 24}
workflows={p.name:p for p in (d.ROOT/'.github/workflows').glob('super*-prices.yml')}
assert workflows.keys()==expected_minutes.keys(), 'Missing or unexpected city collector workflow'
for name,p in workflows.items():
 t=p.read_text()
 assert 'super_daily_run.py claim' in t and 'super_daily_run.py publish' in t,p
 assert "local_hour" not in t,p
 import re
 crons=re.findall(r"cron: '([^']+)'",t)
 assert len(crons)==1 and crons[0].split()==[str(expected_minutes[name]),'6','*','*','0,2,4'],p
 if p.name!='super-prices.yml':assert '--deployment-only' in t,p
 assert '  refresh:' in t and '    steps:' in t,p
print('Passed: DST, delayed runners, once-daily failed/successful attempts, concurrent publication retry and seven Sun/Tue/Thu morning workflow guards')
