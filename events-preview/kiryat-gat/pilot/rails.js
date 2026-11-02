/* Keyboard navigation must act on the focused category, not the page wrapper. */
document.addEventListener('keydown',event=>{
  if(event.key!=='ArrowLeft'&&event.key!=='ArrowRight')return;
  if(!(event.target instanceof Element)||!event.target.matches('.isnetCategoryRail'))return;
  const rail=event.target,card=rail.querySelector('.eventCard:not([hidden]),.homeCinemaCard');
  event.preventDefault();
  rail.scrollBy({left:(event.key==='ArrowRight'?1:-1)*((card?.getBoundingClientRect().width||260)+16),behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
});

/* Position the controls in the photograph, and expose the actual RTL scroll limits. */
(()=>{
 const grid=document.getElementById('eventsGrid');if(!grid)return;
 let pending=false;
 function update(){
  pending=false;
  grid.querySelectorAll('.isnetCategorySection').forEach(section=>{
   const rail=section.querySelector('.isnetCategoryRail'),wrap=section.querySelector('.isnetRailWrap');if(!rail||!wrap)return;
   const media=rail.querySelector('.eventCard:not([hidden]) .mediaWrap,.homeCinemaCard__media');
   if(media){const box=media.getBoundingClientRect(),base=wrap.getBoundingClientRect();wrap.style.setProperty('--rail-media-center',(box.top-base.top+box.height/2)+'px');}
   const maximum=Math.max(0,rail.scrollWidth-rail.clientWidth),position=Math.abs(rail.scrollLeft),overflow=maximum>2;
   section.querySelectorAll('[data-category-move]').forEach(button=>{
    const hide=!overflow&&button.classList.contains('isnetRailOverlay');if(button.hidden!==hide)button.hidden=hide;
    button.disabled=!overflow||(button.dataset.categoryMove==='start'?position<=2:position>=maximum-2);
   });
  });
 }
 function schedule(){if(!pending){pending=true;requestAnimationFrame(update);}}
 new MutationObserver(schedule).observe(grid,{childList:true,subtree:true,attributes:true,attributeFilter:['hidden']});
 if(typeof ResizeObserver!=='undefined')new ResizeObserver(schedule).observe(grid);
 document.addEventListener('scroll',event=>{if(event.target instanceof Element&&event.target.matches('.isnetCategoryRail'))schedule();},{capture:true,passive:true});
 window.addEventListener('resize',schedule,{passive:true});schedule();
})();
