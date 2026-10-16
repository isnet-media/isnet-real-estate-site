const assert=require('node:assert/strict'),S=require('../events-preview/shared/saved-list.js');
const url=S.link('https://isnet.co.il/events-preview/ashdod/?category=kids#cinema',['one','two','one']);
assert.equal(new URL(url).search,'');assert.deepEqual(S.decode(new URL(url).hash),['one','two']);
assert.equal(S.decode('#cinema'),null);assert.equal(S.decode('#saved=invalid'),null);
assert.deepEqual(S.clean(['ok','<script>',null,'../bad','ok']),['ok']);
assert.throws(()=>S.link('https://isnet.co.il/',[]),/EMPTY_LIST/);
assert.throws(()=>S.link('https://isnet.co.il/',Array.from({length:101},(_,i)=>'id'+i)),/LIST_TOO_LONG/);
console.log('PASS: shared snapshots, deduplication, malformed input, no filter leakage, bounded URLs');

const fs=require('fs'),vm=require('vm'),nodes=new Map(),node=id=>{if(!nodes.has(id))nodes.set(id,{});return nodes.get(id)};
const app=fs.readFileSync('events-preview/ashdod/pilot/app.js','utf8');
const context=vm.createContext({state:{query:'',category:null,subcategory:null,favoritesOnly:true,cinema:[]},sharedSaved:null,filtered:()=>[{event_id:'saved-one'}],eventCard:e=>'<article>'+e.event_id+'</article>',$:node,document:{querySelectorAll:()=>[]},window:{publicTaxonomy:[]}});
vm.runInContext(app.slice(app.indexOf('function renderResults(){'),app.indexOf('function render(){')),context);
context.renderResults();assert(node('eventsGrid').innerHTML.includes('saved-one'));assert(!node('eventsGrid').hidden);
context.state.favoritesOnly=false;context.sharedSaved=['saved-one'];context.renderResults();assert(node('eventsGrid').innerHTML.includes('saved-one'));
console.log('PASS: a one-event saved/shared list is visible instead of being removed by home category thresholds');
