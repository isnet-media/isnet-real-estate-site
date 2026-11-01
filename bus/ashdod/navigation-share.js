/* Bus-only navigation and explicit rich sharing; no messages are sent automatically. */
(()=>{'use strict';
 const nav=document.getElementById('isnet-public-navigation');
 if(nav){
  nav.classList.add('bus-navigation');
  nav.querySelector('[data-isnet-marketing-open]')?.remove();
  for(const a of nav.querySelectorAll('a')){
   if(a.getAttribute('href')==='/events-preview/ashdod/')a.remove();
   if(a.href==='https://ashdodnet.com/'){a.textContent='חזרה לאשדוד נט ↗';a.removeAttribute('target');a.setAttribute('aria-label','חזרה לאשדוד נט')}
  }
  const shareButton=nav.querySelector('[data-isnet-share-open]');
  if(shareButton){shareButton.innerHTML='<svg class="share-icon" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true" focusable="false"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 10.5 6.8-4m-6.8 7 6.8 4"/></svg><span>שיתוף</span>';shareButton.setAttribute('aria-label','שיתוף')}
  const resize=()=>document.documentElement.style.setProperty('--bus-nav-height',Math.ceil(nav.getBoundingClientRect().height)+'px');
  resize();if(window.ResizeObserver)new ResizeObserver(resize).observe(nav);else window.addEventListener('resize',resize);
 }
 const resultShare=document.getElementById('share');if(resultShare)resultShare.textContent='שיתוף הנסיעה';
 function payload(){
  const url=new URL(location.href),allowed=new Set(['from','to','date','time','mode','target_kind','transfer']);
  for(const key of [...url.searchParams.keys()])if(!allowed.has(key))url.searchParams.delete(key);
  const hasResult=!document.getElementById('answer')?.hidden&&!!document.querySelector('#answer .route-card');
  if(!hasResult)url.search='';
  const from=document.getElementById('from')?.value.trim(),to=document.getElementById('to')?.value.trim();
  let text='מתי יש אוטובוס? — מבית אשדוד נט';
  if(from&&to&&url.searchParams.has('from')&&url.searchParams.has('to')){
   text+='\nמ'+from+' אל '+to;
   const date=document.getElementById('date').value,time=document.getElementById('time').value;
   if(date&&time)text+='\n'+date.split('-').reverse().join('.')+' · החל מ־'+time;
  }else text+='\nמצאו אוטובוס באשדוד ולערים אחרות, והשוו גם נסיעה ברכבת.';
  return {title:'מתי יש אוטובוס? | אשדוד נט',text,url:url.href};
 }
 let dialog,opener,current;
 function openShare(button){
  opener=button;current=payload();
  if(!dialog){
   dialog=document.createElement('dialog');dialog.id='bus-share-dialog';dialog.setAttribute('aria-labelledby','bus-share-title');
   dialog.innerHTML='<h2 id="bus-share-title">איך תרצו לשתף?</h2><p class="share-description"></p><div class="share-options"><a data-channel="whatsapp" target="_blank" rel="noopener noreferrer">שיתוף בוואטסאפ</a><a data-channel="facebook" target="_blank" rel="noopener noreferrer">שיתוף בפייסבוק</a><a data-channel="email">שליחה בדוא״ל</a><button type="button" data-native-share>אפשרויות שיתוף בנייד</button><button type="button" data-copy-share>העתקת קישור</button></div><input readonly dir="ltr" aria-label="קישור לשיתוף"><p role="status" aria-live="polite"></p><button type="button" class="share-close">סגירה</button>';
   document.body.append(dialog);
   dialog.querySelector('.share-close').onclick=()=>dialog.close();
   dialog.addEventListener('close',()=>opener?.focus({preventScroll:true}));
   dialog.addEventListener('click',e=>{if(e.target!==dialog)return;const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close()});
   dialog.querySelector('[data-copy-share]').onclick=async()=>{const input=dialog.querySelector('input'),status=dialog.querySelector('[role=status]');try{await navigator.clipboard.writeText(current.url);status.textContent='הקישור הועתק'}catch{input.focus();input.select();status.textContent='סמנו והעתיקו את הקישור המוצג'}};
   dialog.querySelector('[data-native-share]').onclick=async()=>{try{await navigator.share(current)}catch(e){if(e.name!=='AbortError')dialog.querySelector('[role=status]').textContent='אפשר לבחור וואטסאפ, דוא״ל או העתקת קישור.'}};
  }
  const message=current.text+'\n'+current.url;
  dialog.querySelector('.share-description').textContent=current.text;
  dialog.querySelector('[data-channel=whatsapp]').href='https://wa.me/?text='+encodeURIComponent(message);
  dialog.querySelector('[data-channel=facebook]').href='https://www.facebook.com/sharer/sharer.php?u='+encodeURIComponent(current.url);
  dialog.querySelector('[data-channel=email]').href='mailto:?subject='+encodeURIComponent(current.title)+'&body='+encodeURIComponent(message);
  dialog.querySelector('[data-native-share]').hidden=typeof navigator.share!=='function';
  dialog.querySelector('input').value=current.url;dialog.querySelector('[role=status]').textContent='';dialog.showModal();
 }
 document.addEventListener('click',event=>{const button=event.target.closest('[data-isnet-share-open],#share');if(!button)return;event.preventDefault();event.stopImmediatePropagation();openShare(button)},true);
})();
