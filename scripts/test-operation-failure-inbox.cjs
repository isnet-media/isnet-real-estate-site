const assert=require('node:assert/strict');
const {incidentFor,record}=require('../.github/scripts/record-operation-failure.cjs');
const run={id:123,run_attempt:2,name:'Publish priceboard',conclusion:'failure',head_sha:'a'.repeat(40),head_branch:'main'};
assert.equal(incidentFor({...run,conclusion:'success'},'owner/repo','now'),null);
assert.equal(incidentFor({...run,name:'Record operation failures'},'owner/repo','now'),null);
assert.throws(()=>incidentFor({...run,id:'../../bad'},'owner/repo','now'));
assert.equal(incidentFor(run,'owner/repo','now').incident_key,'github:owner/repo:123:2');
let writes=[];const context={repo:{owner:'owner',repo:'repo'},payload:{workflow_run:run}};
const github={rest:{repos:{getContent:async()=>{throw Object.assign(Error('missing'),{status:404})},createOrUpdateFileContents:async a=>writes.push(a)},actions:{listJobsForWorkflowRun:()=>{}}},paginate:async()=>[{id:7,name:'deploy',conclusion:'failure',steps:[{name:'test',number:4,conclusion:'failure'},{name:'done',conclusion:'success'}]}]};
(async()=>{
 const core={info:()=>{}};await record({github,context,core});
 assert.equal(writes.length,1);assert.equal(writes[0].path,'ops/incident-response/inbox/123-2.json');
 const saved=JSON.parse(Buffer.from(writes[0].content,'base64'));assert.equal(saved.failed_jobs[0].failed_steps.length,1);assert(!('logs' in saved));
 github.rest.repos.getContent=async()=>({data:{}});await record({github,context,core});assert.equal(writes.length,1,'No duplicate incident write');
 github.rest.repos.getContent=async()=>{throw Object.assign(Error('forbidden'),{status:403})};await assert.rejects(record({github,context,core}),/forbidden/);
 console.log('PASS: failure-only capture, attempt identity, no recursive capture, metadata-only evidence, idempotence and real permission errors');
})().catch(e=>{console.error(e);process.exitCode=1});
