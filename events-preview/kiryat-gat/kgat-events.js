/* City-owned published snapshot; no dependency on another city's CMS edition. */
(()=>{
const snapshot=window.ISNET_CITY_BOOTSTRAP;
const request=(name)=>fetch('data/'+name+'.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('Event feed unavailable');return r.json()});
const data=()=>snapshot?Promise.resolve(snapshot):request('events');
window.ISNET_PUBLIC_CMS={loadSource:data,loadCards:data,loadHub:data,publishedEvents:()=>Promise.resolve([]),metrics:{}};
window.KGAT_EVENTS={matches:(e,ids)=>ids.has(e.category)||(e.category_memberships||[]).some(x=>ids.has(x.category))||(ids.has('seniors')&&(e.audiences||[]).includes('seniors'))||(ids.has('kids')&&(e.audiences||[]).includes('kids'))};
})();
