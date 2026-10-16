import json,subprocess
from build_event_public_assets import compact,slug,visible,merge,ROOT
base={'event_id':'example_123456789','title':'שלום עולם!','description':'א'*1000,'internal_notes':'private','long_description':'detail','start_date':'2099-01-01'}
card=compact(base)
assert card['description']=='א'*400 and 'internal_notes' not in card and 'long_description' not in card
assert len(base['description'])==1000 and base['internal_notes']=='private'
assert visible(base,'2026-10-16') and not visible({**base,'status':'hidden'},'2026-10-16')
assert not visible({**base,'start_date':'2000-01-01'},'2026-10-16')
assert not visible(merge([base],[{'event_id':base['event_id'],'record_type':'override','payload':{'status':'hidden'}}])[0],'2026-10-16')
events=[]
for city in ('ashdod','rishon-lezion'):events+=json.loads((ROOT/f'events-preview/{city}/data/events.json').read_text())['events']
# Compare generated canonical slugs with the actual live event URL functions.
source=(ROOT/'events-preview/ashdod/pilot/event.js').read_text()
functions=[]
for name,next_name in [('eventDisplayTitle','localDate'),('slugifyHebrew','eventSlug'),('eventSlug','directEventUrl')]:
 functions.append(source[source.index('function '+name+'('):source.index('function '+next_name+'(')])
code='\n'.join(functions)+"\nlet s='';process.stdin.on('data',x=>s+=x);process.stdin.on('end',()=>console.log(JSON.stringify(JSON.parse(s).map(eventSlug))));"
actual=json.loads(subprocess.check_output(['node','-e',code],input=json.dumps(events).encode()))
assert actual==[slug(e) for e in events]
print('PASS: bounded listing copy, private fields omitted, hidden/past filtering, canonical slug parity for',len(events),'events')
