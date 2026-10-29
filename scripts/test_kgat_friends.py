"""Regression checks for local occurrence isolation and scoped member offers."""
from datetime import date
from sync_kgat_friends import extract,enrich

def card(title,venue,day='05.11.26',time='17:30'):
 return f'''<div class="search_show_row"><a href="https://friends-hist.co.il/show/yuval"><h3>{title}</h3></a><div class="tooltip-show-content">מומלץ החל מגיל 4 משך ההצגה 90 דקות</div><p class="tooptip-regular-price">מחיר רגיל: 99 ₪</p><p class="tooptip-discounted-price">מחיר לחברי ההסתדרות: 49 ₪</p><div class="events_list"><div class="wrap_item"><div class="hall-name-wrap">{venue}</div><div class="wrap_event">יום חמישי {day} {time}<a data-event_id="123">להזמנה</a></div></div></div></div>'''
html=card('יובל המבולבל – המסע אל הכוכב','היכל התרבות קרית גת.')+card('יובל המבולבל – המסע אל הכוכב','היכל התרבות יבנה')+card('יובל המבולבל – המסע אל הכוכב','היכל התרבות קרית גת.','01.10.26')
rows=extract(html,today=date(2026,10,29));assert len(rows)==1
assert rows[0]['member_price']==49 and rows[0]['regular_price']==99
old={'events':[{'event_id':'stable-id','title':'יובל המבולבל - בהצגה המסע אל הכוכב','city':'קריית גת','venue':'היכל התרבות קרית גת','start_date':'2026-11-05','start_time':'17:30','description':'תיאור ידני','description_manual_override':True,'image_url':'assets/approved.jpg','image_publishable':True}]}
data,report=enrich(old,rows,'2026-10-29T00:00:00Z');assert not report['new'] and len(report['matched'])==1
assert data['events'][0]['event_id']=='stable-id' and data['events'][0]['description']=='תיאור ידני'
assert data['events'][0]['image_url']=='assets/approved.jpg'
assert data['events'][0].get('price_min_ils') is None # Member price is never a general price.
assert data['events'][0]['friends_offer']['member_price_ils']==49
assert old['events'][0].get('friends_offer') is None
again,report=enrich(data,rows,'2026-10-29T00:00:00Z');assert again==data and not report['new']
ambiguous={'events':old['events']+[dict(old['events'][0],event_id='other-id')]};_,report=enrich(ambiguous,rows,'now');assert report['held'] and not report['matched']
print('PASS: FRIENDS city/date isolation, exact occurrence aliases, member pricing, locked copy, preserved photographs, idempotency and ambiguity hold')
