(function(root){
  'use strict';
  const fields=['title','short_pitch','long_description','category','subcategory','start_date','end_date','start_time','venue','address','purchase_url','youtube_id','image_credit','image_publishable','image_verified','image_url','thumbnail_url','age_min','age_max','organizer','accessibility','contact_phone','content_source_url','ticket_status'];
  const same=(a,b)=>JSON.stringify(a??null)===JSON.stringify(b??null);
  function merge(base={},payload={}){
    const out={...base,...payload};
    if(payload.overlay_version===2){
      const locked=new Set(payload.locked_fields||[]);
      for(const key of fields)if(!locked.has(key)){
        if(Object.prototype.hasOwnProperty.call(base,key))out[key]=base[key];else delete out[key];
      }
    }
    if(payload.description_manual_override===true){
      const text=out.long_description||'';
      out.description=text;out.series_description=text;out.editorial_description=text;
    }
    if(payload.image_manual_override===true&&payload.image_data_url){
      out.image_url=payload.image_data_url;out.thumbnail_url=payload.image_data_url;
      out.thumbnail_ready=true;
    }
    return out;
  }
  function patch(values,baseline,previous={}){
    const locked=new Set(previous.overlay_version===2?previous.locked_fields||[]:fields.filter(k=>Object.prototype.hasOwnProperty.call(previous,k)));
    for(const key of fields)if(!same(values[key],baseline[key]))locked.add(key);
    const out={...previous,...values,overlay_version:2,locked_fields:[...locked]};
    out.category_manual_override=locked.has('category');out.subcategory_manual_override=locked.has('subcategory');
    out.description_manual_override=locked.has('long_description');
    out.image_manual_override=previous.image_manual_override===true||Boolean(values.image_data_url);
    if(out.image_manual_override)for(const key of ['image_url','thumbnail_url','image_credit','image_verified','image_publishable'])if(!out.locked_fields.includes(key))out.locked_fields.push(key);
    return out;
  }
  function visible(e){return Boolean(e)&&!["hidden","draft","archived","trashed","deleted","cancelled","canceled"].includes(e.status)&&!["draft","unpublished","hidden","archived"].includes(e.publication_status)&&e.is_active!==false;}
  const api={fields,merge,patch,visible};root.ISNET_EVENT_OVERLAY=api;
  if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof window==='object'?window:globalThis);
/* Shared event identity and media safety: no fuzzy matching, no guessed times. */
(function(root){'use strict';
const norm=s=>String(s||'').replace(/&#(?:0*39|x0*27);|&apos;/gi,"'").replace(/&amp;/gi,'&').normalize('NFKC').toLowerCase().replace(/[\u0591-\u05c7]/g,'').replace(/["'״׳]/g,'').replace(/[^\p{L}\p{N}]+/gu,' ').trim().replace(/\s+/g,' ');
const BAD=/^data:(?!image\/(?:png|jpeg|webp);base64,)|^blob:|placeholder|no_pic|no-pic|favicon|artistshadow|eventnew\.jpg|microsoft_oauth_logo|spacer\.|blank\./i;
const illustration=u=>/\/illustrations\/|\/defaults\//i.test(String(u||''));
let mediaRegistry={},factRegistry={};
function sourceKey(value){try{const u=new URL(value);if(!/^https?:$/.test(u.protocol))return '';u.hash='';for(const k of [...u.searchParams.keys()])if(/^(utm_|fbclid|gclid)/.test(k))u.searchParams.delete(k);if(u.pathname==='/'||/\/(?:events|calendar|tickets-culture)\/?$/.test(u.pathname)&&!u.search)return '';return decodeURIComponent(u.hostname.toLowerCase()+u.pathname.replace(/\/+$/,'')+u.search).toLowerCase()}catch{return ''}}
function titleKey(e){return norm(e.title).replace(/^סינדרלה מחזמר חנוכה עם נעמה סופר על$/,'סינדרלה').replace(/^פאטמה הסטנדאפיסטית הבדואית$/,'פאטמה הסטנדאפיסטית').replace(/^מרתון סטנדאפ יום רביעי חגיגה פאצו בר$/,'מרתון סטנדאפ יום רביעי חגיגה').replace(/\s+(?:במופע סטנדאפ|במופע סטנד אפ|מופע סטנדאפ|סטנדאפ|סטנד אפ)$/,'').replace(/\s+(?:התיאטרון העברי|תיאטרון בית ליסין|תיאטרון הקאמרי|חנוכה 2026)$/,'').trim()}
function venueKey(e){const room=String(e.venue||'').match(/(?:אולם|חדר)\s*([1-9]\d*)/);const v=norm(e.venue||e.venue_name||'').replace(/(?:אולם|חדר)\s*\d+/g,'').replace(/^(?:אולם|אודיטוריום)\s+/,'');let key=e.venue_institution_id;
if(!key){for(const [re,id] of [[/שיכוני המזרח|השדרה 50/,'rishon_shikunei'],[/(?:friends|mofet|מופת).*ראשון/,'rishon_friends'],[/פלשתים/,'philisti-museum'],[/מאירהוף/,'ashdod_city_library'],[/היכל.*(?:מאיר ניצן|ראשון)|מאיר ניצן.*היכל/,'htrl'],[/דיונה/,'ironit_diyona'],[/מונארט/,'ironit_monart'],[/משכן.*אשדוד/,'mishkan_ashdod'],[/תיאטרון חולון/,'holon-theatre'],[/שטיינברג/,'holon-steinberg'],[/הוט סינמה|dream stage/,'hot-cinema'],[/סינמטק יבנה/,'yavne-cinema']])if(re.test(v)){key=id;break}}
return String(key||v.replace(/אשדוד|ראשון לציון|הרצליה|חולון|יבנה|קרית גת|קריית גת/g,'').replace(/\b(?:אולם|מופעים)\b/g,'').trim())+(room?':room'+room[1]:'')}
function groupKey(e){return (e.series_id?'series:'+e.series_id:'title:'+titleKey(e))+'|venue:'+venueKey(e)}
function sameProduction(a,b){return titleKey(a)===titleKey(b)&&venueKey(a)===venueKey(b)}
function safeImage(e){return Boolean(e&&e.image_url&&!BAD.test(e.image_url)&&e.image_verified===true&&e.image_publishable===true&&e.source_image_kind!=='source_placeholder'&&(e.image_represents_event!==false||e.source_image_kind==='illustration'))}
function sanitize(e){let out={...e};const fact=factRegistry[e.event_id];if(fact&&!e.human_manual_override&&Object.entries(fact.match).every(([k,v])=>e[k]===v)&&!Object.keys(fact.fields).some(k=>(e.locked_fields||[]).includes(k)||e[k+'_manual_override']))out={...out,...fact.fields,_verified_fact_repair:fact.source_url};delete out.duplicate_of;delete out._duplicate_ids;const repair=mediaRegistry[sourceKey(out.content_source_url||out.detail_source_url||out.source_url)];if(repair&&(!safeImage(out)||illustration(out.image_url))&&norm(repair.title)===norm(e.title)&&!e.image_manual_override&&!(e.locked_fields||[]).includes('image_url'))out={...out,...repair.fields};
if(BAD.test(String(out.image_url||''))){out.image_url=null;out.thumbnail_url=null;out.thumbnail_ready=false;out.image_verified=false;out.image_publishable=false;out.image_represents_event=false;out.source_image_kind='source_placeholder';}
if(BAD.test(String(out.thumbnail_url||''))){out.thumbnail_url=null;out.thumbnail_ready=false}
if(illustration(out.image_url)){out.image_represents_event=false;out.source_image_kind='illustration';out.image_credit='תמונת המחשה — לא צילום מהאירוע';}
if(out.image_represents_event===false&&out.source_image_kind!=='illustration'){out.thumbnail_url=null;out.thumbnail_ready=false}
return out}
function sameOccurrence(a,b){if(!a.start_date||!a.start_time||a.start_date!==b.start_date||a.start_time!==b.start_time)return false;const av=venueKey(a),bv=venueKey(b),sameVenue=av&&bv&&(av===bv||(av.split(':room')[0]===bv.split(':room')[0]&&(!av.includes(':room')||!bv.includes(':room'))));const sameSource=sourceKey(a.content_source_url||a.detail_source_url)&&sourceKey(a.content_source_url||a.detail_source_url)===sourceKey(b.content_source_url||b.detail_source_url);if(!sameVenue&&!((!av||!bv)&&sameSource))return false;if(titleKey(a)&&titleKey(a)===titleKey(b))return true;const u=sourceKey(a.content_source_url||a.detail_source_url),v=sourceKey(b.content_source_url||b.detail_source_url);return Boolean(u&&u===v&&norm(a.title)===norm(b.title))}
function score(e){return (e.source_content_authoritative?100:0)+(e.image_manual_override?50:0)+(e.description_manual_override?30:0)+(safeImage(e)&&!illustration(e.image_url)?20:0)+(e.purchase_url?5:0)+(e.description?2:0)-(Number(e.source_priority)||10)/100}
function reconcile(input,options={}){const unique=new Map;for(const raw of input||[]){const e=sanitize(raw),id=e.event_id||e.id,prev=unique.get(id);if(prev){if(!sameOccurrence(prev,e))throw Error('Conflicting event ID: '+id);if(score(e)>score(prev))unique.set(id,e)}else unique.set(id,e)}const all=[...unique.values()],groups=[],slots=new Map;
for(const e of all){const slot=String(e.start_date)+'|'+String(e.start_time||e.event_id||e.id),peers=slots.get(slot)||[];const g=peers.find(g=>{const known=g.filter(x=>venueKey(x));return venueKey(e)&&known.length?known.every(x=>sameOccurrence(x,e)):g.some(x=>sameOccurrence(x,e))});if(g)g.push(e);else{const fresh=[e];groups.push(fresh);peers.push(fresh);slots.set(slot,peers)}}
const canonical=new Map();for(const g of groups){g.sort((a,b)=>Number(Boolean(venueKey(b)))-Number(Boolean(venueKey(a)))||Number(venueKey(b).includes(':room'))-Number(venueKey(a).includes(':room'))||score(b)-score(a)||String(a.event_id||a.id).localeCompare(String(b.event_id||b.id)));const first=g[0],id=first.event_id||first.id;
for(const e of g)canonical.set(e.event_id||e.id,{...e,...(e!==first?{duplicate_of:id}:{}),_integrity_group_key:groupKey(first)});
if(g.length>1){const memberships=new Map;for(const e of g)for(const m of [{category:e.category,subcategory:e.subcategory},...(e.category_memberships||[])])if(m.category)memberships.set(m.category+'|'+(m.subcategory||''),m);canonical.set(id,{...canonical.get(id),category_memberships:[...memberships.values()],audiences:[...new Set(g.flatMap(e=>e.audiences||[]))],_image_alternatives:[...new Set(g.filter(e=>safeImage(e)&&!illustration(e.image_url)).flatMap(e=>[e.thumbnail_ready&&e.thumbnail_url,e.image_url]).filter(Boolean))],source_aliases:[...(first.source_aliases||[]),...g.slice(1).map(e=>({event_id:e.event_id||e.id,title:e.title,url:e.purchase_url||e.ticket_url}))],_duplicate_ids:g.slice(1).map(e=>e.event_id||e.id)})}}
return all.map(e=>canonical.get(e.event_id||e.id)).filter(e=>options.keepDuplicates||!e.duplicate_of)}
function resolve(events,id){const all=reconcile(events,{keepDuplicates:true}),found=all.find(e=>(e.event_id||e.id)===id||(e.source_aliases||[]).some(a=>a.event_id===id));return found?.duplicate_of?all.find(e=>(e.event_id||e.id)===found.duplicate_of):found}
const matchesCategory=(e,ids)=>ids.has(e.category)||(e.category_memberships||[]).some(m=>ids.has(m.category));
function imageError(img){let urls=[];try{urls=JSON.parse(img.dataset.mediaAlternatives||'[]')}catch{}const next=urls.find(u=>u&&u!==img.getAttribute('src')&&!BAD.test(u));if(next){img.dataset.mediaAlternatives=JSON.stringify(urls.slice(urls.indexOf(next)+1));img.src=next;return}const fallback=img.ownerDocument.createElement('div');fallback.className='image placeholder fallback';fallback.textContent='תמונה אינה זמינה';img.replaceWith(fallback)}
const api={imageError,setFactRegistry:r=>{factRegistry=r||{}},matchesCategory,norm,sourceKey,titleKey,venueKey,groupKey,sameProduction,sameOccurrence,safeImage,sanitize,reconcile,resolve,setMediaRegistry:r=>{mediaRegistry=Object.fromEntries(Object.entries(r||{}).map(([k,v])=>[sourceKey(k),v]))}};root.ISNET_EVENT_IDENTITIES=api;api.ready=root.document&&typeof fetch==='function'?fetch(new URL('data/event-quality-media.json',root.document.currentScript.src),{cache:'no-cache',signal:typeof AbortSignal!=='undefined'&&AbortSignal.timeout?AbortSignal.timeout(10000):undefined}).then(r=>r.ok?r.json():{}).then(r=>{api.setMediaRegistry(r.repairs);api.setFactRegistry(r.fact_repairs)}).catch(()=>{}):Promise.resolve();if(typeof module==='object'&&module.exports)module.exports.integrity=api;
})(typeof window==='object'?window:globalThis);
