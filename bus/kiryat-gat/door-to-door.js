/* Ashdod bus: safe door-to-door building blocks (not connected to live UI yet).
 * Providers must return verified coordinates and pedestrian routing results.
 * Do not present straight-line distances as walking distances.
 */
(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  else root.BusDoorToDoor=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const finite=x=>typeof x==='number'&&Number.isFinite(x);
  function point(p){
    if(!p||!finite(p.lat)||!finite(p.lon)||Math.abs(p.lat)>90||Math.abs(p.lon)>180)throw Error('Invalid coordinates');
    return {lat:p.lat,lon:p.lon};
  }
  function meters(a,b){
    a=point(a);b=point(b);
    const rad=Math.PI/180,dLat=(b.lat-a.lat)*rad,dLon=(b.lon-a.lon)*rad;
    const h=Math.sin(dLat/2)**2+Math.cos(a.lat*rad)*Math.cos(b.lat*rad)*Math.sin(dLon/2)**2;
    return 6371000*2*Math.atan2(Math.sqrt(h),Math.sqrt(Math.max(0,1-h)));
  }
  function candidates(stops,location,limit=12,maxStraightMeters=1200){
    point(location);
    return stops.filter(s=>s&&finite(s.lat)&&finite(s.lon))
      .map(s=>({stop:s,straightMeters:Math.round(meters(location,s))}))
      .filter(x=>x.straightMeters<=maxStraightMeters)
      .sort((a,b)=>a.straightMeters-b.straightMeters).slice(0,limit);
  }
  function verifyWalk(walk,from,to){
    point(from);point(to);
    if(!walk||walk.mode!=='walking'||walk.verified!==true||
      !finite(walk.distanceMeters)||walk.distanceMeters<0||
      !finite(walk.durationSeconds)||walk.durationSeconds<0||
      !Array.isArray(walk.geometry)||walk.geometry.length<2)throw Error('Verified pedestrian route required');
    walk.geometry.forEach(point);
    return walk;
  }
  function compose({origin,destination,firstStop,lastStop,transit,walkToStop,walkFromStop,departureEpoch}){
    [origin,destination,firstStop,lastStop].forEach(point);
    verifyWalk(walkToStop,origin,firstStop);
    verifyWalk(walkFromStop,lastStop,destination);
    if(!transit||!finite(transit.departureEpoch)||!finite(transit.arrivalEpoch)||
      transit.arrivalEpoch<transit.departureEpoch||!finite(departureEpoch)||
      transit.departureEpoch<departureEpoch+walkToStop.durationSeconds)throw Error('Unverified or unreachable connection');
    const arrivalEpoch=transit.arrivalEpoch+walkFromStop.durationSeconds;
    return {
      origin,destination,transit,walkToStop,walkFromStop,departureEpoch,arrivalEpoch,
      totalSeconds:arrivalEpoch-departureEpoch,
      scheduledOnly:transit.realtimeVerified!==true,
      walkingVerified:true
    };
  }
  function mapBounds(points,padding=0.002){
    const coords=points.map(point);
    if(!coords.length)throw Error('Map requires points');
    return {south:Math.max(-90,Math.min(...coords.map(p=>p.lat))-padding),
      west:Math.max(-180,Math.min(...coords.map(p=>p.lon))-padding),
      north:Math.min(90,Math.max(...coords.map(p=>p.lat))+padding),
      east:Math.min(180,Math.max(...coords.map(p=>p.lon))+padding)};
  }
  return {point,meters,candidates,verifyWalk,compose,mapBounds};
});
