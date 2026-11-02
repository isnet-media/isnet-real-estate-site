"""Add verified FRIENDS dates; attach alternate sellers to matching occurrences."""
import concurrent.futures,re,json
from difflib import SequenceMatcher
import sync_holon_events as h

def main():
 spec=next(s for s in h.read('sources')['sources'] if s['id']=='friends');rows,report=h.ingest(spec)
 raw=h.read('events');added=0;matched=0
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:rows=list(ex.map(h.enrich,rows))
 for e in rows:
  title=h.core.text_norm(e['title'])
  found=next((x for x in raw['events'] if x['start_date']==e['start_date'] and x['start_time']==e['start_time'] and (SequenceMatcher(None,h.core.text_norm(x['title']),title).ratio()>.68 or title.startswith(h.core.text_norm(x['title'])) or h.core.text_norm(x['title']).startswith(title))),None)
  if found:
   found.setdefault('additional_sources',[])
   if e['source_url'] not in found['additional_sources']:found['additional_sources'].append(e['source_url'])
   matched+=1
  else:raw['events'].append(e);added+=1
 raw['events'].sort(key=lambda e:(e['start_date'],e['start_time'],e['title']));h.save('events',raw)
 r=h.read('source-report');r['sources']=[x for x in r['sources'] if x['id']!='friends']+[report];h.save('source-report',r)
 print(json.dumps(dict(added=added,matched=matched,report=report),ensure_ascii=False))
if __name__=='__main__':main()
