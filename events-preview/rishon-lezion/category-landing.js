// ISNET shared layout: edit events-preview/ashdod, not this generated file.
(()=>{
const config={stage:["הופעות במה","הצגות, מוזיקה וסטנדאפ",["music","theatre","standup"]],music:["הופעות ומוזיקה","מופעי מוזיקה בעיר",["music"]],theatre:["הצגות","תיאטרון ומחזות בעיר",["theatre"]],standup:["סטנדאפ","מופעי סטנדאפ בעיר",["standup"]],kids:["ילדים ומשפחה","מופעים, הצגות ופעילויות לילדים",["kids"]],seniors:["גימלאים","הרצאות, סיורים ופעילויות לגיל השלישי",["seniors"]],lecture:["הרצאות","תוכן, מפגשים וידע",["lecture"]],tour:["טיולים וסיורים","לגלות את העיר והסביבה",["tour"]],exhibition:["תערוכות","אמנות ותערוכות בעיר",["exhibition"]],sport:["אירועי ספורט","משחקים ואירועי ספורט",["sport"]],festival:["פסטיבלים","אירועים וחגיגות בעיר",["festival"]],community:["אירועי קהילה","מפגשים ואירועים קהילתיים",["community"]],conference:["כנסים","כנסים ופאנלים",["conference"]],food:["קולינריה","אירועי אוכל בעיר",["food"]]};
const params=new URLSearchParams(location.search),key=params.get("category")||"stage",entry=config[key]||config.stage;
document.title=entry[0]+" | מה עושים בראשון לציון";
document.getElementById("title").textContent=entry[0];document.getElementById("lead").textContent=entry[1];
const tags=key==="stage"?[["stage","הכול"],["music","מוזיקה"],["theatre","הצגות"],["standup","סטנדאפ"]]:[];
document.getElementById("subcategories").innerHTML=tags.map(([id,label])=>'<a href="category.html?category='+id+'" class="'+(key===id?'active':'')+'">'+label+'</a>').join("");
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const iso=new Intl.DateTimeFormat("sv-SE",{timeZone:"Asia/Jerusalem",year:"numeric",month:"2-digit",day:"2-digit"}).format(new Date());
const ids=new Set(entry[2]);let events=[];
const unique=e=>String(e.event_id||e.id||"");
function render(){
 const q=document.getElementById("q").value.trim().toLocaleLowerCase("he");
 const filtered=events.filter(e=>ids.has(e.category)&&(!q||String(e.title||"").toLocaleLowerCase("he").includes(q)));
 document.getElementById("count").textContent=filtered.length+" אירועים";
 document.getElementById("empty").hidden=filtered.length>0;
 document.getElementById("cards").innerHTML=filtered.map(e=>{
 const image=e.image_url||e.image||e.thumbnail_url||e.poster_url||"";
 const venue=esc(e.venue||"ראשון לציון");
 const date=esc(e.start_date||"");
 const media=image?'<img class="image" src="'+esc(image)+'" loading="lazy" alt="" onerror="this.outerHTML=\'<div class=&quot;image placeholder&quot;>✦</div>\'">':'<div class="image placeholder">✦</div>';
 return '<a class="card" href="event.html?id='+encodeURIComponent(unique(e))+'">'+media+'<div class="body"><h2>'+esc(e.title)+'</h2><div class="meta">'+date+' · '+venue+'</div><div class="action">לפרטי האירוע ←</div></div></a>';
 }).join("");
}
document.getElementById("q").addEventListener("input",render);
fetch("data/events.json",{cache:"no-store"}).then(r=>{if(!r.ok)throw Error("data");return r.json()}).then(d=>{
 const rows=Array.isArray(d.events)?d.events:[];const map=new Map();for(const e of rows){if(!e||!ids.has(e.category))continue;const k=unique(e);if(k)map.set(k,e)}
 events=[...map.values()].filter(e=>!e.start_date||e.start_date>=iso).sort((a,b)=>String(a.start_date||"").localeCompare(String(b.start_date||"")));render();
}).catch(()=>{document.getElementById("empty").hidden=false;document.getElementById("empty").textContent="לא ניתן לטעון כרגע את רשימת האירועים. נסו שוב מאוחר יותר.";});
})();