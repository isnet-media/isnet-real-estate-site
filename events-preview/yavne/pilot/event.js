// ISNET shared layout: edit events-preview/ashdod, not this generated file.

const $=id=>document.getElementById(id);
const catLabels={conference:"כנסים ופאנלים",food:"אוכל וקולינריה",tour:"טיולים וסיורים",
  music:"מוזיקה",standup:"סטנדאפ",kids:"ילדים ומשפחה",theatre:"תיאטרון",
  lecture:"הרצאות",exhibition:"תערוכות",cinema:"קולנוע",
  community:"קהילה",sport:"ספורט ביבנה",tour:"סיורים",other:"אירוע"
};
let sportsMeta={branches:{},teams:[]};
const fmtFull=new Intl.DateTimeFormat("he-IL",{weekday:"long",day:"numeric",month:"long",year:"numeric"});
const fmtMonth=new Intl.DateTimeFormat("he-IL",{month:"short"});
const currency=new Intl.NumberFormat("he-IL",{style:"currency",currency:"ILS",maximumFractionDigits:0});

function escapeHtml(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}
function normalizeSearch(s){
  return String(s||"").normalize("NFKD").replace(/\p{M}/gu,"").toLowerCase()
    .replace(/[״"'׳.,!?():;\/\-–—]/g," ")
    .replace(/\s+/g," ").trim();
}
function eventGroupKey(e){
  if(e?.series_id)return "series:"+String(e.series_id);
  return normalizeSearch(e?.title||"");
}
function eventDisplayTitle(e){
  return e?.series_title||e?.title||"אירוע";
}
function localDate(s){const [y,m,d]=String(s||"").split("-").map(Number);return new Date(y,m-1,d)}
function formatTime(t){return t||"השעה תפורסם"}
function priceText(e){
  if(e.is_free===true)return "חינם";
  if(e.price_min_ils==null)return "מחיר לא פורסם";
  if(e.price_is_starting)return "החל מ־"+currency.format(e.price_min_ils);
  if(e.price_max_ils!=null&&e.price_max_ils!==e.price_min_ils)return currency.format(e.price_min_ils)+"–"+currency.format(e.price_max_ils);
  return currency.format(e.price_min_ils);
}
function sportKey(e){
  const b=String(e?.sport_branch||"");
  if(b.includes("כדורגל"))return "football";
  if(b.includes("כדורסל"))return "basketball";
  if(b.includes("כדוריד"))return "handball";
  if(b.includes("כדורעף"))return "volleyball";
  if(b.includes("גלישה"))return "surfing";
  return "other";
}
function sportBranchMeta(eOrKey){
  const key=typeof eOrKey==="string"?eOrKey:sportKey(eOrKey);
  return sportsMeta?.branches?.[key]||{label:"ספורט",icon:"⚑"};
}
function sportTeamConfig(e){
  const home=String(e?.home_team||"").trim(),key=sportKey(e);
  return (sportsMeta?.teams||[]).find(t=>(t.match_home_teams||[]).includes(home)&&(!(t.sports||[]).length||(t.sports||[]).includes(key)))||null;
}
function teamInitials(name){
  return String(name||"קבוצה").split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join("");
}
function isRepresentativeHomeGame(e){
  return e?.category==="sport"&&e?.is_home_game===true&&e?.representative_team===true&&Boolean(e?.home_team);
}
function sportHeroFallback(e){
  const team=sportTeamConfig(e),branch=sportBranchMeta(e),name=team?.name||e.home_team||"ספורט ביבנה";
  const logo=team?.logo_url?'<img src="'+escapeHtml(team.logo_url)+'" alt="" onerror="this.remove()">':'<b>'+escapeHtml(teamInitials(name))+'</b>';
  return '<div class="fallback sportHeroFallback"><span class="sportHeroLogo">'+logo+'</span><span class="sportHeroBranch">'+escapeHtml(branch.icon)+' '+escapeHtml(branch.label)+'</span><strong>'+escapeHtml(name)+'</strong><small>משחק בית ביבנה</small></div>';
}
function isBlockedPurchaseUrl(url){
  try{
    const host=new URL(url,location.href).hostname.toLowerCase();
    return host==="live.tickchak.co.il"||host==="tickchak.co.il"||host.endsWith(".tickchak.co.il");
  }catch{return true}
}
let purchaseHealth={results:{}};
function isBrokenPurchaseUrl(url){
  const result=purchaseHealth.results?.[url],age=Date.now()-Date.parse(result?.checked_at||'');
  return result?.state==='broken'&&Number.isFinite(age)&&age>=0&&age<7*86400000;
}
function purchaseAction(e){
  if(["cancelled","canceled","postponed"].includes(e.status))return null;
  if(!isUpcoming(e))return null;
  const url=String(e.purchase_url||"").trim();
  if(!isBrokenPurchaseUrl(url)&&/^https:\/\//i.test(url)&&(e.source_content_authoritative||!isBlockedPurchaseUrl(url))){
    return {href:url,label:e.ticket_status==="sold_out"?"פרטי הרכישה":"לרכישת כרטיסים",kind:"url",soldOut:e.ticket_status==="sold_out"};
  }
  if(e.ticket_status==="sold_out")return null;
  const phone=String(e.purchase_phone||e.contact_phone||e.venue_phone||"").trim().replace(/[^0-9+]/g,"");
  if(phone)return {href:"tel:"+phone,label:"טלפון לבירורים",kind:"phone"};
  const source=String(e.venue_website||e.ticket_url||"").trim();
  if(!isBrokenPurchaseUrl(source)&&/^https:\/\//i.test(source))return {href:source,label:e.venue_website?"לאתר המארגן":"לעמוד האירוע",kind:"url"};
  return null;
}
function groupPurchaseAction(occ){
  if(occ.every(e=>!isUpcoming(e)))return null;
  for(const e of occ){
    const a=purchaseAction(e);
    if(a)return a;
  }
  return null;
}
function trustedImage(e){
  return Boolean(!(window.isnetEventDefaultImage?.(e)&&window.isnetEventIllustration?.(e))&&e.image_url&&e.image_publishable===true&&e.image_verified===true&&e.source_image_kind!=="source_placeholder"&&(e.image_represents_event!==false||e.source_image_kind==="illustration")&&!/microsoft_oauth_logo|no_pic\.png|favicon|\/placeholders\/|\/images\/live\/more\/eventNew\.jpg|\/images\/artists\/artistShadow\.png/i.test(e.image_url));
}
function bestImageEvent(occ){
  return occ.find(e=>e.image_source==="friends"&&trustedImage(e))
    ||occ.find(e=>e.source_content_authoritative&&trustedImage(e))
    ||occ.find(e=>trustedImage(e)&&e.thumbnail_ready===true)
    ||occ.find(e=>trustedImage(e))
    ||occ[0];
}
function richEvent(occ){
  return occ.find(e=>e.source_content_authoritative)
    ||occ.find(e=>e.rich_content_status==="enriched")
    ||occ.find(e=>e.long_description||e.short_pitch||e.youtube_id)
    ||occ[0];
}
function recommendationKey(e){
  const title=normalizeSearch(eventDisplayTitle(e));
  return e.category==="standup"?title.replace(/\s+(?:ב?מופע\s+)?סטנדאפ$/,""):title;
}
function uniqueByTitle(events){
  const seen=new Set(),out=[];
  for(const e of events){
    const k=recommendationKey(e);
    if(seen.has(k))continue;
    seen.add(k);out.push(e);
  }
  return out;
}
function slugifyHebrew(value,limit=90){
  return String(value||"").normalize("NFKC").trim().toLowerCase()
    .replace(/["'״׳]/g,"")
    .replace(/[^\p{L}\p{N}]+/gu,"-")
    .replace(/^-+|-+$/g,"")
    .slice(0,limit);
}
function eventSlug(e){
  if(e?.seo_slug)return slugifyHebrew(e.seo_slug);
  const base=slugifyHebrew(eventDisplayTitle(e))||"event";
  const suffix=String(e?.event_id||"").replace(/[^a-zA-Z0-9]+/g,"").slice(-8).toLowerCase();
  return suffix?base+"-"+suffix:base;
}
function findSlugEvent(events,requested){
  const normalized=slugifyHebrew(requested,200),exact=events.find(e=>eventSlug(e)===normalized);
  if(exact)return exact;
  // Source collectors can replace an imported ID with its verified source ID.
  // Recover only the exact display title of a generated slug, in one unambiguous group.
  if(!/-[a-z0-9]{8}$/.test(normalized))return null;
  const title=normalized.replace(/-[a-z0-9]{8}$/,''),matches=events.filter(e=>slugifyHebrew(eventDisplayTitle(e))===title);
  if(!matches.length||new Set(matches.map(eventGroupKey)).size!==1)return null;
  return matches.slice().sort((a,b)=>String(a.event_id).localeCompare(String(b.event_id)))[0];
}
function directEventUrl(eventOrId){
  const e=typeof eventOrId==="object"?eventOrId:null;
  return e?"event.html?slug="+encodeURIComponent(eventSlug(e)):"event.html?id="+encodeURIComponent(eventOrId);
}
function ensureMeta(propertyOrName,value,isProperty=false){
  if(!value)return;
  const selector=isProperty?'meta[property="'+propertyOrName+'"]':'meta[name="'+propertyOrName+'"]';
  let el=document.head.querySelector(selector);
  if(!el){el=document.createElement("meta");el.setAttribute(isProperty?"property":"name",propertyOrName);document.head.appendChild(el)}
  el.setAttribute("content",value);
}
function canonicalEventUrl(e){return new URL("event.html?slug="+encodeURIComponent(e._canonical_slug||eventSlug(e)),location.href).href;}
function applySeo(e){
  const localTitle=e.seo_title||eventDisplayTitle(e);
  const title=(localTitle.includes("יבנה")?localTitle:localTitle+" ביבנה")+" | מה עושים ביבנה";
  const desc=(safeEditorial(e.seo_description)||meaningfulEventDescription(e)||autoPitch({...e,title:eventDisplayTitle(e)})).slice(0,180);
  const canonical=canonicalEventUrl(e);
  document.title=title;
  document.querySelector('meta[name="description"]')?.setAttribute("content",desc);
  let link=document.head.querySelector('link[rel="canonical"]');
  if(!link){link=document.createElement("link");link.rel="canonical";document.head.appendChild(link)}
  link.href=canonical;
  ensureMeta("og:type","website",true);
  ensureMeta("og:title",title,true);
  ensureMeta("og:description",desc,true);
  ensureMeta("og:url",canonical,true);
  const image=e.thumbnail_url||e.image_url;
  if(image)ensureMeta("og:image",new URL(image,location.href).href,true);
  ensureMeta("twitter:card",image?"summary_large_image":"summary");
  ensureMeta("twitter:title",title);
  ensureMeta("twitter:description",desc);
  const schema={
    "@context":"https://schema.org",
    "@type":"Event",
    name:eventDisplayTitle(e),
    startDate:e.start_date+(e.start_time?"T"+e.start_time:""),
    eventStatus:["cancelled","canceled"].includes(e.status)?"https://schema.org/EventCancelled":e.status==="postponed"?"https://schema.org/EventPostponed":"https://schema.org/EventScheduled",
    endDate:e.end_date||undefined,
    eventAttendanceMode:"https://schema.org/OfflineEventAttendanceMode",
    location:e.venue?{"@type":"Place",name:e.venue,...(e.address?{address:e.address}:{})}:undefined,
    image:image?[new URL(image,location.href).href]:undefined,
    description:desc,
    url:canonical,
    offers:(e.purchase_url||e.ticket_url)?{"@type":"Offer",url:e.purchase_url||e.ticket_url,...(e.ticket_status==="sold_out"?{availability:"https://schema.org/SoldOut"}:e.ticket_status==="available"?{availability:"https://schema.org/InStock"}:{}),...(e.is_free===true?{price:0,priceCurrency:"ILS"}:typeof e.price_min_ils==="number"?{price:e.price_min_ils,priceCurrency:"ILS"}:{})}:undefined
  };
  Object.keys(schema).forEach(k=>schema[k]===undefined&&delete schema[k]);
  let script=document.getElementById("eventSchema");
  if(!script){script=document.createElement("script");script.id="eventSchema";script.type="application/ld+json";document.head.appendChild(script)}
  script.textContent=JSON.stringify(schema);
  window.ISNET_SEO?.event(e);
}
function isUpcoming(e,now=new Date()){
  const today=new Intl.DateTimeFormat("sv-SE",{timeZone:"Asia/Jerusalem",year:"numeric",month:"2-digit",day:"2-digit"}).format(now);
  if(!/^\d{4}-\d{2}-\d{2}$/.test(e.start_date||""))return false;
  if(e.status==="cancelled"||e.publication_status==="draft"||e.is_active===false)return false;
  if(e.start_date>today)return true;
  if(e.start_date<today)return false;
  if(!/^\d{2}:\d{2}$/.test(e.start_time||""))return true;
  const clock=new Intl.DateTimeFormat("en-GB",{timeZone:"Asia/Jerusalem",hour:"2-digit",minute:"2-digit",hourCycle:"h23"}).format(now);
  return e.start_time>=clock;
}
function safeEditorial(value){
  const text=cleanEditorialText(value);
  if(/מה שמרמז|לא ניתן לאשר|בגרסאות קודמות/.test(text))return "";
  if(/(?:טיקצ[׳\x27]?אק|tickchak).{0,120}(?:מגוון|אירועים|כרטיסים|מופעים|אתר)|(?:מגוון|אירועים|כרטיסים|מופעים|אתר).{0,120}(?:טיקצ[׳\x27]?אק|tickchak)/i.test(text))return "";
  return window.ISNET_EDITORIAL_SAFETY?.publicText(text)??text;
}
function cleanEditorialText(value){
  let text=String(value||"");
  text=text.replace(/[^.!?\n]*(?:לא פורסם בעמוד המקור|לא צוין במקור|לא ניתן לאמת|לפני פרסום|נדרש לאמת)[^.!?\n]*[.!?]?/g,"");
  text=text.replace(/\\([()_:/])/g,"$1");
  text=text.replace(/\(\s*\[([^\]]+)\]\(\s*https?:\/\/[^)]+\)\s*\)/gi,"");
  text=text.replace(/\[([^\]]+)\]\(\s*https?:\/\/[^)]+\)/gi,"$1");
  text=text.replace(/\(\s*\[([^\]]+)\]\s*\)/g,"");
  text=text.replace(/\[?(?:www\.)?[A-Za-z0-9.-]+\.(?:co\.il|com|org|net|il)\]?\s*\(?\s*https?:\/\/[^)\s]+\)?/gi,"");
  text=text.replace(/https?:\/\/[^\s)]+/gi,"");
  return text.replace(/\s+([,.;:!?])/g,"$1").replace(/\(\s*\)/g,"").replace(/\s{2,}/g," ").trim();
}
function splitParagraphs(text){
  return String(text||"").split(/\n\s*\n/).map(x=>x.trim()).filter(Boolean);
}
function categoryExperience(e){
  const map={
    music:"ערב של מוזיקה והופעה חיה",
    standup:"ערב של סטנדאפ והומור",
    kids:"בילוי לילדים ולמשפחה",
    theatre:"ערב של תיאטרון ובמה",
    lecture:"מפגש של תוכן, ידע והשראה",
    exhibition:"בילוי של אמנות ותרבות",
    workshop:"פעילות מעשית וסדנה",
    cinema:"אירוע קולנוע והקרנה",

    community:"מפגש קהילתי",
    sport:"משחק בית או אירוע ספורטיבי בעיר",
    tour:"סיור וחוויה בעיר"
  };
  return map[e.category]||"אירוע תרבות ופנאי";
}
function autoPitch(e){
  const where=e.venue&&e.venue!=="יבנה"?" • "+e.venue:"";
  return e.title+where+" • "+fmtFull.format(localDate(e.start_date))+" • "+formatTime(e.start_time)+
    (e.ticket_status==="sold_out"?" • הכרטיסים אזלו":"");
}
function meaningfulEventDescription(e){
  if(e.source_content_authoritative)return String(e.series_description||e.description||"").trim();
  // Prefer editorial descriptions already attributed to this event.
  // Research citations and URLs are never part of public editorial copy.
  const candidates=e.content_source_url && e.description_manual_override!==true
    ? [e.series_description,e.description,e.long_description,e.short_pitch]
    : [e.long_description,e.series_description,e.description,e.short_pitch];
  return candidates.map(safeEditorial).find(v=>
    v.length>=25 &&
    !/(?:טיקצ[׳\x27]?אק|tickchak).{0,120}(?:מגוון|אירועים|כרטיסים|מופעים|אתר)/i.test(v) &&
    !/(?:מגוון|אירועים|כרטיסים|מופעים|אתר).{0,120}(?:טיקצ[׳\x27]?אק|tickchak)/i.test(v) &&
    !v.includes("תיאור מפורט של האירוע לא פורסם") &&
    !v.includes("המועד, המחיר, המיקום ודרכי יצירת הקשר מופיעים")
  )||"";
}
function autoHighlights(e,occ){
  const items=[];
  if(occ.length>1)items.push("מועדי האירוע מפורטים בעמוד");
  else items.push("מועד האירוע מרוכז וברור בעמוד");
  if(e.venue)items.push("מיקום: "+e.venue);
  else items.push("פרטי המקום יתעדכנו עם פרסומם");
  if(groupPurchaseAction(occ))items.push("קישור רכישה ישיר זמין מהעמוד");
  else items.push("פרטי רכישה יעודכנו לאחר אימות");
  return items;
}
function autoSuitability(e){
  const map={
    music:"מתאים למי שמחפש ערב מוזיקלי ובילוי תרבותי ביבנה.",
    standup:"מתאים למי שמחפש ערב סטנדאפ והומור. יש לבדוק מגבלת גיל אצל המארגן לפני רכישה.",
    kids:"מתאים למשפחות וילדים; מומלץ לבדוק את טווח הגילים המדויק אצל המארגן.",
    theatre:"מתאים לחובבי הצגות, במה ותיאטרון.",
    lecture:"מתאים למי שמחפש הרצאה, העשרה ותוכן.",
    exhibition:"מתאים לחובבי אמנות, תרבות ותערוכות.",
    workshop:"מתאים למי שמחפש פעילות מעשית או סדנה.",
    cinema:"מתאים למי שמחפש הקרנה או אירוע קולנוע.",
    community:"מתאים למי שמחפש פעילות ומפגש קהילתי בעיר.",
    sport:"מתאים למי שמחפש פעילות ספורטיבית; מומלץ לבדוק דרישות השתתפות אצל המארגן.",

    tour:"מתאים למי שמחפש סיור או פעילות היכרות עם העיר."
  };
  return map[e.category]||"מתאים למי שמחפש בילוי, תרבות ופנאי ביבנה.";
}

