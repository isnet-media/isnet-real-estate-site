"""Refresh reviewed Yavne branches using the existing official-feed adapters."""
from pathlib import Path
import argparse,collections,json
from super_city_runtime import load

def run(raw_dir):
 collector=load('refresh_super_prices');deals=load('build_super_deals')
 # Existing collector imports its promotion builder by name; scope it to this city.
 import build_super_deals
 original=build_super_deals.build
 build_super_deals.build=deals.build
 try:report=collector.run(raw_dir)
 finally:build_super_deals.build=original
 D=collector.D;catalog=json.loads((D/'catalog.json').read_text())
 catalog['coverage_complete']=report['all_sources_updated'];collector.write(D/'catalog.json',catalog)
 prices=json.loads((D/'prices.json').read_text());prices['coverage_complete']=catalog['coverage_complete'];collector.write(D/'prices.json',prices)
 status=json.loads((D/'source-status.json').read_text());status.pop('connection_notes',None);collector.write(D/'source-status.json',status)
 d=json.loads((D/'deals.json').read_text());d['city']='יבנה';collector.write(D/'deals.json',d)
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--raw-dir',type=Path,required=True);a=p.parse_args();run(a.raw_dir)
