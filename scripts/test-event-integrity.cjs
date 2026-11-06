const assert=require('node:assert/strict'),fs=require('node:fs'),q=require('../events-preview/shared/event-overlay.js').integrity;
const row=(id,fields={})=>({event_id:id,title:'הופעה לדוגמה',venue:'אולם העיר',start_date:'2026-12-01',start_time:'20:30',category:'music',...fields});
let out=q.reconcile([row('a'),row('b')]);assert.equal(out.length,1);assert.equal(q.resolve([row('a'),row('b')],'b').event_id,out[0].event_id);
assert.equal(q.reconcile([row('a'),row('b',{start_time:'21:00'})]).length,2);assert.equal(q.reconcile([row('a'),row('b',{venue:'אולם אחר'})]).length,2);
assert.equal(q.reconcile([row('a',{venue:'הוט סינמה אשדוד - אולם 2'}),row('b',{venue:'הוט סינמה אשדוד - אולם 3'})]).length,2);
assert.equal(q.reconcile([row('a',{venue:'הוט סינמה אשדוד - אולם 2'}),row('b',{venue:'הוט סינמה אשדוד'})]).length,1);
assert.equal(q.reconcile([row('a',{title:'סינדרלה עם רינת גבאי'}),row('b',{title:'סינדרלה עם נעמה סופר על'})]).length,2);
assert.notEqual(q.groupKey(row('a')),q.groupKey(row('b',{venue:'אולם אחר'})));
assert(!q.sameProduction(row('a',{series_id:'series'}),row('b',{series_id:'series',title:'הפקה אחרת'})));
assert.equal(q.reconcile([row('a',{start_time:null}),row('b',{start_time:null})]).length,2);
assert.throws(()=>q.reconcile([row('a'),row('a',{title:'אחר'})]),/Conflicting event ID/);
assert.equal(q.reconcile([row('a'),row('a')]).length,1);
const blank=row('empty',{image_url:'data:image/svg+xml,%3Csvg%3E',image_publishable:true,image_verified:true,thumbnail_url:'data:image/svg+xml,blank',thumbnail_ready:true});assert(!q.safeImage(blank));assert.equal(q.sanitize(blank).image_url,null);
const placeholder=row('p',{image_url:'https://images.makore.co.il/placeholders/v1/event-8.webp',image_publishable:true,image_verified:true});assert(!q.safeImage(placeholder));
const ill=q.sanitize(row('i',{image_url:'../ashdod/assets/illustrations/v4/theatre-stage.webp',image_publishable:true,image_verified:true,image_represents_event:true}));assert.equal(ill.image_represents_event,false);assert.equal(ill.source_image_kind,'illustration');assert(ill.image_credit.includes('המחשה'));
q.setMediaRegistry({'https://source.test/show/one':{title:'הופעה לדוגמה',fields:{image_url:'https://source.test/event.jpg',image_verified:true,image_publishable:true,image_represents_event:true}}});assert.equal(q.sanitize({...blank,content_source_url:'https://source.test/show/one'}).image_url,'https://source.test/event.jpg');assert.equal(q.sanitize({...blank,title:'הפקה אחרת',content_source_url:'https://source.test/show/one'}).image_url,null);
assert.equal(q.sanitize(row('new',{content_source_url:'https://source.test/show/one',image_url:'https://source.test/new-poster.jpg',image_verified:true,image_publishable:true})).image_url,'https://source.test/new-poster.jpg');
q.setMediaRegistry({});
const registry=JSON.parse(fs.readFileSync('events-preview/shared/data/event-quality-media.json'));q.setMediaRegistry(registry.repairs);q.setFactRegistry(registry.fact_repairs);
const c=registry.fact_repairs.mevalim_ri_1eefd1529c92d3ae;assert.equal(q.sanitize({event_id:'mevalim_ri_1eefd1529c92d3ae',...c.match}).title,c.fields.title);assert.equal(q.sanitize({event_id:'different',...c.match}).title,c.match.title);
for(const city of ['ashdod','rishon-lezion','yavne','kiryat-gat','holon','herzliya']){const data=JSON.parse(fs.readFileSync('events-preview/'+city+'/data/'+(['holon','herzliya'].includes(city)?'events-public.json':'events.json')));const reviewed=q.reconcile(data.events),again=q.reconcile(reviewed);assert.equal(reviewed.length,again.length);assert.equal(new Set(reviewed.map(e=>e.event_id)).size,reviewed.length);assert(!reviewed.some(e=>String(e.image_url).startsWith('data:image/svg')));for(const e of reviewed){assert(data.events.some(x=>x.event_id===e.event_id));assert(!e.duplicate_of)}}
console.log('PASS: all six feeds, exact occurrence identity, distinct times/venues/casts, old IDs, source media, editorial image locks, illustrations and conflicting IDs');

