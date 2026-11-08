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
