#!/usr/bin/env python3
"""Deterministic editorial cleanup, overlap classification and approved fallbacks."""
import copy,json,re
from check_preexisting_event_id_collisions import duplicate_groups, verify_preserved_duplicates
from collections import defaultdict,Counter
from pathlib import Path
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from apply_rishon_editorial import venue_key
from rishon_editorial_sources import norm
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'events-preview/rishon-lezion';TODAY=datetime.now(ZoneInfo('Asia/Jerusalem')).date();LIMIT=(TODAY+timedelta(days=153)).isoformat()
def fallback(e):
 cat=e.get('category');sub=e.get('subcategory','');title=e.get('title','')
 if 'seniors'in e.get('audiences',[]):
  name='senior-digital'if re.search('דיגיטל|מחשב|מדיה|וורד|אקסל',title)else'senior-guided-tour'if cat=='tour'else'senior-live-music'if cat=='music'else'senior-cinema'if cat=='cinema'else'senior-theater'if cat=='theatre'else'senior-handcraft'if cat=='workshop'else'senior-social-coffee'if cat=='community'else'senior-lecture'
  return '../shared/images/defaults/ashdod-seniors/'+name+'.webp'
 if cat=='kids':
  if sub in ['kids-story','story-time']:return '../ashdod/assets/illustrations/v1/story-time.webp'
  if sub=='kids-music':return '../ashdod/assets/illustrations/v2/parent-child-play.webp'
  return '../ashdod/assets/illustrations/v4/children-theatre.webp'
 name={'music':'live-music','theatre':'theatre-stage','community':'wellbeing-circle','workshop':'adult-crafts','exhibition':'history-museum','tour':'history-museum','festival':'live-music','cinema':'theatre-stage'}.get(cat)
 if cat=='lecture':return '../ashdod/assets/illustrations/v1/lecture.webp'
 if cat=='standup':return '../ashdod/assets/illustrations/v2/standup-stage.webp'
 return '../ashdod/assets/illustrations/v4/'+name+'.webp'if name else None

