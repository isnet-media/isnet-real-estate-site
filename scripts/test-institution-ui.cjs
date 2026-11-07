#!/usr/bin/env node
// Safe smoke tests for shared organizer pages and lecture artwork.
const fs=require("node:fs"),assert=require("node:assert/strict");
const base="events-preview";
const load=(city,name)=>fs.readFileSync(base+"/"+city+"/"+name,"utf8");
for(const city of ["ashdod","rishon-lezion"]){
 const registry=JSON.parse(load(city,"data/institutions.json"));
 const events=JSON.parse(load(city,"data/events.json")).events;
 const operator=load(city,"operator.html"),index=load(city,"index.html");
 const ids=registry.institutions.map(x=>x.id);
 assert.equal(ids.length,new Set(ids).size);
 assert.ok(operator.includes('id="contactDetails"')&&operator.includes('id="operatorEvents"'));
 assert.ok(index.includes('id="operatorStrip"'));
 assert.ok(index.includes('operator.html?id='));
 assert.ok(operator.includes('data/institutions.json'));
 assert.ok(index.includes("איור להמחשה"),"Distinct fallback designs must be clearly labeled");
 for(const org of registry.institutions.filter(x=>x.featured)){
  const results=events.filter(e=>e.operator_id===org.id||
   (e.sources||[]).some(src=>(org.source_names||[]).includes(src.name)));
  assert.ok(results.length>0,"No source events for "+org.id);
 }
 for(const e of events)assert.ok((e.sources||[]).length,"Missing source in "+city);
}
const ash=JSON.parse(load("ashdod","data/events.json")).events;
const ofek=ash.filter(e=>e.operator_id==="ofek_ashdod");
// The calendar changes as dates expire. Verify every current occurrence from
// the last verified source snapshot, rather than a historical launch count.
const today=new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Jerusalem',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
const snapshot=JSON.parse(fs.readFileSync(base+'/admin/data/ashdod-local-snapshot.json','utf8'));
const expectedOfek=snapshot.events.filter(e=>e.local_source_name==='ofek_ashdod'&&e.start_date>=today);
assert.ok(expectedOfek.length>0,'Ofek verified future snapshot is empty; refresh the source evidence');
const ofekSourceId=e=>{
 const u=new URL(e.content_source_url||e.ticket_url);
 assert.ok(['www.ofek-ashdod.org.il','ofek-ashdod.org.il'].includes(u.hostname));
 assert.equal(u.searchParams.get('type'),'event');
 assert.match(u.searchParams.get('id')||'',/^\d+$/);
 return u.searchParams.get('id');
};
for(const expected of expectedOfek){
 const id=ofekSourceId(expected);
 assert.ok(ofek.some(e=>ofekSourceId(e)===id&&e.start_date===expected.start_date&&e.start_time===expected.start_time),
  'Missing verified Ofek occurrence '+id+' '+expected.start_date+' '+expected.start_time);
}
assert.ok(ofek.some(e=>e.category==="tour"||e.category==="seniors"&&/סיור|טיול/.test(e.title||"")),"Ofek excursions must remain identifiable as tours, including seniors events");
assert.ok(ofek.some(e=>e.category==="lecture"||e.category==="seniors"),"Ofek senior programming must remain indexed");
assert.ok(!ofek.some(e=>e.category==="workshop"||e.category==="classes"),"Workshops and classes must not be published on the event board");
for(const e of ofek){
 assert.ok(e.contact_phone,"Ofek office phone missing");
 if(e.category==="tour"&&e.venue?.includes("יציאה לסיור"))
  assert.ok(!e.address,"Do not use Ofek office as tour departure address");
}
const app=load("ashdod","app.js");
assert.ok(app.includes("lectureFallbackTopic(e)"),"Topic matching must exist");
assert.ok(app.includes('class="category-fallback lectureArtwork"'));
const details=load("ashdod","event.js");
assert.ok(details.includes("operator.html?id="),"Event detail must navigate to operator");
assert.ok(details.includes("טלפון המקום"),"Venue-specific contact must be exposed");
console.log("PASS: 2 cities, organizer pages, lecture artwork, "+ofek.length+" Ofek events, contact integrity");
