"""Ensure storage migration cannot publish or modify unrelated news/events/assets."""
import hashlib
import json
from pathlib import Path
import sys
from prepare_pages_public import ROOT, delivery_cities
before,after=map(Path,sys.argv[1:])
cities={'SUPER.'+c for c in delivery_cities(ROOT)}
untouched=0
for path in before.rglob('*'):
    if not path.is_file():continue
    rel=path.relative_to(before);parts=rel.parts
    if str(rel) in {'deployment-version.json','super-delivery-status.json'}:continue
    if len(parts)>2 and parts[0] in cities and parts[1]=='data':
        assert not (after/rel).exists(),str(rel)
        continue
    actual=(after/rel).read_bytes();original=path.read_bytes()
    if parts[0] in cities and path.suffix=='.html':
        import re
        actual=re.sub(rb'<script data-super-delivery="[a-f0-9]{40}">.*?</script>',b'',actual,count=1,flags=re.S)
    assert actual==original,'Unexpected public change: '+str(rel)
    untouched+=1
print(json.dumps({'unchanged_public_files':untouched,'editorial_rebuild':False,'prices_rewritten':False}))