def finalize(data,catalog):
 from repair_rishon_public_quality import prepare,finish
 # Snapshot every already-shared identifier before any editorial mutation.
 # These identities can be linked from public pages and the CMS.
 before=copy.deepcopy(data['events'])
 protected_ids=frozenset(duplicate_groups(before))
 data,catalog=prepare(data,catalog)
 events=data['events'];aliases={norm(k):norm(v)for k,v in catalog.get('title_aliases',{}).items()};by_name=defaultdict(list);stats=Counter()
 # Colliding IDs are an audit finding, NOT a reason to discard one record.
 # Reconciliation requires source identity, CMS and public-link verification.
 counts=Counter(e.get('event_id') for e in events)
 stats['repeated_ids']=sum(n-1 for n in counts.values() if n>1)
 stats['preexisting_collision_groups_for_review']=len(protected_ids)
 for p in catalog['programs']:by_name[norm(p['lookup_title'])].append(p)
 def key(e):return aliases.get(norm(e['title']),norm(e['title']))
 for e in events:
  if e.get('event_id') in protected_ids:continue
  day=e.get('start_date','')
  if day<TODAY.isoformat():continue
  if day>LIMIT:
   if e.get('is_active')is not False:e['is_active']=False;e['visibility_reason']='outside_editorial_window';stats['outside_window']+=1
   continue
  if e.get('visibility_reason')=='outside_editorial_window':e['is_active']=True;e.pop('visibility_reason',None)
  candidates=by_name[key(e)];url=e.get('detail_source_url')or e.get('content_source_url')or e.get('image_source');p=next((p for p in candidates if p.get('lookup_url')==url),None)
  if not p and len(candidates)==1:p=candidates[0]
  if not p and candidates and len(set(x['description']for x in candidates))==1:p=candidates[0]
  if p and not(e.get('content_origin')=='manual'and e.get('content_locked')):
   if p.get('display_title'):
    e.setdefault('source_title',e['title']);e['title']=p['display_title']
   text=p['description'];cat=p['category'];e.update(category=cat,subcategory=p['subcategory'],description=text,long_description=text,series_description=text,editorial_description=text,short_pitch=text.split('. ')[0]+'.',description_manual_override=True,content_locked=True,content_origin='editorial',editorial_version=1,content_ready_for_media=True,content_enrichment_status='ready')
   if e.get('category')=='kids':e['audiences']=['kids','families']
   elif 'kids'in e.get('audiences',[]):e['audiences']=[a for a in e['audiences']if a not in ['kids','families']]+['adults']
   if not e.get('content_source_url'):e['content_source_url']=p['source_url']
   stats['catalog_applied']+=1
  if e.get('category')=='other':
   urls=' '.join(str(e.get(k)or'')for k in ['ticket_url','content_source_url','image_source'])
   if '/stand-up/'in urls:e['category']='standup';e['subcategory']='standup';stats['classified_by_source']+=1
   elif '/kids-shows/'in urls:e['category']='kids';e['subcategory']='kids-theatre';e['audiences']=['kids','families'];stats['classified_by_source']+=1
  # An unnamed film is a calendar placeholder, not a publishable program.
  if norm(e['title']) in ['הקרנת סרט','מופע פרטים בהמשך']:
   e['is_active']=False;e['visibility_reason']='awaiting_program_details';stats['awaiting_identity']+=1
  if e.get('is_active')is False:continue
  if e.get('category')=='standup'and re.search('מרתון',e['title'])and 'פאצ' in (str(e.get('venue',''))+' '+e['title']):
   if len(e.get('long_description')or e.get('description')or'')<110:
    text='ערב סטנדאפ במתכונת מרתון בפאצ׳ו בר בראשון לציון, לקהל הבוגר ולחובבי הופעות קומיות. בכל כרטיס מופיעים המועד המסוים ופרטי ההזמנה. את הרכב המשתתפים ותנאי הכניסה המעודכנים יש לבדוק בעמוד המארגן של אותו ערב.'
    e.update(description=text,long_description=text,series_description=text,editorial_description=text,description_manual_override=True,content_origin='editorial',content_ready_for_media=True)
  cats=set(e.get('categories',[]));cats.discard('other');cats.add(e.get('category'))
  if 'seniors'in e.get('audiences',[]):cats.add('seniors')
  e['categories']=sorted(x for x in cats if x)
 groups=defaultdict(list)
 for e in events:
  if TODAY.isoformat()<=e.get('start_date','')<=LIMIT and e.get('is_active')is not False:groups[(key(e),e['start_date'],str(e.get('start_time')or'')[:5],venue_key(e.get('venue')))].append(e)
 for rows in groups.values():
  if len(rows)<2 or any(e.get('event_id') in protected_ids for e in rows):continue
  primary=max(rows,key=lambda e:(bool(e.get('editorial_version')),bool(e.get('source_content_authoritative')),len(e.get('long_description')or e.get('description')or''),bool(e.get('image_verified'))))
  for other in rows:
   if other is primary:continue
   if not primary.get('image_verified')and other.get('image_verified'):
    for k in ['image_url','image_source','image_origin_url','image_credit','image_verified','image_publishable','image_strategy','image_rights_status','thumbnail_url','thumbnail_ready']:
     if k in other:primary[k]=other[k]
   other['is_active']=False;other['duplicate_of']=primary['event_id'];other['canonical_event_id']=primary['event_id'];stats['duplicates']+=1
 by_id={e['event_id']:e for e in events}
 for e in events:
  if e.get('event_id') in protected_ids or e.get('canonical_event_id') in protected_ids:continue
  target=e.get('canonical_event_id');seen={e['event_id']}
  while target and target not in seen and target in by_id:
   seen.add(target);next_id=by_id[target].get('canonical_event_id')
   if not next_id:break
   target=next_id
  if target and target not in [e['event_id']]:e['canonical_event_id']=target;e['duplicate_of']=target
 for e in events:
  if e.get('event_id') in protected_ids:continue
  if not TODAY.isoformat()<=e.get('start_date','')<=LIMIT or e.get('is_active')is False:continue
  if not(e.get('image_verified')and e.get('image_url')):
   image=fallback(e)
   if image and(SITE/image).exists():
    e.update(image_url=image,image_source='ISNET approved activity illustration bank',image_origin_url=image,image_credit='אילוסטרציה להמחשה: ISNET',image_strategy='approved_category_illustration',image_verified=True,image_publishable=True,image_rights_status='isnet_owned_illustration',thumbnail_url=image,thumbnail_ready=True);stats['approved_illustrations']+=1
 stats.update(finish(data,catalog,protected_event_ids=protected_ids))
 # prepare() can normalize fields before the editorial passes. Do not
 # rewrite even those fields on a record in an unresolved collision group.
 if len(data['events'])!=len(before):
  raise ValueError('Rishon finalizer changed record count; refusing unsafe write')
 for i,original in enumerate(before):
  if original.get('event_id') in protected_ids:
   data['events'][i]=original
 verify_preserved_duplicates(before,data['events'],'rishon-lezion')
 return data,dict(stats)

def main():
 path=SITE/'data/events.json';data=json.loads(path.read_text());catalog=json.loads((SITE/'data/editorial-programs.json').read_text());data,stats=finalize(data,catalog);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');active=[e for e in data['events']if e.get('start_date','')>=TODAY.isoformat()and e.get('is_active')is not False];report={'checked_at':datetime.now(ZoneInfo('Asia/Jerusalem')).isoformat(),'window_end':LIMIT,'active_events':len(active),'categories':dict(Counter(e.get('category')for e in active)),'with_editorial_text':sum(max(len(e.get(k)or'')for k in ['description','long_description','series_description'])>=110 for e in active),'original_photos':sum(e.get('image_verified')is True and e.get('image_strategy')!='approved_category_illustration'for e in active),'approved_illustrations':sum(e.get('image_strategy')=='approved_category_illustration'for e in active),'without_image':sum(not e.get('image_verified')for e in active),'changes':stats,'needs_review':[{'id':e['event_id'],'title':e['title'],'category':e.get('category'),'source':e.get('ticket_url')}for e in active if e.get('category')=='other'or max(len(e.get(k)or'')for k in ['description','long_description','series_description'])<110]};(ROOT/'events-preview/admin/data/rishon-readiness.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='needs_review'},ensure_ascii=False))
if __name__=='__main__':main()
