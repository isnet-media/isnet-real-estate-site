(()=>{
if(location.pathname.includes("/kiryat-gat/")&&["conference","food"].includes(new URLSearchParams(location.search).get("category"))){location.replace("./");return;}
if(location.pathname.includes("/kiryat-gat/")&&new URLSearchParams(location.search).get("category")==="seniors"&&window.ISNET_SENIORS){window.ISNET_SENIORS.init();return;}
if(location.pathname.includes("/kiryat-gat/")&&new URLSearchParams(location.search).get("category")==="kids"&&window.ISNET_KIDS){window.ISNET_KIDS.init();return;}
const config={stage:["הופעות במה","הצגות, מוזיקה וסטנדאפ",["music","theatre","standup"]],music:["הופעות ומוזיקה","מופעי מוזיקה בעיר",["music"]],theatre:["הצגות","תיאטרון ומחזות בעיר",["theatre"]],standup:["סטנדאפ","מופעי סטנדאפ בעיר",["standup"]],kids:["ילדים ומשפחה","מופעים, הצגות ופעילויות לילדים",["kids"]],seniors:["גימלאים","הרצאות, סיורים ופעילויות לגיל השלישי",["seniors"]],lecture:["הרצאות","תוכן, מפגשים וידע",["lecture"]],tour:["טיולים וסיורים","לגלות את העיר והסביבה",["tour"]],exhibition:["תערוכות","אמנות ותערוכות בעיר",["exhibition"]],sport:["אירועי ספורט","משחקי בית של הקבוצות הייצוגיות, תחרויות ופעילות ספורט עממית",["sport"]],community:["אירועי קהילה","מפגשים ואירועים קהילתיים",["community"]],conference:["כנסים","כנסים ופאנלים",["conference"]],food:["קולינריה","אירועי אוכל בעיר",["food"]]};
const params=new URLSearchParams(location.search),key=params.get("category")||"stage",entry=config[key]||config.stage;
document.title=entry[0]+" | מה עושים בקריית גת";
document.getElementById("title").textContent=entry[0];document.getElementById("lead").textContent=entry[1];
const tags=key==="stage"?[["stage","הכול"],["music","מוזיקה"],["theatre","הצגות"],["standup","סטנדאפ"]]:[];
document.getElementById("subcategories").innerHTML=tags.map(([id,label])=>'<a href="category.html?category='+id+'" class="'+(key===id?'active':'')+'">'+label+'</a>').join("");
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const iso=new Intl.DateTimeFormat("sv-SE",{timeZone:"Asia/Jerusalem",year:"numeric",month:"2-digit",day:"2-digit"}).format(new Date());
const ids=new Set(entry[2]);let events=[];
const unique=e=>String(e.event_id||e.id||"");
function trustedImage(e){
  return Boolean(!(window.isnetEventDefaultImage?.(e)&&window.isnetEventIllustration?.(e))&&e.image_url&&e.image_publishable===true&&e.image_verified===true&&e.source_image_kind!=="source_placeholder"&&(e.image_represents_event!==false||e.source_image_kind==="illustration")&&!/microsoft_oauth_logo|no_pic\.png|favicon|\/placeholders\/|\/images\/live\/more\/eventNew\.jpg|\/images\/artists\/artistShadow\.png/i.test(e.image_url));
}
function categoryImage(e){
 const illustration=window.isnetEventIllustration?.(e);
 if(illustration)return illustration.src;
 const photos={theatre:"theatre",standup:"standup",kids:"kids",lecture:"lecture"};
 if(photos[e.category])return "../media-bank/defaults/"+photos[e.category]+".webp";
 if(e.category==="seniors")return "../media-bank/defaults/seniors/seniors-lecture.webp";
 return "../shared/images/defaults/category-"+(config[e.category]?e.category:"community")+".svg";
}
function render(){
 const q=document.getElementById("q").value.trim().toLocaleLowerCase("he");
 const filtered=events.filter(e=>window.KGAT_EVENTS.matches(e,ids)&&(!q||String(e.title||"").toLocaleLowerCase("he").includes(q)));
 document.getElementById("count").textContent=filtered.length+" אירועים";
 document.getElementById("empty").hidden=filtered.length>0;
 document.getElementById("cards").innerHTML=filtered.map(e=>{
 const original=events.find(x=>x.title===e.title&&x.image_source==="friends"&&trustedImage(x))||e;
 const sourceImage=trustedImage(original);
 const image=sourceImage?(original.thumbnail_ready&&original.thumbnail_url?original.thumbnail_url:original.image_url):categoryImage(e);
 const venue=esc(e.venue||"קריית גת");
 const date=esc(e.start_date||"")+(key==="sport"?" · "+esc(e.start_time||"השעה טרם פורסמה"):"");
 const media=image?'<img class="image" src="'+esc(image)+'" loading="lazy" alt="'+esc(sourceImage&&e.source_image_kind!=="illustration"?e.title:"תמונת המחשה")+'" onerror="this.outerHTML=\'<div class=&quot;image placeholder&quot;>✦</div>\'">':'<div class="image placeholder">✦</div>';
 const mediaCredit=e.source_image_kind==='illustration'?'<small class="imageCredit">תמונת המחשה</small>':'';
 return '<a class="card" href="event.html?id='+encodeURIComponent(unique(e))+'">'+media+mediaCredit+'<div class="body"><h2>'+esc(e.title)+'</h2><div class="meta">'+date+' · '+venue+'</div><div class="action">לפרטי האירוע ←</div></div></a>';
 }).join("");
}
document.getElementById("q").addEventListener("input",render);
Promise.all([
 (window.ISNET_PUBLIC_CMS?.loadCards?.()||fetch("data/events.json",{cache:"no-store"}).then(r=>{if(!r.ok)throw Error("data");return r.json()})),
 window.ISNET_PUBLIC_CMS?.publishedEvents?.(location.pathname.split("/").filter(Boolean)[1],{listing:true})||Promise.resolve([])
]).then(([d,cms])=>{
 const rows=(window.ISNET_EVENT_IDENTITIES?.reconcile?.(Array.isArray(d.events)?d.events:[])||(Array.isArray(d.events)?d.events:[]));
 const map=new Map(rows.filter(Boolean).map(e=>[unique(e),e]));
 for(const row of (Array.isArray(cms)?cms:[])){
  const id=row?.event_id||row?.payload?.event_id;
  if(id&&row.payload&&(map.has(id)||row.record_type==="manual"))map.set(id,{...map.get(id),...row.payload,event_id:id});
 }
 events=[...map.values()].filter(e=>window.KGAT_EVENTS.matches(e,ids)&&e.is_active!==false&&!["cancelled","canceled","hidden","draft","deleted"].includes(e.status)&&!["hidden","draft","unpublished","archived"].includes(e.publication_status)&&(!e.start_date||e.start_date>=iso)).sort((a,b)=>String(a.start_date||"").localeCompare(String(b.start_date||"")));render();
}).catch(()=>{document.getElementById("empty").hidden=false;document.getElementById("empty").textContent="לא ניתן לטעון כרגע את רשימת האירועים. נסו שוב מאוחר יותר.";});
})();

