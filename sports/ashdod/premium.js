(()=>{
 const holder=document.querySelector('#score-strip');if(!holder)return;
 const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 let refreshing=false;
 function refresh(){if(refreshing||document.hidden)return;refreshing=true;
 fetch('results.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error();return r.json()}).then(d=>{
  const sport=document.body.dataset.sport,section=document.body.dataset.teamSection;
  const matches=d.items.filter(m=>(!sport||m.sport===sport)&&(!section||section==='בוגרים'&&m.sport==='כדורגל')&&Number.isFinite(m.team_score)&&Number.isFinite(m.opponent_score));
  const selected=d.items.filter(m=>['football-1198','football-6922','football-6929','football-7276','basket-men'].includes(m.id)&&Number.isFinite(m.team_score)&&Number.isFinite(m.opponent_score));
  holder.style.gridTemplateColumns=`repeat(${Math.max(1,selected.length)},minmax(0,1fr))`;
  holder.innerHTML=selected.map(m=>{
   const age=Date.now()-Date.parse(m.fetched_at);
   const active=m.status==='live'&&Number.isFinite(age)&&age>=-30000&&age<120000;
   const stale=m.status==='live'&&!active;
   const status=active?(m.sport==='כדורסל'?`רבע ${m.period??'—'} · ${m.clock??'—'}`:`דקה ${m.minute??'—'}`):stale?'העדכון מתעכב':'הסתיים';
   const opponent=d.items.find(t=>t.team===m.opponent);
   const mark=opponent?.logo?`<img src="${esc(opponent.logo)}" alt="">`:`<span class="opponent-mark" aria-hidden="true">${esc(m.opponent.trim().split(/\s+/).filter(w=>!['הפועל','מכבי'].includes(w)).slice(0,2).map(w=>w[0]).join(''))}</span>`;
   return `<a class="strip-game" href="results.html#${esc(m.id)}" aria-label="${esc(m.team)} ${m.team_score}, ${esc(m.opponent)} ${m.opponent_score}, ${esc(status)}"><div class="match-topline"><span>${esc(m.sport)} · ${esc(m.date)}</span><span class="match-status">${esc(status)}</span></div><div class="match-body"><span class="match-side"><img src="${esc(m.logo)}" alt=""><strong>${esc(m.team)}</strong></span><span class="match-score"><b>${m.team_score}</b><i>:</i><b>${m.opponent_score}</b></span><span class="match-side">${mark}<strong>${esc(m.opponent)}</strong></span></div></a>`;
  }).join('')||'<span class="rail-loading">תוצאות למסגרת זו טרם זמינות. <a href="results.html" style="color:white">לכל תוצאות המחזור ←</a></span>';
  if(document.body.classList.contains('sport-home')){
   document.querySelector('.next-strip')?.remove();
   const today=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Jerusalem',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
   const dateKey=x=>{const a=(x||'').split('/');return a.length===3?`${a[2]}-${a[1].padStart(2,'0')}-${a[0].padStart(2,'0')}`:''};
   const upcoming=d.items.filter(m=>m.next?.date&&dateKey(m.next.date)>=today).sort((a,b)=>(dateKey(a.next.date)+(a.next.time||'')).localeCompare(dateKey(b.next.date)+(b.next.time||''))).slice(0,6);
   if(upcoming.length){const block=document.createElement('section');block.className='next-strip';block.setAttribute('aria-label','משחקים קרובים');block.innerHTML=`<h2>המשחקים הקרובים</h2><div class="upcoming-grid">${upcoming.map(m=>`<a class="upcoming-card" href="results.html#${esc(m.id)}"><img src="${esc(m.logo)}" alt=""><span><b>${esc(m.team)}</b><small>נגד ${esc(m.next.opponent)}</small><small>${esc(m.next.date)} · ${esc(m.next.time||'שעה טרם נקבעה')}</small></span></a>`).join('')}</div>`;holder.closest('.match-strip').after(block)}
  }
 }).catch(()=>{holder.innerHTML='<span class="rail-loading"><a href="results.html" style="color:white">לתוצאות המחזור ←</a></span>'}).finally(()=>{refreshing=false});
 }
 refresh();setInterval(refresh,30000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()});
})();
