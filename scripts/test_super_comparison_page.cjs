// Branch ranking and the public gap must use one verified, cheapest offer per branch.
const assert=require('node:assert/strict'),fs=require('node:fs');
const {summarize,searchRank}=require('../SUPER.ASHDOD/assets/compare-page.js');
const branches=['a','b','c','d'].map(id=>({id,name:id}));
const product=(id,offers,calculation_unit='package')=>({id,name:id,calculation_unit,offers});
const offer=(branch_id,price,extra={})=>({branch_id,price,calculation_unit:'package',...extra});
let s=summarize([product('brand-one',[offer('a',10),offer('b',15),offer('c',30),offer('missing',1)]),product('brand-two',[offer('a',12),offer('b',12),offer('c',20),offer('d',0),offer('d',1,{eligible_for_basket:false}),offer('d',2,{calculation_unit:'kg'})])],branches);
assert.deepEqual(s.ranked.map(r=>[r.branch.id,r.best.o.price]),[['a',10],['b',12],['c',20]]);
assert.equal(s.max,20);assert.equal(s.gap,10);assert.equal(s.percent,100);assert.equal(s.ranked[2].offers.length,2);
s=summarize([product('one',[offer('a',3.9),offer('b',5.9)])],branches);assert.equal(s.gap,2);assert.ok(Math.abs(s.percent-51.282051)<0.00001);
s=summarize([product('one',[offer('a',10)])],branches);assert.equal(s.gap,null);assert.equal(s.percent,null);
s=summarize([product('one',[offer('a',10),offer('b',10)])],branches);assert.equal(s.gap,0);assert.equal(s.percent,0);
s=summarize([product('one',[offer('a',NaN),offer('b',Infinity)]),product('unknown',[offer('c',7)],'unknown')],branches);assert.equal(s.ranked.length,0);
const page=fs.readFileSync('SUPER.ASHDOD/compare/index.html','utf8');assert.match(page,/SUPER_SHELL_START/);assert.match(page,/productQuery/);
assert.match(fs.readFileSync('SUPER.ASHDOD/live.js','utf8'),/compare\/\?product=/);
console.log('Verified per-branch minimums, sorting, gap denominator, invalid units, missing branches, ties and single-branch state');

assert.ok(searchRank({name:'עגבנייה רגילה',key:'tomato-regular'},'עגבניה')<searchRank({name:'עגבניה מרוסקות · 800 גרם',key:'catalogue-x'},'עגבניה'));
assert.ok(searchRank({name:'אורז פרסי · 1 ק״ג',key:'rice'},'אורז פרסי')<searchRank({name:'רוטב לאורז פרסי',key:'sauce'},'אורז פרסי'));
