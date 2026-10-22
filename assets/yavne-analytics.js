/* Yavne Net property 378336340 / stream 5260877346, verified 2026-10-22.
 * Reused across the three Yavne editions. No shopping lists or raw searches. */
(function () {
  const scopes = [[/^\/events-preview\/yavne(?:\/|$)/, 'events_yavne'], [/^\/SUPER\.YAVNE(?:\/|$)/, 'super_yavne'], [/^\/meusharim\/yavne(?:\/|$)/, 'classes_yavne']];
  const group = scopes.find(([pattern]) => pattern.test(location.pathname))?.[1];
  if (!group || window.yavneAnalytics) return;
  const id = 'G-JLRT7GKSXB';
  const clean = value => { try { const u = new URL(value); return u.origin + u.pathname; } catch { return ''; } };
  const categories = new Set(['stage','music','theatre','standup','lecture','sport','exhibition','community','kids','seniors','cinema','food','tour','workshop']);
  const category = new URL(location.href).searchParams.get('category');
  const page = clean(location.href) + (group === 'events_yavne' && categories.has(category) ? '?category=' + category : '');
  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  if (!document.querySelector('script[src*="googletagmanager.com/gtag/js"]')) {
    const tag = document.createElement('script'); tag.async = true;
    tag.src = 'https://www.googletagmanager.com/gtag/js?id=' + id;
    document.head.appendChild(tag); window.gtag('js', new Date());
  }
  window.gtag('config', id, {send_page_view:false, content_group:group, page_location:page, page_referrer:clean(document.referrer)});
  const common = () => ({send_to:id, content_group:group, page_location:page, page_referrer:clean(document.referrer)});
  window.gtag('event', 'page_view', {...common(), page_title:document.title});
  const allowed = new Set(['search','select_category','select_event','select_date','ticket_click','view_item']);
  const keys = new Set(['category','category_name','selection_type','selected_date','date_start','date_end','event_id','event_title','event_date','purchase_method','result_count','currency','value']);
  function send(name, params = {}) {
    if (!allowed.has(name)) return;
    const safe = {};
    for (const [key,value] of Object.entries(params)) {
      if (keys.has(key) && (typeof value === 'string' || (typeof value === 'number' && Number.isFinite(value)))) safe[key] = typeof value === 'string' ? value.slice(0,120) : value;
    }
    if (name === 'search') safe.search_term = '[withheld]';
    if (name === 'view_item' && Array.isArray(params.items)) safe.items = params.items.slice(0,1).map(item => ({item_id:String(item.item_id || '').slice(0,100),item_name:String(item.item_name || '').slice(0,100),item_category:String(item.item_category || '').slice(0,40)}));
    window.gtag('event', name, {...safe,...common()});
  }
  window.yavneAnalytics = {send, safeSearch:() => '[withheld]', metadata:e => e ? {event_id:String(e.event_id || '').slice(0,100),event_title:String(e.series_title || e.title || '').slice(0,100),category:String(e.category || '').slice(0,40),event_date:/^\d{4}-\d{2}-\d{2}$/.test(e.start_date || '') ? e.start_date : ''} : {}};
})();
