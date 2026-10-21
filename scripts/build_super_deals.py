"""Select diverse simple promotions from official PromoFull XML files.
Usage: python scripts/build_super_deals.py --raw-dir <downloaded-snapshot>
Input XML must have a companion .meta.json containing its official source_url.
No estimated promotions, club/coupon offers, multi-buy or unknown weight units.
"""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal,InvalidOperation
import argparse,collections,hashlib,json,re,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'SUPER.ASHDOD/data';TZ=ZoneInfo('Asia/Jerusalem')
def dec(s):
 try:return Decimal(str(s or '0'))
 except InvalidOperation:return Decimal(0)
def cents(n):return int((dec(n)*100).quantize(Decimal('1')))
def text(node,key):return next(((c.text or '').strip() for c in node if c.tag.split('}')[-1].casefold()==key.casefold()),'')
def kg(s):return bool(re.fullmatch(r'(?:1\s*)?(?:קילוגרמים?|קילוגרם|ק[״\"]?ג)',str(s).strip()))
def when(s):
 try:
  d=datetime.fromisoformat(s);return d if d.tzinfo else d.replace(tzinfo=TZ)
 except ValueError:return None
def category(name):
 # Match common prepared foods before their ingredient words.
 if re.search(r'שוקולד|מצופה שוק|קליק|גליד|מקרון|סוכריו|עוג|ביסקו|ופל|וופל',name):return 'מאפים ומתוקים'
 if re.search(r'תחליב|רחצה|יוגורט.*650|משחת|ניקוי',name):return 'ניקיון וטיפוח'
 if re.search(r'משקה|מיץ|סודה|קולה',name):return 'משקאות'
 if re.search(r'אבקת מרק|פיצה|לזניה|חטיף אצות|דגני בוקר',name):return 'מזווה ומוצרים לבית'
 for k,pat in [('ניקיון וטיפוח',r'כביסה|מרכך|ניקוי|נייר|טואלט|שמפו|משחת|מ.שיניים|סבון|מגבונ|תחבוש|חיתול|דאודורנט'),('חלב וביצים',r'חלב|גבינ|קוטג|יוגורט|מעדן|חמאה|שמנת|ביצים'),('בשר ודגים',r'עוף|בקר|אנטריקוט|בשר|פרגי|שניצל|סלמון|אמנון|דג |דגים|פסטרמה|נקניק'),('פירות וירקות',r'תפוח עץ|בננ|עגבני|מלפפון|תפו.?א|תפוח אדמה|גזר|בצל|תמר|אבוקדו|ירקות|ברוקולי|אפונה'),('משקאות',r'קפה|תה |משקה|מיץ|מים |סודה|קולה|יין |בירה|וויסקי'),('מאפים ומתוקים',r'לחם|לחמנ|עוג|שוקולד|וופל|ופל|ביסקו|חטיף|גלידה|סוכריו')]:
  if re.search(pat,name):return k
 return 'מזווה ומוצרים לבית'
def parse_source(xml,meta,branch,products,now):
 root=ET.fromstring(xml);chain=text(root,'ChainID');store=text(root,'StoreID');assert chain==branch['id'].split('-')[0] and int(store)==int(branch['id'].split('-')[-1]),('Wrong branch XML',branch['id'])
 out=[];excluded=collections.Counter()
 for p in root.findall('.//Promotion'):
  start=when(text(p,'PromotionStartDateTime'));end=when(text(p,'PromotionEndDateTime'));club=text(p,'ClubID')
  if not start or not end or not start<=now<=end:excluded['inactive']+=1;continue
  if not re.fullmatch(r'0(?:\s*-.*)?',club):excluded['club']+=1;continue
  if text(p,'AdditionalIsCoupon')!='0':excluded['coupon_or_unknown']+=1;continue
  if text(p,'PromotionDays'):excluded['restricted_days']+=1;continue
  groups=p.findall('./Groups/Group')
  if len(groups)!=1:excluded['combined_groups']+=1;continue
  g=groups[0];min_purchase=dec(text(g,'MinPurchaseAmount'))
  if min_purchase>0:excluded['minimum_spend']+=1;continue
  for item in g.findall('./PromotionItems/PromotionItem'):
   barcode=text(item,'ItemCode');pid=barcode if barcode in products else chain+':'+barcode;prod=products.get(pid)
   if not prod:excluded['unknown_product']+=1;continue
   regular=next((o for o in prod.get('offers',[]) if o['branch_id']==branch['id'] and o.get('source_type')=='official_file' and o.get('kind')=='רגיל' and o.get('eligible_for_basket') and o.get('price',0)>0),None)
   if not regular:excluded['no_regular_price']+=1;continue
   weighted=text(item,'bIsWeighted')=='1';price=dec(text(item,'DiscountedPrice'));qty=dec(text(item,'MinQty'))
   if text(item,'RewardType')!='3' or qty!=1 or price<=0:excluded['complex_reward']+=1;continue
   if weighted:
    if prod.get('weighted')!='1' or not kg(prod.get('unit_quantity')) or not kg(regular.get('raw_unit')) or regular.get('calculation_unit')!='kg' or cents(regular.get('raw_price'))!=cents(regular['price']):excluded['ambiguous_weight']+=1;continue
   elif prod.get('weighted')!='0' or regular.get('calculation_unit')!='package':excluded['unit_mismatch']+=1;continue
   if price>=dec(regular['price']):excluded['no_current_saving']+=1;continue
   name=prod['name']
   if re.search(r'מכונ[הת]|מקרר|טלוויז|שואב|כיריים|מיטה|ספה|מזרן|מאוורר|מזגן|בריכה|צעצוע',name):excluded['large_non_grocery']+=1;continue
   out.append({'id':branch['id']+':'+text(p,'PromotionID')+':'+barcode,'promotion_id':text(p,'PromotionID'),'barcode':pid,'name':name,'description':text(p,'PromotionDescription'),'branch_id':branch['id'],'branch_name':branch['name'],'chain':branch['chain'],'address':branch['address'],'price':float(price),'shelf_price':regular['price'],'difference':float(dec(regular['price'])-price),'quantity':prod['quantity'],'unit_quantity':prod['unit_quantity'],'start':start.isoformat(),'end':end.isoformat(),'club_id':club,'coupon_required':False,'min_purchase':0,'weighted':weighted,'min_qty':1,'category':category(name),'max_qty_raw':text(item,'MaxQty'),'redemption_limit_raw':text(p,'RedemptionLimit'),'start_hour':text(p,'PromotionStartHour'),'end_hour':text(p,'PromotionEndHour'),'remarks':text(p,'Remarks'),'restrictions':text(p,'AdditionalRestrictions'),'source_url':meta['source_url'],'source_date':now.date().isoformat(),'source_filename':meta.get('filename'),'source_sha256':hashlib.sha256(xml).hexdigest(),'regular_source_url':branch.get('price_file_url'),'basket_applied':False,'evidence':{'reward_type':text(item,'RewardType'),'discounted_price':text(item,'DiscountedPrice'),'min_qty':text(item,'MinQty'),'club_id':club,'coupon':text(p,'AdditionalIsCoupon'),'group_count':len(groups),'min_purchase':text(g,'MinPurchaseAmount'),'promotion_update_time':text(p,'PromotionUpdateTime')}})
 return out,dict(excluded)
