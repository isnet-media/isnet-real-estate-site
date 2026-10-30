#!/usr/bin/env python3
"""Read-only FRIENDS discovery for Ashdod and Rishon LeZion.

Outputs auditable source candidates. Does not publish, modify events or download images.
"""
import json
import re
import time
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"events-preview/admin/data/event-source-priority.json"
OUTPUT=ROOT/"events-preview/admin/data/friends-discovery.json"
UA="ISNET-Events-Source-Discovery/1.0 (contact via isnet.co.il)"
HEADERS={"User-Agent":UA,"Accept-Language":"he-IL,he;q=0.9"}
def clean(s):
    return re.sub(r"\s+"," ",str(s or "")).strip()

def get(url, session):
    r=session.get(url,headers=HEADERS,timeout=25)
    r.raise_for_status()
    if urlparse(r.url).hostname not in {"friends-hist.co.il","www.friends-hist.co.il"}:
        raise ValueError("Unexpected redirect")
    return BeautifulSoup(r.text,"html.parser")

def extract_city(soup,city):
    found={}
    for a in soup.select('a[href*="/show/"]'):
        href=urljoin("https://friends-hist.co.il/",a.get("href","")).split("#")[0]
        if urlparse(href).hostname not in {"friends-hist.co.il","www.friends-hist.co.il"}:
            continue
        title=clean(a.get_text(" ",strip=True)) or clean(a.get("title"))
        if not title:
            img=a.find("img")
            title=clean(img.get("alt")) if img else ""
        if not title or title in {"לפרטים והזמנה","להזמנה","פרטים נוספים"}:
            continue
        found.setdefault(href,{"title":title,"production_url":href,"city":city,"source_id":"friends-hist",
                              "rights_status":"not_verified","status":"candidate_requires_event_date_validation"})
    return list(found.values())


def extract_dated_occurrences(soup, city, today=None):
    """Extract venue-confirmed, scheduled FRIENDS cards as review-only candidates.

    Do not infer local dates from a city heading or a production page alone.
    Never treat an image displayed on FRIENDS as licensed for ISNET publishing.
    """
    today = today or datetime.now(ZoneInfo("Asia/Jerusalem")).date()
    if city not in {"ashdod", "rishon-lezion"}:
        return []
    rows, seen = [], set()
    for card in soup.select(".search_show_row"):
        h = card.select_one(".wrap_title h3") or card.select_one("h3")
        a = card.select_one('a[href*="/show/"]')
        title = clean(h.get_text(" ", strip=True)) if h else ""
        production_url = urljoin("https://friends-hist.co.il/", a.get("href", "")) if a else ""
        if not title or urlparse(production_url).hostname not in {"friends-hist.co.il", "www.friends-hist.co.il"}:
            continue
        image = card.select_one(".wrap_img a img")
        raw_image = (image.get("data-lazy-src") or image.get("data-src") or image.get("src")) if image else None
        candidate_image = urljoin("https://friends-hist.co.il/", raw_image) if raw_image else None
        if not candidate_image or not candidate_image.startswith("https://") or any(
            token in candidate_image.lower() for token in ("logo", "placeholder", "default-image", "no-image")
        ):
            candidate_image = None
        description = clean(
            (card.select_one(".tooltip-show-content") or card.select_one(".wrap_description")).get_text(" ", strip=True)
        ) if card.select_one(".tooltip-show-content") or card.select_one(".wrap_description") else None
        for occurrence in card.select(".events_list .wrap_item"):
            venue = clean(occurrence.select_one(".hall-name-wrap").get_text(" ", strip=True)) if occurrence.select_one(".hall-name-wrap") else ""
            venue_ok = ("אשדוד" in venue) if city == "ashdod" else bool(
                re.search(r"ראשון\s*לציון|ראשל[\"״׳']?צ", venue)
            )
            if not venue_ok:
                continue
            when_node = occurrence.select_one(".wrap_event")
            when = clean(when_node.get_text(" ", strip=True)) if when_node else ""
            match = re.search(r"(?<!\d)(\d{1,2}\.\d{1,2}\.\d{2,4})\s+(\d{1,2}:\d{2})(?!\d)", when)
            if not match:
                continue
            try:
                start_date = datetime.strptime(
                    match.group(1), "%d.%m.%Y" if len(match.group(1).split(".")[-1]) == 4 else "%d.%m.%y"
                ).date()
                hour, minute = map(int, match.group(2).split(":"))
                if not 0 <= hour <= 23 or not 0 <= minute <= 59:
                    continue
            except ValueError:
                continue
            if not today <= start_date <= today + timedelta(days=540):
                continue
            clock = f"{hour:02d}:{minute:02d}"
            key = (production_url, city, start_date.isoformat(), clock, venue)
            if key in seen:
                continue
            seen.add(key)
            button = occurrence.select_one("[data-event_id]")
            rows.append({
                "title": title,
                "city": city,
                "start_date": start_date.isoformat(),
                "start_time": clock,
                "venue": venue,
                "production_url": production_url,
                "source_url": production_url,
                "source_event_id": button.get("data-event_id") if button else None,
                "source_id": "friends-hist",
                "description_candidate": description if description and len(description) >= 80 else None,
                "image_candidate_url": candidate_image,
                "image_rights_status": "not_verified",
                "status": "candidate_requires_human_review",
                "publication_enabled": False,
            })
    return rows

def main():
    source=next(s for s in json.loads(CONFIG.read_text(encoding="utf-8"))["sources"] if s["id"]=="friends-hist")
    items=[]; dated=[]; errors=[]
    with requests.Session() as session:
        for entry in source["cities"]:
            try:
                page=get(entry["url"],session)
                matches=extract_city(page,entry["slug"])
                items.extend(matches)
                dated.extend(extract_dated_occurrences(page,entry["slug"]))
            except Exception as exc:
                errors.append({"city":entry["slug"],"error":type(exc).__name__+": "+str(exc)[:240]})
            time.sleep(2)
    report={"generated_at":datetime.now(timezone.utc).isoformat(),"source_id":"friends-hist",
            "publication_enabled":False,"cms_updated":False,"image_reuse_authorized":False,
            "city_counts":{c["slug"]:sum(v["city"]==c["slug"] for v in items) for c in source["cities"]},
            "errors":errors,"candidates":items,
            "dated_city_counts":{c["slug"]:sum(v["city"]==c["slug"] for v in dated) for c in source["cities"]},
            "dated_occurrence_candidates":dated,
            "dated_candidate_policy":"Venue and full local date/time required; images and copy unlicensed and not published"}
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"city_counts":report["city_counts"],"dated_city_counts":report["dated_city_counts"],"errors":errors},ensure_ascii=False))
if __name__=="__main__":
    main()
