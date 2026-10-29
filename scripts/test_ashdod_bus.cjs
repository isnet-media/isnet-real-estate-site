const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),E=require('../bus/ashdod/engine.js');
const data=JSON.parse(fs.readFileSync(__dirname+'/../bus/ashdod/data/network.json'));
let realDate=data.valid_from.slice(0,4)+'-'+data.valid_from.slice(4,6)+'-'+data.valid_from.slice(6);while([5,6].includes(new Date(realDate+'T12:00:00Z').getUTCDay()))realDate=E.dayShift(realDate,1);
function fixture(){return {stops:{a:{id:'a',code:'1',name:'א',city:'אשדוד',lat:31.8,lon:34.6},b:{id:'b',code:'2',name:'ב',city:'אשדוד',lat:31.8,lon:34.61},c:{id:'c',code:'3',name:'ג',city:'תל אביב יפו',lat:32,lon:34.7},d:{id:'d',code:'4',name:'ד',city:'תל אביב יפו',lat:32.01,lon:34.71}},routes:{r:{id:'r',number:'1',operator:'מפעיל'},s:{id:'s',number:'2',operator:'מפעיל'}},services:{all:{start:'20261029',end:'20261128',days:[1,1,1,1,1,1,1]}},patterns:[{route:'r',headsign:'ב',stops:[['a',0,0,0,1],['b',600,600,1,0]]},{route:'s',headsign:'ד',stops:[['b',0,0,0,1],['c',600,600,0,0],['d',900,900,1,0]]}],trips:[[0,'all',28800],[1,'all',29600]]}}
const at=(d,from,to,extra={})=>E.plan(d,{from:{id:from},to:{id:to},date:'2026-10-29',time:'07:59',...extra});
test('direct city journey respects boarding and alighting',()=>{const r=at(fixture(),'a','b');assert.equal(r[0].duration,600);assert.equal(r[0].wait,60);assert.equal(r[0].transfers,0)});
test('one transfer with a two minute margin',()=>{const r=at(fixture(),'a','c');assert.equal(r[0].transfers,1);assert.equal(r[0].arrive,30200)});
test('missed connection is not proposed',()=>{const d=fixture();d.trips[1][2]=29460;assert.equal(at(d,'a','c').length,0)});
test('direct-only mode excludes transfers',()=>assert.equal(at(fixture(),'a','c',{maxTransfers:0}).length,0));
test('dropoff-only stop cannot be used to board',()=>assert.equal(at(fixture(),'b','a').length,0));
test('pickup-only stop cannot be a destination',()=>{const d=fixture();d.patterns[1].stops[1][4]=1;assert.equal(at(d,'a','c').length,0)});
test('calendar weekday restrictions apply',()=>{const d=fixture();d.services.all.days[4]=0;assert.equal(at(d,'a','b').length,0)});
test('expired service is excluded',()=>{const d=fixture();d.services.all.end='20261028';assert.equal(at(d,'a','b').length,0)});
test('past departure is excluded',()=>assert.equal(at(fixture(),'a','b',{time:'08:01',date:'2026-11-28'}).length,0));
test('previous service day after midnight',()=>{const d=fixture();d.trips[0][2]=25*3600;const r=at(d,'a','b',{date:'2026-10-30',time:'00:50'});assert.equal(r[0].depart,3600)});
test('next day departure is supported near midnight',()=>{const d=fixture();d.trips[0][2]=600;const r=at(d,'a','b',{time:'23:50'});assert.equal(r[0].depart,87000)});
test('physical stop aliases work without inventing a walking transfer',()=>{const d=fixture();d.stops.b2={...d.stops.b,id:'b2'};d.patterns[1].stops[0][0]='b2';assert.equal(at(d,'a','c')[0].transfers,1)});
test('city target ends at last served stop within the selected city',()=>{const r=at(fixture(),'a',null,{to:{kind:'city',city:'תל אביב יפו'}});assert.equal(r[0].legs.at(-1).to.id,'d')});
test('real feed has valid references and monotonic stop times',()=>{assert.ok(data.local_stop_ids.length>300);assert.ok(data.patterns.length>100);for(const p of data.patterns){assert.ok(data.routes[p.route]);let last=-Infinity;for(const [sid,arr,dep,pick,drop] of p.stops){assert.ok(data.stops[sid]);assert.ok(arr>=last);assert.ok(dep>=arr);assert.ok([0,1,2,3].includes(pick));assert.ok([0,1,2,3].includes(drop));last=dep}}for(const [p,s,t] of data.trips){assert.ok(data.patterns[p]);assert.ok(data.services[s]);assert.ok(Number.isInteger(t))}});
test('real intracity journey exists',()=>{const groups=E.groups(data),from=groups.find(s=>s.code==='11856'),to=groups.find(s=>s.code==='12784');assert.ok(E.plan(data,{from,to,date:realDate,time:'08:00'}).some(r=>r.legs[0].route.number==='1'&&r.transfers===0))});
test('real intercity journey reaches Tel Aviv',()=>{const from=E.groups(data).find(s=>s.code==='11856'),rs=E.plan(data,{from,to:{kind:'city',city:'תל אביב יפו'},date:realDate,time:'08:00'});assert.ok(rs.length);assert.ok(rs.every(r=>r.legs.at(-1).to.city==='תל אביב יפו'))});
test('distance calculation and name normalization',()=>{assert.equal(E.distance({lat:31.8,lon:34.6},{lat:31.8,lon:34.6}),0);assert.equal(E.norm('רובע א׳'),'רובעא')});

test('later feeder avoids unnecessary waiting at the transfer stop',()=>{const d=fixture();d.trips.push([0,'all',30000]);d.trips[1][2]=31200;const r=at(d,'a','c');assert.equal(r[0].depart,30000);assert.equal(r[0].arrive,31800)});
test('a direct ride dominates an earlier feeder with the same arrival',()=>{const d=fixture();d.patterns.push({route:'r',headsign:'ג',stops:[['a',0,0,0,1],['c',600,600,1,0]]});d.trips.push([2,'all',29600]);const r=at(d,'a','c');assert.equal(r[0].transfers,0);assert.ok(!r.some(x=>x.transfers&&x.arrive===30200))});
