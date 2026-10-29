"""Apply reviewed Kiryat Gat food sources; never infer ratings, hours or kashrut."""
import json,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'events-preview/kiryat-gat'
DATE='2026-10-29'
# Stable IDs preserve saved places. Source-specific facts, not directory reviews.
ROWS=[
('morduch','מורדוך הגדול','היוצר 22','meat','27541496'),
('namisu','נאמיסו סושי','שדרות אבני החושן 1','asian','27413316'),
('bukhari','אצל הבוכרי','דרך הדרום 9','local','26605373'),
('millennium','שיפודי המילניום','שדרות העצמאות 49','meat','1719040'),
('caprese','קפרזה','דרך הדרום 20','italian','10149957'),
('toro','שווארמה טורו','דרך הדרום — מספר הבית טעון בירור','meat','10051536'),
('you','You','היוצר 22','restaurant','26535857'),
('zoares','זוארס שווארמה וגריל בשרים','אסתר המלכה 13','meat','10115255'),
('oshi','אושי אושי','BIG כרמי גת','asian','27294812'),
('mexicani','המקסיקני','היוצר 20 — יש לוודא כתובת מול המקום','street','26516646'),
('mexicano','מקסיקנו בר גריל','אסתר המלכה','street','10129798'),
('japanika','ג׳פניקה קריית גת — Japanika Quick','אסתר המלכה 11','asian','27392925'),
('fernando','פרננדוס כרמי גת','אסתר המלכה 13','meat','10142949'),
('rotem','הקוסקוס של רותם','דרך הדרום 9','local','26582999'),
('tunisandwich','טוניסנדוויץ','המלאכה 3','street','26890873'),
('cholent','הטשולנט','נינווה 18','local','10150287'),
('special-burger','ספיישל בורגר & רול','שדרות לכיש 15','burger','10137648'),
('hapnina','הפנינה','טבת 9','restaurant','26862942'),
('cafe-lyon','קפה ליון BIG כרמי גת','שדרות לכיש 153, BIG כרמי גת','cafe','10145209'),
('bbb','BBB קריית גת','דרך הדרום 3, BIG קריית גת','burger','25985168'),
('roya','רויה רול בר','דרך הדרום 3','street','5545271'),
('cafe','קפה קפה','צומת פלוגות — מחוץ לעיר','cafe','4937703'),
('italian','האיטלקיה','שדרות לכיש 37','italian','26375919'),
('bleecker','בליקר בייקרי קריית גת','דרך הדרום — מספר הבית טעון בירור','cafe','26672522'),
('la-padel','La Padel','BIG כרמי גת','restaurant','10167840'),
('segev','הבאגט של השף שגב','שדרות לכיש 7','street','10124034'),
('fresh','פרש דה מרקט — Fresh The Market','דרך הדרום 3, BIG קריית גת','italian','https://ontopo.com/he/il/page/freshthemarketkg'),
('geronimo','ג׳רונימו — Geronimo','BIG כרמי גת — שדרות אבני החושן / שדרות לכיש','burger','27310937'),
('itzik','איציק שווארמה ובשרים על האש','שדרות לכיש 177','meat','26570122'),
('schnitzel','שניצל רחוב','שדרות לכיש — מספר הבית טעון בירור','street','26811347'),
('manhattan','מנהטן — טוסט נקניק','שדרות לכיש 16','street','25986592'),
('dani','מסעדת דני','נתרן 7, אזור התעשייה','local','https://www.qiryat-gat.muni.il/137/'),
('camila','קמילה — גריל בשרים ישראלי','ישפרו סנטר — יש לוודא כתובת מול המקום','meat','https://ontopo.com/he/il/page/34545871'),
('eliyahu','חומוס אליהו קריית גת','זרחן 13 — יש לוודא כתובת מול המקום','hummus','26234924'),
('mama','מאמא אירועי בוטיק','קריית גת — יש לוודא כתובת מול המקום','catering','3381238'),
('burgerim','בורגרים — Burgerim','שדרות מלכי ישראל — מספר הבית טעון בירור','burger','26034440'),
('perla','פרל׳ה — סנדוויץ׳ בר','שדרות מלכי ישראל 178','street','https://www.rest.co.il/rest/80379617/'),
('yanknik','יאנקניק','הרימון 1','street','https://www.rest.co.il/rest/80341479/'),
('burger-express','בורגר אקספרס','קריית גת — כתובת מדויקת במקור','burger','https://www.rest.co.il/rest/80333201/'),
('del-amor','פיצה דל אמור','שדרות העצמאות 49','pizza','https://www.rest.co.il/rest/80225592/'),
('roladin','רולדין','קריית גת — כתובת מדויקת במקור','cafe','https://www.rest.co.il/rest/80383899/'),
('cream','גלידריה קפה קרים','שדרות מלכי ישראל 178, ישפרו סנטר','dessert','https://www.rest.co.il/rest/80360941/'),
('pitzale','פיצל׳ה קריית גת','גאון הירדן 43','pizza','https://www.rest.co.il/rest/77396670/'),
('pita-street','פיתה רחוב קריית גת','שדרות מלכי ישראל 178, ישפרו סנטר','street','https://www.rest.co.il/rest/80343971/'),
('bistro-pizza','ביסטרו פיצה','מירון 1','pizza','https://www.rest.co.il/rest/80172268/'),
('potato','פוטטו סטאר','קריית גת — כתובת מדויקת במקור','street','https://www.rest.co.il/rest/80382542/'),
('oren-mashi','אורן משי — קריית גת','שדרות לכיש','bakery','https://www.rest.co.il/rest/80392577/'),
('sweet-moment','רגע מתוק','קריית גת — כתובת מדויקת במקור','cafe','https://www.rest.co.il/rest/80328206/'),
('aroma','ארומה — אספרסו בר','כיכר פ״ז 3','cafe','https://www.rest.co.il/rest/80002060/'),
('elite','קפה עלית — אספרסו בר','דרך החרושת','cafe','https://www.rest.co.il/rest/80113105/'),
('crespella','קרספלה — Crespella','נחל ירקון 147','cafe','https://www.rest.co.il/rest/80390308/'),
('labriut','לבריאות','שדרות לכיש 1','cafe','https://www.rest.co.il/rest/80283732/'),
('begahalim','בגחלים','קריית גת — כתובת מדויקת במקור','meat','https://www.rest.co.il/rest/80328321/'),
('chickchak','צ׳יק צ׳אק — ChickChak','הגבורה 30','cafe','https://www.rest.co.il/rest/80286057/'),
('cofix','קופיקס — Cofix','כיכר פ״ז 62','cafe','https://www.rest.co.il/rest/80242638/'),
('bread-station','תחנת לחם — קריית גת','דרך הדרום 20','bakery','https://www.rest.co.il/rest/80311368/'),
('yivgi','קלית יבגי','קריית גת — כתובת מדויקת במקור','cafe','https://www.rest.co.il/rest/80328579/'),
('varda','מזנון ורדה','כיכר פ״ז 4','hummus','https://www.rest.co.il/rest/80071375/'),
('falafel-square','פלאפל בכיכר','שדרות העצמאות 145','hummus','https://www.rest.co.il/rest/80344485/'),
('falafel-sabich','פלאפל סביח','הזית','hummus','https://www.rest.co.il/rest/80358030/'),
('falafel-teimani','פלאפל תימני','שדרות פ״ז','hummus','https://www.rest.co.il/rest/80332956/'),
('guettos','Guetto’s — שווארמה ובשרים על האש','יהודה 79','meat','https://www.rest.co.il/rest/80344486/'),
('shawarma-station','שווארמה בתחנה','דרך הדרום 7','meat','https://www.rest.co.il/rest/80367810/'),
('falafel-cohen','פלאפל כהן','קריית גת — כתובת מדויקת במקור','hummus','https://www.rest.co.il/rest/80366161/'),
('shawarma-square','שווארמה בכיכר','שדרות מלכי ישראל 178, ישפרו סנטר','meat','https://www.rest.co.il/rest/80373229/'),
('hummus-kgat','חומוס קריית גת','קריית גת — כתובת מדויקת במקור','hummus','https://www.rest.co.il/rest/80340777/'),
('shawarma-sali','שווארמה סאלי קריית גת','דרך הדרום 7','meat','https://www.rest.co.il/rest/80388748/'),
('shirat','שירת הגרגרים','קריית גת — כתובת מדויקת במקור','hummus','https://www.rest.co.il/rest/80338999/'),
]
LABELS={'meat':'בשרים וגריל','asian':'סושי ואסייתי','local':'אוכל ביתי','italian':'מטבח איטלקי','restaurant':'מסעדה','street':'אוכל רחוב','burger':'המבורגרים','cafe':'בית קפה','hummus':'חומוסייה','catering':'אירוח ואירועים','pizza':'פיצריה','dessert':'גלידה וקפה','bakery':'מאפייה וקונדיטוריה'}
PHOTOS={'meat':'grill','asian':'asian','local':'home','italian':'italian','restaurant':'grill','street':'street','burger':'burger','cafe':'cafe','hummus':'hummus','catering':'home','pizza':'pizza','dessert':'dessert','bakery':'cafe'}
NOTES={
 'toro':'במקורות מופיעים דרך הדרום 20 ו־22; יש לוודא את מספר הבית לפני הגעה.',
 'bleecker':'במקורות מופיעים דרך הדרום 20 ו־22; יש לוודא את מספר הבית לפני הגעה.',
 'schnitzel':'ברשימה שנמסרה מופיע לכיש 18; באיזי מופיע לכיש 14. יש לוודא מול המקום.',
 'camila':'אונטופו ואיזי מציינים מלכי ישראל 178, ישפרו סנטר; ברשימה שנמסרה מופיע ישראל פולק 49. יש לוודא את הכתובת.',
 'mama':'באיזי מופיע מבוא סיוון 8, וברשימה שנמסרה ישראל פולק 41. גם אופי האירוח טעון בירור מול המקום.',
 'burgerim':'באיזי מופיע מלכי ישראל 180, וברשימה שנמסרה 178. יש לוודא את מספר הבית.',
 'eliyahu':'באיזי מופיע זרחן 13; ברשימה שנמסרה פינת שדרות צורן. יש לוודא את הכניסה.',
 'geronimo':'המקום מזוהה עם BIG כרמי גת; המקורות מציינים רחובות שונים במתחם. מומלץ להשתמש בניווט המקושר.',
 'mexicani':'בפרופיל העסק מופיע היוצר 20, וברשימת האזור דרך הדרום 9. יש לוודא את הכתובת.',
 'manhattan':'בכותרת הפרופיל מופיע לכיש 16, ובטקסט העסק מוזכר גם סניף באסתר המלכה 11. יש לוודא את הסניף המבוקש.',
 'la-padel':'מתחם פאדל המופיע גם בקטגוריית המסעדות; יש לברר זמינות אוכל וישיבה לפני הגעה.'}
