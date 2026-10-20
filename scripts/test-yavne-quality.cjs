const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const {parseHTML}=require('linkedom');
const data=JSON.parse(fs.readFileSync('events-preview/yavne/data/events.json'));
const taxonomy=JSON.parse(fs.readFileSync('events-preview/admin/data/taxonomy.json'));
const context={window:{},location:{pathname:'/events-preview/yavne/category.html'},console,URL,URLSearchParams,Intl,Date,Set,Map,setTimeout};
vm.runInNewContext(fs.readFileSync('events-preview/yavne/yavne-events.js','utf8'),context);
for(const name of ['kids-hub','seniors-hub'])vm.runInNewContext(fs.readFileSync('events-preview/yavne/'+name+'.js','utf8'),context);
const helper=context.window.YAVNE_EVENTS,kids=context.window.ISNET_KIDS,seniors=context.window.ISNET_SENIORS;
const at={day:'2026-10-20',time:'00:00'};
const find=t=>data.events.find(e=>e.title.includes(t));
assert.equal(data.events.length,101);
for(const artist of ['דניאל סטיופין','אלי פיניש','סיפור הנס'])assert.equal(data.events.filter(e=>e.title.includes(artist)).length,1,artist+' deduplicated');
assert.equal(data.events.filter(e=>e.title==='הזוג המוזר').length,2,'Separate dates retained');
for(const t of ['מסביב לעולם','סיגי הסופגנייה','מפרץ ההרפתקאות'])assert(kids.visible(find(t),at),t+' discoverable in kids');
assert(!kids.forKids(find('ילדים בהזמנה')),'Adult lecture about children excluded from kids');
const health=find('סוגי הזיכרון');
assert(seniors.filterRows([health],{active:'senior-health',at}).length===1);
assert(seniors.filterRows([health],{active:'senior-lectures',at}).length===1);
assert(helper.matches(health,new Set(['lecture']))&&helper.matches(health,new Set(['seniors'])));
assert(helper.matches(find('מסביב לעולם'),new Set(['theatre'])));
assert.equal(find('בלב הפרא').category,'cinema');
for(const e of data.events){
 assert(!/גן יבנה|חבל יבנה|קבוצת יבנה/.test(e.city+' '+e.venue+' '+e.title));
 for(const m of e.category_memberships||[]){
  const c=taxonomy.primary_categories.find(c=>c.id===m.category);
  if(c&&m.subcategory)assert(c.subcategories.some(s=>s.id===m.subcategory),m.category+'/'+m.subcategory);
 }
 if(e.image_publishable&&e.image_url.startsWith('assets/'))assert(fs.existsSync('events-preview/yavne/'+e.image_url));
 const fallback=context.window.isnetEventIllustration(e);if(fallback?.src.startsWith('../ashdod/'))assert(fs.existsSync('events-preview/'+fallback.src.slice(3)));
}
async function listing(category,sub){
 const {document}=parseHTML('<html><title></title><body><h1 id="title"></h1><p id="lead"></p><nav id="subcategories"></nav><input id="q" value=""><span id="count"></span><p id="empty" hidden></p><div id="cards"></div></body></html>');
 const ctx={...context,document,window:{ISNET_CITY_BOOTSTRAP:{...data,taxonomy},ISNET_PUBLIC_CMS:{loadCards:async()=>data,publishedEvents:async()=>[]}}};
 ctx.location={pathname:'/events-preview/yavne/category.html',search:'?category='+category+(sub?'&subcategory='+sub:'')};
 vm.runInNewContext(fs.readFileSync('events-preview/yavne/yavne-events.js','utf8'),ctx);
 vm.runInNewContext(fs.readFileSync('events-preview/yavne/category-landing.js','utf8'),ctx);
 await new Promise(setImmediate);
 const cards=document.querySelectorAll('#cards .card');assert(cards.length>0,category+' loads');
 if(sub)for(const card of cards){const id=new URL(card.href,'https://example.com').searchParams.get('id');assert(helper.matchesSub(data.events.find(e=>e.event_id===id),category,sub));}
 assert(document.querySelectorAll('#subcategories a').length>1,'subcategory navigation exists');
}
(async()=>{await listing('lecture','health-medicine');await listing('music','dance-performance');await listing('theatre');console.log('PASS Yavne: duplicates, retained dates, multi-category and subcategory membership, child/adult separation, images and category filtering');})().catch(e=>{console.error(e);process.exitCode=1});
