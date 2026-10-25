"""Notify IndexNow of public canonical URLs whose rendered content actually changed.

The ownership key is intentionally public. Google does not support IndexNow;
Google discovers the separately advertised XML sitemaps through robots.txt.
"""
import argparse,hashlib,json,os,time
from pathlib import Path
from urllib.parse import urlparse,unquote
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
HOST='isnet.co.il';ENDPOINT='https://api.indexnow.org/indexnow'
def fingerprints(root):
 result={}
 for name in ('sitemap.xml','movie-sitemap.xml','discovery-sitemap.xml'):
  path=root/'events-preview'/name
  if not path.exists():continue
  for loc in ET.parse(path).findall('.//{*}loc'):
   url=loc.text or '';parts=urlparse(url)
   if parts.scheme!='https' or parts.netloc!=HOST or parts.query or '/admin/' in parts.path:continue
   file=(root/unquote(parts.path).lstrip('/')).resolve()
   try:file.relative_to(root.resolve())
   except ValueError:continue
   if parts.path.endswith('/'):file=file/'index.html'
   if file.is_file():result[url]=hashlib.sha256(file.read_bytes()).hexdigest()
 return result

def notify(root,state,submit=False,opener=urlopen):
 root=Path(root);state=Path(state);current=fingerprints(root)
 previous=json.loads(state.read_text()) if state.exists() else {}
 changed=sorted(u for u,h in current.items() if previous.get(u)!=h)
 removed=sorted(set(previous)-set(current));urls=changed+removed
 report={'changed':len(changed),'removed':len(removed),'total_canonical':len(current),'status':'dry_run','search_engine':'IndexNow participating engines; not Google'}
 if not submit or not urls:
  if not urls:report['status']='unchanged'
  return report
 config=json.loads((root/'events-preview/shared/data/search-indexing.json').read_text());key=config['indexnow_key']
 if not (8<=len(key)<=128 and all(c in '0123456789abcdef' for c in key)):raise ValueError('Invalid public ownership key')
 key_url='https://'+HOST+'/'+key+'.txt'
 try:
  with opener(Request(key_url,headers={'User-Agent':'ISNET-IndexNow/1.0'}),timeout=20) as response:
   if response.read().decode().strip()!=key:raise ValueError('Public key file has not deployed yet')
  for offset in range(0,len(urls),10000):
   payload={'host':HOST,'key':key,'keyLocation':key_url,'urlList':urls[offset:offset+10000]}
   request=Request(ENDPOINT,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json; charset=utf-8','User-Agent':'ISNET-IndexNow/1.0'},method='POST')
   with opener(request,timeout=30) as response:
    status=response.status
    if status not in (200,202):raise ValueError('Unexpected response '+str(status))
  state.parent.mkdir(parents=True,exist_ok=True);state.write_text(json.dumps(current,separators=(',',':')))
  report.update(status='accepted',http_status=status,note='Receipt of URLs is not a promise to crawl or index them.')
 except (HTTPError,URLError,ValueError,TimeoutError,OSError) as error:
  report.update(status='deferred',reason=str(error));print('::warning::IndexNow notification deferred; the live site is unaffected and unchanged state will be retried next publication.')
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--submit',action='store_true');p.add_argument('--state',default=os.environ.get('RUNNER_TEMP','/tmp')+'/events-indexnow-state.json');a=p.parse_args();print(json.dumps(notify(ROOT,a.state,a.submit),ensure_ascii=False))
