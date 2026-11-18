"""Read-only Linux host capacity sampler. Run ONLY on authorized host.

No network calls, no SSH, no secrets, no privileged operations, no deletion.
Outputs percentages to avoid leaking paths/hostnames and helps decide capacity upgrades.
"""
import json
import os
import sys
from pathlib import Path

def read_meminfo():
    vals={}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key,_,val=line.partition(":")
        if key in {"MemTotal","MemAvailable","SwapTotal","SwapFree"}:
            vals[key]=int(val.strip().split()[0])*1024
    return vals
def report(path="/"):
    fs=os.statvfs(path)
    total=fs.f_blocks*fs.f_frsize
    free=fs.f_bavail*fs.f_frsize
    inode_pct=100*fs.f_favail/fs.f_files if fs.f_files else None
    mem=read_meminfo()
    cpus=os.cpu_count() or 1
    result={
        "disk_total_bytes":total,"disk_free_bytes":free,
        "disk_free_pct":round(100*free/total,2) if total else None,
        "inode_free_pct":round(inode_pct,2) if inode_pct is not None else None,
        "memory_total_bytes":mem.get("MemTotal"),
        "memory_available_pct":round(100*mem["MemAvailable"]/mem["MemTotal"],2),
        "swap_used_pct":round(100*(mem.get("SwapTotal",0)-mem.get("SwapFree",0))/mem["SwapTotal"],2) if mem.get("SwapTotal") else None,
        "load_5min_per_cpu":round(os.getloadavg()[1]/cpus,3),
        "cpu_count":cpus,
    }
    warnings=[]
    if result["disk_free_pct"] is not None and result["disk_free_pct"]<25:warnings.append("disk_headroom_below_25pct")
    if result["inode_free_pct"] is not None and result["inode_free_pct"]<15:warnings.append("inode_headroom_below_15pct")
    if result["memory_available_pct"]<20:warnings.append("memory_headroom_below_20pct")
    if result["load_5min_per_cpu"]>=0.85:warnings.append("load_above_0.85_per_cpu")
    result["warnings"]=warnings
    return result
if __name__=="__main__":
    try:
        r=report()
        print(json.dumps(r))
        sys.exit(1 if r["warnings"] else 0)
    except (OSError,KeyError,ValueError) as e:
        print(json.dumps({"error":type(e).__name__}))
        sys.exit(2)
