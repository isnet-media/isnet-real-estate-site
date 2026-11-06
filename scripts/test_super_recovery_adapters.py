"""Recovery needs the same isolated collector factory in every city adapter."""
import importlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for city in ('YAVNE','KGAT','RISHON','HOLON','BATYAM'):
 module=importlib.import_module('refresh_'+city.lower()+'_super_prices')
 c=module.collector()
 assert c.D==ROOT/('SUPER.'+city)/'data',city
 assert callable(c.refresh_branch) and callable(c.recover_branches),city
print('Passed: five isolated recovery adapters expose working collector factories')
