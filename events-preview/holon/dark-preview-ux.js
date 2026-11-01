// ISNET shared layout: edit events-preview/ashdod, not this generated file.
/* ISNET dark-preview-only controls. No changes to ingestion or publishing. */
(function(){
  function ready(){
    const rail=document.getElementById('eventsGrid');
    if(!rail)return;
    const arrows=[...document.querySelectorAll('[data-rail-dir]')];
    function move(direction){
      const first=rail.querySelector('.eventCard');
      const distance=first?first.getBoundingClientRect().width+16:300;
      rail.scrollBy({left:(direction==='start'?distance:-distance),behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
    }
    for(const arrow of arrows)arrow.addEventListener('click',()=>move(arrow.dataset.railDir));
    rail.addEventListener('keydown',e=>{
      if(e.key!=='ArrowLeft'&&e.key!=='ArrowRight')return;
      if(innerWidth>650)return;
      e.preventDefault();
      move(e.key==='ArrowRight'?'start':'end');
    });
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ready);
  else ready();
})();
