"""Restore a hash-verified publication candidate without collecting any prices."""
import argparse,base64,gzip,hashlib,io,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def restore(city):
 folder=ROOT/'.supermarket-recovery';manifest=json.loads((folder/'manifest.json').read_text())
 assert city in manifest['cities']
 packed=b''.join(base64.b64decode((folder/p).read_text(),validate=True) for p in manifest['parts'])
 assert hashlib.sha256(packed).hexdigest()==manifest['sha256']
 expected='SUPER.'+city+'/data/'
 with tarfile.open(fileobj=io.BytesIO(packed),mode='r:gz') as archive:
  for member in archive.getmembers():
   name=member.name;path=Path(name)
   assert not path.is_absolute() and '..' not in path.parts and member.isfile()
   assert any(name.startswith('SUPER.'+c+'/data/') for c in manifest['cities'])
   assert member.size<50_000_000
   if not name.startswith(expected):continue
   target=ROOT/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(archive.extractfile(member).read())
 report=json.loads((ROOT/expected/'refresh-status.json').read_text())
 assert report['checked_at']==manifest['cities'][city]['checked_at']
 assert report['updated_count']==manifest['cities'][city]['updated_count']
 print('Restored existing collection evidence:',city,report['checked_at'],report['updated_count'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--city',choices=['ASHDOD','YAVNE','KGAT','RISHON','HOLON','BATYAM'],required=True);restore(p.parse_args().city)
