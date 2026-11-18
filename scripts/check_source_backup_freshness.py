"""Read-only daily check of GitHub source backup artifact freshness.

Checks existing workflow's latest successful run and its unexpired artifact.
Does not download data, create a backup, or verify external/offsite copies.
"""
import json
import os
import sys
from datetime import datetime,timezone
from urllib.request import Request,urlopen

def latest_backup(repo, token, now=None):
    if not repo or not token:raise RuntimeError("GITHUB_REPOSITORY and GITHUB_TOKEN required")
    now=now or datetime.now(timezone.utc)
    def get(path):
        req=Request("https://api.github.com/repos/"+repo+path,headers={
            "Authorization":"Bearer "+token,"Accept":"application/vnd.github+json",
            "User-Agent":"ISNET-backup-readiness/1.0"})
        with urlopen(req,timeout=20) as r:return json.load(r)
    runs=get("/actions/workflows/daily-source-backup.yml/runs?per_page=15").get("workflow_runs",[])
    good=next((r for r in runs if r.get("status")=="completed" and r.get("conclusion")=="success"),None)
    if good is None:return {"ok":False,"reason":"no_recent_successful_backup"}
    age=(now-datetime.fromisoformat(good["created_at"].replace("Z","+00:00"))).total_seconds()/3600
    data=get("/actions/runs/"+str(good["id"])+"/artifacts")
    artifacts=[a for a in data.get("artifacts",[]) if a.get("name")=="isnet-source-backup-"+str(good["id"]) and not a.get("expired") and a.get("size_in_bytes",0)>0]
    return {"ok":age<=36 and bool(artifacts),"run_id":good["id"],"age_hours":round(age,1),"artifact_count":len(artifacts),"reason":"healthy" if age<=36 and artifacts else "backup_too_old_or_artifact_missing"}
if __name__=="__main__":
    try:res=latest_backup(os.environ.get("GITHUB_REPOSITORY"),os.environ.get("GITHUB_TOKEN"))
    except Exception as e:res={"ok":False,"reason":"backup_check_failed","exception":type(e).__name__}
    print(json.dumps(res))
    sys.exit(0 if res["ok"] else 1)
