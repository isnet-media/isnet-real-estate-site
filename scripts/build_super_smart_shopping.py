"""Publish curated same-size brand comparisons using verified branch shelf offers."""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import json,re,gzip
ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/'SUPER.ASHDOD'; DATA=SITE/'data'
GROUPS=[
 {'id':'rice','title':'אורז פרסי','size':'1 ק״ג','amount':1000,'unit':'גרם','note':'אותו סוג אורז ואותו משקל. מקור הגידול, דרגת המיון והכשרות עשויים להשתנות.','products':[
 ('7290000211442','סוגת',False),('7290020505538','רמי לוי',True),('7290118520009','קרפור',True),('7290018571712','מיה',False),('7290019393856','האופה',False),('7290117907733','שקדיה',False),('7296073705291','RIZELLE',False)]},
 {'id':'pasta','title':'פסטה ספגטי רגילה','size':'500 גרם','amount':500,'unit':'גרם','note':'ספגטי רגילה באותו משקל; עובי האטרייה, זמני הבישול והכשרות עשויים להשתנות. לא משווים כאן פסטה מלאה, ללא גלוטן או כוסמין.','products':[
 ('7290000060880','אסם',False),('3560071382865','קרפור',True),('7290119673537','רמי לוי',True),('7290117769676','רמי לוי',True),('8076800195057','ברילה',False),('8004690051573','לה מוליזנה',False),('8003740005054','אריגי',False),('7296073124399','מוריני',False),('7296073706502','MANTANINO',False)]},
 {'id':'cottage','title':'קוטג׳ 5%','size':'250 גרם','amount':250,'unit':'גרם','note':'אותו אחוז שומן ואותו משקל. מרקם, טעם, רכיבים, ערכים תזונתיים וכשרות לא אומתו כזהים.','products':[
 ('7290000041445','תנובה',False),('7290002868996','טרה',False),('7290004127329','תנובה',False)]},
 {'id':'peas','title':'אפונה עדינה קפואה','size':'600 גרם','amount':600,'unit':'גרם','note':'אפונה עדינה קפואה באותו משקל. גודל האפונה, מקור הגידול, המיון והכשרות עשויים להשתנות.','products':[
 ('7290000104201','סנפרוסט',False),('7290000103549','סנפרוסט',False),('7290019981688','ערוגות המשק',False),('7290004537265','שדה בשקית',False),('7290018564028','רמי לוי',True),('7290003359257','ויליגר טבע',False),('7290017616339','יוחננוף',True)]}
]
# Explicit food-type rules. Package quantities must be verified separately.
RULES={
 'rice':(r'אורז פרסי',r'מלא|תערובת|מוכן|לתינוק'),
 'pasta':(r'ספגטי',r'מלא|חיטה מל|כוסמ|קמח כוס|גלוטן|חומוס|עדשים|מנה חמה|רוטב|קונגאק|ספגטיני|טריקול|טרקול|פרפלה|ספגטי שט|ספגטי אורגני מכיל חי'),
 'cottage':(r'קוטג.*(?<![0-9.])5\s*%',r'זיתי|סיב|עם סי|בצל|טעם'),
 'peas':(r'אפונה.*עדינה|אפונה עדינה',r'גזר|מרק|תרמיל|משומר|שימור|יבש|פריכ'),
}
NEW=[
 ('basmati','אורז בסמטי','1 ק״ג',1000,r'אורז.*בסמטי',r'מלא|תערובת|מוכן'),
 ('jasmine','אורז יסמין','1 ק״ג',1000,r'אורז.*יסמין',r'מלא|תערובת|מוכן'),
 ('sugar','סוכר לבן','1 ק״ג',1000,r'סוכר לבן',r'חום|קנים|וניל|אבקת'),
 ('flour','קמח חיטה לבן רגיל','1 ק״ג',1000,r'קמח.*(?:חיטה לבן|לבן)',r'מלא|סיב|תופח|כוסמין|פיצה|לחם|עוג|חלה|דורום|פסטה|ללא גלוטן'),
 ('penne','פסטה פנה רגילה','500 גרם',500,r'(?:^|\s)פנה(?:\s|$)',r'מלא|חיטה מל|כוסמ|קמח כוס|גלוטן|חומוס|עדשים|רוטב|דפנה|טריקול|טרקול|פנה חיטה$'),
 ('fusilli','פסטה פוזילי רגילה','500 גרם',500,r'פוזילי|פוסילי',r'מלא|חיטה מל|כוסמ|קמח כוס|גלוטן|חומוס|עדשים|טריקול|טרקול|רוטב|פוזילי חי$|פוזילי טר$'),
 ('lentils-green','עדשים ירוקות יבשות','500 גרם',500,r'עדשים ירוק',r'שימור|מבושל|מוכן|נבט|מרק|פסטה|פריכ|זוג|קמח'),
 ('lentils-red','עדשים אדומות יבשות','500 גרם',500,r'עדשים אדומ|עדשים כתומ',r'שימור|מבושל|מוכן|נבט|מרק|פסטה|פריכ|זוג|קמח'),
 ('lentils-green-kg','עדשים ירוקות יבשות','1 ק״ג',1000,r'עדשים ירוק',r'שימור|מבושל|מוכן|נבט|מרק|פסטה|פריכ|זוג|קמח'),
 ('tahini','טחינה גולמית רגילה','500 גרם',500,r'טחינה',r'חומוס|סלט|מלא|שוק|חרוב|ממרח|מוכנה|לחיץ|עוג|חציל|מעודנת|אורגני|מתובל|עם שומשו|משומשו'),
 ('couscous','קוסקוס בינוני רגיל','500 גרם',500,r'קוסקוס.*בינוני|בינוני.*קוסקוס',r'מלא|כוסמין|גלוטן|מוכן|מרק'),
 ('white-cheese','גבינה לבנה 5%','250 גרם',250,r'גבינ.*לבנ.*(?<![0-9.])5\s*%',r'טעם|זיתי|בצל|סיב|עזים'),
 ('frozen-corn','גרעיני תירס קפואים','800 גרם',800,r'גרעיני תירס|תירס קפוא',r'קלח|שניצל|חטיף|פריכ|שימור|מתוק|לייט|קל '),
 ('green-beans','שעועית ירוקה שלמה קפואה','800 גרם',800,r'שעועית ירוקה.*שלמה|שעועית.*שלמה.*ירוקה',r'חתוכ|עדינה|מרק|שימור|רוטב'),
]
for gid,title,size,amount,include,exclude in NEW:
 GROUPS.append({'id':gid,'title':title,'size':size,'amount':amount,'unit':'גרם','note':'אותו סוג מוצר ובאותו משקל אריזה. רכיבים, מקור גידול, טעם, כשרות וערכים תזונתיים עשויים להשתנות; בדקו את האריזה.','products':[]})
 RULES[gid]=(include,exclude)

