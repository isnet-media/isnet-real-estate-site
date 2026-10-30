/* Door-to-door orchestrator. Provider is injected; never calls public demo APIs directly.
 * Provider.geocode(text) => [{label,lat,lon,confidence,source,precision}]
 * Provider.walk(from,to) => verified pedestrian geometry as specified in DOOR_TO_DOOR.md
 */
(function(root,factory){
 const api=factory(typeof module==='object'&&module.exports?require('./door-to-door.js'):root.BusDoorToDoor);
 if(typeof module==='object'&&module.exports)module.exports=api;
 else root.BusJourneyPlanner=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(D){
 'use strict';
 if(!D)throw Error('Door-to-door core unavailable');
 const seconds=t=>{const a=String(t).split(':').map(Number);if(a.length!==2||a.some(x=>!Number.isInteger(x))||a[0]>23||a[0]<0||a[1]>59||a[1]<0)throw Error('Invalid time');return a[0]*3600+a[1]*60};
 const unique=(xs)=>[...new Map(xs.map(x=>[x.id,x])).values()];
 function boardingStops(data){const ids=new Set(data.patterns.flatMap(p=>p.stops.filter(s=>s[3]===0).map(s=>s[0])));return unique(Object.values(data.stops).filter(s=>ids.has(s.id)&&s.city==='אשדוד'))}
 function alightingStops(data){const ids=new Set(data.patterns.flatMap(p=>p.stops.filter(s=>s[4]===0).map(s=>s[0])));return unique(Object.values(data.stops).filter(s=>ids.has(s.id)))}
 async function address(provider,text){
   if(!text||text.trim().length<3||text.length>180)throw Error('Enter a valid address');
   const results=await provider.geocode(text);
   if(!Array.isArray(results))throw Error('Geocoding unavailable');
   const exact=results.filter(x=>x&&x.precision==='address'&&x.confidence>=0.8&&x.source&&Number.isFinite(x.lat)&&Number.isFinite(x.lon));
   if(exact.length!==1)throw Error(exact.length?'Address ambiguous: choose a specific result':'Exact address not verified');
   return exact[0];
 }
 async function walkCandidates(provider,location,stops,{limit=8,radius=900}={}){
   const pool=D.candidates(stops,location,limit,radius);
   const resolved=await Promise.allSettled(pool.map(async item=>{
     const walk=await provider.walk(location,item.stop);
     return {...item,walk:D.verifyWalk(walk,location,item.stop)};
   }));
   return resolved.filter(x=>x.status==='fulfilled').map(x=>x.value)
     .sort((a,b)=>a.walk.durationSeconds-b.walk.durationSeconds);
 }
 function stopChoice(stop){return {kind:'stop',id:stop.id,ids:[stop.id],name:stop.name,city:stop.city,code:stop.code}}
 async function plan({data,engine,provider,fromText,toText,date,time,maxTransfers=1,boardingBufferSeconds=120}){
   if(!data||!engine||!provider||!provider.geocode||!provider.walk)throw Error('Required provider missing');
   const [origin,destination]=await Promise.all([address(provider,fromText),address(provider,toText)]);
   const [boards,alights]=await Promise.all([
     walkCandidates(provider,origin,boardingStops(data)),
     walkCandidates(provider,destination,alightingStops(data))
   ]);
   if(!boards.length||!alights.length)return {routes:[],reason:'No verified walking connections',origin,destination};
   const start=seconds(time),results=[];
   // Schedule planner expects a local clock time. Walking+buffer shifts the earliest feasible boarding.
   for(const board of boards.slice(0,5)){
     const earliest=start+board.walk.durationSeconds+boardingBufferSeconds;
     if(earliest>=86400)continue;
     const departureTime=String(Math.floor(earliest/3600)).padStart(2,'0')+':'+String(Math.floor(earliest%3600/60)).padStart(2,'0');
     for(const alight of alights.slice(0,7)){
       const transitRoutes=engine.plan(data,{from:stopChoice(board.stop),to:stopChoice(alight.stop),date,time:departureTime,maxTransfers,limit:4});
       for(const transit of transitRoutes){
         if(transit.depart<earliest)continue;
         const total=transit.arrive+alight.walk.durationSeconds-start;
         if(total<0||total>24*3600)continue;
         results.push({origin,destination,board:board.stop,alight:alight.stop,
           walkToStop:board.walk,walkFromStop:alight.walk,transit,
           totalSeconds:total,departureSeconds:start,arrivalSeconds:transit.arrive+alight.walk.durationSeconds,
           scheduledOnly:true});
       }
     }
   }
   results.sort((a,b)=>a.arrivalSeconds-b.arrivalSeconds||a.transit.transfers-b.transit.transfers);
   const seen=new Set();
   return {origin,destination,routes:results.filter(x=>{
     const key=x.transit.legs.map(l=>[l.route.id,l.from.id,l.to.id,l.depart].join(':')).join('|');
     if(seen.has(key))return false;seen.add(key);return true;
   }).slice(0,5)};
 }
 return {address,walkCandidates,plan,boardingStops,alightingStops};
});
