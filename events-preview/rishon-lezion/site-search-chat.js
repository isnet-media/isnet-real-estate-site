// ISNET shared layout: edit events-preview/ashdod, not this generated file.
(function(){
'use strict';
if(!/\/ashdod(?:\/|$)/.test(location.pathname))return;
const input=document.getElementById('searchInput'),submit=document.getElementById('searchSubmit'),clear=document.getElementById('clearSearch');
if(!input||!submit||!window.Worker||!window.ISNET_SEARCH_CATALOG)return;
const host=document.querySelector('.isnetNavDiscovery__search');
const panel=document.createElement('section');panel.className='siteSearchChat';panel.hidden=true;panel.setAttribute('aria-label','חיפוש בשיחה בכל האתר');
const toolbar=document.createElement('div');toolbar.className='siteSearchChat__toolbar';const heading=document.createElement('strong');heading.textContent='מחפשים יחד';const reset=document.createElement('button');reset.type='button';reset.textContent='חיפוש חדש';toolbar.append(heading,reset);
const log=document.createElement('div');log.className='siteSearchChat__log';
const status=document.createElement('p');status.setAttribute('role','status');status.setAttribute('aria-live','polite');status.className='siteSearchChat__status';
panel.append(toolbar,log,status);host.querySelector('#quickFilters')?.before(panel);if(!panel.parentNode)host.append(panel);
const style=document.createElement('style');style.textContent=`.siteSearchChat{margin:14px 0;color:#edf0f6;text-align:right}.siteSearchChat__toolbar{display:flex;align-items:center;justify-content:space-between;gap:10px}.siteSearchChat__toolbar strong{font:700 19px Heebo,Arial,sans-serif}.siteSearchChat__toolbar button{font:inherit;color:#f2d39c;background:transparent;border:1px solid #a98a52;border-radius:20px;padding:7px 13px;cursor:pointer}.siteSearchChat__log{max-height:640px;overflow:auto;overscroll-behavior:contain;padding:4px}.siteSearchChat__message{padding:10px 13px;margin:12px 0;border-radius:12px;line-height:1.7;font-size:16px;white-space:pre-line}.siteSearchChat__message--user{background:#393740;color:#fff;border-inline-start:3px solid #d0ac68}.siteSearchChat__cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.siteSearchChat__card{display:flex;flex-direction:column;gap:7px;background:#252730;border:1px solid #53545b;border-radius:13px;padding:14px;min-width:0}.siteSearchChat__card h3{font:700 18px/1.45 Heebo,Arial,sans-serif;margin:0;color:#fff}.siteSearchChat__card p{font-size:14px;line-height:1.7;color:#d0d5df;margin:0}.siteSearchChat__card small{font-size:13px;color:#f0d5a5;line-height:1.6}.siteSearchChat__card a{display:block;text-decoration:none;color:#172436;background:#efd39d;border-radius:8px;padding:9px 12px;font-weight:700;margin-top:auto}.siteSearchChat__status{font-size:14px;color:#e6d5b9;line-height:1.6}.siteSearchChat a:focus-visible,.siteSearchChat button:focus-visible{outline:3px solid #f3ca7a;outline-offset:3px}@media(max-width:600px){.siteSearchChat__cards{grid-template-columns:minmax(0,1fr)}.siteSearchChat__log{max-height:65vh}.siteSearchChat__card p{font-size:15px}}`;document.head.append(style);
let worker,readyPromise,payload,placesPromise,coursesPromise,context=null,sequence=0,failed=false,busy=false,lastQuery='',expectAge=false;
const jobs=new Map();
const json=async url=>{const r=await fetch(url);if(!r.ok)throw Error('source unavailable');return r.json()};
function fail(){failed=true;busy=false;status.textContent='החיפוש בשיחה אינו זמין כרגע. אפשר להשתמש בחיפוש הרגיל ובקטגוריות.';worker?.terminate();for(const j of jobs.values()){clearTimeout(j.timer);j.reject(Error('worker unavailable'))}jobs.clear()}
async function ensure(){
 if(readyPromise)return readyPromise;
 readyPromise=(async()=>{
  const started=Date.now();while(!window.ISNET_SEARCH_CATALOG()?.events?.length){if(Date.now()-started>15000)throw Error('catalog unavailable');await new Promise(r=>setTimeout(r,200))}
  const base=window.ISNET_SEARCH_CATALOG();
  placesPromise=placesPromise||json('data/places.json').catch(()=>null);
  const [places,saturdayGuide]=await Promise.all([placesPromise,json('data/saturday-guide.json?v=20261015-1').catch(()=>null)]);payload={...base,places,saturdayGuide};
  worker=new Worker('site-search-engine.js?v=20261015-saturday2');worker.onerror=fail;
  worker.onmessage=e=>{const data=e.data;if(data.kind==='ready'){const job=jobs.get('init');if(job){clearTimeout(job.timer);jobs.delete('init');job.resolve(data)}return}const job=jobs.get(data.id);if(!job)return;clearTimeout(job.timer);jobs.delete(data.id);if(data.kind==='error')job.reject(Error('search failed'));else job.resolve(data)};
  await initialize();if(!places)status.textContent='מידע על מקומות קבועים לא נטען; החיפוש זמין באירועים ובקולנוע.';
 })().catch(e=>{fail();throw e});return readyPromise;
}
function initialize(){return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{jobs.delete('init');reject(Error('index timeout'))},15000);jobs.set('init',{resolve,reject,timer});worker.postMessage({kind:'init',payload})})}
function message(text,user){const p=document.createElement('p');p.className='siteSearchChat__message'+(user?' siteSearchChat__message--user':'');p.textContent=text;log.append(p);return p}
const types={event:'אירוע',movie:'סרט',place:'מקום או אטרקציה',course:'חוג'};
function cards(items){const grid=document.createElement('div');grid.className='siteSearchChat__cards';for(const r of items){const card=document.createElement('article');card.className='siteSearchChat__card';const category=document.createElement('small');category.textContent=[types[r.type],r.category,r.subcategory].filter(Boolean).filter((v,i,a)=>a.indexOf(v)===i).join(' · ');const h=document.createElement('h3');h.textContent=r.title;card.append(category,h);if(r.description){const p=document.createElement('p');p.textContent=r.description+(r.description.length>=240?'…':'');card.append(p)}const facts=document.createElement('p');facts.textContent=[r.venue,r.date?new Date(r.date+'T12:00:00').toLocaleDateString('he-IL'):null,r.time,r.price==null?'מחיר לא צוין':r.price===0?'חינם':'החל מ־'+r.price+' ₪'].filter(Boolean).join(' · ');card.append(facts);if(r.reasons.length){const why=document.createElement('small');why.textContent='התאמה לפי התוכן: '+r.reasons.join(' · ');card.append(why)}for(const note of r.notes){const n=document.createElement('small');n.textContent=note;card.append(n)}const a=document.createElement('a');a.href=r.href;a.textContent=r.type==='movie'?'לפרטי הסרט וההקרנות ←':r.type==='course'?'לפרטי החוג והרשמה ←':r.type==='place'?'לפרטי המקום ←':'לפרטי האירוע והזמנה ←';card.append(a);grid.append(card)}log.append(grid)}
async function run(){
 const raw=input.value.trim().slice(0,500);if(!raw||busy)return;
 if(/^(?:מה (?:לעשות|עושים|יש לעשות|אפשר לעשות)|מה פתוח|פתוח)\s+ב?שבת(?:\s+בראשון לציון)?[?!.]*$/.test(raw)){location.href='saturday.html'+(/בראשון לציון/.test(raw)?'?area=ashdod':'');return}
 panel.hidden=false;const feedback=document.getElementById('searchFeedback');if(feedback)feedback.hidden=true;
 busy=true;reset.disabled=true;if(clear)clear.disabled=true;lastQuery=raw;message(raw,true);status.textContent='מחפש בתיאורים, בתתי־הקטגוריות ובמועדים שבאתר…';
 try{
  await ensure();
  if(/חוג|קורס/.test(raw)&&!payload.courses){coursesPromise=coursesPromise||json('/meusharim/ashdod/data/classes.json');payload.courses=(await coursesPromise).records||[];await initialize()}
  const query=expectAge&&/^(?:\d{1,2}|שנתיים|שלוש|ארבע|חמש|שש|שבע|שמונה|תשע|עשר)$/.test(raw)?'בן '+raw:raw;
  const now=new Date(),day=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Jerusalem',year:'numeric',month:'2-digit',day:'2-digit'}).format(now),parts=new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Jerusalem',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(now).split(':');
  const id=++sequence;const result=await new Promise((resolve,reject)=>{const timer=setTimeout(()=>{jobs.delete(id);reject(Error('search timeout'))},10000);jobs.set(id,{resolve,reject,timer});worker.postMessage({kind:'search',id,query,context,day,nowMinutes:Number(parts[0])*60+Number(parts[1])})});
  context=result.context;expectAge=result.needsAge;
  if(context.reset){context=null;expectAge=false;message('החיפוש אופס. מה מחפשים עכשיו?');status.textContent='';return}
  const constraints=[context.family===true?'לילדים ולמשפחה':context.family===false?'למבוגרים':null,context.age!=null?'גיל '+context.age:null,context.period?({today:'היום',tomorrow:'מחר',saturday:'בשבת',friday:'בשישי',weekend:'בסוף השבוע',week:'השבוע'})[context.period]:null,context.maxPrice!=null?'עד '+context.maxPrice+' ₪':null,context.after!=null?'אחרי '+String(Math.floor(context.after/60)).padStart(2,'0')+':'+String(context.after%60).padStart(2,'0'):null].filter(Boolean);
  if(result.count){message('מצאתי '+result.count+' אפשרויות'+(constraints.length?' לפי: '+constraints.join(' · '):'')+'.'+(result.count>12?' מוצגות 12 התוצאות הראשונות.':''));cards(result.results)}else message('לא נמצאה התאמה במידע הזמין באתר'+(constraints.length?' לפי: '+constraints.join(' · '):'')+'. אפשר לשנות תאריך, תקציב או נושא. מקומות קבועים וחוגים אינם מוצגים לפי יום מסוים בלי מידע מאומת על מועדים.');
  if(expectAge)message('בני כמה הילדים? אפשר לכתוב כאן גיל, ואדייק את החיפוש.');
  status.textContent='אפשר להמשיך באותו חיפוש: „רק בשבת”, „אחרי 16:00” או „עד 100 שקל”. התשובות מבוססות על מאגר האתר; מידע חסר אינו מושלם בניחוש.';
  input.value='';input.placeholder='אפשר להמשיך לדייק כאן…';
  const tail=log.lastElementChild;if(tail)log.scrollTop=log.scrollHeight-tail.offsetHeight;
 }catch(_){fail()}finally{busy=false;reset.disabled=false;if(clear)clear.disabled=false}
}
function enabled(){return !failed&&typeof window.ISNET_SEARCH_CATALOG==='function'}
input.addEventListener('input',e=>{if(!enabled())return;e.stopImmediatePropagation()},true);
input.addEventListener('keydown',e=>{if(e.key!=='Enter'||!enabled())return;e.preventDefault();e.stopImmediatePropagation();run()},true);
submit.addEventListener('click',e=>{if(!enabled())return;e.preventDefault();e.stopImmediatePropagation();run()},true);
function newSearch(){context=null;expectAge=false;lastQuery='';log.replaceChildren();panel.hidden=true;input.value='';input.placeholder='כתוב בצורה חופשית, מה אתה מחפש';status.textContent='';input.focus()}
reset.onclick=newSearch;clear?.addEventListener('click',e=>{if(!enabled())return;e.stopImmediatePropagation();newSearch()},true);
})();

