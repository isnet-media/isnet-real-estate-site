"""Prevent senior classes, away fixtures and midnight placeholder regressions."""
from datetime import date
from kgat_sport_rules import sport_kind,repair,eligible
from sync_kgat_sports import football,basket_rows,TEAMS
for t in ['תנועה וספורט לגיל השלישי עם לנה בורוכוב','אימון זיכרון','הרצאה על ספורט ובריאות','הליכה בעקבות ההיסטוריה','תחרות בישול','תחרות תחפושות']:
 assert sport_kind(t) is None,t
for t in ['אימון פתוח לחודש המודעות לסרטן השד','צעדה עירונית','אליפות שחייה','טורניר כדורסל','מרוץ הלילה']:
 assert sport_kind(t),t
e=repair({'title':'תנועה וספורט לגיל השלישי עם לנה','category':'sport','category_memberships':[{'category':'sport'}]})
assert e['category']=='seniors' and not any(m['category']=='sport' for m in e['category_memberships']) and 'seniors' in e['audiences']
def row(home,away,day='01/11/2026',time='00:00',venue=''):
 return '<a class="table_row" href="/leagues/games/game/?game_id=-1">'+''.join('<div class="table_col"><span class="sr-only">label</span>'+x+'</div>' for x in [day,home+' - '+away,venue,time,''])+'</a>'
html=row('מכבי קריית גת','מכבי יפו')+row('הפועל עכו','מכבי קריית גת')+row('מכבי קריית גת','חופשית')+row('מכבי קריית גת','מכבי יפו','01/01/2020')*7
games=football(html,TEAMS[0],date(2026,10,29));assert len(games)==1
g=games[0];assert g['start_time'] is None and g['time_status']=='pending' and g['venue_status']=='pending'
assert 'game_id=-1' not in g['ticket_url'] and eligible(g)
html=row('מכבי קריית גת','מכבי יפו',time='15:00',venue='רחובות אצטדיון עירוני')*10
assert football(html,TEAMS[0],date(2026,10,29))[0]['location_scope']=='outside_city'
game={'date':'2026-11-10T18:30:00','home':{'team':'א.ס. אשקלון/קרית גת','points':None},'away':{'team':'הפועל חיפה'},'status':'future','link':'https://ibasketball.co.il/match/779129/','venues':[19389]}
games=basket_rows([game],date(2026,10,29),{'19389':'רח׳ אבני החושן, קרית גת'})
assert len(games)==1 and games[0]['start_time']=='18:30' and games[0]['location_scope']=='city'
game['home'],game['away']=game['away'],game['home'];assert not basket_rows([game],date(2026,10,29))
print('PASS: sport scope, seniors routing, home-only adult teams, missing times and venues, outside-city labeling, basketball home/away')
