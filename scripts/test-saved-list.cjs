const assert=require('node:assert/strict'),S=require('../events-preview/shared/saved-list.js');
const url=S.link('https://isnet.co.il/events-preview/ashdod/?category=kids#cinema',['one','two','one']);
assert.equal(new URL(url).search,'');assert.deepEqual(S.decode(new URL(url).hash),['one','two']);
assert.equal(S.decode('#cinema'),null);assert.equal(S.decode('#saved=invalid'),null);
assert.deepEqual(S.clean(['ok','<script>',null,'../bad','ok']),['ok']);
assert.throws(()=>S.link('https://isnet.co.il/',[]),/EMPTY_LIST/);
assert.throws(()=>S.link('https://isnet.co.il/',Array.from({length:101},(_,i)=>'id'+i)),/LIST_TOO_LONG/);
console.log('PASS: shared snapshots, deduplication, malformed input, no filter leakage, bounded URLs');
