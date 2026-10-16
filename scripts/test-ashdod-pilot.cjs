const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const nodes=new Map();
const ctx={Intl,URL,URLSearchParams,Date,location:{pathname:'/test/',href:'https://isnet.co.il/events-preview/ashdod/event.html'},window:{},document:{getElementById(id){if(!nodes.has(id))nodes.set(id,{innerHTML:'',hidden:false});return nodes.get(id)}}};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync('events-preview/shared/editorial-safety.js','utf8'),ctx);
vm.runInContext(fs.readFileSync('events-preview/ashdod/pilot/event.js','utf8').replace(/\ninit\(\);\s*$/,''),ctx);
const event=(id,date,extra={})=>({event_id:id,title:id,category:'music',start_date:date,...extra});
const at=new Date('2026-10-11T10:00:00Z');
assert.equal(ctx.isUpcoming(event('future','2026-10-12'),at),true);
assert.equal(ctx.isUpcoming(event('past','2026-10-10'),at),false);
assert.equal(ctx.isUpcoming(event('earlier today','2026-10-11',{start_time:'12:00'}),at),false);
assert.equal(ctx.isUpcoming(event('later today','2026-10-11',{start_time:'14:00'}),at),true);
assert.equal(ctx.isUpcoming(event('bad','2026-99'),at),false);
assert.equal(ctx.isUpcoming(event('draft','2026-10-12',{publication_status:'draft'}),at),false);
ctx.renderRelated(event('current','2099-10-12'),[
 event('current','2099-10-12'),event('past','2020-01-01'),event('next','2099-10-13'),event('next','2099-10-14'),event('other','2099-10-13',{category:'kids'})
]);
const related=nodes.get('relatedGrid').innerHTML;
assert.equal((related.match(/class="relatedCard"/g)||[]).length,1,'future recommendations render and deduplicate');
assert(!related.includes('past')&&!related.includes('other'));
assert.equal(ctx.meaningfulEventDescription({description:"מחפשים מה לעשות? הזמינו כרטיסים לכל האירועים באתר טיקצ'אק LIVE"}), '');
assert.equal(ctx.meaningfulEventDescription({long_description:'לפי אתר המקור יש לבדוק מידע לפני פרסום',description:'מופע במונארט אשדוד ביום שני בשעה 11:00.'}),'מופע במונארט אשדוד ביום שני בשעה 11:00.');
assert.equal(ctx.purchaseAction(event('phone','2099-10-12',{contact_phone:'08-8545170'})).href,'tel:088545170');
assert.equal(ctx.purchaseAction(event('old','2020-01-01',{purchase_url:'https://example.com/ticket'})),null);
assert.equal(ctx.purchaseAction(event('aggregator','2099-10-12',{purchase_url:'https://live.tickchak.co.il/ashdod',contact_phone:'123'})).kind,'phone');
assert.equal(ctx.trustedImage({image_url:'https://static.smarticket.co.il/assets/microsoft_oauth_logo.png',image_verified:true,image_publishable:true}),false);
assert.equal(ctx.trustedImage({image_url:'category.webp',image_verified:true,image_publishable:true,image_represents_event:false}),false);
const app=fs.readFileSync('events-preview/ashdod/pilot/app.js','utf8');
const from=app.indexOf('function nextWeekendRange(){'),to=app.indexOf('\nfunction formatTime',from);
ctx.today=()=>new Date('2026-10-17T12:00:00');
ctx.daysFrom=(base,n)=>{const d=new Date(base);d.setDate(d.getDate()+n);return d};
vm.runInContext(app.slice(from,to),ctx);
assert.equal(ctx.nextWeekendRange()[1].getDate(),17,'Saturday stays in the current weekend');
console.log('PASS: upcoming dates, Israel clock, visible recommendations, duplicates, editorial safety, contact fallback, past CTA and Saturday filter');

ctx.isNonEventActivity=()=>false;
const mergeStart=app.indexOf('function publishedBoardEvents('),mergeEnd=app.indexOf('async function init(){',mergeStart);
vm.runInContext(app.slice(mergeStart,mergeEnd),ctx);
assert.equal(ctx.publishedBoardEvents([event('corrected','2026-10-11')],[{event_id:'corrected',payload:{start_date:'2026-10-10'}}],'2026-10-11').length,0,'CMS past-date corrections must remove cards');
assert.equal(ctx.publishedBoardEvents([event('rescheduled','2026-10-10')],[{event_id:'rescheduled',payload:{start_date:'2026-10-12'}}],'2026-10-11').length,1,'CMS future-date corrections must restore cards');
console.log('PASS: board merges CMS corrections before filtering dates');

