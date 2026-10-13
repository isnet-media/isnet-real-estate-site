(()=>{
"use strict";
if(!location.pathname.includes('/ashdod/'))return;
const header="<header class=\"siteTopbar isnetBrandHeader\" aria-label=\"ניווט ראשי\">\n    <div class=\"siteTopbar__inner\">\n      <div class=\"isnetBrandGroup\" aria-label=\"מה עושים באשדוד מבית אשדוד נט\">\n        <a class=\"siteTopbar__brand siteTopbar__events\" href=\"./\" aria-label=\"לעמוד הראשי של מה עושים באשדוד\" title=\"לעמוד הראשי של מה עושים באשדוד\">\n          <img src=\"assets/branding/what-to-do-ashdod-dark.svg?v=20261013-brand1\" width=\"340\" height=\"158\" alt=\"מה עושים באשדוד\" decoding=\"async\">\n        </a>\n        <a class=\"siteTopbar__brand siteTopbar__ashdodnet\" href=\"https://ashdodnet.com/\" target=\"_blank\" rel=\"noopener\" aria-label=\"לעמוד הראשי של אשדוד נט\" title=\"לעמוד הראשי של אשדוד נט\">\n          <span class=\"isnetBrandByline\">מבית</span>\n          <img src=\"assets/branding/ashdodnet-dark.svg?v=20261013-brand1\" width=\"195\" height=\"82\" alt=\"אשדוד נט\" decoding=\"async\">\n        </a>\n      </div>\n      <nav class=\"isnetSiteMenu\" aria-label=\"כל אזורי האתר\">\n        <details>\n          <summary aria-label=\"פתיחת תפריט האתר\"><span class=\"isnetHamburger\" aria-hidden=\"true\"><i></i><i></i><i></i></span><span>תפריט</span></summary>\n          <div class=\"isnetSiteMenu__panel\">\n            <a class=\"isnetSiteMenu__home\" href=\"./\">עמוד הבית — כל האירועים ←</a>\n            <div class=\"isnetSiteMenu__heading\">אירועים לפי קטגוריה</div>\n            <div class=\"isnetSiteMenu__links\">\n              <a href=\"category.html?category=stage\">הופעות ומוזיקה</a>\n              <a href=\"./?category=theatre\">תיאטרון והצגות</a>\n              <a href=\"./?category=standup\">סטנדאפ ובידור</a>\n              <a href=\"category.html?category=kids\">ילדים ומשפחה</a>\n              <a href=\"cinema.html\">קולנוע וסרטים</a>\n              <a href=\"category.html?category=lecture\">הרצאות</a>\n              <a href=\"./?category=conference\">כנסים ופאנלים</a>\n              <a href=\"category.html?category=sport\">אירועי ספורט</a>\n              <a href=\"category.html?category=exhibition\">תערוכות ואמנות</a>\n\n\n              <a href=\"category.html?category=seniors\">הגיל השלישי וגמלאים</a>\n              <a href=\"./?category=food\">אוכל וקולינריה</a>\n            </div>\n            <div class=\"isnetSiteMenu__heading\">מקומות קבועים בעיר</div>\n            <div class=\"isnetSiteMenu__links\">\n              <a href=\"places.html?category=culture\">מוסדות תרבות</a>\n              <a href=\"places.html?category=parks\">פארקים</a>\n              <a href=\"places.html?category=beaches\">חופים</a>\n              <a href=\"places.html?category=nature\">טבע וטיולים</a>\n              <a href=\"places.html?category=attractions\">אטרקציות</a>\n              <a href=\"places.html?category=must-see\">מקומות שכדאי להכיר</a>\n            </div>\n          </div>\n        </details>\n      </nav>\n    </div>\n  </header>";
const topics={all:'הכול','senior-trips':'טיולים וסיורים','senior-lectures':'הרצאות והעשרה','senior-workshops':'סדנאות ויצירה','senior-culture':'תרבות ומופעים','senior-music':'מוזיקה ושירה','senior-dance':'ריקוד','senior-sport':'ספורט ותנועה','senior-health':'בריאות','senior-social':'מפגשים חברתיים','senior-digital':'דיגיטל וטכנולוגיה',other:'פעילויות נוספות'};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeUrl=s=>{if(!s)return '';try{const u=new URL(s,location.href);return ['https:','http:'].includes(u.protocol)?u.href:''}catch{return ''}};
function clock(now=new Date()){const p=Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Jerusalem',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(now).map(p=>[p.type,p.value]));return {day:p.year+'-'+p.month+'-'+p.day,time:p.hour+':'+p.minute}}
// Display shared adult lectures without changing their source category or ID.
function adultLecture(e){
 if(!e||e.category!=='lecture')return false;
 const audience=(Array.isArray(e.audiences)?e.audiences:[]).map(a=>String(a).toLowerCase());
 const young=new Set(['kids','children','youth','teens','ילדים','נוער']);
 if(audience.length&&audience.every(a=>young.has(a)))return false;
 if(e.age_max!==null&&e.age_max!==undefined&&e.age_max!==''&&Number.isFinite(Number(e.age_max))&&Number(e.age_max)<60)return false;
 if(/(?:לילדים|לנוער|לבני נוער)/.test(e.title||'')&&!/(?:להורים|הורות|סבים|סבתות)/.test(e.title||''))return false;
 return true;
}
function up60Activity(e){
 if(!e)return false;
 const organizer=[e.venue,e.venue_name,e.organizer,e.organizer_name,e.local_source_name].filter(v=>typeof v==='string').join(' ');
 return /אפ\s*60\s*\+?|up\s*60\s*\+?/i.test(organizer)||/community\.ashdod\.muni\.il\/Ashdod_up60(?:[/?#]|$)/i.test(e.content_source_url||e.source_url||'');
}
function visible(e,at=clock()){
 if(!e||!(e.category==='seniors'||adultLecture(e)||up60Activity(e))||e.is_active===false||['cancelled','canceled','inactive','hidden','draft','deleted'].includes(e.status)||['draft','hidden','unpublished','archived'].includes(e.publication_status))return false;
 if(!/^\d{4}-\d{2}-\d{2}$/.test(e.start_date||''))return false;
 const until=e.end_date&&e.end_date>=e.start_date?e.end_date:e.start_date;
 if(until<at.day)return false;
 if(until>at.day)return true;
 const time=String(e.end_time||e.start_time||'').slice(0,5);return !time||time>=at.time;
}
function mergeRows(base,overrides=[]){const map=new Map(base.filter(Boolean).map(e=>[e.event_id||e.id,e]));for(const row of overrides){const id=row?.event_id||row?.payload?.event_id;if(id&&row.payload&&(map.has(id)||row.record_type==='manual'))map.set(id,{...map.get(id),...row.payload,event_id:id})}return [...map.values()]}
const clean=s=>window.ISNET_EDITORIAL_SAFETY?.publicText?.(String(s||''))??String(s||'');
function title(e){return clean(e.title).replace(/\s*\d{1,2}[/.]\d{1,2}[/.](?:\d{4}|\d{2})\s*$/,'').trim()}
function topic(e){
 if(up60Activity(e)){
  if(e.category==='lecture')return 'senior-lectures';
  if(/דיגיטלי|רשתות חברתיות|בינה מלאכותית|\bAI\b|קאנבה|קנבה|חופשה בקליק/i.test(e.title||''))return 'senior-digital';
  if(/בריא|בריאות|זיכרון/.test(e.title||''))return 'senior-health';
  return topics[e.subcategory]?e.subcategory:'senior-workshops';
 }
 return e.category==='lecture'?'senior-lectures':topics[e.subcategory]?e.subcategory:'other';
}
function matches(e,q){return !q||[title(e),e.title,e.venue,e.address,e.description,e.series_description,e.source_description,e.local_source_name==='ofek_ashdod'?'אופק':'',topics[topic(e)]].join(' ').toLocaleLowerCase('he').includes(q.toLocaleLowerCase('he'))}
const date=s=>new Intl.DateTimeFormat('he-IL',{weekday:'long',day:'numeric',month:'long',year:'numeric'}).format(new Date(s+'T12:00:00Z'));
const month=s=>new Intl.DateTimeFormat('he-IL',{month:'long',year:'numeric'}).format(new Date(s+'-01T12:00:00Z'));
const detail=e=>'event.html?id='+encodeURIComponent(e.event_id||e.id);
function price(e){if(e.is_free===true)return 'ללא תשלום';const n=e.price_min_ils;if(n===null||n===undefined||n===''||!Number.isFinite(Number(n)))return '';return (Number(e.price_max_ils)>Number(n)?'החל מ־':'')+new Intl.NumberFormat('he-IL',{style:'currency',currency:'ILS',maximumFractionDigits:0}).format(Number(n))}
function picture(e){
 const u=safeUrl(e.thumbnail_ready&&e.thumbnail_url?e.thumbnail_url:e.image_url);
 const original=u&&e.image_verified===true&&e.image_publishable===true&&e.image_represents_event!==false&&!['illustration','source_placeholder'].includes(e.source_image_kind)&&!/\/defaults\/|\/illustrations\/|\/placeholders\/|no_pic\.png|artistShadow\.png|microsoft_oauth_logo/i.test(u);
 if(original)return {url:u,original:true};
 const bank={'senior-trips':'senior-guided-tour','senior-lectures':'senior-lecture','senior-workshops':'senior-handcraft','senior-culture':'senior-theater','senior-music':'senior-live-music','senior-dance':'senior-fitness','senior-sport':'senior-fitness','senior-social':'senior-social-coffee','senior-digital':'senior-digital'};
 // A craft illustration would misrepresent a laughter workshop; use a text panel instead.
 if(/צחוק/.test(e.title||''))return {url:'',original:false};
 return {url:bank[topic(e)]?'../shared/images/defaults/ashdod-seniors/'+bank[topic(e)]+'.webp':'',original:false};
}
function summary(e){
 const texts=[e.source_description,e.description,e.series_description].map(clean).map(t=>t.split('\n').filter(line=>!['עמוד הבית','>',e.title,'סדרת הערים המרתקות','ערים מרתקות'].includes(line.trim())).join(' ').trim());
 const text=texts.find(t=>t&&t!==e.title&&!/מועד האירוע:|שעה:|לא פורסמה|^לא נמצא תיאור$/.test(t));
 if(text)return text.replace(/<[^>]*>/g,'').replace(/\s+/g,' ').slice(0,170);
 if(topic(e)==='senior-trips')return 'טיול או סיור מודרך'+(e.local_source_name==='ofek_ashdod'?' במסגרת אופק':'')+'. פרטי המסלול וההשתתפות בעמוד הפעילות.';
 if(topic(e)==='senior-lectures')return 'מפגש הרצאות והעשרה'+(e.local_source_name==='ofek_ashdod'?' במסגרת אופק':'')+'. פרטי התוכנית וההרשמה בעמוד הפעילות.';
 if(/צחוק/.test(e.title||''))return 'סדנת צחוק בהנחיית אורית שירי, במסגרת אופק.';
 return '';
}
function readSaved(raw){try{const ids=JSON.parse(raw||'[]');return new Set(Array.isArray(ids)?ids.filter(id=>typeof id==='string'&&id.length>0&&id.length<=256).slice(0,500):[])}catch{return new Set()}}
function inPeriod(e,period,at=clock()){
 if(period==='all')return true;
 if(['soon','week','month'].includes(period)){
  if(period==='month')return e.start_date.slice(0,7)===at.day.slice(0,7);
  const end=new Date(at.day+'T12:00:00Z');end.setUTCDate(end.getUTCDate()+(period==='week'?6:29));return e.start_date>=at.day&&e.start_date<=end.toISOString().slice(0,10);
 }
 return e.start_date.startsWith(period);
}
function filterRows(rows,{active='all',q='',period='all',savedOnly=false,saved=new Set(),at=clock()}={}){return rows.filter(e=>visible(e,at)&&(active==='all'||topic(e)===active)&&matches(e,q)&&inPeriod(e,period,at)&&(!savedOnly||saved.has(e.event_id||e.id)))}
function card(e,saved=false){
 const img=picture(e),url=safeUrl(e.purchase_url||e.ticket_url),p=price(e),t=title(e),soldOut=['sold_out','soldout','sold-out'].includes(e.ticket_status);
 const trip=topic(e)==='senior-trips',unknownMeeting=/נקודת המפגש לא פורסמה/.test(e.venue||'');
 const venue=unknownMeeting?'סיור מטעם אופק':(!e.venue||e.venue==='אשדוד'?'מיקום מפורט: יש לברר עם המארגן':clean(e.venue));
 const practical=[e.meeting_point?'נקודת מפגש: '+clean(e.meeting_point):unknownMeeting?'לנקודת המפגש: יש לברר עם אופק':'',typeof e.accessibility==='string'?'נגישות: '+clean(e.accessibility):'',e.walking_level?'רמת הליכה: '+clean(e.walking_level):''].filter(Boolean);
 return '<article class="snCard" data-event-id="'+esc(e.event_id||e.id)+'"><button type="button" class="snSave" data-save="'+esc(e.event_id||e.id)+'" aria-pressed="'+saved+'" aria-label="'+esc((saved?'הסרת ':'שמירת ')+t+' '+(saved?'מהמועדפים':'למועדפים'))+'"><span aria-hidden="true">'+(saved?'♥':'♡')+'</span></button><a class="snMedia" href="'+esc(detail(e))+'" tabindex="-1" aria-hidden="true">'+(img.url?'<img src="'+esc(img.url)+'" alt="" loading="lazy" decoding="async">':'<span class="snMediaText" aria-hidden="true">'+esc(topics[topic(e)])+'</span>')+(!img.original&&img.url?'<span class="snCredit">המחשה</span>':'')+'</a><div class="snCardCopy"><h3><a href="'+esc(detail(e))+'">'+esc(trip&&!/סיור|טיול/.test(t)?'סיור: '+t:t)+'</a></h3><p class="snSummary">'+esc(summary(e))+'</p><p class="snDate">'+esc(date(e.start_date))+(e.start_time?' · <bdi>'+esc(e.start_time)+'</bdi>':'')+'</p><p class="snVenue">'+esc(venue)+'</p>'+(practical.length?'<details class="snPractical"><summary>מידע לקראת היציאה</summary><p>'+practical.map(esc).join('<br>')+'</p>'+(unknownMeeting&&e.purchase_phone&&/^[\d\s+()-]+$/.test(e.purchase_phone)?'<a href="tel:'+esc(e.purchase_phone.replace(/[^\d+]/g,''))+'">בירור בטלפון '+esc(e.purchase_phone)+'</a>':'')+'</details>':'')+'<div class="snCardBottom">'+(soldOut?'<p class="snAvailability">מצב ההרשמה הידוע: אזלו המקומות</p>':'')+(p?'<p class="snPrice">'+esc(p)+'<small>מחיר שפורסם · פרטי התשלום בהזמנה</small></p>':'')+'<div class="snActions"><a class="snButton" href="'+esc(detail(e))+'">לפרטי הפעילות ←</a>'+(url?'<a class="snBooking" href="'+esc(url)+'" target="_blank" rel="noopener">'+(soldOut?'לבדיקת זמינות באתר המארגן ↗':'לפרטים והרשמה ↗')+'</a>':'')+'</div></div></div></article>';
}
const explore=[['הצגות ותיאטרון','ערב של סיפור ובמה','category.html?category=theatre','◈'],['תערוכות ואמנות','מבט חדש במוזיאונים בעיר','category.html?category=exhibition','▧'],['חופים','ים, אוויר ורגע לעצמכם','places.html?category=beaches','≈'],['מוזיקה והופעות','למצוא את הצלילים שלכם','category.html?category=music','♫'],['קולנוע','סרט טוב על המסך הגדול','cinema.html','▣'],['פארקים וטבע','לצאת החוצה ולהחליף אווירה','places.html?category=parks','♧'],['הרצאות','סקרנות בכל גיל','category.html?category=lecture','◉'],['סטנדאפ','לצאת ולצחוק','category.html?category=standup','✧']];
async function init(){
 document.body.classList.add('seniorsPage');document.querySelector('.siteTopbar').outerHTML=header;
 document.title='גימלאים — פנאי, תרבות וטיולים באשדוד | מה עושים באשדוד';
 const root=document.querySelector('main');root.innerHTML='<p role="status">טוענים פעילויות ורעיונות לבילוי…</p>';
 try{
  const [data,cms]=await Promise.all([fetch('data/events.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('events');return r.json()}),window.ISNET_PUBLIC_CMS?.publishedEvents?.('ashdod')||Promise.resolve([])]);
  const rows=mergeRows(window.ISNET_EVENT_IDENTITIES?.reconcile?.(data.events||[])||data.events||[],cms).filter(e=>visible(e)).sort((a,b)=>(a.start_date+' '+(a.start_time||'')).localeCompare(b.start_date+' '+(b.start_time||'')));
  const months=[...new Set(rows.map(e=>e.start_date.slice(0,7)))];let active='all',savedOnly=false,saved=new Set();
  const storageKey='isnet-ashdod-seniors-saved-v1';try{saved=readSaved(localStorage.getItem(storageKey))}catch{}
  root.innerHTML='<a class="snBreadcrumb" href="./">כל הבילויים באשדוד ←</a><header class="snIntro"><div><span class="snEyebrow">זמן לדברים שאוהבים</span><h1>הבית של הגימלאים<br><em>באשדוד</em></h1><p class="snLead">לצאת, להכיר, ללמוד וליהנות.<br>כל מה שמתחשק לעשות בעיר, במקום אחד.</p><div class="snIntroLinks"><a href="#senior-activities">לפעילויות הקרובות ↓</a><a href="#senior-explore">לעוד בילויים בעיר ↓</a></div></div><figure class="snCityPhoto"><a href="places.html?category=beaches" aria-label="גלו את חופי אשדוד"><img src="https://ashdodnet.com/dyncontent/2020/1/15/fba23138-8d97-488e-8e71-8eba6f163329.jpg" alt="רצועת החוף באשדוד" fetchpriority="high" decoding="async"><span>הים תמיד קרוב<br><small>גלו את החופים בעיר ←</small></span></a><figcaption>צילום: אשדוד נט</figcaption></figure></header><section class="snExplore" id="senior-explore" aria-labelledby="snExploreTitle"><div class="snSectionHead"><h2 id="snExploreTitle">עוד דרכים ליהנות מאשדוד</h2><p>בחרו לפי מה שאתם אוהבים</p></div><nav class="snExploreGrid" aria-label="בילויים נוספים בעיר">'+explore.map(([t,d,u,i])=>'<a class="snExploreLink" href="'+u+'"><span class="snExploreIcon" aria-hidden="true">'+i+'</span><span><strong>'+t+'</strong><small>'+d+'</small></span><span class="snArrow" aria-hidden="true">←</span></a>').join('')+'</nav></section><section id="senior-activities" aria-labelledby="snActivityTitle"><div class="snSectionHead"><h2 id="snActivityTitle">הפעילויות הקרובות לגימלאים</h2><p>כל המועדים לפי סדר התאריכים</p></div><nav class="snFilters" aria-label="סינון לפי תחום עניין">'+Object.entries(topics).filter(([k])=>k==='all'||rows.some(e=>topic(e)===k)).map(([k,t])=>'<button type="button" data-topic="'+k+'" aria-pressed="'+(k==='all')+'">'+t+'</button>').join('')+'</nav><div class="snTools"><label class="snSearch"><span aria-hidden="true">⌕</span><input id="snSearch" type="search" placeholder="חפשו פעילות, מקום או מארגן" aria-label="חיפוש פעילות, מקום או מארגן"></label><label class="snMonthLabel" for="snMonth">מתי יוצאים?<select id="snMonth"><option value="all">כל החודשים</option><option value="soon">ב־30 הימים הקרובים</option><option value="week">בשבעת הימים הקרובים</option><option value="month">החודש</option>'+months.map(m=>'<option value="'+m+'">'+month(m)+'</option>').join('')+'</select></label></div><div class="snResultBar"><p id="snCount" role="status" aria-live="polite"></p><button id="snReset" type="button" hidden>ניקוי הסינון</button></div><div id="snResults"></div><div id="snEmpty" class="snEmpty" hidden><h3>לא נמצאה פעילות מתאימה לבחירה</h3><p>אפשר לבחור חודש אחר, לנקות את הסינון או לגלות עוד בילויים בעיר.</p><a href="#senior-explore">לעוד בילויים בעיר ↑</a></div></section><footer class="snFooter"><a href="./">לכל האירועים באשדוד ←</a></footer>';
  // Bring the activities forward, while keeping a short gateway to general leisure.
  const activities=root.querySelector('#senior-activities'),discovery=root.querySelector('#senior-explore');
  activities.after(discovery);
  activities.insertAdjacentHTML('beforebegin','<nav class="snCityGateway" aria-label="בילויים לכל תושבי העיר"><span>מתחשק לכם גם…</span><a href="category.html?category=theatre">הצגה ←</a><a href="category.html?category=exhibition">תערוכה ←</a><a href="places.html?category=beaches">יום ליד הים ←</a><a href="#senior-explore">כל הרעיונות ↓</a></nav>');
  activities.querySelector('.snSectionHead').insertAdjacentHTML('afterend','<div class="snHomeControls"><nav class="snPeriods" aria-label="בחירת תקופה מהירה"><button type="button" data-period="soon">הקרובים</button><button type="button" data-period="week">בשבעת הימים הקרובים</button><button type="button" data-period="month">החודש</button><button type="button" data-period="all">כל התאריכים</button></nav><button type="button" id="snSaved" aria-pressed="false">♡ המועדפים שלי</button></div><p class="snSavedHint">לחצו על הלב בכרטיסייה כדי לשמור פעילות. המועדפים נשמרים בדפדפן הזה, ללא הרשמה.</p><p id="snSaveStatus" class="snSaveStatus" role="status" aria-live="polite"></p>');
  root.querySelector('#snMonth').value='soon';
  const empty=root.querySelector('#snEmpty');
  function render(){
   const q=root.querySelector('#snSearch').value.trim(),selected=root.querySelector('#snMonth').value;
   const found=filterRows(rows,{active,q,period:selected,savedOnly,saved});
   root.querySelector('#snCount').textContent=(found.length===1?'פעילות אחת':found.length+' פעילויות')+(savedOnly?' במועדפים':'');root.querySelector('#snEmpty').hidden=found.length>0;root.querySelector('#snReset').hidden=!q&&selected==='all'&&active==='all'&&!savedOnly;
   empty.querySelector('h3').textContent=savedOnly?'עוד אין כאן פעילויות שמורות':'לא נמצאה פעילות מתאימה לבחירה';empty.querySelector('p').textContent=savedOnly?'בחרו פעילות ולחצו על הלב כדי לחזור אליה בקלות. אפשר לשמור גם פעילות בחודש רחוק יותר.':'אפשר לבחור חודש אחר, לנקות את הסינון או לגלות עוד בילויים בעיר.';
   const groups=new Map();for(const e of found){const m=e.start_date.slice(0,7);if(!groups.has(m))groups.set(m,[]);groups.get(m).push(e)}
   root.querySelector('#snResults').innerHTML=[...groups].map(([m,events])=>'<section class="snMonthGroup" aria-label="'+esc(month(m))+'"><h2>'+esc(month(m))+'</h2><div class="snCards">'+events.map(e=>card(e,saved.has(e.event_id||e.id))).join('')+'</div></section>').join('');
   root.querySelectorAll('[data-topic]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.topic===active)));
   root.querySelectorAll('[data-period]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.period===selected&&!savedOnly)));
   root.querySelector('#snSaved').setAttribute('aria-pressed',String(savedOnly));
  }
  function reset(){active='all';savedOnly=false;root.querySelector('#snSearch').value='';root.querySelector('#snMonth').value='all';render()}
  root.addEventListener('click',e=>{
   const bookmark=e.target.closest('[data-save]');if(bookmark){const id=bookmark.dataset.save;if(saved.has(id))saved.delete(id);else saved.add(id);let persisted=true;try{localStorage.setItem(storageKey,JSON.stringify([...saved]))}catch{persisted=false}render();root.querySelector('#snSaveStatus').textContent=persisted?(saved.has(id)?'הפעילות נשמרה במועדפים':'הפעילות הוסרה מהמועדפים'):'השמירה זמינה כרגע בעמוד הזה בלבד; הדפדפן לא מאפשר שמירה להמשך.';const next=[...root.querySelectorAll('[data-save]')].find(b=>b.dataset.save===id)||root.querySelector('#snSaved');next.focus({preventScroll:true});return;}
   const period=e.target.closest('[data-period]');if(period){savedOnly=false;root.querySelector('#snMonth').value=period.dataset.period;render()}
   const b=e.target.closest('[data-topic]');if(b){active=b.dataset.topic;render()}
   if(e.target.closest('#snSaved')){savedOnly=!savedOnly;active='all';root.querySelector('#snSearch').value='';root.querySelector('#snMonth').value='all';render()}
   if(e.target.closest('#snReset'))reset();
  });
  root.querySelector('#snSearch').addEventListener('input',render);root.querySelector('#snMonth').addEventListener('change',()=>{savedOnly=false;render()});render();

 }catch{root.innerHTML='<p class="snEmpty" role="alert">לא ניתן לטעון כרגע את הפעילויות. <a href="./?category=seniors">לפעילויות בעמוד הראשי ←</a></p>'}
}
window.ISNET_SENIORS={init,visible,mergeRows,matches,title,picture,price,card,readSaved,inPeriod,filterRows,adultLecture,up60Activity,topic};
})();
