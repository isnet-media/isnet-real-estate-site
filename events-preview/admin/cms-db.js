(function(){
  function client(){
    const cfg=window.ISNET_AUTH_CONFIG||{};
    if(!cfg.enabled||!window.supabase)return null;
    return window.supabase.createClient(cfg.supabaseUrl,cfg.supabaseAnonKey,{auth:{persistSession:true,autoRefreshToken:true}});
  }
  async function userId(db){
    const {data:{user}}=await db.auth.getUser();
    return user?.id||null;
  }
  window.ISNET_DB={
    async listMediaAssets(){
      const db=client();if(!db)throw new Error("database unavailable");
      if(!await userId(db))throw new Error("not authenticated");
      const {data,error}=await db.from("isnet_media_assets").select("*").order("created_at",{ascending:false}).limit(1000);
      if(error)throw error;
      return data||[];
    },
    async uploadMediaAsset(file, metadata){
      const db=client();if(!db)throw new Error("database unavailable");
      const uid=await userId(db);if(!uid)throw new Error("not authenticated");
      if(!file || !["image/jpeg","image/png","image/webp"].includes(file.type) || file.size>5*1024*1024)
        throw new Error("Only JPG/PNG/WebP images up to 5MB are allowed");
      const type=String(metadata.asset_type||"");
      if(!["event_poster","artist","production","venue","subcategory","category"].includes(type))
        throw new Error("Invalid asset type");
      const rights=String(metadata.rights_status||"unknown");
      if(!["verified","permission_required","unknown","expired"].includes(rights))
        throw new Error("Invalid rights status");
      const filename=crypto.randomUUID()+"."+(file.type==="image/png"?"png":file.type==="image/webp"?"webp":"jpg");
      const objectPath="uploads/"+new Date().toISOString().slice(0,10)+"/"+filename;
      const {error:uploadError}=await db.storage.from("isnet-event-media").upload(objectPath,file,{cacheControl:"3600",upsert:false,contentType:file.type});
      if(uploadError)throw uploadError;
      const row={asset_id:"asset_"+crypto.randomUUID(),asset_type:type,
        original_url:String(metadata.original_url||metadata.source_url||""),
        source_url:String(metadata.source_url||""),
        source_id:String(metadata.source_id||"manual"),
        title:String(metadata.title||""),image_credit:String(metadata.image_credit||""),
        rights_status:rights,reviewer:rights==="verified"?uid:null,
        object_path:objectPath,subjects:Array.isArray(metadata.subjects)?metadata.subjects:[],
        related_event_ids:Array.isArray(metadata.related_event_ids)?metadata.related_event_ids:[]};
      const {data,error}=await db.from("isnet_media_assets").insert(row).select().single();
      if(error){
        await db.storage.from("isnet-event-media").remove([objectPath]);
        throw error;
      }
      return data;
    },
    async mediaPreviewUrl(objectPath){
      const db=client();if(!db)throw new Error("database unavailable");
      if(!await userId(db))throw new Error("not authenticated");
      const {data,error}=await db.storage.from("isnet-event-media").createSignedUrl(objectPath,120);
      if(error)throw error;
      return data.signedUrl;
    },

    async listEventRecords(){
      const db=client();if(!db)return [];
      const {data,error}=await db.from("cms_event_records").select("*");
      if(error){console.warn("cms_event_records unavailable",error);return []}
      return data||[];
    },
    async getEventRecord(city,eventId){
      const db=client();if(!db)return null;
      const {data,error}=await db.from("cms_event_records").select("*").eq("city_slug",city).eq("event_id",eventId).maybeSingle();
      if(error){console.warn("get event record failed",error);return null}
      return data||null;
    },
    async saveEventRecord(city,eventId,payload,recordType="override"){
      const db=client();if(!db)throw new Error("database unavailable");
      const uid=await userId(db);if(!uid)throw new Error("not authenticated");
      const row={city_slug:city,event_id:eventId,record_type:recordType,payload,status:payload.status||null,updated_by:uid,updated_at:new Date().toISOString()};
      const {data,error}=await db.from("cms_event_records").upsert(row,{onConflict:"city_slug,event_id"}).select().single();
      if(error)throw error;return data;
    },
    async publishEvent(city,eventId,payload,recordType="override"){
      const db=client();if(!db)throw new Error("database unavailable");
      const uid=await userId(db);if(!uid)throw new Error("not authenticated");
      const slug=String(payload.seo_slug||"").trim();
      if(!slug)throw new Error("missing slug");
      const publishedAt=new Date().toISOString();
      const publicPath="/events/"+slug;
      const publicPayload={...payload,status:"active",publication_status:"published",published_at:publishedAt,public_path:publicPath};
      const row={
        city_slug:city,event_id:eventId,record_type:recordType,payload:publicPayload,
        status:"active",seo_slug:slug,publication_status:"published",
        published_at:publishedAt,public_path:publicPath,updated_by:uid,updated_at:publishedAt
      };
      const {data,error}=await db.from("cms_event_records").upsert(row,{onConflict:"city_slug,event_id"}).select().single();
      if(error)throw error;return data;
    },
    async unpublishEvent(city,eventId,payload,recordType="override"){
      const db=client();if(!db)throw new Error("database unavailable");
      const uid=await userId(db);if(!uid)throw new Error("not authenticated");
      const row={
        city_slug:city,event_id:eventId,record_type:recordType,payload:{...payload,publication_status:"unpublished"},
        status:payload.status||"active",seo_slug:payload.seo_slug||null,publication_status:"unpublished",
        updated_by:uid,updated_at:new Date().toISOString()
      };
      const {data,error}=await db.from("cms_event_records").upsert(row,{onConflict:"city_slug,event_id"}).select().single();
      if(error)throw error;return data;
    },
    async deleteEventRecord(city,eventId){
      const db=client();if(!db)throw new Error("database unavailable");
      const {error}=await db.from("cms_event_records").delete().eq("city_slug",city).eq("event_id",eventId);
      if(error)throw error;return true;
    }
  };
})();