ctx.renderRelated(event('current','2099-10-12',{category:'standup'}),[event('n1','2099-10-13',{title:'נועה מנור',category:'standup'}),event('n2','2099-10-13',{title:'נועה מנור במופע סטנדאפ',category:'standup'})]);
assert.equal((nodes.get('relatedGrid').innerHTML.match(/class="relatedCard"/g)||[]).length,1,'generic standup title suffix does not duplicate recommendations');
console.log('PASS: semantic title duplicates in recommendations');

const searchStart=app.indexOf('const SEARCH_CONCEPTS='),searchEnd=app.indexOf('function preciseSubcategoryIntent(',searchStart);
vm.runInContext(app.slice(searchStart,searchEnd),ctx);
ctx.iso=()=> '2026-10-11';
const familyIntent=ctx.parseSearchIntent('לאן יוצאים עם הילדים');
assert.equal(familyIntent.terms.length,0,'conversational verb must not be required in event text');
assert(ctx.eventSemanticScore(event('סערה בדלי מים','2099-10-12',{category:'kids',short_pitch:'הצגת ילדים לגילאי 4–10'}),familyIntent)>0,'verified child event matches family intent');
assert.equal(ctx.parseSearchIntent('אסף מור יוסף').terms.length,3,'performer names remain required search terms');
console.log('PASS: conversational family search and performer-name search');

assert.equal(ctx.eventSemanticScore(event('adult comedy','2099-10-12',{category:'standup',long_description:'סיפורים על ילדותו של האמן ועל חיי המשפחה.'}),familyIntent),null,'childhood biography is not a children activity');
assert.equal(ctx.eventSemanticScore(event('senior festival','2099-10-12',{category:'festival',title:'פסטיבל ילד פלא - יעודי לגדולות מהחיים'}),familyIntent),null,'senior club event is not a family recommendation');
assert.equal(ctx.eventSemanticScore(event('adult age limit','2099-10-12',{category:'theatre',short_pitch:'מופע לכל המשפחה',age_min:18}),familyIntent),null,'verified adult age limit takes precedence');
assert(ctx.eventSemanticScore(event('family theatre','2099-10-12',{category:'theatre',short_pitch:'הצגה להורים ולילדים'}),familyIntent)>0,'family theatre remains discoverable');
console.log('PASS: family search excludes adult shows, childhood biographies and senior-only events');

vm.runInContext('purchaseHealth={results:{"https://tickets.example/event":{state:"broken",checked_at:new Date().toISOString()}}}',ctx);
assert.equal(ctx.purchaseAction(event('broken','2099-01-01',{purchase_url:'https://tickets.example/event'})),null);
assert.equal(ctx.purchaseAction(event('broken','2099-01-01',{purchase_url:'https://tickets.example/event',contact_phone:'08-1234567'})).kind,'phone');
vm.runInContext('purchaseHealth={results:{"https://tickets.example/event":{state:"broken",checked_at:"2020-01-01T00:00:00Z"}}}',ctx);
assert.equal(ctx.purchaseAction(event('old-audit','2099-01-01',{purchase_url:'https://tickets.example/event'})).kind,'url');
console.log('PASS: recent exact broken-link suppression, contact fallback, stale-audit expiry');

assert.equal(new URL(ctx.canonicalEventUrl({event_id:'richer-other-occurrence',title:'כותרת מעודכנת',_canonical_slug:'selected-occurrence'})).searchParams.get('slug'),'selected-occurrence');
console.log('PASS: richer grouped content retains the selected event canonical slug');

const replaced={event_id:'makore_as_newid12345678',title:'מופע בשם מדויק',start_date:'2099-01-01'};
assert.equal(ctx.findSlugEvent([replaced],'מופע-בשם-מדויק-oldid123').event_id,replaced.event_id);
assert.equal(ctx.findSlugEvent([replaced],'שם-שונה-oldid123'),null);
assert.equal(ctx.findSlugEvent([{...replaced,series_id:'one'},{...replaced,event_id:'other',series_id:'two'}],'מופע-בשם-מדויק-oldid123'),null);
console.log('PASS: exact-title legacy slug recovery after source ID replacement; ambiguous groups rejected');

const longTitleEvent={event_id:'long-title-12345678',title:'א'.repeat(120)};assert.equal(ctx.findSlugEvent([longTitleEvent],ctx.eventSlug(longTitleEvent)),longTitleEvent);
console.log('PASS: full generated slugs retain ID suffixes for long Hebrew titles');
