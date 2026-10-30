// ISNET private routing gateway (Node 20+). Deploy behind a same-origin reverse proxy.
// Required: NOMINATIM_URL, VALHALLA_URL, ALLOWED_ORIGIN. No third-party demo servers.
'use strict';
const http=require('node:http');
const NOMINATIM=process.env.NOMINATIM_URL,VALHALLA=process.env.VALHALLA_URL;
const PORT=Number(process.env.PORT||8787);
const ALLOWED_ORIGIN=process.env.ALLOWED_ORIGIN;
const MAX_BODY=2048,MAX_PER_MIN=30,counts=new Map();
function json(res,status,data){res.writeHead(status,{'content-type':'application/json; charset=utf-8','cache-control':'no-store','x-content-type-options':'nosniff'});res.end(JSON.stringify(data))}
function validPoint(p){return p&&typeof p.lat==='number'&&Number.isFinite(p.lat)&&Math.abs(p.lat)<=90&&typeof p.lon==='number'&&Number.isFinite(p.lon)&&Math.abs(p.lon)<=180}
function decodePolyline6(s){let i=0,lat=0,lon=0,out=[];while(i<s.length){const read=()=>{let shift=0,result=0,b;do{if(i>=s.length)throw Error('Invalid polyline');b=s.charCodeAt(i++)-63;result|=(b&31)<<shift;shift+=5;if(shift>35)throw Error('Invalid polyline')}while(b>=32);return(result&1)?~(result>>1):(result>>1)};lat+=read();lon+=read();out.push({lat:lat/1e6,lon:lon/1e6});if(out.length>10000)throw Error('Too many points')}return out}
async function upstream(url,options={}){const c=new AbortController(),t=setTimeout(()=>c.abort(),8000);try{const r=await fetch(url,{...options,signal:c.signal});if(!r.ok)throw Error('Upstream '+r.status);return await r.json()}finally{clearTimeout(t)}}
function addressQuery(q){const t=q.replace(/\s+/g,' ').trim();if(t.length<5||t.length>160||!/[0-9]/.test(t))throw Error('Address with house number required');return t}
function parseGeocode(items,q){const requested=(q.match(/(?:^|\\s)(\\d+[א-ת]?)(?=\\s|$)/)||[])[1];return items.filter(x=>x&&x.lat&&x.lon&&x.address&&x.address.house_number&&
  (x.address.city==='אשדוד'||x.address.town==='אשדוד'||x.address.municipality==='אשדוד')&&String(x.address.house_number).replace(/\\s/g,'')===requested)
 .map(x=>({label:x.display_name,lat:Number(x.lat),lon:Number(x.lon),precision:'address',
 confidence:0.9,source:'OpenStreetMap / Nominatim',houseNumber:x.address.house_number}))
 .filter(x=>validPoint(x));}
async function handle(req,res){
 if(!NOMINATIM||!VALHALLA||!ALLOWED_ORIGIN)return json(res,503,{error:'Providers not configured'});
 const origin=req.headers.origin;if(origin&&origin!==ALLOWED_ORIGIN)return json(res,403,{error:'Origin denied'});
 const ip=(req.socket.remoteAddress||'unknown'),minute=Math.floor(Date.now()/60000),key=ip+':'+minute;
 if(counts.size>5000)counts.clear();const n=(counts.get(key)||0)+1;counts.set(key,n);
 if(n>MAX_PER_MIN)return json(res,429,{error:'Rate limit exceeded'});
 const url=new URL(req.url,'http://localhost');
 if(req.method==='GET'&&url.pathname==='/api/bus/health')return json(res,200,{configured:true,live:false});
 if(req.method==='GET'&&url.pathname==='/api/bus/geocode'){
  const q=addressQuery(url.searchParams.get('q')||'');
  const upstreamUrl=new URL('/search',NOMINATIM);upstreamUrl.searchParams.set('q',q+', אשדוד, ישראל');upstreamUrl.searchParams.set('format','jsonv2');upstreamUrl.searchParams.set('addressdetails','1');upstreamUrl.searchParams.set('countrycodes','il');upstreamUrl.searchParams.set('limit','5');
  return json(res,200,{results:parseGeocode(await upstream(upstreamUrl),q)});
 }
 if(req.method==='POST'&&url.pathname==='/api/bus/walk-route'){
  const chunks=[];let size=0;for await(const chunk of req){size+=chunk.length;if(size>MAX_BODY)return json(res,413,{error:'Payload too large'});chunks.push(chunk)}
  const body=JSON.parse(Buffer.concat(chunks).toString('utf8'));if(!validPoint(body.from)||!validPoint(body.to))return json(res,400,{error:'Invalid coordinates'});
  const v=new URL('/route',VALHALLA);v.searchParams.set('json',JSON.stringify({locations:[body.from,body.to],costing:'pedestrian',units:'kilometers'}));
  const response=await upstream(v);const leg=response.trip?.legs?.[0],summary=response.trip?.summary;
  if(!leg?.shape||!summary||!Number.isFinite(summary.length)||!Number.isFinite(summary.time))throw Error('No verified walking route');
  const geometry=decodePolyline6(leg.shape);if(geometry.length<2)throw Error('Missing walking geometry');
  return json(res,200,{mode:'walking',verified:true,distanceMeters:Math.round(summary.length*1000),durationSeconds:Math.ceil(summary.time),geometry,source:'Valhalla / OpenStreetMap'});
 }
 return json(res,404,{error:'Not found'});
}
const server=http.createServer((req,res)=>{handle(req,res).catch(e=>json(res,e.message==='Address with house number required'?400:502,{error:e.message==='Address with house number required'?e.message:'Routing service unavailable'}))});
if(require.main===module)server.listen(PORT,process.env.BIND_HOST||'127.0.0.1',()=>console.log('ISNET bus gateway listening on loopback',PORT));
module.exports={validPoint,decodePolyline6,parseGeocode,server};
