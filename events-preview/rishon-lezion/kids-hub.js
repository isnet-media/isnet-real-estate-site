// ISNET shared layout: edit events-preview/ashdod, not this generated file.
(()=>{
"use strict";
if(!location.pathname.includes('/ashdod/'))return;
const header="<header class=\"siteTopbar isnetBrandHeader\" aria-label=\"ניווט ראשי\">\n    <div class=\"siteTopbar__inner\">\n      <div class=\"isnetBrandGroup\" aria-label=\"מה עושים בראשון לציון מבית ראשון נט\">\n        <a class=\"siteTopbar__brand siteTopbar__events\" href=\"./\" aria-label=\"לעמוד הראשי של מה עושים בראשון לציון\" title=\"לעמוד הראשי של מה עושים בראשון לציון\">\n          <img src=\"assets/branding/what-to-do-ashdod-dark.svg?v=20261013-brand1\" width=\"340\" height=\"158\" alt=\"מה עושים בראשון לציון\" decoding=\"async\">\n        </a>\n        <a class=\"siteTopbar__brand siteTopbar__ashdodnet\" href=\"https://www.rishonet.com/\" target=\"_blank\" rel=\"noopener\" aria-label=\"לעמוד הראשי של ראשון נט\" title=\"לעמוד הראשי של ראשון נט\">\n          <span class=\"isnetBrandByline\">מבית</span>\n          <img src=\"assets/branding/ashdodnet-dark.svg?v=20261013-brand1\" width=\"195\" height=\"82\" alt=\"ראשון נט\" decoding=\"async\">\n        </a>\n      </div>\n      <nav class=\"isnetSiteMenu\" aria-label=\"כל אזורי האתר\">\n        <details>\n          <summary aria-label=\"פתיחת תפריט האתר\"><span class=\"isnetHamburger\" aria-hidden=\"true\"><i></i><i></i><i></i></span><span>תפריט</span></summary>\n          <div class=\"isnetSiteMenu__panel\">\n            <a class=\"isnetSiteMenu__home\" href=\"./\">עמוד הבית — כל האירועים ←</a>\n            <div class=\"isnetSiteMenu__heading\">אירועים לפי קטגוריה</div>\n            <div class=\"isnetSiteMenu__links\">\n              <a href=\"category.html?category=stage\">הופעות ומוזיקה</a>\n              <a href=\"./?category=theatre\">תיאטרון והצגות</a>\n              <a href=\"./?category=standup\">סטנדאפ ובידור</a>\n              <a href=\"category.html?category=kids\">ילדים ומשפחה</a>\n              <a href=\"cinema.html\">קולנוע וסרטים</a>\n              <a href=\"category.html?category=lecture\">הרצאות</a>\n              <a href=\"category.html?category=sport\">אירועי ספורט</a>\n              <a href=\"category.html?category=exhibition\">תערוכות ואמנות</a>\n\n\n              <a href=\"category.html?category=seniors\">הגיל השלישי וגמלאים</a>\n              <a href=\"./?category=food\">אוכל וקולינריה</a>\n            </div>\n            <div class=\"isnetSiteMenu__heading\">מקומות קבועים בעיר</div>\n            <div class=\"isnetSiteMenu__links\">\n              <a href=\"places.html?category=culture\">מוסדות תרבות</a>\n              <a href=\"places.html?category=parks\">פארקים</a>\n              <a href=\"places.html?category=beaches\">חופים</a>\n              <a href=\"places.html?category=nature\">טבע וטיולים</a>\n              <a href=\"places.html?category=attractions\">אטרקציות</a>\n              <a href=\"places.html?category=must-see\">מקומות שכדאי להכיר</a>\n            </div>\n          </div>\n        </details>\n      </nav>\n    </div>\n  </header>";
const topics={all:'הכול',theatre:'הצגות ומופעים',stories:'שעת סיפור',creative:'יצירה וסדנאות',outdoor:'בחוץ ובטבע',family:'פעילויות משפחתיות'};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeUrl=s=>{if(!s)return '';try{const u=new URL(s,location.href);return ['https:','http:'].includes(u.protocol)?u.href:''}catch{return ''}};
function clock(now=new Date()){const p=Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Jerusalem',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(now).map(p=>[p.type,p.value]));return {day:p.year+'-'+p.month+'-'+p.day,time:p.hour+':'+p.minute}}
// Share explicitly child/family activities; a family-themed adult play is not enough.
function forKids(e){
 if(!e)return false;
 const text=[e.title,e.organizer,e.organizer_name,e.local_source_name].filter(Boolean).join(' ');
 if(/גדולות מהחיים|אפ\s*60|up\s*60/i.test(text)||e.category==='seniors')return false;
 if(e.category==='kids'||/^kids-|^story-time$/.test(e.subcategory||''))return true;
 if(/לילדים|לקטנטנים|לכל המשפחה|למשפחות|להורים ולילדים|הורים וילדים/.test(e.title||''))return true;
 return (Array.isArray(e.audiences)?e.audiences:[]).some(a=>['kids','children','families','ילדים','משפחות'].includes(String(a).toLowerCase()));
}
function visible(e,at=clock()){
 if(!e||!forKids(e)||e.is_active===false||['cancelled','canceled','inactive','hidden','draft','deleted'].includes(e.status)||['draft','hidden','unpublished','archived'].includes(e.publication_status))return false;
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
 const t=e.title||'',sub=e.subcategory||'';
 if(/שעת סיפור|סיפור עם רינתי/.test(t)||sub==='story-time')return 'stories';
 if(/סדנ|יצירה|ציור|מצייר|כתיבה/.test(t)||sub==='kids-workshops')return 'creative';
 if(/פיקניק|חוף|טבע|סיור|בישול שטח/.test(t))return 'outdoor';
 if(/הצג|מופע|מחזמר|בלט/.test(t)||['kids-theatre','kids-shows'].includes(sub))return 'theatre';
 return 'family';
}
function matches(e,q){return !q||[title(e),e.title,e.venue,e.address,e.description,e.series_description,e.source_description,e.local_source_name==='ofek_ashdod'?'אופק':'',topics[topic(e)]].join(' ').toLocaleLowerCase('he').includes(q.toLocaleLowerCase('he'))}
const date=s=>new Intl.DateTimeFormat('he-IL',{weekday:'long',day:'numeric',month:'long',year:'numeric'}).format(new Date(s+'T12:00:00Z'));
const month=s=>new Intl.DateTimeFormat('he-IL',{month:'long',year:'numeric'}).format(new Date(s+'-01T12:00:00Z'));
const detail=e=>'event.html?id='+encodeURIComponent(e.event_id||e.id);
function price(e){if(e.is_free===true)return 'ללא תשלום';const n=e.price_min_ils;if(n===null||n===undefined||n===''||!Number.isFinite(Number(n)))return '';return (Number(e.price_max_ils)>Number(n)?'החל מ־':'')+new Intl.NumberFormat('he-IL',{style:'currency',currency:'ILS',maximumFractionDigits:0}).format(Number(n))}
function picture(e){
 const u=safeUrl(e.thumbnail_ready&&e.thumbnail_url?e.thumbnail_url:e.image_url);
 if(u&&e.image_verified===true&&e.image_publishable===true&&e.image_represents_event!==false&&!['illustration','source_placeholder'].includes(e.source_image_kind)&&!/\/defaults\/|\/illustrations\/|\/placeholders\/|no_pic\.png|artistShadow\.png|microsoft_oauth_logo/i.test(u))return {url:u,original:true};
 const fallback=window.isnetEventIllustration?.({...e,category:'kids'});
 return {url:fallback?.src||'',original:false};
}
function summary(e){
 const texts=[e.source_description,e.description,e.series_description].map(clean).map(t=>t.split('\n').filter(line=>!['עמוד הבית','>',e.title,'סדרת הערים המרתקות','ערים מרתקות'].includes(line.trim())).join(' ').trim());
 const text=texts.find(t=>t&&t!==e.title&&!/מועד האירוע:|שעה:|לא פורסמה|^לא נמצא תיאור$/.test(t));
 if(text)return text.replace(/<[^>]*>/g,'').replace(/\s+/g,' ').slice(0,170);
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
 const unknownMeeting=/נקודת המפגש לא פורסמה/.test(e.venue||'');
 const venue=unknownMeeting?'נקודת מפגש: יש לברר עם המארגן':(!e.venue||e.venue==='ראשון לציון'?'מיקום מפורט: יש לברר עם המארגן':clean(e.venue));
 const practical=[e.meeting_point?'נקודת מפגש: '+clean(e.meeting_point):unknownMeeting?'לנקודת המפגש: יש לברר עם המארגן':'',typeof e.accessibility==='string'?'נגישות: '+clean(e.accessibility):'',e.walking_level?'רמת הליכה: '+clean(e.walking_level):''].filter(Boolean);
 const age=[e.age_min,e.age_max].filter(v=>v!==null&&v!==undefined&&v!==''&&Number.isFinite(Number(v))); const ageText=age.length===2?'גילאים '+age[0]+'–'+age[1]:age.length?(e.age_min!==null&&e.age_min!==undefined?'מגיל '+age[0]:'עד גיל '+age[0]):'';
 return '<article class="kdCard" data-event-id="'+esc(e.event_id||e.id)+'"><button type="button" class="kdSave" data-save="'+esc(e.event_id||e.id)+'" aria-pressed="'+saved+'" aria-label="'+esc((saved?'הסרת ':'שמירת ')+t+' '+(saved?'מהמועדפים':'למועדפים'))+'"><span aria-hidden="true">'+(saved?'♥':'♡')+'</span></button><a class="kdMedia" href="'+esc(detail(e))+'" tabindex="-1" aria-hidden="true">'+(img.url?'<img src="'+esc(img.url)+'" alt="" loading="lazy" decoding="async">':'<span class="kdMediaText" aria-hidden="true">'+esc(topics[topic(e)])+'</span>')+(!img.original&&img.url?'<span class="kdCredit">המחשה</span>':'')+'</a><div class="kdCardCopy"><h3><a href="'+esc(detail(e))+'">'+esc(t)+'</a></h3><p class="kdSummary">'+esc(summary(e))+'</p><p class="kdDate">'+esc(date(e.start_date))+(e.start_time?' · <bdi>'+esc(e.start_time)+'</bdi>':'')+'</p><p class="kdVenue">'+esc(venue)+'</p>'+(ageText?'<p class="kdAge">'+esc(ageText)+'</p>':'')+(practical.length?'<details class="kdPractical"><summary>מידע לקראת היציאה</summary><p>'+practical.map(esc).join('<br>')+'</p>'+(unknownMeeting&&e.purchase_phone&&/^[\d\s+()-]+$/.test(e.purchase_phone)?'<a href="tel:'+esc(e.purchase_phone.replace(/[^\d+]/g,''))+'">בירור בטלפון '+esc(e.purchase_phone)+'</a>':'')+'</details>':'')+'<div class="kdCardBottom">'+(soldOut?'<p class="kdAvailability">מצב ההרשמה הידוע: אזלו המקומות</p>':'')+(p?'<p class="kdPrice">'+esc(p)+'<small>מחיר שפורסם · פרטי התשלום בהזמנה</small></p>':'')+'<div class="kdActions"><a class="kdButton" href="'+esc(detail(e))+'">לפרטי הפעילות ←</a>'+(url?'<a class="kdBooking" href="'+esc(url)+'" target="_blank" rel="noopener">'+(soldOut?'לבדיקת זמינות באתר המארגן ↗':'לפרטים והרשמה ↗')+'</a>':'')+'</div></div></div></article>';
}
const explore=[['פארקים ומשחקים','מרחב לרוץ, לשחק ולבלות','places.html?category=parks','♧'],['חופים וטיילת','חול, אוויר ים וזמן ביחד','places.html?category=beaches','≈'],['אטרקציות','למצוא את ההרפתקה הבאה','places.html?category=attractions','✧'],['קולנוע','לבחור סרט שמתאים לילדים','cinema.html','▣'],['מוזיאונים ותערוכות','יום של סקרנות ואמנות','category.html?category=exhibition','▧'],['טבע בעיר','לגלות את ראשון לציון ברגל','places.html?category=nature','❋']];
async function init(){
 document.body.classList.add('kidsPage');document.querySelector('.siteTopbar').outerHTML=header;
 document.title='ילדים בראשון לציון — פעילויות, הצגות ובילוי משפחתי | מה עושים בראשון לציון';
 const root=document.querySelector('main');root.innerHTML='<p role="status">טוענים פעילויות ורעיונות לבילוי…</p>';
 try{
  const [data,cms]=await Promise.all([fetch('data/events.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('events');return r.json()}),window.ISNET_PUBLIC_CMS?.publishedEvents?.('ashdod')||Promise.resolve([])]);
  const rows=mergeRows(window.ISNET_EVENT_IDENTITIES?.reconcile?.(data.events||[])||data.events||[],cms).filter(e=>visible(e)).sort((a,b)=>(a.start_date+' '+(a.start_time||'')).localeCompare(b.start_date+' '+(b.start_time||'')));
  const months=[...new Set(rows.map(e=>e.start_date.slice(0,7)))];let active='all',savedOnly=false,saved=new Set();
  const storageKey='isnet-ashdod-kids-saved-v1';try{saved=readSaved(localStorage.getItem(storageKey))}catch{}
  root.innerHTML='<a class="kdBreadcrumb" href="./">כל הבילויים בראשון לציון ←</a><header class="kdIntro"><div><span class="kdEyebrow">הרפתקאות קטנות. זיכרונות גדולים.</span><h1>העולם של הילדים<br><em>בראשון לציון</em></h1><p class="kdLead">הצגות, סיפורים, יצירה ובילוי בחוץ.<br>כל הרעיונות לזמן איכות עם הילדים.</p><div class="kdIntroLinks"><a href="#kids-activities">לפעילויות הקרובות ↓</a><a href="#kids-explore">לעוד בילויים בעיר ↓</a></div></div><figure class="kdCityPhoto"><a href="places.html?category=parks" aria-label="גלו את הפארקים בראשון לציון"><img src="https://www.rishonet.com/dyncontent/2022/10/1/df3cc426-a76e-490b-97b4-0c6285036265.jpg" alt="פארק ראשון לציון ים" fetchpriority="high" decoding="async"><span>יוצאים לשחק<br><small>גלו את הפארקים בעיר ←</small></span></a><figcaption>צילום: יהודה אברהם זייקא / ראשון נט</figcaption></figure></header><section class="kdExplore" id="kids-explore" aria-labelledby="kdExploreTitle"><div class="kdSectionHead"><h2 id="kdExploreTitle">גם בלי אירוע: יוצאים עם הילדים</h2><p>פארקים, ים, תרבות ורעיונות לבילוי משפחתי</p></div><nav class="kdExploreGrid" aria-label="בילויים נוספים בעיר">'+explore.map(([t,d,u,i])=>'<a class="kdExploreLink" href="'+u+'"><span class="kdExploreIcon" aria-hidden="true">'+i+'</span><span><strong>'+t+'</strong><small>'+d+'</small></span><span class="kdArrow" aria-hidden="true">←</span></a>').join('')+'</nav></section><section id="kids-activities" aria-labelledby="kdActivityTitle"><div class="kdSectionHead"><h2 id="kdActivityTitle">מה עושים עם הילדים?</h2><p>כל המועדים לפי סדר התאריכים</p></div><nav class="kdFilters" aria-label="סינון לפי תחום עניין">'+Object.entries(topics).filter(([k])=>k==='all'||rows.some(e=>topic(e)===k)).map(([k,t])=>'<button type="button" data-topic="'+k+'" aria-pressed="'+(k==='all')+'">'+t+'</button>').join('')+'</nav><div class="kdTools"><label class="kdSearch"><span aria-hidden="true">⌕</span><input id="kdSearch" type="search" placeholder="חפשו פעילות, מקום או מארגן" aria-label="חיפוש פעילות, מקום או מארגן"></label><label class="kdMonthLabel" for="kdMonth">מתי יוצאים?<select id="kdMonth"><option value="all">כל החודשים</option><option value="soon">ב־30 הימים הקרובים</option><option value="week">בשבעת הימים הקרובים</option><option value="month">החודש</option>'+months.map(m=>'<option value="'+m+'">'+month(m)+'</option>').join('')+'</select></label></div><div class="kdResultBar"><p id="kdCount" role="status" aria-live="polite"></p><button id="kdReset" type="button" hidden>ניקוי הסינון</button></div><div id="kdResults"></div><div id="kdEmpty" class="kdEmpty" hidden><h3>לא נמצאה פעילות מתאימה לבחירה</h3><p>אפשר לבחור חודש אחר, לנקות את הסינון או לגלות עוד בילויים בעיר.</p><a href="#kids-explore">לעוד בילויים בעיר ↑</a></div></section><footer class="kdFooter"><a href="./">לכל האירועים בראשון לציון ←</a></footer>';
  // Bring the activities forward, while keeping a short gateway to general leisure.
  const activities=root.querySelector('#kids-activities'),discovery=root.querySelector('#kids-explore');
  activities.after(discovery);
  activities.insertAdjacentHTML('beforebegin','<nav class="kdCityGateway" aria-label="בילויים משפחתיים בעיר"><span>יוצאים להרפתקה?</span><a href="places.html?category=parks">פארק ←</a><a href="places.html?category=attractions">אטרקציה ←</a><a href="places.html?category=beaches">יום ליד הים ←</a><a href="#kids-explore">כל הרעיונות ↓</a></nav>');
  activities.querySelector('.kdSectionHead').insertAdjacentHTML('afterend','<div class="kdHomeControls"><nav class="kdPeriods" aria-label="בחירת תקופה מהירה"><button type="button" data-period="soon">הקרובים</button><button type="button" data-period="week">בשבעת הימים הקרובים</button><button type="button" data-period="month">החודש</button><button type="button" data-period="all">כל התאריכים</button></nav><button type="button" id="kdSaved" aria-pressed="false">♡ המועדפים שלי</button></div><p class="kdSavedHint">לחצו על הלב בכרטיסייה כדי לשמור פעילות. המועדפים נשמרים בדפדפן הזה, ללא הרשמה.</p><p id="kdSaveStatus" class="kdSaveStatus" role="status" aria-live="polite"></p>');
  root.querySelector('#kdMonth').value='soon';
  const empty=root.querySelector('#kdEmpty');
  function render(){
   const q=root.querySelector('#kdSearch').value.trim(),selected=root.querySelector('#kdMonth').value;
   const found=filterRows(rows,{active,q,period:selected,savedOnly,saved});
   root.querySelector('#kdCount').textContent=(found.length===1?'פעילות אחת':found.length+' פעילויות')+(savedOnly?' במועדפים':'');root.querySelector('#kdEmpty').hidden=found.length>0;root.querySelector('#kdReset').hidden=!q&&selected==='all'&&active==='all'&&!savedOnly;
   empty.querySelector('h3').textContent=savedOnly?'עוד אין כאן פעילויות שמורות':'לא נמצאה פעילות מתאימה לבחירה';empty.querySelector('p').textContent=savedOnly?'בחרו פעילות ולחצו על הלב כדי לחזור אליה בקלות. אפשר לשמור גם פעילות בחודש רחוק יותר.':'אפשר לבחור חודש אחר, לנקות את הסינון או לגלות עוד בילויים בעיר.';
   const groups=new Map();for(const e of found){const m=e.start_date.slice(0,7);if(!groups.has(m))groups.set(m,[]);groups.get(m).push(e)}
   root.querySelector('#kdResults').innerHTML=[...groups].map(([m,events])=>'<section class="kdMonthGroup" aria-label="'+esc(month(m))+'"><h2>'+esc(month(m))+'</h2><div class="kdCards">'+events.map(e=>card(e,saved.has(e.event_id||e.id))).join('')+'</div></section>').join('');
   root.querySelectorAll('[data-topic]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.topic===active)));
   root.querySelectorAll('[data-period]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.period===selected&&!savedOnly)));
   root.querySelector('#kdSaved').setAttribute('aria-pressed',String(savedOnly));
  }
  function reset(){active='all';savedOnly=false;root.querySelector('#kdSearch').value='';root.querySelector('#kdMonth').value='all';render()}
  root.addEventListener('click',e=>{
   const bookmark=e.target.closest('[data-save]');if(bookmark){const id=bookmark.dataset.save;if(saved.has(id))saved.delete(id);else saved.add(id);let persisted=true;try{localStorage.setItem(storageKey,JSON.stringify([...saved]))}catch{persisted=false}render();root.querySelector('#kdSaveStatus').textContent=persisted?(saved.has(id)?'הפעילות נשמרה במועדפים':'הפעילות הוסרה מהמועדפים'):'השמירה זמינה כרגע בעמוד הזה בלבד; הדפדפן לא מאפשר שמירה להמשך.';const next=[...root.querySelectorAll('[data-save]')].find(b=>b.dataset.save===id)||root.querySelector('#kdSaved');next.focus({preventScroll:true});return;}
   const period=e.target.closest('[data-period]');if(period){savedOnly=false;root.querySelector('#kdMonth').value=period.dataset.period;render()}
   const b=e.target.closest('[data-topic]');if(b){active=b.dataset.topic;render()}
   if(e.target.closest('#kdSaved')){savedOnly=!savedOnly;active='all';root.querySelector('#kdSearch').value='';root.querySelector('#kdMonth').value='all';render()}
   if(e.target.closest('#kdReset'))reset();
  });
  root.querySelector('#kdSearch').addEventListener('input',render);root.querySelector('#kdMonth').addEventListener('change',()=>{savedOnly=false;render()});render();

 }catch{root.innerHTML='<p class="kdEmpty" role="alert">לא ניתן לטעון כרגע את הפעילויות. <a href="./?category=kids">לפעילויות ילדים בעמוד הראשי ←</a></p>'}
}
window.ISNET_KIDS={init,visible,mergeRows,matches,title,picture,price,card,readSaved,inPeriod,filterRows,forKids,topic};
})();
