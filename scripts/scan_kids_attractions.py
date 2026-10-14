"""Read-only HTTP discovery; write a local review snapshot, never event records.

Registry URLs are curated repository input. No forms, purchases, browser calls,
CMS writes, source changes, or automatic promotion of discovered places.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit, urljoin
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "events-preview/ashdod/data/kids-attractions-sources.json"
OUTPUT = ROOT / "events-preview/admin/data/ashdod-kids-attractions-scan.json"

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.text, self.title = [], [], []
        self.current, self.in_title = None, False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title": self.in_title = True
        if tag == "a" and a.get("href"): self.current = [a["href"], []]
    def handle_data(self, data):
        self.text.append(data)
        if self.in_title: self.title.append(data)
        if self.current: self.current[1].append(data)
    def handle_endtag(self, tag):
        if tag == "title": self.in_title = False
        if tag == "a" and self.current:
            self.links.append((self.current[0], " ".join(self.current[1]).strip()))
            self.current = None

def scan(source):
    result = {"source_id": source["id"], "url": source["url"], "candidates": []}
    try:
        u = urlsplit(source["url"])
        url = urlunsplit((u.scheme, u.netloc, quote(u.path, safe="/%"), u.query, ""))
        request = Request(url, headers={"User-Agent": "ISNET-Attractions-Source-Check/1.0"})
        with urlopen(request, timeout=20) as response:
            body = response.read(3_000_000).decode("utf-8", errors="replace")
            result.update(status="ok", http_status=response.status, final_url=response.url)
        page = Page(); page.feed(body)
        result["page_title"] = " ".join(page.title).strip()
        result["content_sha256"] = hashlib.sha256(body.encode()).hexdigest()
        result["closure_notice"] = "סגור עד להודעה חדשה" in " ".join(page.text)
        seen = set()
        pattern = source.get("detail_pattern")
        for href, label in page.links:
            link = urljoin(result["final_url"], href)
            parsed = urlsplit(link)
            if not pattern or pattern not in parsed.path or parsed.netloc != u.netloc or not label:
                continue
            if link in seen: continue
            seen.add(link)
            result["candidates"].append({"name": label[:180], "url": link, "review_status": "needs_location_and_operator_verification"})
    except Exception as error:
        result.update(status="unverified", error=type(error).__name__ + ": " + str(error))
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    registry = json.loads(args.registry.read_text())
    results = list(ThreadPoolExecutor(max_workers=3).map(scan, registry["sources"]))
    snapshot = {"checked_at": datetime.now(timezone.utc).isoformat(), "purpose": "discovery_only", "sources": results, "exclusions": registry.get("excluded", [])}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"sources": len(results), "ok": sum(r["status"] == "ok" for r in results), "candidates": sum(len(r["candidates"]) for r in results)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
