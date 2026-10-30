/* API adapter. All requests use same-origin server endpoints; no provider keys in browser.
 * Requires a deployed, rate-limited API implementing DOOR_TO_DOOR.md.
 */
(function(root,factory){
 const api=factory();
 if(typeof module==='object'&&module.exports)module.exports=api;
 else root.BusProvider=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const timeout=10000;
 async function request(path,init={}){
   const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),timeout);
   try{
     const response=await fetch(path,{...init,signal:controller.signal,headers:{'Accept':'application/json',...(init.headers||{})},credentials:'same-origin'});
     if(!response.ok)throw Error('Provider unavailable ('+response.status+')');
     const data=await response.json();
     if(!data||typeof data!=='object')throw Error('Invalid provider response');
     return data;
   }finally{clearTimeout(timer)}
 }
 function create(base='/api/bus'){
   if(!/^\/(?!\/)[\w/-]+$/.test(base))throw Error('API must be same-origin');
   return {
     async geocode(q){
       const data=await request(base+'/geocode?q='+encodeURIComponent(q)+'&city='+encodeURIComponent('אשדוד'));
       if(!Array.isArray(data.results))throw Error('Invalid geocode results');
       return data.results;
     },
     async walk(from,to){
       return request(base+'/walk-route',{method:'POST',headers:{'Content-Type':'application/json'},
         body:JSON.stringify({from:{lat:from.lat,lon:from.lon},to:{lat:to.lat,lon:to.lon}})});
     },
     async health(){return request(base+'/health')}
   };
 }
 return {create};
});
