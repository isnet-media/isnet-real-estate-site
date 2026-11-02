"""Expand culinary variety from structured local-address restaurant records."""
import concurrent.futures,json,re
from urllib.parse import urljoin
import sync_herzliya_events as c

def main():
 base='https://www.rest.co.il';s=c.get(base+'/restaurants/herzliya/');links=sorted({urljoin(base,a['href']) for a in s.select('a[href]') if re.fullmatch(r'/rest/\d+/',a['href'])})
 def one(u):
  try:
   s=c.get(u);blocks=[]
   for n in s.select('script[type="application/ld+json"]'):
    try:x=json.loads(n.get_text());blocks.extend(x if isinstance(x,list) else x.get('@graph',[x]))
    except ValueError:pass
   x=next((x for x in blocks if isinstance(x,dict) and 'הרצליה' in json.dumps(x.get('address',{}),ensure_ascii=False)),None)
   if not x:return
   a=x['address'];title=x.get('name') or s.find('h1').get_text(' ',strip=True);d=c.clean(c.BeautifulSoup(x.get('description',''),'html.parser').get_text(' ',strip=True))[:500];text=title+' '+d+' '+str(x.get('servesCuisine',''))
   kind='cafe' if re.search('קפה|מאפ|קונדיט',text) else 'asian' if re.search('סושי|אסיית|סיני|יפני',text) else 'italian' if re.search('פיצ|פסט|איטלק',text) else 'burger' if re.search('המבורגר',text) else 'meat' if re.search('בשר|סטייק',text) else 'street'
   image=x.get('image');image=image[0] if isinstance(image,list) and image else image
   if isinstance(image,dict):image=image.get('url')
   photo=c.photo(image,u)
   if not photo:return
   return dict(id='rest-'+u.strip('/').split('/')[-1],title=title,category='food',subcategory=kind,description=d or 'פרטי המקום והתפריט במקור המקושר.',source_url=u,booking_url=u,address=c.clean(a.get('streetAddress','')+' '+a.get('addressLocality','')),city='הרצליה',image=photo,image_role='official_promotional',image_origin_url=image,image_credit='צילום: עמוד '+title+' ב־Rest',source_checked_at=c.NOW.isoformat(),kosher=None,saturday=None,homepage_featured=True)
  except Exception:return
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:items=[r for r in ex.map(one,links[:45]) if r]
 food=c.read('restaurants');names={c.h.core.text_norm(x['title']) for x in food['items']}
 for x in items:
  if c.h.core.text_norm(x['title']) not in names:food['items'].append(x);names.add(c.h.core.text_norm(x['title']))
 c.save('restaurants',food);print('Structured restaurant records with local address and source photo:',len(items),'total:',len(food['items']))
if __name__=='__main__':main()
