const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const overlay=require('../events-preview/shared/event-overlay.js');
const base={title:'חדש',start_date:'2026-11-20',category:'music',long_description:'מקור חדש',image_url:'source.webp'};
const edit=overlay.patch({title:'עריכה',start_date:'2026-11-01'},{title:'קודם',start_date:'2026-11-01'});
const merged=overlay.merge(base,edit);
assert.equal(merged.title,'עריכה');assert.equal(merged.start_date,'2026-11-20');
assert.equal(overlay.merge(base,{...edit,locked_fields:[]}).title,'חדש');
assert.equal(overlay.merge(base,{overlay_version:2,locked_fields:['long_description'],description_manual_override:true,long_description:'ידני'}).description,'ידני');
assert.equal(overlay.merge(base,{overlay_version:2,locked_fields:['image_url','thumbnail_url'],image_manual_override:true,image_data_url:'data:image/png;base64,abc'}).thumbnail_url,'data:image/png;base64,abc');
assert.equal(overlay.visible({status:'hidden'}),false);assert.equal(overlay.visible({status:'active'}),true);
let remote={city_slug:'ashdod',event_id:'one',payload:{title:'before'},updated_at:'old'};
const calls=[];
class Query{
 constructor(){this.filters={};this.op='read';this.offset=0;this.end=199;}
 select(){return this;}eq(k,v){this.filters[k]=v;return this;}order(){return this;}range(a,b){this.offset=a;this.end=b;return this;}
 update(row){this.op='update';this.row=row;return this;}insert(row){this.op='insert';this.row=row;return this;}delete(){this.op='delete';return this;}
 async maybeSingle(){
  calls.push(this.op);
  if(this.op==='read')return {data:{...remote},error:null};
  if(this.filters.updated_at&&remote.updated_at!==this.filters.updated_at)return {data:null,error:null};
  remote={...remote,...this.row};return {data:{...remote},error:null};
 }
 then(resolve){return Promise.resolve({data:Array.from({length:Math.max(0,Math.min(200,405-this.offset))},(_,i)=>({city_slug:'ashdod',event_id:String(this.offset+i),updated_at:'v1'})),error:null}).then(resolve);}
}
const db={from(){return new Query()},auth:{getUser:async()=>({data:{user:{id:'editor'}}})}};
const window={ISNET_AUTH_CONFIG:{enabled:true},supabase:{createClient(){return db}}};
vm.runInNewContext(fs.readFileSync('events-preview/admin/cms-db.js','utf8'),{window,console,Date,Map});
(async()=>{
 const records=await window.ISNET_DB.listEventRecords();assert.equal(records.length,405);
 await window.ISNET_DB.getEventRecord('ashdod','one');remote.updated_at='concurrent';
 await assert.rejects(()=>window.ISNET_DB.saveEventRecord('ashdod','one',{title:'mine'}),e=>e.code==='EDIT_CONFLICT');assert.equal(remote.payload.title,'before');
 await window.ISNET_DB.getEventRecord('ashdod','one');const saved=await window.ISNET_DB.saveEventRecord('ashdod','one',{title:'mine'});assert.equal(saved.payload.title,'mine');
 let sourceCalls=0,cmsCalls=0;
 const win={ISNET_EVENT_OVERLAY:overlay};
 vm.runInNewContext(fs.readFileSync('events-preview/shared/public-cms.js','utf8'),{window:win,document:{currentScript:{src:'https://example.com/events-preview/shared/public-cms.js'}},location:{pathname:'/events-preview/ashdod/'},URL,Map,console,fetch:async address=>{
  const u=new URL(address);if(u.pathname.endsWith('events.json')){sourceCalls++;return {ok:true,json:async()=>({events:[base]})};}
  cmsCalls++;const offset=Number(u.searchParams.get('offset'));return {ok:true,json:async()=>Array.from({length:Math.max(0,Math.min(200,405-offset))},(_,i)=>({event_id:String(offset+i),payload:{title:'event'},record_type:'manual'}))};
 }});
 const [source,rows,again]=await Promise.all([win.ISNET_PUBLIC_CMS.loadSource(),win.ISNET_PUBLIC_CMS.publishedEvents('ashdod'),win.ISNET_PUBLIC_CMS.publishedEvents('ashdod')]);
 assert.equal(rows.length,405);assert.equal(again,rows);assert.equal(sourceCalls,1);assert.equal(cmsCalls,3);
 console.log('PASS: source-field locks, explicit unlock, manual copy and images, visibility, 405-record DB/API pagination, concurrent edit rejection, safe save, shared fetch deduplication');
})().catch(error=>{console.error(error);process.exitCode=1});
