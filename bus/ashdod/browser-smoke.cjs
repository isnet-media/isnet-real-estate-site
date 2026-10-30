'use strict';
/**
 * Browser regression for an actual Ashdod-quarter to rail trip using the
 * bundled dated GTFS snapshot. No external tile requests; local Leaflet.
 */
const assert=require('node:assert/strict');
const http=require('node:http');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'../..');
const dir=path.join(__dirname,'screenshots');
const leaflet=path.join(root,'node_modules','leaflet','dist');
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.svg':'image/svg+xml','.png':'image/png'};
const image=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScL/nwAAAABJRU5ErkJggg==','base64');
async function main(){
 const server=http.createServer((req,res)=>{
  const pathname=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname);
  const relative=pathname.endsWith('/')?pathname+'index.html':pathname;
  const file=path.resolve(root,'.'+relative);
  if(!file.startsWith(root+path.sep)){res.writeHead(403);res.end();return}
  fs.stat(file,(err,info)=>{
   if(err||!info.isFile()){res.writeHead(404);res.end();return}
   res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream'});
   fs.createReadStream(file).pipe(res);
  });
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const port=server.address().port;
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const url=new URL('http://127.0.0.1:'+port+'/bus/ashdod/');
 Object.entries({from:'11931',to:'place:ashdod-rail',date:'2026-10-30',time:'13:00',mode:'local',target_kind:'place',transfer:'0'}).forEach(([k,v])=>url.searchParams.set(k,v));
 fs.mkdirSync(dir,{recursive:true});
 try{
  for(const [label,size] of [['mobile',{width:390,height:844}],['desktop',{width:1365,height:768}]]){
   const ctx=await browser.newContext({viewport:size,locale:'he-IL',timezoneId:'Asia/Jerusalem'});
   const page=await ctx.newPage();
   await page.addInitScript(()=>{
    const RealDate=Date, fixed=RealDate.parse('2026-10-30T11:00:00Z');
    class FixedDate extends RealDate{
      constructor(...a){super(...(a.length?a:[fixed]))}
      static now(){return fixed}
    }
    window.Date=FixedDate;
   });
   await page.route('https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',r=>r.fulfill({path:path.join(leaflet,'leaflet.js'),contentType:'text/javascript'}));
   await page.route('https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',r=>r.fulfill({path:path.join(leaflet,'leaflet.css'),contentType:'text/css'}));
   await page.route('https://tile.openstreetmap.org/**',r=>r.fulfill({status:200,body:image,contentType:'image/png'}));
   await page.goto(url.href,{waitUntil:'load',timeout:30000});
   await page.locator('#results .route-card').first().waitFor({state:'visible',timeout:30000});
   const eyebrow=(await page.locator('#resultEyebrow').innerText()).trim();
   assert.equal(eyebrow,'קו ישיר מתחנה סמוכה',label+': direct bus fallback missing');
   const badges=await page.locator('#results .route-card .badge').allInnerTexts();
   assert.ok(badges.length>0,label+': missing bus results');
   assert.ok(badges.every(t=>t==='ללא החלפה'),label+': bus transfers incorrectly prioritized');
   const lines=await page.locator('#results .route-card .line-pill').allInnerTexts();
   assert.ok(lines.includes('35'),label+': nearby direct line 35 missing');
   const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth);
   assert.ok(overflow<=2,label+': horizontal overflow '+overflow+'px');
   const button=page.locator('#results .route-card').first().getByRole('button',{name:'הצג תחנות על מפה'});
   await button.click();
   const panel=page.locator('#results .route-card .stop-map').first();
   assert.equal(await panel.isHidden(),false,label+': stops map not visible');
   await panel.locator('.leaflet-container').waitFor({state:'visible',timeout:10000}).catch(()=>{});
   const mapExists=await page.evaluate(()=>!!document.querySelector('#results .route-card .stop-map .leaflet-pane'));
   assert.ok(mapExists,label+': Leaflet map failed to render');
   await page.screenshot({path:path.join(dir,label+'.png'),fullPage:true});
   console.log('PASS '+label+': direct routing, map, RTL and no horizontal overflow ('+badges.length+' options)');
   await ctx.close();
  }
 }finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
}
main().catch(e=>{console.error(e);process.exitCode=1});