def balanced(items,limit_per_branch=14):
 by_branch=collections.defaultdict(list)
 for d in items:by_branch[d['branch_id']].append(d)
 result=[]
 for bid,ds in by_branch.items():
  unique={}
  for d in sorted(ds,key=lambda d:(d['price'],d['id'])):unique.setdefault(d['barcode'],d)
  cats=collections.defaultdict(list)
  for d in unique.values():cats[d['category']].append(d)
  for cat in cats:cats[cat].sort(key=lambda d:(-d['difference']/d['shelf_price'],d['id']))
  chosen=[]
  while len(chosen)<limit_per_branch and any(cats.values()):
   for cat in sorted(cats):
    if cats[cat] and len(chosen)<limit_per_branch:chosen.append(cats[cat].pop(0))
  result.extend(chosen)
 return result

def build(raw_dir):
 catalog=json.loads((D/'catalog.json').read_text());branches={b['id']:b for b in catalog['branches']};products={}
 for f in (D/'offers').glob('*.json'):products.update(json.loads(f.read_text()))
 now=datetime.now(TZ);items=[];sources=[];excluded={}
 for path in sorted(Path(raw_dir).glob('*.xml')):
  meta_path=path.with_suffix('.meta.json')
  if not meta_path.exists():continue
  meta=json.loads(meta_path.read_text());xml=path.read_bytes();r=ET.fromstring(xml);bid=text(r,'ChainID')+'-'+text(r,'StoreID').zfill(3)
  if bid not in branches:continue
  ds,ex=parse_source(xml,meta,branches[bid],products,now);items.extend(ds);excluded[bid]=ex;sources.append({'branch_id':bid,'chain':branches[bid]['chain'],'source_url':meta['source_url'],'filename':meta.get('filename'),'sha256':hashlib.sha256(xml).hexdigest(),'eligible_count':len(ds)})
 selected=balanced(items);chains=collections.Counter(d['chain'] for d in selected);branch_count=len({d['branch_id'] for d in selected})
 assert len(chains)>=4 and len(selected)>=24,'Insufficient broad coverage: do not publish a Carrefour-only section'
 result={'status':'verified_selection','updated_at':now.isoformat(),'city':'אשדוד','scope':'Selected simple unit-price promotions from official branch feeds; not all city chains or all promotions.','deals':selected,'stats':{'selected_count':len(selected),'eligible_observations':len(items),'chain_count':len(chains),'branch_count':branch_count,'by_chain':dict(chains)},'sources':sources,'excluded':excluded,'note':'Only active single-group, quantity-one fixed special prices with no coupon, club or minimum-spend requirement. Weighted items require verified kg units. Shelf-price difference refers to the current imported shelf snapshot, not a historical price. Availability must be checked at the branch. Daily hours and redemption limits, if reported, are displayed. Promotions are not applied to basket totals.'}
 (D/'deals.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result['stats']);return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--raw-dir',required=True);a=p.parse_args();build(a.raw_dir)
