/* Apply only to staged public HTML, after every page generator has finished. */
const fs = require('node:fs');
const path = require('node:path');
const CLIENT = 'ca-pub-3043177344534285';
const RECORD = 'google.com, pub-3043177344534285, DIRECT, f08c47fec0942fa0';
const TAG = `<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${CLIENT}"\n     crossorigin="anonymous"></script>`;
// Prepared placements stay invisible until Google's site review is complete.
// Report by AdSense Site + Ad unit; unit names include the domain and section.
const UNITS = {astrology:'8903576192',events:'9688055155',supermarket:'7498995184'};
function preparePlacement(html, rel) {
  const section = rel==='astrology/index.html' ? 'astrology' :
    /^events-preview\/[^/]+\/index\.html$/.test(rel) ? 'events' :
    /^SUPER\.[A-Z]+\/index\.html$/.test(rel) ? 'supermarket' : null;
  if(!section || html.includes('data-isnet-ad-placement=')) return html;
  const city=rel.split('/')[0]==='events-preview'?rel.split('/')[1]:rel.split('/')[0];
  const block=`\n<section hidden data-isnet-ad-placement="${section}" data-ad-site="isnet.co.il" data-ad-edition="${city}" data-ad-state="prepared-pending-site-approval" aria-label="פרסומת" style="box-sizing:border-box;width:100%;max-width:970px;margin:32px auto;overflow:hidden"><ins class="adsbygoogle" style="display:block" data-ad-client="${CLIENT}" data-ad-slot="${UNITS[section]}" data-ad-format="auto" data-full-width-responsive="true"></ins></section>\n`;
  // End of the reading area, outside navigation/forms; no anchor or overlay.
  return /<\/main>/i.test(html)?html.replace(/<\/main>/i,block+'</main>'):html.replace(/<\/body>/i,block+'</body>');
}
function apply(root) {
  const report = {added: [], existing: [], review: [], fragments: []};
  function walk(dir) {
    for (const item of fs.readdirSync(dir, {withFileTypes:true})) {
      if (item.isSymbolicLink()) throw Error('Symlink in public output');
      const file = path.join(dir,item.name);
      if (item.isDirectory()) {walk(file); continue;}
      if (!/\.html?$/i.test(item.name)) continue;
      const original = fs.readFileSync(file,'utf8'), rel = path.relative(root,file).replaceAll('\\','/');
      const html = preparePlacement(original,rel);
      const head = html.match(/<head\b[^>]*>[\s\S]*?<\/head>/i);
      if (!head) {report.fragments.push(rel); continue;}
      const loaders = html.match(/<script\b[^>]*\bsrc\s*=\s*["'][^"']*adsbygoogle\.js[^"']*["'][^>]*>/gi) || [];
      if (loaders.length) {
        if (loaders.length===1 && head[0].includes(loaders[0]) && loaders[0].includes(CLIENT)) {report.existing.push(rel);if(html!==original)fs.writeFileSync(file,html);}
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
