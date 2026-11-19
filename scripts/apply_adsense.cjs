/* Apply only to staged public HTML, after every page generator has finished. */
const fs = require('node:fs');
const path = require('node:path');
const CLIENT = 'ca-pub-3043177344534285';
const RECORD = 'google.com, pub-3043177344534285, DIRECT, f08c47fec0942fa0';
const TAG = `<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${CLIENT}"\n     crossorigin="anonymous"></script>`;
function apply(root) {
  const report = {added: [], existing: [], review: [], fragments: []};
  function walk(dir) {
    for (const item of fs.readdirSync(dir, {withFileTypes:true})) {
      if (item.isSymbolicLink()) throw Error('Symlink in public output');
      const file = path.join(dir,item.name);
      if (item.isDirectory()) {walk(file); continue;}
      if (!/\.html?$/i.test(item.name)) continue;
      const html = fs.readFileSync(file,'utf8'), rel = path.relative(root,file).replaceAll('\\','/');
      const head = html.match(/<head\b[^>]*>[\s\S]*?<\/head>/i);
      if (!head) {report.fragments.push(rel); continue;}
      const loaders = html.match(/<script\b[^>]*\bsrc\s*=\s*["'][^"']*adsbygoogle\.js[^"']*["'][^>]*>/gi) || [];
      if (loaders.length) {
        if (loaders.length===1 && head[0].includes(loaders[0]) && loaders[0].includes(CLIENT)) report.existing.push(rel);
        else report.review.push(rel);
        continue;
      }
      fs.writeFileSync(file,html.replace(/<head\b[^>]*>/i,m=>m+'\n'+TAG+'\n'));
      report.added.push(rel);
    }
  }
  walk(root);
  const ads = path.join(root,'ads.txt');
  let text = fs.existsSync(ads) ? fs.readFileSync(ads,'utf8') : '';
  if (!/^\s*google\.com\s*,\s*pub-3043177344534285\s*,\s*DIRECT\s*,\s*f08c47fec0942fa0\s*(?:#.*)?$/im.test(text)) {
    fs.writeFileSync(ads,text+(text&&!text.endsWith('\n')?'\n':'')+RECORD+'\n');
  }
  if (report.review.length) throw Error('AdSense loaders need manual ownership/duplicate review: '+report.review.join(', '));
  console.log(JSON.stringify({adsense:CLIENT,...Object.fromEntries(Object.entries(report).map(([k,v])=>[k,v.length]))}));
  return report;
}
module.exports={apply,TAG,RECORD};
if(require.main===module) {if(!process.argv[2]) throw Error('Public staging directory is required');apply(path.resolve(process.argv[2]));}
