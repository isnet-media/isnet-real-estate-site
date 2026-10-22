(function(root){'use strict';
const normalize=s=>String(s||'').normalize('NFKC').replace(/["'״׳]/g,'').replace(/עגבנייה|עגבניית|עגבניות|עגבנית/g,'עגבניה').replace(/\s+/g,' ').trim();
function category(p){
 const n=normalize(p.name);
 if(p.weighted==='1'&&p.calculation_unit==='kg'){
  if(/^עגבניה(?: |$)/.test(n)&&!(/מיובש|ממולא|מוחמ|מארז|רוטב/.test(n))){
   const organic=/אורגנ/.test(n)?' אורגנית':'';
   if(/שרי/.test(n)){let type=/צהוב|כתו/.test(n)?'צהובות':/לובלו/.test(n)?'לובלו':/מנומר/.test(n)?'מנומרות':/וויטני/.test(n)?'וויטני':/אשכול/.test(n)?'אשכולות':'רגילות';return ['tomato-cherry-'+type+organic,'עגבניות שרי '+type+organic];}
   if(/מגי/.test(n))return ['tomato-magi'+organic,'עגבניות מגי'+organic];
   if(/תמר/.test(n))return ['tomato-plum'+organic,'עגבניות תמר'+organic];
   if(/ירוק/.test(n))return ['tomato-green'+organic,'עגבניות ירוקות'+organic];
   if(/^(עגבניה)( אורגנית)?( במשקל| ישראל| שקיל| לקג| אדומות| רגילה| רגילות)*$/.test(n))return ['tomato-regular'+organic,'עגבנייה רגילה'+organic];
  }
  if(/עוף/.test(n)&&/קפוא|טרי/.test(n)&&!(/הודו|נקניק|ממולא|מתובל|מבושל|מעושן|טחון|מוכן|טמפורה|שניצל/.test(n))){
   const cut=[['breast','חזה',/חזה/],['quarters','כרעיים',/כרע/],['thighs','ירכיים',/ירכ/],['drums','שוקיים',/שוק/],['wings','כנפיים',/כנפ/],['liver','כבד',/כבד/],['hearts','לבבות',/לבב/],['whole','עוף שלם',/שלם|עוף מס/]].find(x=>x[2].test(n));
   if(cut){let state=/קפוא/.test(n)?'קפוא':'טרי',bone=/ללא עצם|בלי עצם/.test(n)?' ללא עצם':'',skin=/ללא עור|בלי עור/.test(n)?' ללא עור':'';return ['chicken-'+cut[0]+'-'+state+bone+skin,cut[1]+' עוף '+state+bone+skin];}
  }
 }
 return ['exact-'+normalize(p.name)+'|'+p.quantity+'|'+p.unit_quantity+'|'+p.weighted+'|'+p.calculation_unit+'|'+normalize(p.manufacturer),p.name];
}
function group(products){const m=new Map;for(const p of products){const [key,label]=category(p);if(!m.has(key))m.set(key,{key,name:label,products:[],branches:new Set});const g=m.get(key);g.products.push(p);for(const b of p.branch_ids||[])g.branches.add(b);}return [...m.values()].map(g=>({...g,branch_ids:[...g.branches],offer_count:g.branches.size,search_text:g.products.map(p=>p.search_text||p.name).join(' ').replace(/עגבנייה|עגבניית|עגבניות|עגבנית/g,'עגבניה')}));}
const api={normalize,category,group};if(typeof module!=='undefined')module.exports=api;root.SuperProductGroups=api;
})(typeof window==='undefined'?globalThis:window);
