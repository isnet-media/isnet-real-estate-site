const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),assert=require('node:assert/strict');
const {apply,TAG,RECORD}=require('./apply_adsense.cjs');
const root=fs.mkdtempSync(path.join(os.tmpdir(),'isnet-adsense-'));
try {
  fs.writeFileSync(path.join(root,'index.html'),'<html><head><title>שלום</title></head><body><div class="OUTBRAIN">existing</div></body></html>');
  fs.writeFileSync(path.join(root,'fragment.html'),'<div>fragment</div>');
  fs.writeFileSync(path.join(root,'ads.txt'),'example.com, 123, DIRECT');
  assert.equal(apply(root).added.length,1);
  const once=fs.readFileSync(path.join(root,'index.html'),'utf8');
  assert(once.includes(TAG));assert(once.includes('<div class="OUTBRAIN">existing</div>'));
  assert.equal(apply(root).existing.length,1);assert.equal(fs.readFileSync(path.join(root,'index.html'),'utf8'),once);
  assert.equal(fs.readFileSync(path.join(root,'ads.txt'),'utf8'),'example.com, 123, DIRECT\n'+RECORD+'\n');
  fs.mkdirSync(path.join(root,'astrology'));fs.writeFileSync(path.join(root,'astrology/index.html'),'<head></head><body><main>תוכן</main></body>');
  apply(root);const prepared=fs.readFileSync(path.join(root,'astrology/index.html'),'utf8');
  assert(prepared.includes('<section hidden data-isnet-ad-placement="astrology"'));assert(prepared.includes('8903576192'));assert(!prepared.includes('.push('));
  apply(root);assert.equal(fs.readFileSync(path.join(root,'astrology/index.html'),'utf8'),prepared);
  const foreign='<head><script src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-123"></script></head>';
  fs.writeFileSync(path.join(root,'foreign.html'),foreign);assert.throws(()=>apply(root),/manual ownership/);assert.equal(fs.readFileSync(path.join(root,'foreign.html'),'utf8'),foreign);
  console.log('PASS: head placement, idempotency, publisher preservation, existing ads.txt, Outbrain and fragments');
} finally {fs.rmSync(root,{recursive:true,force:true});}