def package_grams(p):
 try:q=Decimal(p.get('quantity') or '0')
 except:return None
 unit=p.get('unit_quantity','')
 if unit in ('גרם','גרמים'):return q
 if unit in ('קילוגרם','קילוגרמים','ק״ג','ק"ג'):return q*1000
 return None

def brand_label(p):
 name=p['name']
 known=[('רמי לוי',r'רמי\s*לוי'),('שופרסל',r'שופרסל'),('קרפור',r'קרפור|Carrefour'),('יוחננוף',r'יוחננוף'),('סוגת',r'סוגת'),('אסם',r'אסם'),('ברילה',r'ברילה'),('סנפרוסט',r'סנפרוסט'),('מיה',r'מיה'),('תנובה',r'תנובה'),('טרה',r'טרה'),('שטראוס',r'שטראוס'),('שקדיה',r'שקדיה'),('רומו',r'רומו'),('ליגורי',r'ליגורי|LIGUORI'),('לה מוליזנה',r'מוליזנה'),('ויליגר',r'ויליגר'),('אחוה',r'אחוה'),('אל ארז',r'אל ארז'),('הר ברכה',r'הר ברכה'),('טעמן',r'טעמן'),('תבואות',r'תבואות')]
 for label,pattern in known:
  if re.search(pattern,name,re.I):return label,label in ('רמי לוי','שופרסל','קרפור','יוחננוף')
 manufacturer=p.get('manufacturer','')
 return ('יצרן: '+manufacturer if manufacturer and manufacturer not in ('לא ידוע','שונות',',','כללי') else 'לפי שם המוצר'),False

