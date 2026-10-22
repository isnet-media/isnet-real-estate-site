"""Official-feed refresh for reviewed physical Kiryat Gat branches only."""
from pathlib import Path
from datetime import datetime,timedelta
import argparse,json
from super_city_runtime import load

def collector():
 c=load('refresh_super_prices','KGAT');base_listing=c.listing
 def listing(b):
  if b['chain']=='מחסני השוק':return base_listing(dict(b,chain='ויקטורי'))
  if b['chain'] in ('שוק העיר','נטו חיסכון'):
   base=b['source_url'].rstrip('/')+'/'
   assert base in ('https://shuk-hayir.binaprojects.com/','https://supersapir.binaprojects.com/')
   s=c.session();c.request(s,base+'Main.aspx');entries=[]
   for day in (datetime.now(c.TZ).date(),datetime.now(c.TZ).date()-timedelta(days=1)):
    js=c.request(s,base+'MainIO_Hok.aspx',method='POST',data={'wReshet':'','WStore':str(int(b['store_id'])),'WDate':day.strftime('%d/%m/%Y'),'WFileType':'0'}).json()
    for x in js:
     n=x.get('FileNm','')
     if n.startswith(('Price','Promo')):entries.append({'name':n,'url':base+'Download/'+n})
   return s,list({x['name']:x for x in entries}.values())
  return base_listing(b)
 c.listing=listing
 return c

def run(raw_dir):
 c=collector();deals=load('build_super_deals','KGAT')
 import build_super_deals
 old=build_super_deals.build;build_super_deals.build=deals.build
 try:r=c.run(raw_dir)
 finally:build_super_deals.build=old
 D=c.D;cat=json.loads((D/'catalog.json').read_text());cat['coverage_complete']=r['all_sources_updated'];c.write(D/'catalog.json',cat)
 p=json.loads((D/'prices.json').read_text());p['coverage_complete']=cat['coverage_complete'];c.write(D/'prices.json',p)
 s=json.loads((D/'source-status.json').read_text());s.pop('connection_notes',None);c.write(D/'source-status.json',s)
 d=json.loads((D/'deals.json').read_text());d['city']='קריית גת';c.write(D/'deals.json',d)
 return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--raw-dir',type=Path,required=True);a=p.parse_args();run(a.raw_dir)
