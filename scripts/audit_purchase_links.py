#!/usr/bin/env python3
"""Non-destructive purchase-link audit. Blocked requests are unverified, not broken."""
import argparse
import ipaddress
import json
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'events-preview/admin/data/purchase-link-audit.json'

def safe_public_url(url):
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
            return False
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == 'https' else 80), type=socket.SOCK_STREAM)
        return bool(addresses) and all(ipaddress.ip_address(row[4][0]).is_global for row in addresses)
    except (ValueError, OSError):
        return False

def check(url, timeout=7, session=None, guard=safe_public_url):
    import requests
    session = session or requests.Session()
    current = url
    checked_at = datetime.now(timezone.utc).isoformat()
    def result(state, reason, code=None):
        return {'state':state, 'reason':reason, 'http_status':code, 'final_url':current, 'checked_at':checked_at}
    for _ in range(5):
        if not guard(current):
            return result('unverified', 'invalid_or_non_public_destination')
        try:
            response = session.get(current, timeout=timeout, allow_redirects=False, stream=True, headers={'User-Agent':'ISNET-Link-Quality/1.0'})
            with response:
                code = response.status_code
                if code in (301,302,303,307,308):
                    target = response.headers.get('Location')
                    if not target: return result('unverified','redirect_without_destination',code)
                    current = urljoin(current,target)
                    continue
                if code in (404,410): return result('broken','http_not_found',code)
                if code in (401,403,429): return result('unverified','access_restricted',code)
                if not 200 <= code < 300: return result('unverified','unexpected_response',code)
                chunks=[]
                for chunk in response.iter_content(chunk_size=4096):
                    chunks.append(chunk)
                    if sum(map(len,chunks)) >= 65536: break
                text=b''.join(chunks).decode(response.encoding or 'utf-8',errors='replace').lower()
                if any(marker in text for marker in ('just a moment','verify you are human','access denied','checking your browser')):
                    return result('unverified','verification_page',code)
                p=urlsplit(current)
                if not p.path.strip('/') and not p.query:
                    return result('needs_review','generic_homepage',code)
                if '<title>404' in text or '<title>page not found' in text:
                    return result('needs_review','possible_soft_404',code)
                return result('reachable','http_success_not_ticket_availability',code)
        except requests.RequestException:
            return result('unverified','network_error')
    return result('unverified','too_many_redirects')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--workers',type=int,default=6)
    parser.add_argument('--timeout',type=float,default=7)
    parser.add_argument('--limit',type=int,default=0)
    args=parser.parse_args()
    references=[]
    for city in ('ashdod','rishon-lezion'):
        data=json.loads((ROOT/f'events-preview/{city}/data/events.json').read_text())
        for event in data['events']:
            url=event.get('purchase_url') or event.get('ticket_url')
            if url:
                references.append({'city':city,'event_id':event['event_id'],'url':url})
    urls=list(dict.fromkeys(row['url'] for row in references))
    if args.limit: urls=urls[:args.limit]
    results={}
    started=time.monotonic()
    with ThreadPoolExecutor(max_workers=max(1,min(args.workers,8))) as executor:
        jobs={executor.submit(check,url,args.timeout):url for url in urls}
        for future in as_completed(jobs):
            results[jobs[future]]=future.result()
            if len(results)%50==0: print('LINK AUDIT',len(results),'/',len(urls),flush=True)
    states={state:sum(row['state']==state for row in results.values()) for state in ('reachable','broken','needs_review','unverified')}
    report={'generated_at':datetime.now(timezone.utc).isoformat(),'checked_urls':len(results),'total_unique_urls':len(set(row['url'] for row in references)),'complete':not args.limit or len(results)==len(set(row['url'] for row in references)),'summary':states,'results':results,'events':references,'notes':['HTTP success is not proof of ticket availability.','Access restrictions and network errors do not prove a broken link.']}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('LINK AUDIT COMPLETE',states,'seconds',round(time.monotonic()-started),flush=True)

if __name__=='__main__': main()
