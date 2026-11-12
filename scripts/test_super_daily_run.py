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
# Friday UTC can already be Saturday locally; Sunday must resume collection.
assert not d.allowed(now('2026-11-07T06:00:00+02:00'),{}, {})
assert not d.allowed(now('2026-07-03T21:30:00+00:00'),{}, {})
assert d.allowed(now('2026-11-08T06:00:00+02:00'),{}, {})
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
# These are UTC schedules: 07:30–07:54 in winter, 08:30–08:54 in summer, Sunday–Friday.
expected_minutes={"super-prices.yml":30,"super-yavne-prices.yml":34,"super-kgat-prices.yml":38,"super-rishon-prices.yml":42,"super-holon-prices.yml":46,"super-batyam-prices.yml":50,"super-tlv-prices.yml":54}
workflows={p.name:p for p in (d.ROOT/'.github/workflows').glob('super*-prices.yml')}
assert workflows.keys()==expected_minutes.keys(), 'Missing or unexpected city collector workflow'
for name,p in workflows.items():
 t=p.read_text()
 assert 'super_daily_run.py claim' in t and 'super_daily_run.py publish' in t,p
 assert "local_hour" not in t,p
 import re
 crons=re.findall(r"cron: '([^']+)'",t)
 assert len(crons)==1 and crons[0].split()==[str(expected_minutes[name]),'5','*','*','0-5'],p
 if p.name!='super-prices.yml':assert '--deployment-only' in t,p
 assert '  refresh:' in t and '    steps:' in t,p
print('Passed: DST, delayed runners, once-daily failed/successful attempts, concurrent publication retry and seven morning/Saturday workflow guards')
