const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const src=fs.readFileSync('assets/yavne-analytics.js','utf8');
for(const [path,group] of [['/events-preview/yavne/event.html','events_yavne'],['/SUPER.YAVNE/compare/','super_yavne'],['/meusharim/yavne/course.html','classes_yavne']]){
 const tags=[],window={},location={pathname:path,href:'https://isnet.co.il'+path+'?q=private%40example.com#private'};
 const document={title:'יבנה',referrer:'https://www.yavnenet.co.il/?q=secret',querySelector(){return null},createElement(){return {}},head:{appendChild(x){tags.push(x)}}};
 const ctx={window,document,location,URL,Set,Date};vm.runInNewContext(src,ctx);vm.runInNewContext(src,ctx);
 assert.equal(tags.length,1);assert(tags[0].src.endsWith('G-JLRT7GKSXB'));
 const configs=window.dataLayer.filter(x=>x[0]==='config');assert.equal(configs.length,1);assert.equal(configs[0][1],'G-JLRT7GKSXB');assert.equal(configs[0][2].send_page_view,false);
 const views=window.dataLayer.filter(x=>x[1]==='page_view');assert.equal(views.length,1);assert.equal(views[0][2].content_group,group);assert.equal(views[0][2].page_location,'https://isnet.co.il'+path);
 window.yavneAnalytics.send('search',{search_term:'private@example.com',email:'secret',result_count:5});window.yavneAnalytics.send('unknown',{shopping_list:'secret'});
 const searches=window.dataLayer.filter(x=>x[1]==='search');assert.equal(searches.length,1);assert.equal(searches[0][2].search_term,'[withheld]');assert.equal(searches[0][2].result_count,5);assert(!('email' in searches[0][2]));
 assert(!JSON.stringify(window.dataLayer).includes('secret'));assert(!JSON.stringify(window.dataLayer).includes('private'));
}
for(const pathname of ['/SUPER.ASHDOD/','/SUPER.KGAT/','/events-preview/rishon-lezion/','/meusharim/ashdod/']){
 const window={};vm.runInNewContext(src,{window,location:{pathname},URL,Set});assert.equal(window.dataLayer,undefined);
}
console.log('PASS Yavne GA4: correct stream and content groups; one initial page view; search/list privacy; no other-city tracking');
