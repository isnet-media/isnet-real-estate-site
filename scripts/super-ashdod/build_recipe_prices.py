"""Rebuild recipe reference medians from the normalized official-file snapshot.
Usage: python scripts/super-ashdod/build_recipe_prices.py /path/to/normalized-direct.json
Prices are regular listed prices, not promotions or verified stock. Product update
is retained separately from the date of the official file that lists the price.
"""
from pathlib import Path
import json,statistics,sys
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'SUPER.ASHDOD/recipes'
snapshot=json.loads(Path(sys.argv[1]).read_text());products={p['id']:p for p in snapshot['products']};branches={b['id']:b for b in snapshot['branches']}
# Pack sizes come from explicit product names or Quantity+UnitQty. No retailer
# comparison-unit conversions are used for packages. Weighted entries require
# agreement of raw-price, normalized-price and price per kg, with kg in metadata.
SELECTION={
 'redlentils':('עדשים כתומות סוגת, שקית 1 ק״ג','kg',1,['7290001041192']),
 'greenlentils':('עדשים ירוקות סוגת, שקית 1 ק״ג','kg',1,['7290001041208']),
 'rice':('אורז פרסי סוגת, 1 ק״ג','kg',1,['7290000211442']),
 'bulgur':('בורגול מיה, 500 גרם','kg',.5,['7290010153510']),
 'pasta':('ספגטי פרפקטו, 500 גרם','kg',.5,['7290000060316']),
 'couscous':('קוסקוס הנמל, 350 גרם','kg',.35,['7290002040019']),
 'tahini':('טחינה גולמית, 500 גרם','kg',.5,['7290010328253']),
 'paste':('רסק עגבניות יכין, 100 גרם','kg',.1,['7290018989333']),
 'oil':('שמן קנולה מזוכך, בקבוק 1 ליטר','liter',1,['7290002374312']),
 'breadcrumbs':('פירורי לחם מוזהבים, 200 גרם','kg',.2,['7290100700075']),
 'chickpeas':('גרגירי חומוס מבושלים קפואים, 800 גרם','kg',.8,['7290020396228']),
 'redbeans':('שעועית אדומה מבושלת טעם הטבע, 380 גרם','kg',.38,['7290112357106']),
 'corn':('גרעיני תירס קפואים וילי פוד, 800 גרם','kg',.8,['7290117264393']),
 'coconut':('חלב קוקוס, 400 מ״ל','liter',.4,['7290011996222']),
 'spinach':('תרד טבע פרוסט, 800 גרם','kg',.8,['7290013187857']),
 'cottage':('קוטג׳ טרה 5%, 250 גרם','kg',.25,['7290002868996']),
 'feta':('גבינה בולגרית EURO 13%, 200 גרם','kg',.2,['7290108509106']),
 'oats':('קוואקר שיבולת שועל, 500 גרם','kg',.5,['7290000480107']),
 'paprika':('פפריקה מתוקה, 100 גרם','kg',.1,['7290010002122']),
 'cumin':('כמון, 100 גרם','kg',.1,['7290010002030']),
 'pepper':('פלפל שחור טחון, 100 גרם','kg',.1,['7290010002078']),
 'salt':('מלח, 1 ק״ג','kg',1,['7290004063016']),
 'curry':('אבקת קארי, 80 גרם','kg',.08,['7290013677327']),
 'oregano':('אורגנו, 40 גרם','kg',.04,['7290010002382']),
 'turmeric':('כורכום טחון, 80 גרם','kg',.08,['7290010003761']),
 'cinnamon':('קינמון טחון, 80 גרם','kg',.08,['7290010003839']),
 'soy':('רוטב סויה יאמאסה, 500 מ״ל','liter',.5,['4903001904192']),
 'mushrooms':('שמפיניון טרי ארוז, 250 גרם','kg',.25,['7290006265500']),
 'wholebread':('לחם פשוט מלא אנג׳ל, 750 גרם','kg',.75,['7290014940901']),
 'pita':('פיתות אנג׳ל, 10 יחידות','piece',10,['7290020216717']),
 'eggs':('ביצים M, אריזת 12','piece',12,['7290001201596']),
 'parsley':('פטרוזיליה, צרור','piece',1,['7290010192007']),
 'raisins':('צימוקים בהירים, 300 גרם','kg',.3,['7290014094833']),
 'lettuce':('חסה ערבית בשקית, יחידה','piece',1,['7290003996018']),
 'quinoa':('קינואה סוגת, 500 גרם','kg',.5,['7290100700273']),
 'peas':('אפונה עדינה קפואה סנפרוסט, 600 גרם','kg',.6,['7290000104201']),
 'greenbeans':('שעועית ירוקה שלמה קפואה סנפרוסט, 800 גרם','kg',.8,['7290000104683']),
 'groundchicken':('חזה עוף טחון 100%, 600 גרם, מיט פלייס','kg',.6,['7290002292616']),
 'chicken':('חזה עוף טרי, במשקל','kg',None,['7290055700007:3502','7290002680161']),
 'drumsticks':('שוקי עוף טריות, במשקל','kg',None,['7290055700007:3517','7290000611839','7290000859701','7290696200003:2206033']),
 'whitefish':('פילה אמנון 100% דג תנובה, במשקל','kg',None,['7290000652542']),
 'salmon':('סלמון מנות 100% דג תנובה, במשקל','kg',None,['7290000644783']),
 'groundbeef':('בשר בקר טחון טרי, במשקל','kg',None,['7290001004746']),
 'wholechicken':('עוף שלם טרי ארוז, במשקל','kg',None,['7290000859664']),
 'carrot':('גזר רגיל, במשקל','kg',None,['7290055700007:1708','7290000000102','7290000001102']),
 'cucumber':('מלפפון רגיל, במשקל','kg',None,['7290055700007:1502','7290000000101','7290000000695']),
 'tomato':('עגבנייה רגילה, במשקל','kg',None,['7290055700007:1501','7290000000100']),
 'redpepper':('פלפל אדום רגיל, במשקל','kg',None,['7290055700007:1516','7290000000104','7290803800003:742','7290873255550:9913002','7290058173198:10128','7290696200003:2061']),
 'lemon':('לימון, במשקל','kg',None,['7290055700007:1551','7290000000117','7290000001117']),
 'eggplant':('חציל רגיל, במשקל','kg',None,['7290055700007:1511','7290000000106']),
 'zucchini':('קישוא ירוק, במשקל','kg',None,['7290055700007:1510','7290000000107']),
 'sweetpotato':('בטטה, במשקל','kg',None,['7290055700007:1574','7290000000138','7290803800003:622','7290873255550:4412319','7290785400000:102']),
 'cauliflower':('כרובית טרייה, במשקל','kg',None,['7290055700007:1507','7290873255550:4412838','7290785400000:13','7290058173198:10107']),
 'garlic':('שום יבש בתפזורת, במשקל','kg',None,['7290055700007:1883']),
 'potato':('תפוח אדמה לבן ארוז, במשקל','kg',None,['7290000000111','7290000000422']),
 'onion':('בצל יבש, במשקל','kg',None,['7290055700007:1519','7290000000108']),
 'cabbage':('כרוב לבן, במשקל','kg',None,['7290055700007:1505','7290000000109'])}