def cents(v):return int((Decimal(str(v))*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
def build():
 catalog=json.loads((DATA/'catalog.json').read_text()); shards={};groups=[]
 all_products={}
 for f in sorted((DATA/'offers').glob('*.json')):
  shard=json.loads(f.read_text());shards[f.stem]=shard;all_products.update(shard)
 # The same GTIN's official metadata can verify size when an older merged row
 # has no unit. Never infer grams from an unlabelled numeric quantity.
 extra_sizes={}
 snapshot=ROOT/'scripts/super-ashdod/shufersal-20261021.json.gz'
 if snapshot.exists():
  for p in json.loads(gzip.decompress(snapshot.read_bytes()))['products']:
   if p.get('weighted')=='0' and package_grams(p):extra_sizes[p['id']]=package_grams(p)

 for spec in GROUPS:
  group={k:v for k,v in spec.items() if k!='products'};group['products']=[]
  members=list(spec['products']);seen={p[0] for p in members}
  include,exclude=RULES[spec['id']]
  for pid,p in sorted(all_products.items()):
   if pid in seen or p.get('weighted')!='0' or p.get('calculation_unit')!='package':continue
   if not re.search(include,p['name'],re.I) or re.search(exclude,p['name'],re.I):continue
   grams=package_grams(p) or extra_sizes.get(pid)
   if grams!=spec['amount']:continue
   brand,private=brand_label(p);members.append((pid,brand,private));seen.add(pid)
  for pid,brand,private in members:
   key=pid[-2:]
   if key not in shards:shards[key]=json.loads((DATA/'offers'/f'{key}.json').read_text())
   p=shards[key].get(pid)
   if not p:continue
   assert p['weighted']=='0' and p['calculation_unit']=='package'
   if p['unit_quantity'] in ('גרם','גרמים'):assert Decimal(p['quantity'])==spec['amount'],pid
   offers=[]
   for o in p['offers']:
    if o.get('kind')=='רגיל' and o.get('source_type')=='official_file' and o.get('eligible_for_basket') is True and o.get('calculation_unit')=='package' and o.get('price',0)>0:
     offers.append({'branch_id':o['branch_id'],'price_cents':cents(o['price']),'updated_at':o.get('updated_at')})
   group['products'].append({'id':pid,'name':p['name'],'brand':brand,'private_label':private,'offers':offers})
  if len(group['products'])>=2:groups.append(group)
 branches=[{k:b.get(k) for k in ('id','chain','name','address','source_url','price_file_url','file_date')} for b in catalog['branches']]
 result={'schema_version':1,'retrieved_at':catalog['retrieved_at'],'branches':branches,'groups':groups,'method':'Reviewed food-type rules and curated exact-size GTIN groups. Compare only official regular shelf prices in the same branch and snapshot. Cheapest includes the selected reference itself. No price imputation, stock confirmation, nutrition or quality equivalence claim. Savings apply only to the selected demonstration list, not the full family basket. Private labels are curated or explicitly named in the source product name, never inferred from price or manufacturer alone.'}
 # Groups without a price in a branch remain explicitly unavailable in the UI.
 assert all(any(o['branch_id']==b['id'] for g in groups for p in g['products'] for o in p['offers']) for b in branches)
 (DATA/'smart-shopping.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(f'Smart shopping: {len(groups)} groups, {len(branches)} branches, {sum(len(g["products"]) for g in groups)} curated products')
 return result
if __name__=='__main__':build()
