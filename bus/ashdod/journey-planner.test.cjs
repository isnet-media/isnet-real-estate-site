const assert=require('node:assert/strict');
const test=require('node:test');
const P=require('./journey-planner.js');
const origin={lat:31.800,lon:34.650},destination={lat:31.810,lon:34.660};
const a={id:'a',name:'A',city:'אשדוד',code:'111',lat:31.8005,lon:34.6505};
const b={id:'b',name:'B',city:'אשדוד',code:'222',lat:31.8095,lon:34.6595};
const walk=(from,to)=>({mode:'walking',verified:true,distanceMeters:100,durationSeconds:120,geometry:[from,to]});
const provider={
 async geocode(q){return [{...((q==='origin address')?origin:destination),label:q,precision:'address',confidence:0.95,source:'test'}]},
 async walk(from,to){return walk(from,to)}
};
const data={stops:{a,b},patterns:[{stops:[['a',0,0,0,0],['b',0,0,0,0]]}]};
const engine={plan:(_data,{from,to,time})=>from.id==='a'&&to.id==='b'&&time==='08:04'?[{depart:8*3600+10*60,arrive:8*3600+25*60,transfers:0,legs:[{route:{id:'r',number:'4'},from:a,to:b,depart:8*3600+10*60}]}]:[]};
test('reject ambiguous or street-only geocoding',async()=>{
 await assert.rejects(P.address({geocode:async()=>[{...origin,precision:'street',confidence:1,source:'test'}]},'long address'));
 await assert.rejects(P.address({geocode:async()=>[{...origin,precision:'address',confidence:1,source:'test'},{...destination,precision:'address',confidence:1,source:'test'}]},'long address'));
});
test('include both walking legs in end-to-end time',async()=>{
 const x=await P.plan({data,engine,provider,fromText:'origin address',toText:'target address',date:'2026-10-30',time:'08:00'});
 assert.equal(x.routes.length,1);
 assert.equal(x.routes[0].totalSeconds,27*60);
 assert.equal(x.routes[0].scheduledOnly,true);
});
test('destination walking route is requested in correct direction',async()=>{
 const calls=[];const x=await P.plan({data,engine,provider:{...provider,walk:async(f,t)=>{calls.push([f,t]);return walk(f,t)}},fromText:'origin address',toText:'target address',date:'2026-10-30',time:'08:00'});
 assert.equal(x.routes.length,1);
 assert.ok(calls.some(([f,t])=>f.id==='b'&&t.label==='target address'));
});
test('missing pedestrian paths do not generate fabricated journeys',async()=>{
 const x=await P.plan({data,engine,provider:{...provider,walk:async()=>{throw Error('No footpath')}},fromText:'origin address',toText:'target address',date:'2026-10-30',time:'08:00'});
 assert.equal(x.routes.length,0);
});
