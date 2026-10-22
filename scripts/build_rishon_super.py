"""Build the Rishon LeZion edition from its own verified data and the shared components."""
from pathlib import Path
import json,re
from super_city_runtime import ROOT,load
SITE=ROOT/'SUPER.RISHON'
def build():
 basket=load('build_super_city_basket','RISHON');catalog=json.loads((SITE/'data/catalog.json').read_text());variants={}
 for name,definition in [('family','city-family-basket.json'),('basic','city-basket-products.json')]:
  spec=json.loads((ROOT/'scripts/super-rishon'/definition).read_text());variants[name]=basket.build_variant(spec,catalog,name)
 for v in variants.values():
  v['method']='Verified physical Rishon LeZion branches only. Fixed product priority, shelf prices and identical quantities. Reviewed frozen salmon portions total 3 kg in whole packs or explicit kg. Basket contains dairy, frozen fish and pantry items, not fresh meat, fruit or vegetables. Price-file data does not guarantee stock.'
 (SITE/'data/city-basket.json').write_text(json.dumps(dict(schema_version=1,default_variant='family',variants=variants),ensure_ascii=False,indent=2)+'\n')
 load('build_super_smart_shopping','RISHON').build()
 shell=load('super_ashdod_shell','RISHON')
 for path in shell.pages():
  text=shell.decorate(path.read_text(),path)
  text=re.sub(r'<script\b[^>]*src="[^\"]*assets/ashdod-analytics\.js[^\"]*"[^>]*>\s*</script>','',text)
  if path.read_text()!=text:path.write_text(text)
if __name__=='__main__':build()
