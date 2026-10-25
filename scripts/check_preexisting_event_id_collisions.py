#!/usr/bin/env python3
"""Read-only safety gate for inherited duplicate event IDs in city feeds.

The current Rishon feed contains previously reported duplicate identifiers.
Reject new collisions, loss of existing collision records, and changes to
colliding records. Unrelated unique records may still be added or updated.
This script never deletes, rekeys, modifies or publishes any records.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess


CITY_SLUGS = ("ashdod", "rishon-lezion")


def _identity(event):
    return json.dumps(event, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def duplicate_groups(events):
    counts = Counter(e.get("event_id") for e in events)
    return {
        event_id: Counter(_identity(e) for e in events if e.get("event_id") == event_id)
        for event_id, count in counts.items()
        if count > 1
    }


def verify_preserved_duplicates(baseline, current, city):
    previous = duplicate_groups(baseline)
    present = duplicate_groups(current)
    old_ids = set(previous)
    new_ids = set(present)
    if old_ids != new_ids:
        raise AssertionError(
            f"{city}: collision groups changed; new={sorted(map(str, new_ids-old_ids))}, "
            f"removed={sorted(map(str, old_ids-new_ids))}. Preserve records for manual review."
        )
    for event_id in old_ids:
        if previous[event_id] != present[event_id]:
            raise AssertionError(
                f"{city}: colliding event_id {event_id!r} changed; do not overwrite or rekey "
                "unverified collision records."
            )
    return len(old_ids)


def audit_ref(baseline_ref):
    for city in CITY_SLUGS:
        path = Path("events-preview") / city / "data" / "events.json"
        old_text = subprocess.check_output(
            ["git", "show", f"{baseline_ref}:{path.as_posix()}"], text=True
        )
        baseline = json.loads(old_text)["events"]
        current = json.loads(path.read_text(encoding="utf-8"))["events"]
        inherited = verify_preserved_duplicates(baseline, current, city)
        print(f"{city}: legacy collision groups preserved={inherited}; new collisions=0")
        if inherited:
            print(
                f"::warning::{city}: {inherited} inherited collision groups retained for "
                "identity/source/CMS review; no automatic deletion or rekey."
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-ref", default="HEAD")
    args = parser.parse_args()
    audit_ref(args.baseline_ref)


if __name__ == "__main__":
    main()
