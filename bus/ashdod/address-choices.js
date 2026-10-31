/* Rank actual stop addresses, never turn a house-number difference into distance. */
(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('./engine'):root.BusEngine,typeof module==='object'&&module.exports?require('./streets'):root.BusStreets);if(typeof module==='object'&&module.exports)module.exports=api;else root.BusAddressChoices=api})(typeof globalThis==='undefined'?this:globalThis,function(E,S){
 function streetFor(query,streets){const key=S.key(query),matches=streets.filter(s=>[s.name,...s.aliases].some(a=>S.key(a)===key));return matches.length===1?matches[0]:null}
 function candidates(query,street,groups,limit=3){
  const match=String(query).trim().match(/(?:^|\s)(\d+)([א-ת]?)$/),house=match?Number(match[1]):null,keys=new Set([street.name,...street.aliases].map(S.key));
  return groups.filter(g=>g.ids.some(id=>street.stopIds.includes(id))).map(g=>{
   const number=String(g.house||g.street||'').match(/(?:^|\s)(\d+)(?:[א-ת])?$/),sameStreet=keys.has(S.key(g.street||''));
   return {...g,addressLabel:g.street||g.name,addressRank:sameStreet?0:1,numberGap:house!==null&&sameStreet&&number?Math.abs(house-Number(number[1])):Infinity};
  }).sort((a,b)=>a.addressRank-b.addressRank||a.numberGap-b.numberGap||a.name.localeCompare(b.name,'he')).slice(0,limit);
 }
 return {streetFor,candidates};
});
