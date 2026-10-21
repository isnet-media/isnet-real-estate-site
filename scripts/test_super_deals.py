"""Promotion eligibility regression tests and published selection checks."""
import copy,json,xml.etree.ElementTree as ET
from datetime import datetime
from build_super_deals import parse_source,TZ,D
branch={'id':'7290058140886-026','name':'אשדוד','chain':'רמי לוי','address':'היהלומים 8','price_file_url':'https://url.publishedprices.co.il/file/d/PriceFull.gz'}
products={'7290000211442':{'name':'אורז פרסי 1 ק״ג','quantity':'1','unit_quantity':'קילוגרם','weighted':'0','offers':[{'branch_id':branch['id'],'source_type':'official_file','kind':'רגיל','eligible_for_basket':True,'price':11.9,'calculation_unit':'package'}]}}
xml='''<Root><ChainID>7290058140886</ChainID><StoreID>026</StoreID><Promotions><Promotion><PromotionID>123</PromotionID><PromotionStartDateTime>2026-10-01T00:00:00</PromotionStartDateTime><PromotionEndDateTime>2026-10-31T23:59:00</PromotionEndDateTime><ClubID>0 - כלל הלקוחות</ClubID><AdditionalIsCoupon>0</AdditionalIsCoupon><Groups><Group><MinPurchaseAmount>0</MinPurchaseAmount><PromotionItems><PromotionItem><ItemCode>7290000211442</ItemCode><RewardType>3</RewardType><MinQty>1</MinQty><DiscountedPrice>8.90</DiscountedPrice><bIsWeighted>0</bIsWeighted></PromotionItem></PromotionItems></Group></Groups></Promotion></Promotions></Root>'''
now=datetime(2026,10,21,12,tzinfo=TZ);meta={'source_url':'https://url.publishedprices.co.il/file/d/PromoFull.gz'}
def parse(root):return parse_source(ET.tostring(root),meta,branch,products,now)[0]
root=ET.fromstring(xml);ds=parse(root);assert len(ds)==1 and ds[0]['price']==8.9 and ds[0]['difference']==3
for tag,value in [('ClubID','1'),('AdditionalIsCoupon','1'),('PromotionEndDateTime','2026-10-20T23:59:00'),('MinPurchaseAmount','250'),('MinQty','2'),('RewardType','10'),('DiscountedPrice','0'),('DiscountedPrice','12'),('bIsWeighted','1')]:
 bad=copy.deepcopy(root);bad.find('.//'+tag).text=value;assert not parse(bad),(tag,value)
bad=copy.deepcopy(root);bad.find('.//Groups').append(copy.deepcopy(bad.find('.//Group')));assert not parse(bad)
x=json.loads((D/'deals.json').read_text());ds=x['deals'];chains={d['chain'] for d in ds};assert len(chains)>=4 and len(ds)>=24;assert x['stats']['chain_count']==len(chains);assert x['stats']['branch_count']==len({d['branch_id'] for d in ds});assert len({(d['branch_id'],d['barcode']) for d in ds})==len(ds)
for d in ds:
 assert d['price']>0 and d['price']<d['shelf_price']
 assert d['min_qty']==1 and d['min_purchase']==0 and not d['coupon_required']
 assert d['evidence']['reward_type']=='3' and d['evidence']['group_count']==1
 assert d['source_url'].startswith('https://') and len(d['source_sha256'])==64
 assert abs(d['difference']-(d['shelf_price']-d['price']))<.001
print(f'Verified {len(ds)} promotions from {len(chains)} chains; rejected club/coupon/multi-buy/minimum-spend/expired/ambiguous-unit fixtures')
