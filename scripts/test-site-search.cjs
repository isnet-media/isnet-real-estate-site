const assert=require('assert/strict'),fs=require('fs'),{performance}=require('perf_hooks'),E=require('../events-preview/ashdod/site-search-engine.js');
const fixture={events:[{event_id:'kids',title:'הצגת ילדים מצחיקה',description:'קומדיה לכל המשפחה',category:'kids',subcategory:'kids-theatre',start_date:'2026-10-17',start_time:'16:00',age_min:3,age_max:8,price_min_ils:50},{event_id:'adult',title:'סטנדאפ למבוגרים',category:'standup',start_date:'2026-10-17',start_time:'20:00',age_min:18,price_min_ils:90},{event_id:'old',title:'הצגת ילדים',category:'kids',start_date:'2020-01-01'},{event_id:'unknown',title:'הרצאה',category:'lecture',start_date:'2026-10-17'}],movies:[{id:'movie',title:'סרט ילדים מצחיק',synopsis:'קומדיה לכל המשפחה',genres:['קומדיה'],is_family:true,age_rating:'מותר לכל',venues:[{name:'סינמה סיטי',schedule:{'2026-10-17':['14:00','17:00'],'2020-01-01':['12:00']}}]}],taxonomy:[{id:'kids',label:'ילדים',subcategories:[{id:'kids-theatre',label:'הצגות ילדים'}]}],places:{categories:{parks:{title:'פארקים',items:[{id:'p',name:'פארק אשדוד ים',description:'מקום למשפחות',tags:['families']} ]}}}};
const docs=E.create(fixture);const run=(q,prev)=>E.search(docs,E.parse(q,prev),'2026-10-15',13*60);
let r=run('סרט מצחיק לילדים בשבת');assert.equal(r.results[0].id,'m:movie');assert.equal(r.results[0].date,'2026-10-17');assert.equal(r.results[0].href,'movie.html?id=movie');
r=run('אחרי 16:00',r.context);assert.equal(r.results[0].time,'17:00');assert.equal(r.context.type,'movie');
r=run('עם הילד בן ארבע בשבת');assert(!r.results.some(x=>x.id==='e:adult'));assert.equal(r.context.age,4);
r=run('סטנדפ');assert.equal(r.results[0].id,'e:adult');
r=run('סרטים עד 50 שקל');assert.equal(r.count,0); // Unknown price never becomes free.
assert.equal(run('גכעכטלמ').count,0);
assert.equal(run('פארק בשבת').count,0); // No invented opening schedule.
assert.equal(run('הצגת ילדים',null).results[0].subcategory,'הצגות ילדים');

console.log('PASS: unified search constraints and grounded routing');

const locationDocs=E.create({events:[
 {event_id:'in',title:'הצגת ילדים',category:'kids',start_date:'2026-10-17',price_min_ils:30,venue_type:'indoor'},
 {event_id:'out',title:'הצגת ילדים',category:'kids',start_date:'2026-10-17',price_min_ils:30,is_indoor:false},
 {event_id:'unknown-setting',title:'הצגת ילדים',category:'kids',start_date:'2026-10-17',price_min_ils:30}
]});
let locationContext=E.parse('משהו לילדים בשבת עד 50 שקלים לא בחוץ');
assert.equal(locationContext.setting,'indoor');assert(!locationContext.concepts?.includes('nature'));
assert.deepEqual(E.search(locationDocs,locationContext,'2026-10-15',0).results.map(x=>x.id),['e:in']);
locationContext=E.parse('רק בחוץ',locationContext);assert.equal(locationContext.setting,'outdoor');
assert.deepEqual(E.search(locationDocs,locationContext,'2026-10-15',0).results.map(x=>x.id),['e:out']);
console.log('PASS: negated outdoor intent and explicit location evidence; unknown settings excluded');

assert.deepEqual(E.search(locationDocs,E.parse('במקום סגור'),'2026-10-15',0).results.map(x=>x.id),['e:in']);
assert(!E.parse('לא בחוץ',E.parse('טיולים בחוץ')).concepts.includes('nature'));

const fallback=run('הצגת ילדים בשבת עד 20 שקל');assert.equal(fallback.count,0);assert(fallback.alternatives.some(a=>a.label.includes('תקציב')&&a.results.some(x=>x.id==='e:kids')));assert(!fallback.alternatives.some(a=>a.results.some(x=>x.id==='e:adult')));assert.equal(run('גכעכטלמ').alternatives.length,0);
console.log('PASS: labeled budget/date alternatives preserve family, age, location and named terms');

const namedDocs=E.create({events:[{event_id:'mansdorf',title:'שבת של ספורט והשראה לכל המשפחה',description:'מפגש עם עמוס מנסדורף',category:'lecture',start_date:'2026-11-14',start_time:'09:30'},{event_id:'match',title:'כדורעף',category:'sport',start_date:'2026-10-24',start_time:'19:00'}]});
for(const q of ['שבת של ספורט','שבת של ספורט והשראה לכל המשפחה']){
 const result=E.search(namedDocs,E.parse(q),'2026-10-19',0);
 assert.equal(result.results[0]?.id,'e:mansdorf');assert.equal(result.results[0].date,'2026-11-14');assert.equal(result.context.period,undefined);
}
assert.equal(E.search(namedDocs,E.parse('ספורט בשבת'),'2026-10-19',0).results[0]?.id,'e:match');
console.log('PASS: event title containing Saturday is found beyond the nearest weekend; explicit Saturday requests remain constrained');
