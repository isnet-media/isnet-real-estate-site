#!/usr/bin/env python3
"""Bounded public endpoint checks; this is not a browser or load test."""
import argparse,json,re,subprocess,tempfile,time
from pathlib import Path
CITIES=('ashdod','rishon-lezion')
BASE='https://isnet.co.il/events-preview/'
def check(url,kind):
    with tempfile.TemporaryDirectory() as folder:
        body=Path(folder)/'body'
        headers=[]
        if kind=='cms':
            config=(Path(__file__).resolve().parents[1]/'events-preview/shared/public-cms.js').read_text()
            headers=['--header','apikey:'+re.search(r'const key="([^"]+)"',config).group(1)]
        result=subprocess.run(['curl','--silent','--show-error','--location','--fail','--max-time','25','--output',str(body),'--write-out','%{http_code} %{time_starttransfer} %{time_total} %{size_download}',*headers,url],capture_output=True,text=True)
        if result.returncode:raise RuntimeError(f'HTTP check failed ({result.returncode}): {result.stderr[:160]}')
        status,ttfb,total,size=result.stdout.split()
        if status!='200':raise RuntimeError('Unexpected HTTP '+status)
        if kind=='html':
            text=body.read_text();assert '<html' in text.lower() and '<script' in text.lower(),'Invalid HTML shell'
        elif kind=='hub':
            data=json.loads(body.read_text());assert data.get('hub_schema')==1 and isinstance(data.get('events'),list),'Invalid hub data'
        elif kind=='cinema':
            data=json.loads(body.read_text());assert isinstance(data.get('movies'),list),'Invalid cinema data'
        elif kind=='cms':
            assert isinstance(json.loads(body.read_text()),list),'Invalid CMS response'
        return {'url':url,'ok':True,'http_status':int(status),'ttfb_seconds':float(ttfb),'total_seconds':float(total),'download_bytes':int(size)}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='/tmp/isnet-health.json');args=parser.parse_args()
    targets=[]
    for city in CITIES:
        for path,kind in [('', 'html'),('category.html?category=kids','html'),('event.html','html'),('data/events-hubs.json','hub'),('data/cinema.json','cinema')]:targets.append((BASE+city+'/'+path,kind))
        targets.append(('https://qomkxhafrprooekwgsxf.supabase.co/rest/v1/cms_event_records?city_slug=eq.'+city+'&publication_status=eq.published&select=event_id&limit=1','cms'))
    results=[]
    for url,kind in targets:
        try:row=check(url,kind)
        except Exception as error:row={'url':url,'ok':False,'error':str(error)}
        results.append(row)
    report={'checked_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'measurement':'HTTP checks only; not mobile rendering, user latency, or a load test.','ok':all(r['ok'] for r in results),'results':results}
    Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))
    return 0 if report['ok'] else 1
if __name__=='__main__':raise SystemExit(main())
