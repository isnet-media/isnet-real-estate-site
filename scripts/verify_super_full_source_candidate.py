"""Build a review-only COMPLETE supermarket city artifact from one pinned main commit.

This does not collect, publish, upload to Storage, approve media, or modify live data.
It keeps partial per-branch freshness and the source's original timestamps visible.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.stage_super_city_release import stage_city
from scripts.super_committed_delta_preflight import validate_status

REVIEW_CITIES = ("ASHDOD", "BATYAM", "HOLON", "KGAT", "RISHON", "YAVNE")
SOURCE_FILES = ("data/prices.json", "data/refresh-status.json", "data/source-status.json")


def pinned_commit(source: Path, expected_sha: str) -> None:
    if not re.fullmatch(r"[a-f0-9]{40}", expected_sha):
        raise ValueError("Candidate must be pinned to an exact 40-character commit SHA")
    actual = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual != expected_sha:
        raise ValueError("Candidate checkout differs from pinned main commit")


def inspect_city(source: Path, city: str, source_sha: str, now: datetime | None = None) -> dict:
    if city not in REVIEW_CITIES:
        raise ValueError("City not eligible for complete-site private candidate")
    pinned_commit(source, source_sha)
    city_root = source / ("SUPER." + city)
    if not city_root.is_dir():
        raise ValueError("Missing city source")
    data = {}
    sha256 = {}
    for relative in SOURCE_FILES:
        raw = (city_root / relative).read_bytes()
        if not raw:
            raise ValueError("Empty critical source: " + relative)
        value = json.loads(raw.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Critical JSON not an object: " + relative)
        data[relative] = value
        sha256[relative] = hashlib.sha256(raw).hexdigest()
    refresh = data["data/refresh-status.json"]
    prices = data["data/prices.json"]
    source_status = data["data/source-status.json"]
    checked = validate_status(refresh)
    now = now or datetime.now(timezone.utc)
    if checked > now + timedelta(minutes=5):
        raise ValueError("Future-dated source is not a candidate")
    if prices.get("retrieved_at") != refresh.get("checked_at"):
        raise ValueError("Price snapshot retrieved_at disagrees with refresh source")
    if prices.get("branch_count") != refresh.get("branch_count"):
        raise ValueError("Price branch_count disagrees with refresh source")
    if prices.get("coverage_complete") is not refresh.get("all_sources_updated"):
        raise ValueError("Price coverage_complete disagrees with refresh source")
    # The source status is a calendar-date summary, not proof of every supplier's freshness.
    local_date = datetime.fromisoformat(refresh["checked_at"]).date().isoformat()
    if source_status.get("updated_at") != local_date:
        raise ValueError("Source-status calendar date disagrees with collector record")
    p_branches = prices.get("branches")
    r_branches = refresh.get("branches")
    if not isinstance(p_branches, list) or len(p_branches) != refresh["branch_count"]:
        raise ValueError("Price branch records disagree with branch_count")
    p_ids = [x.get("id") for x in p_branches if isinstance(x, dict)]
    r_ids = [x.get("branch_id") for x in r_branches if isinstance(x, dict)]
    if not all(isinstance(x, str) and x for x in p_ids + r_ids):
        raise ValueError("Missing branch identities")
    if len(set(p_ids)) != len(p_branches) or set(p_ids) != set(r_ids):
        raise ValueError("Price branches do not match source provenance identities")
    for relative in ("index.html", "compare/index.html", "deals/index.html",
                     "recipes/index.html", "smart-shopping/index.html"):
        if not (city_root / relative).is_file():
            raise ValueError("Missing essential site page: " + relative)
    first = (city_root / "index.html").read_text(encoding="utf-8").lower()
    if "<html" not in first or 'http-equiv="refresh"' in first or "אינה זמינה כרגע" in first:
        raise ValueError("No usable standalone city shell")
    return {
        "format": "isnet-super-full-source-private-review-v1",
        "city": city,
        "committed_main_sha": source_sha,
        "source_checked_at": refresh["checked_at"],
        "branch_count": refresh["branch_count"],
        "updated_count": refresh["updated_count"],
        "retained_previous_count": refresh["branch_count"] - refresh["updated_count"],
        "all_sources_updated": refresh["all_sources_updated"],
        "coverage_status": refresh.get("coverage_status"),
        "critical_source_sha256": sha256,
        "complete_committed_tree_candidate": True,
        "same_commit_site_and_price_files": True,
        "customer_ready": False,
        "approved_for_public": False,
        "media_rights_verified": False,
        "browser_mobile_accepted": False,
        "same_url_rollback_proved": False,
        "storage_writes": False,
        "collector_invoked": False,
        "public_cutover": False,
    }


def stage_candidate(source: Path, out: Path, city: str, sha: str) -> dict:
    review = inspect_city(source, city, sha)
    result = stage_city(source, out, city)
    review.update({"source_file_count": result["file_count"],
                   "source_payload_bytes": result["payload_bytes"],
                   "manifest_sha256": hashlib.sha256(
                       (out / "release-manifest.json").read_bytes()
                   ).hexdigest()})
    # Review metadata is not a price source and must never be mistaken for one.
    (out / "PRIVATE-REVIEW-ONLY.json").write_text(
        json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return review


def tlv_blocker(source: Path, sha: str) -> dict:
    pinned_commit(source, sha)
    root = source / "SUPER.TLV"
    if not root.is_dir():
        raise ValueError("Missing TLV folder")
    html = (root / "index.html").read_text(encoding="utf-8").lower()
    status = json.loads((root / "data/refresh-status.json").read_bytes())
    validate_status(status)
    placeholder = 'http-equiv="refresh"' in html or "אינה זמינה כרגע" in html
    if not placeholder and status["updated_count"] > 0:
        raise ValueError("TLV may have progressed; needs an independent manual acceptance review")
    return {"city": "TLV", "source_commit": sha, "site_placeholder": placeholder,
            "updated_count": status["updated_count"], "branch_count": status["branch_count"],
            "source_checked_at": status["checked_at"],
            "full_private_candidate": False, "approved_for_public": False,
            "public_cutover": False, "collector_invoked": False}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--city", choices=(*REVIEW_CITIES, "TLV"), required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    source = args.source.resolve()
    if args.city == "TLV":
        report = tlv_blocker(source, args.source_sha)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.output.exists():
            raise ValueError("Refusing to overwrite TLV blocker report")
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    else:
        report = stage_candidate(source, args.output, args.city, args.source_sha)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