function renderHero(e,occ,imageEvent){
  const displayTitle=eventDisplayTitle(e);
  applySeo(e);

  const sportBadge=e.category==="sport"?sportBranchMeta(e):null;
  $("heroBadges").innerHTML=
    '<a class="badge accent categoryLink" href="index.html?category='+encodeURIComponent(e.category||"other")+'#events" title="לעוד אירועים בקטגוריה">'+escapeHtml(catLabels[e.category]||"אירוע")+' ←</a>'+
    (e.status==="cancelled"?'<span class="badge badge--soldout">האירוע בוטל</span>':e.status==="postponed"?'<span class="badge badge--soldout">האירוע נדחה — בדקו מועד חדש אצל המארגן</span>':'')+
    (sportBadge?'<span class="badge">'+escapeHtml(sportBadge.icon)+' '+escapeHtml(sportBadge.label)+'</span>':"")+
    (occ.every(x=>x.ticket_status==="sold_out")?'<span class="badge badge--soldout">אזלו הכרטיסים</span>':"")+
    (occ.every(x=>!isUpcoming(x))?'<span class="badge badge--soldout">האירוע הסתיים</span>':"");
  $("eventTitle").textContent=displayTitle;
  window.ISNET_EVENT_TOOLS?.render(e,occ);
  $("eventPitch").textContent=safeEditorial(e.short_pitch)||meaningfulEventDescription(e).slice(0,240)||autoPitch({...e,title:displayTitle});

  const venues=[...new Set(occ.map(x=>x.venue).filter(Boolean))];
  const dates=[...new Set(occ.map(x=>x.start_date).filter(Boolean))];
  $("heroMeta").innerHTML=[
    venues[0]||"המיקום יפורסם",
    (dates.length>1?"המועד הקרוב: ":"")+fmtFull.format(localDate(occ[0].start_date)),
    formatTime(occ[0].start_time),
    priceText(occ[0]),
    e.duration_minutes?e.duration_minutes+" דקות":null
  ].filter(Boolean).map(x=>'<span>'+escapeHtml(x)+'</span>').join("");

  if(trustedImage(imageEvent)){
    const src=imageEvent.thumbnail_ready&&imageEvent.thumbnail_url?imageEvent.thumbnail_url:imageEvent.image_url;
    $("heroImage").innerHTML='<img data-event-image-id="'+escapeHtml(e.event_id)+'" src="'+escapeHtml(src)+'" alt="'+escapeHtml(eventDisplayTitle(e))+'">'+(imageEvent.image_caption?'<span class="image-caption" style="position:absolute;bottom:8px;right:8px;padding:4px 8px;background:#171717cc;color:white;font-size:12px">'+escapeHtml(imageEvent.image_caption)+'</span>':'');
  }else{
    const illustration=window.isnetEventIllustration?.(e);
    if(illustration){
      $("heroImage").innerHTML='<img src="'+escapeHtml(illustration.src)+'" alt="המחשה: '+escapeHtml(illustration.label)+'"><span class="image-caption" style="position:absolute;bottom:8px;left:8px;padding:4px 8px;background:#171717cc;color:white;font-size:12px">המחשה</span>';
    }else if(e.category==="lecture"){
      const key=String(e.event_id||e.title||"");
      const theme=[...key].reduce((n,c)=>(n*29+c.charCodeAt(0))>>>0,3)%6;
      $("heroImage").innerHTML='<div class="fallback detailLectureArt detailLectureArt--'+theme+'">'+
        '<span class="detailLectureArt__symbol" aria-hidden="true">✦</span><strong>'+escapeHtml(eventDisplayTitle(e))+
        '</strong><small>איור להמחשה</small></div>';
    }else{
      $("heroImage").innerHTML=isRepresentativeHomeGame(e)?sportHeroFallback(e):'<div class="fallback">'+escapeHtml(eventDisplayTitle(e))+'</div>';
    }
  }

  const action=groupPurchaseAction(occ);
  if(action){
    const a=$("heroBuy");
    a.href=action.href;a.textContent=action.label;a.style.display="inline-flex";
    if(action.kind==="phone")a.removeAttribute("target");else a.target="_blank";
    const soldOut=occ.every(x=>x.ticket_status==="sold_out");
    $("heroBuyNote").hidden=!soldOut;
    if(soldOut)$("heroBuyNote").textContent="הכרטיסים לאירוע אזלו. אפשר לצפות בפרטים באתר המקור ולפנות למקום לבירור.";
  }else{
    $("heroBuy").style.display="none";
    $("heroBuyNote").hidden=false;
    $("heroBuyNote").textContent=occ.every(x=>!isUpcoming(x))?"המועדים המופיעים בעמוד זה כבר חלפו.":"פרטי ההזמנה טרם פורסמו.";
  }
}

