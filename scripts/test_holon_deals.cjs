const assert=require('node:assert/strict');
const {active,diverse}=require('../SUPER.HOLON/assets/super-deals.js');
// Start/end hour fields duplicate the endpoints of the full date-time period.
// They must not hide a multi-day Shufersal offer outside a supposed daily 00:00–02:59 window.
const offer={start:'2026-10-18T00:00:00+03:00',end:'2026-10-23T02:59:00+03:00',start_hour:'00:00:00.000',end_hour:'02:59:00.000'};
assert(active(offer,Date.parse('2026-10-22T21:00:00+03:00')));
assert(!active(offer,Date.parse('2026-10-23T03:00:00+03:00')));
assert(!active(offer,Date.parse('2026-10-17T23:59:00+03:00')));
const data=require('../SUPER.HOLON/data/deals.json');
const catalog=require('../SUPER.HOLON/data/catalog.json');
const branches=new Set(catalog.branches.map(b=>b.id));
assert(data.city==='חולון'&&data.deals.length>=24);
assert(data.deals.every(d=>branches.has(d.branch_id)&&d.price>0&&d.price<d.shelf_price&&Number.isFinite(d.price)));
const reordered=diverse(data.deals);assert(reordered.length===data.deals.length);
assert(new Set(reordered.slice(0,11).map(d=>d.chain)).size>=4);
console.log('Holon promotions verified: full validity periods, finite savings, local branch identities and diverse ordering');
