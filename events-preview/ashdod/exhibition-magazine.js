(()=>{
"use strict";
const header="<header class=\"siteTopbar isnetBrandHeader\" aria-label=\"ניווט ראשי\">\n    <div class=\"siteTopbar__inner\">\n      <div class=\"isnetBrandGroup\" aria-label=\"מה עושים באשדוד מבית אשדוד נט\">\n        <a class=\"siteTopbar__brand siteTopbar__events\" href=\"./\" aria-label=\"לעמוד הראשי של מה עושים באשדוד\" title=\"לעמוד הראשי של מה עושים באשדוד\">\n          <img src=\"assets/branding/what-to-do-ashdod-dark.svg?v=20261013-brand1\" width=\"340\" height=\"158\" alt=\"מה עושים באשדוד\" decoding=\"async\">\n        </a>\n        <a class=\"siteTopbar__brand siteTopbar__ashdodnet\" href=\"https://ashdodnet.com/\" target=\"_blank\" rel=\"noopener\" aria-label=\"לעמוד הראשי של אשדוד נט\" title=\"לעמוד הראשי של אשדוד נט\">\n          <span class=\"isnetBrandByline\">מבית</span>\n          <img src=\"assets/branding/ashdodnet-dark.svg?v=20261013-brand1\" width=\"195\" height=\"82\" alt=\"אשדוד נט\" decoding=\"async\">\n        </a>\n      </div>\n      <nav class=\"isnetSiteMenu\" aria-label=\"כל אזורי האתר\">\n        <details>\n          <summary aria-label=\"פתיחת תפריט האתר\"><span class=\"isnetHamburger\" aria-hidden=\"true\"><i></i><i></i><i></i></span><span>תפריט</span></summary>\n          <div class=\"isnetSiteMenu__panel\">\n            <a class=\"isnetSiteMenu__home\" href=\"./\">עמוד הבית — כל האירועים ←</a>\n            <div class=\"isnetSiteMenu__heading\">אירועים לפי קטגוריה</div>\n            <div class=\"isnetSiteMenu__links\">\n              <a href=\"category.html?category=stage\">הופעות ומוזיקה</a>\n              <a href=\"./?category=theatre\">תיאטרון והצגות</a>\n              <a href=\"./?category=standup\">סטנדאפ ובידור</a>\n              <a href=\"category.html?category=kids\">ילדים ומשפחה</a>\n              <a href=\"cinema.html\">קולנוע וסרטים</a>\n              <a href=\"category.html?category=lecture\">הרצאות</a>\n              <a href=\"./?category=conference\">כנסים ופאנלים</a>\n              <a href=\"category.html?category=sport\">אירועי ספורט</a>\n              <a href=\"category.html?category=exhibition\">תערוכות ואמנות</a>\n\n\n              <a href=\"category.html?category=seniors\">הגיל השלישי וגמלאים</a>\n              <a href=\"./?category=food\">אוכל וקולינריה</a>\n            </div>\n            <div class=\"isnetSiteMenu__heading\">מקומות קבועים בעיר</div>\n            <div class=\"isnetSiteMenu__links\">\n              <a href=\"places.html?category=culture\">מוסדות תרבות</a>\n              <a href=\"places.html?category=parks\">פארקים</a>\n              <a href=\"places.html?category=beaches\">חופים</a>\n              <a href=\"places.html?category=nature\">טבע וטיולים</a>\n              <a href=\"places.html?category=attractions\">אטרקציות</a>\n              <a href=\"places.html?category=must-see\">מקומות שכדאי להכיר</a>\n            </div>\n          </div>\n        </details>\n      </nav>\n    </div>\n  </header>";
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeUrl=s=>{try{const u=new URL(s,location.href);return ['https:','http:'].includes(u.protocol)?u.href:''}catch{return ''}};
const admission=e=>/^כניסה לתערוכות מוזיאון אשדוד לאמנות$/.test(e.title||'');
function clock(now=new Date()){
 const p=Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Jerusalem',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(now).map(p=>[p.type,p.value]));
 return {day:p.year+'-'+p.month+'-'+p.day,time:p.hour+':'+p.minute};
}
function isVisibleOccurrence(e,at=clock()){
 if(!e||e.category!=='exhibition'||e.status==='cancelled'||e.publication_status==='draft'||e.is_active===false)return false;
 if(!/^\d{4}-\d{2}-\d{2}$/.test(e.start_date||''))return false;
 if(e.start_date<at.day)return false;
 if(e.start_date>at.day)return true;
 if(admission(e)){
  const weekday=new Date(at.day+'T12:00:00Z').getUTCDay();
  return at.time<([1,4].includes(weekday)?'20:00':[5,6].includes(weekday)?'14:00':'16:00');
 }
 const until=String(e.end_time||e.start_time||'').slice(0,5);
 return !until||until>=at.time;
}
function groupActivities(rows){
 const groups=new Map();
 for(const e of rows){
  const k=[e.title,e.venue||e.venue_name||'',e.subcategory||''].map(x=>String(x||'').normalize('NFKC').trim()).join('|');
  if(!groups.has(k))groups.set(k,{title:e.title,venue:e.venue||e.venue_name||'אשדוד',records:[]});
  groups.get(k).records.push(e);
 }
 return [...groups.values()].map(g=>({...g,records:g.records.slice().sort((a,b)=>(a.start_date+' '+(a.start_time||'')).localeCompare(b.start_date+' '+(b.start_time||'')))}));
}
function mergeRows(base,overrides){
 const map=new Map(base.filter(Boolean).map(e=>[e.event_id,e]));
 for(const row of overrides){const id=row?.event_id||row?.payload?.event_id;if(!id||!row.payload)continue;if(map.has(id)||row.record_type==='manual')map.set(id,{...map.get(id),...row.payload,event_id:id})}
 return [...map.values()];
}
const date=s=>{if(!s)return '';return new Intl.DateTimeFormat('he-IL',{day:'numeric',month:'long',year:'numeric'}).format(new Date(s+'T12:00:00Z'))};
const href=e=>'event.html?id='+encodeURIComponent(e.event_id||e.id);
const ticket=e=>safeUrl(e.purchase_url||e.ticket_url||'');
const searchMatches=(e,q)=>!q||[e.title,e.artist,e.museum,e.kind,e.description,e.venue,e.long_description,e.series_description].filter(Boolean).join(' ').toLocaleLowerCase('he').includes(q);
function price(e){if(e.is_free===true)return 'כניסה חופשית';const n=e.price_min_ils;if(n===null||n===undefined||n==='')return 'מחיר באתר ההזמנה';return (e.price_max_ils&&e.price_max_ils!==n?'החל מ־':'')+new Intl.NumberFormat('he-IL',{style:'currency',currency:'ILS',maximumFractionDigits:0}).format(Number(n))}
function period(e){return e.permanent?'תערוכת קבע':(e.opened_on?'מ־'+date(e.opened_on)+' · ':'')+(e.closes_on?'עד '+date(e.closes_on):'מועד נעילה לא פורסם')}
function artBody(e,hero=false){return '<div class="'+(hero?'exHeroCopy':'exArtCopy')+'"><span class="exEyebrow">'+esc(e.kind)+'</span><p class="exArtist">'+esc(e.artist)+'</p><'+(hero?'h2':'h3')+'>'+esc(e.title)+'</'+(hero?'h2':'h3')+'><p class="exDescription">'+esc(e.description)+'</p><p class="exPlace">'+esc(e.museum)+'</p><p class="exPeriod">'+esc(period(e))+'</p><div class="exActions">'+(e.visit==='ashdod'?'<button class="exButton" type="button" data-plan>לתכנון ביקור ←</button>':'<a class="exButton" href="'+esc(safeUrl(e.ticket_url||e.source_url))+'" target="_blank" rel="noopener">לתכנון ביקור ←</a>')+'<a class="exSource" href="'+esc(safeUrl(e.source_url))+'" target="_blank" rel="noopener">על התערוכה</a></div></div>'}
function art(e,hero=false){return '<article class="'+(hero?'exHero':'exArt')+'" data-exhibition="'+esc(e.id)+'"><figure><img src="'+esc(safeUrl(e.image))+'" alt="'+esc(e.title)+'" '+(hero?'fetchpriority="high"':'loading="lazy"')+' decoding="async"><figcaption class="exCredit">'+esc(e.credit)+'</figcaption></figure>'+artBody(e,hero)+'</article>'}
function schedule(g,id){
 if(!g?.records.length)return '<p>מועדי הביקור יתעדכנו כאן עם פרסומם.</p>';
 const first=g.records[0];
 return '<details class="exVisitDetails" id="'+id+'"><summary>בחירת מועד</summary><label for="'+id+'-select">מתי תרצו להגיע?</label><select id="'+id+'-select" data-schedule="'+id+'">'+g.records.map(e=>'<option value="'+esc(e.event_id)+'">'+esc(date(e.start_date)+(e.start_time?' · '+e.start_time:''))+'</option>').join('')+'</select><p class="exPrice" data-price="'+id+'">'+esc(price(first))+'</p><div class="exActions"><a class="exButton" data-ticket="'+id+'" href="'+esc(ticket(first)||href(first))+'"'+(ticket(first)?' target="_blank" rel="noopener"':'')+'>'+(ticket(first)?'לפרטים והזמנה ←':'לפרטי הביקור ←')+'</a><a class="exSource" data-detail="'+id+'" href="'+esc(href(first))+'">כל פרטי האירוע</a></div></details>';
}
async function init(){
 document.body.classList.add('exhibitionPage');
 document.querySelector('.siteTopbar').outerHTML=header;
 document.title='תערוכות ואמנות באשדוד | מה עושים באשדוד';
 const root=document.querySelector('main');
 root.innerHTML='<p role="status">טוענים את התערוכות והביקורים…</p>';
 try{
  const [data,catalog,cms]=await Promise.all([fetch('data/events.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('events');return r.json()}),fetch('data/exhibitions-magazine.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('catalog');return r.json()}),window.ISNET_PUBLIC_CMS?.publishedEvents?.('ashdod')||Promise.resolve([])]);
  const at=clock();
  const rows=mergeRows(data.events||[],cms).filter(e=>isVisibleOccurrence(e,at));
  const groups=groupActivities(rows),museum=groupActivities(rows.filter(admission))[0];
  const activities=groups.filter(g=>!admission(g.records[0]));
  const exhibitions=(catalog.exhibitions||[]).filter(e=>!e.closes_on||e.closes_on>=at.day);
  const validCatalog=exhibitions.filter(e=>e.permanent||!catalog.review_after||at.day<=catalog.review_after);
  root.innerHTML='<a class="exBreadcrumb" href="./">כל האירועים באשדוד ←</a><header class="exIntro"><div><span class="exEyebrow">אמנות, סיפור ומבט חדש</span><h1>תערוכות באשדוד</h1><p>קחו רגע להתבונן. גלו אמנות בעיר ותכננו את הביקור הבא שלכם.</p></div><nav class="exQuickLinks" aria-label="ניווט בעמוד התערוכות"><a href="#exhibitions-now">התערוכות</a><a href="#museum-visit">לתכנון ביקור</a><a href="#art-events">סיורים ומפגשים</a></nav></header><div class="exTools"><label class="exSearch"><span aria-hidden="true">⌕</span><input id="exSearch" type="search" placeholder="חפשו תערוכה, אמן או מוזיאון" aria-label="חיפוש תערוכה, אמן או מוזיאון"></label><span id="exCount" class="exCount" role="status" aria-live="polite"></span></div><section id="exhibitions-now" aria-label="תערוכות לביקור"><div id="exFeature"></div><div class="exSectionHead"><h2>עוד מבטים, עוד סיפורים</h2><p>כל תערוכה והעולם שהיא פותחת</p></div><div id="exGallery" class="exGallery"></div><p id="exEmpty" class="exEmpty" hidden>לא נמצאה תערוכה מתאימה לחיפוש.</p></section><section class="exVisits" id="museum-visit"><div class="exSectionHead"><h2>מתכננים ביקור במוזיאון</h2><p>כרטיס הכניסה למוזיאון אשדוד לאמנות כולל את אשכול התערוכות</p></div><div class="exVisitBox"><div><h3>מוזיאון אשדוד לאמנות</h3><p>כניסה: הגדוד העברי 12, אשדוד<br>חניון: דרך ארץ 8</p><p>א׳, ג׳, ד׳: 10:00–16:00<br>ב׳, ה׳: 10:00–20:00<br>ו׳–שבת: 10:00–14:00</p><p>בערבי חג ובחגים המוזיאון סגור.</p></div><div>'+schedule(museum,'museum-schedule')+'</div></div></section><section id="art-events"><div class="exSectionHead"><h2>סיורים ומפגשים</h2><p>להיכנס לעומק, לשאול ולהכיר מקרוב</p></div><div id="exActivities" class="exActivities"></div><p id="exActivityEmpty" class="exEmpty" hidden>לא נמצאו סיורים או מפגשים מתאימים לחיפוש.</p></section><footer class="exFooter"><a href="./">בחזרה לכל האירועים באשדוד ←</a></footer>';
  const schedules=new Map();if(museum)schedules.set('museum-schedule',museum);
  function render(){
   const q=document.querySelector('#exSearch').value.trim().toLocaleLowerCase('he');
   const artRows=validCatalog.filter(e=>searchMatches(e,q));
   const activityRows=activities.filter(g=>g.records.some(e=>searchMatches(e,q)));
   document.querySelector('#exCount').textContent=artRows.length+' תערוכות · '+activityRows.length+' סיורים ומפגשים';
   document.querySelector('#exFeature').innerHTML=artRows[0]?art(artRows[0],true):'';
   document.querySelector('#exGallery').innerHTML=artRows.slice(1).map(e=>art(e)).join('');
   document.querySelector('#exEmpty').hidden=artRows.length>0;
   document.querySelector('#exActivityEmpty').hidden=activityRows.length>0;
   document.querySelector('#exActivities').innerHTML=activityRows.map((g,i)=>{
    const e=g.records[0],id='activity-'+i;schedules.set(id,g);
    const source=e.image_verified&&e.image_publishable&&e.image_represents_event!==false?e.image_url:'';
    const image=safeUrl(source||window.isnetEventIllustration?.(e)?.src||'');
    const clean=window.ISNET_EDITORIAL_SAFETY?.publicText;
    const description=[e.description,e.series_description].map(s=>clean?clean(s):String(s||'')).find(Boolean)||'';
    const desc=description.replace(/\s+/g,' ').slice(0,180);
    return '<article class="exActivity">'+(image?'<img loading="lazy" src="'+esc(image)+'" alt="'+esc(source?g.title:'המחשה: '+g.title)+'">':'')+(!source&&image?'<small class="exCredit">המחשה</small>':'')+'<h3>'+esc(g.title)+'</h3><p>'+esc(g.venue)+'</p>'+(desc?'<p>'+esc(desc)+(desc.length===180?'…':'')+'</p>':'')+schedule(g,id)+'</article>';
   }).join('');
  }
  root.addEventListener('click',e=>{if(e.target.closest('[data-plan]')){const d=root.querySelector('#museum-schedule');if(d)d.open=true;root.querySelector('#museum-visit').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'auto':'smooth'});d?.querySelector('summary')?.focus({preventScroll:true})}});
  root.addEventListener('change',e=>{const id=e.target.dataset.schedule;if(!id)return;const event=schedules.get(id)?.records.find(x=>x.event_id===e.target.value);if(!event)return;const link=root.querySelector('[data-ticket="'+id+'"]'),url=ticket(event);link.href=url||href(event);link.textContent=url?'לפרטים והזמנה ←':'לפרטי הביקור ←';if(url){link.target='_blank';link.rel='noopener'}else{link.removeAttribute('target');link.removeAttribute('rel')}root.querySelector('[data-detail="'+id+'"]').href=href(event);root.querySelector('[data-price="'+id+'"]').textContent=price(event)});
  root.querySelector('#exSearch').addEventListener('input',render);render();
 }catch{root.innerHTML='<p class="exEmpty" role="alert">לא ניתן לטעון כרגע את התערוכות. <a href="./?category=exhibition">לרשימת האירועים ←</a></p>'}
}
window.ISNET_EXHIBITIONS={init,groupActivities,isVisibleOccurrence,mergeRows,searchMatches};
})();
