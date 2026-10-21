const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {parseHTML}=require('linkedom');
async function page(dir,name,search=''){
 const {document}=parseHTML(fs.readFileSync(path.join(dir,name),'utf8'));
 for(const el of document.querySelectorAll('select'))Object.defineProperty(el,'value',{value:'',writable:true});
 vm.runInNewContext(fs.readFileSync(path.join(dir,'app.js'),'utf8'),{document,location:{search},URLSearchParams,fetch:async u=>({ok:true,json:async()=>JSON.parse(fs.readFileSync(path.join(dir,u)))})});
 await new Promise(setImmediate);await new Promise(setImmediate);return document;
}
(async()=>{
 for(const city of ['yavne','rishon-lezion']){
  const dir=path.resolve(__dirname,'../meusharim',city),records=JSON.parse(fs.readFileSync(path.join(dir,'data/classes.json'))).records;
  const home=await page(dir,'index.html'),links=[...home.querySelectorAll('#shortcuts > a')];
  assert.equal(links.length,new Set(records.map(r=>r.category)).size);
  for(const link of links){
   const target=new URL(link.getAttribute('href'),'https://isnet.co.il/meusharim/'+city+'/');assert(target.pathname.endsWith('/catalog.html'));
   const cat=target.searchParams.get('category');assert(cat);
   const landing=await page(dir,'catalog.html',target.search);const expected=records.filter(r=>r.category===cat).length;
   assert(landing.querySelector('#count').textContent.startsWith(String(expected)+' '),city+' '+cat);
   assert(landing.querySelector('#results article'),city+' '+cat+' empty');
  }
  console.log('PASS:',city,links.length,'category links open catalog pages with matching course results');
 }
})().catch(e=>{console.error(e);process.exit(1)});
