import copy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from repair_stage_source_metadata import board_sources, repair
import swap_our_stage_events_with_boards as importer


class BoardProvenanceTests(unittest.TestCase):
    def test_uses_existing_content_source_without_changing_facts(self):
        event = {'event_id': 'board_1', 'source': 'national_stage_boards',
                 'content_source_url': 'https://example.org/show/1',
                 'title': 'Show', 'start_date': '2026-11-19', 'image_url': None}
        before = copy.deepcopy(event)
        self.assertEqual(repair([event]), ['board_1'])
        self.assertEqual(event.pop('sources'), board_sources(before['content_source_url']))
        self.assertEqual(event, before)

    def test_preserves_existing_provenance_and_is_idempotent(self):
        event = {'event_id': 'board_1', 'source': 'national_stage_boards',
                 'content_source_url': 'https://example.org/show/1'}
        repair([event])
        before = copy.deepcopy(event)
        self.assertEqual(repair([event]), [])
        self.assertEqual(event, before)

    def test_does_not_invent_sources_or_use_purchase_link(self):
        for url in (None, '', 'javascript:alert(1)', 'https://[invalid/', 'https://user:password@example.org/'):
            self.assertEqual(board_sources(url), [])
        event = {'event_id': 'board_1', 'source': 'national_stage_boards',
                 'purchase_url': 'https://example.org/ticket'}
        self.assertEqual(repair([event]), [])
        self.assertNotIn('sources', event)
        self.assertEqual(board_sources('https://example.org/show', 'provider')[0]['name'], 'provider')

    def test_new_import_keeps_collected_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for city in ('ashdod', 'rishon-lezion'):
                folder = root / 'events-preview' / city / 'data'
                folder.mkdir(parents=True)
                (folder / 'events.json').write_text('{"events":[]}')
            collected = root / 'collected.json'
            collected.write_text(json.dumps({'events': [{
                'city': 'rishon-lezion', 'title': 'Test show',
                'date_time': '2030-11-19T20:00:00', 'venue': 'Hall',
                'source_url': 'https://example.org/show/1', 'source_id': 'provider'}]}))
            with patch.object(importer, 'ROOT', root), patch.object(importer, 'COLLECT', collected), \
                 patch.object(importer, 'REPORT', root / 'report.json'), \
                 patch.dict('os.environ', {'STAGE_SWAP_FROM_BOARDS': 'YES_MATCHED_EVENTS_ONLY'}), \
                 contextlib.redirect_stdout(io.StringIO()):
                importer.main()
            events = json.loads((root / 'events-preview/rishon-lezion/data/events.json').read_text())['events']
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]['sources'], board_sources('https://example.org/show/1', 'provider'))


if __name__ == '__main__':
    unittest.main()
