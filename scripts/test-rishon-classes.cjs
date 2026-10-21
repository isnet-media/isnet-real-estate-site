const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {parseHTML}=require('linkedom');
const dir=path.resolve(__dirname,'../meusharim/rishon-lezion');
const data=JSON.parse(fs.readFileSync(path.join(dir,'data/classes.json')));
async function page(name,search=''){
 const {document,window}=parseHTML(fs.readFileSync(path.join(dir,name),'utf8'));
 for(const el of document.querySelectorAll('select'))Object.defineProperty(el,'value',{value:'',writable:true});
 const ctx={document,location:{search},URLSearchParams,console,fetch:async u=>({ok:true,json:async()=>JSON.parse(fs.readFileSync(path.join(dir,u)))})};
 const bundle=name==='course.html'?'course.js':'app.js';vm.runInNewContext(fs.readFileSync(path.join(dir,bundle),'utf8'),ctx);
 await new Promise(setImmediate);await new Promise(setImmediate);return {document,window};
}
(async()=>{
 let {document,window}=await page('index.html');assert.equal(document.querySelectorAll('#results article').length,6);assert(document.querySelector('#showResults').textContent.includes(String(data.records.length)));
 ({document,window}=await page('catalog.html','?place='+encodeURIComponent('מרכז קהילה רוזן')));assert(document.querySelector('#count').textContent.startsWith(String(data.records.filter(r=>r.place==='מרכז קהילה רוזן').length)));assert([...document.querySelectorAll('#results article')].every(x=>x.textContent.includes('רוזן')));
 const q=document.querySelector('#q');q.value='שחמט';q.dispatchEvent(new window.Event('input'));assert([...document.querySelectorAll('#results article h3')].every(x=>x.textContent.includes('שחמט')));
 const r=data.records.find(x=>x.name==='ציור'&&x.schedule.length);
 ({document}=await page('course.html','?id='+r.id));assert.equal(document.querySelector('h1').textContent,r.name);assert(document.querySelector('.detail-schedule').textContent.includes(r.schedule[0].label));assert.equal(document.querySelector('.detail-enroll').getAttribute('href'),r.source_url);
 assert(!data.records.some(r=>/יבנה|אשדוד/.test(r.place)));assert.equal(new Set(data.records.map(r=>r.id)).size,data.records.length);
 console.log('PASS: featured courses, center and text filters, internal course, labeled schedules, source inquiry and city isolation');
})().catch(e=>{console.error(e);process.exit(1)});
