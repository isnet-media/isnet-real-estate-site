// Exercise the shipped controllers with a loaded catalogue and an existing list.
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const cities=['ASHDOD','YAVNE','KGAT','RISHON','HOLON','BATYAM'];
(async()=>{for(const city of cities){
 const source=fs.readFileSync(`SUPER.${city}/live.js`,'utf8');
 const key=source.match(/localStorage.getItem\('([^']+)'/)[1];
 let saved=JSON.stringify({'7290004131074':3}),writes=0,dialogs=[];
 const elements=new Map(),element=s=>{if(!elements.has(s))elements.set(s,{innerHTML:'',textContent:'',value:'',style:{},classList:{add(){},contains(){return true}},addEventListener(){},append(){},prepend(){},remove(){},scrollIntoView(){}});return elements.get(s)};
 const doc={querySelector:element,querySelectorAll:()=>[],getElementById:()=>null,createElement:()=>element('new'),body:{classList:{add(){},contains(){return true}}}};
 const catalog={rows:[['7290004131074','חלב','1','ליטר','0','',6.8,1,['branch'],'package'],['7290003643004','אורז','1','קג','0','',12,1,['branch'],'package']],branches:[{id:'branch',name:'בדיקה',chain:'רשת',file_date:'2026-10-23',product_count:2}],retrieved_at:'2026-10-23T08:00:00+03:00'};
 const ctx={window:{addEventListener(){},dispatchEvent(){},SuperProductGroups:{normalize:s=>s,group:()=>[]}},document:doc,localStorage:{getItem:k=>{assert.equal(k,key);return saved},setItem:(k,v)=>{assert.equal(k,key);saved=v;writes++}},fetch:async path=>({ok:true,json:async()=>path.includes('catalog.json')?structuredClone(catalog):{pending:[]}}),location:{hash:''},modal:s=>dialogs.push(s),Event:class{},console:{...console,error:e=>{throw e}}};
 vm.createContext(ctx);vm.runInContext(source,ctx);
 await new Promise(r=>setImmediate(r));
 const before=writes;ctx.window.loadSample();assert.equal(writes,before,city);assert.equal(JSON.parse(saved)['7290004131074'],3,city);assert.match(dialogs.pop(),/נשארו כפי שהן/,city);
 ctx.window.clearCart();ctx.window.loadSample();assert.deepEqual(JSON.parse(saved),{'7290004131074':1,'7290003643004':1},city);
 ctx.window.loadSample();assert.deepEqual(JSON.parse(saved),{'7290004131074':1,'7290003643004':1},city);
 console.log(`${city}: existing list and quantities preserved; sample works only on an empty list`);
}})().catch(e=>{console.error(e);process.exitCode=1});