function renderStory(e,occ){
  const description=meaningfulEventDescription(e);
  const paragraphs=splitParagraphs(description);
  // Never display generic placeholder copy as event editorial content.
  // Schedule, venue, prices and organizer contact remain in their own cards.
  $("aboutSection").hidden=!paragraphs.length;
  $("eventStory").innerHTML=paragraphs.map(p=>'<p>'+escapeHtml(p)+'</p>').join("");

  // Do not fabricate marketing claims when only ticket metadata is available.
  const highlights=Array.isArray(e.highlights)?e.highlights.map(safeEditorial).filter(Boolean):[];
  const suitability=safeEditorial(e.suitability);
  $("highlightsSection").hidden=!highlights.length&&!suitability;
  $("highlights").innerHTML=highlights.map(x=>'<div class="highlight">'+escapeHtml(x)+'</div>').join("");
  $("suitability").textContent=suitability;
  $("suitability").hidden=!suitability;
}

function renderVideo(e){
  if(!e.youtube_id){
    $("videoSection").hidden=true;return;
  }
  $("videoSection").hidden=false;
  $("youtubeFrame").src="https://www.youtube-nocookie.com/embed/"+encodeURIComponent(e.youtube_id)+"?rel=0";
  $("youtubeFrame").title=e.youtube_title||("וידאו - "+e.title);
  $("youtubeTitle").textContent=e.youtube_title||"וידאו מהמופע";
  $("youtubeNote").textContent=safeEditorial(e.youtube_note);
}

