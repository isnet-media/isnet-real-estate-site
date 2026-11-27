(() => {
  if (!['isnet.co.il', 'www.isnet.co.il'].includes(location.hostname)) return;

  const path = location.pathname.toLowerCase();
  const section = path === '/events-preview/holon/health.html' ? 'health'
    : path.startsWith('/events-preview/holon/') ? 'events'
    : path.startsWith('/super.holon/') ? 'supermarket'
    : path.startsWith('/astrology/') ? 'astrology'
    : '';
  if (!section) return;

  const referrerOrigin = document.referrer ? new URL(document.referrer).origin : '';
  if (section === 'astrology' && !/^https:\/\/(?:www\.)?holonnet\.co\.il$/.test(referrerOrigin)) return;

  const measurementId = 'G-K54E6KGZCV';
  const hadGoogleTag = typeof window.gtag === 'function';
  window.dataLayer = window.dataLayer || [];
  if (!hadGoogleTag) {
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag('js', new Date());
    const tag = document.createElement('script');
    tag.async = true;
    tag.src = 'https://www.googletagmanager.com/gtag/js?id=' + measurementId;
    document.head.appendChild(tag);
  }

  window.gtag('config', measurementId, { send_page_view: false });
  window.gtag('event', 'page_view', {
    send_to: measurementId,
    page_location: location.origin + location.pathname,
    page_referrer: referrerOrigin,
    section_name: section,
  });
})();
