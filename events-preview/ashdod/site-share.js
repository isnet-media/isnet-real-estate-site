/* Share the current public page beside its branding on every Ashdod page. */
(()=>{'use strict';if(!location.pathname.includes('/ashdod/'))return;
const header=document.querySelector('.siteTopbar,.sat-header,.cinemaTop,body>header');if(!header||header.querySelector('.isnetSiteShare'))return;
header.classList.add('isnetShareHeader');
const group=header.querySelector('.isnetBrandGroup,.sat-brands,.cinemaBrand,.brand')||header.querySelector('strong');
const share=document.createElement('button');share.type='button';share.className='isnetSiteShare';share.setAttribute('aria-label','שיתוף הדף');share.title='שתפו עם חברים ומשפחה';
share.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true" width="19" height="19" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 10.5 6.8-4m-6.8 7 6.8 4"/></svg><span class="isnetSiteShare__desktop">שיתוף</span><span class="isnetSiteShare__mobile">שיתוף</span>';
if(group)group.after(share);else (header.firstElementChild||header).append(share);
const notice=document.createElement('div');notice.className='isnetShareNotice';notice.setAttribute('role','status');notice.setAttribute('aria-live','polite');document.body.append(notice);
let noticeTimer;function tell(message){clearTimeout(noticeTimer);notice.textContent=message;notice.classList.add('is-visible');noticeTimer=setTimeout(()=>notice.classList.remove('is-visible'),4500)}
const style=document.createElement('style');style.textContent=`
.isnetShareHeader .isnetSiteShare{display:inline-flex;align-items:center;justify-content:center;gap:8px;flex:0 0 auto;min-width:44px;min-height:44px;padding:9px 13px;border:1px solid #b99d61;border-radius:12px;background:#d7b57315;color:#f2d59f;font:700 15px/1.3 Assistant,Arial,sans-serif;cursor:pointer}
.isnetSiteShare:hover{background:#d7b57330!important}.isnetSiteShare:focus-visible{outline:2px solid #f2cd62;outline-offset:4px}.isnetSiteShare__mobile{display:none}
.isnetShareNotice{position:fixed;z-index:10000;bottom:24px;inset-inline:16px;margin:auto;width:fit-content;max-width:calc(100% - 32px);background:#f0d5a0;color:#172030;border-radius:12px;padding:13px 20px;font:700 16px/1.5 Assistant,Arial,sans-serif;text-align:center;box-shadow:0 5px 25px #0005;visibility:hidden}
.isnetShareNotice.is-visible{visibility:visible}.isnetShareDialog{direction:rtl;max-width:calc(100% - 32px);width:440px;border:1px solid #b99d61;border-radius:16px;background:#171a22;color:#fff;padding:22px;font:16px/1.6 Assistant,Arial,sans-serif}.isnetShareDialog::backdrop{background:#0009}.isnetShareDialog input{width:100%;box-sizing:border-box;direction:ltr;font-size:16px;padding:10px;color:#fff;background:#0b0d12;border:1px solid #777;border-radius:8px}.isnetShareDialog button{margin-top:14px;min-height:44px;padding:8px 18px;border:0;border-radius:8px;background:#f0d5a0;color:#172030;font:700 16px Assistant,Arial,sans-serif;cursor:pointer}
@media(max-width:650px){.isnetShareHeader:not(.isnetBrandHeader)>div{flex-wrap:wrap;gap:10px}.isnetShareHeader:not(.isnetBrandHeader) .isnetSiteShare{margin-inline-start:auto}.isnetBrandHeader .siteTopbar__inner{gap:8px!important}.isnetShareHeader .isnetSiteShare{flex-direction:column;gap:2px;width:44px;height:44px;padding:4px}.isnetSiteShare__desktop{display:none}.isnetSiteShare__mobile{display:inline;font-size:10px}}
@media(max-width:360px){.isnetBrandHeader .isnetBrandGroup{gap:8px}.isnetBrandHeader .siteTopbar__ashdodnet{padding-inline-start:8px!important}}
`;document.head.append(style);
share.addEventListener('click',async()=>{
 const url=new URL(location.pathname,location.origin);
 for(const key of ['id','slug','category','subcategory','date','area','audience','topic','food','venue','team','cuisine','mood','service','place']){const value=new URL(location.href).searchParams.get(key);if(value)url.searchParams.set(key,value)}
 if(/^#[\w-]+$/.test(location.hash))url.hash=location.hash;
 const title=document.querySelector('main h1,.cinemaBrand h1,.hero h1')?.textContent?.trim()||document.title||'מה עושים באשדוד';
 const payload={title,text:title+' · מה עושים באשדוד',url:url.href};
 try{if(typeof navigator.share==='function'){await navigator.share(payload);return}}catch(error){if(error.name==='AbortError')return}
 try{await navigator.clipboard.writeText(payload.url);tell('הקישור לדף הועתק — אפשר לשלוח לחברים ולמשפחה.')}
 catch{
  let dialog=document.querySelector('.isnetShareDialog');
  if(!dialog){dialog=document.createElement('dialog');dialog.className='isnetShareDialog';dialog.setAttribute('aria-label','העתקת קישור לדף');const label=document.createElement('label');label.textContent='העתיקו את הקישור ושלחו לחברים ולמשפחה';const field=document.createElement('input');field.readOnly=true;field.setAttribute('aria-label','קישור לדף');label.append(field);const close=document.createElement('button');close.type='button';close.textContent='סגירה';close.onclick=()=>dialog.close();dialog.append(label,close);document.body.append(dialog)}
  const field=dialog.querySelector('input');field.value=payload.url;dialog.showModal();field.focus();field.select();
 }
});


})();
