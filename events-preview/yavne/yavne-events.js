/* Yavne-only category memberships; one event ID can belong to several lists. */
(function(){
 const memberships=e=>Array.isArray(e.category_memberships)?e.category_memberships:[{category:e.category,subcategory:e.subcategory}];
 function matches(e,ids){return ids.has(e.category)||memberships(e).some(m=>ids.has(m.category))||(ids.has('seniors')&&(e.audiences||[]).includes('seniors'))||(ids.has('kids')&&(e.audiences||[]).some(a=>['kids','families'].includes(a)));}
 function matchesSub(e,category,sub){return memberships(e).some(m=>(!category||m.category===category)&&m.subcategory===sub);}
 function subnav(events,key,params){
  if(key==='stage')return;
  const group=window.ISNET_CITY_BOOTSTRAP?.taxonomy?.primary_categories?.find(c=>c.id===key);
  const subs=(group?.subcategories||[]).filter(s=>events.some(e=>matchesSub(e,key,s.id)));
  const el=document.getElementById('subcategories');if(!el||!subs.length)return;
  const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const selected=params.get('subcategory');el.innerHTML=[{id:'',label:'הכול'},...subs].map(s=>'<a class="'+((selected||'')===s.id?'active':'')+'" href="category.html?category='+encodeURIComponent(key)+(s.id?'&amp;subcategory='+encodeURIComponent(s.id):'')+'">'+esc(s.label)+'</a>').join('');
 }
 window.YAVNE_EVENTS={matches,matchesSub,subnav};
 const originalIllustration=window.isnetEventIllustration;
 window.isnetEventIllustration=e=>{
  if(!e)return null;
  const sub=e.subcategory||'';
  const mapped={history:['v4/history-museum','היסטוריה'], 'travel-geography':['v4/history-museum','תרבויות העולם'], 'parenting-family':['v4/wellbeing-circle','מפגש והרצאה'], 'psychology-growth':['v4/wellbeing-circle','התפתחות אישית'], 'reading-clubs':['v4/book-club','מועדון קריאה'], 'dance-performance':['v4/ballet-dance','מחול'], 'folk-dancing':['v4/folk-dance','ריקודי עם'], 'story-time':['v1/story-time','שעת סיפור']};
  const item=mapped[sub];
  if(item)return {src:'../ashdod/assets/illustrations/'+item[0]+'.webp',label:item[1]+' — המחשה'};
  return originalIllustration?.(e)||null;
 };
 // The published snapshot avoids a slow or failed CMS blocking category pages.
 const api=window.ISNET_PUBLIC_CMS,data=window.ISNET_CITY_BOOTSTRAP;
 if(api&&data&&location.pathname.endsWith('/category.html')){
  for(const method of ['loadCards','loadHub']){const original=api[method];api[method]=city=>!city||city==='yavne'?Promise.resolve(data):original(city);}
  const published=api.publishedEvents;
  api.publishedEvents=(city,options)=>Promise.race([published(city,options),new Promise(resolve=>setTimeout(()=>resolve([]),1200))]);
 }
})();
