"""Reject truncated homepage uploads and broken inline application scripts."""
from pathlib import Path
from html.parser import HTMLParser
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
class Page(HTMLParser):
 def __init__(self):super().__init__();self.inline=[];self.current=None;self.sources=[];self.ids=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if a.get('id'):self.ids.append(a['id'])
  if tag=='script':
   if a.get('src'):self.sources.append(a['src'])
   else:self.current=[]
 def handle_data(self,data):
  if self.current is not None:self.current.append(data)
 def handle_endtag(self,tag):
  if tag=='script' and self.current is not None:self.inline.append(''.join(self.current));self.current=None
text=(ROOT/'SUPER.ASHDOD/index.html').read_text();assert text.rstrip().endswith('</body></html>'),'Homepage is truncated'
p=Page();p.feed(text);assert p.current is None,'Unclosed inline script'
assert any(s.startswith('live.js') for s in p.sources),'Missing live price application'
for key in ('home','cityBasket','choiceBlock','dealsBlock','familyBlock','products','basket'):assert p.ids.count(key)==1,key
with tempfile.TemporaryDirectory() as directory:
 for i,script in enumerate(p.inline):
  path=Path(directory)/f'inline-{i}.js';path.write_text(script);subprocess.run(['node','--check',str(path)],check=True)
print('Verified complete homepage, required sections, live price loader and inline JavaScript syntax')
