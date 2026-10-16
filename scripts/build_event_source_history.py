#!/usr/bin/env python3
"""Central comparison of public source snapshots; never reads private CMS drafts."""
import hashlib,json,os,subprocess
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]
REPO='isnet-media/isnet-real-estate-site'
FIELDS=('title','start_date','end_date','start_time','venue','category','subcategory','purchase_url','ticket_status','image_url','description','long_description')
def snapshot(data):
    return {e['event_id']:{'title':e.get('title',''),'hash':hashlib.sha256(json.dumps([e.get(k) for k in FIELDS],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()} for e in data.get('events',[])}
def compare(current,previous):
    return {'added':[k for k in current if k not in previous],'changed':[k for k in current if k in previous and current[k]['hash']!=previous[k]['hash']],'removed':[k for k in previous if k not in current]}
def read(url):
    headers={'Accept':'application/vnd.github+json','User-Agent':'ISNET-Source-History'}
    token=os.getenv('GITHUB_TOKEN','')
    if token:headers['Authorization']='Bearer '+token
    with urlopen(Request(url,headers=headers),timeout=20) as r:return json.load(r)
def main():
    report={'generated_at':datetime.now(timezone.utc).isoformat(),'scope':'Public source data only; CMS editorial revisions are separate.','cities':{}}
    for city in ('ashdod','rishon-lezion'):
        path=f'events-preview/{city}/data/events.json';current=json.loads((ROOT/path).read_text())
        try:
            commits=read('https://api.github.com/repos/'+REPO+'/commits?'+urlencode({'path':path,'sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'per_page':2}))
            if len(commits)<2:raise ValueError('No previous snapshot')
            sha=commits[1]['sha'];previous=read(f'https://raw.githubusercontent.com/{REPO}/{sha}/{path}')
            before=snapshot(previous);after=snapshot(current)
            report['cities'][city]={'available':True,'previous_sha':sha,'previous_at':commits[1]['commit']['committer']['date'],'current_source_at':current.get('generated_at') or current.get('updated_at'),'previous':before,'current':after,**compare(after,before)}
        except Exception as error:
            report['cities'][city]={'available':False,'reason':type(error).__name__}
    (ROOT/'events-preview/admin/data/source-history.json').write_text(json.dumps(report,ensure_ascii=False,separators=(',',':')))
    print('Central public source history:',{k:v['available'] for k,v in report['cities'].items()})
if __name__=='__main__':main()
