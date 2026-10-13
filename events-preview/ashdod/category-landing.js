(()=>{
if(location.pathname.includes("/ashdod/")&&["conference","food"].includes(new URLSearchParams(location.search).get("category"))){location.replace("./");return;}
if(location.pathname.includes("/ashdod/")&&new URLSearchParams(location.search).get("category")==="seniors"&&window.ISNET_SENIORS){window.ISNET_SENIORS.init();return;}
if(location.pathname.includes("/ashdod/")&&new URLSearchParams(location.search).get("category")==="exhibition"&&window.ISNET_EXHIBITIONS){window.ISNET_EXHIBITIONS.init();return;}
if(location.pathname.includes("/ashdod/")&&new URLSearchParams(location.search).get("category")==="kids"&&window.ISNET_KIDS){window.ISNET_KIDS.init();return;}
const config={stage:["הופעות במה","הצגות, מוזיקה וסטנדאפ",["music","theatre","standup"]],music:["הופעות ומוזיקה","מופעי מוזיקה בעיר",["music"]],theatre:["הצגות","תיאטרון ומחזות בעיר",["theatre"]],standup:["סטנדאפ","מופעי סטנדאפ בעיר",["standup"]],kids:["ילדים ומשפחה","מופעים, הצגות ופעילויות לילדים",["kids"]],seniors:["גימלאים","הרצאות, סיורים ופעילויות לגיל השלישי",["seniors"]],lecture:["הרצאות","תוכן, מפגשים וידע",["lecture"]],tour:["טיולים וסיורים","לגלות את העיר והסביבה",["tour"]],exhibition:["תערוכות","אמנות ותערוכות בעיר",["exhibition"]],sport:["אירועי ספורט","משחקים ואירועי ספורט",["sport"]],community:["אירועי קהילה","מפגשים ואירועים קהילתיים",["community"]],conference:["כנסים","כנסים ופאנלים",["conference"]],food:["קולינריה","אירועי אוכל בעיר",["food"]]};
const params=new URLSearchParams(location.search),key=params.get("category")||"stage",entry=config[key]||config.stage;
document.title=entry[0]+" | מה עושים באשדוד";
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
 const filtered=events.filter(e=>ids.has(e.category)&&(!q||String(e.title||"").toLocaleLowerCase("he").includes(q)));
 document.getElementById("count").textContent=filtered.length+" אירועים";
 document.getElementById("empty").hidden=filtered.length>0;
 document.getElementById("cards").innerHTML=filtered.map(e=>{
 const original=events.find(x=>x.title===e.title&&x.image_source==="friends"&&trustedImage(x))||e;
 const sourceImage=trustedImage(original);
 const image=sourceImage?(original.thumbnail_ready&&original.thumbnail_url?original.thumbnail_url:original.image_url):categoryImage(e);
 const venue=esc(e.venue||"אשדוד");
 const date=esc(e.start_date||"");
 const media=image?'<img class="image" src="'+esc(image)+'" loading="lazy" alt="'+esc(sourceImage?e.title:"תמונת המחשה")+'" onerror="this.outerHTML=\'<div class=&quot;image placeholder&quot;>✦</div>\'">':'<div class="image placeholder">✦</div>';
 return '<a class="card" href="event.html?id='+encodeURIComponent(unique(e))+'">'+media+'<div class="body"><h2>'+esc(e.title)+'</h2><div class="meta">'+date+' · '+venue+'</div><div class="action">לפרטי האירוע ←</div></div></a>';
 }).join("");
}
document.getElementById("q").addEventListener("input",render);
fetch("data/events.json",{cache:"no-store"}).then(r=>{if(!r.ok)throw Error("data");return r.json()}).then(d=>{
 const rows=(window.ISNET_EVENT_IDENTITIES?.reconcile?.(Array.isArray(d.events)?d.events:[])||(Array.isArray(d.events)?d.events:[]));const map=new Map();for(const e of rows){if(!e||!ids.has(e.category))continue;const k=unique(e);if(k)map.set(k,e)}
 events=[...map.values()].filter(e=>!e.start_date||e.start_date>=iso).sort((a,b)=>String(a.start_date||"").localeCompare(String(b.start_date||"")));render();
}).catch(()=>{document.getElementById("empty").hidden=false;document.getElementById("empty").textContent="לא ניתן לטעון כרגע את רשימת האירועים. נסו שוב מאוחר יותר.";});
})();