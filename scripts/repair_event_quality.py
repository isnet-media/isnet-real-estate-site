#!/usr/bin/env python3
"""Deterministic, bounded repairs. Never generates facts or overwrites editorial locks."""
import argparse, copy, hashlib, json, os, re
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from audit_ashdod_subcategories import infer

ROOT=Path(__file__).resolve().parents[1]
INACTIVE={'hidden','draft','unpublished','archived','trashed','deleted','cancelled','canceled'}
IMAGE_FIELDS=('image_url','image_origin_url','image_source','image_credit','image_verified','image_publishable','image_represents_event','source_image_kind','image_strategy','image_rights_status')
def norm(s): return re.sub(r'\s+',' ',str(s or '')).strip()
def locked(e, field):
    return field in (e.get('locked_fields') or []) or e.get(field+'_manual_override') is True or (field.startswith(('image_','thumbnail_')) and e.get('image_manual_override') is True)
def active(e,day):
    return e.get('is_active') is not False and e.get('status') not in INACTIVE and e.get('publication_status') not in INACTIVE and (e.get('end_date') or e.get('start_date') or '')>=day

def repair(data,taxonomy,definitions,catalog,day):
    """Pure operation for tests and dry runs; change records retain exact before/after."""
    data=copy.deepcopy(data);tax=copy.deepcopy(taxonomy);changes=[];issues=[]
    def issue(kind,e,reason):
        identity=str(e.get('event_id') or e.get('id') or 'system')
        key=hashlib.sha256((kind+'|'+identity+'|'+reason).encode()).hexdigest()[:20]
        issues.append(dict(id=key,type=kind,event_id=identity,title=e.get('title',''),reason=reason))
    def set_fields(e,fields,reason):
        delta={k:v for k,v in fields.items() if e.get(k)!=v}
        if any(locked(e,k) for k in delta):
            issue('editorial_lock',e,reason);return False
        if not delta:return False
        changes.append(dict(event_id=e.get('event_id'),reason=reason,before={k:e.get(k) for k in delta},after=delta))
        e.update(delta);return True
    defs=definitions['categories']
    for cat in tax['primary_categories']:
        if cat['id'] not in defs:
            if cat.get('requires_mapping') is not True:
                changes.append(dict(event_id='taxonomy:'+cat['id'],reason='unreviewed_source_taxonomy',before={'requires_mapping':cat.get('requires_mapping')},after={'requires_mapping':True}))
                cat['requires_mapping']=True
            issue('taxonomy_mapping',{'id':cat['id'],'title':cat.get('label','')},'Primary category lacks reviewed classification definitions')
        approved=defs.get(cat['id'],{}).get('subcategories',{})
        for sub in cat.get('subcategories',[]):
            if sub['id'] not in approved:
                if sub.get('requires_mapping') is not True:
                    changes.append(dict(event_id='taxonomy:'+cat['id']+'/'+sub['id'],reason='unreviewed_source_taxonomy',before={'requires_mapping':sub.get('requires_mapping')},after={'requires_mapping':True}))
                    sub['requires_mapping']=True
                issue('taxonomy_mapping',{'id':cat['id']+'/'+sub['id'],'title':sub.get('label','')},'Source subtype lacks a reviewed definition; retained for mapping, excluded from automatic classification')
    valid={c['id']:{s['id'] for s in c.get('subcategories',[]) if s['id'] in defs.get(c['id'],{}).get('subcategories',{})} for c in tax['primary_categories']}
    seen={};rows=[]
    for e in data['events']:
        eid=e.get('event_id')
        if not eid:raise ValueError('Missing event_id')
        if eid in seen:
            if e==seen[eid]:
                changes.append(dict(event_id=eid,reason='identical_duplicate_row',before={'copies':2},after={'copies':1}));continue
            raise ValueError('Conflicting event_id: '+eid+'; no writes performed')
        seen[eid]=e;rows.append(e)
    data['events']=rows
    # Media donors must be the SAME production and SAME explicit source detail URL.
    donors={}
    for e in rows:
        if (e.get('image_url') and e.get('image_verified') is True and e.get('image_publishable') is True and e.get('image_represents_event') is True and e.get('source_image_kind')=='source_card_image' and not re.search(r'illustration|defaults/|placeholder|no_pic|favicon|opengraph-image',e['image_url'],re.I)):
            key=(norm(e.get('title')),e.get('content_source_url'))
            if key[0] and key[1]:donors.setdefault(key,[]).append(e)
    clips=[]
    for artist in catalog.get('artists',[]):
        if artist.get('video_verified') is True and re.fullmatch(r'[\w-]{11}',artist.get('youtube_id','')):
            try: recent=0 <= (datetime.fromisoformat(day).date()-datetime.fromisoformat(artist['verified_at'][:10]).date()).days <=30
            except (KeyError,ValueError):recent=False
            if recent:clips.append(artist)
    slots={}
    for e in rows:
        if not active(e,day):continue
        cat=e.get('category');sub=e.get('subcategory')
        if not sub or sub not in valid.get(cat,set()):
            target,confidence,evidence,conflict=infer(e,valid,defs)
            if target and confidence>=0.95 and not conflict and evidence in ('title','source_explicit_subcategory') and not locked(e,'category'):
                set_fields(e,{'subcategory':target,'subcategory_review_status':'auto_repaired_from_explicit_evidence','subcategory_review_confidence':confidence},'verified_subcategory_rule')
            if e.get('subcategory') not in valid.get(cat,set()):issue('subcategory',e,'No unambiguous approved subtype from explicit event evidence')
        bad_image=not e.get('image_url') or e.get('image_publishable') is not True or e.get('source_image_kind') in ('illustration','source_placeholder','not_available') or e.get('image_represents_event') is False or re.search(r'illustration|defaults/|placeholder|no_pic|favicon',str(e.get('image_url')),re.I)
        if bad_image:
            matches=donors.get((norm(e.get('title')),e.get('content_source_url')),[])
            urls={x['image_url'] for x in matches}
            if len(urls)==1:
                donor=matches[0];fields={k:donor[k] for k in IMAGE_FIELDS if k in donor}
                fields.update(thumbnail_ready=False,thumbnail_url=None)
                set_fields(e,fields,'verified_same_source_production_image')
            else:issue('image',e,'No unique verified same-production source image; research required')
        if cat=='standup' and not e.get('youtube_id'):
            title=re.sub(r'\s+(?:במופע סטנדאפ|במופע סטנד אפ|בסטנדאפ|סטנדאפ)$','',norm(e.get('title')))
            matches=[a for a in clips if title in [norm(x) for x in a.get('aliases',[a['name']])]]
            if len({a['youtube_id'] for a in matches})==1:
                a=matches[0];set_fields(e,dict(youtube_id=a['youtube_id'],youtube_title=a['youtube_title'],youtube_note=a.get('youtube_note','קטע מייצג של האמן, לא טריילר למופע המסוים.'),video_verified=True,clip_type='representative'),'verified_exact_artist_catalog')
            if not e.get('youtube_id'):issue('standup_video',e,'No recent verified exact artist clip; never guess a video')
        if not any(norm(e.get(k)) for k in ('description','long_description','series_description')):issue('content',e,'Missing event description; source research required')
        key=(norm(e.get('title')),e.get('start_date'),e.get('start_time'),norm(e.get('venue')))
        if key in slots:issue('possible_duplicate',e,'Same title/date/time/venue as '+slots[key]+'; preserve IDs pending source comparison')
        else:slots[key]=e['event_id']
    return data,tax,changes,issues

