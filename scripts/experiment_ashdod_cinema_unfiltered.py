#!/usr/bin/env python3
"""Unfiltered Ashdod cinema experiment: scan official venues and movie detail pages.
Never use saved ISNET trailers to fill gaps. This is a diagnostic, not publication.
"""
import json,re,time,unicodedata,os
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
 soup=BeautifulSoup(html,"html.parser")
 for node in soup.select("iframe[src], iframe[data-src], a[href]"):
  src=node.get("src") or node.get("data-src") or node.get("href") or ""
  m=re.search(r"(?:youtube[.]com/(?:embed/|watch[?]v=)|youtu[.]be/|youtube-nocookie[.]com/embed/)([A-Za-z0-9_-]{11})",src)
  if m and m.group(1) not in ids:ids.append(m.group(1))
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
    media_tags=[{"tag":t.name,"src":str(t.get("src") or t.get("data-src") or "")[:180]} for t in soup.select("iframe[src],iframe[data-src],video[src],source[src]")][:8]
    hints=[]
    for term in ("youtube","youtube.com","youtu.be","vimeo","trailer","videoUrl","VideoUrl","טריילר","jwplayer","player"):
     count=detail.lower().count(term.lower())
     if count:hints.append({"term":term,"count":count})
    report["movies"].append({"title":title,"url":url,"trailer_ids_found":vids,"has_description":bool(soup.select_one('meta[name="description"]')),"video_hints":hints,"media_tags":media_tags})
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

for report in output["sources"]:
 for row in report["movies"][:4]: print("MEDIA_SAMPLE",json.dumps(row,ensure_ascii=False)[:2200])

def norm_title(s):
 s=unicodedata.normalize("NFKC",s or "").strip()
 s=re.sub(r"\s*[-–—]\s*(?:מדובב(?: לעברית)?|עם כתוביות)\s*$","",s)
 return re.sub(r"[^0-9a-zא-ת]+","",s.lower())
dataset_path=Path("events-preview/ashdod/data/cinema.json")
existing=json.loads(dataset_path.read_text(encoding="utf-8"))
lookup={}
for film in existing.get("movies",[]):
 lookup.setdefault(norm_title(film.get("title")),[]).append(film)
def base_title(s):
 s=unicodedata.normalize("NFKC",s or "").strip()
 s=re.sub(r"\\s*[-–—]?\\s*(?:מדובב(?: לעברית| לרוסית)?|אנגלית|גרסה באנגלית|עם כתוביות)\\s*$","",s)
 return norm_title(s)
base_lookup={}
for film in existing.get("movies",[]):
 base_lookup.setdefault(base_title(film.get("title")),[]).append(film)
matched=[]
unmatched=[]
for source in output["sources"]:
 if source["source"]!="hot-cinema":continue
 for item in source["movies"]:
  ids=item.get("trailer_ids_found") or []
  candidates=lookup.get(norm_title(item.get("title")) or "",[])
  # Accept a normalized language suffix only if exactly one local film has that base title.
  if not candidates:
   possible=base_lookup.get(base_title(item.get("title")),[])
   if len(possible)==1 and len(lookup.get(norm_title(possible[0].get("title")),[]))==1:candidates=possible
  if len(candidates)==1 and ids:
   target=candidates[0]
   if target["id"] not in [x["id"] for x in matched]:
    matched.append({"id":target["id"],"title":target["title"],"source_title":item["title"],"trailer_id":ids[0],"source_url":item["url"]})
  else:unmatched.append({"title":item.get("title"),"reason":"no_trailer" if not ids else "no_exact_match"})
output["official_matched_to_existing"]=matched
output["unmatched_sample"]=unmatched[:30]
Path("cinema-unfiltered-ashdod-report.json").write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
print("MATCHED_EXISTING",len(matched),"unmatched",len(unmatched))
print("MATCHED_FILMS",json.dumps(matched,ensure_ascii=False))
if os.environ.get("ISNET_PUBLISH_FRESH")=="1" and len(matched)>=3:
 for item in matched:
  dest=next(m for m in existing["movies"] if m["id"]==item["id"])
  dest["trailer_youtube_id"]=item["trailer_id"]
  dest["trailer_source_url"]=item["source_url"]
  dest["trailer_source_name"]="HOT Cinema Ashdod - official embedded trailer"
 dataset_path.write_text(json.dumps(existing,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("PUBLISHED_FRESH_TRAILERS",len(matched))
