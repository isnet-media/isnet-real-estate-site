"""Official-feed refresh for reviewed physical Bat Yam branches only."""
from pathlib import Path
from datetime import datetime,timedelta
import argparse,json,re
from super_city_runtime import load

def collector():
 c=load('refresh_super_prices','BATYAM');c.ACCOUNTS['AM:PM']='doralon';base_listing=c.listing
 def listing(b):
  if b['chain']=='מחסני השוק':return base_listing(dict(b,chain='ויקטורי'))
  if b['chain'] in ('שוק העיר','נטו חיסכון','סופר ספיר','סופר ברקת'):
   base=b['source_url'].rstrip('/')+'/'
   assert base in ('https://shuk-hayir.binaprojects.com/','https://supersapir.binaprojects.com/','https://superbareket.binaprojects.com/')
   s=c.session();c.request(s,base+'Main.aspx');entries=[]
   for day in (datetime.now(c.TZ).date(),datetime.now(c.TZ).date()-timedelta(days=1)):
    js=c.request(s,base+'MainIO_Hok.aspx',method='POST',data={'wReshet':'','WStore':str(int(b['store_id'])),'WDate':day.strftime('%d/%m/%Y'),'WFileType':'0'}).json()
    for x in js:
     n=x.get('FileNm','')
     if n.startswith(('Price','Promo')):entries.append({'name':n,'url':base+'Download/'+n})
   return s,list({x['name']:x for x in entries}.values())
  if b['chain']=='חצי חינם':
   from bs4 import BeautifulSoup
   from urllib.parse import urlparse,unquote
   s=c.session();entries=[]
   for day in (datetime.now(c.TZ).date(),datetime.now(c.TZ).date()-timedelta(days=1)):
    for page in range(1,31):
     html=c.request(s,'https://shop.hazi-hinam.co.il/Prices',params={'s':int(b['store_id']),'d':day.isoformat(),'p':page}).text
     soup=BeautifulSoup(html,'html.parser');batch=[]
     for a in soup.select('a[href]'):
      url=a['href']
      if not url.startswith('https://hazihinamprod01.blob.core.windows.net/regulatories/'):continue
      name=unquote(urlparse(url).path.rsplit('/',1)[-1])
      if name.startswith(('Price','Promo')):batch.append({'name':name,'url':url})
     entries.extend(batch)
     pages=[int(a.get_text().strip()) for a in soup.select('a[href]') if '?p=' in a['href'] and a.get_text().strip().isdigit()]
     if not pages or page>=max(pages):break
    else:raise ValueError('Truncated Hazi Hinam publication listing')
   return s,list({x['name']:x for x in entries}.values())
  return base_listing(b)
 c.listing=listing
 return c

def run(raw_dir):
 c=collector();deals=load('build_super_deals','BATYAM')
 import build_super_deals
 old=build_super_deals.build;build_super_deals.build=deals.build
 try:r=c.run(raw_dir)
 finally:build_super_deals.build=old
 D=c.D;cat=json.loads((D/'catalog.json').read_text());cat['coverage_complete']=r['all_sources_updated'];c.write(D/'catalog.json',cat)
 p=json.loads((D/'prices.json').read_text());p['coverage_complete']=cat['coverage_complete'];c.write(D/'prices.json',p)
 s=json.loads((D/'source-status.json').read_text());s.pop('connection_notes',None);c.write(D/'source-status.json',s)
 d=json.loads((D/'deals.json').read_text());d['city']='בת ים'
 for deal in d.get('deals',[]):
  if re.search(r'^(?:אבקת מרק|מרק\s*400)',deal['name']):deal['category']='מזווה ומוצרים לבית'
 c.write(D/'deals.json',d)
 return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--raw-dir',type=Path,required=True);a=p.parse_args();run(a.raw_dir)