def run(root=ROOT,apply=False,day=None):
    day=day or datetime.now(ZoneInfo('Asia/Jerusalem')).date().isoformat()
    admin=root/'events-preview/admin/data';feed=root/'events-preview/ashdod/data/events.json';taxpath=admin/'taxonomy.json'
    inputs={p:p.read_bytes() for p in (feed,taxpath,admin/'subcategory-definitions.json',root/'events-preview/shared/standup-videos.json')}
    data,tax,changes,issues=repair(*[json.loads(v) for v in inputs.values()],day)
    # Bound unexpected broad modifications. Refuse before any data write.
    if len(changes)>max(150,len(data['events'])//3):raise ValueError('Repair change limit exceeded; no writes performed')
    # Independent schema and protected-field invariants.
    before=json.loads(inputs[feed]);original={e['event_id']:e for e in before['events']}
    assert len({e['event_id'] for e in data['events']})==len(data['events'])
    for e in data['events']:
        old=original[e['event_id']]
        for field in ('title','start_date','start_time','venue','purchase_url','ticket_url','category','status','publication_status'):
            assert old.get(field)==e.get(field),field
        for field in old.get('locked_fields') or []:assert old.get(field)==e.get(field),field
    now=datetime.now(timezone.utc).isoformat()
    for filename in ('ashdod-local-report.json','ashdod-supplemental-report.json','mevalim-ashdod-direct-report.json'):
        path=admin/filename
        try:
            source=json.loads(path.read_text());stamp=source.get('at') or source.get('generated_at');age=(datetime.now(timezone.utc)-datetime.fromisoformat(stamp.replace('Z','+00:00'))).total_seconds()/3600
            if age>36:issues.append(dict(id='stale-'+filename,type='source_stale',title=filename,reason='Last source report exceeds 36 hours'))
            for name,row in source.get('sources',{}).items():
                if row.get('ok') is False or row.get('issues') or row.get('detail_fetch_failures') or row.get('card_detail_errors'):issues.append(dict(id='source-'+name,type='source_partial',title=name,reason='Source reports failed or partial collection'))
        except (OSError,ValueError,TypeError):issues.append(dict(id='unreadable-'+filename,type='source_unknown',title=filename,reason='Source report unavailable or invalid; not assumed healthy'))
    if os.getenv('UPSTREAM_CONCLUSION') and os.environ['UPSTREAM_CONCLUSION']!='success':
        issues.append(dict(id='upstream-workflow',type='source_workflow_failed',title=os.getenv('UPSTREAM_NAME','איסוף'),reason='Upstream workflow '+os.environ['UPSTREAM_CONCLUSION']+'; '+os.getenv('UPSTREAM_URL','')))
    cinema=json.loads((root/'events-preview/ashdod/data/cinema.json').read_text())
    for m in cinema.get('movies',[]):
        if any(any(d>=day and t for d,t in v.get('schedule',{}).items()) for v in m.get('venues',[])) and not m.get('trailer_youtube_id'):issues.append(dict(id='trailer-'+m['id'],type='cinema_trailer',title=m.get('title'),reason='Active film lacks embedded trailer'))
    report=dict(schema_version=1,checked_at=now,mode='apply' if apply else 'dry_run',state='attention' if issues else 'healthy',scope='Ashdod source feeds; CMS overlays remain authoritative; no claim of live-page verification',input_sha256={str(p.relative_to(root)):hashlib.sha256(b).hexdigest() for p,b in inputs.items()},repairs=changes,unresolved=issues,counts=dict(repairs=len(changes),unresolved=len(issues)))
    if apply:
        feed.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');taxpath.write_text(json.dumps(tax,ensure_ascii=False,indent=2)+'\n')
        # Reread persisted facts; only then report a completed data repair.
        assert json.loads(feed.read_text())==data and json.loads(taxpath.read_text())==tax
        report['data_readback_verified']=True
        history_path=admin/'automatic-repair-history.json'
        history=json.loads(history_path.read_text()) if history_path.exists() else {'schema_version':1,'repairs':[]}
        known={x['repair_id'] for x in history['repairs']}
        for change in changes:
            repair_id=hashlib.sha256(json.dumps(change,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            if repair_id not in known:
                history['repairs'].append({'repair_id':repair_id,'checked_at':now,**change});known.add(repair_id)
        history_path.write_text(json.dumps(history,ensure_ascii=False,indent=2)+'\n')
    (admin/'automatic-repair-status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'state':report['state'],**report['counts'],'applied':apply},ensure_ascii=False))
    return report
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args();run(apply=args.apply)
