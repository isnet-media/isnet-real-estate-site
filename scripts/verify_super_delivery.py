"""Read-only cutover gate: verify the independent origin serves this exact release.

No collectors, timestamps, secrets, uploads or price mutations are involved.
"""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from prepare_pages_public import ROOT, DELIVERY_ORIGIN, delivery_cities


def verify_city(city, commit):
    base = ROOT / ('SUPER.'+city) / 'data'
    paths = [base/'catalog.json', base/'source-status.json']
    shards = sorted((base/'offers').glob('*.json'))
    if shards:
        paths.append(shards[0])
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        url = DELIVERY_ORIGIN+'/'+relative+'?__release='+commit
        with tempfile.TemporaryDirectory() as tmp:
            body, headers = Path(tmp)/'body', Path(tmp)/'headers'
            subprocess.run(['curl','--fail','--silent','--show-error','--location',
                            '--max-time','45','--dump-header',str(headers),
                            '--output',str(body),url], check=True)
            metadata=headers.read_text().lower()
            if 'x-super-source-commit: '+commit not in metadata:
                raise ValueError('Independent release header mismatch: '+relative)
            if 'content-type: application/json' not in metadata:
                raise ValueError('Independent origin did not return JSON: '+relative)
            remote=body.read_bytes()
        if hashlib.sha256(remote).digest() != hashlib.sha256(path.read_bytes()).digest():
            raise ValueError('Independent source bytes differ: '+relative)
        json.loads(remote)
    return {'city':city, 'verified_files':len(paths), 'source_commit':commit}


def main():
    cities = sorted(delivery_cities(ROOT))
    if not cities:
        print('Independent data delivery disabled; original Pages payload retained')
        return
    commit = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda city:verify_city(city,commit),cities))
    print(json.dumps({'gate':'independent delivery bytes match immutable source', 'cities':results}))

if __name__ == '__main__':
    main()
