const assert=require('node:assert/strict');
const {plan}=require('./storage-housekeeping.cjs');
const now=Date.parse('2026-11-10T12:00:00Z');
const runs=new Map();let id=0;
function artifact(name,status='completed',conclusion='success',days=1,workflow='Publish priceboard',attempt=1){id++;runs.set(id,{id,name:workflow,status,conclusion,run_attempt:attempt});return{id,name:name.replace('ID',id),workflow_run:{id},expired:false,created_at:new Date(now-days*86400000).toISOString(),size_in_bytes:100};}
const a=[artifact('github-pages-ID-1','completed','success',1),artifact('github-pages-ID-1','completed','success',2),artifact('github-pages-ID-1','completed','success',3),artifact('github-pages-ID-1','completed','failure',4),artifact('github-pages-ID-1','in_progress',null,5),artifact('isnet-source-backup-ID','completed','success',10),artifact('unknown-ID','completed','success',10),artifact('ashdod-supermarket-ID','completed','success',10,'Refresh Ashdod supermarket prices'),artifact('supermarket-refresh-ID','completed','success',1,'Refresh Ashdod supermarket prices'),artifact('supermarket-refresh-ID','completed','failure',20,'Refresh Yavne supermarket prices'),artifact('github-pages-ID-1','completed','success',15,'Publish priceboard',2)];
const result=plan(a,runs,now);assert.deepEqual(result.remove.map(x=>x.id).sort((a,b)=>a-b),[3,8]);assert.deepEqual(result.protectedRuns,[1,2]);
assert.equal(plan([a[0]],runs,now).remove.length,0);assert.equal(plan(a,new Map(),now).remove.length,0);
console.log('PASS: retain two successes, backups, failures, active and unknown artifacts; retain latest city evidence and unmatched attempts');