function renderPeople(e){
  const performers=Array.isArray(e.performers)?e.performers.map(safeEditorial).filter(Boolean):[];
  const creators=Array.isArray(e.creators)?e.creators.map(safeEditorial).filter(Boolean):[];
  if(!performers.length&&!creators.length){
    $("peopleSection").hidden=true;return;
  }
  $("peopleSection").hidden=false;
  let html="";
  if(performers.length){
    html+='<div class="peopleBlock"><h3>על הבמה</h3><ul>'+performers.map(x=>'<li>'+escapeHtml(x)+'</li>').join("")+'</ul></div>';
  }
  if(creators.length){
    html+='<div class="peopleBlock"><h3>יוצרים</h3><ul>'+creators.map(x=>'<li>'+escapeHtml(x)+'</li>').join("")+'</ul></div>';
  }
  $("peopleGrid").innerHTML=html;
}

function sourceOfferLinks(e){
  if(!Array.isArray(e._source_offers)||e._source_offers.length<2)return "";
  return '<div class="sourceOffers"><b>אפשרויות הזמנה נוספות</b>'+e._source_offers
    .filter(o=>o.url!==(e.purchase_url||e.ticket_url))
    .map(o=>{
      const price=o.price_min_ils!=null?(o.price_is_starting?"החל מ־":"")+currency.format(o.price_min_ils):"בדקו מחיר באתר";
      const member=o.member_price_min_ils!=null?" · לחברי ההסתדרות החל מ־"+currency.format(o.member_price_min_ils):"";
      return '<a class="scheduleBuy" href="'+escapeHtml(o.url)+'" target="_blank" rel="noopener">'+escapeHtml(o.name+" · "+price+member)+" ←</a>";
    }).join("")+"</div>";
}
function renderSchedule(occ){
  const groupAction=groupPurchaseAction(occ);
  $("scheduleList").innerHTML=occ.map(e=>{
    const d=localDate(e.start_date);
    const own=purchaseAction(e)||groupAction;
    return '<div class="scheduleItem">'+
      '<div class="scheduleDate"><b>'+String(d.getDate()).padStart(2,"0")+'</b><span>'+escapeHtml(fmtMonth.format(d))+'</span></div>'+
      '<div class="scheduleCopy"><b>'+escapeHtml(fmtFull.format(d))+'</b>'+
        (e.variant_label?'<strong class="scheduleVariant">'+escapeHtml(e.variant_label)+'</strong>':"")+
        '<span>'+escapeHtml(formatTime(e.start_time))+' · '+escapeHtml(e.venue||"המיקום יפורסם")+'</span>'+
        (own?'<a class="scheduleBuy" href="'+escapeHtml(own.href)+'" '+(own.kind==="url"?'target="_blank" rel="noopener"':'')+'>'+(e.ticket_status==="sold_out"?"אזלו הכרטיסים · לפרטי המקור ←":escapeHtml(own.label)+" ←")+'</a>':"")+
        sourceOfferLinks(e)+
      '</div>'+
    '</div>';
  }).join("");
}

