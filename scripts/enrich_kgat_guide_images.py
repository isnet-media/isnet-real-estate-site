"""Local JPG illustrations with visible disclosure; approved originals always win."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CITY=ROOT/'events-preview/kiryat-gat'
BASE='https://isnet.co.il/events-preview/kiryat-gat/assets/illustrations/'
CREDIT='תמונת המחשה שנוצרה בבינה מלאכותית — לא צילום מהמקום או מהאירוע'
def event_image(e):
 if e.get('image_publishable') and e.get('image_verified') and e.get('source_image_kind')!='illustration':return
 name='basketball' if e.get('sport_branch')=='כדורסל' else 'football' if e.get('managed_by')=='kgat_sports' else 'gentle-fitness' if e.get('category')=='seniors' else 'live-music' if e.get('category')=='music' else None
 if not name:return
 e.update(image_url='assets/illustrations/'+name+'.jpg',image_source=BASE+name+'.jpg',image_credit=CREDIT,image_publishable=True,image_verified=True,image_represents_event=False,source_image_kind='illustration',image_rights_status='ai_generated_activity_illustration')
def place_image(p,category='culture'):
 if p.get('image') and p.get('image_role')!='illustration':return
 id=p.get('id','')
 name='pool' if id=='kgat-country' else 'park' if id=='kgat-paz' else 'nature' if category in ['nature','parks'] or id in ['kgat-archaeology','kgat-lachish','kgat-angels','kgat-beit-guvrin','kgat-lachish-saturday'] else 'book-club' if id=='kgat-library' else 'live-music' if id=='kgat-amphi' else 'theatre-stage'
 p.update(image=BASE+name+'.jpg',image_credit=CREDIT,image_alt='תמונת המחשה בלבד',image_role='illustration')
def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def run():
 file=CITY/'data/events.json';d=json.loads(file.read_text())
 for e in d['events']:event_image(e)
 save(file,d)
 file=CITY/'data/places.json';d=json.loads(file.read_text())
 for key,cat in d['categories'].items():
  if not cat.get('hero_image') or cat.get('hero_image_role')=='illustration':
   cat['hero_image']=BASE+('park' if key=='parks' else 'nature' if key=='nature' else 'theatre-stage')+'.jpg'
   cat['hero_image_role']='illustration'
  if 'תמונות המחשה' not in cat.get('intro',''):cat['intro']=cat.get('intro','')+' התמונות המסומנות הן תמונות המחשה.'
  for item in cat.get('items',[]):place_image(item,key)
 save(file,d)
 for filename,key in [('institutions','institutions'),('attractions-guide','verified_sources'),('saturday-guide','items')]:
  file=CITY/'data'/ (filename+'.json');d=json.loads(file.read_text())
  for item in d.get(key,[]):place_image(item,'nature' if filename=='saturday-guide' else 'culture')
  save(file,d)
 print('Kiryat Gat event and guide images populated; approved originals preserved.')
if __name__=='__main__':run()
