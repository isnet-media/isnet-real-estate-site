// ISNET shared layout: edit events-preview/ashdod, not this generated file.
/* Reuse existing date/calendar behavior; no duplicate event filtering logic. */
document.addEventListener('DOMContentLoaded',()=>{
 const go=document.getElementById('isnetOpenCalendar');
 const existing=document.getElementById('resetDate');
 const box=document.getElementById('calendarBox');
 const openCalendar=mode=>{
   if(box?.hidden) existing?.click();
   if(mode==='week')document.getElementById('weekViewButton')?.click();
   if(mode==='month')document.getElementById('monthViewButton')?.click();
   go?.setAttribute('aria-expanded',String(!box?.hidden));
 };
 go?.addEventListener('click',()=>{if(box?.hidden)openCalendar('month');else document.getElementById('calendarBox')?.scrollIntoView({behavior:'smooth',block:'nearest'});});
 document.querySelectorAll('[data-isnet-day]').forEach(btn=>btn.addEventListener('click',()=>{
   const mode=btn.dataset.isnetDay;
   if(mode==='week'||mode==='month'){openCalendar(mode);return}
   document.querySelector('#quickFilters [data-quick="'+mode+'"]')?.click();
   document.querySelectorAll('[data-isnet-day]').forEach(b=>b.classList.toggle('is-active',b===btn));
 }));
});
