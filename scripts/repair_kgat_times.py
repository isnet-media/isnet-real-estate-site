"""Convert explicitly timezone-qualified source timestamps to Israel time."""
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import requests
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parents[1]/'events-preview/kiryat-gat'
def walk(v):
 if isinstance(v,list):
  for x in v:yield from walk(x)
 elif isinstance(v,dict):
  if 'Event' in str(v.get('@type','')):yield v
  for x in v.values():
   if isinstance(x,(list,dict)):yield from walk(x)
def run():
 d=json.loads((R/'data/events.json').read_text());soup=BeautifulSoup(requests.get('https://www.makore.co.il/browse/city/קריית-גת',timeout=25).content,'html.parser');mapping={}
 for n in soup.select('script[type="application/ld+json"]'):
  try:rows=walk(json.loads(n.string or n.get_text()))
  except ValueError:continue
  for x in rows:
   try:dt=datetime.fromisoformat(x.get('startDate','').replace('Z','+00:00'))
   except ValueError:continue
   if dt.tzinfo is None:continue
   local=dt.astimezone(ZoneInfo('Asia/Jerusalem'));mapping[(x.get('name'),dt.date().isoformat(),dt.strftime('%H:%M'))]=(local.date().isoformat(),local.strftime('%H:%M'))
 changed=0
 for e in d['events']:
  key=(e['title'],e['start_date'],e['start_time'])
  if any(s.get('name')=='makore_kgat' for s in e.get('sources',[])) and key in mapping and not e.get('kgat_timezone_corrected'):
   e['start_date'],e['start_time']=mapping[key];e['kgat_timezone_corrected']=True;changed+=1
 (R/'data/events.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print('Timezone-qualified source timestamps repaired:',changed)
if __name__=='__main__':run()
