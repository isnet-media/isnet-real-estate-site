const cityMap={"ashdod":{name:"אשדוד",base:"../ashdod/"},"rishon-lezion":{name:"ראשון לציון",base:"../rishon-lezion/"}};
const $=id=>document.getElementById(id);
const params=new URLSearchParams(location.search);
const city=params.get("city"),id=params.get("id");
const cfg=cityMap[city];
let original=null,currentImageData=null,taxonomy=null,savedPayload={},baselineValues={},releasedFields=new Set(),recordType="override";
const OVERRIDE_KEY="isnet-event-overrides";

function draftKey(){return "isnet-event-draft:"+city+":"+id}
function readOverrides(){try{return JSON.parse(localStorage.getItem(OVERRIDE_KEY)||"{}")}catch{return{}}}
async function saveOverride(status){
  const payload={...collect(),status};
  try{
    const savedRow=await window.ISNET_DB.saveEventRecord(city,id,payload,recordType);
    savedPayload=savedRow.payload;setBaseline();dirty=false;
    localStorage.removeItem(draftKey());
    $("status").value=status;
    $("saveNote").textContent=status==="hidden"?"האירוע הוסתר ונשמר במערכת.":status==="archived"?"האירוע הועבר לארכיון ונשמר במערכת.":"האירוע הועבר לסל ונשמר במערכת.";
  }catch(err){
    $("saveNote").textContent=err.message||"השמירה נכשלה. האירוע לא הוסתר ולא הועבר.";
    console.error(err);return;
  }
  setTimeout(()=>location.href="./",700);
}
function setOptions(selected=""){
  const items=taxonomy?.primary_categories||[];
  $("category").innerHTML=items.map(item=>'<option value="'+item.id+'" '+(item.id===selected?'selected':'')+'>'+item.label+'</option>').join("");
}
function renderSubcategories(categoryId,selected=""){
  const cat=(taxonomy?.primary_categories||[]).find(x=>x.id===categoryId);
  const items=cat?.subcategories||[];
  $("subcategory").innerHTML='<option value="">בחרו תת־קטגוריה</option>'+items.map(item=>'<option value="'+item.id+'" '+(item.id===selected?'selected':'')+'>'+item.label+'</option>').join("");
}
function renderTaxonomy(containerId,items,selected=[]){
  const selectedSet=new Set(selected||[]);
  $(containerId).innerHTML=(items||[]).map(item=>'<label class="tax-option"><input type="checkbox" value="'+item.id+'" '+(selectedSet.has(item.id)||selectedSet.has(item.label)?'checked':'')+'><span>'+item.label+'</span></label>').join("");
}
function selectedTaxonomy(containerId){return Array.from($(containerId).querySelectorAll('input[type="checkbox"]:checked')).map(x=>x.value)}
function renderAllTaxonomies(e={}){
  renderTaxonomy("secondaryCategories",taxonomy.secondary_categories,e.secondary_categories||[]);
  renderTaxonomy("audiencesText",taxonomy.audiences,e.audiences||[]);
  renderTaxonomy("topics",taxonomy.topics,e.topics||[]);
  const orgs=(taxonomy.organizations||[]).filter(x=>!x.cities||x.cities.includes(city));
  renderTaxonomy("organizations",orgs,e.organizations||[]);
  renderTaxonomy("distributionTargets",taxonomy.distribution_targets,e.distribution_targets||[]);
}
function makeSlug(value){
  return String(value||"").normalize("NFKC").trim().toLowerCase()
    .replace(/["'״׳]/g,"")
    .replace(/[^\p{L}\p{N}]+/gu,"-")
    .replace(/^-+|-+$/g,"")
    .slice(0,90);
}
function imageUrl(e){const raw=e.thumbnail_url||e.image_url||"";return raw?(/^(https?:|data:)/.test(raw)?raw:cfg.base+raw):""}
function fill(e,ed={}){
  $("title").value=e.title||"";
  $("shortPitch").value=ed.short_pitch||e.short_pitch||"";
  $("description").value=ed.long_description||e.long_description||e.series_description||e.description||"";
  $("category").value=e.category||""; renderSubcategories($("category").value,e.subcategory||""); $("status").value=e.status||"active"; $("promotion").value=e.promotion||"normal";
  renderAllTaxonomies(e);
  $("smartDistribution").checked=e.smart_distribution!==false;
  $("seoTitle").value=e.seo_title||e.title||"";
  $("seoDescription").value=e.seo_description||ed.short_pitch||e.short_pitch||"";
  $("seoSlug").value=e.seo_slug||makeSlug(e.title||"");
  $("schemaType").value=e.schema_type||"Event";
  $("seoIndex").checked=e.seo_index!==false;
  $("promoteHome").checked=e.promote_home===true;
  $("promoteCity").checked=e.promote_city!==false;
  $("promoteSection").checked=e.promote_section!==false;
  for(const [field,node] of Object.entries({end_date:'endDate',age_min:'ageMin',age_max:'ageMax',organizer:'organizer',accessibility:'accessibility',contact_phone:'contactPhone',content_source_url:'sourceUrl',ticket_status:'ticketStatus'}))$(node).value=e[field]??'';
  $("startDate").value=e.start_date||""; $("startTime").value=e.start_time||"";
  $("venue").value=e.venue||""; $("address").value=e.address||"";
  $("purchaseUrl").value=e.purchase_url||e.ticket_url||"";
  $("youtubeId").value=ed.youtube_id||e.youtube_id||"";
  $("imageCredit").value=e.image_credit||"";
  $("imageApproved").checked=e.image_publishable===true&&e.image_verified===true;
  const img=imageUrl(e); currentImageData=null;
  $("imagePreview").style.backgroundImage=img?'url("'+img.replace(/"/g,"%22")+'")':"none";
  $("imageState").innerHTML=img?($("imageApproved").checked?'<span class="tag good">יש תמונה · מאושרת</span>':'<span class="tag warn">יש תמונה · לבדיקה</span>'):'<span class="tag bad">אין תמונה</span>';
}
function collectValues(){
  return {end_date:$("endDate").value||null,age_min:$("ageMin").value===""?null:Number($("ageMin").value),age_max:$("ageMax").value===""?null:Number($("ageMax").value),organizer:$("organizer").value.trim(),accessibility:$("accessibility").value.trim(),contact_phone:$("contactPhone").value.trim(),content_source_url:$("sourceUrl").value.trim(),ticket_status:$("ticketStatus").value||null,event_id:id,city:cfg.name,title:$("title").value.trim(),short_pitch:$("shortPitch").value.trim(),long_description:$("description").value.trim(),category:$("category").value,subcategory:$("subcategory").value||null,secondary_categories:selectedTaxonomy("secondaryCategories"),audiences:selectedTaxonomy("audiencesText"),topics:selectedTaxonomy("topics"),organizations:selectedTaxonomy("organizations"),distribution_targets:selectedTaxonomy("distributionTargets"),smart_distribution:$("smartDistribution").checked,seo_title:$("seoTitle").value.trim(),seo_description:$("seoDescription").value.trim(),seo_slug:$("seoSlug").value.trim(),schema_type:$("schemaType").value,seo_index:$("seoIndex").checked,promote_home:$("promoteHome").checked,promote_city:$("promoteCity").checked,promote_section:$("promoteSection").checked,status:$("status").value,promotion:$("promotion").value,start_date:$("startDate").value,start_time:$("startTime").value,venue:$("venue").value.trim(),address:$("address").value.trim(),purchase_url:$("purchaseUrl").value.trim(),youtube_id:$("youtubeId").value.trim(),image_credit:$("imageCredit").value.trim(),image_approved:$("imageApproved").checked,image_data_url:currentImageData,updated_at:new Date().toISOString()};
}
function setBaseline(){baselineValues=collectValues();baselineValues.image_publishable=baselineValues.image_approved;baselineValues.image_verified=baselineValues.image_approved;}
function collect(){
  const values=collectValues();
  values.image_publishable=values.image_approved;values.image_verified=values.image_approved;
  const result=window.ISNET_EVENT_OVERLAY.patch(values,baselineValues,savedPayload);
  result.locked_fields=result.locked_fields.filter(key=>!releasedFields.has(key));
  result.category_manual_override=result.locked_fields.includes('category');
  result.subcategory_manual_override=result.locked_fields.includes('subcategory');
  result.description_manual_override=result.locked_fields.includes('long_description');
  if(releasedFields.has('image_url')){result.image_manual_override=false;delete result.image_data_url;}
  return result;
}
const fieldNames={title:'כותרת',short_pitch:'תקציר',long_description:'תיאור',category:'קטגוריה',subcategory:'תת־קטגוריה',start_date:'תאריך',end_date:'תאריך סיום',start_time:'שעה',venue:'מקום',address:'כתובת',purchase_url:'קישור רכישה',image_url:'תמונה',image_credit:'קרדיט תמונה',age_min:'גיל מינימלי',age_max:'גיל מרבי',organizer:'מארגן',ticket_status:'מצב כרטיסים'};
function renderLocks(){
  const container=$("syncLocks");container.replaceChildren();
  const locks=savedPayload.overlay_version===2?savedPayload.locked_fields||[]:window.ISNET_EVENT_OVERLAY.fields.filter(key=>Object.prototype.hasOwnProperty.call(savedPayload,key));
  for(const key of locks){
    const label=document.createElement('label');label.className='checkbox';
    const input=document.createElement('input');input.type='checkbox';input.checked=!releasedFields.has(key);
    input.addEventListener('change',()=>{if(input.checked)releasedFields.delete(key);else releasedFields.add(key);markDirty()});
    label.append(input,document.createTextNode(' שמירת עריכה ידנית: '+(fieldNames[key]||key)));container.append(label);
  }
  if(!locks.length)container.textContent='שדות שלא שונו ידנית ממשיכים להתעדכן מהמקור. שינוי שדה ושמירה מגינים על העריכה.';
}
function validateValues(){
 const v=collectValues();
 if(v.end_date&&v.end_date<v.start_date)return 'תאריך הסיום מוקדם מתאריך ההתחלה.';
 if(v.age_min!==null&&v.age_max!==null&&v.age_max<v.age_min)return 'הגיל המרבי קטן מהגיל המינימלי.';
 for(const key of ['purchase_url','content_source_url'])if(v[key]&&!/^https?:\/\//i.test(v[key]))return 'יש להזין קישור מלא שמתחיל ב־https:// או http://.';
 return '';
}
async function load(){
  if(!cfg||!id)throw Error("missing params");
  taxonomy=await fetch("data/taxonomy.json",{cache:"no-store"}).then(r=>r.json());
  setOptions();
  const [data,editorial]=await Promise.all([
    fetch(cfg.base+"data/events.json",{cache:"no-store"}).then(r=>r.json()),
    fetch(cfg.base+"data/editorial.json",{cache:"no-store"}).then(r=>r.ok?r.json():{events:{}}).catch(()=>({events:{}}))
  ]);
  const dbRecord=await window.ISNET_DB?.getEventRecord?.(city,id);
  recordType=dbRecord?.record_type||"override";
  if(recordType==='manual'){$("restoreBtn").disabled=true;$("restoreBtn").textContent="אירוע ידני — אין גרסת מקור";}
  const e=(data.events||[]).find(x=>x.event_id===id)||(recordType==='manual'?dbRecord?.payload:null);if(!e)throw Error("event not found");
  original={event:e,editorial:editorial.events?.[id]||{}};
  $("cloneLink").href="new.html?clone="+encodeURIComponent(id)+"&city="+encodeURIComponent(city);
  $("pageTitle").textContent=e.title; $("pageMeta").textContent=cfg.name+" · "+(e.start_date||"");
  const saved=localStorage.getItem(draftKey());
  if(dbRecord?.payload){
    const d=dbRecord.payload;savedPayload=d;const merged=window.ISNET_EVENT_OVERLAY.merge(e,d);fill(merged,d.description_manual_override?{...original.editorial,...d}:original.editorial);$("saveNote").textContent="נטענה הגרסה השמורה במערכת המרכזית.";if(d.image_data_url){currentImageData=d.image_data_url;$("imagePreview").style.backgroundImage='url("'+d.image_data_url+'")'}
  } else if(saved){
    const d=JSON.parse(saved);fill({...e,...d},{...original.editorial,...d});$("saveNote").textContent="נטענה טיוטת גיבוי מקומית.";if(d.image_data_url){currentImageData=d.image_data_url;$("imagePreview").style.backgroundImage='url("'+d.image_data_url+'")'}
  } else fill(e,original.editorial);
  setBaseline();baselineValues.image_publishable=baselineValues.image_approved;baselineValues.image_verified=baselineValues.image_approved;
  renderLocks();
}
$("category").addEventListener("change",()=>renderSubcategories($("category").value));
$("imageFile").addEventListener("change",e=>{
  const file=e.target.files?.[0];if(!file)return;
  if(file.size>5*1024*1024){alert("התמונה גדולה מ־5MB. בחר תמונה קטנה יותר.");e.target.value="";return}
  const reader=new FileReader();reader.onload=()=>{currentImageData=reader.result;$("imagePreview").style.backgroundImage='url("'+reader.result+'")';$("imageApproved").checked=false;$("imageState").innerHTML='<span class="tag warn">תמונה חדשה · דורשת אישור</span>'};reader.readAsDataURL(file);
});
let dirty=false;
function markDirty(){
  dirty=true;
  const btn=$("saveDraftBtn");
  if(!btn.disabled) btn.textContent="שמור שינויים";
  $("saveNote").textContent="יש שינויים שעדיין לא נשמרו.";
}
$("saveDraftBtn").addEventListener("click",async()=>{
  const validation=validateValues();if(validation){$("saveNote").textContent=validation;return;}
  const btn=$("saveDraftBtn"),payload=collect();
  btn.disabled=true;btn.textContent="שומר...";
  $("saveNote").textContent="שומר את השינויים במערכת...";
  try{
    const savedRow=await window.ISNET_DB.saveEventRecord(city,id,payload,recordType);
    savedPayload=savedRow.payload;setBaseline();releasedFields.clear();renderLocks();
    localStorage.removeItem(draftKey());
    dirty=false;
    btn.textContent="נשמר ✓";
    $("saveNote").textContent="נשמר במערכת המרכזית ב־"+new Date().toLocaleTimeString("he-IL",{hour:"2-digit",minute:"2-digit"});
  }catch(err){
    localStorage.setItem(draftKey(),JSON.stringify(payload));
    btn.textContent="נשמר גיבוי מקומי";
    $("saveNote").textContent=(err.message||"לא ניתן היה לשמור בשרת.")+" נשמר גיבוי מקומי בדפדפן.";
    console.error(err);
  }finally{
    btn.disabled=false;
  }
});
document.querySelectorAll(".editor-column input,.editor-column textarea,.editor-column select,.side-column input,.side-column textarea,.side-column select").forEach(el=>{
  el.addEventListener("input",markDirty);
  el.addEventListener("change",markDirty);
});
$("hideBtn").addEventListener("click",()=>saveOverride("hidden"));
$("archiveBtn").addEventListener("click",()=>saveOverride("archived"));
$("trashBtn").addEventListener("click",()=>{if(confirm("להעביר את האירוע לסל? אפשר יהיה לשחזר אותו בהמשך."))saveOverride("trashed")});
$("restoreBtn").addEventListener("click",async()=>{
  if(!original||!confirm("להסיר את הגרסה השמורה ולחזור לנתוני המקור? מומלץ לייצא גיבוי לפני פעולה זו."))return;
  try{
    if(Object.keys(savedPayload).length)await window.ISNET_DB.deleteEventRecord(city,id);
    localStorage.removeItem(draftKey());const map=readOverrides();delete map[city+":"+id];localStorage.setItem(OVERRIDE_KEY,JSON.stringify(map));
    savedPayload={};releasedFields.clear();fill(original.event,original.editorial);setBaseline();renderLocks();dirty=false;
    $("saveNote").textContent="החזרה למקור נשמרה בהצלחה.";
  }catch(err){$("saveNote").textContent="החזרה למקור נכשלה: "+err.message;}
});
window.addEventListener('beforeunload',event=>{if(dirty){event.preventDefault();event.returnValue='';}});
$("previewBtn").addEventListener("click",()=>{if(!cfg||!id)return;window.open(cfg.base+"event.html?id="+encodeURIComponent(id),"_blank","noopener")});
load().catch(err=>{$("pageTitle").textContent="לא ניתן לטעון את האירוע";$("pageMeta").textContent=String(err.message||err)});

async function publishCurrentEvent(){
  const btn=$("publishBtn");
  const validation=validateValues();if(validation){$("saveNote").textContent=validation;return;}
  const payload=collect();
  if(!payload.title||!payload.start_date){
    alert("אי אפשר לפרסם בלי כותרת ותאריך.");
    return;
  }
  if(!payload.seo_slug){
    payload.seo_slug=makeSlug(payload.title);
    $("seoSlug").value=payload.seo_slug;
  }
  btn.disabled=true;
  btn.textContent="מפרסם...";
  $("saveNote").textContent="מפרסם את הגרסה הנוכחית...";
  try{
    const row=await window.ISNET_DB.publishEvent(city,id,payload,recordType);
    $("status").value=row.status||row.payload.status||"active";
    savedPayload=row.payload;setBaseline();releasedFields.clear();renderLocks();
    dirty=false;
    btn.textContent="פורסם ✓";
    const slug=row?.seo_slug||payload.seo_slug;
    const preview=cfg.base+"event.html?slug="+encodeURIComponent(slug);
    $("saveNote").innerHTML='האירוע פורסם במערכת המרכזית. <a class="link" target="_blank" rel="noopener" href="'+preview+'">פתח את העמוד הציבורי ↗</a>';
  }catch(err){
    console.error(err);
    btn.textContent="פרסום נכשל";
    $("saveNote").textContent="הפרסום נכשל: "+err.message;
  }finally{
    btn.disabled=false;
  }
}
$("publishBtn")?.addEventListener("click",publishCurrentEvent);
