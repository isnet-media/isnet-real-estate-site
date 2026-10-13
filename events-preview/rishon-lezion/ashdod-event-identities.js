// ISNET shared layout: edit events-preview/ashdod, not this generated file.
/* Verified Ashdod event identity aliases. Raw source records remain unchanged. */
(()=>{
 const series="ashdod-comedy-bar-hot-cinema";
 const title="כוכבי הקומדי בר — מרתון סטנדאפ";
 const known=new Set(["mevalim_as_131599","friends_as_9181c7cdf53edb94fa","friends_as_cab289dedf10fa4c60","makore_as_91fb472ae5344d1b11"]);
 function identity(e){
   const t=String(e?.title||"").normalize("NFKC").replace(/\s+/g," ").trim();
   const venue=String(e?.venue||"");
   const city=String(e?.city||"");
   const named=/^(?:כוכבי הקומדי בר מגיעים למרתון סטנדאפ(?: ראשון לציון(?: \d{1,2}\.\d{1,2}\.\d{2,4})?)?|קומדי\s*בר\s*[-–—]?\s*סטנדאפ)$/.test(t);
   const hall=/הוט\s*סינמה|hot\s*cinema/i.test(venue)&&!/אולם\s*[013-9]/.test(venue);
   return (known.has(e?.event_id)||named)&&e?.category==="standup"&&city==="ראשון לציון"&&hall&&e.start_date&&e.start_time?series:null;
 }
 function priority(e){
   return (typeof e.price_min_ils==="number"?0:100)+(Number(e.source_priority)||50);
 }
 function sourceOffer(e){
   const url=e.purchase_url||e.ticket_url;
   if(!/^https:\/\//.test(url||""))return null;
   const name=e.source==="mevalim_direct"?"מבלים":e.source==="supplemental_friends"?"FRIENDS":e.source==="supplemental_makore"?"HOT CINEMA":"הזמנה";
   return {name,url,price_min_ils:e.price_min_ils??null,member_price_min_ils:e.member_price_min_ils??null,price_is_starting:e.price_is_starting===true,event_id:e.event_id};
 }
 function reconcile(rows){
   if(window.location?.pathname&&!window.location.pathname.includes("/ashdod/"))return rows;
   const slots=new Map();
   for(const e of rows){
     const family=identity(e);if(!family)continue;
     const key=family+"|"+e.start_date+"|"+e.start_time;
     if(!slots.has(key))slots.set(key,[]);
     slots.get(key).push(e);
   }
   const replacements=new Map(),omitted=new Set();
   for(const matches of slots.values()){
     const ranked=[...matches].sort((a,b)=>priority(a)-priority(b));
     const chosen=ranked[0],offers=[],seen=new Set();
     for(const e of ranked){const offer=sourceOffer(e);if(offer&&!seen.has(offer.url)){seen.add(offer.url);offers.push(offer)}}
     const merged={...chosen,series_id:series,series_title:title,title,
       venue:"הוט סינמה ראשון לציון — אולם 2",
       _source_event_ids:matches.map(e=>e.event_id),_source_offers:offers};
     replacements.set(matches[0],merged);
     for(const e of matches.slice(1))omitted.add(e);
   }
   return rows.filter(e=>!omitted.has(e)).map(e=>replacements.get(e)||e);
 }
 window.ISNET_EVENT_IDENTITIES={reconcile};
})();
