/* Rail starts at the official Ashdod station. Access from the city is separate. */
(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('./engine.js'):root.BusEngine);if(typeof module==='object'&&module.exports)module.exports=api;else root.BusRail=api})(typeof globalThis==='undefined'?this:globalThis,function(E){
 function plan(data,{city,date,time,limit=1}){
  const day=date.replaceAll('-','');if(!data||day<data.valid_from||day>data.valid_until)return [];
  const from={ids:data.origin_ids},to={kind:'city',city};
  if(!Object.values(data.stops).some(s=>E.norm(s.city)===E.norm(city)))return [];
  const canonical=Object.values(data.stops).find(s=>E.norm(s.city)===E.norm(city)).city;
  return E.plan(data,{from,to:{...to,city:canonical},date,time,maxTransfers:1,limit}).filter(r=>r.legs.every(l=>l.route.mode==='rail'));
 }
 function departures(data,{from,to,date,time,limit=500}){
  const [h,m]=time.split(':').map(Number),now=h*3600+m*60,out=[];
  for(const run of E.runs(data,date)){
   let board=-1;
   for(let i=0;i<run.p.stops.length;i++){
    const s=run.p.stops[i],depart=run.start+s[2];
    if(board<0&&s[0]===from.id&&s[3]===0&&depart>=now&&depart<=now+86400)board=i;
    if(board>=0&&i>board&&s[0]===to.id&&s[4]===0){out.push({time:run.start+run.p.stops[board][2],route:data.routes[run.p.route],headsign:run.p.headsign,stop:data.stops[from.id]});break}
   }
  }
  const seen=new Set();return out.sort((a,b)=>a.time-b.time).filter(x=>{const k=x.time+':'+x.headsign;if(seen.has(k))return false;seen.add(k);return true}).slice(0,limit);
 }
 return {plan,departures};
});
