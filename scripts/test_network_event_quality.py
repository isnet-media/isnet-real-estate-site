"""Behavioral checks for publication age, source/public selection and honest audit baselines."""
import json,tempfile,unittest
from datetime import datetime,timezone
from pathlib import Path
import audit_network_event_quality as audit
class HealthTests(unittest.TestCase):
 def test_expiry_and_visibility(self):
  self.assertFalse(audit.future({'start_date':'2026-11-01'},'2026-11-02'))
  self.assertTrue(audit.future({'start_date':'2026-11-01','end_date':'2026-11-03'},'2026-11-02'))
  for field,value in [('status','cancelled'),('publication_status','draft'),('is_active',False)]:
   self.assertFalse(audit.future({'start_date':'2026-12-01',field:value},'2026-11-02'))
 def test_public_schema_and_audiences(self):
  self.assertTrue(audit.feed_path('herzliya').endswith('events-public.json'))
  self.assertTrue(audit.feed_path('holon').endswith('events-public.json'))
  self.assertTrue(audit.audience({'category':'lecture','category_memberships':[{'category':'seniors'}]},'seniors'))
  self.assertFalse(audit.audience({'category':'kids','audiences':['kids']},'seniors'))
 def test_age_uses_collection_timestamp_not_file_modification(self):
  with tempfile.TemporaryDirectory() as tmp:
   old=audit.ROOT;audit.ROOT=Path(tmp)
   try:
    directory=audit.ROOT/'events-preview/ashdod/data';directory.mkdir(parents=True)
    (directory/'events.json').write_text(json.dumps({'generated_at':'2026-10-24T09:00:00Z','events':[{'event_id':'one','title':'אירוע','start_date':'2026-11-03','category':'kids','image_url':'assets/missing.jpg'}]}))
    (directory/'restaurants.json').write_text('{"restaurants":[]}')
    report=audit.report_city('ashdod',now=datetime(2026,11,2,tzinfo=timezone.utc))
    self.assertEqual(report['freshness'],'stale');self.assertEqual(report['baseline']['state'],'unavailable')
    self.assertEqual(report['new_event_ids_since_baseline'],0,'Missing history must never label the whole feed as new')
    self.assertEqual(len(report['missing_local_event_media']),1)
   finally:audit.ROOT=old
if __name__=='__main__':unittest.main()
