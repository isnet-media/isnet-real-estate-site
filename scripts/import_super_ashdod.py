"""Copy the reviewed supermarket snapshot to ISNET's independent public hosting."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib,json,shutil,requests
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'scripts/super-ashdod/manifest.json').read_text())
stage=ROOT/'.super-ashdod-staging';target=ROOT/'SUPER.ASHDOD'
if stage.exists():shutil.rmtree(stage)
stage.mkdir()
def download(entry):
 rel=entry['path'];p=Path(rel)
 if p.is_absolute() or '..' in p.parts:raise ValueError('Unsafe asset path')
 u=manifest['origin']+'/'+rel
 if rel.endswith('.html'):
  b=(ROOT/'scripts/super-ashdod/html'/rel).read_bytes()
 else:
  res=requests.get(u,timeout=60)
  res.raise_for_status()
  b=res.content
 if hashlib.sha256(b).hexdigest()!=entry['sha256']:raise ValueError('Snapshot hash mismatch: '+rel)
 if rel.endswith('.html'):
  b=b.replace(b'<head>',b'<head><meta name="robots" content="noindex,nofollow">',1)
 dest=stage/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
 return rel
with ThreadPoolExecutor(max_workers=4) as pool:files=list(pool.map(download,manifest['files']))
prices=json.loads((stage/'data/prices.json').read_text())
assert prices['direct_only'] and prices['branch_count']==14
assert (stage/'index.html').is_file() and (stage/'live.js').is_file()
if target.exists():shutil.rmtree(target)
stage.rename(target)
print('Imported',len(files),'verified assets;',prices['product_count'],'products;',prices['branch_count'],'branches')
