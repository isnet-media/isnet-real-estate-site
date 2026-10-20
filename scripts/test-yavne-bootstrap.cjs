const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('events-preview/yavne/index.html','utf8');
const data=JSON.parse(html.match(/window.ISNET_CITY_BOOTSTRAP=(.*?);<\/script>/)[1]);
const js=fs.readFileSync('events-preview/yavne/pilot/app.js','utf8');
const block=js.slice(js.indexOf('const [data,fallbacks,taxonomy,cmsRows]=await Promise.all(')).split(']);')[0]+']);';
const unavailable=()=>{throw Error('Initial listing must not depend on CMS/network availability')};
const context={window:{ISNET_CITY_BOOTSTRAP:data,ISNET_PUBLIC_CMS:{loadCards:unavailable,publishedEvents:unavailable}},fetch:()=>new Promise(()=>{}),Promise};
Promise.race([vm.runInNewContext('(async()=>{'+block+'return {events:data.events,taxonomy,cmsRows}})()',context),new Promise((_,reject)=>setTimeout(()=>reject(Error('Initial listing stalled')),200))]).then(result=>{
 assert(result.events.length>0);assert(result.taxonomy.primary_categories.length>0);assert.equal(result.cmsRows.length,0);
 assert(!html.includes('window.ISNET_CITY_BOOTSTRAP=undefined'));
 console.log('Yavne event snapshot renders without JSON/CMS requests:',result.events.length,'events');
}).catch(error=>{console.error(error);process.exitCode=1});
