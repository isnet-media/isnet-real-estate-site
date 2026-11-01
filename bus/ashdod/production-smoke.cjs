'use strict';
// Post-Pages-publication check. Never reports success based solely on the merge.
const assert=require('node:assert/strict');
const live=process.env.ISNET_BUS_LIVE_URL||'https://isnet.co.il/bus/ashdod/';
const stamp='ashdod-compact-sticky-20261101';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function fetchText(url){
 const u=new URL(url);u.searchParams.set('_verify',Date.now().toString());
 const response=await fetch(u,{headers:{'User-Agent':'ISNET-bus-release-validation/1.0','Cache-Control':'no-cache'},signal:AbortSignal.timeout(15000)});
 if(!response.ok)throw Error('HTTP '+response.status+' from '+u.origin+u.pathname);
 return response.text();
}
async function main(){
 let last;
 for(let attempt=1;attempt<=72;attempt++){
  try{
   const html=await fetchText(live);
   assert.ok(html.includes('<meta name="isnet-build" content="'+stamp+'">'),'new build marker not deployed');
   const app=await fetchText(new URL('app.js',live).href);
   assert.ok(app.includes("mode==='intercity'&&!routes.length"),'direct-first app.js is not present');
   const engine=await fetchText(new URL('engine.js',live).href);
   assert.ok(engine.includes('aDirect'),'direct-first engine.js is not present');
   const approximate=await fetchText(new URL('approximate.js',live).href);
   assert.ok(approximate.includes('maxBoardMeters'),'nearby route candidate filtering not deployed');
   const data=JSON.parse(await fetchText(new URL('data/network.json',live).href));
   assert.ok(data.stops&&data.patterns&&data.trips,'the public GTFS file is invalid or missing');
   const now=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Jerusalem',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date()).replaceAll('-','');
   assert.ok(data.valid_from<=now&&data.valid_until>=now,'the public GTFS schedule is stale');
   assert.ok(html.includes('id="locateText"'),'visible location button missing');
   const share=await fetchText(new URL('navigation-share.js',live).href);
   assert.ok(share.includes('https://wa.me/')&&share.includes('חזרה לאשדוד נט'),'rich sharing/navigation missing');
   const image=await fetch(new URL('share-card.jpg',live),{signal:AbortSignal.timeout(15000)});
   assert.ok(image.ok&&image.headers.get('content-type')?.includes('image/jpeg'),'share preview image missing');
   const addressChoices=await fetchText(new URL('address-choices.js',live).href);
   assert.ok(addressChoices.includes('numberGap'),'address selection helper missing');
   const streets=JSON.parse(await fetchText(new URL('data/ashdod-streets.json',live).href));
   assert.ok(streets.streets.length>=700,'official Ashdod street index missing');
   const rail=JSON.parse(await fetchText(new URL('data/rail.json',live).href));
   assert.ok(rail.mode==='rail'&&rail.ashdod_origin_ids.length&&rail.valid_from<=now&&rail.valid_until>=now,'rail timetable invalid or stale');
   console.log('LIVE_PUBLICATION_VERIFIED '+live+' build='+stamp+' feed='+data.generated_at+' stops='+Object.keys(data.stops).length);
   return;
  }catch(error){
   last=error;
   console.log('Attempt '+attempt+'/72: '+error.message);
   if(attempt<72)await sleep(10000);
  }
 }
 throw Error('Live site could not be verified after Pages publication: '+(last&&last.message));
}
main().catch(error=>{console.error(error);process.exitCode=1});
