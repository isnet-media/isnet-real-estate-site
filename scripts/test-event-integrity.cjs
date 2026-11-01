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
for(const city of ['ashdod','rishon-lezion','yavne','kiryat-gat','holon']){const data=JSON.parse(fs.readFileSync('events-preview/'+city+'/data/'+(city==='holon'?'events-public.json':'events.json')));const reviewed=q.reconcile(data.events),again=q.reconcile(reviewed);assert.equal(reviewed.length,again.length);assert.equal(new Set(reviewed.map(e=>e.event_id)).size,reviewed.length);assert(!reviewed.some(e=>String(e.image_url).startsWith('data:image/svg')));for(const e of reviewed){assert(data.events.some(x=>x.event_id===e.event_id));assert(!e.duplicate_of)}}
console.log('PASS: all five feeds, exact occurrence identity, distinct times/venues/casts, old IDs, source media, editorial image locks, illustrations and conflicting IDs');

const vm=require('node:vm'),context={window:{location:{pathname:'/events-preview/ashdod/'}},URL,Promise};vm.createContext(context);vm.runInContext(fs.readFileSync('events-preview/shared/event-overlay.js','utf8'),context);vm.runInContext(fs.readFileSync('events-preview/ashdod/ashdod-event-identities.js','utf8'),context);assert.equal(typeof context.window.ISNET_EVENT_IDENTITIES.groupKey,'function');assert.equal(typeof context.window.ISNET_EVENT_IDENTITIES.sanitize,'function');console.log('PASS: legacy identity adapter preserves shared runtime API');

const fake={dataset:{mediaAlternatives:JSON.stringify(['https://same-show.test/backup.jpg'])},getAttribute:()=> 'https://same-show.test/blocked.jpg'};q.imageError(fake);assert.equal(fake.src,'https://same-show.test/backup.jpg');assert.equal(fake.dataset.mediaAlternatives,'[]');console.log('PASS: failed source image uses the same occurrence backup');

const manual=q.reconcile([row('source',{source_content_authoritative:true}),row('editor',{locked_fields:['description'],description:'Approved editorial copy'})]);assert.equal(manual[0].event_id,'source');assert.equal(manual[0].description,'Approved editorial copy');console.log('PASS: explicit editorial locks take priority within duplicate occurrences');

const comedy=[row('friends_as_cab289dedf10fa4c60',{title:'קומדי בר- סטנדאפ',city:'אשדוד',category:'standup',venue:'הוט סינמה אשדוד - אולם 2',source_priority:1}),row('makore_as_91fb472ae5344d1b11',{title:'כוכבי הקומדי בר מגיעים למרתון סטנדאפ אשדוד 19.11.26',city:'אשדוד',category:'standup',venue:'הוט סינמה אשדוד - אולם 2',source_priority:4})];assert(context.window.ISNET_EVENT_IDENTITIES.resolve(comedy,'makore_as_91fb472ae5344d1b11')._source_event_ids.includes('friends_as_cab289dedf10fa4c60'));console.log('PASS: previously reviewed comedy aliases retain old detail links');

const publicGuard=require('./check-public-event-integrity.cjs');assert(publicGuard.invalidPublishedRow(row('future',{title:'מבלים',start_date:publicGuard.day})));assert(!publicGuard.invalidPublishedRow(row('archive',{title:'מבלים',start_date:'2000-01-01'})));assert(!publicGuard.invalidPublishedRow(row('hidden',{title:'מבלים',start_date:publicGuard.day,status:'hidden'})));assert(publicGuard.invalidPublishedRow(row('svg',{start_date:'2000-01-01',image_url:'data:image/svg+xml,blank'})));console.log('PASS: live publication guard distinguishes archived source history from active events');
