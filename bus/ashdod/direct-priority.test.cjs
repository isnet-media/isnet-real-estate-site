'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const E=require('./engine.js'),A=require('./approximate.js'),data=require('./data/network.json');

// Regression for the passenger-reported Ashdod Het quarter -> Ashdod Ad Halom
// station search. It is a timetable snapshot, not a realtime service claim.
test('Het quarter stop 11931: nearby direct bus must precede an unnecessary transfer',t=>{
 const date='2026-10-30';
 if(data.valid_from>date.replaceAll('-','')||data.valid_until<date.replaceAll('-','')){
  t.skip('This historical date is no longer within the bundled GTFS feed range');
  return;
 }
 const from=E.groups(data).find(g=>g.ids.includes('11931'));
 const to=E.places(data).find(p=>p.id==='place:ashdod-rail');
 assert.ok(from,'GTFS origin stop 11931 must be present');
 assert.ok(to,'Ashdod Ad Halom station place must be present');
 assert.equal(from.name,'הכלנית/הצבעוני');
 const exact=E.plan(data,{from,to,date,time:'13:00',maxTransfers:0,limit:5});
 assert.equal(exact.length,0,'there is no direct option from this exact platform at this hour');
 const nearest=A.plan(data,E,{from,to,date,time:'13:00',maxTransfers:0,limit:5,maxBoardMeters:350,maxAlightMeters:500});
 assert.ok(nearest.length>0,'a nearby boarding stop should offer a direct bus');
 assert.equal(nearest[0].trip.transfers,0);
 assert.ok(nearest.some(x=>x.boarding.straightMeters<=100&&x.trip.legs.some(l=>l.route.number==='35')),'line 35 from the adjacent platform must be found');
 assert.ok(nearest.some(x=>x.estimatedTotalSeconds<39*60),'the nearby direct bus should beat the originally shown 39-minute transfer');
 const transfers=E.plan(data,{from,to,date,time:'13:00',maxTransfers:1,limit:5});
 assert.ok(A.reasonableDirect(nearest,transfers).length>0,'a reasonable direct option must win over a transfer');
 for(const x of nearest){
  assert.ok(x.boarding.straightMeters<=350);
  assert.ok(x.alighting.straightMeters<=500);
  assert.equal(x.trip.transfers,0);
 }
});

test('nearby candidate radius is restrictive and never fabricates an inaccessible stop',()=>{
 const from={lat:31.800,lon:34.650},to={lat:31.810,lon:34.660};
 const a={id:'a',name:'A',city:'אשדוד',code:'111',lat:31.8005,lon:34.6505};
 const b={id:'b',name:'B',city:'אשדוד',code:'222',lat:31.8095,lon:34.6595};
 const fixture={stops:{a,b},patterns:[{stops:[['a',0,0,0,0],['b',0,0,0,0]]}]};
 const planner={plan:()=>[{depart:29000,arrive:30000,transfers:0,legs:[{route:{id:'r',number:'4'},from:a,to:b,depart:29000,arrive:30000}]}]};
 assert.equal(A.plan(fixture,planner,{from,to,date:'2026-10-30',time:'08:00',maxTransfers:0,maxBoardMeters:5}).length,0);
});


test('do not prefer a very late direct bus over a much faster transfer',()=>{
 const x=[{estimatedTotalSeconds:80*60},{estimatedTotalSeconds:28*60}];
 const transfers=[{total:15*60}];
 assert.deepEqual(A.reasonableDirect(x,transfers),[{estimatedTotalSeconds:28*60}]);
 assert.equal(A.reasonableDirect([{estimatedTotalSeconds:50*60}],transfers).length,0);
});
