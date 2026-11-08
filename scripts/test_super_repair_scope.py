"""An active city must reject even a syntactically valid repair before writes."""
import json,tempfile
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from unittest.mock import patch
import apply_super_repair as repair
with tempfile.TemporaryDirectory() as directory:
 root=Path(directory);(root/'.supermarket-repair').mkdir();(root/'.supermarket-runs').mkdir()
 (root/'.supermarket-repair/manifest.json').write_text(json.dumps({'cities':{'YAVNE':{}}}))
 (root/'.supermarket-runs/YAVNE.json').write_text(json.dumps({'status':'started','started_at':datetime.now(ZoneInfo('Asia/Jerusalem')).isoformat()}))
 with patch.object(repair,'ROOT',root):
  try:repair.apply('YAVNE')
  except AssertionError as error:assert 'Daily collection is active' in str(error)
  else:raise AssertionError('Active collector was not protected')
  try:repair.apply('HOLON')
  except AssertionError:pass
  else:raise AssertionError('City outside partial manifest was accepted')
 assert not (root/'SUPER.YAVNE').exists(),'Repair wrote files before checking active claim'
print('PASS: active collection and out-of-package city rejected before any data write')
