const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
async function check(city,fail){
 const source=fs.readFileSync(`events-preview/${city}/pilot/app.js`,'utf8');
 const start=source.indexOf('async function init(){'),end=source.indexOf('  const searchInput=$("searchInput");',start);
 const code=source.slice(start,end)+'}\ninit();';
 let cinemaResolve,sportsResolve;
 const cinema=new Promise(resolve=>cinemaResolve=resolve),sports=new Promise(resolve=>sportsResolve=resolve);
 let rendered=0,cinemaRendered=0,sportsRendered=0;
 const state={},window={addEventListener(){},ISNET_PUBLIC_CMS:{loadCards:async()=>({events:[{event_id:'one',title:'אירוע'}]}),publishedEvents:async actual=>{assert.equal(actual,city,'CMS must belong to current city');return []}}};
 const context={window,state,$:()=>({}),document:{querySelectorAll:()=>[]},closeTrailer(){},location:{pathname:`/events-preview/${city}/`,search:'',hash:''},URLSearchParams,catLabels:{},sharedSaved:null,iso:()=>'',today:()=>'',publishedBoardEvents:rows=>rows,render:()=>rendered++,renderCinema:()=>cinemaRendered++,renderSportsFilters:()=>sportsRendered++,fetch:address=>{
  if(address.includes('cinema.json'))return cinema;
  if(address.includes('sports.json'))return sports;
  return Promise.resolve({json:async()=>address.includes('taxonomy')?{primary_categories:[]}: {}});
 }};
 await vm.runInNewContext(code,context);
 assert.equal(rendered,1,'Initial event list renders before cinema/sports resolve');
 assert.equal(state.events.length,1);assert.equal(state.cinemaLoading,true);
 cinemaResolve({ok:!fail,json:async()=>({movies:[{id:'film'}]})});
 sportsResolve({ok:!fail,json:async()=>({teams:[{id:'team'}]})});
 await new Promise(resolve=>setImmediate(resolve));
 assert.equal(state.cinemaLoading,false);assert.equal(state.cinema.length,fail?0:1);
 assert.equal(state.sportsMeta.teams.length,fail?0:1);assert.equal(rendered,2);assert.equal(cinemaRendered,2);assert.equal(sportsRendered,1);
}
(async()=>{for(const city of ['ashdod','rishon-lezion','yavne'])for(const fail of [false,true])await check(city,fail);console.log('PASS: event list renders independently of delayed cinema/sports; successful and failed responses recover; correct city CMS');})().catch(e=>{console.error(e);process.exitCode=1});
