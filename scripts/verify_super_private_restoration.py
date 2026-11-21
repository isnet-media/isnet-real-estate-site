"""Read-only release verification and nonproduction restore rehearsal.

Validates a pinned private Storage manifest against the exact original Git tree,
authenticates critical readbacks, ensures public Storage reads are denied, and
reconstructs the entire city from the pinned Git commit into a TEMP directory.
No database writes, collector jobs, DNS, or live public cutover.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

PROJECT = "qomkxhafrprooekwgsxf"
BUCKET = "isnet-super-staging"
SIX_RELEASE = "5958cfaca9a61eacfdb1aa216635c3d3ff810850"
RELEASES = dict.fromkeys(("ASHDOD", "BATYAM", "HOLON", "KGAT", "RISHON", "YAVNE"), SIX_RELEASE)
RELEASES["TLV"] = "c674f83485453570106ce39a55c9c66f3a061ec3"
ROOT = Path(__file__).resolve().parents[1]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git_tree(rev, city):
    return subprocess.check_output(
        ["git", "rev-parse", rev+":SUPER."+city], cwd=ROOT, text=True
    ).strip()

def fetch(url, secret=None):
    headers = {"User-Agent":"ISNET-release-readback/1.0"}
    if secret:
        headers.update({"apikey": secret, "Authorization":"Bearer "+secret})
    req = Request(url, headers=headers, method="GET")
    with urlopen(req, timeout=60) as response:
        return response.read()

def audit(city):
    if city not in RELEASES:
        raise ValueError("Unrecognized city")
    release = RELEASES[city]
    base = os.environ.get("SUPABASE_URL","").rstrip("/")
    secret = os.environ.get("SUPABASE_SERVICE_ROLE_KEY","")
    if base != "https://"+PROJECT+".supabase.co" or not secret:
        raise RuntimeError("Only approved private Supabase project is accepted")
    if git_tree("HEAD",city) != git_tree(release,city):
        raise RuntimeError("City source Git tree changed: do not silently reuse pinned release")
    prefix = "releases/"+city+"/"+release+"/"
    def private_object(name):
        url=base+"/storage/v1/object/authenticated/"+BUCKET+"/"+quote(prefix+name,safe="/")
        return fetch(url,secret)
    manifest=json.loads(private_object("release-manifest.json"))
    if manifest.get("city") != city or manifest.get("release") != release:
        raise RuntimeError("Release manifest identity mismatch")
    if manifest.get("private") is not True or manifest.get("public_cutover") is not False:
        raise RuntimeError("Manifest claims unsupported publication mode")
    items=manifest.get("files")
    if not isinstance(items,list) or not items:
        raise RuntimeError("Release manifest has no inventory")
    index={}
    for item in items:
        name=item.get("path","")
        if name in index or not name.startswith("SUPER."+city+"/") or ".." in Path(name).parts:
            raise RuntimeError("Invalid or duplicate path in release manifest")
        index[name]=item
    if len(index) != manifest.get("files_verified"):
        raise RuntimeError("File inventory length mismatch")
    if sum(x["bytes"] for x in items) != manifest.get("bytes_verified"):
        raise RuntimeError("Release byte count mismatch")

    # The pinned commit can restore every original byte, not just price metadata.
    with tempfile.TemporaryDirectory(prefix="isnet-rollback-rehearsal-") as tmp:
        target=Path(tmp)
        tar=target/"pinned-git-backup.tar"
        with tar.open("wb") as out:
            subprocess.run(["git","archive","--format=tar",release,"SUPER."+city],
                           cwd=ROOT,stdout=out,check=True)
        restored=target/"restored"
        restored.mkdir()
        with tarfile.open(tar,"r") as archive:
            archive.extractall(restored,filter="data")
        all_files=sorted(p.relative_to(restored).as_posix() for p in restored.rglob("*") if p.is_file())
        if set(all_files)!=set(index):
            raise RuntimeError("Restoration file list differs from private manifest")
        for name in all_files:
            data=(restored/name).read_bytes()
            item=index[name]
            if len(data)!=item["bytes"] or sha(data)!=item["sha256"]:
                raise RuntimeError("Restoration SHA256 differs: "+name)
        # Authenticated readback proves private Storage contains exact price/status samples.
        for relative in ("data/prices.json","data/refresh-status.json","data/source-status.json"):
            name="SUPER."+city+"/"+relative
            if name not in index:
                raise RuntimeError("Missing critical metadata: "+name)
            remote=private_object(name)
            if sha(remote)!=index[name]["sha256"]:
                raise RuntimeError("Private Storage readback SHA256 differs: "+name)
        probe="SUPER."+city+"/data/prices.json"
        public_url=base+"/storage/v1/object/public/"+BUCKET+"/"+quote(prefix+probe,safe="/")
        try:
            fetch(public_url)
        except HTTPError as ex:
            if ex.code not in (400,401,403,404):
                raise RuntimeError("Unexpected public access probe HTTP "+str(ex.code)) from None
        else:
            raise RuntimeError("PRIVATE price object is exposed publicly")
        status=json.loads((restored/("SUPER."+city)/"data/refresh-status.json").read_text(encoding="utf-8"))
    report={"city":city,"release":release,"files_restored_and_verified":len(index),
            "bytes_restored_and_verified":manifest["bytes_verified"],
            "authenticated_critical_files_verified":3,
            "anonymous_public_storage_read_denied":True,
            "restore_dry_run_verified":True,
            "source_status_checked_at":status.get("checked_at"),
            "updated_count":status.get("updated_count"),
            "branch_count":status.get("branch_count"),
            "coverage_status":status.get("coverage_status"),
            "live_website_untouched":True}
    print(json.dumps(report,ensure_ascii=False,sort_keys=True))
    Path(os.environ.get("RUNNER_TEMP","/tmp"),"super-verify-"+city+".json").write_text(
        json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--city",choices=sorted(RELEASES),required=True)
    audit(p.parse_args().city)
