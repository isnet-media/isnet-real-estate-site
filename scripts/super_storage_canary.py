"""One-way immutable canary to a private Supabase Storage bucket.

Uses existing Actions secrets, limits uploads to two already-public TLV JSON files.
No live DNS, links, scans, prices, buckets or RLS rules are modified.
"""
import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_REF = "qomkxhafrprooekwgsxf"
BUCKET = "isnet-super-staging"
FILES = ("SUPER.TLV/data/source-status.json","SUPER.TLV/data/prices.json")
ROOT = Path(__file__).resolve().parents[1]

def request(url, method, key, data=None, content_type=None):
    headers = {"apikey":key,"Authorization":"Bearer "+key,"User-Agent":"isnet-super-canary/1.0"}
    if content_type:
        headers["Content-Type"]=content_type
    req=urllib.request.Request(url,data=data,headers=headers,method=method)
    with urllib.request.urlopen(req,timeout=35) as resp:
        return resp.status,resp.read()

def main():
    base=os.getenv("SUPABASE_URL","").rstrip("/")
    key=os.getenv("SUPABASE_SERVICE_ROLE_KEY","")
    if not key or base != "https://"+PROJECT_REF+".supabase.co":
        raise RuntimeError("Canary blocked: missing key or unexpected Supabase project URL")
    for rel in FILES:
        path=ROOT/rel
        data=path.read_bytes()
        if len(data)>1_000_000:raise RuntimeError("Canary payload size exceeded")
        json.loads(data)
        digest=hashlib.sha256(data).hexdigest()
        destination="canary/"+rel.replace("/","-").replace(".json","")+"-"+digest[:16]+".json"
        encoded=urllib.parse.quote(destination,safe="/")
        put_url=base+"/storage/v1/object/"+BUCKET+"/"+encoded
        try:
            status,_=request(put_url,"POST",key,data,content_type="application/json")
            if status not in (200,201):raise RuntimeError("Upload status rejected")
        except urllib.error.HTTPError as exc:
            if exc.code!=409:raise RuntimeError("Upload failed, http "+str(exc.code)) from None
        read_url=base+"/storage/v1/object/authenticated/"+BUCKET+"/"+encoded
        status,actual=request(read_url,"GET",key)
        if status!=200 or hashlib.sha256(actual).hexdigest()!=digest:raise RuntimeError("Readback checksum mismatch")
        print(json.dumps({"path":destination,"bytes":len(data),"sha256":digest,"readback":True,"public_access":False}))
if __name__=="__main__":
    main()
