// Official Smarticket occurrences 17756 and 17982, checked 6 November 2026.
// Correct only the reviewed source spelling/address; preserve old detail IDs.
const assert=require('node:assert/strict'),fs=require('node:fs');
const q=require('../events-preview/shared/event-overlay.js').integrity;
const registry=JSON.parse(fs.readFileSync('events-preview/shared/data/event-quality-media.json','utf8'));
q.setFactRegistry(registry.fact_repairs);
for(const id of ['makore_as_e349c7d2119c6764c4','makore_as_51e3db1c7140e29eb5']){
 const repair=registry.fact_repairs[id];
 assert(repair,'Reviewed correction missing: '+id);
 const old={...repair.match,event_id:id,category:'lecture'};
 const official={...old,...repair.fields,event_id:id+'-official'};
 const result=q.reconcile([old,official]);
 assert.equal(result.length,1);
 assert(q.resolve([old,official],id));
 assert(q.resolve([old,official],official.event_id));
 assert.equal(result[0].start_date,old.start_date);
 assert.equal(result[0].start_time,old.start_time);
 for(const [key,value] of Object.entries(repair.fields)){
  assert.equal(q.sanitize(old)[key],value);
  assert.equal(q.sanitize({...old,locked_fields:[key]})[key],old[key]);
  assert.equal(q.sanitize({...old,human_manual_override:true})[key],old[key]);
 }
 for(const changed of [{start_date:'2099-11-10'},{start_time:'23:00'},{venue:'אולם אחר'}]){
  const separate={...official,...changed};
  assert.equal(q.reconcile([old,separate]).length,2,'Different occurrence must remain separate');
  const unmatched={...old,...changed};
  for(const key of Object.keys(repair.fields))assert.equal(q.sanitize(unmatched)[key],unmatched[key]);
 }
}
console.log('PASS: two verified Ashdod lectures, exact match guards, dates/venues, editor locks and old IDs');
