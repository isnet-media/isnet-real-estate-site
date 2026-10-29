/* Shared Ashdod brand lockup. Other city editions keep their own header. */
(()=>{"use strict";if(!location.pathname.includes('/kiryat-gat/'))return;
const header=document.querySelector('.siteTopbar');if(!header)return;
const events=header.querySelector('.siteTopbar__events'),publisher=header.querySelector('.siteTopbar__ashdodnet');if(!events||!publisher)return;
header.classList.add('isnetBrandHeader');
let group=header.querySelector('.isnetBrandGroup');if(!group){group=document.createElement('div');group.className='isnetBrandGroup';group.setAttribute('aria-label','מה עושים בקריית גת מבית קריית גת נט');events.before(group);group.append(events,publisher);}
const eventsImg=events.querySelector('img'),publisherImg=publisher.querySelector('img');
if(eventsImg){eventsImg.src='assets/branding/what-to-do-kgat-dark.svg?v=20261029-kgat2';eventsImg.width=340;eventsImg.height=158;}
if(publisherImg){publisherImg.src='assets/branding/kgatnet-dark.svg?v=20261029-kgat2';publisherImg.width=195;publisherImg.height=82;}
if(!publisher.querySelector('.isnetBrandByline')){const byline=document.createElement('span');byline.className='isnetBrandByline';byline.textContent='מבית';publisher.prepend(byline);}

})();
