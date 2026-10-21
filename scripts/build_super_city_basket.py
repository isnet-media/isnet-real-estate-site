"""Build fixed grocery comparison baskets from the public official-feed snapshot.
Packages use fixed GTINs. Fresh weighted lines use an editorial candidate list
for the same kind and quantity, with explicit kg metadata and matching raw price.
Ambiguous units, absent prices and partial baskets never contribute to rankings.
"""
from pathlib import Path
from decimal import Decimal,ROUND_HALF_UP
import json,re
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'SUPER.ASHDOD'
def cents(n):return int((Decimal(str(n))*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
def kg_unit(s):return bool(re.fullmatch(r'(?:1\s*)?(?:קילוגרמים?|קילוגרם|ק[״\"]?ג)',str(s).strip()))
def build_variant(definition,catalog,variant):
 rows={r[0]:r for r in catalog['rows']};shards={};products=[]
 def product(pid):
  key=pid[-2:]
  if key not in shards:
   path=D/'data/offers'/f'{key}.json';shards[key]=json.loads(path.read_text()) if path.exists() else {}
  return shards[key].get(pid)
 for item in definition:
  assert item['quantity']>0
  candidates=item.get('candidates',[item['id']]);known=[product(pid) for pid in candidates if product(pid)]
  if item.get('pricing_unit')!='kg':
   assert all(p.get('weighted')=='0' and p.get('calculation_unit')=='package' for p in known),item['id']
  products.append({**item,'source_name':known[0]['name'] if known else rows.get(item['id'],['',''])[1],'pricing_unit':item.get('pricing_unit','whole_package')})
 branches=[]
 for branch in catalog['branches']:
  lines=[]
  for item in products:
   matches=[]
   for pid in item.get('candidates',[item['id']]):
    p=product(pid)
    if not p:continue
    for o in p.get('offers',[]):
     if o['branch_id']!=branch['id'] or o.get('source_type')!='official_file' or o.get('kind')!='רגיל' or o.get('eligible_for_basket') is not True or o.get('price',0)<=0:continue
     if item['pricing_unit']=='kg':
      # Both source product and offer must explicitly indicate kg. No guessing
      # from plausible prices and no blind conversion of malformed gram fields.
      if p.get('weighted')!='1' or not kg_unit(p.get('unit_quantity')) or not kg_unit(o.get('raw_unit')) or o.get('calculation_unit')!='kg' or o.get('raw_price') is None or cents(o['price'])!=cents(o['raw_price']):continue
     elif o.get('calculation_unit')!='package':continue
     matches.append((pid,p,o))
    if matches:break # Fixed candidate priority, never cheapest-per-product choice.
   assert len({cents(m[2]['price']) for m in matches})<=1,('Conflicting regular prices',branch['id'],item['id'])
   selected=matches[0] if matches else None;pid,p,o=selected if selected else (None,None,None)
   lines.append({'id':item['id'],'product_id':pid,'source_name':p['name'] if p else None,'quantity':item['quantity'],'pricing_unit':item['pricing_unit'],'price_cents':cents(o['price']) if o else None,'line_total_cents':cents(Decimal(str(o['price']))*Decimal(str(item['quantity']))) if o else None,'source_type':o.get('source_type') if o else None,'kind':o.get('kind') if o else None,'source_url':(o.get('source_url') or branch.get('price_file_url')) if o else None,'price_updated_at':o.get('updated_at') if o else None,'raw_unit':o.get('raw_unit') if o else None,'product_unit':p.get('unit_quantity') if p else None,'raw_price':o.get('raw_price') if o else None})
  found=sum(x['line_total_cents'] is not None for x in lines);complete=found==len(products)
  branches.append({**{k:branch.get(k) for k in ['id','chain','name','address','city','file_date','source_url','price_file_url','files_applied']},'lines':lines,'found':found,'complete':complete,'total_cents':sum(x['line_total_cents'] for x in lines) if complete else None})
 branches.sort(key=lambda b:(not b['complete'],b['total_cents'] if b['complete'] else -b['found'],b['chain'],b['name']))
 complete=[b for b in branches if b['complete']];rankable=len(complete)>=2;minimum=complete[0]['total_cents'] if rankable else None;maximum=complete[-1]['total_cents'] if rankable else None
 status=json.loads((D/'data/source-status.json').read_text())
 result={'schema_version':1,'variant_id':variant,'city':catalog['city'],'retrieved_at':catalog['retrieved_at'],'price_date':catalog['retrieved_at'][:10],'scope_complete':catalog.get('coverage_complete',False),'price_mode':'regular_shelf_fixed_quantities','products':products,'branches':branches,'complete_branch_count':len(complete),'ranking_available':rankable,'minimum_cents':minimum,'maximum_cents':maximum,'average_cents':round(sum(b['total_cents'] for b in complete)/len(complete)) if complete else None,'gap_cents':maximum-minimum if rankable else None,'gap_percent_of_cheapest':round((maximum-minimum)/minimum*100,2) if rankable else None,'winner_ids':[b['id'] for b in complete if b['total_cents']==minimum] if rankable else [],'most_expensive_ids':[b['id'] for b in complete if b['total_cents']==maximum] if rankable else [],'pending_chains':[p['chain'] for p in status['pending']],'target_budget_ils':[600,700] if variant=='family' else None,'method':'Fixed packaged-product GTINs and package quantities. Fresh produce and whole fresh chicken use explicit matching kind/variety and kg quantities; producer, kosher certification, grade and size may differ. Selected product IDs are disclosed per branch. Only complete branch baskets of official regular shelf prices are ranked. Percentage gap is divided by the cheapest basket. Reported price is not stock confirmation.'}
 print(f'{variant}: {len(products)} lines; {len(complete)}/{len(branches)} complete; min={minimum}, max={maximum}, mean={result["average_cents"]} agorot')
 return result

def build():
 catalog=json.loads((D/'data/catalog.json').read_text());base=json.loads((ROOT/'scripts/super-ashdod/city-basket-products.json').read_text());family=json.loads((ROOT/'scripts/super-ashdod/city-family-basket.json').read_text())
 result={'schema_version':1,'default_variant':'family','variants':{'family':build_variant(family,catalog,'family'),'basic':build_variant(base,catalog,'basic')}}
 (D/'data/city-basket.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result
if __name__=='__main__':build()
