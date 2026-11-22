/* Kiryat Gat Net page measurement for the transport guide. */
(function () {
  const id = 'G-JKZ876L4PP';
  const page = location.origin + location.pathname;
  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  window.gtag('js', new Date());
  window.gtag('config', id, {
    send_page_view: false,
    content_group: 'transport_kgat',
    page_location: page,
    page_referrer: document.referrer ? new URL(document.referrer).origin : '',
  });
  window.gtag('event', 'page_view', { send_to: id, page_location: page });
  const tag = document.createElement('script');
  tag.async = true;
  tag.src = 'https://www.googletagmanager.com/gtag/js?id=' + id;
  document.head.appendChild(tag);
})();
