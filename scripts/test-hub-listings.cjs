const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const {parseHTML}=require('linkedom');
const overlay=require('../events-preview/shared/event-overlay.js');
async function render(city,hub,mode){
 const base=`events-preview/${city}/`;
 const {document}=parseHTML(fs.readFileSync(base+'category.html','utf8'));
 const selectPrototype=document.defaultView.HTMLSelectElement.prototype;
 Object.defineProperty(selectPrototype,'value',{configurable:true,get(){return this.querySelector('option[selected]')?.value||this.querySelector('option')?.value||''},set(value){for(const o of this.querySelectorAll('option')){if(o.value===value)o.setAttribute('selected','');else o.removeAttribute('selected')}}});
 const location={pathname:`/${base}category.html`,search:`?category=${hub}`,href:`https://example.com/${base}category.html?category=${hub}`};
 const calls=[];
 const sourceData=JSON.parse(fs.readFileSync(base+'data/events.json','utf8'));
 const selected=sourceData.events.find(e=>e.category===hub);
 const cmsRows=[{event_id:'manual-hub-check',record_type:'manual',payload:{event_id:'manual-hub-check',category:hub,title:'מוזיקה בדיקת ניהול',start_date:'2099-01-01',description:'טקסט ניהול מלא',venue:'מקום בדיקה'}}];
 if(selected)cmsRows.push({event_id:selected.event_id,record_type:'override',payload:{...selected,status:'hidden'}});
 const window={location,ISNET_EVENT_OVERLAY:overlay};
 const context={window,document,location,URL,URLSearchParams,Map,Set,Intl,Date,console,history:{replaceState(){}},localStorage:{getItem:()=>null,setItem(){},removeItem(){}},matchMedia:()=>({matches:false}),fetch:async address=>{
  const u=new URL(address,location.href);calls.push(u.pathname);
  if(u.pathname.includes('/rest/v1/')){assert.equal(u.searchParams.get('city_slug'),'eq.'+city,'CMS city isolation');return {ok:true,json:async()=>cmsRows};}
  const name=u.pathname.split('/').pop();
  if(name==='events-hubs.json'&&mode==='missing')return {ok:false};
  const p=base+'data/'+name;
  return {ok:fs.existsSync(p),json:async()=>JSON.parse(fs.readFileSync(p,'utf8'))};
 }};
 document.currentScript={src:'https://example.com/events-preview/shared/public-cms.js'};
 vm.runInNewContext(fs.readFileSync('events-preview/shared/public-cms.js','utf8'),context);
 if(mode==='full'){
  window.ISNET_PUBLIC_CMS.loadHub=window.ISNET_PUBLIC_CMS.loadSource;
  const original=window.ISNET_PUBLIC_CMS.publishedEvents;
  window.ISNET_PUBLIC_CMS.publishedEvents=city=>original(city);
 }
 if(city==='ashdod')vm.runInNewContext(fs.readFileSync(base+'ashdod-event-identities.js','utf8'),context);
 const file={kids:'kids-hub.js',seniors:'seniors-hub.js',exhibition:'exhibition-magazine.js'}[hub];
 vm.runInNewContext(fs.readFileSync(base+file,'utf8').replace('}catch{root.innerHTML=', '}catch(error){throw error;root.innerHTML='),context);
 const api=window[{kids:'ISNET_KIDS',seniors:'ISNET_SENIORS',exhibition:'ISNET_EXHIBITIONS'}[hub]];
 await api.init();
 const main=document.querySelector('main');
 assert(!main.querySelector('[role="alert"]'),`${city}/${hub}: init successful`);
 const initial=main.innerHTML;
 const input=main.querySelector('input[type="search"]');
 input.value='מוזיקה';input.dispatchEvent(new document.defaultView.Event('input'));
 return {initial,search:main.innerHTML,calls};
}
(async()=>{
 for(const city of ['ashdod','rishon-lezion'])for(const hub of (city==='ashdod'?['kids','seniors','exhibition']:['kids','seniors'])){
  const full=await render(city,hub,'full'),light=await render(city,hub,'hub'),fallback=await render(city,hub,'missing');
  assert.equal(light.initial,full.initial,`${city}/${hub}: initial DOM identical`);
  assert.equal(light.search,full.search,`${city}/${hub}: full-text search identical`);
  assert.equal(fallback.initial,full.initial,`${city}/${hub}: recovery identical`);
  assert(!light.calls.some(p=>p.endsWith('/events.json')),'No full dataset download');
  assert.equal(light.calls.filter(p=>p.endsWith('/events-hubs.json')).length,1,`${city}/${hub}: deduplicated hub request ${light.calls.join(',')}`);
 }
 console.log('PASS: specialized hubs in both cities: complete rendered DOM, full-text search, one slim request, full-data fallback');
})().catch(e=>{console.error(e);process.exitCode=1});
