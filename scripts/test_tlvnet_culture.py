"""Official genre/date/hall boundaries without network collection."""
from datetime import timedelta
from bs4 import BeautifulSoup
import collect_tlvnet_events as c
def soup(s):return BeautifulSoup(s,'html.parser')
day=(c.NOW+timedelta(days=2)).strftime('%d.%m.%Y')
def row(id,clock='20:30',hall='צוותא 1',date=day):
 return f'<li class="shedule_item"><div class="shedule_it_block"><span class="shedule_date_txt">{date}</span></div><div class="shedule_it_block time">{clock}</div><div class="shedule_it_block">{hall}</div><div><a class="shedule_name_txt" href="/event/{id}">מופע {id}</a></div></li>'
plays=soup('<a href="/event/1">מחזמר</a><a href="/event/2">הצגה</a>')
music=soup('<a href="/event/1">מחזמר מוזיקלי</a><a href="/event/3">קונצרט קאמרי</a><a href="/event/4">הופעה חיה</a>')
events=c.parse_tzavta(soup(''.join(row(i) for i in range(1,6))),plays,music)
assert [e['category'] for e in events]==['theatre','theatre','music','music']
assert [e.get('concert_kind') for e in events]==[None,None,'classical','live']
for bad in [row(1,clock=''),row(1,clock='25:00'),row(1,hall='יגור'),row(1,date='01.01.2020'),row(1,date='31.02.2026')]:
 assert not c.parse_tzavta(soup(bad),plays,music)
assert all(e['city']=='tel-aviv' and e['image_rights']=='not_supplied' and e['source_url'].startswith('https://www.tzavta.co.il/event/') for e in events)
print('PASS: official theatre/music membership, musical priority, classical/live, explicit clock/date, local halls, unknown genre and no fabricated image rights')

# Habima encodes local wall-clock components as UTC epoch values.
import copy
from zoneinfo import ZoneInfo
wall=(c.NOW+timedelta(days=2)).replace(hour=20,minute=30,second=0,microsecond=0)
stamp=int(wall.replace(tzinfo=ZoneInfo('UTC')).timestamp())
data={'shows':{'he':{'p':{'title':'בדיקת הצגה','url':'https://www.habima.co.il/shows/test/'}}},'venues':{'he':{'1':'אולם רובינא','363':'אולם שרובר תאטרון ירושלים'}},'presentations':{'he':{'p':[{'id':12,'time':stamp,'venue_id':1}]}}}
detail=soup('<h1>בדיקת הצגה</h1><h2 class="content-title primary-title">דרמה היסטורית</h2>')
rows=c.parse_habima(data,{'p':detail})
assert len(rows)==1 and rows[0]['start']==wall.isoformat()
assert rows[0]['category']=='theatre' and rows[0]['image'] is None and rows[0]['image_rights']=='not_supplied'
assert rows[0]['source_occurrence_id']==12 and rows[0]['city']=='tel-aviv'
for label in ['קונצרט','הרצאה על דרמה','סיור','מופע אורח','']:
 assert not c.parse_habima(data,{'p':soup(f'<h1>בדיקת הצגה</h1><h2 class="content-title primary-title">{label}</h2>')})
for field,value in [('venue_id',363),('venue_id',999),('time',True),('time',None),('time','20:30'),('time',0)]:
 bad=copy.deepcopy(data);bad['presentations']['he']['p'][0][field]=value
 assert not c.parse_habima(bad,{'p':detail})
bad=copy.deepcopy(data);bad['venues']['he']['1']='אולם בירושלים'
assert not c.parse_habima(bad,{'p':detail})
assert not c.parse_habima(data,{})
assert not c.habima_url('https://www.habima.co.il.evil.example/shows/test/')
print('PASS: Habima wall-clock date/time, explicit play genre, hall identity, non-local/unknown/missing-clock rejection and no image-rights invention')
