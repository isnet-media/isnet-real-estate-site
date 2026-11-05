"""Detect a missed morning even when yesterday's snapshot is under 30 hours old."""
from datetime import datetime
from check_super_public import collection_due
def at(s):return datetime.fromisoformat(s)
yesterday='2026-11-04T09:28:04+02:00'
assert not collection_due(yesterday,at('2026-11-05T07:59:00+02:00'))
assert collection_due(yesterday,at('2026-11-05T08:00:00+02:00'))
assert not collection_due('2026-11-05T06:40:00+02:00',at('2026-11-05T09:54:00+02:00'))
friday='2026-11-06T06:30:00+02:00'
assert not collection_due(friday,at('2026-11-07T20:00:00+02:00'))
assert not collection_due(friday,at('2026-11-08T07:59:00+02:00'))
assert collection_due(friday,at('2026-11-08T08:00:00+02:00'))
assert collection_due('2026-10-24T06:30:00+03:00',at('2026-10-25T08:00:00+02:00'))
print('Passed: missed morning, two-hour grace, Saturday pause, Sunday resumption and DST')
