(()=>{'use strict';
const $=id=>document.getElementById(id),E=window.BusEngine;let data,railData,railLoad,streetChoices=[],allGroups=[],localGroups=[],destinationLocalGroups=[],placeChoices=[],cityChoices=[],mode='local',selected={from:null,to:null},shown={},routes=[],geoBusy=false;
const create=(tag,cls,text)=>{const x=document.createElement(tag);if(cls)x.className=cls;if(text!==undefined)x.textContent=text;return x};
const stationName=s=>s.name.replaceAll("''",'״'),mins=s=>Math.max(0,Math.ceil(s/60));
function clock(s){const days=Math.floor(s/86400),x=((s%86400)+86400)%86400;return String(Math.floor(x/3600)).padStart(2,'0')+':'+String(Math.floor(x%3600/60)).padStart(2,'0')+(days>0?' (+יום)':days<0?' (יום קודם)':'')}
function timeNode(sec){const b=create('bdi','',clock(sec));b.dir='ltr';return b}
function israelNow(){const parts=Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Jerusalem',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(new Date()).map(p=>[p.type,p.value]));return{date:parts.year+'-'+parts.month+'-'+parts.day,time:parts.hour+':'+parts.minute}}
function setNow(){const n=israelNow();$('date').value=n.date;$('time').value=n.time}
function status(text,error=false){$('loadStatus').textContent=text;$('loadStatus').classList.toggle('error',error)}
function label(x){return x.kind==='city'?x.city:x.kind==='external'?x.name+(x.city?' · '+x.city:''):stationName(x)+' · '+x.city}
function clearResults(){$('answer').hidden=true;document.getElementById('railAlternatives')?.remove();routes=[]}
function select(field,item){clearResults();selected[field]=item;$(field).value=label(item);close(field);if(field==='from')$('nearby').hidden=true}
function close(field){$(field+'Options').hidden=true;$(field).setAttribute('aria-expanded','false');$(field).removeAttribute('aria-activedescendant')}

function externalChoice(field){const text=$(field).value.trim();if(text)select(field,{kind:'external',id:'external:'+text,name:text,city:field==='from'?'אשדוד':'',ids:[],search:E.norm(text)})}
function fallback(){const out=$('externalFallback');out.replaceChildren();const a=create('a','text-button','המשך לחיפוש תחבורה ציבורית לפי הכתובות ↗');a.href='https://www.google.com/maps/dir/?api=1&origin='+encodeURIComponent(selected.from?(selected.from.query||label(selected.from)):$('from').value)+'&destination='+encodeURIComponent(selected.to?(selected.to.query||label(selected.to)):$('to').value)+'&travelmode=transit';a.target='_blank';a.rel='noopener';out.append(create('p','','במתכנן ההמשך בדקו מחדש את יום ושעת הנסיעה.'),a);if(selected.from?.kind==='stop'){const near=localGroups.map(s=>({...s,meters:E.distance(selected.from,s)})).filter(s=>!s.ids.some(id=>selected.from.ids.includes(id))&&s.meters<=400).sort((a,b)=>a.meters-b.meters).slice(0,4);if(near.length){out.append(create('p','','או בחרו תחנת עלייה אחרת בסביבה (מרחק בקו אווירי, ללא חישוב הליכה):'));for(const s of near){const btn=create('button','text-button',stationName(s)+' · כ־'+Math.round(s.meters)+' מ׳');btn.type='button';btn.onclick=()=>{select('from',s);search()};out.append(btn)}}}}
function suggestions(field,street=null){
 if(!data)return;
 const typed=$(field).value.trim(),addressStreet=street||window.BusAddressChoices.streetFor(typed,streetChoices),raw=street?'':typed;
 const physical=field==='from'?localGroups:destinationLocalGroups;
 const pool=field==='from'?[...localGroups,...streetChoices]:raw?[...placeChoices,...cityChoices,...allGroups,...streetChoices]:mode==='local'?[...placeChoices,...destinationLocalGroups]:cityChoices;
 const unique=[...new Map(pool.map(x=>[x.kind+':'+x.id,x])).values()];
 let list=addressStreet&&addressStreet.stopIds.length?window.BusAddressChoices.candidates(typed,addressStreet,physical,3):raw?E.searchChoices(unique,raw,5):unique.slice(0,5);
 if(field==='from'&&!raw&&!street)list=[];
 shown[field]=list;const out=$(field+'Options');out.replaceChildren();
 if(addressStreet&&list.length){const title=create('p','choice-heading','בחרו תחנה ברחוב '+addressStreet.name);title.id=field+'-choice-heading';out.append(title);out.append(create('p','choice-help','הכתובות הן של התחנות; מיקום מספר הבית שהקלדתם טרם אומת.'))}
 if(!list.length)out.append(create('div','option-empty','אפשר לבחור מיקום נוכחי, או להמשיך לחיפוש לפי הכתובת.'));
 list.forEach((x,i)=>{
  const b=create('button','',x.kind==='city'?x.city:stationName(x));b.type='button';b.id=field+'-option-'+i;b.setAttribute('role','option');
  const note=x.kind==='street'?'רחוב מוכר · אפשר להמשיך לפי הכתובת':x.addressLabel?x.addressLabel+' · תחנה '+x.code:x.kind==='city'?'לתחנת ירידה בעיר':x.kind==='place'?'התחנה המתאימה תופיע בתוצאה':x.city+' · תחנה '+x.code;
  b.append(create('small','',note));b.addEventListener('mousedown',e=>e.preventDefault());
  b.onclick=()=>{if(x.kind==='street'){if(x.stopIds.length){selected[field]=null;suggestions(field,x)}else select(field,{...x,query:typed});return}if(field==='to'&&x.kind==='city')changeMode('intercity');select(field,x);if(field==='from'){$('to').focus();status('תחנת העלייה נבחרה. עכשיו בחרו יעד.')}else status('היעד נבחר. אפשר לחפש נסיעה.')};
  const row=create('div','station-choice');row.append(b);
  if(x.kind==='stop'){const map=navigation(x);map.className='choice-map';map.textContent='מפה ↗';map.setAttribute('aria-label','מפה: '+stationName(x)+' · תחנה '+x.code);row.append(map)}
  out.append(row);
 });
 if(raw){const go=create('button','address-continuation','המשך לפי הכתובת: '+typed);go.type='button';go.id=field+'-option-external';go.setAttribute('role','option');go.append(create('small','','פתיחת חיפוש לפי הכתובת המלאה'));go.addEventListener('mousedown',e=>e.preventDefault());go.onclick=()=>externalChoice(field);out.append(go)}
 out.hidden=false;$(field).setAttribute('aria-expanded','true');
}
function resolveTyped(field){
 if(selected[field])return true;
 const raw=$(field).value.trim();
 if(!raw){status(field==='from'?'הקלידו כתובת, או בחרו תחנות ליד המיקום שלכם.':'הקלידו לאן רוצים להגיע.');$(field).focus();return false}
 const options=shown[field]||[],exact=options.filter(x=>x.kind!=='street'&&E.norm(x.name||x.city)===E.norm(raw));
 if(exact.length===1){if(field==='to'&&exact[0].kind==='city')changeMode('intercity');select(field,exact[0]);return true}
 suggestions(field);
 if(!(shown[field]||[]).length){externalChoice(field);return true}
 status(field==='from'?'בחרו אחת התחנות המוצגות, או השתמשו במיקום שלי.':'בחרו את היעד המוצג מתחת לשדה.');$(field).focus();return false;
}
function bindSearch(field){const input=$(field);input.addEventListener('input',()=>{clearResults();selected[field]=null;suggestions(field)});input.addEventListener('focus',()=>{if(!selected[field])suggestions(field)});input.addEventListener('blur',()=>setTimeout(()=>{if(document.activeElement!==input&&!$(field+'Options').contains(document.activeElement))close(field)},160));input.addEventListener('keydown',e=>{const box=$(field+'Options'),buttons=[...box.querySelectorAll('button')];if(e.key==='Escape')return close(field);if(!buttons.length||box.hidden)return;if(['ArrowDown','ArrowUp'].includes(e.key)){e.preventDefault();let i=buttons.findIndex(b=>b.classList.contains('active'));i=(i+(e.key==='ArrowDown'?1:-1)+buttons.length)%buttons.length;buttons.forEach((b,j)=>b.classList.toggle('active',i===j));input.setAttribute('aria-activedescendant',buttons[i].id);buttons[i].scrollIntoView({block:'nearest'})}if(e.key==='Enter'){const active=buttons.findIndex(b=>b.classList.contains('active'));e.preventDefault();if(active>=0)buttons[active].click();else{resolveTyped(field);if(selected[field]){if(field==='from')$('to').focus();else $('search').focus()}}}})}
function changeMode(next){clearResults();mode=next;if(mode==='intercity')loadRail().catch(()=>{});$('localTab').setAttribute('aria-selected',String(mode==='local'));$('intercityTab').setAttribute('aria-selected',String(mode==='intercity'));$('to').placeholder=mode==='local'?'למשל: אסותא, גן העיר, רכבת':'למשל: תל אביב, ירושלים, יבנה';if(selected.to&&((mode==='local'&&selected.to.city!=='אשדוד')||(mode==='intercity'&&selected.to.city==='אשדוד'))){selected.to=null;$('to').value=''}close('to');renderQuick()}
function renderQuick(){const root=$('quick');root.replaceChildren();if(!data)return;const specs=mode==='local'?[['אסותא','אסותא','תחנת בית החולים'],['גן העיר','גן העיר','ליד העירייה'],['רכבת / ביג','רכבת/מסוף ביג','תחנות האוטובוס במסוף'],['רובע א׳','מסחרי רובע א','תחנת המרכז המסחרי'],['סטאר סנטר','סטאר','תחנה ליד המרכז'],['חוף הקשתות','הקשתות','תחנה ליד החוף']]:[['תל אביב','תל אביב','לתחנת ירידה בעיר'],['ירושלים','ירושלים','לתחנת ירידה בעיר'],['באר שבע','באר שבע','לתחנת ירידה בעיר'],['יבנה','יבנה','לתחנת ירידה בעיר'],['אשקלון','אשקלון','לתחנת ירידה בעיר'],['רחובות','רחובות','לתחנת ירידה בעיר']];for(const [title,key,sub] of specs){const item=mode==='local'?(key==='רכבת/מסוף ביג'?placeChoices[0]:destinationLocalGroups.find(s=>E.norm(s.name).includes(E.norm(key)))):cityChoices.find(c=>E.norm(c.city).includes(E.norm(key)));if(!item)continue;const b=create('button','',title);b.type='button';b.append(create('span','',sub));b.onclick=()=>{select('to',item);if(!selected.from){$('from').focus();suggestions('from')}else $('search').focus()};root.append(b)}}
function groupFor(stop){return allGroups.find(g=>g.ids.includes(stop.id))||{...stop,ids:[stop.id]}}
function navigation(stop){const a=create('a','station-map-link','מיקום התחנה במפה ↗');a.href='https://www.google.com/maps/search/?api=1&query='+stop.lat+','+stop.lon;a.target='_blank';a.rel='noopener';return a}
function renderResult(r,index,network=data){
 const isRail=network.mode==='rail';
 const first=r.legs[0],last=r.legs.at(-1),card=create('article','route-card simple-answer');
 const lines=create('div','route-lines');
 r.legs.forEach((l,i)=>{if(i)lines.append(create('span','','←'));lines.append(create('span','line-pill',isRail?'רכבת '+l.headsign:'קו '+l.route.number))});
 lines.append(create('strong','direction','לכיוון '+(isRail?last.to.name:first.headsign.replaceAll('_',' / '))));card.append(lines);
 const badges=create('div','route-badges');badges.append(create('span','badge',r.transfers?'החלפה אחת':'ללא החלפה'));card.append(badges);
 const next=create('div','next-bus');next.append(create('span','next-label',isRail?'הרכבת הבאה מעד הלום':'האוטובוס הבא בתחנת העלייה'),create('strong','route-time',clock(r.depart)));card.append(next);
 const deps=(isRail?window.BusRail.departures(network,{from:first.from,to:first.to,date:$('date').value,time:clock(r.depart).slice(0,5),limit:5}):E.departures(network,{stop:groupFor(first.from),date:$('date').value,time:clock(r.depart).slice(0,5),routeId:first.route.id,headsign:first.headsign,limit:5})).filter(d=>d.time>=r.depart);
 const following=deps.filter(d=>d.time>r.depart).slice(0,3);
 if(following.length)card.append(create('p','next-departures','לאחר מכן: '+following.map(d=>clock(d.time)).join(' · ')));
 const facts=create('div','answer-facts');
 const row=(label,value,stop)=>{const box=create('section','answer-fact');box.append(create('span','fact-label',label),create('strong','fact-value',value));if(stop)box.append(navigation(stop));facts.append(box);return box};
 row('עולים בתחנה',stationName(first.from),first.from);
 row(r.transfers?'נסיעה כולל ההחלפה':'זמן נסיעה משוער','כ־'+mins(r.duration)+' דקות');
 row('יורדים בתחנה',stationName(last.to),last.to);
 if(selected.to?.kind==='place'&&Number.isFinite(selected.to.lat)){row('מהתחנה לנקודת היעד','כ־'+Math.round(E.distance(last.to,selected.to))+' מטר בקו אווירי').classList.add('destination-distance')}
 card.append(facts,create('p','schedule-note','השעות לפי לוח הזמנים; ההגעה בפועל עשויה להשתנות.'));
 const timetable=create('details','all-departures');timetable.append(create('summary','','כל שעות הקו מהתחנה הזאת'));
 timetable.addEventListener('toggle',()=>{if(!timetable.open||timetable.dataset.ready)return;timetable.dataset.ready='1';
  timetable.append(create('p','schedule-note','שעות מעבר מתוכננות בתחנת העלייה, לכיוון שנבחר. מוצגים התאריכים הקרובים לפי הלוח הזמין.'));
  for(let n=0;n<7;n++){const date=E.dayShift($('date').value,n);if(date.replaceAll('-','')>network.valid_until)break;
   const times=(isRail?window.BusRail.departures(network,{from:first.from,to:first.to,date,time:'00:00',limit:500}):['00:00','12:00'].flatMap(time=>E.departures(network,{stop:groupFor(first.from),date,time,routeId:first.route.id,headsign:first.headsign,limit:500})).filter((d,i,a)=>a.findIndex(x=>x.time===d.time)===i).sort((a,b)=>a.time-b.time)).filter(d=>d.time<86400);
   const day=create('section','timetable-day');day.append(create('h3','',new Date(date+'T12:00:00').toLocaleDateString('he-IL',{weekday:'long',day:'numeric',month:'numeric'})));
   const list=create('div','departure-times');if(times.length)times.forEach(d=>list.append(timeNode(d.time)));else list.textContent='אין נסיעות בלוח לתאריך הזה';day.append(list);timetable.append(day);
  }
 });card.append(timetable);
 const details=create('details','journey-details');details.append(create('summary','','תחנות בדרך ופרטי הנסיעה'));
 r.legs.forEach((l,i)=>{const leg=create('section','leg');leg.append(create('h4','',(isRail?'רכבת '+l.headsign:'קו '+l.route.number)+' · לכיוון '+(isRail?l.to.name:l.headsign.replaceAll('_',' / '))));
  if(i)leg.append(create('p','','החלפה בתחנה '+stationName(l.from)));
  leg.append(create('p','','תחנת עלייה '+l.from.code+' · '+clock(l.depart)),create('p','','תחנת ירידה '+l.to.code+' · '+clock(l.arrive)));
  const list=create('ol','stops-list');l.stopList.forEach(stop=>list.append(create('li','',stationName(stop))));leg.append(list);details.append(leg);
 });card.append(details);addStopsMap(card,r.legs);return card;
}
function addStopsMap(card,legs){
 const all=legs.flatMap(l=>[l.from,l.to]).filter(s=>Number.isFinite(s?.lat)&&Number.isFinite(s?.lon));
 if(!all.length)return;
 const btn=create('button','text-button','הצג תחנות על מפה');
 btn.type='button';btn.setAttribute('aria-expanded','false');
 const panel=create('div','stop-map');panel.hidden=true;
 const note=create('p','small-note','המפה מציגה את מיקומי התחנות. הקו המחבר ביניהן סכמטי בלבד ואינו מסלול הכביש.');
 btn.onclick=()=>{
  panel.hidden=!panel.hidden;panel.parentElement.hidden=panel.hidden;btn.setAttribute('aria-expanded',String(!panel.hidden));
  if(panel.hidden)return;
  if(!window.L){panel.textContent='המפה אינה זמינה כרגע. אפשר להשתמש בקישורי מיקום התחנות.';return}
  if(panel.dataset.ready){panel._map?.invalidateSize();return;}
  const map=window.L.map(panel,{scrollWheelZoom:false});
  window.L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'&copy; OpenStreetMap contributors',maxZoom:19}).addTo(map);
  const coords=all.map(s=>[s.lat,s.lon]);
  all.forEach((stop,i)=>{const popup=document.createElement('span');popup.textContent='תחנה '+(stop.code||'')+' · '+stationName(stop);window.L.marker(coords[i]).addTo(map).bindPopup(popup)});
  window.L.polyline(coords,{color:'#146b64',weight:3,dashArray:'6,8'}).addTo(map);
  map.fitBounds(window.L.latLngBounds(coords).pad(.25),{maxZoom:15});
  panel._map=map;panel.dataset.ready='1';setTimeout(()=>map.invalidateSize(),30);
 };
 const mapDetails=create('div','map-details');mapDetails.hidden=true;mapDetails.append(note,panel);btn.addEventListener('click',()=>{mapDetails.hidden=panel.hidden});card.append(btn,mapDetails);
}
function renderApproximateResult(x,index=0){
 const card=renderResult(x.trip,index),facts=card.querySelector('.answer-facts');
 let target=card.querySelector('.destination-distance');
 if(!target){target=create('section','answer-fact destination-distance');target.append(create('span','fact-label','מהתחנה לנקודת היעד'),create('strong','fact-value'));facts.append(target)}
 target.querySelector('strong').textContent='כ־'+x.alighting.straightMeters+' מטר בקו אווירי';
 if(x.boarding.straightMeters>20)facts.firstChild.append(create('p','access-distance','כ־'+x.boarding.straightMeters+' מטר מתחנת המוצא שבחרתם, בקו אווירי'));
 return card;
}
async function loadRail(){
 if(railData)return railData;
 if(!railLoad)railLoad=fetch('./data/rail.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('rail');return r.json()}).then(x=>{railData=x;return x}).catch(e=>{railLoad=null;throw e});
 return railLoad;
}
async function appendRailAlternatives(){
 document.getElementById('railAlternatives')?.remove();
 if(mode!=='intercity'||selected.to.city==='אשדוד')return;
 const area=create('section','rail-alternatives');area.id='railAlternatives';area.setAttribute('aria-label','אפשרות נסיעה ברכבת');
 area.append(create('h2','','אפשרות ברכבת — מעד הלום'));
 const official=create('a','station-map-link','בדיקת שעות ושינויים ברכבת ישראל ↗');official.href='https://www.rail.co.il/';official.target='_blank';official.rel='noopener';
 try{
  const network=await loadRail(),date=$('date').value,day=date.replaceAll('-','');
  const trips=window.BusRail.plan(network,{city:selected.to.city,date,time:$('time').value,limit:1});
  if(trips.length){
   if(!$('results').children.length){$('noResults').hidden=true;status('נמצאה אפשרות ברכבת מעד הלום.')}
   area.append(create('p','rail-access-note','השעות הן ליציאה מתחנת רכבת אשדוד עד הלום. ההגעה מהכתובת שלכם לתחנה אינה כלולה.'));
   const access=create('a','station-map-link rail-access-link','איך מגיעים באוטובוס לעד הלום?');
   const url=new URL(location.href);url.search='';const params={from:selected.from.id,to:'place:ashdod-rail',target_kind:'place',date,time:$('time').value,mode:'local',transfer:'0'};
   Object.entries(params).forEach(([k,v])=>url.searchParams.set(k,v));access.href=url.href;area.append(access);
   trips.forEach((r,i)=>{const card=renderResult(r,i,network);card.classList.add('rail-card');area.append(card)});
  }else area.append(create('p','rail-access-note',day<network.valid_from||day>network.valid_until?'אין כרגע לוח רכבות לתאריך שבחרתם. בדקו באתר רכבת ישראל.':'לא נמצאה רכבת מתאימה ליעד ולשעה בלוח שבאתר. אפשר לבדוק גם באתר רכבת ישראל.'));
 }catch{area.append(create('p','rail-access-note','לא הצלחנו לטעון את לוח הרכבות כרגע. אפשר לבדוק באתר רכבת ישראל.'))}
 area.append(official);$('answer').append(area);
}
function makeUrl(){const p=new URLSearchParams({from:selected.from.id,to:selected.to.kind==='city'?'city:'+selected.to.city:selected.to.id,date:$('date').value,time:$('time').value,mode,target_kind:selected.to.kind,transfer:$('transfer').checked?'1':'0'});return location.origin+location.pathname+'?'+p.toString()}
async function search(e){e?.preventDefault();if(!data)return;if(!resolveTyped('from')||!resolveTyped('to'))return;if(['external','street'].includes(selected.from.kind)||['external','street'].includes(selected.to.kind)||(selected.to.external&&selected.to.kind!=='city')){document.querySelector('.hero').classList.add('has-results');$('answer').hidden=false;$('resultTitle').textContent=label(selected.to);$('resultEyebrow').textContent='חיפוש לפי כתובת';const officialStreet=selected.from.kind==='street'||selected.to.kind==='street';$('resultNote').textContent=officialStreet?'הרחוב מוכר במאגר הרשמי, אך אין לו תחנה משויכת במאגר התחבורה. אפשר להמשיך לחיפוש לפי הכתובת.':'אין כרגע התאמה מאומתת לתחנה או למסלול הזה במאגר. אפשר להמשיך למתכנן תחבורה לפי הכתובות.';status(officialStreet?'הרחוב זוהה. להמשך, פתחו חיפוש לפי הכתובת.':'המשך חיפוש לפי הכתובת.');$('results').replaceChildren();$('noResults').hidden=false;$('emptyNote').textContent='לא מוצגת כאן נסיעה מחושבת. בחרו בקישור למטה להמשך.';$('tomorrow').hidden=true;fallback();return}if(selected.to.kind!=='city'&&selected.from.ids.some(id=>selected.to.ids.includes(id))){status('תחנת המוצא והיעד זהות. בחרו יעד אחר.',true);return}
 const date=$('date').value,key=date.replaceAll('-','');if(key<data.valid_from||key>data.valid_until){status('אין בקובץ לוח זמנים לתאריך הזה. בחרו תאריך בטווח המוצג.',true);return}
 status('מחפשים נסיעות שמתאימות לכם…');document.querySelector('.hero').classList.add('has-results');$('answer').hidden=false;$('answer').setAttribute('aria-busy','true');$('results').replaceChildren();$('search').disabled=true;await new Promise(resolve=>setTimeout(resolve,20));try{
 if($('approximateMode').checked&&selected.from.city==='אשדוד'&&selected.to.city==='אשדוד'&&Number.isFinite(selected.from.lat)&&Number.isFinite(selected.to.lat)){
  const estimates=window.BusApproximate.plan(data,E,{from:selected.from,to:selected.to,date,time:$('time').value,maxTransfers:mode==='local'?0:($('transfer').checked?1:0),limit:5});
  $('resultTitle').textContent=label(selected.to);
  $('resultEyebrow').textContent='אפשרויות מתחנות סמוכות · מרחקים משוערים';
  $('resultNote').textContent='מסלול ישיר סביר מקבל עדיפות על החלפה בין אוטובוסים. המרחקים בקו אווירי בלבד, וההליכה בפועל עשויה להיות ארוכה יותר. הזמנים מבוססים על לוח זמנים מתוכנן, ללא מידע בזמן אמת. תחנת מוצא ויעד שנבחרו אינן בהכרח כתובות מדויקות.';
  $('results').replaceChildren();estimates.slice(0,1).forEach((x,i)=>$('results').append(renderApproximateResult(x,i)));
  $('noResults').hidden=!!estimates.length;
  if(!estimates.length){$('emptyNote').textContent='לא נמצא מסלול מתאים בין התחנות הסמוכות. אפשר להמשיך למתכנן חיצוני.';fallback()}
  $('tomorrow').hidden=true;
  status(estimates.length?'נמצא מסלול מומלץ.':'לא נמצא מסלול מתאים.');
  $('answer').scrollIntoView({behavior:'smooth',block:'start'});
  return;
 }
 routes=E.plan(data,{from:selected.from,to:selected.to,date,time:$('time').value,maxTransfers:mode==='local'?0:($('transfer').checked?1:0),limit:5});
 let fallbackTransfers=null;
 // Before offering a transfer, look for a direct bus from a very close stop.
 // These distances are explicitly straight-line estimates, not verified pedestrian routes.
 if(!routes.length&&!$('transfer').checked&&selected.from.city==='אשדוד'&&selected.to.city==='אשדוד'&&Number.isFinite(selected.from.lat)&&Number.isFinite(selected.to.lat)&&window.BusApproximate){
  const nearbyDirect=window.BusApproximate.plan(data,E,{from:selected.from,to:selected.to,date,time:$('time').value,maxTransfers:0,limit:5,maxBoardMeters:350,maxAlightMeters:500});
  fallbackTransfers=E.plan(data,{from:selected.from,to:selected.to,date,time:$('time').value,maxTransfers:1,limit:5});
  const reasonableDirect=nearbyDirect;
  if(reasonableDirect.length){
   $('resultTitle').textContent=label(selected.to);
   $('resultEyebrow').textContent='קו ישיר מתחנה סמוכה';
   $('resultNote').textContent='אין קו ישיר מתחנת העלייה שנבחרה. נמצאו קווים ישירים מתחנות קרובות, אך המרחקים אליהן הם בקו אווירי בלבד, לא מרחקי הליכה מאומתים. יש לבדוק את דרך ההליכה, מעברי החצייה וזמני ההגעה לתחנה לפני היציאה. הזמנים הם לפי לוח מתוכנן ולא מידע חי.';
   $('results').replaceChildren();
   reasonableDirect.slice(0,1).forEach((x,i)=>$('results').append(renderApproximateResult(x,i)));
   $('noResults').hidden=true;$('tomorrow').hidden=true;
   status('נמצא מסלול ישיר מומלץ מתחנה סמוכה.');
   history.replaceState(null,'',makeUrl());
   $('answer').scrollIntoView({behavior:'smooth',block:'start'});
   return;
  }
 }
 if(mode==='intercity'&&!routes.length&&!$('transfer').checked){
   routes=fallbackTransfers||E.plan(data,{from:selected.from,to:selected.to,date,time:$('time').value,maxTransfers:1,limit:5});
   if(routes.length)status('לא נמצא מסלול ישיר מתחנת המוצא או מתחנות סמוכות; מוצגות אפשרויות עם החלפה כמוצא אחרון.');
 }$('resultTitle').textContent=label(selected.to);$('resultEyebrow').textContent='מ'+stationName(selected.from)+' · '+new Date(date+'T12:00:00').toLocaleDateString('he-IL',{weekday:'short',day:'numeric',month:'numeric'})+' · יציאה מהתחנה מ־'+$('time').value;$('resultNote').textContent='הזמנים מתוכננים ואינם כוללים הליכה. '+(selected.to.kind==='city'?'היעד הוא תחנת הירידה המצוינת בכל אפשרות בעיר / באזור שנבחרו. ':selected.to.kind==='place'?'היעד כולל כמה תחנות באותו מתחם; תחנת הירידה המדויקת מופיעה בכל מסלול. ':'')+'החיפוש מציע נסיעות מהרשת שנקלטה, עד שש שעות קדימה לעלייה הראשונה.';(mode==='local'?routes.slice(0,1):routes).forEach((r,i)=>$('results').append(renderResult(r,i)));$('noResults').hidden=!!routes.length;if(!routes.length)fallback();$('emptyNote').textContent='ייתכן שאין שירות בשעה שנבחרה, שנדרשת תחנת עלייה אחרת או שהמסלול מחייב החלפות שאינן כלולות בגרסה הזאת. אין בכך אישור שאין שירות ליעד.';const tomorrow=E.dayShift(date,1);$('tomorrow').hidden=tomorrow.replaceAll('-','')>data.valid_until;status(routes.length?(mode==='local'?'נמצא מסלול מומלץ לפי לוח הזמנים.':'נמצאו '+routes.length+' אפשרויות לפי לוח הזמנים.'):'לא נמצאו אפשרויות בטווח החיפוש.');history.replaceState(null,'',makeUrl());(matchMedia('(max-width:600px)').matches?$('answer'):document.querySelector('.hero')).scrollIntoView({behavior:'smooth',block:'start'})}catch(err){status('לא הצלחנו לחשב את המסלול כרגע. נסו שוב.',true)}finally{await appendRailAlternatives();if($('results').children.length)$('resultNote').textContent='';$('answer').setAttribute('aria-busy','false');$('search').disabled=false}}
function nearby(){if(!data||geoBusy)return;if(!navigator.geolocation){status('הדפדפן אינו תומך במיקום. אפשר לבחור תחנה בחיפוש.',true);return}geoBusy=true;close('from');close('to');$('locate').disabled=true;$('locateText').disabled=true;status('ממתינים לאישור מיקום מהדפדפן…');navigator.geolocation.getCurrentPosition(position=>{geoBusy=false;$('locate').disabled=false;$('locateText').disabled=false;const here={lat:position.coords.latitude,lon:position.coords.longitude},found=localGroups.map(s=>({...s,meters:E.distance(here,s)})).sort((a,b)=>a.meters-b.meters).slice(0,5);$('nearbyList').replaceChildren();$('nearby').hidden=false;const acc=Math.round(position.coords.accuracy);$('nearbyNote').textContent=(found[0]?.meters>5000?'המיקום שזוהה רחוק מאשדוד. ':'')+'המרחקים הם בקו אווירי, לא מסלול הליכה. דיוק המיקום שהדפדפן דיווח: כ־'+acc+' מטר.';for(const s of found){const row=create('div','nearby-row'),copy=create('div','');copy.append(create('strong','',stationName(s)),create('small','','תחנה '+s.code+' · '+(s.meters>=1000?(s.meters/1000).toFixed(1)+' ק״מ':Math.round(s.meters)+' מטר')+' בקו אווירי'));const actions=create('div','nearby-actions'),pick=create('button','','לצאת מכאן');pick.type='button';pick.onclick=()=>{select('from',s);status('תחנת המוצא נבחרה. עכשיו בחרו יעד.');$('to').focus()};const walk=create('a','','ניווט הליכה ↗');walk.href='https://www.google.com/maps/dir/?api=1&origin='+here.lat+','+here.lon+'&destination='+s.lat+','+s.lon+'&travelmode=walking';walk.target='_blank';walk.rel='noopener';actions.append(pick,walk);row.append(copy,actions);$('nearbyList').append(row)}status('נמצאו תחנות קרובות באשדוד. בחרו מאיזו תחנה לצאת.');$('nearby').scrollIntoView({behavior:'smooth'})},error=>{geoBusy=false;$('locate').disabled=false;$('locateText').disabled=false;status(error.code===1?'המיקום לא אושר. אפשר לבחור תחנה לפי הכתובות המוצגות.':'המיקום אינו זמין כרגע. אפשר לבחור תחנה לפי הכתובות המוצגות.')},{enableHighAccuracy:true,timeout:12000,maximumAge:60000})}
$('journeyForm').addEventListener('submit',search);$('localTab').onclick=()=>changeMode('local');$('intercityTab').onclick=()=>changeMode('intercity');$('now').onclick=()=>{clearResults();setNow()};for(const id of ['date','time','transfer','approximateMode'])$(id).addEventListener('change',clearResults);$('locate').onclick=nearby;$('locateText').onclick=nearby;$('closeNearby').onclick=()=>$('nearby').hidden=true;$('tomorrow').onclick=()=>{$('date').value=E.dayShift($('date').value,1);$('time').value='08:00';search()};$('share').onclick=async()=>{try{await navigator.clipboard.writeText(makeUrl());$('share').textContent='הקישור הועתק ✓'}catch{status('אפשר להעתיק את כתובת העמוד כדי לשתף את החיפוש.')}};bindSearch('from');bindSearch('to');setNow();
fetch('./data/network.json?day='+israelNow().date,{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('feed');return r.json()}).then(x=>{data=x;allGroups=E.groups(data);placeChoices=E.places(data);const canBoard=new Set(data.patterns.flatMap(p=>p.stops.filter(s=>s[3]===0).map(s=>s[0])));localGroups=allGroups.filter(s=>s.city==='אשדוד'&&s.ids.some(id=>canBoard.has(id)));const canAlight=new Set(data.patterns.flatMap(p=>p.stops.filter(s=>s[4]===0).map(s=>s[0])));destinationLocalGroups=allGroups.filter(s=>s.city==='אשדוד'&&s.ids.some(id=>canAlight.has(id)));const coveredCities=new Set(Object.values(data.stops).map(s=>s.city));const cities=[...new Set([...(data.destination_cities||[]),...coveredCities])].filter(c=>c&&c!=='אשדוד');cityChoices=cities.map(city=>({kind:'city',id:'city:'+city,city,external:!coveredCities.has(city),search:E.norm(city),label:city})).sort((a,b)=>a.city.localeCompare(b.city,'he'));const aliases=[['קריית גת','קרית גת'],['תל אביב','תל אביב יפו'],['נתבג','נמל תעופה בן גוריון']];for(const [alias,city] of aliases){const c=cityChoices.find(c=>c.city===city);if(c)c.search+=' '+E.norm(alias)}for(const g of new Set([...localGroups,...destinationLocalGroups])){if(g.name.includes('גן העיר'))g.search+=' '+E.norm('עירייה עיריית אשדוד סיטי');if(g.name.includes('אסותא'))g.search+=' '+E.norm('בית חולים');if(g.name.includes('מסוף ביג'))g.search+=' '+E.norm('תחנת רכבת עד הלום')}
 const n=israelNow(),min=data.valid_from.slice(0,4)+'-'+data.valid_from.slice(4,6)+'-'+data.valid_from.slice(6),max=data.valid_until.slice(0,4)+'-'+data.valid_until.slice(4,6)+'-'+data.valid_until.slice(6);$('date').min=n.date>min?n.date:min;$('date').max=max;$('search').disabled=n.date>max;if(n.date>max)status('לוח הזמנים שבאתר פג תוקף. אין להסתמך עליו; עברו למתכנן משרד התחבורה בקישור למטה.',true);else status('מוכנים. בחרו תחנת מוצא ויעד.');const count=new Set(Object.values(data.routes).map(r=>r.operator+'|'+r.number)).size;$('dataSummary').textContent=localGroups.length+' תחנות עלייה באשדוד · '+count+' קווי אוטובוס ברשת · הופק '+new Date(data.generated_at).toLocaleDateString('he-IL');$('sourceDetails').textContent='הופק: '+new Date(data.generated_at).toLocaleString('he-IL',{timeZone:'Asia/Jerusalem'})+'. טווח לוחות הזמנים בקובץ: '+min+' עד '+max+'. שירות בכל יום כפוף ללוח של הקו.';renderQuick();
 fetch('./data/ashdod-streets.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('streets');return r.json()}).then(source=>{streetChoices=window.BusStreets.choices(source,allGroups);$('dataSummary').textContent+=' · '+source.streets.length+' רחובות רשמיים';for(const field of ['from','to'])if(document.activeElement===$(field)&&!selected[field])suggestions(field)}).catch(()=>{});
 const params=new URLSearchParams(location.search);if(params.get('mode')==='intercity')changeMode('intercity');for(const f of ['from','to']){const id=params.get(f);if(id){const item=f==='to'&&id.startsWith('city:')?cityChoices.find(c=>c.id===id):f==='to'?E.resolveDestination(data,id,params.get('target_kind')==='stop'):allGroups.find(g=>g.ids.includes(id)&&g.city==='אשדוד');if(item)select(f,item)}}if(params.get('date')&&params.get('date')>=$('date').min&&params.get('date')<=max)$('date').value=params.get('date');if(/^\d\d:\d\d$/.test(params.get('time')||''))$('time').value=params.get('time');if(params.get('transfer')==='0')$('transfer').checked=false;if(selected.from&&selected.to)search();
}).catch(()=>{status('לא הצלחנו לטעון את לוח הזמנים. נסו לרענן, או עברו למתכנן משרד התחבורה.',true);$('dataSummary').textContent='נתוני הנסיעות אינם זמינים כרגע';$('sourceDetails').textContent='לא נטען קובץ נתונים; אין מוצגות תוצאות נסיעה.'});
})();
