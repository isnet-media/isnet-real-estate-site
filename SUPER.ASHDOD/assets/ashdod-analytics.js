/* Ashdod Net GA4: public page paths only, without search text or shopping lists. */
(function () {
  if (!/^\/SUPER\.ASHDOD(?:\/|$)/.test(location.pathname) || window.superAshdodAnalytics) return;
  window.superAshdodAnalytics = true;
  const id = 'G-YEFDXMCHB1';
  const clean = value => { try { const u = new URL(value); return u.origin + u.pathname; } catch { return ''; } };
  const views = new Set(['home','products','basket','compare','monthly']);
  const page = () => clean(location.href) + (views.has(location.hash.slice(1)) && location.hash !== '#home' ? location.hash : '');
  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  if (!document.querySelector('script[src*="googletagmanager.com/gtag/js"]')) {
    const tag = document.createElement('script'); tag.async = true;
    tag.src = 'https://www.googletagmanager.com/gtag/js?id=' + id;
    document.head.appendChild(tag); window.gtag('js', new Date());
  }
  window.gtag('config', id, {send_page_view:false, content_group:'super_ashdod', page_location:page(), page_referrer:clean(document.referrer)});
  let last = '';
  function track() {
    const current = page(); if (current === last) return; last = current;
    window.gtag('event','page_view',{send_to:id, page_location:current, page_title:document.title, page_referrer:clean(document.referrer), content_group:'super_ashdod'});
  }
  track(); window.addEventListener('hashchange',track);
})();