function renderPractical(e,occ){
  const venues=[...new Set(occ.map(x=>x.venue).filter(Boolean))];
  const prices=occ.map(priceText);
  const onePrice=[...new Set(prices)].length===1?prices[0]:"המחיר משתנה לפי מועד";
  const audience=(Array.isArray(e.audiences)&&e.audiences.length)?e.audiences.map(a=>({seniors:"הגיל השלישי",women:"נשים",kids:"ילדים",families:"משפחות",adults:"מבוגרים"}[a]||a)).join(", "):null;
  const age=e.age_min!=null&&e.age_max!=null?"גילאי "+e.age_min+"–"+e.age_max:e.age_min!=null?"מגיל "+e.age_min:e.age_max!=null?"עד גיל "+e.age_max:null;
  const rows=[
    ["מקום",venues.filter(v=>v!==e.city).join(" / ")||"המיקום המדויק לא פורסם במקור"],
    ...(e.address?[["כתובת",e.address]]:[]),
    ["מחיר",onePrice],
    ...(typeof e.accessibility==="string"&&e.accessibility.trim()?[["נגישות",e.accessibility]]:[]),
    ["כרטיסים",occ.every(x=>x.ticket_status==="sold_out")?"אזלו הכרטיסים":"יש לבדוק זמינות באתר המקור"],
    ...(e.duration_minutes?[["משך",e.duration_minutes+" דקות"]]:[]),
    ...(age?[["גילים",age]]:[]),
    ...(audience?[["קהל",audience]]:[]),
    ...(e.organizer?[["מארגן",e.organizer]]:[]),
    ...(e.ticket_provider?[["מערכת כרטיסים",e.ticket_provider]]:[])
  ];
  const info=rows.map(([a,b])=>'<div class="infoRow"><b>'+escapeHtml(a)+'</b><span>'+escapeHtml(b)+'</span></div>').join("");
  const contact=String(e.contact_phone||e.purchase_phone||"").replace(/[^0-9+*]/g,"");
  const contactHtml=contact?'<div class="infoRow"><b>טלפון לבירורים</b><a href="tel:'+escapeHtml(contact)+'">'+escapeHtml(e.contact_phone||e.purchase_phone)+'</a>'+(e.contact_phone_secondary?'<a class="contactSecondary" href="tel:'+escapeHtml(String(e.contact_phone_secondary).replace(/[^0-9+]/g,""))+'">'+escapeHtml(e.contact_phone_secondary)+'</a>':"")+'</div>':"";
  const venueAddress=e.address||(e.venue&&e.venue!=="יבנה"&&!/לא פורסמ|לא פורסם/.test(e.venue)?e.venue:"");
  const maps=venueAddress?'<div class="infoRow"><b>ניווט</b><a href="https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(venueAddress)+'" target="_blank" rel="noopener">לפתיחת מפה ←</a></div>':"";
  const origin=String(e.ticket_url||e.purchase_url||"");
  const source=origin.startsWith("https://")?'<div class="infoRow"><b>מקור המידע</b><a href="'+escapeHtml(origin)+'" target="_blank" rel="noopener">לעמוד האירוע ←</a></div>':"";
  const safeOperator=/^[a-z0-9_]+$/.test(e.operator_id||"")?e.operator_id:null;
  const operatorPage=safeOperator?'<div class="infoRow"><b>כל הפעילויות של המפעיל</b>'+
    '<a href="operator.html?id='+encodeURIComponent(safeOperator)+'">'+escapeHtml(e.operator_name||e.organizer||"כל הפעילויות")+' ←</a></div>':"";
  const email=e.contact_email?'<div class="infoRow"><b>דואר אלקטרוני</b>'+
    '<a href="mailto:'+escapeHtml(e.contact_email)+'">'+escapeHtml(e.contact_email)+'</a></div>':"";
  const venuePhone=e.venue_phone&&e.venue_phone!==e.contact_phone?
    '<div class="infoRow"><b>טלפון המקום</b><a href="tel:'+escapeHtml(e.venue_phone.replace(/[^0-9+*]/g,""))+'">'+escapeHtml(e.venue_phone)+'</a></div>':"";
  $("practicalInfo").innerHTML=info+contactHtml+venuePhone+email+maps+operatorPage+source;
}
function renderRelated(current,all){
  const currentKey=eventGroupKey(current);
  const related=uniqueByTitle(
    all.filter(e=>eventGroupKey(e)!==currentKey&&recommendationKey(e)!==recommendationKey(current)&&e.category===current.category&&isUpcoming(e))
      .sort((a,b)=>(a.start_date+(a.start_time||"99:99")).localeCompare(b.start_date+(b.start_time||"99:99")))
  ).slice(0,3);

  $("relatedSection").hidden=!related.length;
  if(!related.length)return;
  $("relatedGrid").innerHTML=related.map(e=>{
    const img=trustedImage(e)?(e.thumbnail_ready&&e.thumbnail_url?e.thumbnail_url:e.image_url):null;
    return '<a class="relatedCard" href="'+directEventUrl(e)+'">'+
      '<div class="relatedCard__media">'+(img?'<img src="'+escapeHtml(img)+'" alt="">':'')+'</div>'+
      '<div class="relatedCard__body"><h3>'+escapeHtml(eventDisplayTitle(e))+'</h3><span>'+escapeHtml(fmtFull.format(localDate(e.start_date)))+'</span></div>'+
    '</a>';
  }).join("");
}

