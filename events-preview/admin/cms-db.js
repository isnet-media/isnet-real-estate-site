(function(){
  const versions=new Map(),records=new Map();
  let instance=null;
  const key=(city,id)=>city+":"+id;
  function remember(row,city,id){const k=key(city||row.city_slug,id||row.event_id);versions.set(k,row?.updated_at||null);records.set(k,row);return row;}
  async function persist(db,row){
    const k=key(row.city_slug,row.event_id);
    if(!versions.has(k)){
      const {data,error}=await db.from("cms_event_records").select("updated_at").eq("city_slug",row.city_slug).eq("event_id",row.event_id).maybeSingle();
      if(error)throw error;
      if(data)throw new Error("נמצאה רשומה קיימת שלא נטענה לעריכה. רעננו לפני שמירה.");
      versions.set(k,null);records.set(k,null);
    }
    const expected=versions.get(k);
    let request=expected===null?db.from("cms_event_records").insert(row):db.from("cms_event_records").update(row).eq("city_slug",row.city_slug).eq("event_id",row.event_id).eq("updated_at",expected);
    const {data,error}=await request.select().maybeSingle();
    if(error)throw error;
    if(!data){const conflict=new Error("האירוע השתנה מאז שנטען. השינויים שלך לא נדרסו ולא נשמרו; רעננו את האירוע לפני ניסיון נוסף.");conflict.code="EDIT_CONFLICT";throw conflict;}
    return remember(data);
  }
  function client(){
    const cfg=window.ISNET_AUTH_CONFIG||{};
    if(!cfg.enabled||!window.supabase)return null;
    return instance||(instance=window.supabase.createClient(cfg.supabaseUrl,cfg.supabaseAnonKey,{auth:{persistSession:true,autoRefreshToken:true}}));
  }
  async function userId(db){
    const {data:{user}}=await db.auth.getUser();
    return user?.id||null;
  }
  window.ISNET_DB={
    async listEventRecords(){
      const db=client();if(!db)return [];
      const rows=[];
      for(let offset=0;;offset+=200){
        const {data,error}=await db.from("cms_event_records").select("*").order("city_slug").order("event_id").range(offset,offset+199);
        if(error)throw error;
        for(const row of data||[])rows.push(remember(row));
        if((data||[]).length<200)break;
      }
      return rows;
    },
    async getEventRecord(city,eventId){
      const db=client();if(!db)return null;
      const {data,error}=await db.from("cms_event_records").select("*").eq("city_slug",city).eq("event_id",eventId).maybeSingle();
      if(error)throw error;
      return remember(data,city,eventId);
    },
    async saveEventRecord(city,eventId,payload,recordType="override"){
      const db=client();if(!db)throw new Error("database unavailable");
      const uid=await userId(db);if(!uid)throw new Error("not authenticated");
      const previous=records.get(key(city,eventId));
      if(recordType==='override'&&['hidden','archived','trashed'].includes(payload.status)&&previous?.publication_status!=='published'){
        if(previous)throw new Error('קיימת טיוטה שלא פורסמה. ההסתרה נעצרה כדי לא לחשוף או למחוק אותה; נדרש טיפול במנגנון הנראות בשרת.');
        payload={status:payload.status};
        return persist(db,{city_slug:city,event_id:eventId,record_type:recordType,payload,status:payload.status,publication_status:'published',updated_by:uid,updated_at:new Date().toISOString()});
      }
      const row={city_slug:city,event_id:eventId,record_type:recordType,payload,status:payload.status||null,updated_by:uid,updated_at:new Date().toISOString()};
      return persist(db,row);
    },
    async savePublicPatch(city,eventId,payload,recordType="override"){
      const db=client();if(!db)throw new Error('database unavailable');
      const uid=await userId(db);if(!uid)throw new Error('not authenticated');
      const previous=records.get(key(city,eventId));
      if(previous&&previous.publication_status!=='published'&&recordType!=='manual')throw new Error('קיימת טיוטה שלא פורסמה; הפעולה נעצרה כדי לא לפרסם אותה בטעות.');
      const row={city_slug:city,event_id:eventId,record_type:recordType,payload,status:payload.status||previous?.status||null,updated_by:uid,updated_at:new Date().toISOString()};
      if(recordType!=='manual')row.publication_status='published';
      return persist(db,row);
    },
    async publishEvent(city,eventId,payload,recordType="override"){
      const db=client();if(!db)throw new Error("database unavailable");
      const uid=await userId(db);if(!uid)throw new Error("not authenticated");
      const slug=String(payload.seo_slug||"").trim();
      if(!slug)throw new Error("missing slug");
      const publishedAt=new Date().toISOString();
      const publicPath="/events-preview/"+city+"/event.html?slug="+encodeURIComponent(slug);
      const publicStatus=["cancelled","canceled","postponed"].includes(payload.status)?payload.status:"active";
      const publicPayload={...payload,status:publicStatus,publication_status:"published",published_at:publishedAt,public_path:publicPath};
      const row={
        city_slug:city,event_id:eventId,record_type:recordType,payload:publicPayload,
        status:publicStatus,seo_slug:slug,publication_status:"published",
        published_at:publishedAt,public_path:publicPath,updated_by:uid,updated_at:publishedAt
      };
      return persist(db,row);
    },
    async unpublishEvent(city,eventId,payload,recordType="override"){
      const db=client();if(!db)throw new Error("database unavailable");
      const uid=await userId(db);if(!uid)throw new Error("not authenticated");
      const row={
        city_slug:city,event_id:eventId,record_type:recordType,payload:{...payload,publication_status:"unpublished"},
        status:payload.status||"active",seo_slug:payload.seo_slug||null,publication_status:"unpublished",
        updated_by:uid,updated_at:new Date().toISOString()
      };
      return persist(db,row);
    },
    async deleteEventRecord(city,eventId){
      const db=client();if(!db)throw new Error("database unavailable");
      const expected=versions.get(key(city,eventId));
      if(!expected)throw new Error("יש לטעון מחדש את האירוע לפני חזרה למקור.");
      const {data,error}=await db.from("cms_event_records").delete().eq("city_slug",city).eq("event_id",eventId).eq("updated_at",expected).select("event_id");
      if(error)throw error;
      if(!data?.length)throw new Error("האירוע השתנה בינתיים. רעננו לפני חזרה למקור.");
      versions.set(key(city,eventId),null);records.delete(key(city,eventId));return true;
    }
  };
})();