def build():
 old=json.loads((R/'data/restaurants.json').read_text())
 byid={p['id']:p for p in old['restaurants']}
 items=[]
 for id,name,address,kind,source in ROWS:
  source=source if source.startswith('https:') else 'https://easy.co.il/page/'+source
  p=byid.get('kgat-'+id,{}).copy()
  photo=PHOTOS[kind]
  p.update(id='kgat-'+id,name=name,en='',kind=kind,kinds=list(dict.fromkeys(['restaurant',kind] if kind not in ['bakery','dessert','catering'] else [kind])),label=LABELS[kind],moods=['coffee','family'] if kind in ['cafe','bakery','dessert'] else ['family','evening'],address=address+('' if 'קריית גת' in address or 'מחוץ לעיר' in address else ', קריית גת'),description=LABELS[kind]+' ב'+('סביבת קריית גת.' if id=='cafe' else 'קריית גת.')+' '+NOTES.get(id,'פרטי המקום והקשר במקור המקושר; מומלץ לבדוק תפריט ושעות לפני הגעה.'),image='assets/food/'+photo+'-illustration.jpg',image_role='illustration',image_alt='תמונת המחשה קולינרית — לא צילום מהמקום',credit='תמונת המחשה שנוצרה בבינה מלאכותית; לא צילום מהמסעדה',site=source,site_label='לפרטי המקום',source_url=source,source_label='איזי' if 'easy.co.il' in source else 'Rest' if 'rest.co.il' in source else 'אונטופו' if 'ontopo' in source else 'עיריית קריית גת',checked_at=DATE,city='kiryat-gat',area='nearby' if id=='cafe' else 'city',kosher='יש לבדוק תעודת כשרות עדכנית מול המקום.',kosherVerified=False,saturdayVerified=False,saturday_note='לא אומתה פתיחה בשבת ביום.')
  if id in NOTES:p['address_note']=NOTES[id]
  if id=='namisu':p.update(site='https://www.namisu.co.il/',site_label='לאתר המסעדה',phone='088660660',saturday_note='לפי אתר המקום: פתיחה במוצאי שבת, שעה אחרי צאת השבת.')
  if id=='japanika':p.update(site='https://japanika.net/branches/',site_label='לאתר הרשת ולפרטי הסניף',description='סניף ג׳פניקה קוויק בקריית גת, באסתר המלכה 11. מטבח אסייתי וסושי. הסניף מפורסם ככשר; באיזי מצוינת רבנות מקומית.',kosher='כשר — רבנות מקומית, לפי פרסום איזי; באתר הרשת הסניף מסומן ככשר. מומלץ לבדוק תעודה עדכנית במקום.',kosherVerified=True,kosher_verification_basis='published_branch_information',kosher_source_url='https://easy.co.il/page/27392925',official_source_url='https://japanika.net/branches/',saturday_note='לפי אתר הרשת: פתיחה במוצאי שבת, כשעה וחצי לאחר צאת השבת; לא בשבת ביום.',search_aliases=['גפניקה','ג׳פניקה','ג\'פניקה','Japanika','גפניקה קרית גת'])
  if id=='fresh':p.update(booking=source,phone='088500085',description='מסעדה איטלקית במרכז BIG קריית גת, עם ארוחות בוקר, פסטות, פיצות ודגים. תפריט והזמנת שולחן בקישור המקום.')
  items.append(p)
 result={'city':'kiryat-gat','checked_at':DATE,'restaurants':items,'coverage':{'user_list_count':20,'user_list_included':20,'scope':'Reviewed Easy regional results, Rest local cards and supplied list; not a claim of exhaustive city coverage.'}}
 (R/'data/restaurants.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 js=R/'restaurants.js';s=js.read_text();s=re.sub(r'const places=\[.*?\];',lambda _: 'const places='+json.dumps(items,ensure_ascii=False,separators=(',',':'))+';',s,count=1,flags=re.S)
 s=s.replace('isnet-yavne-food-saved','isnet-kiryat-gat-food-saved')
 if '"burger":"המבורגרים"' not in s:s=s.replace('const kinds={','const kinds={"burger":"המבורגרים","meat":"בשרים וגריל","asian":"סושי ואסייתי","italian":"איטלקי","hummus":"חומוסיות",')
 s=s.replace("esc(p.name)+'\">'","esc(p.image_alt||p.name)+'\">'")
 s=s.replace("esc(p.name)+'\" loading", "esc(p.image_alt||p.name)+'\" loading")
 s=s.replace("esc(p.name)+'\" alt", "esc(p.image_alt||p.name)+'\" alt")
 s=s.replace("צילום: '+esc(p.credit)","'+esc(p.credit)")
 js.write_text(s)
 html=R/'restaurants.html';s=html.read_text();s=s.replace('<div class="hero-photo"><small>מדריך מקומי</small></div>','<div class="hero-photo"><img src="assets/food/cafe-illustration.jpg" alt="ארוחת בוקר — תמונת המחשה שנוצרה בבינה מלאכותית" fetchpriority="high"><small>תמונת המחשה — לא צילום ממסעדה</small></div>')
 s=s.replace('מסעדות ובתי קפה בקריית גת ובסביבה, עם כתובת וקישור למקור.','מסעדות, בתי קפה, אוכל רחוב וטעמים מקומיים בקריית גת ובסביבה, עם קישורים לפרטי המקומות.')
 s=re.sub(r'restaurants.js\?v=[^"\s]+','restaurants.js?v='+hashlib.sha256(js.read_bytes()).hexdigest()[:12],s)
 s=s.replace('<script src="/assets/yavne-analytics.js?v=20261022-1" defer></script>','')
 html.write_text(s)
 print('Built',len(items),'places; all 20 supplied places included.')
if __name__=='__main__':build()
