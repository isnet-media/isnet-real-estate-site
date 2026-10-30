const test=require('node:test');
const assert=require('node:assert/strict');
const A=require('./approximate.js');
const origin={lat:31.800,lon:34.650},destination={lat:31.810,lon:34.660};
const a={id:'a',name:'A',city:'אשדוד',code:'111',lat:31.8005,lon:34.6505};
const b={id:'b',name:'B',city:'אשדוד',code:'222',lat:31.8095,lon:34.6595};
const data={stops:{a,b},patterns:[{stops:[['a',0,0,0,0],['b',0,0,0,0]]}]};
const engine={plan:(_,{from,to,time})=>from.id==='a'&&to.id==='b'&&time==='08:05'?[{depart:29400,arrive:30300,transfers:0,legs:[{route:{id:'r',number:'4'},from:a,to:b,depart:29400}]}]:[]};
test('approximate candidate distances explicitly use straight-line values',()=>{
 const r=A.nearest([a],origin);assert.equal(r.length,1);
 assert.ok(r[0].straightMeters>0);assert.match(r[0].warning,/קו אווירי/);
});
test('scheduled route includes conservative walking estimate, without claiming realtime',()=>{
 const r=A.plan(data,engine,{from:origin,to:destination,date:'2026-10-30',time:'08:00'});
 assert.equal(r.length,1);assert.equal(r[0].approximation,true);assert.equal(r[0].live,false);
 assert.ok(r[0].estimatedTotalSeconds>r[0].trip.arrive-r[0].trip.depart);
});
test('no route returns empty array rather than fabricated journey',()=>{
 assert.deepEqual(A.plan(data,{plan:()=>[]},{from:origin,to:destination,date:'2026-10-30',time:'08:00'}),[]);
});
