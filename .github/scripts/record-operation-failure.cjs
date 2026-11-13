'use strict';
const RECORDER='Record operation failures';
function incidentFor(run, repo, capturedAt) {
  if (!run || run.name===RECORDER || !['failure','timed_out','startup_failure','action_required'].includes(run.conclusion)) return null;
  if (!Number.isSafeInteger(run.id)||run.id<1) throw Error('Invalid workflow run ID');
  const attempt=run.run_attempt||1;
  if (!Number.isSafeInteger(attempt)||attempt<1) throw Error('Invalid run attempt');
  return {schema_version:1,incident_key:`github:${repo}:${run.id}:${attempt}`,status:'new',repository:repo,run_id:run.id,attempt,workflow:run.name,conclusion:run.conclusion,source_commit:run.head_sha,branch:run.head_branch,created_at:run.created_at,completed_at:run.updated_at,captured_at:capturedAt,url:`https://github.com/${repo}/actions/runs/${run.id}`,failed_jobs:[]};
}
async function record({github,context,core}) {
  const repo=`${context.repo.owner}/${context.repo.repo}`;
  const incident=incidentFor(context.payload.workflow_run,repo,new Date().toISOString());
  if (!incident) return {status:'skipped'};
  const path=`ops/incident-response/inbox/${incident.run_id}-${incident.attempt}.json`;
  try { await github.rest.repos.getContent({...context.repo,path,ref:'main'});return {status:'already_recorded'}; }
  catch(e) { if(e.status!==404) throw e; }
  const jobs=await github.paginate(github.rest.actions.listJobsForWorkflowRun,{...context.repo,run_id:incident.run_id,filter:'latest',per_page:100});
  incident.failed_jobs=jobs.filter(j=>['failure','timed_out','action_required'].includes(j.conclusion)).map(j=>({id:j.id,name:j.name,conclusion:j.conclusion,failed_steps:(j.steps||[]).filter(s=>s.conclusion==='failure').map(s=>({name:s.name,number:s.number}))}));
  // Metadata only. Never execute failing-run code, download artifacts, or copy raw logs/secrets.
  await github.rest.repos.createOrUpdateFileContents({...context.repo,path,branch:'main',message:`Record operation incident ${incident.run_id} attempt ${incident.attempt}`,content:Buffer.from(JSON.stringify(incident,null,2)+'\n').toString('base64')});
  core.info(`Recorded workflow failure ${incident.run_id}; diagnosis remains pending.`);
  return {status:'recorded',path};
}
module.exports={incidentFor,record};
