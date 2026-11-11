"""Publish only a pointer to already validated committed prices; never collect."""
import hashlib
import json
from pathlib import Path
import subprocess
import time
from prepare_pages_public import ROOT, CITIES
from verify_super_delivery import verify_city
import concurrent.futures

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()

pointer=ROOT/'.supermarket-delivery/release.json'
commit=git('rev-parse','HEAD')
paths=['SUPER.'+c+'/data' for c in sorted(CITIES)]
tree=hashlib.sha256(git('ls-tree','-r',commit,'--',*paths).encode()).hexdigest()
previous=json.loads(pointer.read_text()) if pointer.exists() else {}
if previous.get('data_tree_sha256')==tree:
    print('Data trees unchanged; retaining validated independent release '+previous['source_commit'])
    raise SystemExit(0)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    results=list(pool.map(lambda city:verify_city(city,commit),sorted(CITIES)))
pointer.parent.mkdir(exist_ok=True)
pointer.write_text(json.dumps({'source_commit':commit,'data_tree_sha256':tree,
  'source':'validated committed supermarket snapshots'},indent=2)+'\n')
git('config','user.name','ISNET supermarket delivery')
git('config','user.email','actions@users.noreply.github.com')
git('add','--','.supermarket-delivery/release.json')
git('commit','-m','Point independent supermarket delivery at validated data '+commit[:12])
for attempt in range(5):
    try:
        git('pull','--rebase','origin','main')
        git('push','origin','HEAD:main')
        print(json.dumps({'source_commit':commit,'verified_cities':results,'collection_started':False}))
        break
    except subprocess.CalledProcessError:
        if (ROOT/'.git/rebase-merge').exists() or (ROOT/'.git/rebase-apply').exists():
            git('rebase','--abort')
            raise RuntimeError('Concurrent release pointer changed; refusing to overwrite')
        if attempt==4:raise
        time.sleep(2+attempt)
