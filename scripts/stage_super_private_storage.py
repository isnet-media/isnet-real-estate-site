"""Stage a complete, immutable city edition in PRIVATE Supabase Storage.

This script never modifies prices, triggers collection, edits DNS, or exposes files
to unauthenticated users. It refuses unexpected projects and verifies every file.
"""
import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

REF = "qomkxhafrprooekwgsxf"
BUCKET = "isnet-super-staging"
ALLOWED_CITIES = ("ASHDOD","YAVNE","KGAT","RISHON","HOLON","BATYAM","TLV")  # TLV private canary passed
ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_SIZE = 20 * 1024 * 1024

def call(url, method, secret, body=None, content_type=None):
    headers = {"apikey":secret, "Authorization":"Bearer "+secret,
               "User-Agent":"ISNET-private-super-release/1.0"}
    if content_type: headers["Content-Type"] = content_type
    req = Request(url, method=method, headers=headers, data=body)
    with urlopen(req, timeout=45) as response:
        return response.status, response.read()

def publish(city, release_override=None):
    if city not in ALLOWED_CITIES: raise ValueError("City not yet approved for full-stage pilot")
    base=os.getenv("SUPABASE_URL","").rstrip("/")
    token=os.getenv("SUPABASE_SERVICE_ROLE_KEY","")
    if base != "https://"+REF+".supabase.co" or not token:
        raise RuntimeError("Private storage not configured for expected project")
    root = ROOT/("SUPER."+city)
    if not root.is_dir(): raise RuntimeError("City source not found")
    paths=sorted(p for p in root.rglob("*") if p.is_file())
    if not 100<=len(paths)<=250: raise RuntimeError("Unexpected city file count")
    if any(p.is_symlink() for p in root.rglob("*")): raise RuntimeError("Symlink in city source")
    head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    release=release_override or head
    if release_override:
        if len(release)!=40 or any(ch not in "0123456789abcdef" for ch in release):
            raise RuntimeError("Invalid release SHA")
        def tree(commit):
            return subprocess.check_output(
                ["git","rev-parse",commit+":SUPER."+city],cwd=ROOT,text=True
            ).strip()
        if tree(head)!=tree(release):
            raise RuntimeError("City sources changed since requested release; refusing reuse")

    manifest=[]
    for p in paths:
        data=p.read_bytes()
        if len(data)>MAX_FILE_SIZE: raise RuntimeError("File too large for staging bucket")
        if p.suffix.lower()==".json": json.loads(data.decode("utf-8"))
        mime = {
            ".json":"application/json", ".html":"text/html", ".css":"text/css",
            ".js":"application/javascript", ".webp":"image/webp", ".jpg":"image/jpeg",
            ".jpeg":"image/jpeg", ".png":"image/png", ".svg":"image/svg+xml",
            ".ttf":"font/ttf", ".txt":"text/plain"
        }.get(p.suffix.lower())
        if mime is None: raise RuntimeError("Unexpected file extension: "+p.suffix)
        relative=p.relative_to(ROOT).as_posix()
        object_name=f"releases/{city}/{release}/{relative}"
        url=base+"/storage/v1/object/"+BUCKET+"/"+quote(object_name,safe="/")
        content_type=mime
        checksum=hashlib.sha256(data).hexdigest()
        read_url=base+"/storage/v1/object/authenticated/"+BUCKET+"/"+quote(object_name,safe="/")
        def verified_existing():
            try:
                status,existing=call(read_url,"GET",token)
            except HTTPError as ex:
                if ex.code==404: return False
                raise RuntimeError("Private read failed for "+relative+" HTTP "+str(ex.code)) from None
            if status!=200 or hashlib.sha256(existing).hexdigest()!=checksum:
                raise RuntimeError("Immutable object mismatch; refusing overwrite: "+relative)
            return True
        if not verified_existing():
            try:
                result,_=call(url,"POST",token,data,content_type)
                if result not in (200,201):
                    raise RuntimeError("Unexpected upload status for "+relative)
            except HTTPError as ex:
                body=ex.read().decode("utf-8","replace")[:350]
                # Storage sometimes reports an already-existing object as HTTP 400.
                # Accept an ambiguous conflict ONLY after a read-back SHA256 match.
                if ex.code not in (400,409) or not verified_existing():
                    raise RuntimeError("Upload failed "+relative+" HTTP "+
                                       str(ex.code)+" "+body) from None
            if not verified_existing():
                raise RuntimeError("Upload missing after success: "+relative)
        manifest.append({"path":relative,"sha256":checksum,"bytes":len(data)})
    report={"city":city,"release":release,"files_verified":len(manifest),
            "bytes_verified":sum(x["bytes"] for x in manifest),
            "private":True,"public_cutover":False,"files":manifest}
    # Store a manifest that is self-contained, immutable, and verified too.
    raw=json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2).encode("utf-8")
    destination=f"releases/{city}/{release}/release-manifest.json"
    url=base+"/storage/v1/object/"+BUCKET+"/"+quote(destination,safe="/")
    try:call(url,"POST",token,raw,"application/json")
    except HTTPError as ex:
        if ex.code!=409:raise RuntimeError("Manifest upload failed") from None
    _,actual=call(base+"/storage/v1/object/authenticated/"+BUCKET+"/"+quote(destination,safe="/"),"GET",token)
    if actual!=raw:raise RuntimeError("Manifest verification failed")
    print(json.dumps({k:v for k,v in report.items() if k!="files"},ensure_ascii=False))
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--city",required=True,choices=ALLOWED_CITIES)
    parser.add_argument("--release",help="Reuse private release only if city Git tree is identical")
    options=parser.parse_args()
    publish(options.city, options.release)
