#!/usr/bin/env python3
"""Recover existing event provenance before applying the verified institution registry."""
import json
from urllib.parse import urlsplit
from enrich_events_institutions import BASE, CITIES, apply_registry

def ensure_source_reference(event):
    """Recover provenance already present on the record, without claiming a fresh verification."""
    if event.get("sources"):
        return 0
    url = next((event.get(key) for key in ("content_source_url", "detail_source_url", "source_url", "purchase_url", "ticket_url")
                if isinstance(event.get(key), str) and urlsplit(event[key]).scheme in ("http", "https") and urlsplit(event[key]).hostname), None)
    name = next((event.get(key) for key in ("local_source_name", "source_id", "source") if isinstance(event.get(key), str) and event[key].strip()), None)
    if not name and url:
        name = urlsplit(url).hostname
    if not name:
        return 0
    reference = {"name": name, "provenance_origin": "existing_event_metadata"}
    if url:
        reference["url"] = url
    if event.get("source_event_id"):
        reference["source_event_id"] = str(event["source_event_id"])
    event["sources"] = [reference]
    return 1


def normalize(event, institutions):
    return ensure_source_reference(event) + apply_registry(event, institutions)

def main():
    for city in CITIES:
        path=BASE/city/'data/events.json'
        doc=json.loads(path.read_text())
        registry=json.loads((BASE/city/'data/institutions.json').read_text())['institutions']
        changed=sum(bool(normalize(event,registry)) for event in doc['events'])
        if changed:
            path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
        print('PROVENANCE',city,'updated',changed,'events',len(doc['events']),flush=True)

if __name__=='__main__':main()
