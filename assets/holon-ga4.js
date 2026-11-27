(() => {
  if (!['isnet.co.il', 'www.isnet.co.il'].includes(location.hostname)) return;

  const sections = new Map([
    ['/events-preview/holon/', 'events'],
    ['/events-preview/holon/index.html', 'events'],
    ['/events-preview/holon/health.html', 'health'],
    ['/super.holon/', 'supermarket'],
    ['/super.holon/index.html', 'supermarket'],
    ['/astrology/', 'astrology'],
    ['/astrology/index.html', 'astrology'],
  ]);
  const section = sections.get(location.pathname.toLowerCase());
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
