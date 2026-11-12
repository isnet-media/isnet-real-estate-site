"""Scheduled-day freshness and no-network guards for delayed health jobs."""
from datetime import datetime
from unittest.mock import patch
from check_super_public import collection_due
import check_super_public as health
from super_schedule import in_window

def at(s): return datetime.fromisoformat(s)
last='2026-11-12T09:00:00+02:00' # Thursday
for stamp in ['2026-11-13T11:00:00+02:00','2026-11-14T11:00:00+02:00',
              '2026-11-15T10:29:59+02:00']:
 assert not collection_due(last,at(stamp)),stamp
assert collection_due(last,at('2026-11-15T10:30:00+02:00'))
sunday='2026-11-15T09:00:00+02:00'
assert not collection_due(sunday,at('2026-11-16T11:00:00+02:00'))
assert not collection_due(sunday,at('2026-11-17T10:29:59+02:00'))
assert collection_due(sunday,at('2026-11-17T10:30:00+02:00'))
assert not collection_due('2026-11-17T09:00:00+02:00',at('2026-11-17T11:00:00+02:00'))
assert collection_due('2026-10-22T09:00:00+03:00',at('2026-10-25T10:30:00+02:00'))
for stamp in ['2026-11-15T12:00:00+02:00','2026-11-15T18:00:00+02:00',
              '2026-11-16T09:00:00+02:00','2026-07-07T09:00:00+00:00']:
 with patch.object(health,'now',at(stamp)),patch.object(health.requests,'get',side_effect=AssertionError('HTTP outside window')):
  health.main()
assert in_window(at('2026-07-07T08:00:00+00:00'),health=True) # 11 summer
assert not in_window(at('2026-07-07T09:00:00+00:00'),health=True) # noon summer
print('PASS: scheduled-day freshness, grace, DST and no HTTP outside approved mornings')
