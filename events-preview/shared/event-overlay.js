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
// Reviewed aliases: https://www.teatron.org.il/shows/עופרה/ (14.11.2026, 21:00, Ashdod).
const ofraAliases=new Set(['עפרה','עופרה','עפרה המחזמר על עופרה חזה','עפרה המחזמר על עפרה חזה','עופרה המחזמר על עופרה חזה','עופרה המחזמר על עפרה חזה','עפרה מחזמר התיאטרון העברי','עפרה תיאטרון העברי','עפרה מחזמר מרהיב על עפרה חזה','עפרה מחזמר מרהיב על עופרה חזה']);
// Only source metadata is removed. Cast, adaptations, sequels and meaningful subtitles stay intact.
function theatreTitle(value){
 let title=norm(value).replace(/תאטרון/g,'תיאטרון');
 let previous;
 do{previous=title;title=title.replace(/\s+(?:עונת (?:ה)?מנויים|סדרת (?:ה)?מנויים)(?:\s+\d{2,4}){0,2}$/,'').replace(/\s+(?:(?:תיאטרון|התיאטרון|ת)\s+(?:הקאמרי|קאמרי|בית ליסין|באר שבע|הבימה|חיפה|העברי)|בית ליסין)$/,'').trim()}while(title!==previous);
 return title||norm(value);
}
function baseTitleKey(e){if(e.category==='theatre'&&ofraAliases.has(norm(e.title)))return 'production:ofra-hebrew-theatre';return (e.category==='theatre'?theatreTitle(e.title):norm(e.title)).replace(/\s+לוח הופעות והזמנת כרטיסים$/,'').replace(/^סינדרלה מחזמר חנוכה עם נעמה סופר על$/,'סינדרלה').replace(/^פאטמה הסטנדאפיסטית הבדואית$/,'פאטמה הסטנדאפיסטית').replace(/^מרתון סטנדאפ יום רביעי חגיגה פאצו בר$/,'מרתון סטנדאפ יום רביעי חגיגה').replace(/\s+(?:במופע סטנדאפ|במופע סטנד אפ|מופע סטנדאפ|סטנדאפ|סטנד אפ)(?: חדש)?$/,'').replace(/\s+(?:התיאטרון העברי|תיאטרון בית ליסין|תיאטרון הקאמרי|חנוכה 2026)$/,'').trim()}
// Exact reviewed alternatives only. These never strip a cast name or guess from image similarity.
const reviewedProductions=[
 // Official Mishkan booking confirms 7 Dec 2026, 17:30. The second title only
 // repeats the venue after a separator; preserve both source IDs and offers.
 {id:'hipazon-sipur-hanes-2026',titles:['משכן אומנויות הבמה אשדוד - סיפור הנס חיפזון וזהירון חנוכה','משכן אומנויות הבמה אשדוד - סיפור הנס חיפזון וזהירון חנוכה | המשכן לאמנויות הבמה אשדוד'],source:'https://mishkan-ashdod.smarticket.co.il/סיפור_הנס/?id=8223'},
 {id:'dragon-keepers-2026',titles:['שומרי הדרקונים - חנוכה 2026','שומרי הדרקונים - מחזמר הרפתקאות - חנוכה 2026'],source:'https://sababa.events/he/event/khraniteli-drakonov-priklyuchencheskiy-myuzikl-khanuka-2026/ashdod/'},
 {id:'daniel-styopin-standup',titles:['דניאל סטיופין ("קופה ראשית") - מופע סטנדאפ','דניאל סטיופין במופע סטנדאפ'],source:'https://tickets.mevalim.co.il/event/XWqbBU_QbiHlpJ6'},
 {id:'imi-generalit-musical',titles:['אמי הגנרלית - התיאטרון העברי','אמי הגנרלית - מחזמר','אמי הגנרלית - המחזמר'],source:'https://www.teatron.org.il/shows/אמי-הגנרלית-מחזמר/'},
 {id:'fiddler-hebrew-theatre',titles:['כנר על הגג - התיאטרון העברי','כנר על הגג - מחזמר תיאטרון העברי'],source:'https://www.teatron.org.il/shows/כנר-על-הגג-המחזמר/'},
 {id:'voca-people-20',titles:['VOCA PEOPLE ווקה פיפל','voca people - ווקה פיפל - הסנסציה הבינלאומית חוגגת 20'],source:'https://htrl.co.il/show/voca-people-ווקה-פיפל/'},
 {id:'yonatan-gruber-ze-ma-yesh',titles:['יונתן גרובר - זה מה יש','יונתן גרובר - סטנדאפ'],source:'https://www.heichalbair.co.il/יונתן_גרובר_-_סטנדאפ/?id=3139'},
 // Both official listings identify the same Ashdod performance (12 Nov 2026, 20:30, Mishkan).
 {id:'nova-andalusian-ashdod-2026',titles:['נוּבָּה חדשה','נוֹבָּה חדשה - הדור הבא של המוזיקה האנדלוסית'],source:'https://tickets.mevalim.co.il/event/u7D6qOMHCmG7pOx'}
];
// Editorially verified aliases: same production, exact original city/venue/date/time in primary show boards.
// The occurrence matcher still requires identical date, time and venue; source IDs and offers are retained.
reviewedProductions.push(
 {id:'dragon-keepers-2026',titles:['שומרי הדרקונים'],source:'https://friends-hist.co.il/show/שומרי-הדרקונים/'}, // Ashdod 2026-11-29 18:30
 {id:'high-school-drama-2026',titles:['היי סקול דרמה - האקדמיה למדעי היוטיוב - חנוכה 2026','היי סקול דרמה – האקדמיה למדעי היוטיוב – חנוכה 2026 – משפחת טרסוב'],source:'https://friends-hist.co.il/show/היי-סקול-דרמה-האקדמיה-למדעי-היוטיוב-ח/'}, // Ashdod 2026-12-16 17:30
 {id:'nuclear-marriage-comedy-2026',titles:['נישואים גרעיניים','נישואים גרעיניים - קומדיה זוגית פרועה','נישואים גרעיניים - הצגת הבידור שתחסוך לכם טיפול זוגי'],source:'https://friends-hist.co.il/show/נישואים-גרעיניים/'}, // Ashdod 2026-12-19 21:00
 {id:'imi-generalit-musical',titles:['אמי הגנרלית – המחזמר! – התיאטרון העברי'],source:'https://friends-hist.co.il/show/אימי-הגנרלית-המחזמר/'}, // Ashdod 2027-01-16 21:00
 {id:'roni-sasson-comedy-bar',titles:['רוני ששון במופע סטנדאפ','רוני ששון במופע סטנד אפ – קומדי בר'],source:'https://friends-hist.co.il/show/רוני-ששון-במופע-סטנד-אפ-קומדי-בר/'}, // Rishon 2026-11-06 22:00
 {id:'daniel-cohen-comedy-bar',titles:['דניאל כהן במופע סטנדאפ','דניאל כהן במופע סטנד אפ – קומדי בר'],source:'https://friends-hist.co.il/show/דניאל-כהן-במופע-סטנד-אפ/'}, // Rishon 2026-11-20 22:00
 {id:'nova-andalusian-rishon-2026',titles:['נובה חדשה התזמורת האנדלוסית','נובה חדשה – התזמורת האנדלוסית אשדוד'],source:'https://friends-hist.co.il/show/נובה-חדשה-התזמורת-האנדלוסית-אשדוד/'} // Rishon 2026-11-22 20:30
);
// FRIENDS, the official Mishkan board and the linked booking listing were read on 12 Nov 2026.
// Exact same production/cast at Mishkan Ashdod, 26 Dec 2026 21:00; retain both booking IDs.
reviewedProductions.push({id:'toc-toc-tomix-2026',titles:['טוק טוק – קומדיה אובססיבית','טוק טוק – קומדיה אובססיבית – Toc-toc'],source:'https://friends-hist.co.il/show/טוק-טוק-קומדיה-אובססיבית/'});
const reviewedTitleKeys=new Map(reviewedProductions.flatMap(p=>p.titles.map(t=>[norm(t),'production:'+p.id])));
function titleKey(e){return ['theatre','music','kids','standup'].includes(e.category)&&reviewedTitleKeys.get(norm(e.title))||baseTitleKey(e)}
function venueKey(e){const room=String(e.venue||'').match(/(?:אולם|חדר)\s*([1-9]\d*)/);const v=norm(e.venue||e.venue_name||'').replace(/(?:אולם|חדר)\s*\d+/g,'').replace(/^(?:אולם|אודיטוריום)\s+/,'');let key=e.venue_institution_id;
if(!key){for(const [re,id] of [[/שיכוני המזרח|השדרה 50/,'rishon_shikunei'],[/(?:friends|mofet|מופת).*ראשון/,'rishon_friends'],[/פלשתים/,'philisti-museum'],[/מאירהוף/,'ashdod_city_library'],[/היכל.*(?:מאיר ניצן|ראשון)|מאיר ניצן.*היכל/,'htrl'],[/דיונה/,'ironit_diyona'],[/מונארט/,'ironit_monart'],[/משכן.*אשדוד/,'mishkan_ashdod'],[/תיאטרון חולון/,'holon-theatre'],[/שטיינברג/,'holon-steinberg'],[/הוט סינמה|dream stage/,'hot-cinema'],[/סינמטק יבנה/,'yavne-cinema']])if(re.test(v)){key=id;break}}
return String(key||v.replace(/אשדוד|ראשון לציון|הרצליה|חולון|יבנה|קרית גת|קריית גת/g,'').replace(/\b(?:אולם|מופעים)\b/g,'').trim())+(room?':room'+room[1]:'')}
function groupKey(e){return (e.series_id&&e.category!=='theatre'&&!titleKey(e).startsWith('production:')?'series:'+e.series_id:'title:'+titleKey(e))+'|venue:'+venueKey(e)}
function sameProduction(a,b){return titleKey(a)===titleKey(b)&&venueKey(a)===venueKey(b)}
function safeImage(e){return Boolean(e&&e.image_url&&!BAD.test(e.image_url)&&e.image_verified===true&&e.image_publishable===true&&e.source_image_kind!=='source_placeholder'&&(e.image_represents_event!==false||e.source_image_kind==='illustration'))}
function sanitize(e){let out={...e};const fact=factRegistry[e.event_id];if(fact&&!e.human_manual_override&&Object.entries(fact.match).every(([k,v])=>e[k]===v)&&!Object.keys(fact.fields).some(k=>(e.locked_fields||[]).includes(k)||e[k+'_manual_override']))out={...out,...fact.fields,_verified_fact_repair:fact.source_url};delete out.duplicate_of;delete out._duplicate_ids;const repair=mediaRegistry[sourceKey(out.content_source_url||out.detail_source_url||out.source_url)];if(repair&&(!safeImage(out)||illustration(out.image_url))&&norm(repair.title)===norm(e.title)&&!e.image_manual_override&&!(e.locked_fields||[]).includes('image_url'))out={...out,...repair.fields};
if(BAD.test(String(out.image_url||''))){out.image_url=null;out.thumbnail_url=null;out.thumbnail_ready=false;out.image_verified=false;out.image_publishable=false;out.image_represents_event=false;out.source_image_kind='source_placeholder';}
if(BAD.test(String(out.thumbnail_url||''))){out.thumbnail_url=null;out.thumbnail_ready=false}
if(illustration(out.image_url)){out.image_represents_event=false;out.source_image_kind='illustration';out.image_credit='תמונת המחשה — לא צילום מהאירוע';}
if(out.image_represents_event===false&&out.source_image_kind!=='illustration'){out.thumbnail_url=null;out.thumbnail_ready=false}
return out}
function sameOccurrence(a,b){if(!a.start_date||!a.start_time||a.start_date!==b.start_date||a.start_time!==b.start_time)return false;const av=venueKey(a),bv=venueKey(b),sameVenue=av&&bv&&(av===bv||(av.split(':room')[0]===bv.split(':room')[0]&&(!av.includes(':room')||!bv.includes(':room'))));const sameSource=sourceKey(a.content_source_url||a.detail_source_url)&&sourceKey(a.content_source_url||a.detail_source_url)===sourceKey(b.content_source_url||b.detail_source_url);if(!sameVenue&&!((!av||!bv)&&sameSource))return false;if(titleKey(a)&&titleKey(a)===titleKey(b))return true;const u=sourceKey(a.content_source_url||a.detail_source_url),v=sourceKey(b.content_source_url||b.detail_source_url);return Boolean(u&&u===v&&norm(a.title)===norm(b.title))}
// A suspicion blocks publication for source review; it is never an automatic fuzzy merge.
function suspectedDuplicates(events){
 const slots=new Map(),pairs=[];
 for(const e of events.filter(e=>root.ISNET_EVENT_OVERLAY.visible(e)&&!e.duplicate_of&&e.start_date&&e.start_time&&venueKey(e)&&['theatre','music','standup','kids'].includes(e.category))){const k=e.start_date+'|'+e.start_time+'|'+venueKey(e);if(!slots.has(k))slots.set(k,[]);slots.get(k).push(e)}
 for(const group of slots.values())for(let i=0;i<group.length;i++)for(let j=i+1;j<group.length;j++){const a=group[i],b=group[j],x=baseTitleKey(a),y=baseTitleKey(b),short=x.length<y.length?x:y,long=x.length<y.length?y:x;if(titleKey(a)!==titleKey(b)&&(x===y||short.split(' ').length>=2&&long.startsWith(short+' ')))pairs.push([a,b])}
 return pairs;
}
function score(e){return (e.source_content_authoritative?100:0)+(e.image_manual_override?50:0)+(e.description_manual_override?30:0)+(safeImage(e)&&!illustration(e.image_url)?20:0)+(e.purchase_url?5:0)+(e.description?2:0)-(Number(e.source_priority)||10)/100}
function reconcile(input,options={}){const unique=new Map;for(const raw of input||[]){const e=sanitize(raw),id=e.event_id||e.id,prev=unique.get(id);if(prev){if(!sameOccurrence(prev,e))throw Error('Conflicting event ID: '+id);if(score(e)>score(prev))unique.set(id,e)}else unique.set(id,e)}const all=[...unique.values()],groups=[],slots=new Map;
for(const e of all){const slot=String(e.start_date)+'|'+String(e.start_time||e.event_id||e.id),peers=slots.get(slot)||[];const g=peers.find(g=>{const known=g.filter(x=>venueKey(x));return venueKey(e)&&known.length?known.every(x=>sameOccurrence(x,e)):g.some(x=>sameOccurrence(x,e))});if(g)g.push(e);else{const fresh=[e];groups.push(fresh);peers.push(fresh);slots.set(slot,peers)}}
const canonical=new Map();for(const g of groups){g.sort((a,b)=>Number(Boolean(venueKey(b)))-Number(Boolean(venueKey(a)))||Number(venueKey(b).includes(':room'))-Number(venueKey(a).includes(':room'))||score(b)-score(a)||String(a.event_id||a.id).localeCompare(String(b.event_id||b.id)));const first=g[0],id=first.event_id||first.id;
const approved={};for(const k of [...(root.ISNET_EVENT_OVERLAY?.fields||[]),'description','series_description','editorial_description','image_represents_event','source_image_kind']){const owner=g.find(x=>(x.locked_fields||[]).includes(k)||(x.description_manual_override&&['description','long_description','series_description','editorial_description','short_pitch'].includes(k))||(x.image_manual_override&&['image_url','thumbnail_url','image_credit','image_verified','image_publishable','image_represents_event','source_image_kind'].includes(k)));if(owner&&Object.prototype.hasOwnProperty.call(owner,k))approved[k]=owner[k]}
if(Object.keys(approved).length){approved.locked_fields=[...new Set(g.flatMap(e=>e.locked_fields||[]))];if(g.some(e=>e.image_manual_override))approved.image_manual_override=true;if(g.some(e=>e.description_manual_override))approved.description_manual_override=true}
for(const e of g)canonical.set(e.event_id||e.id,{...e,...(e!==first?{duplicate_of:id}:approved),_integrity_group_key:groupKey(first)});
if(g.length>1){const memberships=new Map;for(const e of g)for(const m of [{category:e.category,subcategory:e.subcategory},...(e.category_memberships||[])])if(m.category)memberships.set(m.category+'|'+(m.subcategory||''),m);canonical.set(id,{...canonical.get(id),category_memberships:[...memberships.values()],audiences:[...new Set(g.flatMap(e=>e.audiences||[]))],_image_alternatives:[...new Set(g.filter(e=>safeImage(e)&&!illustration(e.image_url)).flatMap(e=>[e.thumbnail_ready&&e.thumbnail_url,e.image_url]).filter(Boolean))],source_aliases:[...new Map([...g.flatMap(e=>e.source_aliases||[]),...g.slice(1).map(e=>({event_id:e.event_id||e.id,title:e.title,url:e.purchase_url||e.ticket_url}))].map(a=>[JSON.stringify(a),a])).values()],_duplicate_ids:g.slice(1).map(e=>e.event_id||e.id)})}}
return all.map(e=>canonical.get(e.event_id||e.id)).filter(e=>options.keepDuplicates||!e.duplicate_of)}
function resolve(events,id){const all=reconcile(events,{keepDuplicates:true}),found=all.find(e=>(e.event_id||e.id)===id||(e.source_aliases||[]).some(a=>a.event_id===id));return found?.duplicate_of?all.find(e=>(e.event_id||e.id)===found.duplicate_of):found}
const matchesCategory=(e,ids)=>ids.has(e.category)||(e.category_memberships||[]).some(m=>ids.has(m.category));
function imageError(img){let urls=[];try{urls=JSON.parse(img.dataset.mediaAlternatives||'[]')}catch{}const next=urls.find(u=>u&&u!==img.getAttribute('src')&&!BAD.test(u));if(next){img.dataset.mediaAlternatives=JSON.stringify(urls.slice(urls.indexOf(next)+1));img.src=next;return}const fallback=img.ownerDocument.createElement('div');fallback.className='image placeholder fallback';fallback.textContent='תמונה אינה זמינה';img.replaceWith(fallback)}
// Dynamic CMS reads must not bypass the build gate. Reject only the suspect overlays;
// leave the source records intact and expose the rejected IDs for operational review.
function guardPublishedOverlays(source,rows){
 const proposed=new Map(source.map(e=>[String(e.event_id||e.id),e]));
 for(const row of rows)if(proposed.has(String(row.event_id))||row.record_type==='manual')proposed.set(String(row.event_id),{...row.payload,event_id:row.event_id});
 const day=new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Jerusalem',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
 const suspects=suspectedDuplicates(reconcile([...proposed.values()]).filter(e=>(e.end_date||e.start_date||'')>=day));
 const ids=new Set(suspects.flatMap(pair=>pair.flatMap(e=>[e.event_id||e.id,...(e._duplicate_ids||[]),...(e.source_aliases||[]).map(a=>a.event_id)])));
 const blocked=rows.filter(r=>ids.has(r.event_id));
 if(blocked.length){api.rejectedOverlayIds=[...new Set([...(api.rejectedOverlayIds||[]),...blocked.map(r=>r.event_id)])];if(typeof console!=='undefined')console.warn('ISNET duplicate guard: withheld suspect CMS overlays for review',blocked.map(r=>r.event_id))}
 return blocked.length?rows.filter(r=>!ids.has(r.event_id)):rows;
}
const api={policyVersion:'20261102-production2',theatreTitle,suspectedDuplicates,guardPublishedOverlays,imageError,setFactRegistry:r=>{factRegistry=r||{}},matchesCategory,norm,sourceKey,titleKey,venueKey,groupKey,sameProduction,sameOccurrence,safeImage,sanitize,reconcile,resolve,setMediaRegistry:r=>{mediaRegistry=Object.fromEntries(Object.entries(r||{}).map(([k,v])=>[sourceKey(k),v]))}};root.ISNET_EVENT_IDENTITIES=api;api.ready=root.document&&typeof fetch==='function'?fetch(new URL('data/event-quality-media.json',root.document.currentScript.src),{cache:'no-cache',signal:typeof AbortSignal!=='undefined'&&AbortSignal.timeout?AbortSignal.timeout(10000):undefined}).then(r=>r.ok?r.json():{}).then(r=>{api.setMediaRegistry(r.repairs);api.setFactRegistry(r.fact_repairs)}).catch(()=>{}):Promise.resolve();if(typeof module==='object'&&module.exports)module.exports.integrity=api;
})(typeof window==='object'?window:globalThis);
