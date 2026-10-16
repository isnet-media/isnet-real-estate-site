import json
from normalize_event_provenance import BASE, normalize, ensure_source_reference
registry=json.loads((BASE/'ashdod/data/institutions.json').read_text())['institutions']
event={'title':'סיור','venue':'נקודת המפגש לא פורסמה','local_source_name':'ofek_ashdod','content_source_url':'https://www.ofek-ashdod.org.il/page.php?type=event&id=123','purchase_phone':'08-9238680'}
normalize(event,registry)
assert event['operator_id']=='ofek_ashdod' and event['sources'][0]['name']=='ofek_ashdod'
assert not event.get('address')
assert normalize(event,registry)==0
unknown={'title':'ללא מקור','purchase_url':'#updates'}
assert ensure_source_reference(unknown)==0 and not unknown.get('sources')
assert ensure_source_reference({'source':'mevalim_direct','purchase_url':'#updates'})==1
print('PASS: exact source identities, no invented provenance or departure addresses, idempotence')
