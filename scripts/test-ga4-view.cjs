const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const window={},location={pathname:'/events-preview/ashdod/event.html',href:'https://isnet.co.il/events-preview/ashdod/event.html?id=one',search:'',hash:''};
const document={title:'אירוע',referrer:'',querySelector(){return {}},addEventListener(){},head:{appendChild(){}}};
vm.runInNewContext(fs.readFileSync('events-preview/ashdod/ashdod-analytics.js','utf8'),{window,document,location,URL,URLSearchParams,Set,sessionStorage:{getItem(){return null}}});
window.ashdodAnalytics.send('view_item',{items:[{item_id:'one'}]});
assert.equal(window.dataLayer.filter(x=>x[0]==='event'&&x[1]==='view_item').length,1);
window.ashdodAnalytics.send('arbitrary_event',{});assert.equal(window.dataLayer.filter(x=>x[1]==='arbitrary_event').length,0);
assert(!window.ashdodAnalytics.safeSearch('ילדים 123 secret@example.com').includes('secret'));
console.log('PASS: shared GA4 bootstrap accepts event views, blocks unknown events and withholds private search terms');
