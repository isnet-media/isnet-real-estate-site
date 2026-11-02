"""Reviewed locality, duplicate occurrence and media safeguards before publication."""
import json,re
from difflib import SequenceMatcher
import sync_herzliya_events as c

def main():
 raw=c.read('events');before=len(raw['events']);out=[]
 def identity(e):
  t=c.h.core.text_norm(e['title'])
  for key in ['היומן','מדיאה','נוסטרדמוס','או לה לה','היפהפייה הנרדמת','היפיפיה הנרדמת']:
   if key in t:return 'היפהפיה הנרדמת' if 'נרדמת' in key else key
  if 'תזמורת המהפכה' in t and 'יוסי בנאי' in t:return 'תזמורת המהפכה יוסי בנאי'
  if e['start_date']=='2026-11-08' and 'קונצרט' in t:return 'סימפונית חיפה קונצרט 1'
  return t
 for e in raw['events']:
  if 'מרכז אגדה' in e['title']:e['category']='kids';e['subcategory']='kids-workshops'
  t=e['title']
  if re.search('ילדים|פעוט|תינוק|גן עם אמא|תנועה עם ניצן|החתול במגפי|תירס חם|דן דן הנגן|שומרי הדרקונים|סינדרלה|שעת סיפור|לגילאי [1-9]',t):e['category']='kids';e['subcategory']='kids-shows'
  elif re.search('גמלא|ותיק|הרצא|זמן זהב|בריאות|מסע עולמי|הערים המרתקות',t) and e['category']!='cinema':e['category']='lecture';e['subcategory']='general-lectures'
  elif re.search('היומן|מדיאה|בלט|נוסטרדמוס|מחול',t):e['category']='theatre';e['subcategory']='theatre'
  title=identity(e);found=None
  for other in out:
   if e['start_date']!=other['start_date'] or e['start_time']!=other['start_time']:continue
   ot=identity(other)
   if title==ot or min(len(title),len(ot))>=8 and (title.startswith(ot+' ') or ot.startswith(title+' ') or SequenceMatcher(None,title,ot).ratio()>.77):found=other;break
  if found:
   found.setdefault('additional_sources',[])
   for url in [e['source_url'],*e.get('additional_sources',[])]:
    if url!=found['source_url'] and url not in found['additional_sources']:found['additional_sources'].append(url)
   if found.get('image_role')!='official_promotional' and e.get('image_role')=='official_promotional':
    for field in ['image','image_origin_url','image_credit','image_role']:found[field]=e[field]
   if len(e['description'])>len(found['description']):found['description']=e['description']
   found['audiences']=list(set(found.get('audiences',[])+e.get('audiences',[])))
  else:out.append(e)
 raw['events']=out;c.save('events',raw);print('Deduplicated',len(out),'occurrences from',before)
if __name__=='__main__':main()
