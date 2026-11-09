"""Recovery never downloads or drops a healthy branch or its promotions."""
import json,tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch
import refresh_super_prices as c
import recover_super_sources as recovery
now=datetime.now(c.TZ)
if now.weekday()==5:now=now.replace(day=now.day-1)
class Clock(datetime):
 @classmethod
 def now(cls,tz=None):return now.astimezone(tz) if tz else now.replace(tzinfo=None)
def product(pid,bid):return {'id':pid,'name':'food','quantity':'1','unit_quantity':'unit','weighted':'0','calculation_unit':'package','offers':[{'branch_id':bid,'price':9,'eligible_for_basket':True}]}
with tempfile.TemporaryDirectory() as tmp:
 ledger=Path(tmp)/'.supermarket-runs/ASHDOD.json';ledger.parent.mkdir()
 ledger.write_text(json.dumps({'status':'completed','started_at':now.isoformat(),'finished_at':now.isoformat()}))
 data=Path(tmp)/'data';(data/'offers').mkdir(parents=True)
 good={'id':'good','chain':'test','file_date':now.date().isoformat()};bad={'id':'bad','chain':'test','file_date':'2026-10-27'}
 reports=[{'branch_id':'good','status':'updated','file_date':good['file_date']},{'branch_id':'bad','status':'retained_previous','previous_file_date':bad['file_date']}]
 for name,obj in {'catalog':{'branches':[good,bad],'retrieved_at':now.isoformat()},'prices':{},'deals':{'deals':[{'name':'preserve'}]},'refresh-status':{'branches':reports}}.items():(data/(name+'.json')).write_text(json.dumps(obj))
 (data/'offers/11.json').write_text(json.dumps({'11':product('11','good'),'22':product('22','bad')}))
 def fetch(b,*_):
  assert b['id']=='bad','Healthy branch fetched twice'
  return dict(b,file_date=now.date().isoformat()),{'22':product('22','bad')},{'branch_id':'bad','status':'updated','file_date':now.date().isoformat()}
 with patch.object(c,'D',data),patch.object(c,'ROOT',Path(tmp)),patch.object(c,'refresh_branch',side_effect=fetch) as call,patch.object(recovery,'datetime',Clock),patch.object(recovery,'WORKSPACE_LOCK',Path(tmp)/'workspace.lock'):
  result=recovery.recover('ASHDOD',Path(tmp)/'raw')
 assert call.call_count==1
 assert json.loads((data/'offers/11.json').read_text())['11']['offers'][0]['branch_id']=='good'
 assert json.loads((data/'deals.json').read_text())['deals'][0]['name']=='preserve'
 assert result['attempted_count']==1 and result['all_sources_updated']
 assert json.loads((data/'recovery-attempt.json').read_text())['branch_ids']==['bad']
 print('Passed: only stale branch fetched; healthy prices and existing promotions preserved')
