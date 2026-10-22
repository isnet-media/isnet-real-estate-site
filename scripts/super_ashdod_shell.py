"""Single shared supermarket brand + category template, applied before publication.
Run this after any generator and before upload. New HTML pages are included
without being manually registered. Only checkout-local QA fixtures are excluded.
"""
from pathlib import Path
import argparse,os,re
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'SUPER.ASHDOD'
TEMPLATE=SITE/'assets/branding/super-shell.html'
START='<!-- SUPER_SHELL_START -->';END='<!-- SUPER_SHELL_END -->'
VERSION='4'

def render_shell(prefix,category=None,cart_count=False):
 text=TEMPLATE.read_text().strip().replace('{{ROOT}}',prefix).replace('{{CART_COUNT}}',' <span class="super-cart-count" id="count">0</span>' if cart_count else '')
 if category:
  text=re.sub(r'(<a\b[^>]*data-super-category="'+re.escape(category)+r'"[^>]*)(>)',r'\1 aria-current="page"\2',text,count=1)
 return START+text+END

def decorate(text,path):
 relative=Path(path).relative_to(SITE)
 prefix=os.path.relpath(SITE,Path(path).parent).replace(os.sep,'/')+'/'
 category='home' if relative==Path('index.html') else 'recipes' if relative.parts[0]=='recipes' else 'smart' if relative.parts[0]=='smart-shopping' else 'deals' if relative.parts[0]=='deals' else None
 shell=render_shell(prefix,category,cart_count=category=='home')
 # Legacy guides use implicit head/body; make those explicit before decoration.
 if not re.search(r'<head(?:\s|>)',text,re.I):
  text=re.sub(r'(<html\b[^>]*>)',r'\1<head>',text,count=1,flags=re.I)
  marker=re.search(r'<(?:header|main|body)\b',text,re.I)
  if marker:
   text=text[:marker.start()]+'</head><body>'+text[marker.start():]
  if '</body>' not in text.lower():text=text.replace('</html>','</body></html>')
 if not re.search(r'<body(?:\s|>)',text,re.I):
  text=re.sub(r'</head>', '</head><body>',text,count=1,flags=re.I)
  text=re.sub(r'</html>', '</body></html>',text,count=1,flags=re.I)
 if START in text:
  text=re.sub(re.escape(START)+r'.*?'+re.escape(END),lambda m:shell,text,count=1,flags=re.S)
 else:
  # Upgrade old single-page headers; remove the former category block with it.
  text=re.sub(r'(<body\b[^>]*>\s*)<header\b.*?</header>(?:<div class="super-categories">.*?</nav><button.*?</button></div></div>)?', lambda m:m[1],text,count=1,flags=re.S)
  text=re.sub(r'(<body\b[^>]*>)',lambda m:m[0]+shell,text,count=1,flags=re.I)
 text=re.sub(r'<link\b[^>]*href="[^"]*assets/branding/super-header\.css[^\"]*"[^>]*>','',text)
 text=re.sub(r'<script\b[^>]*src="[^"]*assets/branding/super-header\.js[^\"]*"[^>]*>\s*</script>','',text)
 assets=f'<link rel="stylesheet" href="{prefix}assets/branding/super-header.css?v={VERSION}"><script defer src="{prefix}assets/branding/super-header.js?v={VERSION}"></script>'
 text=re.sub(r'<script\b[^>]*src="[^"]*assets/ashdod-analytics\.js[^"]*"[^>]*>\s*</script>','',text)
 assets+=f'<script defer src="{prefix}assets/ashdod-analytics.js?v=1"></script>'
 text=re.sub(r'<link\b[^>]*href="[^"]*assets/design-system\.css[^"]*"[^>]*>','',text)
 assets+=f'<link rel="stylesheet" href="{prefix}assets/design-system.css?v=1">'
 text=text.replace('</head>',assets+'</head>',1)
 assert text.count(START)==text.count(END)==1,path
 assert text.count('class="super-sticky"')==1 and text.count('class="super-category-track"')==1,path
 assert '{{ROOT}}' not in text and '{{CART_COUNT}}' not in text,path
 return text

def pages():
 return sorted(p for p in SITE.rglob('*.html') if 'assets' not in p.relative_to(SITE).parts and not p.name.startswith('qa-'))

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
 for path in pages():
  text=path.read_text();expected=decorate(text,path)
  if args.check:assert text==expected,f'Shared brand/category shell is missing or stale: {path}'
  elif text!=expected:path.write_text(expected)
 print(f'{"Verified" if args.check else "Synchronized"} shared shell on {len(pages())} supermarket pages')
if __name__=='__main__':main()
