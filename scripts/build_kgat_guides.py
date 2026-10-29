"""Reviewed local directories. No inferred opening hours, prices or real photographs."""
import json,re
from datetime import date
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'events-preview/kiryat-gat';D=R/'data';today=date.today().isoformat()
def save(name,value):(D/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
tour='https://qiryat-gat.muni.il/תיירות-בקרית-גת-וסביבתה/'
places=json.loads((D/'places.json').read_text())
def p(id,name,desc,source,area='קריית גת',**kwargs):return dict(id='kgat-'+id,name=name,description=desc,source_url=source,museum_url=source,operator_website_url=source,map_query=name+' '+area,location=area,badges=[area],checked_at=today,**kwargs)
parks=[p('paz','פארק פ״ז','מדשאות, מתקני משחק ופארק הסיפור „תירס חם” במרכז העיר. מקום לפיקניק ולבילוי משפחתי.',tour),p('archaeology','הפארק הארכאולוגי חרבת פאטוט','פארק בלב אזור התעשייה, עם שרידים ארכאולוגיים, מתקני משחק ומסלול רכיבה. בדקו גישה ופעילות לפני ביקור.',tour)]
culture=[p('hall','היכל התרבות אדית פולק','הבמה העירונית למוזיקה, תיאטרון, סטנדאפ והקרנות סרטים. לוח המועדים והכרטיסים באתר המארגן.','https://matnaskg.smarticket.co.il/'),p('library','הספרייה העירונית','שעות סיפור, סדנאות ומפגשי ספרות; הפעילויות המתוארכות מופיעות בלוח הילדים והקהילה.','https://matnaskg.org.il/events/'),p('rachel','בית רחל וישראל פולק','הצגות לילדים, פעילויות קהילה ומפגשים. הזמנה לפי האירוע בלוח העירוני.','https://matnaskg.smarticket.co.il/'),p('tenufa','מרכז תנופה','הרצאות ומפגשים בנושאי הורות, קריירה וכלכלה לצד פעילויות קהילתיות.','https://matnaskg.org.il/events/'),p('wax','בית וקס','מפגשים והרצאות לגיל השלישי ופעילויות קהילה; יש לבדוק את פרטי ההרשמה בכל אירוע.','https://matnaskg.org.il/events/'),p('amphi','אמפיתאטרון קריית גת','מתחם מופעים תחת כיפת השמיים. הכניסה בהתאם לפרסום המארגן לכל אירוע.',tour)]
nature=[p('lachish','גן לאומי תל לכיש','מרכז מבקרים, שרידי עיר קדומה ותצפיות על השפלה. מחוץ לעיר; הרשמה ומצב פתיחה באתר רשות הטבע והגנים.','https://www.parks.org.il/reserve-park/lachish/','חבל לכיש — מחוץ לעיר'),p('angels','יער המלאכים–שחריה','מסלולים וחניוני פיקניק ממזרח לעיר. לפי הודעת קק״ל: חניון המשפחות, בית היערן והשירותים סגורים לעבודות; יש לבדוק הודעות עדכניות לפני היציאה.','https://www.kkl.org.il/travel/kkl_shahariya_forest/','סביבת קריית גת',notice='סגירה חלקית ועבודות — יש לבדוק באתר קק״ל'),p('beit-guvrin','גן לאומי בית גוברין–מרשה','מערות ומורשת בארץ אלף המערות. מחוץ לעיר; מסלולים, כרטיסים ומגבלות ביקור לפי רשות הטבע והגנים.','https://www.parks.org.il/reserve-park/bet-guvrin/','סביבת קריית גת')]
attractions=[p('country','קאנטרי ארבע העונות','מתחם בריכות ושחייה בעיר. שעות, מסלולי כניסה ורחצה נפרדת יש לברר אצל המפעיל.',tour),*parks]
for key,items in [('parks',parks),('culture',culture),('nature',nature),('attractions',attractions),('must-see',[parks[0],culture[0],culture[-1],nature[0]])]:
 places['categories'][key]['items']=items
save('places',places)
save('attractions-guide',{'items':[],'verified_sources':[dict(x,kind='outdoor' if x in parks else 'water',audiences=['families','kids','adults']) for x in attractions]})
save('institutions',{'institutions':culture})
# Opening hours are verified on the park operator's current page, not assumed.
save('saturday-guide',{'items':[{'id':'kgat-lachish-saturday','title':'גן לאומי תל לכיש','kind':'nature','area':'nearby','city':'חבל לכיש — מחוץ לקריית גת','venue':'גן לאומי תל לכיש','description':'שרידי העיר הקדומה, תצפית ומרכז מבקרים. הכניסה למרכז המבקרים בהזמנה מראש.','family':True,'saturday_hours':'08:00–16:00 (שעון חורף)','saturday_verified':True,'source_url':'https://www.parks.org.il/reserve-park/lachish/','checked_on':today,'recheck_on':today,'booking_url':'https://www.parks.org.il/reserve-park/lachish/','price':None,'note':'שעות ומגבלות עשויות להשתנות; יש לבדוק במקור לפני יציאה.'}]})
# Culinary inventory has its own reviewed sources and media provenance.
from expand_kgat_food import build as build_food
build_food()
