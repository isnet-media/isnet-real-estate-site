#!/usr/bin/env python3
"""Regression checks for the non-destructive legacy event-ID safety gate."""
from check_preexisting_event_id_collisions import verify_preserved_duplicates


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
    print("10 legacy-collision safety scenarios passed")


if __name__ == "__main__":
    main()
