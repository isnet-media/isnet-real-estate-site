"""Durable once-per-Israel-day claims and conflict-safe supermarket publication."""
import argparse,json,os,subprocess,time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]
CITIES={'ASHDOD','YAVNE','KGAT','RISHON','HOLON','BATYAM'}
def git(*args):
 return subprocess.run(['git',*args],cwd=ROOT,check=True,text=True,capture_output=True).stdout.strip()
def allowed(now,claim,report):
 if now.hour<6:return False
 today=now.date()
 for record,key in ((claim,'started_at'),(report,'checked_at')):
  value=record.get(key)
  if value and datetime.fromisoformat(value).astimezone(ZoneInfo('Asia/Jerusalem')).date()>=today:return False
 return True
def read(path):return json.loads(path.read_text()) if path.exists() else {}
def publish(paths,message):
 git('config','user.name','ISNET supermarket updater');git('config','user.email','actions@users.noreply.github.com')
 git('add','--',*paths)
 if not git('diff','--cached','--name-only'):return
 git('commit','-m',message)
 for attempt in range(5):
  try:
   git('pull','--rebase','origin','main');git('push','origin','HEAD:main');return
  except subprocess.CalledProcessError:
   if (ROOT/'.git/rebase-merge').exists() or (ROOT/'.git/rebase-apply').exists():
    git('rebase','--abort');raise RuntimeError('Concurrent changes overlap this city; refusing to overwrite')
   if attempt==4:raise
   time.sleep(2+attempt)
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['claim','publish','failed']);p.add_argument('--city',choices=sorted(CITIES),required=True);a=p.parse_args()
 now=datetime.now(ZoneInfo('Asia/Jerusalem'));site='SUPER.'+a.city;ledger=ROOT/'.supermarket-runs'/f'{a.city}.json';report=ROOT/site/'data/refresh-status.json'
 if a.action=='claim':
  # Every caller has per-city workflow concurrency; refresh remote before reading the durable claim.
  git('pull','--rebase','origin','main')
  collect=allowed(now,read(ledger),read(report))
  if collect:
   ledger.parent.mkdir(exist_ok=True);ledger.write_text(json.dumps({'city':a.city,'started_at':now.isoformat(),'status':'started','run_id':os.environ.get('GITHUB_RUN_ID')},indent=2)+'\n')
   publish([str(ledger.relative_to(ROOT))],f'Claim daily {a.city} supermarket collection {now.date()}')
  with open(os.environ['GITHUB_OUTPUT'],'a') as out:out.write('collect='+str(collect).lower()+'\n')
  print('Daily collection claimed' if collect else 'No collection: before 06:00 or already attempted today')
 else:
  claim=read(ledger);claim.update(status='completed' if a.action=='publish' else 'failed',finished_at=now.isoformat())
  if a.action=='publish':claim['result']=read(report).get('updated_count')
  ledger.write_text(json.dumps(claim,indent=2)+'\n')
  if a.action=='failed':
   # Never accidentally commit unvalidated collector output while recording a failure.
   git('reset','--',site);git('restore','--',site)
  publish(([site] if a.action=='publish' else [])+[str(ledger.relative_to(ROOT))],f'Record {a.city} supermarket daily {claim["status"]}')
if __name__=='__main__':main()
