import copy,json,tempfile,unittest
from pathlib import Path
from repair_event_quality import repair,run
TAX={'primary_categories':[{'id':'standup','subcategories':[{'id':'standup','label':'סטנדאפ'},{'id':'raw','label':'event'}]},{'id':'music','subcategories':[{'id':'concerts','label':'קונצרטים'}]}]}
DEFS={'categories':{'standup':{'subcategories':{'standup':{'label':'סטנדאפ'}}},'music':{'subcategories':{'concerts':{'label':'קונצרטים'}}}}}
CLIPS={'artists':[{'name':'אמן לדוגמה','aliases':['אמן לדוגמה'],'youtube_id':'abcdefghijk','youtube_title':'קטע מייצג','video_verified':True,'verified_at':'2026-10-19'}]}
def event(id='one',**kw):return dict(event_id=id,title='אמן לדוגמה במופע סטנדאפ',category='standup',start_date='2026-11-01',description='תיאור מקור',venue='אולם',**kw)
class Tests(unittest.TestCase):
 def test_repairs_and_idempotence(self):
  data={'events':[event()]};out,tax,changes,issues=repair(data,TAX,DEFS,CLIPS,'2026-10-20')
  self.assertEqual(out['events'][0]['subcategory'],'standup');self.assertEqual(out['events'][0]['youtube_id'],'abcdefghijk');self.assertTrue(tax['primary_categories'][0]['subcategories'][1]['requires_mapping']);self.assertEqual(data,{'events':[event()]})
  self.assertEqual(repair(out,tax,DEFS,CLIPS,'2026-10-20')[2],[])
 def test_locks_and_unavailable_catalog(self):
  e=event(locked_fields=['subcategory','youtube_id']);out,_,_,_=repair({'events':[e]},TAX,DEFS,CLIPS,'2026-10-20');self.assertNotIn('subcategory',out['events'][0]);self.assertNotIn('youtube_id',out['events'][0])
  old=copy.deepcopy(CLIPS);old['artists'][0]['verified_at']='2020-01-01';self.assertNotIn('youtube_id',repair({'events':[event()]},TAX,DEFS,old,'2026-10-20')[0]['events'][0])
 def test_ambiguous_artist_and_future_verification(self):
  e=event();e['title']='אמן לדוגמה ואמן אחר במופע סטנדאפ';self.assertNotIn('youtube_id',repair({'events':[e]},TAX,DEFS,CLIPS,'2026-10-20')[0]['events'][0])
  c=copy.deepcopy(CLIPS);c['artists'][0]['verified_at']='2027-01-01';self.assertNotIn('youtube_id',repair({'events':[event()]},TAX,DEFS,c,'2026-10-20')[0]['events'][0])
 def test_same_source_image_only(self):
  a=event('a',content_source_url='https://official/event/1',image_url='https://official/photo.jpg',image_verified=True,image_publishable=True,source_image_kind='source_card_image');b=event('b',content_source_url='https://official/event/1');c=event('c',content_source_url='https://official/event/2')
  result=repair({'events':[a,b,c]},TAX,DEFS,CLIPS,'2026-10-20')[0]['events'];self.assertEqual(result[1]['image_url'],a['image_url']);self.assertNotIn('image_url',result[2])
 def test_ambiguous_donor_and_manual_image(self):
  a=event('a',content_source_url='u',image_url='https://official/a.jpg',image_verified=True,image_publishable=True);b={**a,'event_id':'b','image_url':'https://official/b.jpg'};c=event('c',content_source_url='u');self.assertNotIn('image_url',repair({'events':[a,b,c]},TAX,DEFS,CLIPS,'2026-10-20')[0]['events'][2])
  c['image_manual_override']=True;self.assertNotIn('image_url',repair({'events':[a,c]},TAX,DEFS,CLIPS,'2026-10-20')[0]['events'][1])
 def test_duplicates_and_inactive(self):
  e=event();self.assertEqual(len(repair({'events':[e,e]},TAX,DEFS,CLIPS,'2026-10-20')[0]['events']),1)
  with self.assertRaises(ValueError):repair({'events':[e,{**e,'title':'אחר'}]},TAX,DEFS,CLIPS,'2026-10-20')
  e['status']='hidden';self.assertEqual(repair({'events':[e]},TAX,DEFS,CLIPS,'2026-10-20')[0]['events'][0],e)
 def test_failed_validation_writes_nothing(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);admin=root/'events-preview/admin/data';admin.mkdir(parents=True);feed=root/'events-preview/ashdod/data';feed.mkdir(parents=True);shared=root/'events-preview/shared';shared.mkdir()
   e=event();payload=json.dumps({'events':[e,{**e,'title':'conflict'}]});(feed/'events.json').write_text(payload);(admin/'taxonomy.json').write_text(json.dumps(TAX));(admin/'subcategory-definitions.json').write_text(json.dumps(DEFS));(shared/'standup-videos.json').write_text(json.dumps(CLIPS))
   with self.assertRaises(ValueError):run(root,True,'2026-10-20')
   self.assertEqual((feed/'events.json').read_text(),payload);self.assertFalse((admin/'automatic-repair-status.json').exists())
if __name__=='__main__':unittest.main()
