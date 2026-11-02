/* Runtime safeguards: cinema paints without board/editorial/network dependencies. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
(async()=>{
for(const city of ['ashdod','rishon-lezion','yavne','kiryat-gat','holon','herzliya']){
const root='events-preview/'+city+'/',source=fs.readFileSync(root+'pilot/app.js','utf8'),full=JSON.parse(fs.readFileSync(root+'data/cinema.json')),listing=JSON.parse(fs.readFileSync(root+'data/cinema-listing.json'));
assert(Buffer.byteLength(JSON.stringify(listing))<Buffer.byteLength(JSON.stringify(full)),'Listing must exclude heavy detail metadata');
const html=fs.readFileSync(root+'index.html','utf8'),inline=html.match(/window\.ISNET_CINEMA_BOOTSTRAP=([\s\S]*?);<\/script>/);assert(inline,'Inline cinema bootstrap required');assert.deepEqual(JSON.parse(inline[1]),listing,'City bootstrap must match its own feed');
assert.deepEqual(listing.movies.map(m=>m.id),full.movies.map(m=>m.id));
for(const m of listing.movies){const original=full.movies.find(x=>x.id===m.id);assert.deepEqual(m.venues.map(v=>v.schedule),original.venues.map(v=>v.schedule));assert(!m.venues.some(v=>v.sessions),'Booking session details belong on the film page');}
const start=source.indexOf('  state.cinemaLoading=true;',source.indexOf('async function init(){')),end=source.indexOf('  const sportsRequest=',start);assert(start>=0&&end>start);
const elements=new Map(),get=id=>{if(!elements.has(id))elements.set(id,{innerHTML:''});return elements.get(id)},state={cinema:[]};let draws=0,fetches=0,resolveEditorial;
const editorial=new Promise(r=>resolveEditorial=r);
vm.runInNewContext(source.slice(start,end),{state,escapeHtml:s=>String(s),$:get,location:{hash:'#cinema',search:''},URLSearchParams,window:{ISNET_CINEMA_BOOTSTRAP:listing,addEventListener(){},CinemaEditorial:{ready:editorial,unique:m=>m}},document:{querySelectorAll:()=>[]},fetch(){fetches++;throw Error('Inline feed must not require a request')},render(){throw Error('Cinema must not render the full event board')},renderCinema(){draws++},closeTrailer(){},console});
await new Promise(r=>setImmediate(r));assert.equal(fetches,0);assert.equal(state.cinemaLoading,false);assert.equal(state.cinema.length,listing.movies.length);assert.equal(draws,1);
get('cinemaFilters').onclick({target:{closest:()=>({dataset:{cinema:'cinema-city'}})}});assert.equal(state.cinemaVenue,'cinema-city');assert.equal(state.cinemaLimit,24);
resolveEditorial();await new Promise(r=>setImmediate(r));assert.equal(state.cinemaEditorialReady,true);
const renderStart=source.indexOf('function render(){'),renderEnd=source.indexOf('\nfunction bindDynamic',renderStart);
vm.runInNewContext(source.slice(renderStart,renderEnd)+';render();',{state:{cinemaOpen:true},document:{querySelectorAll(){throw Error('No board DOM work allowed in cinema')}}});
let formats=0,now=0;const dayStart=source.indexOf('const cinemaDayFormatter='),dayEnd=source.indexOf('function cinemaMovieAvailable',dayStart);
const context={Intl:{DateTimeFormat:class{format(){formats++;return '2026-11-02'}}},Date:class extends Date{static now(){return now}}};vm.createContext(context);vm.runInContext(source.slice(dayStart,dayEnd),context);
vm.runInContext('for(let i=0;i<2000;i++)cinemaToday()',context);assert.equal(formats,1,'Date formatting must be reused across cards and sort comparisons');now=2000;vm.runInContext('cinemaToday()',context);assert.equal(formats,2,'The Israel date must refresh, including across midnight');
console.log(city+': PASS: same films and schedules, compact inline listing, zero cinema fetches, no board rendering, cached calendar clock');
}
})().catch(e=>{console.error(e);process.exitCode=1});
