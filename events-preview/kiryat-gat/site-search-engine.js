/* Local structured search. No external model and no server query per message. */
(function(root){
'use strict';
const norm=s=>String(s??'').toLowerCase().replace(/[\u0591-\u05c7]/g,'').replace(/[ךםןףץ]/g,c=>({'ך':'כ','ם':'מ','ן':'נ','ף':'פ','ץ':'צ'}[c])).replace(/[^\p{L}\p{N}]+/gu,' ').trim().replace(/\s+/g,' ');
const forms=s=>{s=norm(s);return s.length>=4&&/^[ובלהכמש]/.test(s)?[s,s.slice(1)]:[s]};
const groups=[
 ['standup','סטנדאפ',['סטנדאפ','סטנדפ','סטנד אפ'],['standup','סטנדאפ']],
 ['funny','משהו מצחיק',['מצחיק','מצחיקה','לצחוק','צחוק','קומדיה','סטנדאפ','סטנדפ','סטנד אפ','בידור'],['standup','קומדיה','סטנדאפ','קומי']],
 ['music','מוזיקה',['מוזיקה','מוסיקה','הופעה','הופעות','זמר','זמרת','שירים'],['music','מוזיקה','מוסיקה','זמר','מופע מוזיקלי']],
 ['concert','קונצרטים',['קונצרט','קונצרטים','קלאסית','תזמורת','סימפוני'],['concerts','קונצרט','קלאסית','תזמורת']],
 ['theatre','הצגות',['הצגה','הצגות','תיאטרון','מחזמר'],['theatre','הצגה','תיאטרון','מחזמר']],
 ['learn','הרצאות',['הרצאה','הרצאות','להעשיר','ללמוד'],['lecture','הרצאה','הרצאות']],
 ['dance','מחול וריקוד',['מחול','ריקוד','ריקודים','פלמנקו','בלט'],['dance','מחול','ריקוד','פלמנקו','בלט']],
 ['art','אמנות ותערוכות',['אמנות','אומנות','תערוכה','תערוכות','מוזיאון','גלריה'],['exhibition','אמנות','תערוכה','מוזיאון','גלריה']],
 ['sport','ספורט',['כדורגל','כדורסל','כדוריד','ספורט'],['sport','כדורגל','כדורסל','כדוריד','ספורט']],
 ['escape','חדרי בריחה',['חדר בריחה','חדרי בריחה','אסקייפ'],['חדר בריחה','חדרי בריחה','escape']],
 ['nature','טיולים וטבע',['טיול','טיולים','טבע','בחוץ'],['nature','טבע','טיול','טיולים','חוף','פארק']],
 ['water','שיט וספורט ימי',['שיט','שייט','אבובים','בננה','ספורט ימי'],['שיט','שייט','אבובים','ספורט ימי']],
 ['bowling','באולינג',['באולינג','בולינג'],['באולינג','בולינג']],
 ['karaoke','קריוקי',['קריוקי','קאריוקי'],['קריוקי','קאריוקי']]
];
const stop=new Set(norm('אני אנחנו רוצה רוצים מחפש מחפשת מחפשים תמצא תני תן לי לנו עם של את זה יש משהו מה לאן איפה אפשר לעשות לצאת לבלות בילוי פעילות אירוע אירועים בעיר קריית גת בקריית גת אשדד באשדד בבקשה רק גם עוד פתוח פתוחה פתוחימ פתוחות עד אחרי לפני בשעה בן בת גיל בגיל גילאי לילד לילדה לילדים ילד ילדים משפחה למשפחה משפחתי משפחתית לכל היום מחר בשבת שבת בשישי שישי סופש סוף השבוע בערב ערב בצהריים בבוקר חינם ללא תשלום שקל שקלים שח זול תקציב מקסימום סרט סרטים קולנוע היכל התרבות הוט חוג חוגים קורס קורסים אטרקציה אטרקציות מקום מקומות בלי לא יותר פחות חדש חיפוש נקה מחדש ארבע שלוש שנתיים חמש שש שבע שמונה תשע עשר').split(' '));
const wordMatchers=new Map();
const has=(hay,word)=>{const w=norm(word);let re=wordMatchers.get(w);if(!re){re=new RegExp('(?:^| )[ובלהכמש]?'+w+'(?: |$)');wordMatchers.set(w,re)}return re.test(hay)};
const any=(hay,words)=>words.some(w=>has(hay,w));
function distance(a,b){if(Math.abs(a.length-b.length)>2)return 99;let row=Array.from({length:b.length+1},(_,i)=>i);for(let i=1;i<=a.length;i++){let prev=row[0];row[0]=i;for(let j=1;j<=b.length;j++){const old=row[j];row[j]=Math.min(row[j]+1,row[j-1]+1,prev+(a[i-1]===b[j-1]?0:1));prev=old}}return row[b.length]}
function parse(q,previous){
 const s=norm(q).slice(0,500);if(/^(?:מה (?:לעשות|עושימ|יש|אפשר)|מה פתוח)/.test(s))previous=null;const c={...(previous||{}),terms:[]};
 if(/(?:חיפוש חדש|התחל מחדש|נקה)/.test(s))return {terms:[],reset:true};
 const indoorOnly=/לא בחוצ|בלי בחוצ|לא באוויר הפתוח|במקומ סגור|במקומות סגורימ|בתוכ מבנה/.test(s);
 if(indoorOnly){c.setting='indoor';if(c.concepts)c.concepts=c.concepts.filter(id=>id!=='nature');}else if(/רק בחוצ|רק באוויר הפתוח/.test(s))c.setting='outdoor';else if(/בלי הגבלת מקומ/.test(s))delete c.setting;
 const concepts=groups.filter(g=>any(s,g[2])&&!((indoorOnly||/רק בחוצ|רק באוויר הפתוח/.test(s))&&g[0]==='nature'));if(concepts.length)c.concepts=concepts.map(g=>g[0]);
 if(/קולנוע|סרט|סינמה|הוט סינמה/.test(s))c.type='movie';else if(/חוג|קורס/.test(s))c.type='course';else if(/אטרקצי|חדר[י ]+בריחה|באולינג|בולינג|קריוקי|פארק|חופ|שיט|שייט/.test(s))c.type='place';else if(/הצג|הופע|סטנד|הרצא|קונצרט/.test(s))c.type='event';
 if(any(s,['ילדים','ילד','ילדה','משפחה','משפחתי','משפחתית','קטנטנים','פעוטות']))c.family=true;
 if(/לא לילד|בלי ילד|למבוגר|למבוגרת|למבוגרים/.test(s))c.family=false;
 const age=s.match(/(?:בנ|בת|גיל|בגיל|גילאי)\s+(\d{1,2}|שנתיימ|שלוש|ארבע|חמש|שש|שבע|שמונה|תשע|עשר)(?:\s|$)/);if(age){c.age=({שנתיימ:2,שלוש:3,ארבע:4,חמש:5,שש:6,שבע:7,שמונה:8,תשע:9,עשר:10})[age[1]]??Number(age[1]);if(c.age<18)c.family=true}
 const price=s.match(/(?:עד|תקציב|מקסימומ)\s+(\d{1,4})/);if(price)c.maxPrice=Number(price[1]);if(/חינמ|ללא תשלומ|בלי לשלמ/.test(s))c.maxPrice=0;if(/בלי הגבלת מחיר/.test(s))delete c.maxPrice;
 if(/כל התאריכימ|בלי הגבלת תאריכ/.test(s))delete c.period;else if(/מחר/.test(s))c.period='tomorrow';else if(/היומ|הערב|הלילה/.test(s))c.period='today';else if(/סופש|סופ השבוע/.test(s))c.period='weekend';else if(/שבת/.test(s))c.period='saturday';else if(/שישי/.test(s))c.period='friday';else if(/השבוע/.test(s))c.period='week';
 const hour=s.match(/אחרי\s+(\d{1,2})(?::(\d\d))?/);if(hour)c.after=Number(hour[1])*60+Number(hour[2]||0);else if(/אחר הצהריימ|אחרי הצהריימ/.test(s))c.after=14*60;else if(/בערב/.test(s))c.after=18*60;
 const settingWords=new Set(norm('לא בלי בחוץ באוויר הפתוח במקום מקומות סגור סגורים בתוך מבנה הגבלת').split(' '));
 const recognized=new Set(concepts.flatMap(g=>g[2].flatMap(w=>norm(w).split(' '))));
 c.terms=s.split(' ').filter(w=>w&&!(c.setting&&settingWords.has(w))&&!/^\d+$/.test(w)&&!forms(w).some(f=>stop.has(f)||recognized.has(f))&&!['אחר','הצהריימ','מתחשק','מתאימ','מתאימה','שמתאימ'].includes(w));
 if(previous&&!c.terms.length&&previous.terms?.length)c.terms=previous.terms;
 c.titleQuery=s;
 return c;
}
function settingOf(record){
 if(record.is_indoor===true||record.indoor===true)return 'indoor';
 if(record.is_indoor===false||record.indoor===false)return 'outdoor';
 const value=String(record.venue_type||record.location_type||record.setting||'').toLowerCase();
 return ['indoor','outdoor'].includes(value)?value:null;
}
function create(payload){
 const labels={};for(const c of payload.taxonomy||[]){labels[c.id]=c.label;for(const sub of c.subcategories||[])labels[sub.id]=sub.label}
 let docs=[];const add=d=>{const text=norm([d.title,d.description,d.category,d.subcategory,d.venue,...(d.tags||[])].filter(Boolean).join(' '));docs.push({...d,text,titleText:norm(d.title),tokens:[...new Set(text.split(' ').flatMap(forms))]})};
 for(const e of payload.events||[]){if(e.status==='cancelled'||e.is_active===false||e.publication_status==='draft')continue;add({id:'e:'+e.event_id,type:'event',setting:settingOf(e),title:e.title,description:[e.description,e.short_pitch,e.long_description,e.series_description,e.series_title,e.variant_label,e.organizer].filter(Boolean).join(' '),category:labels[e.category]||e.category,subcategory:labels[e.subcategory]||e.subcategory,tags:[e.category,e.subcategory,...(e.audiences||[]),e.sport_branch].filter(Boolean),venue:e.venue,href:'event.html?id='+encodeURIComponent(e.event_id),dates:[{date:e.start_date,time:e.start_time||'',endDate:e.end_date}],min:e.age_min,max:e.age_max,family:e.category==='kids'||(e.audiences||[]).some(a=>['kids','families'].includes(a)),price:e.is_free?0:e.price_min_ils})}
 for(const m of payload.movies||[]){const dates=[];for(const v of m.venues||[]){for(const [date,times] of Object.entries(v.schedule||{}))for(const time of times)dates.push({date,time,venue:v.name});for(const s of v.sessions||[])dates.push({date:s.date,time:s.time,venue:v.name})}const rating=String(m.age_rating||'').match(/(?:מגיל|גיל)\s*(\d+)/);add({id:'m:'+m.id,type:'movie',setting:settingOf(m),title:m.title,description:m.synopsis||'',category:'קולנוע',tags:m.genres||[],venue:(m.venues||[]).map(v=>v.name).join(' · '),href:'movie.html?id='+encodeURIComponent(m.id),dates,family:m.is_family===true,min:rating?Number(rating[1]):null,price:null})}
 const seen=new Set();for(const [cat,group] of Object.entries(payload.places?.categories||{}))for(const p of group.items||[]){if(seen.has(p.id))continue;seen.add(p.id);add({id:'p:'+p.id,type:'place',setting:settingOf(p),title:p.name,description:[p.tagline,p.description,...(p.highlights||[])].filter(Boolean).join(' '),category:group.title,subcategory:cat,tags:[...(p.tags||[]),...(p.badges||[])],venue:p.location||p.address||'',href:cat==='kids-attractions'?'attraction.html?id='+encodeURIComponent(p.id):'places.html?category='+encodeURIComponent(cat)+'#'+encodeURIComponent(p.id),dates:[],family:(p.tags||[]).some(t=>['kids','families'].includes(t)),price:null})}
 for(const p of payload.saturdayGuide?.items||[]){if(!p.recurring_saturday)continue;if(p.place_id)docs=docs.filter(d=>d.id!=='p:'+p.place_id);add({id:'s:'+p.id,type:'place',setting:p.opening_kind==='outdoor'?'outdoor':settingOf(p),title:p.title,description:p.description,category:p.kind==='nature'?'טיולים וטבע':p.kind==='museum'?'מוזיאונים ותרבות':'אטרקציות',subcategory:'פתוח בשבת',tags:[p.city,p.opening_kind==='outdoor'?'טיול עצמאי':'פתוח בשבת'],venue:p.city,href:'saturday.html#'+encodeURIComponent(p.id),dates:[],family:p.family===true,price:p.is_free===true?0:null,saturdayEligible:true,openingKind:p.opening_kind,reviewAfter:p.review_after,closedDates:p.closed_dates||[],hours:p.hours||'',saturdayHours:p.saturday_hours||null})}
 for(const r of payload.courses||[])add({id:'c:'+r.id,type:'course',setting:settingOf(r),title:r.name,description:[r.subtitle,r.description,r.instructor].filter(Boolean).join(' '),category:r.category,subcategory:r.subcategory,tags:r.ages||[],venue:r.place,href:'/meusharim/kiryat-gat/course.html?id='+encodeURIComponent(r.id),dates:[],family:(r.ages||[]).some(a=>['עד 5','6-12','13-18'].includes(a)),price:null});
 return docs;
}
const shift=(day,n)=>{const d=new Date(day+'T12:00:00Z');d.setUTCDate(d.getUTCDate()+n);return d.toISOString().slice(0,10)};
function dateMatch(date,c,day){if(date<day)return false;const dow=new Date(day+'T12:00:00Z').getUTCDay(),friday=shift(day,(5-dow+7)%7),saturday=shift(day,(6-dow+7)%7);switch(c.period){case'today':return date===day;case'tomorrow':return date===shift(day,1);case'friday':return date===friday;case'saturday':return date===saturday;case'weekend':return date===friday||date===saturday;case'week':return date<=shift(day,6);default:return true}}
function search(docs,c,day,nowMinutes,allowAlternatives=true){
 // A phrase present in an event title is a name lookup, not an implicit date filter.
 const titleQuery=c.titleQuery||'';
 const titleLookup=titleQuery.split(' ').length>=2&&docs.some(d=>['event','movie'].includes(d.type)&&d.titleText.includes(titleQuery));
 if(titleLookup)c={titleQuery,titleLookup:true,terms:[]};
 const matches=[];for(const d of docs){if(titleLookup&&!d.titleText.includes(titleQuery))continue;if(c.setting&&d.setting!==c.setting)continue;if(c.type&&d.type!==c.type)continue;if(c.family===true&&!d.family&&!any(d.text,['לילדים','למשפחה','לכל המשפחה','פעוטות']))continue;if(c.family===false&&d.family)continue;
 if(c.age!=null&&((d.min!=null&&c.age<d.min)||(d.max!=null&&c.age>d.max)))continue;
 if(c.maxPrice!=null&&(d.price==null||d.price>c.maxPrice))continue;
 let dates=d.dates.filter(x=>dateMatch(x.date,c,day)&&(!x.time||x.date!==day||nowMinutes==null||Number(x.time.slice(0,2))*60+Number(x.time.slice(3,5))>=nowMinutes)&&(c.after==null||(x.time&&Number(x.time.slice(0,2))*60+Number(x.time.slice(3,5))>=c.after)));
 if(['event','movie'].includes(d.type)&&!dates.length)continue;
 if((c.period||c.after!=null)&&['place','course'].includes(d.type)){
 const target=c.period==='today'?day:c.period==='tomorrow'?shift(day,1):c.period==='friday'?null:shift(day,(6-new Date(day+'T12:00:00Z').getUTCDay()+7)%7);
 if(!d.saturdayEligible||!target||new Date(target+'T12:00:00Z').getUTCDay()!==6||(d.reviewAfter&&target>d.reviewAfter)||(d.closedDates||[]).includes(target))continue;
 if(c.after!=null&&(!d.saturdayHours||c.after>=d.saturdayHours[1]))continue;
 }
 let score=0;const reasons=c.setting?[c.setting==='indoor'?'מקום סגור לפי פרטי המקור':'בחוץ לפי פרטי המקור']:[];
 for(const id of c.concepts||[]){const g=groups.find(g=>g[0]===id);if(g&&any(d.text,g[3])){score+=15;reasons.push(g[1])}else{score=-1;break}}
 if(score<0)continue;
 let all=true;for(const term of c.terms||[]){const variants=forms(term);if(variants.some(t=>has(d.titleText,t))){score+=25;continue}if(variants.some(t=>d.tokens.includes(t))){score+=10;continue}if(term.length>=4&&d.tokens.some(t=>Math.abs(t.length-term.length)<=1&&distance(term,t)<=(term.length>=7?2:1))){score+=4;continue}all=false;break}if(!all)continue;
 if(!(c.titleLookup||c.concepts?.length||c.terms?.length||c.type||c.setting||c.family!=null||c.period||c.maxPrice!=null||c.age!=null))continue;
 dates.sort((a,b)=>(a.date+' '+a.time).localeCompare(b.date+' '+b.time));
 const notes=[];if(c.age!=null&&d.min==null&&d.max==null)notes.push('התאמת גיל מדויקת לא צוינה');if(d.type==='place')notes.push(d.openingKind==='outdoor'?'מסלול טיול עצמאי — יש לבדוק גישה, מזג אוויר וסגירות':d.hours?'שעות שבת רגילות: '+d.hours+'; יש לוודא חריגים מול המקום':'יש לבדוק שעות פתיחה ומחיר מול המקום');if(d.type==='course')notes.push('לימים, שעות ומחיר — בדף החוג');
 matches.push({id:d.id,type:d.type,title:d.title,description:d.description.slice(0,240),category:d.category,subcategory:d.subcategory,venue:dates[0]?.venue||d.venue,href:d.href,date:dates[0]?.date,time:dates[0]?.time,price:d.price,reasons,notes,score:score+(c.type?10:0)})}
 matches.sort((a,b)=>b.score-a.score||String(a.date||'9999').localeCompare(String(b.date||'9999'))||a.title.localeCompare(b.title,'he'));const seen=new Set();const unique=matches.filter(d=>{const key=d.type+norm(d.title)+d.date+d.time;if(seen.has(key))return false;seen.add(key);return true});const alternatives=[];
 if(allowAlternatives&&!unique.length){
  const options=[];
  if(c.period||c.after!=null){const relaxed={...c};delete relaxed.period;delete relaxed.after;options.push(['ללא סינון מועד ושעה',relaxed]);}
  if(c.maxPrice!=null){const relaxed={...c};delete relaxed.maxPrice;options.push(['ללא הגבלת תקציב — המחיר מופיע בכל תוצאה כשידוע',relaxed]);}
  for(const [label,relaxed] of options){const found=search(docs,relaxed,day,nowMinutes,false);if(found.count)alternatives.push({label,count:found.count,results:found.results.slice(0,3)});}
 }
 return {count:unique.length,results:unique.slice(0,12),alternatives,needsAge:c.family===true&&c.age==null,context:c};
}
const api={norm,parse,create,search};if(typeof module!=='undefined'&&module.exports)module.exports=api;root.SiteSearchEngine=api;
if(typeof WorkerGlobalScope!=='undefined'&&root instanceof WorkerGlobalScope){let docs=[];root.onmessage=e=>{try{if(e.data.kind==='init'){docs=create(e.data.payload);root.postMessage({kind:'ready',count:docs.length});return}const context=parse(e.data.query,e.data.context);const result=search(docs,context,e.data.day,e.data.nowMinutes);root.postMessage({kind:'result',id:e.data.id,...result})}catch(_){root.postMessage({kind:'error',id:e.data.id})}}}
})(typeof self!=='undefined'?self:globalThis);