refs={};excluded=[]
for key,(name,unit,pack,ids) in SELECTION.items():
 offers=[]
 for pid in ids:
  p=products[pid]
  for o in p['offers']:
   if not o.get('eligible_for_basket') or o.get('source_type')!='official_file' or o.get('kind')!='רגיל':continue
   if pack is None:
    valid=p.get('weighted')=='1' and 'קילוגרם' in p.get('unit_quantity','') and 'קילוגרם' in o.get('raw_unit','') and abs(o['price']-o.get('raw_price',0))<.001 and abs(o['price']-float(o.get('unit_price',0)))<.01
    if not valid:excluded.append({'product_id':pid,'branch_id':o['branch_id'],'reason':'weighted_unit_disagreement'});continue
   b=branches[o['branch_id']]
   offers.append({'branch_id':b['id'],'branch_name':b['name'],'chain':b['chain'],'product_id':pid,'product_name':p['name'],'quantity':p['quantity'],'unit_quantity':p['unit_quantity'],'weighted':p['weighted'],'package_quantity':pack,'price':o['price'],'unit_price':round(o['price']/(pack or 1),8),'source_url':b['source_url'],'price_file_url':o.get('source_url') or b['price_file_url'],'file_date':b['file_date'],'product_price_updated_at':o['updated_at'],'raw_price':o.get('raw_price'),'raw_unit':o.get('raw_unit'),'files_applied':b.get('files_applied',[])})
 # Dedupe equivalent produce/meat entries per branch to avoid one branch having more weight.
 bybranch={}
 for o in offers:bybranch.setdefault(o['branch_id'],[]).append(o['unit_price'])
 unit_price=statistics.median([statistics.median(v) for v in bybranch.values()]);assert unit_price>0
 refs[key]={'name':name,'unit':unit,'unit_price':round(unit_price,8),'branch_count':len(bybranch),'product_ids':ids,'offers':offers,'selection':'explicit_product' if len(ids)==1 else 'equivalent_plain_produce_or_meat','limited_coverage':len(bybranch)<3}
