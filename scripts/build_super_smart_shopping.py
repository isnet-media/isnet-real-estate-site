"""Publish curated same-size brand comparisons using verified branch shelf offers."""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import json
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
def cents(v):return int((Decimal(str(v))*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
def build():
 catalog=json.loads((DATA/'catalog.json').read_text()); shards={};groups=[]
 for spec in GROUPS:
  group={k:v for k,v in spec.items() if k!='products'};group['products']=[]
  for pid,brand,private in spec['products']:
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
  groups.append(group)
 branches=[{k:b.get(k) for k in ('id','chain','name','address','source_url','price_file_url','file_date')} for b in catalog['branches']]
 result={'schema_version':1,'retrieved_at':catalog['retrieved_at'],'branches':branches,'groups':groups,'method':'Curated same-type and equal-package-size groups. Compare only official regular shelf prices in the same branch and snapshot. Cheapest includes the selected reference itself. No price imputation, stock confirmation, nutrition or quality equivalence claim. Savings apply only to the selected demonstration list, not the full family basket. Private labels are explicitly curated, never inferred from price.'}
 for b in branches:
  assert all(any(o['branch_id']==b['id'] for p in g['products'] for o in p['offers']) for g in groups),(b['id'],'missing group')
 (DATA/'smart-shopping.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(f'Smart shopping: {len(groups)} groups, {len(branches)} branches, {sum(len(g["products"]) for g in groups)} curated products')
 return result
if __name__=='__main__':build()
