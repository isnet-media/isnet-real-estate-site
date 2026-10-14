// ISNET shared layout: edit events-preview/ashdod, not this generated file.
const $=id=>document.getElementById(id);
const titles={
  "kids-attractions":"אטרקציות לילדים בראשון לציון והסביבה",
  parks:"פארקים בראשון לציון",
  nature:"טבע וטיולים",
  beaches:"החופים בראשון לציון",
  attractions:"אטרקציות",
  culture:"מוסדות תרבות בראשון לציון",
  "must-see":"מקומות שחייבים להכיר"
};
const state={category:new URLSearchParams(location.search).get("category")||"parks",filter:"all",data:null,cat:null};

function esc(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}
function mapsUrl(q){return "https://www.google.com/maps/search/?api=1&query="+encodeURIComponent(q)}
function setMeta(title,intro){
  document.title=title+" | מה עושים בראשון לציון?";
  const meta=document.querySelector('meta[name="description"]');
  if(meta&&intro)meta.setAttribute("content",intro);
}
function renderHero(cat){
  state.cat=cat;
  $("placesTitle").textContent=cat.title;
  $("placesEyebrow").textContent=cat.eyebrow||"";
  $("placesIntro").textContent=cat.intro||"";
  $("heroBackdrop").style.backgroundImage='url("'+String(cat.hero_image||"").replace(/"/g,"%22")+'")';
  $("heroCredit").textContent=cat.hero_credit||"";
  $("placesStats").innerHTML=(cat.stats||[]).map(x=>
    '<div class="stat"><b>'+esc(x.value)+'</b><span>'+esc(x.label)+'</span></div>'
  ).join("");
  setMeta(cat.title,cat.intro);
}
function placeCard(item){
  const tags=(item.badges||[]).map(x=>'<span>'+esc(x)+'</span>').join("");
  const highlights=(item.highlights||[]).map(x=>'<li>'+esc(x)+'</li>').join("");
  const exhibitions=(item.current_exhibitions||[]).map(x=>
    '<a href="'+esc(x.source_url)+'" target="_blank" rel="noopener" style="display:block;color:inherit;text-decoration:none"><img src="'+esc(x.image)+'" alt="'+esc(x.title)+'" loading="lazy" style="width:100%;height:100px;object-fit:contain;background:#101116;border-radius:8px"><strong style="display:block;font-size:13px;margin-top:6px">'+esc(x.title)+'</strong><small style="display:block;color:#c1c5cc;font-size:11px">'+esc(x.image_credit)+'</small></a>'
  ).join("");
  return '<article class="placeCard" id="'+esc(item.id)+'" style="scroll-margin-top:90px">'+
    '<div class="placeMedia">'+
      (item.image?'<img src="'+esc(item.image)+'" alt="'+esc(item.name)+'" loading="lazy" onerror="this.closest(\'.placeMedia\').classList.add(\'imageFailed\');this.remove()">':'<span class="placeMediaIcon" aria-hidden="true">'+esc(item.icon||'✧')+'</span>')+
      '<div class="placeBadges">'+tags+'</div>'+
      (item.image_credit?'<small class="imageCredit">'+esc(item.image_credit)+'</small>':'')+
    '</div>'+
    '<div class="placeBody">'+
      '<span class="placeType">'+esc(state.cat?.item_label||(state.category==="beaches"?"חוף בראשון לציון":"מקום בראשון לציון"))+'</span>'+
      '<h2>'+(state.category==='kids-attractions'?'<a style="color:inherit;text-decoration:none" href="attraction.html?id='+encodeURIComponent(item.id)+'">'+esc(item.name)+'</a>':esc(item.name))+'</h2>'+
      '<h3>'+esc(item.tagline||"")+'</h3>'+
      '<p>'+esc(item.description||"")+'</p>'+
      '<ul class="placeHighlights">'+highlights+'</ul>'+
      (exhibitions?'<section aria-label="תערוכות שמוצגות כעת"><h3>מציגות כעת במוזיאון</h3><div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:12px 0">'+exhibitions+'</div></section>':'')+
      (state.category==='kids-attractions'&&item.notice?'<p class="kidsAttractionNotice">'+esc(item.notice)+'</p>':'')+
      '<div class="placeActions">'+
        (state.category==='kids-attractions'?'<a class="primaryAction" href="attraction.html?id='+encodeURIComponent(item.id)+'">לפרטי האטרקציה ←</a>':'')+
        (item.museum_url?'<a class="primaryAction" href="'+esc(item.museum_url)+'" target="_blank" rel="noopener">פעילויות המוזיאון ←</a>':'')+
        '<a class="primaryAction" href="'+mapsUrl(item.map_query||item.name+" ראשון לציון")+'" target="_blank" rel="noopener">איך מגיעים ←</a>'+
      '</div>'+
    '</div>'+
  '</article>';
}
function renderFilters(cat){
  const wrap=$("placeFilters");
  const heading=$("placesFilterTitle");
  if(heading)heading.textContent=cat.filter_title||"מה מתאים לכם?";
  wrap.innerHTML=(cat.filters||[]).map(f=>
    '<button class="'+(state.filter===f.id?"is-active":"")+'" data-filter="'+esc(f.id)+'">'+esc(f.label)+'</button>'
  ).join("");
  $("placesToolbar").hidden=false;
  wrap.onclick=e=>{
    const b=e.target.closest("[data-filter]");if(!b)return;
    state.filter=b.dataset.filter;
    renderGrid(cat);
    renderFilters(cat);
  };
}
function renderGrid(cat){
  const arr=(cat.items||[]).filter(x=>state.filter==="all"||(x.tags||[]).includes(state.filter));
  $("placesGrid").innerHTML=arr.length
    ?arr.map(placeCard).join("")
    :'<div class="emptyPlaces"><b>לא מצאנו מקום בסינון הזה</b><span>בחרו אפשרות אחרת.</span></div>';
}
function renderSafety(cat){
  if(!cat.safety_title&&!cat.safety_text)return;
  $("safetyTitle").textContent=cat.safety_title||"";
  $("safetyText").textContent=cat.safety_text||"";
  const official=$("officialStatusLink"),tourism=$("tourismSourceLink");
  if(cat.official_status_url)official.href=cat.official_status_url;else official.hidden=true;
  if(cat.tourism_source_url)tourism.href=cat.tourism_source_url;else tourism.hidden=true;
  $("safetyCard").hidden=false;
}
function renderBeachInfo(cat){
  if(state.category!=="beaches")return;
  const info=$("beachInfo"); if(!info)return;

  if(cat.season){
    $("seasonCard").innerHTML=
      '<span class="infoPanel__label">עונת הרחצה</span>'+
      '<h2>'+esc(cat.season.title||"")+'</h2>'+
      '<div class="seasonDates"><b>'+esc(cat.season.start||"")+'</b><span>עד</span><b>'+esc(cat.season.end||"")+'</b></div>'+
      '<strong class="seasonHours">'+esc(cat.season.current_hours||"")+'</strong>'+
      '<p>'+esc(cat.season.note||"")+'</p>'+
      (cat.season.source_url?'<a href="'+esc(cat.season.source_url)+'" target="_blank" rel="noopener">לשעות הרשמיות ←</a>':'');
  }

  if(cat.environment){
    $("environmentCard").innerHTML=
      '<span class="infoPanel__label">'+esc(cat.environment.badge||"")+'</span>'+
      '<h2>'+esc(cat.environment.title||"")+'</h2>'+
      '<p>'+esc(cat.environment.text||"")+'</p>'+
      (cat.environment.source_url?'<a href="'+esc(cat.environment.source_url)+'" target="_blank" rel="noopener">למידע העירוני ←</a>':'');
  }

  if(cat.daily_status){
    $("dailyStatusCard").innerHTML=
      '<span class="infoPanel__label">מצב הים</span>'+
      '<h2>'+esc(cat.daily_status.title||"")+'</h2>'+
      '<p>'+esc(cat.daily_status.text||"")+'</p>'+
      (cat.daily_status.source_url?'<a href="'+esc(cat.daily_status.source_url)+'" target="_blank" rel="noopener">מצב החופים בראשון נט ←</a>':'');
  }

  $("beachRules").innerHTML=(cat.rules||[]).map((rule,i)=>
    '<div class="beachRule"><span>'+(i+1)+'</span><p>'+esc(rule)+'</p></div>'
  ).join("");

  info.hidden=false;
}
function renderComingSoon(){
  const title=titles[state.category]||"מה עושים בראשון לציון?";
  $("placesHero").hidden=true;
  $("placesToolbar").hidden=true;
  $("placesPanel").hidden=true;
  $("safetyCard").hidden=true;
  $("comingSoonTitle").textContent=title;
  $("comingSoon").hidden=false;
  document.title=title+" | מה עושים בראשון לציון?";
}
async function init(){
  try{
    const data=await fetch("data/places.json?ts="+Date.now(),{cache:"no-store"}).then(r=>{if(!r.ok)throw new Error("places data");return r.json()});
    state.data=data;
    const cat=data.categories?.[state.category];
    if(!cat){renderComingSoon();return}
    if(state.category==="kids-attractions"){document.body.classList.add("kidsAttractionsPage");$("placesHero").insertAdjacentHTML("beforebegin",'<a class="kidsAttractionsBack" href="category.html?category=kids">לעולם הילדים בראשון לציון ←</a>');$("tourismSourceLink").textContent="עוד רעיונות באתר טיולי ↗";}
    renderHero(cat);
    renderFilters(cat);
    renderGrid(cat);
    renderBeachInfo(cat);
    renderSafety(cat);
    $("placesPanel").hidden=false;
    if(location.hash)document.getElementById(decodeURIComponent(location.hash.slice(1)))?.scrollIntoView({block:"start"});
  }catch(err){
    console.error(err);
    renderComingSoon();
  }
}
init();
