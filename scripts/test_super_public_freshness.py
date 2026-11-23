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
assert not collection_due(last,at('2026-11-15T10:30:00+02:00'))
sunday='2026-11-15T09:00:00+02:00'
assert not collection_due(sunday,at('2026-11-16T11:00:00+02:00'))
assert not collection_due(sunday,at('2026-11-17T10:29:59+02:00'))
assert collection_due(sunday,at('2026-11-17T10:30:00+02:00'))
assert not collection_due('2026-11-17T09:00:00+02:00',at('2026-11-17T11:00:00+02:00'))
assert not collection_due('2026-10-22T09:00:00+03:00',at('2026-10-25T10:30:00+02:00'))
for stamp in ['2026-11-15T12:00:00+02:00','2026-11-15T18:00:00+02:00',
              '2026-11-16T09:00:00+02:00','2026-07-07T09:00:00+00:00']:
 with patch.object(health,'now',at(stamp)),patch.object(health.requests,'get',side_effect=AssertionError('HTTP outside window')):
  health.main()
assert in_window(at('2026-07-07T08:00:00+00:00'),health=True) # 11 summer
assert not in_window(at('2026-07-07T09:00:00+00:00'),health=True) # noon summer
print('PASS: scheduled-day freshness, grace, DST and no HTTP outside approved mornings')

# Public pages use Pages; ISNET JSON uses one pinned release; TLV has its own API.
from unittest.mock import Mock
release = 'a' * 40
fresh_date = '2026-11-15'
branch = {'id': 'branch-1', 'file_date': fresh_date}
refresh = {'checked_at': fresh_date + 'T09:00:00+02:00',
           'branches': [{'branch_id': 'branch-1', 'status': 'updated'}]}
price_data = {'branch_count': 1, 'branches': [branch]}

def response_for(url, **kwargs):
    if url.endswith('/release'):
        return Mock(json=Mock(return_value={'source_commit': release}))
    if 'refresh-status.json' in url:
        return Mock(json=Mock(return_value=refresh))
    return Mock(json=Mock(return_value=price_data))

with patch.object(health, 'now', at('2026-11-15T11:00:00+02:00')):
    with patch.object(health.requests, 'get', side_effect=response_for) as request:
        assert health.get_delivery_release() == release
        assert health.check('KGAT', 1, release) == ('KGAT', [])
        assert health.check('TLV', 1) == ('TLV', [])
        urls = {call.args[0] for call in request.call_args_list}
        assert 'https://isnet.co.il/SUPER.KGAT/deals/' in urls
        for name in ('prices.json', 'catalog.json', 'refresh-status.json'):
            assert f'{health.DELIVERY_ORIGIN}/SUPER.KGAT/data/{name}?__release={release}' in urls
            assert f'https://tlvnet.com/api/super-data/{name}' in urls
            assert f'https://isnet.co.il/SUPER.KGAT/data/{name}' not in urls
    with patch.object(health.requests, 'get') as request:
        assert health.check('KGAT', 1)[1] == ['Independent data release unavailable']
        request.assert_not_called()
    with patch.object(health.requests, 'get', return_value=Mock(json=Mock(return_value={'source_commit': '../bad'}))):
        try:
            health.get_delivery_release()
        except ValueError:
            pass
        else:
            raise AssertionError('Malformed release accepted')
print('PASS: release pin, city isolation, live page routes and unavailable delivery handling')
