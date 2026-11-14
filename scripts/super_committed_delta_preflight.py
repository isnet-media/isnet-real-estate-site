"""Read-only gate for copying ALREADY-COMMITTED supermarket editions to private storage.

Compares seven pinned private releases with the current verified Git main tree.
It NEVER collects prices, writes storage, changes DNS, or marks stale data fresh.
A changed source tree is a review candidate, not permission to cut over.
"""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIX_RELEASE = "5958cfaca9a61eacfdb1aa216635c3d3ff810850"
PINNED = dict.fromkeys(("ASHDOD", "BATYAM", "HOLON", "KGAT", "RISHON", "YAVNE"), SIX_RELEASE)
PINNED["TLV"] = "c674f83485453570106ce39a55c9c66f3a061ec3"
REQUIRED = ("data/prices.json", "data/refresh-status.json", "data/source-status.json")
FIVE_MINUTES = timedelta(minutes=5)

def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)

def tree_files(ref, city):
    prefix = "SUPER." + city + "/"
    out = {}
    data = git("ls-tree", "-r", "-z", ref, "--", prefix)
    for row in data.split(bytes([0])):
        if not row:
            continue
        info, raw_path = row.split(bytes([9]), 1)
        mode, kind, sha = info.decode("ascii").split(" ")
        path = raw_path.decode("utf-8")
        if mode != "100644" or kind != "blob" or not path.startswith(prefix):
            raise ValueError("Unexpected source entry (symlink or type): " + path)
        out[path] = sha
    for item in REQUIRED:
        if prefix + item not in out:
            raise ValueError("Missing required committed source: " + prefix + item)
    return out

def blob(ref, city, item):
    # Fixed allowlisted city, known relative paths; no shell expansion.
    return git("show", ref + ":SUPER." + city + "/" + item)

def parse_checked_at(status):
    value = status.get("checked_at")
    if not isinstance(value, str):
        raise ValueError("Missing checked_at in committed refresh metadata")
    checked = datetime.fromisoformat(value)
    if checked.tzinfo is None:
        raise ValueError("checked_at missing timezone; cannot compare freshness")
    return checked.astimezone(timezone.utc)

def validate_status(status):
    checked = parse_checked_at(status)
    branches = status.get("branches")
    if not isinstance(branches, list):
        raise ValueError("Missing branch provenance")
    total = status.get("branch_count")
    updated = status.get("updated_count")
    if type(total) is not int or type(updated) is not int or total <= 0:
        raise ValueError("Invalid branch counts")
    if not (0 <= updated <= total) or len(branches) != total:
        raise ValueError("Count mismatch in committed branch status")
    confirmed = sum(1 for x in branches if x.get("status") == "updated")
    if confirmed != updated:
        raise ValueError("Updated count does not match branch provenance")
    full = status.get("all_sources_updated")
    if type(full) is not bool or full != (updated == total):
        raise ValueError("all_sources_updated disagrees with branch counts")
    return checked

def evaluate(base, candidate, changed, now):
    old = validate_status(base)
    new = validate_status(candidate)
    if new > now + FIVE_MINUTES:
        return "blocked", "source checked_at is in the future"
    if not changed:
        return "unchanged", "No committed source file changed"
    if new < old:
        return "blocked", "Candidate source timestamp regressed"
    if any(x.startswith("data/") for x in changed) and new <= old:
        return "blocked", "Data changed without newer validated source timestamp"
    return "private_candidate_review", ("New committed edition requires private SHA256 readback, "
                                        "partial-source disclosure, asset rights review, and no public cutover")

def audit(candidate_ref="origin/main"):
    report = {
        "candidate_commit": git("rev-parse", candidate_ref + "^{commit}").decode().strip(),
        "public_cutover": False, "storage_writes": False, "collector_invoked": False,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "cities": [], "blocked": 0, "changed_cities": 0
    }
    now = datetime.now(timezone.utc)
    for city, release in sorted(PINNED.items()):
        city_report = {"city": city, "pinned_private_release": release}
        try:
            origin = tree_files(release, city)
            current = tree_files(candidate_ref, city)
            changed = sorted(p.removeprefix("SUPER." + city + "/")
                             for p in set(origin) | set(current) if origin.get(p) != current.get(p))
            base_status = json.loads(blob(release, city, "data/refresh-status.json"))
            next_status = json.loads(blob(candidate_ref, city, "data/refresh-status.json"))
            state, reason = evaluate(base_status, next_status, changed, now)
            if state != "unchanged":
                report["changed_cities"] += 1
            if state == "blocked":
                report["blocked"] += 1
            city_report.update({
                "state": state, "reason": reason, "changed_files": len(changed),
                "changed_paths": changed[:25], "changed_paths_truncated": len(changed) > 25,
                "pinned_file_count": len(origin), "candidate_file_count": len(current),
                "source_checked_at": next_status["checked_at"],
                "updated_branches": next_status["updated_count"],
                "total_branches": next_status["branch_count"],
                "coverage_status": next_status.get("coverage_status"),
                "all_sources_updated": next_status["all_sources_updated"],
                "critical_sha256": {
                    name: hashlib.sha256(blob(candidate_ref, city, name)).hexdigest()
                    for name in REQUIRED
                }
            })
            # Structural validation only: do not rewrite or claim new supplier data.
            for name in REQUIRED:
                json.loads(blob(candidate_ref, city, name))
        except (ValueError, KeyError, subprocess.CalledProcessError, UnicodeDecodeError) as ex:
            report["blocked"] += 1
            city_report.update({"state": "blocked", "reason": str(ex)})
        report["cities"].append(city_report)
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-ref", default="origin/main")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summary = audit(args.candidate_ref)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_commit": summary["candidate_commit"],
                      "blocked": summary["blocked"], "changed_cities": summary["changed_cities"],
                      "states": {city["city"]: city["state"] for city in summary["cities"]}},
                     ensure_ascii=False))
    if summary["blocked"]:
        raise SystemExit("Refusing private export: invalid or regressed committed sources")

if __name__ == "__main__":
    main()
