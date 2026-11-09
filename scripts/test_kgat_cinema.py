"""Screening dates and city boundaries, independent of live-site availability."""
from datetime import datetime
from zoneinfo import ZoneInfo
from refresh_kgat_cinema import parse
NOW=datetime(2026,11,9,12,tzinfo=ZoneInfo('Asia/Jerusalem'))
def card(title,day,time,venue='היכל התרבות קרית גת',category='סרטים'):
 return f'<a class="show" href="film"><h2>{title}</h2><div class="date_container">ביום רביעי, {day}</div><div class="time_container">בשעה {time}</div><div class="theater_container">{venue}</div><div class="category">{category}</div></a>'
assert parse(card('סרט עתידי','11 בנובמבר 2026','20:00'),NOW)==[{'title':'סרט עתידי','date':'2026-11-11','time':'20:00','booking_url':'https://matnaskg.smarticket.co.il/film'}]
assert not parse(card('עבר','4 בנובמבר 2026','20:00'),NOW)
assert not parse(card('עיר אחרת','11 בנובמבר 2026','20:00','היכל התרבות אשדוד'),NOW)
assert not parse(card('הצגה','11 בנובמבר 2026','20:00',category='תיאטרון'),NOW)
assert not parse(card('שעה חסרה','11 בנובמבר 2026','טרם פורסמה'),NOW)
assert not parse(card('תאריך שגוי','31 בנובמבר 2026','20:00'),NOW)
assert len(parse(card('ערב','9 בנובמבר 2026','20:00'),NOW))==1
print('Cinema parser: exact dates/times, future filtering and city isolation passed')
