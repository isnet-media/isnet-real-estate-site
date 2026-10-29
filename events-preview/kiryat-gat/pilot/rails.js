/* Keyboard navigation must act on the focused category, not the page wrapper. */
document.addEventListener('keydown',event=>{
  if(event.key!=='ArrowLeft'&&event.key!=='ArrowRight')return;
  if(!(event.target instanceof Element)||!event.target.matches('.isnetCategoryRail'))return;
  const rail=event.target,card=rail.querySelector('.eventCard:not([hidden])');
  event.preventDefault();
  rail.scrollBy({left:(event.key==='ArrowRight'?1:-1)*((card?.getBoundingClientRect().width||260)+16),behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
});
