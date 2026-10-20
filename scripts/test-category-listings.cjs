const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const {parseHTML}=require('linkedom');
const overlay=require('../events-preview/shared/event-overlay.js');
async function run(city,category,compact,missing=false){
 const {document}=parseHTML('<html><title></title><body><h1 id="title"></h1><p id="lead"></p><nav id="subcategories"></nav><input id="q" value=""><span id="count"></span><p id="empty" hidden></p><div id="cards"></div></body></html>');
 const data=JSON.parse(fs.readFileSync(`events-preview/${city}/data/events.json`));
 const cards=JSON.parse(fs.readFileSync(`events-preview/${city}/data/events-cards.json`));
 const requests=[];
 const rows=[{event_id:'manual-test',record_type:'manual',payload:{event_id:'manual-test',title:'Manual CMS event',category,start_date:'2099-01-01'}}];
 const original=data.events.find(e=>e.category===category);
 if(original)rows.push({event_id:original.event_id,record_type:'override',payload:{...original,status:'hidden'}});
 const window={ISNET_EVENT_OVERLAY:overlay};
 const context={window,document,location:{pathname:`/events-preview/${city}/category.html`,search:`?category=${category}`},URL,URLSearchParams,Map,Set,Intl,Date,console,fetch:async address=>{
  const u=new URL(address,`https://example.com/events-preview/${city}/`);requests.push(u.pathname);
  if(u.pathname.endsWith('events-cards.json'))return {ok:!missing,json:async()=>cards};
  if(u.pathname.endsWith('events.json'))return {ok:true,json:async()=>data};
  return {ok:true,json:async()=>rows};
 }};
 document.currentScript={src:'https://example.com/events-preview/shared/public-cms.js'};
 vm.runInNewContext(fs.readFileSync('events-preview/shared/public-cms.js','utf8'),context);
 if(!compact){window.ISNET_PUBLIC_CMS.loadCards=window.ISNET_PUBLIC_CMS.loadSource;const published=window.ISNET_PUBLIC_CMS.publishedEvents;window.ISNET_PUBLIC_CMS.publishedEvents=city=>published(city);}
 vm.runInNewContext(fs.readFileSync(`events-preview/${city}/category-landing.js`,'utf8'),context);
 await new Promise(resolve=>setImmediate(resolve));
 const initial=document.getElementById('cards').innerHTML;
 assert(initial.includes('manual-test'),'CMS manual events remain visible');
 if(original)assert(!initial.includes('id='+encodeURIComponent(original.event_id)+'"'),'CMS hidden event remains hidden');
 document.getElementById('q').value='Manual CMS';document.getElementById('q').dispatchEvent(new document.defaultView.Event('input'));
 assert.equal(document.querySelectorAll('#cards .card').length,1,'Search still filters');
 return {initial,requests};
}
(async()=>{
 for(const city of ['ashdod','rishon-lezion'])for(const category of ['music','theatre','standup','lecture','sport','community']){
  const full=await run(city,category,false),light=await run(city,category,true),fallback=await run(city,category,true,true);
  assert.equal(light.initial,full.initial,`${city}/${category}: identical card rendering`);
  assert.equal(fallback.initial,full.initial,'Missing compact asset falls back safely');
  assert(!light.requests.some(u=>u.endsWith('/events.json')),'No full dataset request on listing path');
  assert.equal(light.requests.filter(u=>u.endsWith('/events-cards.json')).length,1,'Shared compact request');
 }
 console.log('PASS: both cities, six categories, identical full/compact cards, CMS visibility, manual events, search, no full-data fetch and missing-asset recovery');
})().catch(e=>{console.error(e);process.exitCode=1});
