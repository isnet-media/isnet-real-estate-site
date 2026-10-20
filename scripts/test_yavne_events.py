from bs4 import BeautifulSoup
from sync_yavne_events import community_rows,SOURCES
from sync_events_from_sources import smarticket_rows
s=BeautifulSoup('<a href="/show?id=20">22 אוקטובר קליף והצלליות פרטים נוספים קליף והצלליות מוזיקה היכל התרבות יבנה ביום חמישי, 22 באוקטובר 2026 בשעה 20:30</a>','html.parser')
a=smarticket_rows(s,next(s for s in SOURCES if s["name"]=="htyavne"));assert len(a)==1 and a[0]['start_date']=='2026-10-22' and a[0]['start_time']=='20:30';assert a[0]['purchase_url'].endswith('id=20')
s=BeautifulSoup('<a href="https://yavne-matnasim.smarticket.co.il/show?id=22">בוקר של תרבות יום שני, 26.10.2026 10:00 מרכז קהילתי נאות שזר לפרטים נוספים</a><a href="/login">כניסה</a>','html.parser')
a=community_rows(s,next(s for s in SOURCES if s["name"]=="yavne_community"));assert len(a)==1 and a[0]['title']=='בוקר של תרבות' and a[0]['start_date']=='2026-10-26';assert 'נאות שזר' in a[0]['venue']
print('Yavne source adapters: date, time, direct link and login rejection passed')

from sync_yavne_events import structured_rows
s=BeautifulSoup('<script type="application/ld+json">{"@type":"Event","name":"מופע ביבנה","startDate":"2026-10-22T17:30:00Z","location":{"name":"היכל התרבות יבנה"}}</script>','html.parser')
a=structured_rows(s,next(s for s in SOURCES if s['name']=='makore_yavne'));assert a[0]['start_time']=='20:30',a
print('Yavne UTC-to-Israel event time conversion passed')
