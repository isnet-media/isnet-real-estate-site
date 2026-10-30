/* Scheduled transit planning. Uses exact GTFS calendars, pickup/dropoff rules and direction. */
(function(root){'use strict';
const norm=s=>String(s||'').replace(/["'׳״־–-]/g,'').replace(/\s+/g,'').toLowerCase();
const distance=(a,b)=>{const r=Math.PI/180,x=(b.lat-a.lat)*r,y=(b.lon-a.lon)*r;return 6371000*2*Math.asin(Math.sqrt(Math.sin(x/2)**2+Math.cos(a.lat*r)*Math.cos(b.lat*r)*Math.sin(y/2)**2))};
const dayShift=(date,n)=>{const d=new Date(date+'T12:00:00Z');d.setUTCDate(d.getUTCDate()+n);return d.toISOString().slice(0,10)};
const active=(s,date)=>{const key=date.replaceAll('-','');return s&&s.start<=key&&s.end>=key&&s.days[new Date(date+'T12:00:00Z').getUTCDay()]===1};
function groups(data){const out=new Map();for(const s of Object.values(data.stops)){const key=[s.code,s.lat.toFixed(5),s.lon.toFixed(5)].join('|');if(!out.has(key))out.set(key,{...s,ids:[],kind:'stop',label:s.name+' · '+s.city,search:norm([s.name,s.city,s.code].join(' '))});out.get(key).ids.push(s.id)}return [...out.values()]}
function runs(data,date){const out=[];for(const offset of [-1,0,1]){const d=dayShift(date,offset);for(const [pi,service,start] of data.trips){if(active(data.services[service],d))out.push({p:data.patterns[pi],start:start+offset*86400,key:[pi,service,start,offset].join('|')})}}return out}
function directLeg(run,bi,ai,data){const a=run.p.stops[bi],b=run.p.stops[ai];return {route:data.routes[run.p.route],headsign:run.p.headsign,from:data.stops[a[0]],to:data.stops[b[0]],depart:run.start+a[2],arrive:run.start+b[1],stops:ai-bi,stopList:run.p.stops.slice(bi,ai+1).map(s=>data.stops[s[0]]),runKey:run.key}}

function places(data){
 const anchor={lat:31.7746,lon:34.665};
 const ids=Object.values(data.stops).filter(s=>s.city==='אשדוד'&&distance(s,anchor)<=250&&norm(s.name).includes('רכבת')&&(norm(s.name).includes('מסוףביג')||norm(s.name).includes('אשדודעדהלום'))).map(s=>s.id);
 return ids.length?[{id:'place:ashdod-rail',kind:'place',name:'רכבת אשדוד עד הלום / מסוף ביג',city:'אשדוד',lat:anchor.lat,lon:anchor.lon,ids,search:norm('רכבת תחנת רכבת עד הלום ביג מסוף ביג BIG מתחם')}]:[];
}
function resolveDestination(data,id,exactStop=false){
 const pp=places(data),place=pp.find(p=>p.id===id||(!exactStop&&id==='52242'&&p.ids.includes(id)));
 return place||groups(data).find(g=>g.ids.includes(id));
}

function destinations(data,target){if(target.kind==='city')return new Set(Object.values(data.stops).filter(s=>s.city===target.city).map(s=>s.id));return new Set(target.ids||[target.id])}
function plan(data,{from,to,date,time,maxTransfers=1,limit=5}){
 const [hh,mm]=time.split(':').map(Number),now=hh*3600+mm*60;
 if(!Number.isFinite(now)||!from||!to)return [];
 const origins=new Set(from.ids||[from.id]),ends=destinations(data,to),rr=runs(data,date);const results=[],reach=new Map();
 const targetIndex=new Map();if(to.kind==='city')for(const p of data.patterns){let idx=-1;p.stops.forEach((s,i)=>{if(ends.has(s[0])&&s[4]===0)idx=i});targetIndex.set(p,idx)}
 const isEnd=(run,i)=>ends.has(run.p.stops[i][0])&&(to.kind!=='city'||targetIndex.get(run.p)===i);
 function add(legs){const last=legs.at(-1),first=legs[0];if(last.arrive<first.depart||last.arrive>now+12*3600)return;results.push({legs,depart:first.depart,arrive:last.arrive,duration:last.arrive-first.depart,total:last.arrive-now,wait:first.depart-now,transfers:legs.length-1})}
 // First vehicle. Retain feasible runs so a later feeder can reduce transfer waiting.
 for(const run of rr){let board=-1;for(let i=0;i<run.p.stops.length;i++){const s=run.p.stops[i],dep=run.start+s[2];if(board<0&&origins.has(s[0])&&s[3]===0&&dep>=now&&dep<=now+6*3600)board=i;
  if(board>=0&&i>board&&s[4]===0){const leg=directLeg(run,board,i,data);if(isEnd(run,i))add([leg]);if(leg.arrive<=now+6*3600){if(!reach.has(s[0]))reach.set(s[0],[]);reach.get(s[0]).push(leg)}}}}
 if(maxTransfers){
  // Only the same physical stop (aliases with identical code/coordinates). No guessed street crossings.
  const aliases=new Map();for(const g of groups(data)){const options=g.ids.flatMap(id=>reach.get(id)||[]).sort((a,b)=>a.arrive-b.arrive);if(options.length)for(const id of g.ids)aliases.set(id,options)}
  for(const run of rr){let board=-1,first=null;for(let i=0;i<run.p.stops.length;i++){const s=run.p.stops[i],options=aliases.get(s[0])||[],dep=run.start+s[2];if(s[3]===0&&dep<=now+8*3600){for(const r of options){if(r.arrive+120>dep)break;if(r.runKey!==run.key&&!(run.p.route===r.route.id&&run.p.headsign===r.headsign)&&(!first||r.depart>first.depart)){board=i;first=r}}}if(board>=0&&i>board&&s[4]===0&&isEnd(run,i))add([first,directLeg(run,board,i,data)])}}

 }
 results.sort((a,b)=>a.arrive-b.arrive||a.transfers-b.transfers||b.depart-a.depart);
 const useful=results.filter(r=>!results.some(o=>o!==r&&o.legs.at(-1).to.code===r.legs.at(-1).to.code&&o.arrive<=r.arrive&&o.transfers<=r.transfers&&o.depart>=r.depart&&(o.arrive<r.arrive||o.transfers<r.transfers||o.depart>r.depart)));
 const seen=new Set();return useful.filter(r=>{const k=r.legs.map(l=>[l.route.id,l.from.code,l.to.code,l.depart].join(':')).join('|');if(seen.has(k))return false;seen.add(k);return true}).slice(0,limit);
}
function departures(data,{stop,date,time,routeId,headsign,limit=8}){const now=time.split(':').map(Number).reduce((a,n,i)=>a+n*(i?60:3600),0),ids=new Set(stop.ids||[stop.id]),out=[];for(const run of runs(data,date)){if(routeId&&run.p.route!==routeId)continue;if(headsign&&run.p.headsign!==headsign)continue;for(const s of run.p.stops)if(ids.has(s[0])&&s[3]===0&&run.start+s[2]>=now&&run.start+s[2]<=now+12*3600)out.push({time:run.start+s[2],route:data.routes[run.p.route],headsign:run.p.headsign,stop:data.stops[s[0]]})}out.sort((a,b)=>a.time-b.time);const seen=new Set();return out.filter(d=>{const key=[d.route.id,d.headsign,d.time].join('|');if(seen.has(key))return false;seen.add(key);return true}).slice(0,limit)}
root.BusEngine={places,resolveDestination,norm,distance,dayShift,active,groups,runs,plan,departures};if(typeof module!=='undefined')module.exports=root.BusEngine;
})(typeof window==='undefined'?globalThis:window);
