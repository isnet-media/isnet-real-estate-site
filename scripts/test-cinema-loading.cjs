const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
(async()=>{
for(const city of ['ashdod','rishon-lezion','yavne']){
 const source=fs.readFileSync(`events-preview/${city}/pilot/app.js`,'utf8');
 const start=source.indexOf('  state.cinemaLoading=true;',source.indexOf('async function init(){'));
 const end=source.indexOf('  const sportsRequest=',start);
 let resolveFeed,resolveEditorial;const feed=new Promise(r=>resolveFeed=r),editorial=new Promise(r=>resolveEditorial=r);
 const elements=new Map(),get=id=>{if(!elements.has(id))elements.set(id,{});return elements.get(id)};
 const state={cinema:[]};let draws=0;
 vm.runInNewContext(source.slice(start,end),{state,$:get,location:{hash:'#cinema',search:''},URLSearchParams,window:{addEventListener(){},CinemaEditorial:{ready:editorial,unique:films=>films}},document:{querySelectorAll:()=>[]},fetch:()=>feed,renderCinema(){draws++},render(){throw Error('Event board must not block cinema')},closeTrailer(){},console});
 assert.equal(typeof get('cinemaSearch').oninput,'function');
 assert.equal(typeof get('cinemaFilters').onclick,'function');
 resolveFeed({ok:true,json:async()=>({movies:[{id:'test'}]})});
 await new Promise(r=>setImmediate(r));
 assert.equal(state.cinemaLoading,false);assert.equal(state.cinema.length,1);assert.equal(draws,1);
 get('cinemaSearch').oninput({target:{value:'קומדיה'}});assert.equal(state.cinemaQuery,'קומדיה');
 resolveEditorial();await new Promise(r=>setImmediate(r));assert(draws>=3);
 const html=fs.readFileSync(`events-preview/${city}/index.html`,'utf8');assert(html.includes('בטעינה - כבר עולים'));assert(!html.includes('מכינים לכם ערב של קולנוע'));
}
console.log('PASS: cinema renders and filters work while event/CMS and editorial requests are unresolved, in all three cities');
})().catch(e=>{console.error(e);process.exitCode=1});