reference={'updated_at':snapshot['retrieved_at'][:10],'currency':'ILS','method':'median_of_branch_regular_unit_prices','method_he':'חציון המחיר הרגיל ליחידת מידה בסניפים שנקלטו, לכל מוצר ייחוס נבחר. במוצרי ירקות ועוף שקולים מקבילים: חציון בכל סניף ואז חציון בין הסניפים. אין שימוש במחיר המינימום או במבצעים. זה אינו מחיר סל שנבדק בסניף יחיד.','quantity_assumptions':{'tablespoon_oil_liter':.015,'garlic_clove_kg':.005,'lemon_piece_kg':.15,'teaspoon_ground_spice_kg':.002,'salt_recipe_kg':.004,'pepper_recipe_kg':.0005},'references':refs,'excluded':excluded,'coverage_note':'מחיר שמופיע בקובץ אינו אישור מלאי. מועד עדכון מחיר המוצר נשמר בנפרד מתאריך הקובץ. מוצרי ייחוס עם פחות משלושה סניפים מסומנים בכיסוי מצומצם; הם אינם מדד למחיר מקובל בכל העיר. מחירי חומרי הגלם מחושבים לפי הכמות הנצרכת, ולא לפי קניית כל האריזות בשלמותן.'}
(D/'price-reference.json').write_text(json.dumps(reference,ensure_ascii=False,indent=2)+'\n')
data=json.loads((D/'recipes.json').read_text())
def C(*args):return [{'ref':ref,'quantity':qty} for ref,qty in args]
def base(oil=2,garlic=3,**spices):
 comps=C(('oil',oil*.015),('garlic',garlic*.005))
 for ref,n in spices.items():comps+=C((ref,n*.002))
 return comps+C(('salt',.004),('pepper',.0005))
# One component list for each displayed ingredient, in existing display order.
MAP={
'chicken-lentil-meatballs':[C(('groundchicken',.6)),C(('redlentils',.2)),C(('rice',.35)),C(('onion',.3)),C(('carrot',.25)),C(('tomato',.6)),C(('paste',.1)),C(('eggs',1)),C(('breadcrumbs',.04)),C(('cabbage',.5)),C(('lemon',.15)),C(('oil',.045),('garlic',.015)),C(('cumin',.002),('paprika',.002),('salt',.004),('pepper',.0005))],
'chicken-tray':[C(('drumsticks',1.3)),C(('potato',1)),C(('carrot',.3)),C(('tomato',.3)),C(('cucumber',.3)),C(('lemon',.15)),C(('oil',.045),('garlic',.02)),C(('paprika',.002),('cumin',.002),('salt',.004),('pepper',.0005))],
'lentil-bolognese':[C(('pasta',.5)),C(('redlentils',.25)),C(('mushrooms',.25)),C(('tomato',.6)),C(('paste',.1)),C(('onion',.2)),C(('carrot',.15)),C(('lettuce',.5)),C(('cucumber',.4)),C(('tahini',.08)),C(('lemon',.15)),base(2,3,oregano=1)],
'chickpea-shakshuka':[C(('eggs',8)),C(('chickpeas',.48)),C(('tomato',.8)),C(('redpepper',.3)),C(('onion',.2)),C(('pita',5)),C(('cucumber',.5)),C(('tomato',.3)),C(('lemon',.15)),base(3,3,paprika=1,cumin=.5)],
'chicken-rice-stir-fry':[C(('chicken',.6)),C(('rice',.35)),C(('cabbage',.4)),C(('carrot',.2)),C(('redpepper',.3)),C(('soy',.045)),C(('lemon',.075)),C(('lemon',.075)),base(3,3)],
'bean-sweet-potato-chili':[C(('redbeans',.48)),C(('sweetpotato',.7)),C(('corn',.285)),C(('tomato',.6)),C(('paste',.1)),C(('onion',.2)),C(('rice',.35)),C(('tahini',.1)),C(('lemon',.075)),base(2,3,paprika=1,cumin=1)],
'fish-meatballs':[C(('whitefish',.75)),C(('eggs',1)),C(('breadcrumbs',.05)),C(('onion',.2)),C(('redpepper',.3)),C(('tomato',.5)),C(('paste',.1)),C(('couscous',.35)),C(('chickpeas',.2)),C(('parsley',1)),base(2,4,paprika=1,cumin=1)],
'mujaddara-cauliflower':[C(('greenlentils',.35)),C(('rice',.35)),C(('onion',.6)),C(('cauliflower',1)),C(('tomato',.6)),C(('cucumber',.4)),C(('tahini',.1)),C(('lemon',.15)),C(('parsley',1)),base(4,0,cumin=1,turmeric=.5)],
'zucchini-cheese-bake':[C(('zucchini',.6)),C(('potato',.6)),C(('cottage',.5)),C(('feta',.1)),C(('eggs',5)),C(('oats',.08)),C(('onion',.15)),C(('tomato',.35),('cucumber',.35)),C(('wholebread',.25)),C(('lemon',.15)),base(2,0)],
'lentil-coconut-curry':[C(('redlentils',.25)),C(('chickpeas',.4)),C(('coconut',.4)),C(('spinach',.2)),C(('tomato',.3)),C(('carrot',.3)),C(('onion',.2)),C(('rice',.35)),C(('cucumber',.5)),C(('lemon',.15)),base(2,3,curry=2)],
'chicken-bulgur':[C(('chicken',.6)),C(('bulgur',.35)),C(('chickpeas',.3)),C(('carrot',.3)),C(('onion',.2)),C(('raisins',.05)),C(('tomato',.3)),C(('cucumber',.3)),C(('parsley',1)),C(('lemon',.15)),C(('tahini',.08)),base(2,0,cumin=1,paprika=1,cinnamon=.25)],
'eggplant-chicken-siniya':[C(('groundchicken',.6)),C(('eggplant',1)),C(('tahini',.12)),C(('tomato',.7)),C(('cucumber',.4)),C(('onion',.2)),C(('pita',5)),C(('parsley',1)),C(('lemon',.15)),base(2,3,cumin=1,paprika=1)]}
for r in data['recipes']:
 components=MAP.get(r['slug'],[x['components'] for x in r['ingredients']])
 assert len(components)==len(r['ingredients'])
 for ingredient,comps in zip(r['ingredients'],components):
  ingredient['components']=comps;ingredient['cost']=round(sum(refs[c['ref']]['unit_price']*c['quantity'] for c in comps),2)
 r['total']=round(sum(x['cost'] for x in r['ingredients']),2)
 r['pricing_status']='official_reference_cost';r['price_date']=reference['updated_at']
