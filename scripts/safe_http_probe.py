"""Small bounded production HTTP probe, not a capacity or stress benchmark.

Per-host sequential requests; no authentication, cache-busting, writes or retries.
This measures external public-edge HTTP availability/latency only.
"""
import argparse
import json
import statistics
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

TARGETS = {
    "tlvnet_home": "https://tlvnet.com/",
    "isnet_events": "https://isnet.co.il/events-preview/tel-aviv/",
    "isnet_super": "https://isnet.co.il/SUPER.TLV/",
}
def sample(url, timeout):
    t0 = time.perf_counter()
    try:
        with urlopen(Request(url, headers={"User-Agent":"ISNET-readonly-health-probe/1.0","Accept":"text/html"}),timeout=timeout) as r:
            code = r.status
            r.read(65536)
            return {"http":code,"seconds":round(time.perf_counter()-t0,3),"ok":200 <= code < 400}
    except HTTPError as exc:
        return {"http":exc.code,"seconds":round(time.perf_counter()-t0,3),"ok":False}
    except (URLError, TimeoutError, OSError) as exc:
        return {"http":None,"seconds":round(time.perf_counter()-t0,3),"ok":False,"error":type(exc).__name__}
def probe(samples=6, pause=1.0, timeout=8.0):
    output={}
    for label,url in TARGETS.items():
        results=[]
        for i in range(samples):
            if i:time.sleep(pause)
            results.append(sample(url,timeout))
        ok_times=sorted(row["seconds"] for row in results if row["ok"])
        output[label]={"url":url,"requests":len(results),"successes":len(ok_times),
                       "p50_s":round(statistics.median(ok_times),3) if ok_times else None,
                       "p95_s":ok_times[min(len(ok_times)-1,max(0,int(len(ok_times)*0.95+0.999)-1))] if ok_times else None,
                       "http_statuses":[r["http"] for r in results]}
    return output
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--samples",type=int,default=6)
    p.add_argument("--pause",type=float,default=1.0)
    a=p.parse_args()
    if not (1<=a.samples<=8 and a.pause>=1.0):
        p.error("Refusing unbounded probe: samples must be 1..8 and pause at least 1 second")
    r=probe(a.samples,a.pause)
    print(json.dumps(r,ensure_ascii=False,indent=2))
    failures=sum(v["requests"]-v["successes"] for v in r.values())
    raise SystemExit(0 if failures==0 else 1)
