const assert=require('node:assert/strict');
const test=require('node:test');
const D=require('./door-to-door.js');
const origin={lat:31.80,lon:34.65},boarding={lat:31.801,lon:34.651};
const alighting={lat:31.82,lon:34.67},destination={lat:31.821,lon:34.671};
const walk=(a,b,seconds)=>({mode:'walking',verified:true,distanceMeters:150,durationSeconds:seconds,geometry:[a,b]});
test('distance is finite and symmetric',()=>{
 assert.equal(D.meters(origin,origin),0);
 assert.ok(D.meters(origin,boarding)>0);
 assert.ok(Math.abs(D.meters(origin,boarding)-D.meters(boarding,origin))<1e-6);
});
test('candidate prefilter does not pretend to compute walking distance',()=>{
 const xs=D.candidates([{...boarding,id:'a'},{lat:33,lon:35,id:'b'}],origin);
 assert.equal(xs.length,1);
 assert.equal(xs[0].stop.id,'a');
 assert.ok(Number.isFinite(xs[0].straightMeters));
 assert.equal('walkMeters' in xs[0],false);
});
test('reject unverified pedestrian geometry',()=>{
 assert.throws(()=>D.verifyWalk({mode:'walking',verified:false,distanceMeters:100,durationSeconds:100,geometry:[origin,boarding]},origin,boarding));
 assert.throws(()=>D.verifyWalk({mode:'driving',verified:true,distanceMeters:100,durationSeconds:100,geometry:[origin,boarding]},origin,boarding));
});
test('compose includes both walking legs and scheduled status',()=>{
 const r=D.compose({origin,destination,firstStop:boarding,lastStop:alighting,
  walkToStop:walk(origin,boarding,180),walkFromStop:walk(alighting,destination,240),
  transit:{departureEpoch:1000,arrivalEpoch:1600},departureEpoch:700});
 assert.equal(r.arrivalEpoch,1840);
 assert.equal(r.totalSeconds,1140);
 assert.equal(r.scheduledOnly,true);
});
test('reject missed connection',()=>{
 assert.throws(()=>D.compose({origin,destination,firstStop:boarding,lastStop:alighting,
  walkToStop:walk(origin,boarding,180),walkFromStop:walk(alighting,destination,240),
  transit:{departureEpoch:800,arrivalEpoch:1600},departureEpoch:700}));
});
test('map bounds include all supplied coordinates',()=>{
 const b=D.mapBounds([origin,destination]);
 assert.ok(b.south<origin.lat&&b.north>destination.lat);
 assert.ok(b.west<origin.lon&&b.east>destination.lon);
});
