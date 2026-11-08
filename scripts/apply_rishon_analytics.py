"""Apply Rishon's verified GA4 tag to all present/future pages at publication."""
from pathlib import Path
import argparse,re
ROOT=Path(__file__).resolve().parents[1]
TAG='<script src="/assets/rishon-analytics.js?v=20261108-1" defer></script>'
SCOPES=('events-preview/rishon-lezion','SUPER.RISHON')
def decorate(text):
 text=re.sub(r'<script\b[^>]*src="/assets/rishon-analytics\.js[^\"]*"[^>]*>\s*</script>\s*','',text)
 return re.sub(r'</head>',TAG+'\n</head>',text,count=1,flags=re.I)
def run(check=False):
 count=0;changed=[]
 for scope in SCOPES:
  for p in (ROOT/scope).rglob('*.html'):
   if 'assets' in p.relative_to(ROOT/scope).parts or p.name.startswith('qa-'):continue
   text=p.read_text();expected=decorate(text);assert expected.count('/assets/rishon-analytics.js')==1,p
   count+=1
   if text!=expected:
    changed.append(str(p.relative_to(ROOT)))
    if not check:p.write_text(expected)
 for p in (ROOT/'events-preview/rishon-lezion').glob('*.js'):
  if p.name == 'ashdod-analytics.js':continue
  text=p.read_text();expected=text.replace('window.ashdodAnalytics','window.rishonAnalytics')
  if text!=expected:
   changed.append(str(p.relative_to(ROOT)))
   if not check:p.write_text(expected)
 if check:assert not changed,changed
 print(f'Rishon GA4: {count} pages; {len(changed)} updated; property 384813671 / G-WMLNJMH6ZN')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');run(p.parse_args().check)
