"""Reversible, semantically verified JSON minification in the *staged* public site.

Only SUPER.*/data/offers/*.json and catalog.json files are eligible.
Source checkout, product values, file names, HTTP URLs and all media are untouched.
"""
import argparse
import json
import os
import tempfile
from pathlib import Path

def optimize(root):
    root=Path(root).resolve()
    if not root.is_dir(): raise ValueError("Missing public staging directory")
    savings=0
    changed=0
    examined=0
    errors=[]
    for city in sorted(root.glob("SUPER.*")):
        if not city.is_dir() or city.is_symlink(): continue
        files=sorted((city/"data"/"offers").glob("*.json")) if (city/"data"/"offers").is_dir() else []
        files+=[city/"data"/"catalog.json"]
        for path in files:
            if not path.exists(): continue
            if path.is_symlink() or not path.is_file(): raise ValueError("Unexpected symlink in public price JSON")
            examined+=1
            original=path.read_bytes()
            try:
                doc=json.loads(original.decode("utf-8"),parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
                encoded=json.dumps(doc,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8")
                if json.loads(encoded)!=doc: raise ValueError("Round-trip mismatch")
            except (ValueError,UnicodeError,TypeError) as exc:
                errors.append({"path":str(path.relative_to(root)),"error":type(exc).__name__})
                continue  # preserve original untouched; record for manual quality review
            if len(encoded)>=len(original):continue
            fd,temp=tempfile.mkstemp(prefix=".json-opt-",dir=path.parent)
            try:
                with os.fdopen(fd,"wb") as f:f.write(encoded)
                os.chmod(temp,path.stat().st_mode)
                os.replace(temp,path)
            finally:
                if os.path.exists(temp):os.unlink(temp)
            changed+=1
            savings+=len(original)-len(encoded)
    return {"files_examined":examined,"files_optimized":changed,"saved_bytes":savings,"invalid_json_preserved":errors}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--minimum-savings",type=int,default=0)
    a=p.parse_args()
    outcome=optimize(a.root)
    print(json.dumps(outcome,ensure_ascii=False))
    if outcome["saved_bytes"]<a.minimum_savings:raise SystemExit(1)
