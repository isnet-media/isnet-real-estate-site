import copy
from dedupe_kgat_events import reconcile
from sync_kgat_events import classify
base={'title':'תנועה וספורט לגיל השלישי','start_date':'2026-11-03','venue':'מועדון שבטי ישראל','sources':[{'source_type':'official'}],'event_id':'official','start_time':'10:30'}
secondary={**copy.deepcopy(base),'event_id':'secondary','start_time':'10:00','venue':'מועדון שבטי ישראל, קריית גת','sources':[{'source_type':'secondary'}]}
rows,held=reconcile([secondary,copy.deepcopy(base)]);assert len(rows)==1 and len(held)==1 and rows[0]['start_time']=='10:30' and rows[0]['source_aliases'][0]['event_id']=='secondary'
again,_=reconcile(copy.deepcopy(rows));assert again==rows
other={**copy.deepcopy(base),'event_id':'another-show','start_time':'17:30'}
assert len(reconcile([copy.deepcopy(base),other])[0])==2
assert classify('הרצאה ברוסית עם הסופרת קרן פבזנר','ספריה עירונית פעילויות ילדים')=='lecture'
assert classify('הרצאה לילדים','ילדים')=='kids'
assert classify('דיווה 2X','ילדים')=='seniors'
print('PASS: official source time, alias links, idempotency, separate official sessions and lecture classification')
