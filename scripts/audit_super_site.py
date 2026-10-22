"""Validate local public pages/assets/fragment targets and source freshness."""
from pathlib import Path
from urllib.parse import urlsplit,unquote
from datetime import datetime,date
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
import argparse,json
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'SUPER.ASHDOD';D=SITE/'data';TZ=ZoneInfo('Asia/Jerusalem')
def audit():
 errors=[];count=0;links=0;pages={}
 for p in SITE.rglob('*.html'):
  if p.name.startswith('qa-') or p.name=='super-shell.html':continue
  pages[p.resolve()]=BeautifulSoup(p.read_text(),'html.parser')
 for p,soup in pages.items():
  count+=1
  if not soup.title or not soup.get('lang') and not soup.find('html',lang=True):errors.append(f'{p.relative_to(SITE)}: missing title/language')
  for tag,attr in [('a','href'),('img','src'),('script','src'),('link','href')]:
   for node in soup.find_all(tag):
    value=node.get(attr,'');u=urlsplit(value)
    if not value or u.scheme or u.netloc:continue
    if value.startswith('data:'):continue
    path=unquote(u.path)
    if path.startswith('/SUPER.ASHDOD/'):target=SITE/path.removeprefix('/SUPER.ASHDOD/')
    elif path.startswith('/'):continue
    else:target=p.parent/path if path else p
    target=target.resolve()
    if target.is_dir():target=target/'index.html'
    links+=1
    if not target.exists():errors.append(f'{p.relative_to(SITE)}: missing {value}');continue
    fragment={'compare':'comparison','monthly':'monthlyBlock','deals':'dealsBlock'}.get(u.fragment,u.fragment)
    if u.fragment and target in pages and not pages[target].find(id=unquote(fragment)):errors.append(f'{p.relative_to(SITE)}: missing fragment {value}')
 catalog=json.loads((D/'catalog.json').read_text());today=datetime.now(TZ).date();stale=[]
 for b in catalog['branches']:
  age=(today-date.fromisoformat(b['file_date'])).days
  if age>1:stale.append({'branch_id':b['id'],'file_date':b['file_date'],'age_days':age})
 report={'checked_at':datetime.now(TZ).isoformat(),'page_count':count,'local_link_count':links,'errors':errors,'stale_branches':stale,'status':'ok' if not errors and not stale else 'needs_attention'}
 (D/'site-health.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(report,ensure_ascii=False,indent=2));return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--strict-freshness',action='store_true');a=p.parse_args();r=audit();assert not r['errors'],'Broken public assets/links';assert not(a.strict_freshness and r['stale_branches']),'Stale price sources'
