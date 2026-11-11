"""Small immutable private delta canary from committed supermarket collector output.

This DOES NOT invoke collectors, replace pinned releases, alter production, or
approve/publicly serve partial data. 3 critical JSON files per changed city only.
"""
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
from super_committed_delta_preflight import PINNED, REQUIRED, validate_status, blob, git

PROJECT = "qomkxhafrprooekwgsxf"
BUCKET = "isnet-super-staging"
BASE = f"https://{PROJECT}.supabase.co"
# Explicit canary scope: do not expand without reviewing committed-source gates.
CITIES = ("ASHDOD", "KGAT", "YAVNE")
MAX_JSON = 256 * 1024

def validate_delta(city, source_sha, now=None):
    if city not in CITIES: raise ValueError("City is not in approved private delta canary")
    if not re.fullmatch(r"[a-f0-9]{40}", source_sha): raise ValueError("Source must be exact commit")
    origin = PINNED[city]
    now = now or datetime.now(timezone.utc)
    old = json.loads(blob(origin,city,"data/refresh-status.json"))
    latest = json.loads(blob(source_sha,city,"data/refresh-status.json"))
    prev_time = validate_status(old)
    check_time = validate_status(latest)
    if check_time <= prev_time or check_time > now + timedelta(minutes=5):
        raise ValueError("Refusing stale, regressed or future source timestamps")
    files = {}
    for name in REQUIRED:
        new = blob(source_sha,city,name)
        old_bytes=blob(origin,city,name)
        if len(new)<2 or len(new)>MAX_JSON:raise ValueError("Critical JSON exceeds private canary limit")
        value=json.loads(new.decode("utf-8"))
        if not isinstance(value,dict):raise ValueError("Critical JSON must be object")
        files[name]=new
        # All three critical files must be from one fully committed city edition.
        if new==old_bytes: raise ValueError("Expected changed committed critical JSON: "+name)
    prices=json.loads(files["data/prices.json"])
    source=json.loads(files["data/source-status.json"])
    if prices.get("branch_count")!=latest["branch_count"]:
        raise ValueError("Price count and refresh provenance disagree")
    if prices.get("coverage_complete") is not latest["all_sources_updated"]:
        raise ValueError("Price coverage flag disagrees with refresh provenance")
    if prices.get("retrieved_at")!=latest["checked_at"]:
        raise ValueError("Price retrieval timestamp disagrees with refresh provenance")
    if source.get("updated_at")!=check_time.astimezone(timezone(timedelta(hours=2))).date().isoformat():
        # This is an operational consistency check, not a statement that EVERY source is fresh.
        raise ValueError("Source status date differs from committed collector date")
    return files, latest

def request(method, path, key, raw=None, content_type=None):
    headers={"apikey":key,"Authorization":"Bearer "+key}
    if content_type:headers["Content-Type"]=content_type
    req=Request(BASE+"/storage/v1/object/"+path,headers=headers,method=method,data=raw)
    with urlopen(req,timeout=45) as response:
        body=response.read(MAX_JSON+1)
        if len(body)>MAX_JSON and method=="GET":
            raise RuntimeError("Private readback exceeded limit")
        return body

def stage_file(path, raw, key):
    target=quote(BUCKET+"/"+path,safe="/")
    private="authenticated/"+target
    expected=hashlib.sha256(raw).hexdigest()
    try:
        existing=request("GET",private,key)
    except HTTPError as e:
        # Storage may return 400 with a missing-object error.
        err=e.read().decode("utf-8","replace").lower()[:450]
        if e.code not in (400,404) or (e.code==400 and not ("not found" in err or "does not exist" in err)):
            raise RuntimeError("Unexpected private object read error HTTP "+str(e.code)) from None
        existing=None
    if existing is None:
        try:request("POST",target,key,raw,"application/json")
        except HTTPError as e:
            # Ambiguous duplicate response is accepted only after byte-for-byte readback.
            if e.code not in (400,409):raise RuntimeError("Private write failed HTTP "+str(e.code)) from None
        existing=request("GET",private,key)
    if existing != raw or hashlib.sha256(existing).hexdigest()!=expected:
        raise RuntimeError("Immutable delta mismatch; never overwrite "+path)
    return expected

def main():
    key=os.getenv("SUPABASE_SERVICE_ROLE_KEY","")
    if os.getenv("SUPABASE_URL","").rstrip("/")!=BASE or not key:
        raise RuntimeError("Expected private Supabase project credentials only")
    # Pin one verified main commit even when collectors continue working.
    main_sha=git("rev-parse","origin/main").decode().strip()
    if not re.fullmatch("[a-f0-9]{40}",main_sha):raise RuntimeError("Bad origin/main ref")
    summary=[]
    for city in CITIES:
        files,status=validate_delta(city,main_sha)
        prefix=f"previews/committed-deltas/{city}/{main_sha}/"
        manifest={
            "format":"isnet-super-committed-private-delta-v1",
            "city":city, "source_commit":main_sha, "baseline_release":PINNED[city],
            "source_checked_at":status["checked_at"],
            "updated_branches":status["updated_count"],
            "total_branches":status["branch_count"],
            "coverage_status":status.get("coverage_status"),
            "all_sources_updated":status["all_sources_updated"],
            "private":True,"public_cutover":False,
            "approved_for_public":False,
            "collector_invoked":False,
            "files":[]
        }
        for rel,data in files.items():
            sha=stage_file(prefix+rel,data,key)
            manifest["files"].append({"path":rel,"sha256":sha,"bytes":len(data)})
        raw=(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
        stage_file(prefix+"delta-manifest.json",raw,key)
        summary.append({k:v for k,v in manifest.items() if k!="files"})
    print(json.dumps({"success":True,"staged_cities":summary,"public_cutover":False},ensure_ascii=False))

if __name__=="__main__":main()