(()=>{'use strict';if(!location.pathname.includes('/kiryat-gat/')||new URLSearchParams(location.search).get('category')!=='seniors')return;
fetch('data/senior-guide.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('guide');return r.json()}).then(d=>{if(document.getElementById('kgSeniorSources'))return;const s=document.createElement('section');s.id='kgSeniorSources';s.style.cssText='margin:28px 0;padding:20px;border:1px solid #a28a59;border-radius:18px;background:#171e26;color:#fff';const h=document.createElement('h2');h.textContent='עוד פעילויות ומסגרות לגמלאים בעיר';s.append(h);const note=document.createElement('p');note.textContent=d.note+' נבדק ב־30.10.2026.';s.append(note);const grid=document.createElement('div');grid.style.cssText='display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,270px),1fr));gap:14px';for(const x of d.links||[]){const u=new URL(x.url);if(u.protocol!=='https:')continue;const card=document.createElement('article');card.style.cssText='padding:18px;border:1px solid #65716e;border-radius:14px;background:#202b33';const title=document.createElement('h3');title.textContent=x.title;const p=document.createElement('p');p.textContent=x.description;const a=document.createElement('a');a.textContent='פרטים והרשמה אצל המארגן ↗';a.href=u.href;a.target='_blank';a.rel='noopener';a.style.cssText='display:block;color:#f3d59c;min-height:44px;padding:8px 0';card.append(title,p,a);if(/^\d{9,10}$/.test(x.phone||'')){const tel=document.createElement('a');tel.href='tel:'+x.phone;tel.textContent='התקשרו לבירור: '+x.phone;tel.style.cssText='display:block;min-height:44px;padding:8px 0;color:#b5efcf';card.append(tel)}grid.append(card)}s.append(grid);document.querySelector('main')?.append(s)}).catch(()=>{});
})();
