const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const {parseHTML}=require('linkedom');
const registry=JSON.parse(fs.readFileSync('events-preview/shared/data/movie-editorial.json','utf8'));
const pages=JSON.parse(fs.readFileSync('events-preview/shared/data/movie-page-index.json','utf8'));
const {window,document}=parseHTML('<html><body><section><p id="fullSynopsis"></p></section></body></html>');
const context={window,document,location:{pathname:'/events-preview/ashdod/cinema.html',origin:'https://isnet.co.il'},URL,console,fetch:async url=>({ok:true,json:async()=>url.includes('movie-page-index')?pages:registry})};
vm.runInNewContext(fs.readFileSync('events-preview/shared/cinema-editorial.js','utf8'),context);
(async()=>{const api=window.CinemaEditorial;await api.ready;
for(const city of Object.keys(pages)){
 const feed=JSON.parse(fs.readFileSync('events-preview/'+city+'/data/cinema.json','utf8')).movies;
 const result=api.unique(feed);assert.equal(result.length,new Set(feed.map(m=>api.key(m.id))).size);
 for(const m of feed){const merged=api.merge(feed,m.id);assert(merged);assert.equal(merged.editorial_text,registry.movies[api.key(m.id)].original_text);assert.equal(api.url(m.id,city),pages[city][m.id]);
  for(const v of m.venues)for(const [date,times] of Object.entries(v.schedule||{}))for(const time of times)assert(merged.venues.find(x=>x.id===v.id).schedule[date].includes(time));
 }
}
api.mount({id:'our-loves'});assert.equal(document.getElementById('fullSynopsis').textContent,registry.movies['our-loves'].original_text);assert(document.getElementById('movieEditorial').textContent.includes(registry.movies['our-loves'].audience_rating.value+'/10'));
assert(document.querySelector('#movieEditorial a[href="https://www.seret.co.il/movies/s_movies.asp?MID=8593"]'));
assert.equal(api.merge([],'missing'),null);console.log('PASS: city aliases, merged showtimes, canonical destinations, original text and attributed audience grade');
})().catch(e=>{console.error(e);process.exitCode=1});
