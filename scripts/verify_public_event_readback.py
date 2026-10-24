"""Compare GitHub event feeds with the exact public JSON fetched by visitors.

Read-only. Does not update the CMS, source data, or the public site.
HTTP retrieval is evidence of JSON delivery, *not* DOM/mobile card rendering.
"""
import argparse
import collections
import datetime as dt
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

CITIES = ("ashdod", "rishon-lezion")
CHECK_FIELDS = ("title", "date", "date_time", "time", "description", "image",
                "image_url", "tickets_url", "ticket_url", "venue", "category", "subcategory")


def index(events):
    ids = collections.Counter(str(e.get("event_id")) for e in events)
    by_id = {str(e.get("event_id")): e for e in events if e.get("event_id")}
    return ids, by_id


def compare_city(city, root):
    result = {"city": city, "status": "unknown", "scope": "public JSON feed; not rendered cards"}
    local_path = root / "events-preview" / city / "data" / "events.json"
    local_data = json.loads(local_path.read_text(encoding="utf-8"))
    local = local_data.get("events")
    if not isinstance(local, list):
        raise ValueError(f"Unexpected GitHub events shape for {city}")
    result["github_count"] = len(local)

    # Cache bypass, no API keys and no write privileges. Allow maximum 12 MiB.
    url = f"https://isnet.co.il/events-preview/{city}/data/events.json"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ISNET-Public-Event-Readback/1.0",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            result["http_status"] = response.status
            result["http_last_modified"] = response.headers.get("Last-Modified")
            result["http_cache_status"] = response.headers.get("CF-Cache-Status")
            payload = response.read(12 * 1024 * 1024 + 1)
            if len(payload) > 12 * 1024 * 1024:
                raise ValueError("Public JSON exceeds readback safety limit")
            live_data = json.loads(payload)
    except Exception as exc:
        result["status"] = "fetch_failed"
        result["error"] = f"{type(exc).__name__}: {exc}"[:350]
        return result

    live = live_data.get("events")
    if not isinstance(live, list):
        result["status"] = "invalid_public_json"
        result["error"] = "Public data is not an object with an events array"
        return result
    result["public_count"] = len(live)
    local_ids, local_by_id = index(local)
    live_ids, live_by_id = index(live)
    local_duplicates = sorted(key for key, n in local_ids.items() if n > 1)
    live_duplicates = sorted(key for key, n in live_ids.items() if n > 1)
    missing = sorted((local_ids - live_ids).elements())
    extra = sorted((live_ids - local_ids).elements())
    common = sorted(local_by_id.keys() & live_by_id.keys())
    changed = []
    changed_fields = collections.Counter()
    for event_id in common:
        lhs, rhs = local_by_id[event_id], live_by_id[event_id]
        if lhs == rhs:
            continue
        changed.append(event_id)
        for field in CHECK_FIELDS:
            if lhs.get(field) != rhs.get(field):
                changed_fields[field] += 1
    result.update({
        "github_distinct_ids": len(local_by_id),
        "public_distinct_ids": len(live_by_id),
        # Parity of JSON delivery does not prove uniqueness of event identities.
        "github_duplicate_event_id_groups": len(local_duplicates),
        "public_duplicate_event_id_groups": len(live_duplicates),
        "github_duplicate_event_rows": sum(n - 1 for n in local_ids.values() if n > 1),
        "public_duplicate_event_rows": sum(n - 1 for n in live_ids.values() if n > 1),
        "github_duplicate_event_id_examples": local_duplicates[:20],
        "public_duplicate_event_id_examples": live_duplicates[:20],
        "event_ids_unique": not local_duplicates and not live_duplicates,
        "common_ids": len(common),
        "missing_public_ids": len(missing),
        "extra_public_ids": len(extra),
        "different_full_record_count": len(changed),
        "different_priority_field_counts": dict(changed_fields),
        "missing_public_examples": missing[:10],
        "extra_public_examples": extra[:10],
        "different_record_examples": changed[:10],
        "exact_feed_match": local_data == live_data,
    })
    result["status"] = "match" if result["exact_feed_match"] else "mismatch"
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except Exception:
        sha = None
    report = {
        "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "github_dataset_head": sha,
        "measurement": "Two exact public JSON reads vs checked-out GitHub feed. Does not prove events render in JS, correct rights, or completeness of source calendars.",
        "cities": {},
    }
    for city in CITIES:
        try:
            report["cities"][city] = compare_city(city, root)
        except Exception as exc:
            report["cities"][city] = {"city": city, "status": "error", "error": f"{type(exc).__name__}: {exc}"[:350]}
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    for city, finding in report["cities"].items():
        if finding.get("github_duplicate_event_id_groups", 0):
            print(f"::warning::{city} has {finding['github_duplicate_event_id_groups']} colliding event IDs; JSON parity does not verify record uniqueness.")
    if any(x["status"] != "match" for x in report["cities"].values()):
        sys.exit(2)


if __name__ == "__main__":
    main()
