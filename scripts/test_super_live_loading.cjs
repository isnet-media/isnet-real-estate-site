// A slow catalogue must not throw on search or replace an existing shopping list.
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const elements=new Map;let writes=0,dialogs=[];
const element=s=>{if(!elements.has(s))elements.set(s,{innerHTML:'',textContent:'',value:'',style:{},addEventListener(){}});return elements.get(s)};
const context={window:{addEventListener(){}},document:{querySelector:element},localStorage:{getItem:()=>JSON.stringify({'7290004131074':2}),setItem:()=>writes++},fetch:()=>new Promise(()=>{}),location:{hash:''},modal:html=>dialogs.push(html),console};
vm.createContext(context);vm.runInContext(fs.readFileSync('SUPER.ASHDOD/live.js','utf8'),context);
context.window.renderProducts('milk');assert.match(element('#productList').innerHTML,/טוענים/);
context.window.searchProducts('milk');assert.equal(context.location.hash,'products');
context.window.loadSample();assert.equal(writes,0);assert.match(dialogs.pop(),/הרשימה השמורה/);
(async()=>{await context.window.compareCart();assert.equal(writes,0);assert.match(dialogs.pop(),/הרשימה השמורה/);console.log('Verified slow catalogue search, safe sample action and preserved stored shopping list')})().catch(e=>{console.error(e);process.exitCode=1});
