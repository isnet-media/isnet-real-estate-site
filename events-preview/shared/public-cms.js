(function(){
  const url="https://qomkxhafrprooekwgsxf.supabase.co";
  const key="sb_publishable_njxvSKmgkOQqkGL3JbWiIA_od-9l3wb";
  const root=new URL('../',document.currentScript.src);
  const timeout=()=>typeof AbortSignal!=='undefined'&&AbortSignal.timeout?AbortSignal.timeout(15000):undefined;
  const sourceRequests=new Map(),cmsRequests=new Map();
  function cityName(city){
    city=city||location.pathname.match(/events-preview\/([^/]+)/)?.[1];
    if(!['ashdod','rishon-lezion'].includes(city))throw new Error('Unknown city');return city;
  }
  function loadSource(city){
    city=cityName(city);
    if(!sourceRequests.has(city))sourceRequests.set(city,fetch(new URL(city+'/data/events.json',root),{cache:'no-cache',signal:timeout()}).then(r=>{if(!r.ok)throw new Error('Event data unavailable');return r.json()}).catch(error=>{sourceRequests.delete(city);throw error}));
    return sourceRequests.get(city);
  }
  async function readPublished(city){
    const rows=[];
    for(let offset=0;;offset+=200){
      const endpoint=url+"/rest/v1/cms_event_records?city_slug=eq."+encodeURIComponent(city)+"&publication_status=eq.published&select=event_id,record_type,payload,seo_slug,publication_status,published_at,public_path&order=event_id.asc&offset="+offset+"&limit=200";
      const r=await fetch(endpoint,{headers:{apikey:key},cache:'no-cache',signal:timeout()});
      if(!r.ok)throw new Error('Published CMS events unavailable: '+r.status);
      const page=await r.json();if(!Array.isArray(page))throw new Error('Invalid CMS response');rows.push(...page);
      if(page.length<200)break;
    }
    const source=await loadSource(city);
    const base=new Map((source.events||[]).map(e=>[String(e.event_id),e]));
    return rows.map(row=>({...row,payload:window.ISNET_EVENT_OVERLAY?.merge(base.get(String(row.event_id))||{},row.payload)||row.payload}));
  }
  window.ISNET_PUBLIC_CMS={loadSource,
    publishedEvents(city){
      city=cityName(city);
      if(!cmsRequests.has(city))cmsRequests.set(city,readPublished(city).catch(error=>{cmsRequests.delete(city);console.warn(error);window.ISNET_CMS_DEGRADED=true;return []}));
      return cmsRequests.get(city);
    }
  };
})();
