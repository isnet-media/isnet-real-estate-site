// ISNET shared layout: edit events-preview/ashdod, not this generated file.
// Ashdod GA4: public event metadata only; never transmit raw search text or URLs.
(function () {
  if (!/\/events-preview\/ashdod(?:\/|$)/.test(location.pathname) || window.ashdodAnalytics) return;
  const id = "G-YEFDXMCHB1";
  let debug = new URLSearchParams(location.search).get("ga_debug") === "1";
  try { if (debug) sessionStorage.setItem("ashdod-ga-debug","1"); debug = debug || sessionStorage.getItem("ashdod-ga-debug") === "1"; } catch {}

  const cleanUrl = value => { try { const u = new URL(value); return u.origin + u.pathname; } catch { return ""; } };
  const categoryNames={stage:"הופעות במה",kids:"ילדים ומשפחה",seniors:"גמלאים",lecture:"הרצאות",sport:"אירועי ספורט",exhibition:"תערוכות",music:"מוזיקה",theatre:"הצגות",standup:"סטנדאפ",cinema:"קולנוע",community:"קהילה",food:"קולינריה ואוכל",tour:"טיולים",workshop:"סדנאות"};
  const pageUrl=new URL(location.href),category=pageUrl.pathname.endsWith("/category.html")?pageUrl.searchParams.get("category"):pageUrl.hash==="#cinema"?"cinema":null;
  const measuredLocation=cleanUrl(location.href)+(categoryNames[category]?(pageUrl.pathname.endsWith("/category.html")?"?category="+encodeURIComponent(category):"#cinema"):"");
  const pageTitle=categoryNames[category]?categoryNames[category]+" | מה עושים בראשון לציון":document.title;
  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  if (!window.__ashdodGa4Initialized) {
    window.__ashdodGa4Initialized = true;
    if (!document.querySelector('script[src*="googletagmanager.com/gtag/js"]')) {
      const tag = document.createElement("script");
      tag.async = true; tag.src = "https://www.googletagmanager.com/gtag/js?id=" + id;
      document.head.appendChild(tag);
      window.gtag("js", new Date());
    }
    window.gtag("config", id, {page_location:measuredLocation, page_title:pageTitle, page_referrer:cleanUrl(document.referrer), content_group:"events_ashdod", ...(debug ? {debug_mode:true} : {})});
  }
  const vocabulary = new Set("לאן לצאת מה עושים עם הילדים ילדים ילד ילדה משפחה משפחות היום מחר השבוע סוף שבוע סופש בסופש חינם זול הופעות הופעה מוזיקה מוסיקה סטנדאפ תיאטרון הצגות הצגה קולנוע סרט סרטים הרצאות הרצאה סדנאות סדנה יצירה אמנות אומנות תערוכות תערוכה פסטיבל פסטיבלים קהילה ספורט כדורגל כדורסל כדוריד כדורעף גלישה טיולים טבע פארקים פארק חופים חוף ים ראשון לציון בראשון לציון מבוגרים למבוגרים גמלאים גמלאי גיל השלישי אזרחים ותיקים זוג זוגות ערב בוקר צהריים בילוי בילויים לנוער נוער לילדים קטנים קטנות".split(" "));
  const safeSearch = value => {
    const tokens = String(value).normalize("NFKC").toLowerCase().replace(/[^\p{L}\s]/gu," ").split(/\s+/).filter(Boolean);
    // Only recognized generic activity words leave the browser; names, numbers,
    // email addresses and other unknown terms are omitted altogether.
    return [...new Set(tokens.filter(t => vocabulary.has(t)))].join(" ").slice(0,100) || "[withheld]";
  };
  const metadata = e => e ? {event_id:String(e.event_id || "").slice(0,100),event_title:String(e.series_title || e.title || "").slice(0,100),category:String(e.category || "").slice(0,40),event_date:/^\d{4}-\d{2}-\d{2}$/.test(e.start_date || "") ? e.start_date : ""} : {};
  const allowed = new Set(["search","select_category","select_event","select_date","ticket_click"]);
  const send = (name, params = {}) => {
    if (!allowed.has(name)) return;
    window.gtag("event",name,{...params,send_to:id,page_location:cleanUrl(location.href),page_referrer:cleanUrl(document.referrer),transport_type:"beacon",...(debug ? {debug_mode:true} : {})});
  };
  window.ashdodAnalytics = {send,metadata,safeSearch};
})();

// Category identifiers only; free text and URL parameters are never copied.
document.addEventListener("click",function(event){const tile=event.target.closest?.("[data-topic],[data-food]");if(tile)window.ashdodAnalytics?.send("select_category",{category:String(tile.dataset.food||tile.dataset.topic||"").slice(0,40),content_group:"events_ashdod",section:"saturday"});});
