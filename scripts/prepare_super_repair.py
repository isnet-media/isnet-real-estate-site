"""Pack validated workspace data for conflict-checked publication without re-scan.
Requires bsdiff4. Upload parts, manifest and any reviewed script changes in ONE
Git tree/commit; only then update the main ref with an expected-head lease.
"""
import base64,gzip,hashlib,json,subprocess
from pathlib import Path
import bsdiff4
ROOT=Path(__file__).resolve().parents[1]
CITIES=('ASHDOD','YAVNE','KGAT','RISHON','HOLON','BATYAM','TLV')
def digest(b):return hashlib.sha256(b).hexdigest()
def prepare():
 scopes=['SUPER.'+c+'/'+suffix for c in CITIES for suffix in ('data','index.html','assets/product-groups.js')]
 paths=subprocess.check_output(['git','diff','--name-only','HEAD','--',*scopes],cwd=ROOT,text=True).splitlines()
 paths+=subprocess.check_output(['git','ls-files','--others','--exclude-standard','--',*scopes],cwd=ROOT,text=True).splitlines()
 changes=[]
 for name in sorted(set(paths)):
  try:before=subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT,stderr=subprocess.DEVNULL)
  except subprocess.CalledProcessError:before=b''
  path=ROOT/name;after=path.read_bytes() if path.exists() else b''
  if before==after:continue
  changes.append({'path':name,'before':digest(before),'after':digest(after),'delete':not path.exists(),'patch':base64.b64encode(bsdiff4.diff(before,after)).decode()})
 packed=gzip.compress(json.dumps(changes,separators=(',',':')).encode(),mtime=0)
 folder=ROOT/'.supermarket-repair';folder.mkdir(exist_ok=True)
 parts=[]
 for i,start in enumerate(range(0,len(packed),30000)):
  name=f'{i:03}.b64';(folder/name).write_text(base64.b64encode(packed[start:start+30000]).decode());parts.append(name)
 cities={}
 affected={Path(change['path']).parts[0] for change in changes}
 assert affected,'No verified city changes to package'
 for city in CITIES:
  if 'SUPER.'+city not in affected:continue
  report=json.loads((ROOT/('SUPER.'+city)/'data/refresh-status.json').read_text())
  cities[city]={k:report[k] for k in ('checked_at','updated_count','branch_count','all_sources_updated')}
 manifest={'sha256':digest(packed),'parts':parts,'files':len(changes),'cities':cities}
 (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'files':len(changes),'bytes':len(packed),'parts':len(parts),'cities':cities}))
if __name__=='__main__':prepare()
