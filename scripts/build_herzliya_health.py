"""Render the health-only Herzliya edition using the existing health card layout."""
import argparse
from pathlib import Path
from build_holon_health import build as build_health
ROOT=Path(__file__).resolve().parents[1]
def build(check=False):
 return build_health(check=check,city_dir=ROOT/'events-preview/herzliya')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
 if build(check=args.check) and args.check:raise SystemExit('Herzliya health page needs rebuilding')
