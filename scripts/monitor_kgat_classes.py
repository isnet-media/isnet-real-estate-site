"""Check reviewed sources monthly. Changes require review; never guess new groups."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def main():
 base=ROOT/'meusharim/kiryat-gat/data'
 config=json.loads((base/'source-monitor.json').read_text());results=[]
 for source in config['sources']:
  row={'url':source['url'],'checked_at':datetime.now(timezone.utc).isoformat()}
  try:
   response=requests.get(source['url'],timeout=45);response.raise_for_status()
   soup=BeautifulSoup(response.text,'html.parser');nodes=soup.select(source['selector'])
   if not nodes:raise ValueError('Expected source content missing')
   text=' '.join(x.get_text(' ',strip=True) for x in nodes)
   digest=hashlib.sha256(text.encode()).hexdigest()
   row.update(status='unchanged' if digest==source['reviewed_sha256'] else 'needs_editorial_review',observed_sha256=digest)
  except Exception as exc:row.update(status='unavailable',error=type(exc).__name__)
  results.append(row)
 report={'checked_at':datetime.now(timezone.utc).isoformat(),'sources':results,'catalogue_preserved':True}
 (base/'source-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
