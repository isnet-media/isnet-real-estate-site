"""Build the Bat Yam edition from its own verified data and the shared components."""
from pathlib import Path
import json,re
from super_city_runtime import ROOT,load
SITE=ROOT/'SUPER.BATYAM'
def build():
 basket=load('build_super_city_basket','BATYAM');catalog=json.loads((SITE/'data/catalog.json').read_text());variants={}
 for name,definition in [('family','city-family-basket.json'),('basic','city-basket-products.json')]:
  spec=json.loads((ROOT/'scripts/super-batyam'/definition).read_text());variants[name]=basket.build_variant(spec,catalog,name)
 for v in variants.values():
  v['method']='Verified physical Bat Yam branches only. Fixed product priority, shelf prices and identical quantities. Family basket: dairy, pantry, canned tomatoes, frozen vegetables and 4 x 700 g prepared chicken schnitzel (2.8 kg). Same barcodes and whole packs except reviewed regular canola 1-litre equivalents. No raw meat, fish or fresh produce in the fixed basket. Price-file data does not guarantee stock.'
 (SITE/'data/city-basket.json').write_text(json.dumps(dict(schema_version=1,default_variant='family',variants=variants),ensure_ascii=False,indent=2)+'\n')
 load('build_super_smart_shopping','BATYAM').build()
 # Reuse the city's size-verified brand groups in search, avoiding duplicate generic cards.
 smart=json.loads((SITE/'data/smart-shopping.json').read_text())
 p=SITE/'assets/product-groups.js';text=p.read_text()
 match=re.search(r'const REVIEWED=(\{.*?\});',text)
 reviewed=json.loads(match[1])
 for group in smart['groups']:
  for product in group['products']:reviewed[product['id']]=[group['id'],group['title']+' · '+group['size']]
 text=text[:match.start(1)]+json.dumps(reviewed,ensure_ascii=False,separators=(',',':'))+text[match.end(1):]
 p.write_text(text)
 shell=load('super_ashdod_shell','BATYAM')
 for path in shell.pages():
  text=shell.decorate(path.read_text(),path)
  text=re.sub(r'<script\b[^>]*src="[^\"]*assets/ashdod-analytics\.js[^\"]*"[^>]*>\s*</script>','',text)
  if path.read_text()!=text:path.write_text(text)
 # Keep the visible introduction truthful even before JavaScript has loaded.
 p=SITE/'index.html';text=p.read_text()
 text=re.sub(r'(<span id="introProductCount">).*?(</span>)',lambda m:m[1]+format(catalog['product_count'],',')+m[2],text)
 text=re.sub(r'(<span id="introBranchCount">).*?(</span>)',lambda m:m[1]+str(len(catalog['branches']))+m[2],text)
 p.write_text(text)
if __name__=='__main__':build()
