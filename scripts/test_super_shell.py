"""Regression checks for new nested pages, idempotence and content preservation."""
from super_ashdod_shell import SITE,decorate,pages,START,VERSION
import json,re
from super_city_runtime import load
from html.parser import HTMLParser
from urllib.parse import urlsplit
class Links(HTMLParser):
 def __init__(self):super().__init__();self.refs=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  for key in ('href','src'):
   if key in d:self.refs.append(d[key])
for path in pages():
 source=path.read_text();assert decorate(source,path)==source,path
 parser=Links();parser.feed(source)
 for ref in parser.refs:
  url=urlsplit(ref)
  if url.scheme or url.netloc or not url.path:continue
  target=(path.parent/url.path).resolve()
  assert target.exists(),(path,ref)
newpath=SITE/'future'/'nested'/'new-page.html'
new='<!doctype html><html lang="he" dir="rtl"><head><title>New</title></head><body><article><header>Article title stays</header><p>New content</p></article></body></html>'
result=decorate(new,newpath)
assert result.count(START)==1 and 'Article title stays' in result and 'New content' in result
assert f'../../assets/branding/super-header.css?v={VERSION}' in result
assert 'href="../../compare/"' in result
assert '../../assets/design-system.css?v=1' in result
assert result.count('assets/design-system.css')==1
assert decorate(result,newpath)==result
implicit=decorate('<html><head><title>Implicit</title></head><main>Preserve future content</main></html>',newpath)
assert 'Preserve future content' in implicit and implicit.count(START)==1
legacy='<!doctype html><html lang="he"><meta charset="utf-8"><title>Old</title><header>Old site title</header><main>Keep guide</main></html>'
result=decorate(legacy,SITE/'guides'/'new-guide.html')
assert '<head>' in result and '<body>' in result and 'Keep guide' in result and 'Old site title' not in result
assert result.count(START)==1 and decorate(result,SITE/'guides'/'new-guide.html')==result
for city in ('ASHDOD','YAVNE','KGAT','RISHON','HOLON','BATYAM'):
 shell=load('super_ashdod_shell',city) if city!='ASHDOD' else __import__('super_ashdod_shell')
 home=shell.SITE/'index.html';catalog=json.loads((shell.SITE/'data/catalog.json').read_text())
 stale=re.sub(r'(<span id="intro(?:Product|Branch)Count">)[^<]*(</span>)',r'\g<1>999,999\2',home.read_text())
 rendered=shell.decorate(stale,home)
 for key,count in [('introProductCount',len(catalog['rows'])),('introBranchCount',len(catalog['branches']))]:
  assert f'<span id="{key}">{count:,}</span>' in rendered,(city,key)
 assert shell.decorate(rendered,home)==rendered,city
print('Verified catalogue-derived first-paint product and branch counts for all six cities, including stale template regression')
print(f'Checked shared shell on {len(pages())} pages and automatic handling of future nested pages')
