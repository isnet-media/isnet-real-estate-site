"""Stage existing public paths, excluding repository-only source and evidence."""
import argparse
import json
import os
import re
from pathlib import Path
import shutil
import subprocess

PAGES_LIMIT = 1_000_000_000
WARNING_BYTES = 800_000_000
CRITICAL_BYTES = 900_000_000

def check_capacity(size):
    if size >= PAGES_LIMIT:
        raise ValueError('Public site reaches the 1 GB Pages limit; move heavy assets before uploading')
    if size >= CRITICAL_BYTES:
        print('::warning title=Critical Pages headroom::Public payload exceeds 900 MB; require storage migration before any new city')
    elif size >= WARNING_BYTES:
        print('::warning title=Public hosting capacity::Public site exceeds 800 MB; plan asset storage expansion')


ROOT = Path(__file__).resolve().parents[1]
EXCLUDE = {'scripts', 'tests', 'docs', 'package.json', 'package-lock.json', 'README.md'}

def public_entries(root):
    return [p for p in root.iterdir() if not p.name.startswith('.') and p.name not in EXCLUDE]

DELIVERY_ORIGIN = 'https://isnetsuper.ebs987449.chatgpt.site'
DELIVERY_CONFIG = 'super_delivery.json'
CITIES = {'ASHDOD', 'YAVNE', 'KGAT', 'RISHON', 'HOLON', 'BATYAM', 'TLV'}

def delivery_cities(root):
    config = root / 'scripts' / DELIVERY_CONFIG
    if not config.exists():
        return set()
    selected = json.loads(config.read_text())['cities']
    if not isinstance(selected, list) or any(c not in CITIES for c in selected):
        raise ValueError('Invalid supermarket delivery configuration')
    return set(selected)


def delivery_script(cities, commit):
    if not re.fullmatch(r'[a-f0-9]{40}', commit or ''):
        raise ValueError('Independent delivery requires an immutable source commit')
    settings = json.dumps({'origin': DELIVERY_ORIGIN, 'release': commit,
                           'prefixes': ['/SUPER.' + c + '/data/' for c in sorted(cities)]})
    return '<script data-super-delivery="' + commit + '">' + """(()=>{
const settings=SETTINGS, original=window.fetch;
const currentRelease=original.call(window,settings.origin+'/release',{credentials:'omit',cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('release unavailable');return r.json()}).then(r=>/^[a-f0-9]{40}$/.test(r.source_commit)?r.source_commit:settings.release).catch(()=>settings.release);
function target(value,release=settings.release){const u=new URL(value,document.baseURI);
if(u.origin===location.origin&&settings.prefixes.some(p=>u.pathname.startsWith(p))){
u.host=new URL(settings.origin).host;u.protocol='https:';u.searchParams.set('__release',release);return u.href}return null}
window.fetch=function(input,init){try{const url=target(input instanceof Request?input.url:String(input));
if(url)return currentRelease.then(release=>{const pinned=target(input instanceof Request?input.url:String(input),release);if(input instanceof Request)return original.call(this,new Request(pinned,input),init);return original.call(this,pinned,init)})}catch(error){return Promise.reject(error)}
return original.call(this,input,init)};
document.addEventListener('click',event=>{const a=event.target.closest?.('a[href]');if(!a)return;
const url=target(a.href);if(url)a.href=url},true);
})();""".replace('SETTINGS', settings) + '</script>'


def stage(root, output, *, cities=None, source_commit=None, preserve_news_release=False):
    root, output = root.resolve(), output.resolve()
    if output == root or root in output.parents:
        raise ValueError('Staging output must be outside the checkout')
    if output.exists():
        raise ValueError('Refuse to replace an existing staging directory')
    if preserve_news_release and (root/'.git').exists():
        raise ValueError('A preserved public release must not contain git metadata')
    entries = list(root.iterdir()) if preserve_news_release else public_entries(root)
    if not (root / 'index.html').is_file():
        raise ValueError('Missing public home page')
    for entry in entries:
        if entry.is_symlink() or (entry.is_dir() and any(p.is_symlink() for p in entry.rglob('*'))):
            raise ValueError('Public symlinks are not supported')
    try:
        source_commit = source_commit or subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        source_commit = None
    cities = delivery_cities(root) if cities is None else cities
    if not cities <= CITIES:
        raise ValueError("Unknown delivery city")
    def offloaded(path):
        parts = path.relative_to(root).parts
        return len(parts) >= 3 and parts[0] in {'SUPER.'+c for c in cities} and parts[1] == 'data'
    source_files = [p for entry in entries for p in (entry.rglob('*') if entry.is_dir() else [entry]) if p.is_file()]
    payload_files = [p for p in source_files if not offloaded(p)]
    script = delivery_script(cities, source_commit) if cities else ''
    check_capacity(sum(p.stat().st_size for p in payload_files) + len(script.encode())*sum(p.suffix == '.html' and p.relative_to(root).parts[0] in {'SUPER.'+c for c in cities} for p in payload_files) + 4096)
    output.mkdir(parents=True)
    injected = 0
    for path in payload_files:
        dest = output / path.relative_to(root)
        dest.parent.mkdir(parents=True, exist_ok=True)
        city = path.relative_to(root).parts[0]
        if path.suffix == '.html' and city in {'SUPER.'+c for c in cities} and 'assets' not in path.relative_to(root).parts:
            html = path.read_text()
            if not re.search(r'<head\b[^>]*>', html, re.I):
                raise ValueError('Missing HTML head: ' + str(path))
            dest.write_text(re.sub(r'<head\b[^>]*>', lambda m: m.group(0)+script, html, count=1, flags=re.I))
            injected += 1
        else:
            shutil.copy2(path, dest)
    offload_bytes = sum(p.stat().st_size for p in source_files if offloaded(p))
    report = {'origin': DELIVERY_ORIGIN if cities else None, 'cities': sorted(cities),
              'data_bytes_offloaded': offload_bytes, 'html_pages_routed': injected,
              'source_commit': source_commit, 'browser_origin_preserved': True}
    (output / 'super-delivery-status.json').write_text(json.dumps(report, indent=2)+'\n')
    original_release = json.loads((root/'deployment-version.json').read_text()) if preserve_news_release else {}
    (output / 'deployment-version.json').write_text(json.dumps({
        'source_commit': source_commit,
        'run_id': os.environ.get('GITHUB_RUN_ID'),
        'run_attempt': os.environ.get('GITHUB_RUN_ATTEMPT'),
        **original_release,
        **({'super_delivery_commit':source_commit,'super_delivery_run_id':os.environ.get('GITHUB_RUN_ID')} if preserve_news_release else {}),
    }, indent=2) + '\n')
    files = [p for p in output.rglob('*') if p.is_file()]
    total = sum(p.stat().st_size for p in files)
    check_capacity(total)
    print(json.dumps({'public_files': len(files), 'bytes': total, 'limit_bytes': PAGES_LIMIT, 'headroom_bytes': PAGES_LIMIT-total, **report}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-root', type=Path, default=ROOT)
    parser.add_argument('--preserve-news-release', action='store_true')
    args=parser.parse_args()
    stage(args.source_root, args.output, cities=delivery_cities(ROOT),
          source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
          preserve_news_release=args.preserve_news_release)
