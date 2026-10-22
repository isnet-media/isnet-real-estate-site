"""Build the Kiryat Gat edition from its own verified data and the shared components."""
from pathlib import Path
import json,re
from super_city_runtime import ROOT,load
SITE=ROOT/'SUPER.KGAT'
def build():
 basket=load('build_super_city_basket','KGAT');catalog=json.loads((SITE/'data/catalog.json').read_text());variants={}
 for name,definition in [('family','city-family-basket.json'),('basic','city-basket-products.json')]:
  spec=json.loads((ROOT/'scripts/super-kgat'/definition).read_text());variants[name]=basket.build_variant(spec,catalog,name)
 (SITE/'data/city-basket.json').write_text(json.dumps(dict(schema_version=1,default_variant='family',variants=variants),ensure_ascii=False,indent=2)+'\n')
 load('build_super_smart_shopping','KGAT').build()
 shell=load('super_ashdod_shell','KGAT')
 for path in shell.pages():
  text=shell.decorate(path.read_text(),path)
  text=re.sub(r'<script\b[^>]*src="[^\"]*assets/ashdod-analytics\.js[^\"]*"[^>]*>\s*</script>','',text)
  tag='<script src="/SUPER.KGAT/assets/kgat-analytics.js?v=20261022-1" defer></script>'
  text=re.sub(r'<script\b[^>]*src="/SUPER\.KGAT/assets/kgat-analytics\.js[^\"]*"[^>]*>\s*</script>\s*','',text)
  text=text.replace('</head>',tag+'\n</head>',1)
  if path.read_text()!=text:path.write_text(text)
if __name__=='__main__':build()
