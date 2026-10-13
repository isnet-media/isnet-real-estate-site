"""Apply verified museum card photographs; no network, collection, or publishing."""
import json,re
from pathlib import Path

def apply_ashdod_museum_media(events,root):
 path=Path(root)/'events-preview/ashdod/data/museum-official-media.json'
 if not path.is_file():return 0
 catalog=json.loads(path.read_text())
 count=0
 for event in events:
  day=str(event.get('start_date') or '')
  if day<catalog.get('not_before','') or day>catalog.get('not_after','9999-12-31'):continue
  title=str(event.get('title') or '')
  venue=str(event.get('venue') or event.get('venue_name') or '')
  for rule in catalog.get('rules',[]):
   if not re.search(rule['title_pattern'],title):continue
   # Excludes the Philistine museum and unrelated same-name activities.
   if not re.search(r'מוזיאון אשדוד לאמנות|מוזאון אשדוד לאמנות|טכניקות|אגף הסדנאות',venue):continue
   previous=event.get('image_url')
   if previous and previous!=rule['image_url']:
    saved=event.setdefault('previous_image_sources',[])
    if previous not in saved:saved.append(previous)
   event.update(image_url=rule['image_url'],image_origin_url=rule['origin_url'],
    image_source='ashdodartmuseum_official',image_verified=True,image_publishable=True,
    image_represents_event=True,source_image_kind='source_card_image',
    image_strategy='verified_museum_source',image_review_status='official_museum_card',
    image_rights_status='publisher_directed_source_reuse',image_caption=rule['credit'],
    thumbnail_url=rule['image_url'],thumbnail_ready=True,thumbnail_strategy='official_source_photo',
    thumbnail_source='ashdodartmuseum_official',museum_source_url=rule['source_url'])
   event.update(rule.get('fact_updates',{}))
   checks=event.setdefault('crosscheck_sources',[])
   if rule['source_url'] not in checks:checks.append(rule['source_url'])
   event.pop('rejected_source_image_url',None)
   count+=1
   break
 return count
