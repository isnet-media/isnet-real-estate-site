'use strict';
// Import the official Population Authority CSV without guessing geocoordinates.
// Usage: node import-official-streets.cjs streets.csv [synonyms.csv]
// Writes bus/ashdod/data/ashdod-streets.json, containing names and aliases only.
const fs=require('node:fs'),path=require('node:path');
const {TextDecoder}=require('node:util');
function decode(b){for(const enc of ['utf-8','windows-1255']){try{const s=new TextDecoder(enc,{fatal:true}).decode(b);if(s.includes('שם_רחוב')||s.includes('שם רחוב'))return s}catch{}}throw Error('Unrecognized official CSV encoding or columns')}
function parseCSV(s){const out=[];let row=[],cell='',quoted=false;for(let i=0;i<s.length;i++){const c=s[i];if(c==='"'){if(quoted&&s[i+1]==='"'){cell+='"';i++}else quoted=!quoted}else if(c===','&&!quoted){row.push(cell);cell=''}else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&s[i+1]==='\n')i++;row.push(cell);if(row.some(Boolean))out.push(row);row=[];cell=''}else cell+=c}if(quoted)throw Error('Unclosed CSV quote');row.push(cell);if(row.some(Boolean))out.push(row);return out}
const norm=s=>String(s||'').replace(/^\uFEFF/,'').replace(/[\s\u200e\u200f]+/g,'').replace(/[-_]/g,'').trim();
function records(csv){const rows=parseCSV(csv),head=rows.shift().map(norm);return rows.map(row=>Object.fromEntries(head.map((h,i)=>[h,(row[i]||'').trim()])))}
function extract(streets,synonyms=''){const result=new Map();for(const r of records(streets)){const city=r['שם_ישוב']||r['שםישוב'];const code=r['סמל_ישוב']||r['סמלישוב'];const id=r['סמל_רחוב']||r['סמלרחוב'];const name=r['שם_רחוב']||r['שםרחוב'];if(city!=='אשדוד'||!id||!name||!code)continue;result.set(code+':'+id,{cityCode:code,streetCode:id,name,aliases:[]})}
 if(synonyms)for(const r of records(synonyms)){const code=r['סמל_ישוב']||r['סמלישוב'],id=r['סמל_רחוב']||r['סמלרחוב'];const entry=result.get(code+':'+id);if(!entry)continue;const values=Object.entries(r).filter(([k])=>/שם|סינונ|חלופי/.test(k)&&!(/ישוב/.test(k))).map(([,v])=>v).filter(v=>v&&v!==entry.name);for(const v of values)if(!entry.aliases.includes(v))entry.aliases.push(v)}
 return [...result.values()].sort((a,b)=>a.name.localeCompare(b.name,'he'))}
if(require.main===module){const [file,syn]=process.argv.slice(2);if(!file)throw Error('Provide official CSV filename');const data=extract(decode(fs.readFileSync(file)),syn?decode(fs.readFileSync(syn)):'');if(data.length<100)throw Error('Too few Ashdod streets; check input format');const target=path.resolve(__dirname,'data/ashdod-streets.json');fs.writeFileSync(target,JSON.stringify({source:'Population Authority / data.gov.il',verifiedCoordinates:false,streets:data},null,2)+'\n');console.log('Imported',data.length,'official Ashdod streets:',target)}
module.exports={parseCSV,records,extract};