# Align ingredient labels and preparation with the precise priced form.
for r in data['recipes']:
 for x in r['ingredients']:
  if x['name']=='חומוס מבושל משימורים':x.update(name='גרגירי חומוס מבושלים קפואים',amount='480 גרם, מופשרים לפי הוראות האריזה')
  if x['name']=='חומוס מבושל קפוא או ביתי':x.update(name='גרגירי חומוס מבושלים קפואים',amount='400 גרם')
  if x['name']=='חומוס מבושל':x['name']='גרגירי חומוס מבושלים קפואים';x['amount']=x['amount'].replace(', מסונן','')
  if x['name']=='שעועית אדומה מבושלת משימורים':x.update(name='שעועית אדומה מבושלת, טעם הטבע',amount='480 גרם, מתוך אריזות של 380 גרם')
  if x['name']=='תירס משימורים':x.update(name='גרעיני תירס קפואים',amount='285 גרם')
  if x['name']=='פיתות מלאות':x.update(name='פיתות',amount='5 יחידות, מתוך אריזת 10')
  if x['name']=='פיתות':x['amount']='5 יחידות, מתוך אריזת 10'
  if x['name']=='ספגטי, אפשר מלא':x['name']='ספגטי'
  if x['name']=='קרם או חלב קוקוס לא ממותק':x['name']='חלב קוקוס'
  if x['name']=='ג׳ינג׳ר טרי':x.update(name='לימון לגרידה ולמיץ',amount='חצי לימון, כ־75 גרם')
  if x['name']=='פילה דג לבן קפוא ללא עצמות':x.update(name='פילה אמנון קפוא, 100% דג',amount='750 גרם, להפשיר לפי הוראות האריזה ולבדוק עצמות')
  if x['name']=='חזה עוף טחון':x.update(name='חזה עוף טחון 100%, קפוא',amount='600 גרם, להפשיר במקרר לפי הוראות האריזה')
 r['steps']=[s.replace('ג׳ינג׳ר','גרידת לימון').replace('ג’ינג’ר','גרידת לימון').replace('גינגר','גרידת לימון').replace('שוטפים ומסננים את השעועית והתירס','מכינים את השעועית המבושלת ואת התירס הקפוא לפי הוראות האריזות').replace('מסננים ושוטפים את השעועית והתירס','מכינים את השעועית המבושלת ואת התירס הקפוא לפי הוראות האריזות').replace('שוטפים ומסננים את החומוס','מפשירים את החומוס המבושל לפי הוראות האריזה').replace('מסננים ושוטפים את החומוס','מפשירים את החומוס המבושל לפי הוראות האריזה') for s in r['steps']]
 r['steps']=[s.replace('פיתות מלאות','פיתות').replace('קוצצים שום וגרידת לימון','קוצצים שום ומגררים מעט קליפת לימון שטוף') for s in r['steps']]
data.update(updated_at=reference['updated_at'],pricing='official_reference_ingredient_usage',price_reference='price-reference.json')
(D/'recipes.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
for r in data['recipes']:print(r['slug'],r['total'])
print('Counts',[(n,sum(r['total']<=n for r in data['recipes'])) for n in [50,75,100]])
