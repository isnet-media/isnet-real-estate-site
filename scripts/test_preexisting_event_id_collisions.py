#!/usr/bin/env python3
"""Regression checks for the non-destructive legacy event-ID safety gate."""
from copy import deepcopy
from check_preexisting_event_id_collisions import verify_preserved_duplicates
from sync_events_from_sources import fix_imported_id_collisions


def row(event_id, title):
    return {"event_id": event_id, "title": title, "city": "test"}


def check_rejects(before, after):
    try:
        verify_preserved_duplicates(before, after, "test")
    except AssertionError:
        return
    raise AssertionError("Expected collision safety gate to reject changed records")


def main():
    originals = [row("same", "original a"), row("same", "original b"), row("unique", "old")]
    assert verify_preserved_duplicates(originals, list(originals), "test") == 1
    assert verify_preserved_duplicates(originals, list(reversed(originals)), "test") == 1
    assert verify_preserved_duplicates(
        originals, [originals[0], originals[1], row("unique", "updated")], "test"
    ) == 1
    updated = originals + [row("fresh", "new")]
    assert verify_preserved_duplicates(originals, updated, "test") == 1
    assert verify_preserved_duplicates(
        [row("one", "a")], [row("one", "a"), row("other", "b")], "test"
    ) == 0
    check_rejects(originals, originals + [row("fresh", "a"), row("fresh", "b")])
    check_rejects(originals, [originals[0], originals[2]])
    check_rejects(originals, [originals[0], row("same", "overwritten"), originals[2]])
    check_rejects(originals, originals + [row("same", "duplicated again")])
    check_rejects(originals, [row("same", "original a"), row("same", "original b"),
                              row("same", "third"), originals[2]])
    # An auto-generated identifier can be public/CMS-linked just like a board ID.
    # Previously the importer silently rekeyed pre-existing auto collisions.
    inherited_auto = [
        {"event_id": "auto_ri_old", "title": "legacy show A", "city": "ראשון לציון",
         "start_date": "2026-11-04", "start_time": "20:30", "venue": "Hall A"},
        {"event_id": "auto_ri_old", "title": "legacy show B", "city": "ראשון לציון",
         "start_date": "2026-11-04", "start_time": "21:30", "venue": "Hall B"},
    ]
    snapshot = deepcopy(inherited_auto)
    assert fix_imported_id_collisions(
        inherited_auto, inherited_editorial_ids=frozenset({"auto_ri_old"})
    ) == 0
    assert inherited_auto == snapshot

    fresh_auto = [
        {"event_id": "auto_ri_fresh", "title": "show A", "city": "ראשון לציון",
         "start_date": "2026-11-05", "start_time": "20:30", "venue": "Hall A"},
        {"event_id": "auto_ri_fresh", "title": "show B", "city": "ראשון לציון",
         "start_date": "2026-11-05", "start_time": "20:30", "venue": "Hall B"},
    ]
    assert fix_imported_id_collisions(fresh_auto) == 1
    assert fresh_auto[0]["event_id"] == "auto_ri_fresh"
    assert fresh_auto[1]["event_id"] != fresh_auto[0]["event_id"]
    check_rejects(
        snapshot, [snapshot[0], {**snapshot[1], "event_id": "auto_ri_changed"}]
    )
    print("13 legacy-collision safety scenarios passed")


if __name__ == "__main__":
    main()
