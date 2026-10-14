// ISNET shared layout: edit events-preview/ashdod, not this generated file.
(()=>{
"use strict";
if(!location.pathname.includes('/ashdod/'))return;
const header="<header class=\"siteTopbar isnetBrandHeader\" aria-label=\"ניווט ראשי\">\n    <div class=\"siteTopbar__inner\">\n      <div class=\"isnetBrandGroup\" aria-label=\"מה עושים בראשון לציון מבית ראשון נט\">\n        <a class=\"siteTopbar__brand siteTopbar__events\" href=\"./\" aria-label=\"לעמוד הראשי של מה עושים בראשון לציון\" title=\"לעמוד הראשי של מה עושים בראשון לציון\">\n          <img src=\"assets/branding/what-to-do-ashdod-dark.svg?v=20261013-brand1\" width=\"340\" height=\"158\" alt=\"מה עושים בראשון לציון\" decoding=\"async\">\n        </a>\n        <a class=\"siteTopbar__brand siteTopbar__ashdodnet\" href=\"https://www.rishonet.com/\" target=\"_blank\" rel=\"noopener\" aria-label=\"לעמוד הראשי של ראשון נט\" title=\"לעמוד הראשי של ראשון נט\">\n          <span class=\"isnetBrandByline\">מבית</span>\n          <img src=\"assets/branding/ashdodnet-dark.svg?v=20261013-brand1\" width=\"195\" height=\"82\" alt=\"ראשון נט\" decoding=\"async\">\n        </a>\n      </div>\n      <nav class=\"isnetSiteMenu\" aria-label=\"כל אזורי האתר\">\n        <details>\n          <summary aria-label=\"פתיחת תפריט האתר\"><span class=\"isnetHamburger\" aria-hidden=\"true\"><i></i><i></i><i></i></span><span>תפריט</span></summary>\n          <div class=\"isnetSiteMenu__panel\">\n            <a class=\"isnetSiteMenu__home\" href=\"./\">עמוד הבית — כל האירועים ←</a>\n            <div class=\"isnetSiteMenu__heading\">אירועים לפי קטגוריה</div>\n            <div class=\"isnetSiteMenu__links\">\n              <a href=\"category.html?category=stage\">הופעות ומוזיקה</a>\n              <a href=\"./?category=theatre\">תיאטרון והצגות</a>\n              <a href=\"./?category=standup\">סטנדאפ ובידור</a>\n              <a href=\"category.html?category=kids\">ילדים ומשפחה</a>\n              <a href=\"cinema.html\">קולנוע וסרטים</a>\n              <a href=\"category.html?category=lecture\">הרצאות</a>\n              <a href=\"category.html?category=sport\">אירועי ספורט</a>\n              <a href=\"category.html?category=exhibition\">תערוכות ואמנות</a>\n\n\n              <a href=\"category.html?category=seniors\">הגיל השלישי וגמלאים</a>\n              \n            </div>\n            <div class=\"isnetSiteMenu__heading\">מקומות קבועים בעיר</div>\n            <div class=\"isnetSiteMenu__links\">\n              <a href=\"places.html?category=culture\">מוסדות תרבות</a>\n              <a href=\"places.html?category=parks\">פארקים</a>\n              <a href=\"places.html?category=beaches\">חופים</a>\n              <a href=\"places.html?category=nature\">טבע וטיולים</a>\n              <a href=\"places.html?category=attractions\">אטרקציות</a>\n              <a href=\"places.html?category=must-see\">מקומות שכדאי להכיר</a>\n            </div>\n          </div>\n        </details>\n      </nav>\n    </div>\n  </header>";
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
 if(period==='today')return e.start_date===at.day;
 if(period==='weekend'){const start=new Date(at.day+'T12:00:00Z'),day=start.getUTCDay();start.setUTCDate(start.getUTCDate()+(day===6?-1:(5-day+7)%7));const end=new Date(start);end.setUTCDate(end.getUTCDate()+1);return e.start_date>=at.day&&e.start_date>=start.toISOString().slice(0,10)&&e.start_date<=end.toISOString().slice(0,10);}
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
 return '<article class="kdCard" data-event-id="'+esc(e.event_id||e.id)+'"><button type="button" class="kdSave" data-save="'+esc(e.event_id||e.id)+'" aria-pressed="'+saved+'" aria-label="'+esc((saved?'הסרת ':'שמירת ')+t+' '+(saved?'מהמועדפים':'למועדפים'))+'"><span aria-hidden="true">'+(saved?'♥':'♡')+'</span></button><a class="kdMedia kdMedia--uncropped" href="'+esc(detail(e))+'" tabindex="-1" aria-hidden="true">'+(img.url?'<img src="'+esc(img.url)+'" alt="" loading="lazy" decoding="async">':'<span class="kdMediaText" aria-hidden="true">'+esc(topics[topic(e)])+'</span>')+(!img.original&&img.url?'<span class="kdCredit">המחשה</span>':'')+'</a><div class="kdCardCopy"><h3><a href="'+esc(detail(e))+'">'+esc(t)+'</a></h3><p class="kdSummary">'+esc(summary(e))+'</p><p class="kdDate">'+esc(date(e.start_date))+(e.start_time?' · <bdi>'+esc(e.start_time)+'</bdi>':'')+'</p><p class="kdVenue">'+esc(venue)+'</p>'+(ageText?'<p class="kdAge">'+esc(ageText)+'</p>':'')+(practical.length?'<details class="kdPractical"><summary>מידע לקראת היציאה</summary><p>'+practical.map(esc).join('<br>')+'</p>'+(unknownMeeting&&e.purchase_phone&&/^[\d\s+()-]+$/.test(e.purchase_phone)?'<a href="tel:'+esc(e.purchase_phone.replace(/[^\d+]/g,''))+'">בירור בטלפון '+esc(e.purchase_phone)+'</a>':'')+'</details>':'')+'<div class="kdCardBottom">'+(soldOut?'<p class="kdAvailability">מצב ההרשמה הידוע: אזלו המקומות</p>':'')+(p?'<p class="kdPrice">'+esc(p)+'<small>מחיר שפורסם · פרטי התשלום בהזמנה</small></p>':'')+'<div class="kdActions"><a class="kdButton" href="'+esc(detail(e))+'">לפרטי הפעילות ←</a>'+(url?'<a class="kdBooking" href="'+esc(url)+'" target="_blank" rel="noopener">'+(soldOut?'לבדיקת זמינות באתר המארגן ↗':'לפרטים והרשמה ↗')+'</a>':'')+'</div></div></div></article>';
}
const explore=[['פארקים ומשחקים','מרחב לרוץ, לשחק ולבלות','places.html?category=parks','♧'],['חופים וטיילת','חול, אוויר ים וזמן ביחד','places.html?category=beaches','≈'],['אטרקציות לילדים','בראשון לציון ובסביבה','attractions.html?audience=kids','✧'],['קולנוע','לבחור סרט שמתאים לילדים','cinema.html','▣'],['מוזיאונים ותערוכות','יום של סקרנות ואמנות','category.html?category=exhibition','▧'],['טבע בעיר','לגלות את ראשון לציון ברגל','places.html?category=nature','❋']];
function todayIso(){return clock().day}
function movieHasTimes(m){return (m.venues||[]).some(v=>Object.entries(v.schedule||{}).some(([d,t])=>d>=todayIso()&&Array.isArray(t)&&t.length))}
function familyFilms(data){return (data.movies||[]).filter(m=>m.is_family===true&&(movieHasTimes(m)||m.family_catalog_source_url)).sort((a,b)=>Number(movieHasTimes(b))-Number(movieHasTimes(a))||a.title.localeCompare(b.title,'he'))}
function filmCard(m){
 const href='movie.html?id='+encodeURIComponent(m.id),active=(m.venues||[]).filter(v=>Object.entries(v.schedule||{}).some(([d,t])=>d>=todayIso()&&Array.isArray(t)&&t.length));
 const next=active.flatMap(v=>Object.entries(v.schedule||{}).filter(([d,t])=>d>=todayIso()&&Array.isArray(t)&&t.length).map(([date,times])=>({date,times,venue:v}))).sort((a,b)=>a.date.localeCompare(b.date))[0];
 const poster=m.poster_verification?.url===m.poster_url?m.poster_url:'';
 const schedule=next?'<p class="kdFilmNext">'+esc(new Intl.DateTimeFormat('he-IL',{weekday:'short',day:'numeric',month:'short'}).format(new Date(next.date+'T12:00:00')))+' · '+esc(next.times.slice(0,3).join(' · '))+'</p><p class="kdFilmVenue">'+esc(active.map(v=>v.name).join(' / '))+'</p>':'<p class="kdFilmPending">'+(m.release_date>todayIso()?'בקרוב בקולנוע · '+esc(m.release_date.split('-').reverse().join('.')):'מקטלוג הילדים')+'<br>שעות בראשון לציון טרם אומתו</p>';
 return '<article class="kdFilmCard"><a class="kdFilmPoster" href="'+href+'">'+(poster?'<img src="'+esc(poster)+'" alt="כרזת הסרט '+esc(m.title)+'" loading="lazy" referrerpolicy="no-referrer">':'<span aria-hidden="true">▣</span>')+(m.trailer_youtube_id?'<span class="kdFilmTrailer">▶ טריילר ופרטים</span>':'')+'</a><div class="kdFilmBody"><h3><a href="'+href+'">'+esc(m.title)+'</a></h3><p class="kdFilmMeta">'+esc([m.runtime_minutes?m.runtime_minutes+' דקות':null,m.age_rating].filter(Boolean).join(' · '))+'</p>'+schedule+'<a class="kdFilmDetails" href="'+href+'">'+(next?'לכל ההקרנות והכרטיסים':'לפרטי הסרט ובדיקת הקרנות')+' ←</a></div></article>';
}
function movieSection(data){
 const films=familyFilms(data);if(!films.length)return '';
 const active=films.filter(movieHasTimes),catalog=films.filter(m=>!movieHasTimes(m));
 return '<section id="kids-movies" class="kdMovies" aria-labelledby="kdMoviesTitle"><div class="kdMovieHeading"><div><span class="kdEyebrow">המסך הגדול, ביחד</span><h2 id="kdMoviesTitle">סרטים לילדים ולמשפחה</h2><p>בחרו הרפתקה, צפו בטריילר ומצאו את ההקרנה שלכם.</p></div><a href="./?audience=family#cinema">לכל סרטי הילדים בקולנוע ←</a></div>'+(active.length?'<h3 class="kdFilmGroupTitle">עם הקרנות בראשון לציון <span>'+active.length+' סרטים</span></h3><div class="kdFilmRail" tabindex="0" aria-label="סרטי ילדים עם הקרנות בראשון לציון">'+active.map(filmCard).join('')+'</div>':'')+(catalog.length?'<h3 class="kdFilmGroupTitle">עוד סרטים מעולם הילדים</h3><p class="kdFilmNote">מהקטלוג הרשמי של רשתות הקולנוע. זמינות בראשון לציון נבדקת בעמוד הסרט; אין כרגע שעות מקומיות מאומתות.</p><div class="kdFilmRail" tabindex="0" aria-label="סרטי ילדים מהקטלוג הרשמי">'+catalog.map(filmCard).join('')+'</div>':'')+'</section>';
}
function holidaySpotlight(rows){
 const shows=rows.filter(e=>(e.title||'').includes('קסם של פסטיבל')).sort((a,b)=>(a.start_date+' '+a.start_time).localeCompare(b.start_date+' '+b.start_time));
 if(!shows.length)return '';
 const show=shows[0],photo=picture(show),dates=[...new Set(shows.map(e=>e.start_date))];
 const dateLabel=dates.map(d=>new Intl.DateTimeFormat('he-IL',{day:'numeric',month:'long',year:'numeric'}).format(new Date(d+'T12:00:00'))).join(' · ');
 return '<section class="kdHoliday" aria-labelledby="kdHolidayTitle"><a class="kdHolidayPoster" href="event.html?id='+encodeURIComponent(show.event_id)+'">'+(photo.url?'<img src="'+esc(photo.url)+'" alt="קסם של פסטיבל – חנוכה 2026" loading="lazy">':'')+'</a><div class="kdHolidayCopy"><span class="kdEyebrow">לקראת חנוכה</span><h2 id="kdHolidayTitle">'+esc(show.title)+'</h2><p>מופע חנוכה לילדים ולמשפחות במשכן לאמנויות הבמה בראשון לציון.</p><p class="kdHolidayDate">'+esc(dateLabel)+'</p><nav class="kdHolidayTimes" aria-label="מועדי קסם של פסטיבל">'+shows.map(e=>'<a href="event.html?id='+encodeURIComponent(e.event_id)+'">'+esc(e.start_time)+' <span>לפרטים ←</span></a>').join('')+'</nav></div></section>';
}
function heroPick(rows){
 const e=rows.find(e=>picture(e).original&&picture(e).url);if(!e)return '<a class="kdHeroFallback" href="#kids-movies"><span aria-hidden="true">▣</span><strong>המסך הגדול מחכה לכם</strong><small>בחרו סרט ובדקו הקרנות בראשון לציון ←</small></a>';
 const img=picture(e),date=new Intl.DateTimeFormat('he-IL',{weekday:'short',day:'numeric',month:'short'}).format(new Date(e.start_date+'T12:00:00'));
 return '<a class="kdHeroPick" href="event.html?id='+encodeURIComponent(e.event_id)+'"><img src="'+esc(img.url)+'" alt="'+esc(title(e))+'" fetchpriority="high" decoding="async"><span class="kdHeroTag">בקרוב בעיר</span><div class="kdHeroCaption"><small>'+esc(date)+(e.start_time?' · '+esc(e.start_time):'')+'</small><strong>'+esc(title(e))+'</strong><span>לפרטים ולגילאים ←</span></div></a>';
}
function familyGuide(){
 const sources=[
 ['✦','יוצרים במוזיאון','טכניקידס, ציור וקרמיקה. בדקו גיל, מועד והרשמה מול מוזיאון ראשון לציון לאמנות.','https://www.ashdodartmuseum.org.il/education/%D7%98%D7%9B%D7%A0%D7%99%D7%A7%D7%95%D7%AA-%D7%90%D7%92%D7%A3-%D7%94%D7%A1%D7%93%D7%A0%D7%90%D7%95%D7%AA/'],
 ['♧','ים, טבע וטיול משפחתי','מסלול של תיירות ראשון לציון: פארק הפיראטים, נחל לכיש ומרכז הדולפין והים.','https://visit.ashdod.muni.il/route/ים-טבע-ואקסטרים/'],
 ['☀','פוגשים בעלי חיים בפל״א חי','מידע על הביקור המשפחתי במתחם פארק אתגרים. בדקו שעות וכרטיסים לפני ההגעה.','https://visit.ashdod.muni.il/night-life/%D7%A4%D7%9C%D7%90-%D7%97%D7%99-%D7%90%D7%A9%D7%93%D7%95%D7%93-2/?screen=true']
 ];
 return '<div class="kdGuide"><h3>עוד רעיונות מהמקורות בעיר</h3><p>מקומות ותכניות לבילוי — מועדים והרשמה באתר הרשמי.</p><nav class="kdGuideGrid" aria-label="מקורות רשמיים לבילוי משפחתי">'+sources.map(([icon,t,d,u])=>'<a href="'+esc(u)+'" target="_blank" rel="noopener"><span aria-hidden="true">'+icon+'</span><strong>'+t+'</strong><p>'+d+'</p><small>למקור הרשמי ↗</small></a>').join('')+'</nav></div>';
}
async function init(){
 document.body.classList.add('kidsPage');document.querySelector('.siteTopbar').outerHTML=header;
 document.title='ילדים בראשון לציון — פעילויות, הצגות ובילוי משפחתי | מה עושים בראשון לציון';
 const root=document.querySelector('main');root.innerHTML='<p role="status">טוענים פעילויות ורעיונות לבילוי…</p>';
 try{
  const [data,cms,cinema]=await Promise.all([fetch('data/events.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('events');return r.json()}),window.ISNET_PUBLIC_CMS?.publishedEvents?.('ashdod')||Promise.resolve([]),fetch('data/cinema.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('cinema');return r.json()}).catch(()=>({movies:[]}))]);
  const rows=mergeRows(window.ISNET_EVENT_IDENTITIES?.reconcile?.(data.events||[])||data.events||[],cms).filter(e=>visible(e)).sort((a,b)=>(a.start_date+' '+(a.start_time||'')).localeCompare(b.start_date+' '+(b.start_time||'')));
  const months=[...new Set(rows.map(e=>e.start_date.slice(0,7)))];let active='all',savedOnly=false,saved=new Set();
  const storageKey='isnet-ashdod-kids-saved-v1';try{saved=readSaved(localStorage.getItem(storageKey))}catch{}
  root.innerHTML='<header class="kdIntro"><div class="kdIntroCopy"><h1>מה עושים עם הילדים <em>בראשון לציון?</em></h1></div></header><section class="kdExplore" id="kids-explore" aria-labelledby="kdExploreTitle"><div class="kdSectionHead"><h2 id="kdExploreTitle">גם בלי אירוע: יוצאים עם הילדים</h2><p>פארקים, ים, תרבות ורעיונות לבילוי משפחתי</p></div><nav class="kdExploreGrid" aria-label="בילויים נוספים בעיר">'+explore.map(([t,d,u,i])=>'<a class="kdExploreLink" href="'+u+'"><span class="kdExploreIcon" aria-hidden="true">'+i+'</span><span><strong>'+t+'</strong><small>'+d+'</small></span><span class="kdArrow" aria-hidden="true">←</span></a>').join('')+'</nav></section><section id="kids-activities" aria-labelledby="kdActivityTitle"><div class="kdSectionHead"><h2 id="kdActivityTitle">לוח הפעילויות המשפחתי</h2></div><div class="kdTools"><label class="kdSearch"><span aria-hidden="true">⌕</span><input id="kdSearch" type="search" placeholder="חפשו פעילות, מקום או מארגן" aria-label="חיפוש פעילות, מקום או מארגן"></label><label class="kdTopicLabel" for="kdTopic">איזה בילוי?<select id="kdTopic">'+Object.entries(topics).filter(([k])=>k==='all'||rows.some(e=>topic(e)===k)).map(([k,t])=>'<option value="'+k+'">'+t+'</option>').join('')+'</select></label><label class="kdMonthLabel" for="kdMonth">מתי יוצאים?<select id="kdMonth"><option value="all">כל התאריכים</option><option value="today">היום</option><option value="weekend">סוף השבוע הקרוב</option><option value="soon">ב־30 הימים הקרובים</option><option value="week">בשבעת הימים הקרובים</option><option value="month">החודש</option>'+months.map(m=>'<option value="'+m+'">'+month(m)+'</option>').join('')+'</select></label></div><div class="kdResultBar"><p id="kdCount" role="status" aria-live="polite"></p><button type="button" id="kdSaved" aria-pressed="false" title="המועדפים נשמרים בדפדפן הזה, ללא הרשמה">♡ המועדפים שלי</button><button id="kdReset" type="button" hidden>ניקוי הסינון</button></div><div id="kdResults"></div><div id="kdEmpty" class="kdEmpty" hidden><h3>לא נמצאה פעילות מתאימה לבחירה</h3><p>אפשר לבחור חודש אחר, לנקות את הסינון או לגלות עוד בילויים בעיר.</p><a href="#kids-explore">לעוד בילויים בעיר ↑</a></div></section>';
  // Bring the activities forward, while keeping a short gateway to general leisure.
  const activities=root.querySelector('#kids-activities'),discovery=root.querySelector('#kids-explore');
  root.querySelector('.kdIntro .kdEyebrow')?.remove();
  root.querySelector('.kdIntro').insertAdjacentHTML('afterend','<nav class="kdWorldNav" aria-label="בחרו בילוי לילדים"><a class="kdWorldMovie" href="#kids-movies"><span class="kdWorldIcon" aria-hidden="true">▣</span><strong>סרטים לילדים</strong><small>טריילרים ושעות הקרנה</small><span class="kdWorldArrow" aria-hidden="true">←</span></a><a class="kdWorldShow" href="#kids-activities" data-kids-world="theatre"><span class="kdWorldIcon" aria-hidden="true">◈</span><strong>הצגות לילדים</strong><small>הצגות ומופעים בכל התאריכים</small><span class="kdWorldArrow" aria-hidden="true">←</span></a><a class="kdWorldActivity" href="#kids-activities" data-kids-world="all"><span class="kdWorldIcon" aria-hidden="true">✦</span><strong>פעילויות לילדים</strong><small>סיפורים, יצירה ובילוי משפחתי</small><span class="kdWorldArrow" aria-hidden="true">←</span></a><a class="kdWorldAttraction" href="attractions.html?audience=kids"><span class="kdWorldIcon" aria-hidden="true">✧</span><strong>אטרקציות לילדים</strong><small>בראשון לציון ובסביבה</small><span class="kdWorldArrow" aria-hidden="true">←</span></a></nav>'+holidaySpotlight(rows));
  activities.after(discovery);
  // Keep search, category and date together immediately below the four primary category cards.
  const toolbar=activities.querySelector('.kdTools');
  root.querySelector('.kdWorldNav').after(toolbar);
  toolbar.after(activities);
  discovery.insertAdjacentHTML('beforeend',familyGuide());
  root.querySelector('.kdWorldNav').insertAdjacentHTML('afterend','<details class="kdParentNote"><summary>לפני שמזמינים: גיל, מחיר ונגישות</summary><p>בדקו בכרטיס הפעילות את הגיל המומלץ, המקום והמחיר. כשהמארגן לא פרסם פרט מסוים, כדאי לברר מולו לפני ההזמנה. לסרטים בדקו גם דיבוב ושעות הקרנה בראשון לציון.</p></details>');
  activities.insertAdjacentHTML('afterend',movieSection(cinema));

  activities.querySelector('.kdSectionHead').insertAdjacentHTML('afterend','<p id="kdSaveStatus" class="kdSaveStatus" role="status" aria-live="polite"></p>');
  root.querySelector('#kdMonth').value='all';
  const empty=root.querySelector('#kdEmpty');
  function render(){
   const q=root.querySelector('#kdSearch').value.trim(),selected=root.querySelector('#kdMonth').value;
   const found=filterRows(rows,{active,q,period:selected,savedOnly,saved});
   root.querySelector('#kdCount').textContent=(found.length===1?'פעילות אחת':found.length+' פעילויות')+(savedOnly?' במועדפים':'');root.querySelector('#kdEmpty').hidden=found.length>0;root.querySelector('#kdReset').hidden=!q&&selected==='all'&&active==='all'&&!savedOnly;
   empty.querySelector('h3').textContent=savedOnly?'עוד אין כאן פעילויות שמורות':'לא נמצאה פעילות מתאימה לבחירה';empty.querySelector('p').textContent=savedOnly?'בחרו פעילות ולחצו על הלב כדי לחזור אליה בקלות. אפשר לשמור גם פעילות בחודש רחוק יותר.':'אפשר לבחור חודש אחר, לנקות את הסינון או לגלות עוד בילויים בעיר.';
   const groups=new Map();for(const e of found){const m=e.start_date.slice(0,7);if(!groups.has(m))groups.set(m,[]);groups.get(m).push(e)}
   root.querySelector('#kdResults').innerHTML=[...groups].map(([m,events])=>'<section class="kdMonthGroup" aria-label="'+esc(month(m))+'"><h2>'+esc(month(m))+'</h2><div class="kdCards">'+events.map(e=>card(e,saved.has(e.event_id||e.id))).join('')+'</div></section>').join('');
   root.querySelector('#kdTopic').value=active;
   root.querySelector('#kdSaved').setAttribute('aria-pressed',String(savedOnly));
  }
  function reset(){active='all';savedOnly=false;root.querySelector('#kdSearch').value='';root.querySelector('#kdMonth').value='all';render()}
  root.addEventListener('click',e=>{
   const quick=e.target.closest('[data-kids-period]');if(quick){active='all';savedOnly=false;root.querySelector('#kdSearch').value='';root.querySelector('#kdMonth').value=quick.dataset.kidsPeriod;render();}
   const world=e.target.closest('[data-kids-world]');if(world){active=world.dataset.kidsWorld;savedOnly=false;root.querySelector('#kdSearch').value='';root.querySelector('#kdMonth').value='all';render();}
   const bookmark=e.target.closest('[data-save]');if(bookmark){const id=bookmark.dataset.save;if(saved.has(id))saved.delete(id);else saved.add(id);let persisted=true;try{localStorage.setItem(storageKey,JSON.stringify([...saved]))}catch{persisted=false}render();root.querySelector('#kdSaveStatus').textContent=persisted?(saved.has(id)?'הפעילות נשמרה במועדפים':'הפעילות הוסרה מהמועדפים'):'השמירה זמינה כרגע בעמוד הזה בלבד; הדפדפן לא מאפשר שמירה להמשך.';const next=[...root.querySelectorAll('[data-save]')].find(b=>b.dataset.save===id)||root.querySelector('#kdSaved');next.focus({preventScroll:true});return;}
   if(e.target.closest('#kdSaved')){savedOnly=!savedOnly;active='all';root.querySelector('#kdSearch').value='';root.querySelector('#kdMonth').value='all';render()}
   if(e.target.closest('#kdReset'))reset();
  });
  root.querySelector('#kdTopic').addEventListener('change',()=>{active=root.querySelector('#kdTopic').value;savedOnly=false;render()});root.querySelector('#kdSearch').addEventListener('input',render);root.querySelector('#kdMonth').addEventListener('change',()=>{savedOnly=false;render()});render();

 }catch{root.innerHTML='<p class="kdEmpty" role="alert">לא ניתן לטעון כרגע את הפעילויות. <a href="./?category=kids">לפעילויות ילדים בעמוד הראשי ←</a></p>'}
}
window.ISNET_KIDS={init,visible,mergeRows,matches,title,picture,price,card,readSaved,inPeriod,filterRows,forKids,topic,familyFilms,filmCard,movieSection,holidaySpotlight};
})();





