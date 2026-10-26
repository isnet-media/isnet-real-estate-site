#!/usr/bin/env python3
"""Fetch show-specific editorial/media candidates for matched Ashdod stage events.
Read only. Preserve source attribution, never replace public content on guesswork.
"""
import json,re,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup, NavigableString

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"events-preview/admin/data"
IN=DATA/"event-enrichment-candidates-ashdod.json"
OUT=DATA/"stage-content-media-review-ashdod.json"
CATS={"music","standup","kids","theatre"}
HEAD={"User-Agent":"ISNET-Events-Enrichment/1.0 (isnet.co.il)","Accept-Language":"he-IL,he;q=0.9"}
def clean(s):
    return re.sub(r"\s+"," ",str(s or "")).strip()
def meta(soup,property_name):
    found=soup.find("meta",attrs={"property":property_name}) or soup.find("meta",attrs={"name":property_name})
    return clean(found.get("content")) if found else None

def show_description(soup):
    """Read genuine copy under the official 'show description' heading, not the SEO title."""
    head=soup.find(lambda tag:getattr(tag,"name",None) in ("h2","h3","h4") and "תיאור המופע" in clean(tag.get_text(" ",strip=True)))
    if head is None:return None
    parts=[]
    for node in head.next_elements:
        if getattr(node,"name",None) in ("h1","h2","h3","h4"):break
        if isinstance(node,NavigableString) and getattr(node.parent,"name",None) not in ("script","style","noscript"):
            value=clean(str(node))
            if value and value not in parts:parts.append(value)
        if sum(map(len,parts))>3300:break
    value=clean(" ".join(parts))
    return value[:3300] if len(value)>=90 else None

def show_image(soup,base,title):
    """Find a photo visibly embedded on this show page. Review only, rights unverified."""
    head=soup.find("h1")
    nearby={id(img) for img in head.find_all_previous("img",limit=4)} if head else set()
    want=set(re.findall(r"[A-Za-z0-9א-ת]{3,}",(title or "").lower()))
    found=[]
    for img in soup.select("img"):
        raw=img.get("data-src") or img.get("data-lazy-src") or img.get("src")
        if not raw or raw.startswith(("data:","blob:")):continue
        url=urljoin(base,raw.strip())
        if urlparse(url).scheme not in ("https","http"):continue
        alt=clean(img.get("alt") or img.get("title") or "")
        label=(url+" "+alt).lower()
        if any(x in label for x in ("logo","banner bg","favicon","sprite","cart_icon","sold_icon","less_icon","box-studio","placeholder","facebook","instagram","/icons/")):continue
        score=(5 if "imagedelivery.net" in url else 0)+(5 if id(img) in nearby else 0)+(3 if len(alt)>=12 else 0)+(2 if ("תמונה" in alt or "קולאז" in alt) else 0)
        alt_words=set(re.findall(r"[A-Za-z0-9א-ת]{3,}",alt.lower()))
        if want:score+=5*len(want & alt_words)/len(want)
        if score>=8:found.append((score,url))
    found.sort(key=lambda x:x[0],reverse=True)
    return found[0][1] if found else None

def extract(session,url):
    response=session.get(url,headers=HEAD,timeout=18)
    response.raise_for_status()
    requested=urlparse(url).hostname or ""
    landed=urlparse(response.url).hostname or ""
    if landed!=requested and not landed.endswith("."+requested) and not requested.endswith("."+landed):
        raise ValueError("source_redirected_offsite")
    soup=BeautifulSoup(response.text,"html.parser")
    image=meta(soup,"og:image") or meta(soup,"twitter:image")
    desc=meta(soup,"og:description") or meta(soup,"description")
    title=meta(soup,"og:title") or (clean(soup.title.get_text(" ",strip=True)) if soup.title else None)
    image_method="social_metadata" if image else None
    description_method="social_metadata" if desc else None
    if (urlparse(response.url).hostname or "").removeprefix("www.")=="friends-hist.co.il":
        h1=soup.find("h1")
        show_title=clean(h1.get_text(" ",strip=True)) if h1 else (title or "")
        photo=show_image(soup,response.url,show_title)
        rich_copy=show_description(soup)
        if photo:image,image_method=photo,"show_page_embedded_image"
        if rich_copy:desc,description_method=rich_copy,"show_page_body"
        elif desc and len(desc)<90:desc,description_method=None,None
    videos=[]
    for node in soup.select("iframe[src],a[href]"):
        href=node.get("src") or node.get("href") or ""
        if any(host in href for host in ("youtube.com/watch","youtube.com/embed/","youtu.be/","vimeo.com/")):
            value=urljoin(response.url,href)
            if value not in videos:videos.append(value)
        if len(videos)>=4:break
    return {"fetched_url":response.url,"source_title":title,"description_candidate":desc,
            "description_extraction_method":description_method,
            "image_candidate_url":urljoin(response.url,image) if image else None,
            "image_extraction_method":image_method,
            "video_candidates":videos,"classification_candidate":None,
            "image_rights_status":"unverified","publication_status":"review_required"}

def main():
    feed=json.loads(IN.read_text(encoding="utf-8"))["events"]
    result=[];cache={}
    with requests.Session() as session:
        for event in feed:
            if event.get("category") not in CATS:continue
            proposals=[]
            seen=set()
            for source in event.get("same_production_candidates",[]):
                url=source.get("source_url")
                if not url or url in seen:continue
                seen.add(url)
                try:
                    if url not in cache:
                        cache[url]=extract(session,url)
                        time.sleep(1)
                    detail={"source_id":source.get("source_id"),"source_url":url,**cache[url]}
                except Exception as exc:
                    detail={"source_id":source.get("source_id"),"source_url":url,"fetch_error":str(exc)[:170]}
                proposals.append(detail)
            if proposals:
                result.append({"event_id":event.get("event_id"),"title":event.get("title"),
                               "category":event.get("category"),"subcategory":event.get("subcategory"),
                               "source_candidates":proposals,
                               "never_replace_existing_verified_image_without_identity_check":True})
    output={"generated_at":datetime.now(timezone.utc).isoformat(),"scope":"ashdod_stage_only",
            "events_with_source_matches":len(result),"cms_modified":False,"public_site_modified":False,
            "events":result}
    OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Stage events with reviewable media candidates",len(result))
if __name__=="__main__":main()