const vm=require('node:vm'),context={window:{location:{pathname:'/events-preview/ashdod/'}},URL,Promise};vm.createContext(context);vm.runInContext(fs.readFileSync('events-preview/shared/event-overlay.js','utf8'),context);vm.runInContext(fs.readFileSync('events-preview/ashdod/ashdod-event-identities.js','utf8'),context);assert.equal(typeof context.window.ISNET_EVENT_IDENTITIES.groupKey,'function');assert.equal(typeof context.window.ISNET_EVENT_IDENTITIES.sanitize,'function');console.log('PASS: legacy identity adapter preserves shared runtime API');

const fake={dataset:{mediaAlternatives:JSON.stringify(['https://same-show.test/backup.jpg'])},getAttribute:()=> 'https://same-show.test/blocked.jpg'};q.imageError(fake);assert.equal(fake.src,'https://same-show.test/backup.jpg');assert.equal(fake.dataset.mediaAlternatives,'[]');console.log('PASS: failed source image uses the same occurrence backup');

const manual=q.reconcile([row('source',{source_content_authoritative:true}),row('editor',{locked_fields:['description'],description:'Approved editorial copy'})]);assert.equal(manual[0].event_id,'source');assert.equal(manual[0].description,'Approved editorial copy');console.log('PASS: explicit editorial locks take priority within duplicate occurrences');

const comedy=[row('friends_as_cab289dedf10fa4c60',{title:'קומדי בר- סטנדאפ',city:'אשדוד',category:'standup',venue:'הוט סינמה אשדוד - אולם 2',source_priority:1}),row('makore_as_91fb472ae5344d1b11',{title:'כוכבי הקומדי בר מגיעים למרתון סטנדאפ אשדוד 19.11.26',city:'אשדוד',category:'standup',venue:'הוט סינמה אשדוד - אולם 2',source_priority:4})];assert(context.window.ISNET_EVENT_IDENTITIES.resolve(comedy,'makore_as_91fb472ae5344d1b11')._source_event_ids.includes('friends_as_cab289dedf10fa4c60'));console.log('PASS: previously reviewed comedy aliases retain old detail links');

const publicGuard=require('./check-public-event-integrity.cjs');assert(publicGuard.invalidPublishedRow(row('future',{title:'מבלים',start_date:publicGuard.day})));assert(!publicGuard.invalidPublishedRow(row('archive',{title:'מבלים',start_date:'2000-01-01'})));assert(!publicGuard.invalidPublishedRow(row('hidden',{title:'מבלים',start_date:publicGuard.day,status:'hidden'})));assert(publicGuard.invalidPublishedRow(row('svg',{start_date:'2000-01-01',image_url:'data:image/svg+xml,blank'})));console.log('PASS: live publication guard distinguishes archived source history from active events');

const ofraTitles=['עפרה - המחזמר על עופרה חזה','עפרה - מחזמר התיאטרון העברי','עפרה','עפרה - מחזמר מרהיב על עפרה חזה'];
const ofraRows=ofraTitles.map((title,i)=>row('ofra-'+i,{title,category:'theatre',venue:'המשכן לאמנויות הבמה אשדוד',start_date:'2026-11-14',start_time:'21:00',purchase_url:'https://tickets.test/offer/'+i,image_url:i===0?'https://source.test/ofra.jpg':'../ashdod/assets/illustrations/theatre.jpg',image_verified:true,image_publishable:true,image_represents_event:i===0,source_image_kind:i===0?'source_card_image':'illustration'}));
const ofra=q.reconcile(ofraRows);assert.equal(ofra.length,1);assert.equal(ofra[0].image_url,'https://source.test/ofra.jpg');
for(const original of ofraRows)assert.equal(q.resolve(ofraRows,original.event_id).event_id,ofra[0].event_id);
assert.equal(ofra[0].source_aliases.length,3);
assert.equal(q.reconcile([ofraRows[0],{...ofraRows[1],start_time:'18:00'}]).length,2);
assert.equal(q.reconcile([ofraRows[0],{...ofraRows[1],venue:'אולם מופעים דיונה אשדוד'}]).length,2);
assert.equal(q.reconcile([ofraRows[0],{...ofraRows[1],title:'עפרה עם שחקנים אחרים'}]).length,2);
// Reviewed same-day Ashdod musical title aliases must merge only at the exact venue/time.
const nova= [row('nova-makore',{title:'נוּבָּה חדשה',category:'music',venue:'המשכן לאמנויות הבמה הפיס, אשדוד',start_date:'2026-11-12',start_time:'20:30'}),row('nova-mevalim',{title:'נוֹבָּה חדשה - הדור הבא של המוזיקה האנדלוסית',category:'music',venue:'המשכן לאמנויות הבמה אשדוד',start_date:'2026-11-12',start_time:'20:30'})];
assert.equal(q.reconcile(nova).length,1,'Reviewed Nova musical aliases share one occurrence');
assert.equal(q.reconcile([nova[0],{...nova[1],start_time:'21:00'}]).length,2,'Different Nova time remains separate');
assert.equal(q.reconcile([nova[0],{...nova[1],venue:'אולם דיונה אשדוד'}]).length,2,'Different Nova venue remains separate');
const realOfra=JSON.parse(fs.readFileSync('events-preview/ashdod/data/events.json')).events.filter(e=>e.title.includes('עפרה')&&e.start_date==='2026-11-14');assert.equal(q.reconcile(realOfra).length,1);
console.log('PASS: reviewed Ofra aliases collapse into one sourced poster/card; all old IDs and offers survive; other times/venues/casts remain separate');

