"""Load the established supermarket components with an isolated city data root.
No global paths or Ashdod files are changed. No collector is scheduled here.
"""
from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parents[1]
def load(name,city='YAVNE'):
 assert city in ('YAVNE','KGAT'),'Only the reviewed city edition is supported'
 spec=importlib.util.spec_from_file_location('city_'+name,ROOT/'scripts'/f'{name}.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 site=ROOT/('SUPER.'+city)
 if name=='refresh_super_prices' or name=='build_super_deals':module.D=site/'data'
 elif name=='build_super_city_basket':module.D=site
 elif name=='build_super_smart_shopping':module.SITE=site;module.DATA=site/'data'
 elif name=='super_ashdod_shell':module.SITE=site;module.TEMPLATE=site/'assets/branding/super-shell.html'
 return module
