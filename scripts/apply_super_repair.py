"""Apply a hash-verified daily collection without fetching source prices again."""
import argparse,base64,gzip,hashlib,json
from pathlib import Path
import bsdiff4
ROOT=Path(__file__).resolve().parents[1]
CITIES=('ASHDOD','YAVNE','KGAT','RISHON','HOLON','BATYAM')
def digest(data):return hashlib.sha256(data).hexdigest()
def apply(city):
 folder=ROOT/'.supermarket-repair';manifest=json.loads((folder/'manifest.json').read_text())
 assert city in CITIES and city in manifest['cities']
 packed=b''.join(base64.b64decode((folder/part).read_text(),validate=True) for part in manifest['parts'] if Path(part).name==part)
 assert digest(packed)==manifest['sha256'],'Collection package hash mismatch'
 changes=json.loads(gzip.decompress(packed));assert len(changes)==manifest['files']
 prepared=[];seen=set()
 for change in changes:
  name=change['path'];path=Path(name)
  assert not path.is_absolute() and '..' not in path.parts
  assert path.parts[0] in ['SUPER.'+c for c in CITIES]
  assert path.parts[1]=='data' or name in ('SUPER.BATYAM/index.html','SUPER.HOLON/assets/product-groups.js')
  assert name not in seen;seen.add(name)
  if path.parts[0]!='SUPER.'+city:continue
  target=ROOT/path;before=target.read_bytes() if target.exists() else b''
  if digest(before)==change['after'] and not change['delete']:continue
  assert digest(before)==change['before'],'Concurrent update: refusing to overwrite '+name
  after=bsdiff4.patch(before,base64.b64decode(change['patch'],validate=True))
  assert len(after)<50_000_000 and digest(after)==change['after'],'Candidate hash mismatch'
  if not change['delete']:
   if target.suffix=='.json':json.loads(after)
   else:after.decode('utf-8')
  prepared.append((target,after,change['delete']))
 # Validate all files before replacing any file in this city.
 for target,data,delete in prepared:
  if delete:target.unlink(missing_ok=True)
  else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 report=json.loads((ROOT/('SUPER.'+city)/'data/refresh-status.json').read_text())
 for key in ('checked_at','updated_count','branch_count'):assert report[key]==manifest['cities'][city][key]
 assert report['all_sources_updated'] and report['updated_count']==report['branch_count']
 print('Verified original collection:',city,report['updated_count'],'/',report['branch_count'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--city',choices=CITIES,required=True);apply(p.parse_args().city)
