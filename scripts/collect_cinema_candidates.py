#!/usr/bin/env python3
"""Fetch cinema listings as review-only candidates; NEVER publish unverifiable showtimes."""
import json, re, sys, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

# Official theater listings only. Ashdod pilot; expand after validating data extraction.
SOURCES={
 "ashdod":{
  "cinema-city":"https://www.cinema-city.co.il/city/ashdod",
  "hot-cinema":"https://hotcinema.co.il/theater/5"
 }}
class Text(HTMLParser):
 def __init__(self): super().__init__(); self.bits=[]; self.skip=0
 def handle_starttag(self,t,a):
  if t in ("script","style"):self.skip+=1
 def handle_endtag(self,t):
  if t in ("script","style"):self.skip=max(0,self.skip-1)
 def handle_data(self,s):
  if not self.skip:
   s=" ".join(s.split())
   if s:self.bits.append(s)
def fetch(url):
 request=urllib.request.Request(url,headers={"User-Agent":"ISNET Cinema editorial verification (respectful once-daily request)","Accept-Language":"he-IL,he;q=0.9"})
 with urllib.request.urlopen(request,timeout=20) as r:
  raw=r.read(2_000_000)
  charset=r.headers.get_content_charset() or "utf-8"
 return raw.decode(charset,errors="replace")
def main():
 now=datetime.now(timezone.utc).isoformat()
 results={"checked_at":now,"publication_status":"REVIEW_ONLY_NOT_LIVE","sources":[]}
 for city,venues in SOURCES.items():
  for venue,url in venues.items():
   item={"city":city,"venue":venue,"url":url}
   try:
    doc=fetch(url)
    p=Text();p.feed(doc)
    lines=p.bits
    item.update({"ok":True,"page_title":next((v for v in lines if "קולנוע" in v or "סינמה" in v),""),"preview_text":lines[:350],"potential_showtimes":len(re.findall(r"\\b(?:[01]?\\d|2[0-3]):[0-5]\\d\\b"," ".join(lines)))})
   except Exception as exc:item.update({"ok":False,"error":str(exc)[:200]})
   results["sources"].append(item)
 out=Path("cinema-review-candidates.json");out.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
 print("Sources checked:",sum(s["ok"] for s in results["sources"]),"of",len(results["sources"]))
 print("Review-only file:",out)
 if not any(s["ok"] for s in results["sources"]):sys.exit(1)
if __name__=="__main__": main()
