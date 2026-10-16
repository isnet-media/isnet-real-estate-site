const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const {parseHTML}=require('linkedom');
const overlay=require('../events-preview/shared/event-overlay.js');
const taxonomy=JSON.parse(fs.readFileSync('events-preview/admin/data/taxonomy.json'));
async function check(manual){
 const {document,window}=parseHTML(fs.readFileSync('events-preview/admin/edit.html','utf8'));
 for(const select of document.querySelectorAll('select')){let selected;Object.defineProperty(select,'value',{get(){return selected??this.querySelector('option[selected]')?.getAttribute('value')??this.querySelector('option')?.getAttribute('value')??''},set(v){selected=v},configurable:true});}
 const event={event_id:'test-event',title:'אירוע מקור',category:'music',status:'active',start_date:'2099-01-01',start_time:'20:00',venue:'היכל',description:'תיאור מהמקור',image_url:'image.webp',image_publishable:true,image_verified:true};
 let writes=[];
 const db={listEventRevisions:async()=>[{id:1,action:'UPDATE',recorded_at:'2026-10-16T00:00:00Z',after_row:{payload:{...event,title:'גרסה קודמת',overlay_version:2,locked_fields:['title']}}}],getEventRecord:async()=>manual?{record_type:'manual',payload:event,updated_at:'v1'}:null,saveEventRecord:async(city,id,payload,type)=>{writes.push({payload,type});return {payload,updated_at:'v2'}},publishEvent:async(city,id,payload,type)=>{writes.push({payload,type});return {payload:{...payload,status:'active'},seo_slug:'test'}}};
 window.ISNET_EVENT_OVERLAY=overlay;window.ISNET_DB=db;
 const context=vm.createContext({document,window,console,location:{search:'?city=ashdod&id=test-event',href:'https://example.com/events-preview/admin/edit.html'},URLSearchParams,URL,Date,Set,FileReader:class{},confirm:()=>true,alert:message=>{throw Error(message)},setTimeout:()=>{},localStorage:{getItem:()=>null,setItem(){},removeItem(){}},fetch:async url=>({ok:true,json:async()=>url.includes('taxonomy')?taxonomy:url.includes('editorial')?{events:{}}:{events:manual?[]:[event]}})});
 vm.runInContext(fs.readFileSync('events-preview/admin/edit.js','utf8'),context);
 await new Promise(setImmediate);
 assert.equal(document.getElementById('title').value,event.title);
 assert.ok(document.getElementById('cloneLink').href.includes('clone=test-event'));
 document.getElementById('title').value='כותרת ידנית';document.getElementById('saveDraftBtn').dispatchEvent(new window.Event('click'));
 await new Promise(setImmediate);
 assert.equal(writes.length,1);assert.equal(writes[0].type,manual?'manual':'override');assert.ok(writes[0].payload.locked_fields.includes('title'));
 if(!manual)assert.ok(!writes[0].payload.locked_fields.includes('start_date')); 
 if(manual)assert.equal(document.getElementById('restoreBtn').disabled,true);
 document.getElementById('loadHistory').dispatchEvent(new window.Event('click'));await new Promise(setImmediate);
 assert.equal(document.querySelectorAll('#historyEntries button').length,1);
 document.querySelector('#historyEntries button').dispatchEvent(new window.Event('click'));
 assert.equal(document.getElementById('title').value,'גרסה קודמת');assert.equal(writes.length,1);
 assert(document.getElementById('saveNote').textContent.includes('לעריכה בלבד'));
}
(async()=>{await check(false);await check(true);console.log('PASS: source and manual event editor load, editable fields, source locks, clone link, correct record type on save');})().catch(error=>{console.error(error);process.exitCode=1});
