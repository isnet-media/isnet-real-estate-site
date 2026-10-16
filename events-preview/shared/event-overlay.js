(function(root){
  'use strict';
  const fields=['title','short_pitch','long_description','category','subcategory','start_date','end_date','start_time','venue','address','purchase_url','youtube_id','image_credit','image_publishable','image_verified','image_url','thumbnail_url','age_min','age_max','organizer','accessibility','contact_phone','content_source_url','ticket_status'];
  const same=(a,b)=>JSON.stringify(a??null)===JSON.stringify(b??null);
  function merge(base={},payload={}){
    const out={...base,...payload};
    if(payload.overlay_version===2){
      const locked=new Set(payload.locked_fields||[]);
      for(const key of fields)if(!locked.has(key)){
        if(Object.prototype.hasOwnProperty.call(base,key))out[key]=base[key];else delete out[key];
      }
    }
    if(payload.description_manual_override===true){
      const text=out.long_description||'';
      out.description=text;out.series_description=text;out.editorial_description=text;
    }
    if(payload.image_manual_override===true&&payload.image_data_url){
      out.image_url=payload.image_data_url;out.thumbnail_url=payload.image_data_url;
      out.thumbnail_ready=true;
    }
    return out;
  }
  function patch(values,baseline,previous={}){
    const locked=new Set(previous.overlay_version===2?previous.locked_fields||[]:fields.filter(k=>Object.prototype.hasOwnProperty.call(previous,k)));
    for(const key of fields)if(!same(values[key],baseline[key]))locked.add(key);
    const out={...previous,...values,overlay_version:2,locked_fields:[...locked]};
    out.category_manual_override=locked.has('category');out.subcategory_manual_override=locked.has('subcategory');
    out.description_manual_override=locked.has('long_description');
    out.image_manual_override=previous.image_manual_override===true||Boolean(values.image_data_url);
    if(out.image_manual_override)for(const key of ['image_url','thumbnail_url','image_credit','image_verified','image_publishable'])if(!out.locked_fields.includes(key))out.locked_fields.push(key);
    return out;
  }
  function visible(e){return Boolean(e)&&!["hidden","draft","archived","trashed","deleted","cancelled","canceled"].includes(e.status)&&!["draft","unpublished","hidden","archived"].includes(e.publication_status)&&e.is_active!==false;}
  const api={fields,merge,patch,visible};root.ISNET_EVENT_OVERLAY=api;
  if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof window==='object'?window:globalThis);
