"""Resolve secondary time conflicts and keep old links as aliases."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def norm(v):return re.sub(r'[^\w\u0590-\u05ff]','',str(v).lower()).replace('קריית','קרית')
def venue(e):return norm(e.get('venue','')).replace('קריתגת','').replace('רחבת','')
def official(e):return any(s.get('source_type',s.get('type'))=='official' for s in e.get('sources',[]))
def reconcile(events):
 out=[];held=[]
 for e in sorted(events,key=lambda x:not official(x)):
  same=[x for x in out if norm(x.get('title'))==norm(e.get('title')) and x.get('start_date')==e.get('start_date') and venue(x)==venue(e)]
  target=next((x for x in same if x.get('start_time')==e.get('start_time')),None)
  if target is None and not official(e):target=next((x for x in same if official(x)),None)
  if target is None:out.append(e);continue
  alias={'event_id':e['event_id'],'title':e['title'],'url':e.get('ticket_url')}
  if alias not in target.setdefault('source_aliases',[]):target['source_aliases'].append(alias)
  for a in e.get('source_aliases',[]):
   if a not in target['source_aliases']:target['source_aliases'].append(a)
  if target.get('start_time')!=e.get('start_time'):
   held.append({'event_id':e['event_id'],'title':e['title'],'reason':'secondary_time_conflicts_with_live_official','official_time':target.get('start_time'),'secondary_time':e.get('start_time'),'canonical_id':target['event_id']})
  for s in e.get('sources',[]):
   if s not in target.setdefault('sources',[]):target['sources'].append(s)
 return out,held
def run():
 p=ROOT/'events-preview/kiryat-gat/data/events.json';d=json.loads(p.read_text());d['events'],held=reconcile(d['events']);d['stats']={'events':len(d['events'])};p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 p=ROOT/'events-preview/admin/data/kgat-duplicate-audit.json';p.write_text(json.dumps({'held':held},ensure_ascii=False,indent=2)+'\n');print('Duplicate conflicts resolved:',len(held))
if __name__=='__main__':run()
