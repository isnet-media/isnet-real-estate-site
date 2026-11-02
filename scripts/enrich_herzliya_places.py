"""Recover venue and park photography from each place's own official page."""
import concurrent.futures
from urllib.parse import urljoin
import sync_herzliya_events as c

def one(x):
 if x.get('image_role')=='official_promotional':return x
 try:
  s=c.get(x['source_url']);main=s.select_one('main,.entry-content,#content,.page-content') or s
  urls=[]
  meta=s.select_one('meta[property="og:image"]')
  if meta:urls.append(meta.get('content',''))
  for im in main.select('img[src],img[data-src]'):
   u=im.get('data-src') or im.get('src');urls.append(urljoin(x['source_url'],u))
  for u in list(dict.fromkeys(urls))[:8]:
   image=c.photo(u,x['source_url'])
   if image:
    x.update(image=image,image_origin_url=u,image_role='official_promotional',image_credit='צילום: אתר '+x['title']);break
 except Exception:pass
 return x

def main():
 x=c.read('guides')
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:x['items']=list(ex.map(one,x['items']))
 c.save('guides',x);print('Local places with source images:',sum(p.get('image_role')=='official_promotional' for p in x['items']))
if __name__=='__main__':main()
