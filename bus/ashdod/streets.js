/* Official names are searchable even when no GTFS stop can be assigned safely. */
(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('./engine.js'):root.BusEngine);if(typeof module==='object'&&module.exports)module.exports=api;else root.BusStreets=api})(typeof globalThis==='undefined'?this:globalThis,function(E){
 const key=s=>E.searchTerms(s).filter(t=>!/^\d+[א-ת]?$/.test(t)).map(E.norm).sort().join('|');
 function choices(source,groups){
  const stopIndex=new Map();
  for(const g of groups){if(g.city!=='אשדוד')continue;for(const name of [g.street,...g.name.split('/')]){if(!name)continue;const k=key(name);if(!stopIndex.has(k))stopIndex.set(k,new Set());for(const id of g.ids)stopIndex.get(k).add(id)}}
  return source.streets.map(s=>{
   const aliases=[s.name,...s.aliases],stopIds=new Set();
   for(const name of aliases)for(const id of stopIndex.get(key(name))||[])stopIds.add(id);
   return {kind:'street',id:'street:'+s.cityCode+':'+s.streetCode,streetCode:s.streetCode,name:s.name,city:'אשדוד',ids:[],stopIds:[...stopIds],aliases:s.aliases,search:aliases.join(' '),verifiedCoordinates:false};
  });
 }
 function audit(source,groups){const list=choices(source,groups),linked=list.filter(x=>x.stopIds.length);return {officialStreets:list.length,aliases:source.streets.reduce((n,s)=>n+s.aliases.length,0),withNamedStops:linked.length,withoutNamedStops:list.length-linked.length,sourceUpdatedAt:source.source_updated_at,unmatched:list.filter(x=>!x.stopIds.length).map(x=>({streetCode:x.streetCode,name:x.name}))}}
 return {choices,audit,key};
});
