(function(){
  const url="https://qomkxhafrprooekwgsxf.supabase.co";
  const key="sb_publishable_njxvSKmgkOQqkGL3JbWiIA_od-9l3wb";
  const root=new URL('../',document.currentScript.src);
  const timeout=()=>typeof AbortSignal!=='undefined'&&AbortSignal.timeout?AbortSignal.timeout(15000):undefined;
  const sourceRequests=new Map(),cardRequests=new Map(),cmsRequests=new Map(),rawRequests=new Map();
  const metrics={sourceLoads:0,publishedLoads:0,pages:0,sourceMilliseconds:0,publishedMilliseconds:0};
  const clock=()=>typeof performance!=="undefined"?performance.now():Date.now();
  function cityName(city){
    city=city||location.pathname.match(/events-preview\/([^/]+)/)?.[1];
    if(!['ashdod','rishon-lezion'].includes(city))throw new Error('Unknown city');return city;
  }
  function loadSource(city){
    city=cityName(city);
    if(!sourceRequests.has(city)){const started=clock();metrics.sourceLoads++;sourceRequests.set(city,fetch(new URL(city+'/data/events.json',root),{cache:'no-cache',signal:timeout()}).then(r=>{if(!r.ok)throw new Error('Event data unavailable');return r.json()}).then(data=>{metrics.sourceMilliseconds+=clock()-started;return data}).catch(error=>{sourceRequests.delete(city);throw error}));}
    return sourceRequests.get(city);
  }
  function loadCards(city){
    city=cityName(city);
    if(!cardRequests.has(city))cardRequests.set(city,fetch(new URL(city+'/data/events-cards.json',root),{cache:'no-cache',signal:timeout()}).then(r=>{if(!r.ok)throw new Error('Listing unavailable');return r.json()}).catch(()=>loadSource(city)));
    return cardRequests.get(city);
  }
  async function readRows(city){
    const rows=[];const started=clock();metrics.publishedLoads++;
    for(let offset=0;;offset+=200){
      const endpoint=url+"/rest/v1/cms_event_records?city_slug=eq."+encodeURIComponent(city)+"&publication_status=eq.published&select=event_id,record_type,payload,seo_slug,publication_status,published_at,public_path&order=event_id.asc&offset="+offset+"&limit=200";
      metrics.pages++;const r=await fetch(endpoint,{headers:{apikey:key},cache:'no-cache',signal:timeout()});
      if(!r.ok)throw new Error('Published CMS events unavailable: '+r.status);
      const page=await r.json();if(!Array.isArray(page))throw new Error('Invalid CMS response');rows.push(...page);
      if(page.length<200)break;
    }
    metrics.publishedMilliseconds+=clock()-started;
    return rows;
  }
  async function readPublished(city,listing){
    if(!rawRequests.has(city))rawRequests.set(city,readRows(city).catch(error=>{rawRequests.delete(city);throw error;}));
    const [rows,source]=await Promise.all([rawRequests.get(city),listing?loadCards(city):loadSource(city)]);
    const base=new Map((source.events||[]).map(e=>[String(e.event_id),e]));
    return rows.map(row=>({...row,payload:window.ISNET_EVENT_OVERLAY?.merge(base.get(String(row.event_id))||{},row.payload)||row.payload}));
  }
  window.ISNET_PUBLIC_CMS={loadSource,loadCards,metrics,
    publishedEvents(city,options={}){
      city=cityName(city);const cacheKey=city+(options.listing?':cards':':full');
      if(!cmsRequests.has(cacheKey))cmsRequests.set(cacheKey,readPublished(city,options.listing).catch(error=>{cmsRequests.delete(cacheKey);console.warn(error);window.ISNET_CMS_DEGRADED=true;return []}));
      return cmsRequests.get(cacheKey);
    }
  };
})();
