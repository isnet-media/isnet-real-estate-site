"""Extract a verified last-successful Pages artifact; never rebuild news/events."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
from urllib.request import urlopen
from prepare_pages_public import ROOT, delivery_cities

config=json.loads((ROOT/'scripts/super_delivery.json').read_text())
artifact=Path(os.environ['SUPER_BASELINE_ARTIFACT'])/'artifact.tar'
source=Path(os.environ['SUPER_BASELINE_ROOT'])
source.mkdir()
with tarfile.open(artifact) as archive:
    if any(not (m.isfile() or m.isdir()) for m in archive.getmembers()):
        raise ValueError('Baseline artifact contains unsupported links/devices')
    archive.extractall(source,filter='data')
release=json.loads((source/'deployment-version.json').read_text())
if release.get('source_commit')!=config['baseline_source_commit'] or str(release.get('run_id'))!=str(config['baseline_run_id']):
    raise ValueError('The downloaded artifact is not the verified public release')
live=json.loads(subprocess.check_output(['curl','--fail','--silent','--show-error','--max-time','30','https://isnet.co.il/deployment-version.json']))
if live.get('source_commit')!=release['source_commit'] or str(live.get('run_id'))!=str(release['run_id']):
    raise ValueError('Public news release moved; do not replace another editor deployment')
print(json.dumps({'baseline_verified':release,'collection_started':False,'news_rebuilt':False}))
