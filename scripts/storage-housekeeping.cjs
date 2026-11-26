'use strict';
const DAY=86400000;
function plan(artifacts,runs,now=Date.now()) {
  const current=artifacts.filter(a=>!a.expired);
  const known=a=>runs.get(a.workflow_run?.id);
  const success=a=>{const r=known(a);return r?.status==='completed'&&r.conclusion==='success';};
  const pages=current.filter(a=>/^github-pages-\d+-\d+$/.test(a.name)&&success(a)&&known(a).name==='Publish priceboard');
  const newestRuns=[...new Set(pages.sort((a,b)=>Date.parse(b.created_at)-Date.parse(a.created_at)).map(a=>a.workflow_run.id))].slice(0,2);
  const protectedRuns=new Set(newestRuns),latestEvidence=new Map();
  for(const a of current){const r=known(a);if(!r||!/supermarket prices$/.test(r.name))continue;const old=latestEvidence.get(r.name);if(!old||Date.parse(a.created_at)>Date.parse(old.created_at))latestEvidence.set(r.name,a);}
  const remove=[];
  for(const a of current){
    const r=known(a);if(!success(a)||!r)continue;
    const match=a.name.match(/^github-pages-(\d+)-(\d+)$/);
    if(match&&r.name==='Publish priceboard'){
      if(Number(match[2])!==Number(r.run_attempt)||protectedRuns.has(r.id))continue;
      remove.push(a);continue;
    }
    if(/^(supermarket-refresh-|(?:ashdod|yavne|kgat|rishon|holon|batyam|tlv)-supermarket-)/.test(a.name)&&/supermarket prices$/.test(r.name)&&now-Date.parse(a.created_at)>7*DAY&&latestEvidence.get(r.name)?.id!==a.id)remove.push(a);
  }
  return {remove,protectedRuns:newestRuns};
}
// Inventory is read-only: classify every retained artifact, even unknown and protected ones.
function inventory(artifacts) {
  const groups=new Map();
  const current=artifacts.filter(a=>!a.expired);
  for(const a of current){
    const name=String(a.name||'unnamed');
    const group=name.replace(/-\d{8,}(?:-\d+)?$/,'').replace(/-\d{4}-\d{2}-\d{2}$/,'');
    const entry=groups.get(group)||{group,count:0,bytes:0,oldest:null,newest:null};
    entry.count++;entry.bytes+=Number(a.size_in_bytes)||0;
    const created=a.created_at||null;
    if(created){if(!entry.oldest||created<entry.oldest)entry.oldest=created;if(!entry.newest||created>entry.newest)entry.newest=created;}
    groups.set(group,entry);
  }
  return {groups:[...groups.values()].sort((a,b)=>b.bytes-a.bytes),largest:current.slice().sort((a,b)=>b.size_in_bytes-a.size_in_bytes).slice(0,20).map(a=>({id:a.id,name:a.name,bytes:a.size_in_bytes,created:a.created_at,expires:a.expires_at,run:a.workflow_run?.id}))};
}
module.exports=async function({github,context,core}) {
  const repo=context.repo;
  const artifacts=await github.paginate(github.rest.actions.listArtifactsForRepo,{...repo,per_page:100});
  const runs=new Map();
  for(const a of artifacts){
    if(a.expired||!/^github-pages-\d+-\d+$|^supermarket-refresh-|^(?:ashdod|yavne|kgat|rishon|holon|batyam|tlv)-supermarket-/.test(a.name))continue;
    const id=a.workflow_run?.id;if(!id||runs.has(id))continue;
    const {data}=await github.rest.actions.getWorkflowRun({...repo,run_id:id});runs.set(id,data);
  }
  const p=plan(artifacts,runs);let deletedBytes=0,deletedCount=0;
  for(const a of p.remove){
    // Unknown, active, cancelled and failed runs and every source backup are excluded by plan.
    await github.rest.actions.deleteArtifact({...repo,artifact_id:a.id});
    deletedBytes+=a.size_in_bytes;deletedCount++;
    core.info(JSON.stringify({deleted_id:a.id,name:a.name,bytes:a.size_in_bytes}));
  }
  const remaining=await github.paginate(github.rest.actions.listArtifactsForRepo,{...repo,per_page:100});
  const retained=remaining.filter(a=>!a.expired);
  const report={deletedCount,deletedBytes,protectedSuccessfulRuns:p.protectedRuns,remainingCount:retained.length,remainingBytes:retained.reduce((n,a)=>n+a.size_in_bytes,0)};
  const detail=inventory(retained);
  core.info(JSON.stringify(report));core.info(JSON.stringify({storage_inventory:detail}));
  await core.summary.addHeading('Verified artifact housekeeping').addCodeBlock(JSON.stringify(report,null,2),'json')
    .addHeading('Retained storage by artifact family').addTable([[{data:'Artifact family',header:true},{data:'Count',header:true},{data:'Bytes',header:true},{data:'Oldest',header:true},{data:'Newest',header:true}],...detail.groups.map(g=>[g.group,String(g.count),String(g.bytes),g.oldest||'-',g.newest||'-'])])
    .addHeading('Largest retained artifacts (audit only)').addCodeBlock(JSON.stringify(detail.largest,null,2),'json').write();
};
module.exports.plan=plan;

module.exports.inventory=inventory;