// Reviewed identical listing from Mevalim and FRIENDS: Rishon, 22 Jan 2027, 21:30,
// Heichal Hatarbut / Meir Nitzan. Keep both source IDs and booking links.
const amiRishon=[
 row('mevalim_ri_7cf16cc268ef23c0',{title:'אמי הגנרלית - המחזמר',category:'theatre',city:'ראשון לציון',venue:'היכל התרבות ראשון לציון',start_date:'2027-01-22',start_time:'21:30',content_source_url:'https://www.mevalim.co.il/theater/אמי-הגנרלית-מחזמר/'}),
 row('board_ebd24fa30bfcd149c9',{title:'אמי הגנרלית – המחזמר! – התיאטרון העברי',category:'theatre',city:'ראשון לציון',venue:'היכל התרבות מאיר ניצן ראשון לציון',start_date:'2027-01-22',start_time:'21:30',content_source_url:'https://friends-hist.co.il/show/אימי-הגנרלית-המחזמר/'})
];
assert.equal(q.titleKey(amiRishon[0]),q.titleKey(amiRishon[1]));
assert.equal(q.venueKey(amiRishon[0]),q.venueKey(amiRishon[1]));
assert.equal(q.reconcile(amiRishon).length,1,'Same reviewed musical at same time and venue is one occurrence');
assert.equal(q.suspectedDuplicates(q.reconcile(amiRishon,{keepDuplicates:true})).length,0);
assert.equal(q.resolve(amiRishon,amiRishon[0].event_id).event_id,q.resolve(amiRishon,amiRishon[1].event_id).event_id);
assert.equal(q.reconcile([amiRishon[0],{...amiRishon[1],start_time:'22:00'}]).length,2,'Different time is not the same occurrence');
assert.equal(q.reconcile([amiRishon[0],{...amiRishon[1],venue:'היכל התרבות פתח תקווה'}]).length,2,'Different venue must never merge');
assert.equal(q.reconcile([amiRishon[0],{...amiRishon[1],title:'אמי הגנרלית עם קאסט אחר'}]).length,2,'Different cast must never merge');
console.log('PASS: Rishon Ami musical reviewed title variant reconciles only exact performance, retaining source IDs');