async function init(){
  try{
    const params=new URLSearchParams(location.search);
    const requestedId=params.get("id");
    const requestedSlug=params.get("slug");
    if(!requestedId&&!requestedSlug)throw new Error("missing event key");
    const [data,sports,editorial,artistVideos,publishedCmsRows,linkHealth]=await Promise.all([
      (window.ISNET_PUBLIC_CMS?.loadSource?.()||fetch("data/events.json",{cache:"no-store"}).then(r=>{if(!r.ok)throw new Error("data");return r.json()})),
      fetch("data/sports.json?v=20261005-2").then(r=>r.json()).catch(()=>({branches:{},teams:[]})),
      fetch("data/editorial.json",{cache:"no-store"}).then(r=>r.ok?r.json():{events:{}}).catch(()=>({events:{}})),
      fetch("../shared/standup-videos.json",{cache:"no-store"}).then(r=>r.ok?r.json():{artists:[]}).catch(()=>({artists:[]})),
      window.ISNET_PUBLIC_CMS?.publishedEvents?.("yavne")||Promise.resolve([]),
      fetch("../shared/purchase-link-health.json",{cache:"no-cache"}).then(r=>r.ok?r.json():{results:{}}).catch(()=>({results:{}}))
    ]);
    purchaseHealth=linkHealth||{results:{}};
    sportsMeta=sports||{branches:{},teams:[]};
    const editorialById=editorial?.events||{};
    // Reuse a verified artist clip automatically across cities and future performances.
    // Never guess an artist from a vague title or overwrite event-specific videos.
    const artists=Array.isArray(artistVideos?.artists)?artistVideos.artists:[];
    const matchArtistVideo=event=>{
      if(event.category!=="standup")return null;
      const title=String(event.title||"").normalize("NFKC");
      const performers=Array.isArray(event.performers)?event.performers:[];
      return artists.find(artist=>artist.video_verified===true &&
        /^[a-zA-Z0-9_-]{11}$/.test(artist.youtube_id||"") &&
        (artist.aliases||[artist.name]).some(alias=>{
          const n=String(alias||"").normalize("NFKC").trim();
          return n.length>=5 && (title.includes(n) || performers.some(p=>String(p).normalize("NFKC").includes(n)));
        })
      )||null;
    };
    const cmsRows=Array.isArray(publishedCmsRows)?publishedCmsRows:[];
    const cmsById=new Map(cmsRows.map(r=>[r.event_id,r]));
    let all=(data.events||[]).map(event=>{
      const entry=editorialById[event.event_id];
      const artistVideo=!event.youtube_id&&!entry?.youtube_id?matchArtistVideo(event):null;
      const cms=cmsById.get(event.event_id);
      const cmsPayload=cms?.payload&&typeof cms.payload==="object"?cms.payload:null;
      if(!entry&&!artistVideo&&!cmsPayload)return event;
      const allowed={};
      if(artistVideo){
        allowed.youtube_id=artistVideo.youtube_id;
        allowed.youtube_title=artistVideo.youtube_title||"קטע סטנדאפ של "+artistVideo.name;
        allowed.youtube_note=artistVideo.youtube_note||"קטע מייצג של האמן";
      }
      if(!entry||typeof entry!=="object")return {...event,...allowed,...(cmsPayload||{}),rich_content_status:cmsPayload?"enriched":event.rich_content_status};

      for(const field of ["long_description","short_pitch","youtube_title","youtube_note","suitability"]){
        if(typeof entry[field]==="string"&&entry[field].trim())allowed[field]=entry[field].trim();
      }
      if(Array.isArray(entry.performers))allowed.performers=entry.performers.filter(x=>typeof x==="string");
      if(Array.isArray(entry.creators))allowed.creators=entry.creators.filter(x=>typeof x==="string");
      if(Array.isArray(entry.highlights))allowed.highlights=entry.highlights.filter(x=>typeof x==="string");
      // Do not embed search results or unverified YouTube IDs.
      if(/^[a-zA-Z0-9_-]{11}$/.test(entry.youtube_id||"") && entry.video_verified===true)allowed.youtube_id=entry.youtube_id;
      return {...event,...allowed,...(cmsPayload||{}),rich_content_status:(entry||artistVideo||cmsPayload)?"enriched":event.rich_content_status};
    });
    const existingIds=new Set(all.map(e=>e.event_id));
    for(const row of cmsRows){
      if(row.record_type==="manual"&&!existingIds.has(row.event_id)&&row.payload){
        all.push({...row.payload,event_id:row.event_id,seo_slug:row.seo_slug||row.payload.seo_slug,publication_status:"published"});
      }
    }

    const originalAll=all;
    all=window.ISNET_EVENT_IDENTITIES?.reconcile?.(all)||all;
    const original=requestedId
      ? originalAll.find(e=>e.event_id===requestedId)
      : findSlugEvent(originalAll,requestedSlug);
    const canonical=original?.canonical_event_id&&all.find(e=>e.event_id===original.canonical_event_id);
    const base=canonical||(!requestedId&&findSlugEvent(all,requestedSlug))
      ||(original&&all.find(e=>e.event_id===original.event_id||e._source_event_ids?.includes(original.event_id)));
    if(!base||["hidden","draft","archived","trashed","deleted"].includes(base.status)||["draft","unpublished","hidden","archived"].includes(base.publication_status))throw new Error("event");
    const canonicalSlug=eventSlug(base);
    if(!requestedSlug || slugifyHebrew(requestedSlug,200)!==canonicalSlug){
      history.replaceState(null,"","event.html?slug="+encodeURIComponent(canonicalSlug));
    }
    const key=eventGroupKey(base);
    const series=all.filter(e=>eventGroupKey(e)===key)
      .sort((a,b)=>(a.start_date+(a.start_time||"99:99")).localeCompare(b.start_date+(b.start_time||"99:99")));
    const occurrenceKeys=new Set();
    const distinct=series.filter(e=>{const k=e.start_date+"T"+(e.start_time||"")+"|"+(e.venue||"");if(occurrenceKeys.has(k))return false;occurrenceKeys.add(k);return true});
    const upcoming=distinct.filter(e=>isUpcoming(e));
    const occ=upcoming.length?upcoming:distinct;
    const e={...richEvent(occ),_canonical_slug:canonicalSlug,start_date:occ[0].start_date,start_time:occ[0].start_time};
    const imageEvent=bestImageEvent(occ);

    // GA4 standard ecommerce-style event view. item_id lets the Data API
    // aggregate views per event without exposing personal information.
    window.ashdodAnalytics?.send("view_item",{
      currency:"ILS",
      value:Number(e.price_min_ils||0),
      items:[{
        item_id:String(e.event_id||"").slice(0,100),
        item_name:String(e.series_title||e.title||"").slice(0,100),
        item_category:String(e.category||"").slice(0,40)
      }]
    });

    // A dedicated back-link always returns family visitors to the top of their own hub.
    if(e.category==="kids"||/^kids-|^story-time$/.test(String(e.subcategory||""))){
      const hero=document.querySelector(".eventHero .shell");
      if(hero&&!document.getElementById("kidsHubReturn")){
        const back=document.createElement("a");
        back.id="kidsHubReturn";back.href="category.html?category=kids";
        back.textContent="→ חזרה לעמוד הילדים והמשפחה";
        back.style.cssText="display:inline-flex;margin:0 0 16px;padding:10px 14px;color:#f3dfaa;background:#26232d;border:1px solid #6b5c46;border-radius:10px;text-decoration:none;font-weight:800";
        hero.before(back);
      }
    }
    renderHero(e,occ,imageEvent);
    renderStory(e,occ);
    renderVideo(e);
    renderPeople(e);
    renderSchedule(occ);
    renderPractical(e,occ);
    renderRelated(e,all);
    document.addEventListener("click", action => {
      if (!(action.target instanceof Element)) return;
      const link = action.target.closest("a");
      if (!link) return;
      if (link.matches("#heroBuy, .scheduleBuy")) {
        const row = link.closest(".scheduleItem");
        const selected = row ? occ[Array.from(document.querySelectorAll(".scheduleItem")).indexOf(row)] : e;
        const analytics = window.ashdodAnalytics;
        const params = {...analytics?.metadata(selected),purchase_method:link.protocol === "tel:" ? "phone" : "website"};
        if (row) analytics?.send("select_date",{...analytics.metadata(selected),selected_date:selected.start_date,selection_type:"event_occurrence"});
        analytics?.send("ticket_click",params);
      } else if (link.matches(".relatedCard")) {
        const u=new URL(link.href);
        const relatedId=u.searchParams.get("id");
        const relatedSlug=u.searchParams.get("slug");
        const selected=relatedId?all.find(item=>item.event_id===relatedId):findSlugEvent(all,relatedSlug);
        if(selected) window.ashdodAnalytics?.send("select_event",window.ashdodAnalytics.metadata(selected));
      }
    });

    $("loadingState").hidden=true;
    $("page").hidden=false;
  }catch(err){
    $("loadingState").hidden=true;
    $("errorState").hidden=false;
  }
}
init();
