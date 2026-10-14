"""Compare 20 deterministic catalog records to cached public source pages."""
import json,hashlib,pathlib,sys
from bs4 import BeautifulSoup
root=pathlib.Path(__file__).resolve().parents[1];cache=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else root/'.cache/meusharim');data=root/'meusharim/ashdod/data';records=json.loads((data/'classes.json').read_text())['records']
sample=[]
for i in range(20):
 r=records[i*(len(records)-1)//19];key=hashlib.sha256((r['source_url']+'None').encode()).hexdigest();s=BeautifulSoup(json.loads((cache/(key+'.json')).read_text())['body'],'html.parser').select_one('.event-single')
 def text(sel):
  e=s.select_one(sel);return e.get_text(' ',strip=True) if e else ''
 a=s.select_one('a.buy[href]');url=a['href'] if a and a['href'].startswith('https://') else None
 comparisons={'name':text('h1')==r['name'],'subtitle':text('.title h2')==r['subtitle'],'ages':[a.get_text(' ',strip=True) for a in s.select('.ages a')]==r['ages'],'registration_url':url==r['registration_url'],'description':text('.text-container')==r['description'],'schedule':[{'day':(x.select_one('.date').get_text(' ',strip=True) if x.select_one('.date') else ''),'time':(x.select_one('.time').get_text(' ',strip=True) if x.select_one('.time') else '')} for x in s.select('.shedule-day')]==r['schedule']}
 sample.append({'id':r['id'],'name':r['name'],'source_url':r['source_url'],'verified_at':r['verified_at'],'checks':comparisons,'passed':all(comparisons.values())})
report={'sample_size':len(sample),'passed':sum(r['passed'] for r in sample),'records':sample};(data/'qa-sample.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('source sample',report['passed'],'/',len(sample));assert report['passed']==20
assert len(records)==len({r['id'] for r in records})==len({r['source_url'] for r in records})
assert all(r['detail_verified'] for r in records)
print('Unique IDs, URLs and detail verification PASS',len(records))