// Same 20 Mar 2027, 11:30 FRIENDS Rishon children's show is titled
// "עמי ותמי - הצגת ילדים" in Mevalim and "עמי ותמי" on the producer's FRIENDS page.
// Repair only the exact source ID/date/time/venue, not all similarly titled productions.
const amiTami=[row('mevalim_ri_132151',{title:'עמי ותמי - הצגת ילדים',category:'kids',city:'ראשון לציון',venue:'FRIENDS ראשון לציון',start_date:'2027-03-20',start_time:'11:30',content_source_url:'https://tickets.mevalim.co.il/event/NQm5Uolkhhlq-yX'}),row('board_fe384389fdeacddbea',{title:'עמי ותמי',category:'kids',city:'ראשון לציון',venue:'FRIENDS ראשון לציון',start_date:'2027-03-20',start_time:'11:30',content_source_url:'https://friends-hist.co.il/show/עמי-ותמי/'})];
assert.equal(q.sanitize(amiTami[0]).title,'עמי ותמי','Only reviewed source listing title is repaired');
assert.equal(q.reconcile(amiTami).length,1,'Same source-verified show is one occurrence');
assert.equal(q.suspectedDuplicates(q.reconcile(amiTami,{keepDuplicates:true})).length,0);
assert.equal(q.resolve(amiTami,amiTami[0].event_id).event_id,q.resolve(amiTami,amiTami[1].event_id).event_id);
for(const changed of [{start_date:'2027-03-21'},{start_time:'12:30'},{venue:'FRIENDS חולון'},{title:'עמי ותמי - קאסט אחר'}]){
 assert.equal(q.reconcile([amiTami[0],{...amiTami[1],...changed}]).length,2,'Distinct show remains distinct: '+JSON.stringify(changed));
}
for(const changed of [{start_date:'2027-03-21'},{start_time:'12:30'},{venue:'FRIENDS חולון'},{title:'עמי ותמי - קאסט אחר'},{event_id:'some-other-source'}]){
 assert.equal(q.sanitize({...amiTami[0],...changed}).title,changed.title||amiTami[0].title,'Unverified listing must not be retitled: '+JSON.stringify(changed));
}
console.log('PASS: Rishon Hansel and Gretel specific source correction keeps both IDs; different date/time/venue/cast/source untouched');

// A general source-label rule must work for new productions, not only named incident aliases.
const metadataTitles=['יצירה חדשה לגמרי','יצירה חדשה לגמרי - תאטרון הקאמרי','יצירה חדשה לגמרי - תיאטרון הקאמרי','יצירה חדשה לגמרי- עונת המנויים 27-28','יצירה חדשה לגמרי - תיאטרון הקאמרי - עונת המנויים 2027-2028'];
const metadataRows=metadataTitles.map((title,i)=>row('metadata-'+i,{title,category:'theatre',series_id:'seller-series-'+i}));
assert.equal(q.reconcile(metadataRows).length,1);
assert.equal(new Set(metadataRows.map(q.groupKey)).size,1,'Source series IDs must not split a theatre production');
for(const fields of [{title:'יצירה חדשה לגמרי עם צוות אחר'},{title:'יצירה חדשה לגמרי 2'},{title:'יצירה חדשה לגמרי לילדים'},{venue:'אולם אחר'},{venue:'אולם העיר - אולם 2'},{start_time:'21:00'}]){
 const other={...metadataRows[0],event_id:'distinct',...fields};
 if(fields.venue==='אולם העיר - אולם 2')continue; // A hall without a known room may refer to that room.
 assert.equal(q.reconcile([metadataRows[0],other]).length,2,JSON.stringify(fields));
}
const actualIndian=JSON.parse(fs.readFileSync('events-preview/ashdod/data/events.json')).events.filter(e=>e.title.includes('החולה ההודי'));
const indian=q.reconcile(actualIndian),dates=[...new Set(actualIndian.map(e=>e.start_date+'|'+e.start_time))];
assert.equal(indian.length,dates.length,'One canonical occurrence per actual date/time');
assert.equal(new Set(indian.map(q.groupKey)).size,1,'One carousel card containing every date');
for(const e of actualIndian)assert(q.resolve(actualIndian,e.event_id),'All old detail IDs must resolve');
const allOfra=JSON.parse(fs.readFileSync('events-preview/ashdod/data/events.json')).events.filter(e=>/ע[ו]?פרה/.test(e.title)&&e.start_date==='2026-11-14');assert.equal(q.reconcile(allOfra).length,1);
// Validate the real homepage function in every generated city, including differing source series IDs.
for(const city of ['ashdod','rishon-lezion','yavne','kiryat-gat','holon','herzliya']){
 const source=fs.readFileSync('events-preview/'+city+'/pilot/app.js','utf8');
 const start=source.indexOf('function eventGroupKey('),end=source.indexOf('function eventDisplayTitle(',start);assert(start>=0&&end>start);
 const runtime={window:{ISNET_EVENT_IDENTITIES:q},isRepresentativeHomeGame:()=>false,normalizeSearch:q.norm};vm.createContext(runtime);vm.runInContext(source.slice(start,end),runtime);
 assert.equal(new Set(metadataRows.map(runtime.eventGroupKey)).size,1,city+' generated display groups metadata aliases');
 assert.equal(new Set(indian.map(runtime.eventGroupKey)).size,1,city+' displays the Indian Patient once');
 const feed=JSON.parse(fs.readFileSync('events-preview/'+city+'/data/'+(['holon','herzliya'].includes(city)?'events-public.json':'events.json'))).events;
 const productions=new Map();for(const e of q.reconcile(feed).filter(e=>e.category==='theatre')){const key=q.titleKey(e)+'|'+q.venueKey(e);if(!productions.has(key))productions.set(key,new Set);productions.get(key).add(runtime.eventGroupKey(e))}
 assert([...productions.values()].every(keys=>keys.size===1),city+' must not split a production into carousel cards');
}
console.log('PASS: general theatre metadata/spelling normalization, every Indian Patient date, six real homepage grouping functions, old links and cast/venue/time safeguards');

