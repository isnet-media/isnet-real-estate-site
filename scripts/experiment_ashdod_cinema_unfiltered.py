#!/usr/bin/env python3
"""Unfiltered Ashdod cinema experiment: scan official venues and movie detail pages.
Never use saved ISNET trailers to fill gaps. This is a diagnostic, not publication.
"""
import json,re,time
from pathlib import Path
from urllib.parse import urljoin,urlsplit
import requests
from bs4 import BeautifulSoup
BASES={"hot-cinema":"https://hotcinema.co.il/theater/5","cinema-city":"https://www.cinema-city.co.il/city/ashdod"}
S=requests.Session();S.headers.update({"User-Agent":"Mozilla/5.0 (compatible; ISNET-cinema-intake/1.0)","Accept-Language":"he-IL,he;q=0.9"})
def get(url):
 r=S.get(url,timeout=25);r.raise_for_status();return r.text
def movie_links(doc,base):
 soup=BeautifulSoup(doc,"html.parser");host=urlsplit(base).netloc;found={}
 for a in soup.select("a[href]"):
  u=urljoin(base,a.get("href",""))
  if urlsplit(u).netloc!=host or not re.search(r"/movie(?:s)?/",urlsplit(u).path,re.I):continue
  name=a.get_text(" ",strip=True)
  parent=a.find_parent(["article","section","li","div"])
  if parent:
   heading=parent.select_one("h3,h4,h2")
   if heading:name=heading.get_text(" ",strip=True) or name
  if name in ("אודות הסרט","לפרטים","הזמנת כרטיסים","רכישת כרטיסים",""):name=""
  found.setdefault(u,name[:180])
 return found
def extract_youtube(html):
 ids=[]
 for pat in [r"(?:youtube\.com/embed/|youtube\.com/watch\?v=|youtu\.be/|youtube-nocookie\.com/embed/)([A-Za-z0-9_-]{11})",r'["\\'](?:youtubeId|youtube_id|youtubeVideoId|trailerYoutubeId)["\\']\s*:\s*["\\']([A-Za-z0-9_-]{11})']:
  for v in re.findall(pat,html,re.I):
   if v not in ids:ids.append(v)
 return ids
output={"mode":"unfiltered_live_source_only","sources":[]}
for key,base in BASES.items():
 report={"source":key,"url":base,"movies":[],"status":"unknown"}
 try:
  html=get(base);links=movie_links(html,base)
  report["source_page_bytes"]=len(html);report["links_found"]=len(links)
  for url,title in list(links.items())[:120]:
   try:
    detail=get(url)
    soup=BeautifulSoup(detail,"html.parser")
    title=title or (soup.select_one("h1").get_text(" ",strip=True) if soup.select_one("h1") else "")
    vids=extract_youtube(detail)
    report["movies"].append({"title":title,"url":url,"trailer_ids_found":vids,"has_description":bool(soup.select_one('meta[name="description"]'))})
   except Exception as e:report["movies"].append({"title":title,"url":url,"error":str(e)[:150]})
   time.sleep(.3)
  report["status"]="scanned"
 except Exception as e:report["status"]="error";report["error"]=str(e)[:300]
 output["sources"].append(report)
output["total_detail_pages"]=sum(len(x["movies"]) for x in output["sources"])
output["movies_with_trailer_candidates"]=sum(bool(x.get("trailer_ids_found")) for a in output["sources"] for x in a["movies"])
Path("cinema-unfiltered-ashdod-report.json").write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({k:output[k] for k in ("total_detail_pages","movies_with_trailer_candidates")},ensure_ascii=False))
for r in output["sources"]:print(r["source"],r["status"],"links",r.get("links_found"),"checked",len(r["movies"]),"trailers",sum(bool(x.get("trailer_ids_found")) for x in r["movies"]))
