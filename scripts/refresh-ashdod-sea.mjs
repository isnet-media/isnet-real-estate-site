import {mkdir, writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import https from 'node:https';

export const SOURCE='https://ims.gov.il/sites/default/files/ims_data/xml_files/isr_sea.xml';
export function localTime(date=new Date()) {
  const p=Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Jerusalem',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(date).map(p=>[p.type,p.value]));
  return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`;
}
function value(xml,tag){const m=xml.match(new RegExp(`<${tag}>([\\s\\S]*?)</${tag}>`));if(!m)throw new Error(`Missing ${tag}`);return m[1].trim();}
function time(s){if(!/^\d{4}-\d\d-\d\d \d\d:\d\d$/.test(s))throw new Error('Invalid forecast time');return s.replace(' ','T');}
export function parseSea(xml,now=new Date()) {
  const region=[...xml.matchAll(/<Location>([\s\S]*?)<\/Location>/g)].map(m=>m[1]).find(s=>value(s,'LocationId')==='213');
  if(!region||value(region,'LocationNameEng')!=='Southern Coast')throw new Error('Missing Southern Coast forecast');
  const periods=[...region.matchAll(/<TimeUnitData>([\s\S]*?)<\/TimeUnitData>/g)].map(m=>{
    const s=m[1],elements=[...s.matchAll(/<Element>([\s\S]*?)<\/Element>/g)].map(m=>[value(m[1],'ElementName'),value(m[1],'ElementValue')]);
    const fields=Object.fromEntries(elements),wave=fields['Sea status and waves height']?.match(/^\d+\s*\/\s*(\d+)-(\d+)$/);
    if(!wave)throw new Error('Unrecognized IMS wave range');
    const minCm=Number(wave[1]),maxCm=Number(wave[2]),from=time(value(s,'DateTimeFrom')),to=time(value(s,'DateTimeTo'));
    if(minCm>maxCm||maxCm>2000||from>=to)throw new Error('Invalid wave forecast');
    return {from,to,minCm,maxCm};
  });
  const localNow=localTime(now);
  if(!periods.some(p=>p.from<=localNow&&localNow<p.to))throw new Error('No currently valid forecast; retaining last good file');
  return {schema:1,city:'אשדוד',regionId:213,region:'החוף הדרומי',source:'השירות המטאורולוגי הישראלי',sourceUrl:SOURCE,timeZone:'Asia/Jerusalem',issuedAtLocal:time(value(xml,'IssueDateTime')),fetchedAt:now.toISOString(),periods};
}
async function main(){
  let bytes,lastError;
  for(let attempt=0;attempt<3;attempt++){
    try{bytes=await new Promise((resolve,reject)=>{const req=https.get(SOURCE,{family:4,headers:{'User-Agent':'ISNET-Sea-Forecast/1.0 (https://ashdodnet.com/)','Cache-Control':'no-cache'},signal:AbortSignal.timeout(35000)},r=>{if(r.statusCode!==200){r.resume();reject(new Error(`IMS HTTP ${r.statusCode}`));return;}const chunks=[];r.on('data',c=>chunks.push(c));r.on('end',()=>resolve(Buffer.concat(chunks)));r.on('error',reject)});req.on('error',reject)});break}catch(e){lastError=e;console.error(`IMS attempt ${attempt+1}: ${e.message}`)}
  }
  if(!bytes)throw lastError;
  const xml=new TextDecoder('iso-8859-8').decode(bytes),data=parseSea(xml);
  const output=process.argv[2]||'weather/ashdod/sea.json';
  await mkdir(resolve(output,'..'),{recursive:true});await writeFile(output,JSON.stringify(data,null,2)+'\n');
  console.log(JSON.stringify({region:data.region,periods:data.periods,issuedAt:data.issuedAtLocal}));
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))await main();
