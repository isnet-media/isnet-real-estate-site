// ISNET shared layout: edit events-preview/ashdod, not this generated file.
const $=id=>document.getElementById(id);
const fmtFull=new Intl.DateTimeFormat("he-IL",{weekday:"long",day:"numeric",month:"long",year:"numeric"});
const fmtShort=new Intl.DateTimeFormat("he-IL",{weekday:"short",day:"numeric",month:"short"});
function escapeHtml(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}
function localDate(s){const [y,m,d]=String(s||"").split("-").map(Number);return new Date(y,m-1,d)}
function movieUrl(id){return window.CinemaEditorial?.url(id)||"movie.html?id="+encodeURIComponent(id)}
function venueLabel(id){return id==="cinema-city"?"סינמטק יבנה":"סינמטק יבנה יבנה"}
function cinemaToday(){return new Intl.DateTimeFormat("sv-SE",{timeZone:"Asia/Jerusalem",year:"numeric",month:"2-digit",day:"2-digit"}).format(new Date())}
function activeMovieVenues(movie){return movie.venues.filter(v=>Object.entries(v.schedule||{}).some(([day,times])=>day>=cinemaToday()&&Array.isArray(times)&&times.length))}
function allDates(movie){
  const dates=new Set();
  activeMovieVenues(movie).forEach(v=>Object.keys(v.schedule||{}).filter(d=>d>=cinemaToday()&&Array.isArray(v.schedule[d])&&v.schedule[d].length).forEach(d=>dates.add(d)));
  return [...dates].sort();
}
function renderHero(movie){
  document.title=movie.title+" | מה עושים ביבנה?";
  document.querySelector('meta[name="description"]').setAttribute("content",movie.synopsis||"כל שעות ההקרנה והפרטים על הסרט ביבנה.");
  $("movieTitle").textContent=movie.title;

  const badges=[];
  if(movie.is_family)badges.push('<span class="badge family">ילדים ומשפחה</span>');

  $("heroBadges").innerHTML=badges.join("");
  $("heroMeta").innerHTML=[
    movie.trailer_youtube_id?"טריילר זמין":null,
    movie.runtime_minutes?movie.runtime_minutes+" דקות":null,
    movie.age_rating,
    (movie.genres||[]).join(" · ")
  ].filter(Boolean).map(x=>'<span>'+escapeHtml(x)+'</span>').join("");
  const imageFallback=movie.poster_candidates?.["hot-cinema"]?.url||(movie.trailer_youtube_id?"https://i.ytimg.com/vi/"+encodeURIComponent(movie.trailer_youtube_id)+"/hqdefault.jpg":"");
  if(movie.trailer_youtube_id){
    const img=movie.poster_url||"https://i.ytimg.com/vi/"+encodeURIComponent(movie.trailer_youtube_id)+"/hqdefault.jpg";
    $("heroMedia").innerHTML='<button id="heroMediaTrailer" class="heroPoster" type="button"><img src="'+escapeHtml(img)+'" alt="'+escapeHtml(movie.title)+'" referrerpolicy="no-referrer" data-image-fallback="'+escapeHtml(imageFallback)+'" onerror="if(this.dataset.imageFallback){const u=this.dataset.imageFallback;delete this.dataset.imageFallback;if(u!==this.src){this.src=u}else{this.remove()}}else{this.remove()}"><span><i>▶</i><b>צפו בטריילר</b></span></button>';
    $("heroMediaTrailer").onclick=()=>document.getElementById("trailerSection")?.scrollIntoView({behavior:"smooth",block:"start"});
  }else{
    $("heroMedia").innerHTML=movie.poster_url?'<img class="officialPoster" src="'+escapeHtml(movie.poster_url)+'" alt="כרזת הסרט '+escapeHtml(movie.title)+'" referrerpolicy="no-referrer" data-image-fallback="'+escapeHtml(imageFallback)+'" onerror="if(this.dataset.imageFallback){const u=this.dataset.imageFallback;delete this.dataset.imageFallback;if(u!==this.src){this.src=u}else{this.remove()}}else{this.remove()}">':'<div class="heroFallback"><span>🎬</span><b>'+escapeHtml(movie.title)+'</b></div>';

  }
}
function screeningLanguage(venue,date,time){
  const languages=[...new Set((venue.sessions||[]).filter(s=>s.date===date&&s.time===time).map(s=>s.dubbed_language).filter(Boolean))];
  const labels={he:"עברית",ru:"רוסית",en:"אנגלית",fr:"צרפתית"};
  return languages.map(l=>"מדובב: "+(labels[l]||l)).join(" / ");
}
function screeningBookingUrl(venue,date,time){
  const urls=[...new Set((venue.sessions||[]).filter(s=>s.date===date&&s.time===time).map(s=>s.booking_url).filter(url=>/^https:\/\//.test(url||"")))];
  if(urls.length===1)return urls[0];
  return /^https:\/\//.test(venue.article_url||"")?venue.article_url:"";
}
function renderSchedules(movie){
  $("cinemaSchedules").innerHTML=movie.venues.map(v=>{
    const dates=Object.keys(v.schedule||{}).filter(d=>d>=cinemaToday()&&Array.isArray(v.schedule[d])&&v.schedule[d].length).sort();
    const rows=dates.length?dates.map(date=>{
      const times=(v.schedule[date]||[]).map(t=>{
        const url=screeningBookingUrl(v,date,t),label=t+(screeningLanguage(v,date,t)?" · "+screeningLanguage(v,date,t):"");
        return url?'<a class="showtime" href="'+escapeHtml(url)+'" target="_blank" rel="noopener noreferrer" aria-label="'+escapeHtml("פרטים והזמנה · "+movie.title+" · "+v.name+" · "+date+" · "+label)+'">'+escapeHtml(label)+'</a>':'<span class="showtime">'+escapeHtml(label)+'</span>';
      }).join("");
      return '<div class="dayRow">'+
        '<div class="dayDate"><b>'+escapeHtml(fmtShort.format(localDate(date)))+'</b><span>'+escapeHtml(date.split("-").reverse().join("."))+'</span></div>'+
        '<div class="dayTimes">'+times+'</div>'+
      '</div>';
    }).join(""):'<div class="noSchedule">אין כרגע שעות הקרנה מאומתות במאגר. בדקו באתר הרשמי של בית הקולנוע.</div>';
    return '<section class="cinemaBlock">'+
      '<div class="cinemaBlock__head"><div><span>בית קולנוע</span><h3>'+escapeHtml(v.name)+'</h3></div>'+
      '<span class="screeningCount">הקרנות קרובות</span></div>'+
      '<div class="daysList">'+rows+'</div>'+
    '</section>';
  }).join("");
}
function renderTrailer(movie){
  if(!movie.trailer_youtube_id){$("trailerSection").hidden=false;$("youtubeFrame").parentElement.hidden=true;$("trailerAvailability").textContent="טריילר רשמי לסרט זה טרם אומת. נציג אותו כשיימצא מקור מתאים.";$("trailerExternal").hidden=true;$("trailerExternal").style.display="none";$("youtubeFrame").parentElement.style.display="none";return}
  $("trailerSection").hidden=false;
  $("trailerAvailability").textContent=movie.trailer_verification?.publisher_kind==="cinema_portal"?"טריילר מאומת המקושר מעמוד הסרט באתר רשת הקולנוע.":"קדימון מערוץ המפיץ או היוצר.";
  $("trailerExternal").href="https://www.youtube.com/watch?v="+encodeURIComponent(movie.trailer_youtube_id);
  $("youtubeFrame").src="https://www.youtube-nocookie.com/embed/"+encodeURIComponent(movie.trailer_youtube_id)+"?rel=0";
  $("youtubeFrame").title="טריילר - "+movie.title;
}
function renderSources(movie,updatedAt){
  const venues=activeMovieVenues(movie).filter(v=>/^https:\/\//.test(v.article_url||""));
  $("ticketLinks").innerHTML=venues.map(v=>'<a href="'+escapeHtml(v.article_url)+'" target="_blank" rel="noopener noreferrer">ב'+escapeHtml(v.name.replace('סינמטק יבנה','הוט סינמה'))+' <span aria-hidden="true">↗</span></a>').join('');
  $("ticketAvailability").hidden=venues.length>0;
  if(updatedAt){
    const d=new Date(updatedAt);
    if(!Number.isNaN(d.getTime()))$("updatedAt").textContent="הנתונים עודכנו "+new Intl.DateTimeFormat("he-IL",{day:"numeric",month:"numeric",year:"numeric",hour:"2-digit",minute:"2-digit"}).format(d);
  }
}
function renderRelated(movie,all){
  let related=all.filter(m=>m.id!==movie.id&&allDates(m).length);
  related.sort((a,b)=>{
    const af=Boolean(a.is_family)===Boolean(movie.is_family)?0:1;
    const bf=Boolean(b.is_family)===Boolean(movie.is_family)?0:1;
    return af-bf||a.title.localeCompare(b.title,"he");
  });
  $("relatedGrid").innerHTML=related.slice(0,4).map(m=>{
    const img=m.poster_url||(m.trailer_youtube_id?"https://i.ytimg.com/vi/"+encodeURIComponent(m.trailer_youtube_id)+"/hqdefault.jpg":"");
    return '<a class="relatedCard" href="'+movieUrl(m.id)+'">'+
      '<div class="relatedCard__media">'+(img?'<img src="'+escapeHtml(img)+'" alt="" onerror="this.remove()">':'<div class="relatedFallback">🎬</div>')+'</div>'+
      '<div class="relatedCard__body">'+(m.is_family?'<span class="miniBadge">ילדים ומשפחה</span>':'')+'<h3>'+escapeHtml(m.title)+'</h3><span>'+escapeHtml(m.venues.map(v=>v.id==="cinema-city"?"סינמה סיטי":"סינמטק יבנה").join(" · "))+'</span></div>'+
    '</a>';
  }).join("");
}
function configureDescription(){
  const text=$("fullSynopsis"),button=$("synopsisToggle");
  if(!text||!button)return;
  const expanded=button.getAttribute("aria-expanded")==="true";
  text.classList.add("is-collapsed");
  const overflows=text.scrollHeight>text.clientHeight+1;
  text.classList.toggle("is-collapsed",overflows&&!expanded);
  button.hidden=!overflows;
  button.textContent=expanded?"קרא פחות":"קרא עוד";
  button.onclick=()=>{
    const next=button.getAttribute("aria-expanded")!=="true";
    button.setAttribute("aria-expanded",String(next));
    text.classList.toggle("is-collapsed",!next);
    button.textContent=next?"קרא פחות":"קרא עוד";
  };
}
configureDescription();
if(document.fonts?.ready)document.fonts.ready.then(configureDescription);
window.addEventListener("resize",configureDescription);
async function init(){
  try{
    await window.CinemaEditorial?.ready;
    const id=new URLSearchParams(location.search).get("id")||document.body.dataset.movieId;
    if(!id)throw new Error("missing id");
    const data=await fetch("data/cinema.json",{cache:"no-store"}).then(r=>{if(!r.ok)throw new Error("data");return r.json()});
    const movie=window.CinemaEditorial?.merge(data.movies||[],id)||(data.movies||[]).find(m=>m.id===id||(m.aliases||[]).includes(id));
    if(!movie)throw new Error("movie");
    const cleanUrl=window.CinemaEditorial?.url(id);
    if(!document.body.dataset.staticMovie&&cleanUrl?.startsWith("/events-preview/")){location.replace(cleanUrl+location.hash);return}
    renderHero(movie);
    renderSchedules(movie);
    renderTrailer(movie);
    if(movie.editorial_text||!document.body.dataset.staticMovie)$("fullSynopsis").textContent=movie.editorial_text||movie.synopsis||"פרטי הסרט יתעדכנו כאן.";
    renderSources(movie,data.updated_at);
    window.CinemaEditorial?.mount(movie);
    configureDescription();
    renderRelated(movie,window.CinemaEditorial?.unique(data.movies||[])||data.movies||[]);
    $("loadingState").hidden=true;
    $("page").hidden=false;
    if(location.hash==="#showtimes"||location.hash==="#trailerSection")requestAnimationFrame(()=>document.getElementById(location.hash.slice(1))?.scrollIntoView({block:"start"}));
  }catch(err){
    console.error(err);
    $("loadingState").hidden=true;
    if(document.body.dataset.staticMovie){$("page").hidden=false;return}
    $("errorState").hidden=false;
  }
}
init();