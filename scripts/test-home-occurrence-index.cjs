const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
for(const city of ['ashdod','rishon-lezion','yavne','kiryat-gat','holon','herzliya']){
 const root='events-preview/'+city+'/',source=fs.readFileSync(root+'pilot/app.js','utf8');
 assert(fs.readFileSync(root+'index.html','utf8').includes('id="homeLoading" class="homeLoading" role="status" aria-live="polite">תכף עולים האירועים'));
 const start=source.indexOf('let occurrenceIndexEvents='),end=source.indexOf('function isPersistentExhibition',start);assert(start>=0&&end>start);
 const events=Array.from({length:2000},(_,i)=>({event_id:String(i),title:'מופע '+Math.floor(i/2),venue:i%4<2?'אולם א':'אולם ב',start_date:i%2?'2026-12-01':'2026-12-02',start_time:'20:00'}));
 let calls=0;const state={events,sportsMeta:{}},context={state,eventGroupKey:e=>{calls++;return e.title+'|'+e.venue},Array,Map};vm.createContext(context);vm.runInContext(source.slice(start,end),context);
 for(let round=0;round<2;round++)for(const e of events){const group=context.eventOccurrences(e);assert.equal(group.length,2);assert.equal(group[0].start_date,'2026-12-01');assert(group.every(x=>x.venue===e.venue));}
 assert(calls<=6000,'Index must avoid rescanning 2000 events per card');
 const extra={...events[0],event_id:'new',start_date:'2026-12-03'};state.events=[...events,extra];assert.equal(context.eventOccurrences(extra).length,3,'CMS/full-search replacement must invalidate cache');
 const before=calls;state.sportsMeta={updated:true};context.eventOccurrences(extra);assert(calls>before+2000,'Team metadata changes must invalidate sports grouping');
 assert.deepEqual(context.eventOccurrences({_occurrences:[extra]}),[extra]);
 console.log(city+': PASS loading copy in initial HTML; indexed, date-sorted, venue-safe occurrences; dataset and team invalidation');
}
