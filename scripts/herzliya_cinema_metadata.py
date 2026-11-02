"""Film metadata is shared by identity; sessions always remain Herzliya-owned."""
import copy,json
from pathlib import Path
from enrich_holon_media import norm
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'events-preview/herzliya/data'
def enrich_movies(movies,events):
 registry=json.loads((ROOT/'events-preview/shared/data/movie-editorial.json').read_text())['movies']
 shared={}
 for city in ['ashdod','rishon-lezion']:
  for m in json.loads((ROOT/f'events-preview/{city}/data/cinema.json').read_text())['movies']:shared.setdefault(norm(m['title']),m)
 reviewed=json.loads((D/'film-editorial.json').read_text()) if (D/'film-editorial.json').exists() else {}
 by_title={norm(k):v for k,v in reviewed.items()}
 for m in movies:
  original_id=m['id'];m['editorial']={'title':m['title'],'original_text':by_title.get(norm(m['title']),''),'synopsis_sources':[]}
  match=shared.get(norm(m['title']))
  if match:
   for key in ['trailer_youtube_id','trailer_source_url','trailer_source_name','trailer_verification','runtime_minutes','age_rating','genres','director','cast','year','poster_candidates']:
    if match.get(key):m[key]=copy.deepcopy(match[key])
   record=next((v for v in registry.values() if norm(v['title'])==norm(m['title'])),None)
   if record:m['editorial']=copy.deepcopy(record)
   elif not m['editorial']['original_text']:m['editorial']['original_text']=match.get('synopsis','')
  event=next((e for e in events if e['category']=='cinema' and __import__('re').sub(r'\s*\((?:שלישי זהב|ללא תשלום למנויים)\)','',e['title']).strip()==m['title']),None)
  if event:
   for field in ['runtime_minutes','director']:
    if event.get(field):m[field]=event[field]
   if event.get('image_source_url'):m['editorial']['synopsis_sources']=[event['image_source_url']]
   if event.get('trailer_youtube_id'):
    m['trailer_youtube_id']=event['trailer_youtube_id'];m['trailer_source_url']=event.get('trailer_source_url');m['trailer_verification']={'publisher_kind':'cinema_portal','source_url':event.get('trailer_source_url')}
  if not m['editorial']['original_text'] and event:m['editorial']['original_text']=event.get('description','')
  if m['editorial']['original_text']:
   m['editorial_text']=m['editorial']['original_text'];m['synopsis']=m['editorial_text'][:260]
  m['genres']=[x for x in m.get('genres',[]) if __import__('re').search('[א-ת]',x)]
  if m.get('age_rating') in ['other','unknown']:m.pop('age_rating',None)
  m['metadata_scope']='film_only; local venues and sessions preserved'
  assert m['id']==original_id

def apply_descriptions(events):
 reviewed=json.loads((D/'film-editorial.json').read_text())
 descriptions={norm(k):v for k,v in reviewed.items()}
 for city in ['ashdod','rishon-lezion']:
  for movie in json.loads((ROOT/f'events-preview/{city}/data/cinema.json').read_text())['movies']:
   descriptions.setdefault(norm(movie['title']),movie.get('synopsis',''))
 for e in events:
  if e['category']=='cinema' and descriptions.get(norm(e['title'])):e['description']=descriptions[norm(e['title'])]

def write_media_report(events,movies):
 p=D/'quality-report.json';report=json.loads(p.read_text()) if p.exists() else {}
 report['media_audit']={'checked_at':__import__('datetime').date.today().isoformat(),'occurrences':len(events),'official_image_occurrences':sum(e.get('image_role')=='official_promotional' for e in events),'unique_official_images':len({e['image']for e in events if e.get('image_role')=='official_promotional'}),'films':len(movies),'films_with_source_art':sum(m['poster_verification']['kind']=='official_promotional'for m in movies),'verified_trailers':sum(bool(m.get('trailer_youtube_id'))for m in movies),'pending_source_art':[{'id':e['id'],'title':e['title'],'source_url':e['source_url']}for e in events if e.get('image_role')!='official_promotional'],'fallback_policy':'Readable title card; no repeated generic event photograph'}
 report['event_photos']=report['media_audit']['official_image_occurrences']
 p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