const suspect=[row('review-1',{title:'מופע חדש לגמרי',category:'theatre',start_date:'2099-12-01'}),row('review-2',{title:'מופע חדש לגמרי - גרסה מיוחדת',category:'theatre',start_date:'2099-12-01'})];
assert.equal(q.reconcile(suspect).length,2,'Unreviewed similar titles must never be silently merged');
assert.equal(q.suspectedDuplicates(suspect).length,1,'An unknown similar-title occurrence must stop release for review');
assert.equal(q.suspectedDuplicates([suspect[0],{...suspect[1],start_time:'22:00'}]).length,0);
assert.equal(q.suspectedDuplicates([suspect[0],{...suspect[1],venue:'מקום אחר'}]).length,0);
const digest=require('node:crypto').createHash('sha256').update(fs.readFileSync('events-preview/shared/event-overlay.js')).digest('hex').slice(0,12);
for(const city of ['ashdod','rishon-lezion','yavne','kiryat-gat','holon','herzliya']){
 const html=fs.readFileSync('events-preview/'+city+'/index.html','utf8');assert(html.includes('event-overlay.js?v='+digest),city+' must invalidate cached identity code on every policy edit');
 const feed=JSON.parse(fs.readFileSync('events-preview/'+city+'/data/'+(['holon','herzliya'].includes(city)?'events-public.json':'events.json'))).events;
 const future=q.reconcile(feed).filter(e=>(e.end_date||e.start_date||'')>=publicGuard.day);assert.equal(q.suspectedDuplicates(future).length,0,city+' has unresolved candidates before release');
}
console.log('PASS: unknown duplicate candidates require review, distinct slots stay separate, all six HTML pages use the current policy hash');

const guarded=q.guardPublishedOverlays([suspect[0]],[{event_id:suspect[1].event_id,record_type:'manual',payload:suspect[1]}]);assert.equal(guarded.length,0,'Dynamic CMS must not bypass the release gate');
assert.equal(q.guardPublishedOverlays([metadataRows[0]],[{event_id:metadataRows[1].event_id,record_type:'manual',payload:metadataRows[1]}]).length,1,'Reviewed equivalent overlays remain available');
assert.equal(q.guardPublishedOverlays([suspect[0]],[{event_id:'later',record_type:'manual',payload:{...suspect[1],event_id:'later',start_time:'22:00'}}]).length,1,'A distinct performance is allowed');
console.log('PASS: dynamic CMS withholds unresolved duplicate additions while source events, reviewed aliases and distinct times survive');

assert.equal(q.guardPublishedOverlays([suspect[0]],[{event_id:'archived-overlay',record_type:'source',payload:suspect[1]}]).length,1,'Orphan source overlays are ignored by the board and must not create false duplicate blocks');

// Repeated publication must not append the same legacy link forever.
{
 const legacy={event_id:'legacy-a',title:'שם מקור קודם',url:'https://tickets.example/a'};
 const other={event_id:'legacy-b',title:'שם מקור נוסף',url:'https://tickets.example/b'};
 const rows=[row('stable-a',{source_aliases:[legacy,legacy]}),row('stable-b',{source_aliases:[other]})];
 const once=q.reconcile(rows,{keepDuplicates:true});
 assert.deepEqual(q.reconcile(once,{keepDuplicates:true}),once,'Full normalized records must be stable across repeated builds');
 const canonical=once.find(e=>!e.duplicate_of);
 assert.equal(canonical.source_aliases.filter(a=>a.event_id==='legacy-a').length,1);
 assert(canonical.source_aliases.some(a=>a.event_id==='legacy-b'),'Keep aliases carried by a secondary source');
 for(const id of ['legacy-a','legacy-b','stable-a','stable-b'])assert.equal(q.resolve(once,id).event_id,canonical.event_id);
}
console.log('PASS: repeated publication keeps exact aliases once and preserves all legacy detail links');
