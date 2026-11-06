#!/usr/bin/env python3
"""Restore missing board provenance from the source URL already in each record."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def board_sources(url, name=None):
    if not isinstance(url, str):
        return []
    try:
        parsed = urlsplit(url)
    except ValueError:
        return []
    if parsed.scheme not in ('https', 'http') or not parsed.hostname or parsed.username or parsed.password:
        return []
    return [{'name': name or parsed.hostname, 'url': url, 'source_type': 'national_board'}]


def repair(events):
    changed = []
    for event in events:
        if event.get('source') != 'national_stage_boards' or event.get('sources'):
            continue
        sources = board_sources(event.get('content_source_url'))
        if sources:
            event['sources'] = sources
            changed.append(event['event_id'])
    return changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    for city in ('ashdod', 'rishon-lezion'):
        path = ROOT / 'events-preview' / city / 'data/events.json'
        data = json.loads(path.read_text())
        changed = repair(data['events'])
        if changed and args.apply:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        print(city + ': ' + json.dumps(changed))


if __name__ == '__main__':
    main()
