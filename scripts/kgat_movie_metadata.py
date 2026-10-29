"""Reuse verified film-level metadata, never another city's screening schedules."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def enrich(movies):
 registry=json.loads((ROOT/'events-preview/shared/data/movie-editorial.json').read_text());aliases=registry['aliases']
 catalog=json.loads((ROOT/'events-preview/ashdod/data/cinema.json').read_text())['movies']
 for movie in movies:
  key=aliases.get(movie['id'],movie['id'])
  source=next((m for m in catalog if aliases.get(m['id'],m['id'])==key),None)
  if source and source.get('trailer_verification',{}).get('publisher_kind')=='official_publisher':
   for k in ['trailer_youtube_id','trailer_url','trailer_source_url','trailer_verification','runtime_minutes','age_rating','genres']:
    if k in source:movie[k]=source[k]
   movie['trailer_source_name']='United King Films — טריילר רשמי'
  image=movie.get('poster_url')
  if image and image.startswith('assets/'):
   movie['poster_url']='https://isnet.co.il/events-preview/kiryat-gat/'+image
   movie['poster_verification']={'url':movie['poster_url'],'source':'החברה העירונית קריית גת','kind':'official_promotional_event'}
 return movies
