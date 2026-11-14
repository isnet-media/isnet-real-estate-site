"""Lossless staged JPEG entropy optimization using jpegtran.

No source file, image pixel, dimensions, metadata, or URL is intentionally altered.
Only replace staged file if jpegtran succeeds and produces smaller valid JPEG bytes.
"""
import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

def optimize(root, *, limit=2500, min_size=32768):
    root=Path(root).resolve()
    if not root.is_dir():raise ValueError("Staging root not found")
    executable=shutil.which("jpegtran")
    if not executable:raise RuntimeError("jpegtran binary is required for lossless optimization")
    candidates=[]
    for p in root.rglob("*"):
        if p.is_symlink():raise ValueError("Staging symlinks not permitted")
        if p.is_file() and p.suffix.lower() in {".jpg",".jpeg"} and p.stat().st_size>=min_size:
            candidates.append(p)
    candidates.sort(key=lambda p:p.stat().st_size,reverse=True)
    processed=saved=changed=0
    errors=[]
    for p in candidates[:limit]:
        processed+=1
        before=p.stat().st_size
        fd,temp=tempfile.mkstemp(prefix=".jpeg-opt-",suffix=".jpg",dir=p.parent)
        os.close(fd)
        try:
            try:
                result=subprocess.run([executable,"-copy","all","-optimize","-outfile",temp,str(p)],
                                      capture_output=True,timeout=15)
            except (subprocess.TimeoutExpired,OSError):
                errors.append(str(p.relative_to(root)));continue
            if result.returncode or not Path(temp).is_file():
                errors.append(str(p.relative_to(root)));continue
            b=Path(temp).read_bytes()
            if len(b)<4 or not b.startswith(b"\xff\xd8") or not b.endswith(b"\xff\xd9"):
                errors.append(str(p.relative_to(root)));continue
            if len(b)>=before:continue
            os.chmod(temp,p.stat().st_mode)
            os.replace(temp,p)
            changed+=1
            saved+=before-len(b)
        finally:
            if os.path.exists(temp):os.unlink(temp)
    return {"candidates":len(candidates),"processed":processed,"changed":changed,"saved_bytes":saved,"errors":errors[:20]}

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--root",required=True,type=Path)
    a.add_argument("--limit",type=int,default=2500)
    args=a.parse_args()
    if not 1<=args.limit<=5000:a.error("Refuse unbounded processing")
    print(json.dumps(optimize(args.root,limit=args.limit)))
