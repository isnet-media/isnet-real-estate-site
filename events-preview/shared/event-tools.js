(function(root){
 'use strict';
 const key='isnet-events-favorites';
 function readSaved(){try{const value=JSON.parse(root.localStorage.getItem(key)||'[]');return new Set(Array.isArray(value)?value.filter(x=>typeof x==='string').slice(0,3000):[])}catch{return new Set()}}
 function escapeIcs(value){return String(value||'').replace(/\\/g,'\\\\').replace(/\r?\n/g,'\\n').replace(/;/g,'\\;').replace(/,/g,'\\,');}
 function nextDay(date){const d=new Date(date+'T12:00:00Z');d.setUTCDate(d.getUTCDate()+1);return d.toISOString().slice(0,10).replace(/-/g,'');}
 function calendar(events,url){
  const lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//ISNET//Events//HE','CALSCALE:GREGORIAN'];
  for(const e of events){
   if(!/^\d{4}-\d{2}-\d{2}$/.test(e.start_date||'')||['cancelled','canceled','postponed'].includes(e.status))continue;
   const day=e.start_date.replace(/-/g,''),time=/^\d{2}:\d{2}$/.test(e.start_time||'')?e.start_time.replace(':','')+'00':null;
   lines.push('BEGIN:VEVENT','UID:'+escapeIcs(String(e.event_id||day+time)+'@isnet.co.il'),'DTSTAMP:'+new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d+Z/,'Z'));
   if(time)lines.push('DTSTART;TZID=Asia/Jerusalem:'+day+'T'+time);
   else lines.push('DTSTART;VALUE=DATE:'+day,'DTEND;VALUE=DATE:'+nextDay(e.end_date||e.start_date));
   lines.push('SUMMARY:'+escapeIcs(e.series_title||e.title),'LOCATION:'+escapeIcs([e.venue,e.address].filter(Boolean).join(', ')),'DESCRIPTION:'+escapeIcs(url),'URL:'+url,'END:VEVENT');
  }
  lines.push('END:VCALENDAR');
  // Fold at 75 UTF-8 octets without splitting a Hebrew character.
  return lines.map(line=>{let out='',width=0;for(const char of line){const length=new TextEncoder().encode(char).length;if(width+length>75){out+='\r\n ';width=1;}out+=char;width+=length;}return out}).join('\r\n')+'\r\n';
 }
 function render(e,occ){
  const doc=root.document;if(!doc)return;
  let toolbar=doc.getElementById('eventTools');if(toolbar)toolbar.remove();
  toolbar=doc.createElement('div');toolbar.id='eventTools';toolbar.setAttribute('aria-label','שמירה ושיתוף האירוע');toolbar.style.cssText='display:flex;gap:10px;flex-wrap:wrap;margin:16px 0';
  const notice=doc.createElement('span');notice.setAttribute('role','status');
  const addButton=(text,action)=>{const button=doc.createElement('button');button.type='button';button.textContent=text;button.style.cssText='font:inherit;padding:9px 13px;border-radius:10px;border:1px solid #796947;background:#252630;color:#f3dfb4;cursor:pointer';button.addEventListener('click',action);toolbar.append(button);return button;};
  const url=root.location.href;
  root.ISNET_SHARE_DETAILS={title:e.series_title||e.title,url,details:[...new Set(occ.filter(x=>!['cancelled','canceled'].includes(x.status)).slice(0,6).map(x=>[x.start_date,x.start_time].filter(Boolean).join(' '))),[e.venue,e.address].filter(Boolean).join(' · ')]};
  const saved=readSaved(),ids=occ.map(x=>String(x.event_id));
  const favorite=addButton(ids.some(id=>saved.has(id))?'♥ נשמר במועדפים':'♡ שמירה למועדפים',()=>{
   const current=readSaved(),remove=ids.some(id=>current.has(id));for(const id of ids)if(remove)current.delete(id);else current.add(id);
   try{root.localStorage.setItem(key,JSON.stringify([...current]));favorite.textContent=remove?'♡ שמירה למועדפים':'♥ נשמר במועדפים';notice.textContent='המועדפים נשמרים בדפדפן הזה.';}catch{notice.textContent='לא ניתן לשמור מועדפים בדפדפן הזה.';}
  });
  if(occ.some(x=>!['cancelled','canceled','postponed'].includes(x.status)))addButton(occ.length>1?'הוספת המועדים ליומן':'הוספה ליומן',()=>{
   const file=new Blob([calendar(occ,url)],{type:'text/calendar;charset=utf-8'}),href=URL.createObjectURL(file),a=doc.createElement('a');a.href=href;a.download='isnet-event.ics';doc.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(href),10000);
  });
  addButton('שיתוף האירוע',async()=>{
   if(root.ISNET_SHARE){root.ISNET_SHARE.open(root.ISNET_SHARE_DETAILS);return}
   try{if(root.navigator.share)await root.navigator.share({title:e.series_title||e.title,url});else if(root.navigator.clipboard){await root.navigator.clipboard.writeText(url);notice.textContent='הקישור הועתק.';}else notice.textContent='אפשר להעתיק את כתובת האירוע משורת הכתובת.';}catch(error){if(error.name!=='AbortError')notice.textContent='לא ניתן לשתף כרגע; אפשר להעתיק את כתובת האירוע.';}
  });
  toolbar.append(notice);doc.getElementById('eventTitle')?.after(toolbar);
 }
 const api={readSaved,calendar,render};root.ISNET_EVENT_TOOLS=api;
 if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof window==='object'?window:globalThis);
