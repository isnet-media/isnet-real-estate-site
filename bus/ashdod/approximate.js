/* Lightweight stop ranking and timetable planning, with explicitly approximate distances.
 * Inputs are VERIFIED coordinates, not unverified street text.
 */
(function(root,factory){
 const api=factory(typeof module==='object'&&module.exports?require('./door-to-door.js'):root.BusDoorToDoor);
 if(typeof module==='object'&&module.exports)module.exports=api;else root.BusApproximate=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(D){
 'use strict';
 const walkSpeed=1.15; // illustrative 4.14 km/h, not a prediction
 const buffer=180; // seconds to avoid missed boardings
 const distance=(a,b)=>Math.round(D.meters(a,b));
 function nearest(stops,point,limit=8,radius=1400){
   return D.candidates(stops,point,limit,radius).map(x=>({
     stop:x.stop,straightMeters:x.straightMeters,
     estimatedWalkingSeconds:Math.ceil(x.straightMeters/walkSpeed),
     warning:'מרחק בקו אווירי בלבד; הדרך בפועל עשויה להיות ארוכה יותר'
   }));
 }
 const choice=s=>({kind:'stop',id:s.id,ids:[s.id],name:s.name,city:s.city,code:s.code});
 const hhmm=s=>{const m=Math.ceil(s/60);return String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0')};
 function stopSets(data){
   const boards=new Set(),alights=new Set();
   for(const p of data.patterns)for(const s of p.stops){if(s[3]===0)boards.add(s[0]);if(s[4]===0)alights.add(s[0])}
   const all=Object.values(data.stops);
   return {boards:all.filter(s=>boards.has(s.id)&&s.city==='אשדוד'),alights:all.filter(s=>alights.has(s.id)&&s.city==='אשדוד')};
 }
 function plan(data,engine,{from,to,date,time,maxTransfers=1,limit=5}){
   D.point(from);D.point(to);
   const [h,m]=String(time).split(':').map(Number),start=h*3600+m*60;
   if(!Number.isInteger(h)||!Number.isInteger(m)||h<0||h>23||m<0||m>59)throw Error('Invalid departure time');
   const stops=stopSets(data),origins=nearest(stops.boards,from,7),destinations=nearest(stops.alights,to,8),results=[];
   for(const a of origins){
     const earliest=start+a.estimatedWalkingSeconds+buffer;
     if(earliest>=86400)continue;
     for(const b of destinations){
       const trips=engine.plan(data,{from:choice(a.stop),to:choice(b.stop),date,time:hhmm(earliest),maxTransfers,limit:3});
       for(const trip of trips){
         if(trip.depart<earliest)continue;
         const estimatedArrival=trip.arrive+b.estimatedWalkingSeconds;
         results.push({trip,boarding:a,alighting:b,estimatedArrival,estimatedTotalSeconds:estimatedArrival-start,
           approximation:true,live:false,warning:'המרחקים בקו אווירי, וזמן ההליכה הוא אומדן בלבד. אין התחייבות להספיק לאוטובוס.'});
       }
     }
   }
   results.sort((a,b)=>a.estimatedArrival-b.estimatedArrival||a.trip.transfers-b.trip.transfers);
   const seen=new Set();
   return results.filter(x=>{
     const k=x.trip.legs.map(l=>[l.route.id,l.from.id,l.to.id,l.depart].join(':')).join('|');
     if(seen.has(k))return false;seen.add(k);return true;
   }).slice(0,limit);
 }
 return {nearest,plan,stopSets,distance,walkSpeed,buffer};
});
